"""Prepare production ownership, closed doors and layout-3 interfaces."""
import sys,json,math,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix,Vector
import build_scene as b,build_pass10_draft as d
from common import xyz,ZPP,project,NORMAL
from pass10_common import ROOT,QA,OUT,LIVE,status
from build_pass10_final import group,pose_bells

def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10.blend'));sc=bpy.context.scene
    b.GROUPS.clear();b.M.clear()
    for m in bpy.data.materials:b.M[m.name]=m
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
    meta=json.loads((QA/'scene_metadata_final.json').read_text());old=json.loads((LIVE/'manifest.json').read_text())
    metal=b.M['P10 aged graphite steel'];teal=b.M['P10 restroom teal partitions'];brass=b.M['P10 worn queue brass']
    animations=[]
    # Undo the single open screen demonstration pose in the draft.
    for o in sc.objects:
        if o.get('door_id')=='2':
            side=o['door_side'];p=xyz(8.2+side*.465,.028,0)
            o.matrix_world=Matrix.Translation(p)@Matrix.Rotation(math.radians(72*side),4,'Z')@Matrix.Translation(-p)@o.matrix_world
    for i,u in enumerate([4.8,8.2,11.2],1):
        leaves=[o for o in sc.objects if o.get('door_id')==str(i)]
        for o in leaves:
            o['anim_id']='screen_'+str(i);o['anim_pivot']=list(xyz(u+o['door_side']*.465,.028,0));o['anim_angle']=-79*o['door_side']
        animations.append(dict(id='screen_'+str(i),door=i,screen=i,wall='v0',at=u,parent=None,z_index=900,opening_world=[[u-.55,0,0],[u+.55,0,0],[u+.55,0,114],[u-.55,0,114]]))
    # Group the cutaway fixtures by their actual footprint, keeping floor tiles
    # in the background so they cannot overpaint walkers.
    for o in list(sc.objects):
        n=o.name;layer=o.get('layer');a,v,c,w,z,h=d.bounds(o);u=(a+c)/2;vv=(v+w)/2
        if layer=='restroom':
            if n.startswith(('P10 restroom open door','P10 stall 1 ajar','P10 stall 2 door','P10 stall 3 door','P10 stall 4 door','P10 stall lock')):d.rm(o);continue
            if n.startswith(('P10 green vacant','P10 corridor green vacant')):group(o,'wc_dynamic')
            elif n.startswith(('P10 restroom junction partition','P10 restroom door lintel','P10 restroom door jamb','P10 restroom plaque','P10 restroom room-side plaque','P10 restroom corridor-side plaque','P10 occupancy housing')):group(o,'restroom_entry_wall')
            elif n.startswith(('P10 stall','P10 toilet','P10 open toilet')):
                i=min(range(4),key=lambda k:abs(vv-(4.4+k)));group(o,'restroom_stall_'+str(i+1))
            elif n.startswith(('P10 sink','P10 recessed sink','P10 mirror')):group(o,'restroom_sinks')
            elif n.startswith(('P10 hand dryer','P10 dryer label')):group(o,'restroom_dryer')
            elif n.startswith(('P10 mop','P10 restroom trash')):group(o,'restroom_service')
            elif n.startswith('P10 restroom cutaway right nib'):group(o,'restroom_side_wall')
            elif n.startswith('P10 closet divider'):group(o,'restroom_closet_wall')
            else:group(o,'background')
        if layer=='corridor_dressing':
            names=[('Crescent Nine','corridor_standee_1'),('The Last Train','corridor_standee_2'),('corridor bench','corridor_bench'),('drinking fountain','corridor_fountain'),('fountain bubbler','corridor_fountain'),('corridor trash','corridor_bin'),('fire extinguisher','corridor_extinguisher'),('extinguisher','corridor_extinguisher')]
            found=next((g for p,g in names if n.startswith('P10 '+p)),None)
            group(o,found or 'background')
        if layer=='ticket_ropes':group(o,'queue_front' if vv>7.4 else 'queue_back')
        if n.startswith(('P10 roof billboard upright','P10 roof billboard edge')):group(o,'ad_tower')
    def leaf_tag(objects,ident,pivot,angle):
        for o in objects:o['anim_id']=ident;o['anim_pivot']=list(pivot);o['anim_angle']=angle
    b.layer('restroom_entry_leaf');before=set(sc.objects)
    b.box('P10 closed restroom entry leaf',.99,3.06,1.80,3.10,1,103,teal,.012)
    b.line('P10 restroom entry pull',[xyz(1.08,3.125,44),xyz(1.08,3.125,58)],brass,.014)
    leaf_tag(set(sc.objects)-before,'restroom_entry',xyz(1.80,3.08,0),79)
    animations.append(dict(id='restroom_entry',door='wc',wall='v3',at=1.4,parent='restroom_entry_leaf',opening_world=[[.95,3.08,0],[1.85,3.08,0],[1.85,3.08,105],[.95,3.08,105]]))
    for i,v in enumerate([4.4,5.4,6.4,7.4],1):
        lo=v-.48;hi=v+.48;b.layer('restroom_stall_'+str(i));before=set(sc.objects)
        b.box('P10 closed stall door '+str(i),1.065,lo+.13,1.105,hi-.06,9,78,teal,.007)
        b.ball('P10 stall door lock '+str(i),xyz(1.128,hi-.16,41),.026,brass)
        leaf_tag(set(sc.objects)-before,'stall_'+str(i),xyz(1.1,lo+.13,0),-79)
        animations.append(dict(id='stall_'+str(i),door='stall_'+str(i),wall='u1.1',at=v,parent='restroom_stall_'+str(i),opening_world=[[1.11,lo+.12,8],[1.11,hi-.05,8],[1.11,hi-.05,80],[1.11,lo+.12,80]]))
    # Record the canonical closed matrices; all animation renders start here.
    bpy.context.view_layer.update()
    for o in sc.objects:
        if o.get('anim_id'):o['closed_matrix']=[q for row in o.matrix_world for q in row]
    # Unique WC material so changing its state never changes the frog neon.
    wcma=b.M['P10 frog mint tube core'].copy();wcma.name='P10 independent WC state'
    for o in b.GROUPS.get('wc_dynamic',[]):o.data.materials.clear();o.data.materials.append(wcma)
    specs={e['name']:{k:e[k] for k in ['footprint','height_px']} for e in old['occluders'] if e['name'] not in ['front_low_wall','roxy_blade']}
    specs.update({
      'front_solid_wall':dict(footprint=[0,8.88,3.015,9.07],height_px=159),
      'entrance_neon':dict(footprint=[-.83,9.10,-.03,9.37],height_px=247),
      'restroom_entry_wall':dict(footprint=[0,2.89,2.9,3.13],height_px=125),
      'restroom_entry_leaf':dict(footprint=[.95,3.02,1.85,3.94],height_px=105),
      'restroom_sinks':dict(footprint=[1.90,3.08,2.85,3.65],height_px=103),
      'restroom_dryer':dict(footprint=[.32,3.08,.72,3.34],height_px=70),
      'restroom_service':dict(footprint=[2.10,6.65,2.88,8.30],height_px=88),
      'restroom_side_wall':dict(footprint=[2.86,3.08,2.94,4.4],height_px=30),
      'restroom_closet_wall':dict(footprint=[.02,8.35,2.88,8.44],height_px=35),
      'queue_front':dict(footprint=[5.095,7.695,9.305,7.905],height_px=48),
      'queue_back':dict(footprint=[5.795,6.895,9.305,7.105],height_px=48),
      'corridor_standee_1':dict(footprint=[3.36,.22,3.84,.38],height_px=86),
      'corridor_standee_2':dict(footprint=[6.94,.21,7.42,.37],height_px=86),
      'corridor_bench':dict(footprint=[8.8,2.43,10.22,2.87],height_px=48),
      'corridor_fountain':dict(footprint=[6.91,2.48,7.36,2.86],height_px=49),
      'corridor_bin':dict(footprint=[12.51,2.48,12.85,2.82],height_px=36),
      'corridor_extinguisher':dict(footprint=[10.26,.10,10.47,.26],height_px=52)})
    for i,v in enumerate([4.4,5.4,6.4,7.4],1):specs['restroom_stall_'+str(i)]=dict(footprint=[.04,v-.48,1.14,v+.515],height_px=85)
    for n in list(specs):
        if not b.GROUPS.get(n):specs.pop(n)
    unexpected={n for n,v in b.GROUPS.items() if v and n not in specs and n not in ['background','ad_shelter','ad_paste_wall','ad_tower','wc_dynamic','bell_rooftop_dinkdonk','bell_entrance_dinkdonk']}
    assert not unexpected,unexpected
    for n,e in specs.items():e.update(name=n,z_index=99 if n=='paste_wall' else 1000+round(sum(e['footprint'])*50))
    for e in animations:
        if e['parent']:
            from package_layers import tile_clips
            e['z_index']=max(p['z_index'] for p in tile_clips(specs[e['parent']]))+1
    meta['production_occluders']=list(specs.values());meta['animations']=animations
    meta['led_signs']=[dict(e,door=e['door']-2,column_direction=1) for e in old['led_signs'] if e['wall']=='v0']
    meta['poster_frames']=[dict(e,screen=e['screen']-2) for e in old['poster_frames'] if e['wall']=='v0']
    prev=json.loads((ROOT/'qa9/scene_metadata.json').read_text())
    meta['poster_bulbs']=[dict(e,door=e['door']-2) for e in prev['poster_bulbs'] if e['door']>2]
    meta['neighbour_tube']=prev['neighbour_tube']
    for e in meta['ad_surfaces']:
        e['layer']='ad_'+e['name'];e['z_index']=100 if e['name'] in ['tower','paste_wall'] else e.get('z_index',2024)
    for e in meta['bells'].values():e['fps']=20
    # Add retained wordmark tube paths for a small depth-sorted optical halo.
    for o in sc.objects:
        if o.type=='CURVE' and o.name.startswith('P10 rooftop letter') and 'luminous core' in o.name:
            pts=[o.matrix_world@Vector(p.co[:3]) for p in o.data.splines[0].points]
            meta['neon_paths'].append({'name':o.name,'points_px':[project(p.x,-p.y,p.z*ZPP) for p in pts],'color':[.16,.76,1],'animated':None})
    bpy.context.view_layer.update()
    facing=[o.name for o in sc.objects if o.type=='FONT' and abs((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(NORMAL))>.999]
    assert not facing,facing
    meta['no_camera_facing_text']=True
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT'] and (o.name.startswith(('P10 multiplex','P10 single multiplex','P10 additional','P10 roof access','P10 roof service','P10 projection booth','P10 roof hatch','P10 HVAC','P10 air duct','P10 duct seam','P10 roof puddle','P10 rooftop','P10 roof billboard')) or o.get('pass8_surrounding') or o.get('pass8b_surrounding') or o.get('pass9_surrounding')) and o.get('layer')=='background':o['pass10_surrounding']=True
    sc.render.use_compositing=False;sc.render.use_border=False;sc.cycles.samples=64;sc.cycles.adaptive_threshold=.015
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10.blend'))
    (QA/'scene_metadata_final.json').write_text(json.dumps(meta,indent=2))
    status('Production ownership prepared: %d foreground parents, 3 screen + 5 restroom/stall animations, new LED/poster numbering and ad/WC planes'%len(specs))
if __name__=='__main__':main()
