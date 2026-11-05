"""Production ownership and layout-3 interfaces for the approved packed scene."""
import math,json,copy
import bpy
from mathutils import Vector,Matrix
import build_scene as b
from common import xyz,ZPP,project

def bounds(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [min(p.x for p in pts),min(-p.y for p in pts),max(p.x for p in pts),max(-p.y for p in pts),min(p.z for p in pts)*ZPP,max(p.z for p in pts)*ZPP]

def prepare(sc,old,prior):
    from screen_door_fix import repair_screen_doors
    repair_screen_doors(sc)
    # Also recognizes legacy packed drafts whose bus plates were incorrectly
    # tagged as shelter parts, before the builder ownership repair.
    from parked_bus_fix import repair_parked_bus_plates
    repair_parked_bus_plates(sc,remove=True)
    original_camera=[v for row in sc.camera.matrix_world for v in row]
    # The parked bus was for draft inspection. Production uses moving sprites.
    for o in list(sc.objects):
        if o.get('draft5_bus') or o.get('layer')=='draft5_parked_bus' or o.name.startswith(('D5 art boxing','D5 art courier')):bpy.data.objects.remove(o,do_unlink=True)
    specs={e['name']:copy.deepcopy(e) for e in prior['production_occluders']}
    for key in ['ad_tower','roxy_blade','front_low_wall']:specs.pop(key,None)
    animations=[]
    for o in sc.objects:
        if o.get('door_id')=='2':
            side=o['door_side'];pivot=xyz(8.2+side*.465,.028)
            o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(72*side),4,'Z')@Matrix.Translation(-pivot)@o.matrix_world
    for i,u in enumerate([4.8,8.2,11.2],1):
        for o in sc.objects:
            if o.get('door_id')==str(i):o['anim_id']='screen_'+str(i);o['anim_pivot']=list(xyz(u+o['door_side']*.465,.028));o['anim_angle']=-79*o['door_side']
        animations.append(dict(id='screen_'+str(i),door=i,screen=i,wall='v0',at=u,parent=None,z_index=900,opening_world=[[u-.55,0,0],[u+.55,0,0],[u+.55,0,114],[u-.55,0,114]]))
    bpy.context.view_layer.update()
    for o in sc.objects:
        if o.type not in ['MESH','CURVE','FONT']:continue
        n=o.name;layer=o.get('layer','background');a,v,c,w,z,h=bounds(o);vv=(v+w)/2
        group=layer if layer in specs else 'background'
        if layer=='restroom':
            if n.startswith(('P10 restroom open door','P10 restroom open door pull','P10 stall 1 ajar door','P10 stall 2 door','P10 stall 3 door','P10 stall 4 door','P10 stall lock')):
                bpy.data.objects.remove(o,do_unlink=True);continue
            if n.startswith(('P10 green vacant','P10 corridor green vacant')):group='wc_dynamic'
            elif n.startswith(('P10 restroom junction partition','P10 restroom door lintel','P10 restroom door jamb','P10 restroom plaque','P10 restroom room-side plaque','P10 restroom corridor-side plaque','P10 occupancy housing')):group='restroom_entry_wall'
            elif n.startswith(('P10 stall','P10 toilet','P10 open toilet','D3 stall')):group='restroom_stall_'+str(min(range(4),key=lambda k:abs(vv-(4.4+k)))+1)
            elif n.startswith(('P10 sink','P10 recessed sink','P10 mirror')):group='restroom_sinks'
            elif n.startswith(('P10 hand dryer','P10 dryer label')):group='restroom_dryer'
            elif n.startswith(('P10 mop','P10 restroom trash')):group='restroom_service'
            else:group='background'
        if layer=='ticket_ropes':group='queue_front' if vv>7.4 else 'queue_back'
        if layer=='corridor_dressing':
            pairs=[('Crescent Nine','corridor_standee_1'),('The Last Train','corridor_standee_2'),('corridor bench','corridor_bench'),('drinking fountain','corridor_fountain'),('fountain bubbler','corridor_fountain'),('corridor trash','corridor_bin'),('extinguisher','corridor_extinguisher'),('fire extinguisher','corridor_extinguisher')]
            group=next((g for p,g in pairs if n.startswith('P10 '+p)),'background')
        if layer=='draft6_shelter':group='bus_stop'
        if n.startswith(('D6 shelter','D6 stop pole','D6 stop sign','D6 route 05','D6 timetable','D6 art timetable')):group='bus_stop'
        if n.startswith(('D7 restroom aligned','D7 continuous ticket restroom')):group='restroom_side_wall'
        if n.startswith(('D7 restroom service divider','D7 matching service')):group='restroom_closet_wall'
        if n.startswith('D7 restroom plaque'):group='restroom_entry_wall'
        if layer=='draft6_restroom':
            group='restroom_sinks' if a>1.8 and w<3.7 else 'restroom_stall_'+str(min(range(4),key=lambda k:abs(vv-(4.4+k)))+1)
        if n.startswith('D3 stall laminate'):group='restroom_stall_'+str(min(range(4),key=lambda k:abs(vv-(4.4+k)))+1)
        if o.get('anim_id'):group='background'
        o['cloud_group']=group
    teal=bpy.data.materials['D12 muted desaturated teal laminate'];brass=bpy.data.materials['P10 worn queue brass']
    def tag(objects,ident,group,pivot,angle):
        for o in objects:
            o['cloud_group']=group;o['anim_id']=ident;o['anim_pivot']=list(pivot);o['anim_angle']=angle
            receivers=bpy.data.collections['D12 restroom warm light receivers']
            if o.name not in receivers.objects:receivers.objects.link(o)
    b.layer('restroom_entry_leaf');before=set(sc.objects)
    b.box('Cloud closed restroom entry leaf',.99,3.06,1.80,3.10,1,103,teal,.012)
    b.line('Cloud restroom entry pull',[xyz(1.08,3.125,44),xyz(1.08,3.125,58)],brass,.014)
    tag(set(sc.objects)-before,'restroom_entry','restroom_entry_leaf',xyz(1.80,3.08),79)
    animations.append(dict(id='restroom_entry',door='wc',wall='v3',at=1.4,parent='restroom_entry_leaf',opening_world=[[.95,3.08,0],[1.85,3.08,0],[1.85,3.08,105],[.95,3.08,105]]))
    for i,v in enumerate([4.4,5.4,6.4,7.4],1):
        lo=v-.48;hi=v+.48;before=set(sc.objects);b.layer('restroom_stall_'+str(i))
        b.box('Cloud closed stall door '+str(i),1.065,lo+.13,1.105,hi-.06,9,78,teal,.007)
        b.ball('Cloud stall door lock '+str(i),xyz(1.128,hi-.16,41),.026,brass)
        new=set(sc.objects)-before
        # Keep the marker/etched artwork attached to the moving leaf.
        for o in sc.objects:
            if o.name.startswith('D6 ') and o.get('surface_vandalism'):
                a,v0,c,v1,z,h=bounds(o)
                if 1.06<a<1.16 and lo+.12<=v0 and v1<=hi-.06:new.add(o)
        tag(new,'stall_'+str(i),'restroom_stall_'+str(i),xyz(1.1,lo+.13),-79)
        animations.append(dict(id='stall_'+str(i),door='stall_'+str(i),wall='u1.1',at=v,parent='restroom_stall_'+str(i),opening_world=[[1.11,lo+.12,8],[1.11,hi-.05,8],[1.11,hi-.05,80],[1.11,lo+.12,80]]))
    bpy.context.view_layer.update()
    for o in sc.objects:
        if o.get('anim_id'):o['closed_matrix']=[v for row in o.matrix_world for v in row]
    # Dedicated occupancy material, separate from all neon.
    wc=[o for o in sc.objects if o.get('cloud_group')=='wc_dynamic']
    if wc:
        ma=wc[0].data.materials[0].copy();ma.name='Cloud independent WC state'
        for o in wc:o.data.materials.clear();o.data.materials.append(ma)
    groups={}
    for o in sc.objects:
        g=o.get('cloud_group','background')
        if g not in ['background','wc_dynamic'] and o.type in ['MESH','CURVE','FONT']:groups.setdefault(g,[]).append(o)
    records=[]
    for name,obs in groups.items():
        bs=[bounds(o) for o in obs];fp=[min(a[0] for a in bs),min(a[1] for a in bs),max(a[2] for a in bs),max(a[3] for a in bs)]
        if fp[2]-fp[0]<.005:fp[2]=fp[0]+.005
        if fp[3]-fp[1]<.005:fp[3]=fp[1]+.005
        records.append(dict(name=name,footprint=fp,height_px=max(a[5] for a in bs),z_index=1000+round(sum(fp)*50),objects=[o.name for o in obs]))
    for a in animations:
        if a['parent']:
            r=next(r for r in records if r['name']==a['parent']);a['z_index']=1000+round((r['footprint'][2]+r['footprint'][3])*100)+1
    m=copy.deepcopy(old)
    for key in list(m):
        if key.startswith(('pass4','pass5','pass6','pass7','pass8','pass9')) or key in ['validation','notes','coordinate_deviations','footprint_changes','loop_seam_validation','light_loop_bytes','light_loop_sha256','light_loop_2x_bytes','light_loop_2x_sha256']:m.pop(key,None)
    m.update(layout=3,status='planned',asset_pack_pass=10,asset_pack_revision='10-cloud-draft13',marquees=[],occluders=[],render_layers=[],door_anims=[],wc_indicator={})
    m['doors']=[dict(screen=i,wall='v0',at=u,approach=[[u,1.4],[u,.55]]) for i,u in enumerate([4.8,8.2,11.2],1)]
    m['led_signs']=[dict(e,door=e['door']-2,column_direction=1) for e in old['led_signs'] if e['wall']=='v0']
    m['poster_frames']=[dict(e,screen=e['screen']-2) for e in old['poster_frames'] if e['wall']=='v0']
    stalls=[dict(spot=[1.5,v],route_points=[[1.4,3.5],[1.6,4.1],[1.6,v],[1.5,v]]) for v in [4.4,5.4,6.4,7.4]]
    m['restroom']=dict(door=[1.4,3.0],outside=[1.4,2.6],inside=[1.4,3.5],stalls=stalls,sinks=[[2.12,4.1],[2.63,4.1]],dryer=[.55,3.55],route_points={'sinks':[[[1.4,3.5],[1.6,4.1],[2.12,4.1]],[[1.4,3.5],[1.6,4.1],[2.63,4.1]]],'dryer':[[1.4,3.5],[.55,3.55]]})
    m['queue']=dict(slots=[[round(4.85+.62*i,2),7.4] for i in range(7)],entry=[9.3,7.4],window2_gap=[4.4,5.79])
    m['bus_shelter']=dict(seats=json.loads(sc['draft6_seats_json']),boarding_corridor=list(sc['draft6_boarding_corridor']),route='05',operator='d.gg transit',destination='05 DINK DONK')
    m['vehicle_baked_signs']=['05 DINK DONK','d.gg TRANSIT','DGG 05'];m['baked_signs']=[s for s in old['baked_signs'] if not any(k in s.lower() for k in ['roxy','bus95','d.gg'])]+['DINK DONK','Anything else?','WCAT business','EatFresh']
    props=[]
    for e in old['prop_loops']:
        e=copy.deepcopy(e);n=e['name']
        if n.startswith(('shelter_drip','roof_rain_bus_stop','dgg_neon_halo','awning_rain','film_glass_','water_glass_')):continue
        if n.startswith('poster_bulbs_'):
            number=int(n.split('_')[2])
            if number<3:continue
            e['name']=n.replace('bulbs_'+str(number),'bulbs_'+str(number-2));e['variant_group']='poster_bulbs_'+str(number-2)
        e.pop('parent_slices',None);props.append(e)
    m['prop_loops']=props
    ads=[]
    for name,wall,front,a,c,z0,z1 in [('wcat','u0',-.889,3.60,7.50,266,365),('eatfresh','u0',-.667,.45,3.15,254,328),('shelter','v0',9.262,.083,.637,10.5,70.5)]:
        pts=[(front,c,z1),(front,a,z1),(front,a,z0),(front,c,z0)] if wall=='u0' else [(a,front,z1),(c,front,z1),(c,front,z0),(a,front,z0)]
        ads.append(dict(name=name,wall=wall,offset=front,along=[a,c],z_px=[z0,z1],quad_px=[project(*p) for p in pts],aspect=(c-a)*ZPP/(z1-z0),lit=True,default_art_baked=True,z_index=100 if name!='shelter' else 2024))
    ads.extend(copy.deepcopy(a) for a in old['ad_surfaces'] if a['name']=='paste_wall')
    m['ad_surfaces']=ads;m['glow']=None;m['static_glow_enabled']=False
    m['loop_seconds']=6;m['fps']=24;m['loop_frames']=144;m['light_loop']='light_loop.webm';m['light_loop_2x']='light_loop_2x.webm'
    m['cloud_contract']={'unique_frames':48,'cycle_seconds':2,'repetitions':3,'samples_max':256,'denoiser':'OPTIX','neon':'two separate physical tube circuits alternate every 6 frames; off circuit remains dark glass','no_green_aperture':'Retired in out9; layout 3 uses in-world ad quads.'}
    m['cloud_contract'].update(samples_min=64,adaptive_threshold=.01,persistent_data=True,static_wet_split=False,approved_draft=13,marquee='Dim amber, four smooth chase groups, 2 second period',rain='Draft 10 wet layers, ponds, GN drips/crowns/pours, curb flow and reflection-only catchers; GN rain motion blur disabled')
    assert original_camera==[v for row in sc.camera.matrix_world for v in row]
    return m,dict(groups=records,animations=animations,ad_surfaces=ads,camera_matrix=original_camera)
