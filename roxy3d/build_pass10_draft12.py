"""Brief 24: quieter warm restroom; one fixed-camera draft with weather."""
import sys, shutil, time
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
import build_scene as b
from common import ROOT, ZPP
from build_pass10_draft4 import quality
from build_pass10_draft7 import rain_layer
from pass8_common import gpu
from pngio import read, write

QA=ROOT/'qa10';TMP=ROOT/'cache'/'draft12';SOURCE=ROOT/'roxy_pass10_draft.blend'


def room_object(o):
    if o.type not in ['MESH','CURVE','FONT'] or o.hide_render:return False
    points=[o.matrix_world@Vector(p) for p in o.bound_box]
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    u=(lo[0]+hi[0])*.5;v=-(lo[1]+hi[1])*.5;z=(lo[2]+hi[2])*.5*ZPP
    # Include the tile-bearing wall, fittings and both sides of the doorway;
    # leave the ticket/lobby partition and exterior street wall untouched.
    return -.23<=u<2.90 and 2.93<=v<=8.44 and -1<z<160 and hi[0]-lo[0]<3.15 and hi[1]-lo[1]<6.2


def set_input(tree,socket,value):
    for link in list(socket.links):tree.links.remove(link)
    socket.default_value=value


def mathnode(tree,op,*args):
    q=tree.nodes.new('ShaderNodeMath');q.operation=op
    for s,v in zip(q.inputs,args):
        if isinstance(v,(int,float)):s.default_value=v
        else:tree.links.new(v,s)
    return q.outputs[0]


def range_node(tree,value,a,c,lo=0,hi=1):
    q=tree.nodes.new('ShaderNodeMapRange');q.clamp=True;q.interpolation_type='SMOOTHSTEP'
    tree.links.new(value,q.inputs['Value'])
    for key,val in [('From Min',a),('From Max',c),('To Min',lo),('To Max',hi)]:q.inputs[key].default_value=val
    return q.outputs[0]


def restroom_lighting(sc,room):
    from screen_door_fix import repair_screen_doors
    repair_screen_doors(sc)
    original=bpy.data.collections['D11 cinema interior light receivers']
    rest=bpy.data.collections.new('D12 restroom warm light receivers');sc.collection.children.link(rest)
    other=bpy.data.collections.new('D12 unchanged cinema receivers outside restroom');sc.collection.children.link(other)
    for o in room:rest.objects.link(o)
    room_names={o.name for o in room}
    for o in original.objects:
        if o.name not in room_names:other.objects.link(o)
    repair_screen_doors(sc)
    lamp=sc.objects['P10 restroom soft ceiling'];old_power=lamp.data.energy;old_color=tuple(lamp.data.color)
    # The previous restroom lamp also illuminated the lobby. Retain that
    # exact source outside this room so the approved lobby rig is unchanged.
    continuation=lamp.copy();continuation.data=lamp.data.copy();continuation.name='D12 retained D11 ceiling contribution outside restroom';sc.collection.objects.link(continuation)
    continuation.light_linking.receiver_collection=other
    for o in list(sc.objects):
        if o.type=='LIGHT' and o.light_linking.receiver_collection==original:o.light_linking.receiver_collection=other
    lamp.light_linking.receiver_collection=rest;lamp.data.energy=44;lamp.data.color=(1,.83,.60)
    # All existing lamps keep position, shape and physical falloff. The room's
    # neutral/cool generic ceiling contributions are removed only in this room.
    print('D12 restroom ceiling',old_power,'->',lamp.data.energy,'W; RGB',old_color,'->',tuple(lamp.data.color),flush=True)
    return old_power,old_color,len(room)


def tile_material(source,floor):
    ma=source.copy();ma.name='D12 aged cream '+('floor' if floor else 'wall')+' tile';t=ma.node_tree;n=t.nodes;l=t.links;p=next(q for q in n if q.type=='BSDF_PRINCIPLED')
    tex=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Generated'],sep.inputs[0])
    # Recessed dirt sits alongside existing real grout gaps. Generated UV axes
    # follow each existing tile, with no change to tile geometry or spacing.
    axes=['X','Y'] if floor else ['Y','Z'];edges=[]
    for axis in axes:edges.append(mathnode(t,'MINIMUM',sep.outputs[axis],mathnode(t,'SUBTRACT',1,sep.outputs[axis])))
    edge=mathnode(t,'MINIMUM',*edges);clean=range_node(t,edge,.018,.105,.60,1)
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');l.new(geo.outputs['Position'],noise.inputs['Vector']);noise.inputs['Scale'].default_value=16;noise.inputs['Detail'].default_value=3
    info=n.new('ShaderNodeObjectInfo');variation=range_node(t,info.outputs['Random'],0,1,.86,1.06)
    mottling=range_node(t,noise.outputs['Fac'],.2,.8,.91,1.02)
    factor=mathnode(t,'MULTIPLY',clean,mathnode(t,'MULTIPLY',variation,mottling))
    col=n.new('ShaderNodeMixRGB');col.blend_type='MULTIPLY';col.inputs[0].default_value=1;col.inputs[1].default_value=(.38,.315,.225,1) if floor else (.42,.355,.265,1);l.new(factor,col.inputs[2]);l.new(col.outputs[0],p.inputs['Base Color'])
    set_input(t,p.inputs['Roughness'],.43 if floor else .38);set_input(t,p.inputs['Coat Weight'],0)
    ma['draft12_finish']='aged cream/beige tile, irregular darkening toward existing grout; original bump retained'
    return ma


def grout_material(source):
    ma=source.copy();ma.name='D12 warm grey grout with accumulated dirt';t=ma.node_tree;n=t.nodes;l=t.links;p=next(q for q in n if q.type=='BSDF_PRINCIPLED')
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=24;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.025,.021,.015,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.075,.061,.043,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);set_input(t,p.inputs['Roughness'],.96);set_input(t,p.inputs['Coat Weight'],0)
    return ma


def teal_material(source):
    ma=source.copy();ma.name='D12 muted desaturated teal laminate';t=ma.node_tree;n=t.nodes;l=t.links;p=next(q for q in n if q.type=='BSDF_PRINCIPLED')
    # Retain the original fine manufacturing texture / normal, but use an
    # older, greyer pigment with a less assertive glaze.
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=55;noise.inputs['Detail'].default_value=2
    geo=n.new('ShaderNodeNewGeometry');l.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(.077,.121,.113,1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(.115,.179,.162,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);set_input(t,p.inputs['Roughness'],.58);set_input(t,p.inputs['Coat Weight'],0)
    return ma


def materials(sc,room):
    cache={};counts={'tiles':0,'teal':0,'grout':0}
    basegrout=bpy.data.materials['P10 dark aged grout'];grout=grout_material(basegrout)
    for o in room:
        if not o.data.materials:continue
        isfloor=o.name.startswith('P10 restroom floor tile');iswall=o.name.startswith('P10 restroom wall tile')
        for index,ma in enumerate(list(o.data.materials)):
            if not ma:continue
            new=None
            if isfloor or iswall:
                key=(ma.name,'floor' if isfloor else 'wall')
                if key not in cache:cache[key]=tile_material(ma,isfloor)
                new=cache[key];counts['tiles']+=1
            elif o.name=='P10 restroom tiled floor':new=grout;counts['grout']+=1
            elif 'restroom teal partitions' in ma.name:
                key=(ma.name,'teal')
                if key not in cache:cache[key]=teal_material(ma)
                new=cache[key];counts['teal']+=1
            if new:
                if o.data.users>1:o.data=o.data.copy()
                o.data.materials[index]=new
    # Wall tiles have genuine gaps; the supporting wall face becomes grout.
    # Only that inside face changes, not the back of the structural wall.
    wall=sc.objects['P10 restroom left structural wall']
    if wall.data.users>1:wall.data=wall.data.copy()
    slot=len(wall.data.materials);wall.data.materials.append(grout)
    xmax=max((wall.matrix_world@v.co).x for v in wall.data.vertices)
    for face in wall.data.polygons:
        if (wall.matrix_world@face.center).x>xmax-.0001:face.material_index=slot
    counts['grout']+=1
    print('D12 restroom-only finishes',counts,flush=True);return counts


def main():
    start=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);backup=TMP/'source_draft11.blend'
    if not backup.exists():shutil.copy2(SOURCE,backup)
    assert not (TMP/'render_started').exists(),'Strict draft: do not repeat a started render'
    bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene;assert sc.get('draft11_brief')
    b.GROUPS.clear();b.M.clear();bpy.context.view_layer.update()
    room=[o for o in sc.objects if room_object(o)];old_power,old_color,nroom=restroom_lighting(sc,room);counts=materials(sc,room)
    # Geometry, markings, lobby/carpet, exterior lights and all water remain D11.
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    sc.render.use_compositing=True;sc.render.filepath=str(QA/'draft_12.png');sc['draft12_brief']='BRIEF-24-draft12.md'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    (TMP/'render_started').write_text(datetime.now().astimezone().isoformat(),encoding='utf-8')
    print('D12 restroom revision saved; rendering one camera exposure and matching weather',flush=True)
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png';t=time.perf_counter()
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True);beauty_seconds=time.perf_counter()-t
    t=time.perf_counter();rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True);weather_seconds=time.perf_counter()-t
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False);alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_12.png',out);beauty.unlink();weather.unlink()
    (QA/'DRAFT-12.md').write_text(
        '# Draft 12\n\n'
        'Built from saved Draft 11; updated `roxy_pass10_draft.blend`. Restroom-only changes; fixtures, room layout, YEE/PEPE vandalism, lobby/carpet, approved dark exterior, camera and HDR glare retained.\n'
        f'Restroom ceiling: {old_power:g} -> 44 W; RGB ({old_color[0]:.2f}, {old_color[1]:.2f}, {old_color[2]:.2f}) -> (1.00, 0.83, 0.60), a dim warm fluorescent cast. Removed the shared cool cinema fills from restroom receivers only. Retained the old ceiling source on non-restroom receivers so its existing lobby contribution and all lobby light settings remain intact.\n'
        f'{counts["tiles"]} existing tiles now have aged cream/beige glaze with subtle colour variation and dirt near their real grout gaps; warm grey/brown grime in the floor grout and inside wall backing. {counts["teal"]} existing teal material assignments changed to muted, desaturated laminate; marker/scratch materials and strokes are untouched.\n'
        f'One delivered image: `draft_12.png`, 1280 x 720, Cycles 256 fixed samples, OptiX denoising, current-scene occluded weather. Render time {beauty_seconds:.1f} s beauty + {weather_seconds:.1f} s weather = {beauty_seconds+weather_seconds:.1f} s; total build/composite {time.perf_counter()-start:.1f} s. Inherited drip/crown motion-blur limitation remains unchanged. One STATUS line; stopped.\n',encoding='utf-8')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 12 quieter warm restroom from D11; aged cream tiles, dirty grout, muted teal and preserved YEE/PEPE; lobby lighting/carpet retained; one 720p/256-sample weather-composited draft_12.png; DRAFT-12.md written; stopped.\n')
    print('D12 COMPLETE. ONE IMAGE. STOP.',flush=True)


if __name__=='__main__':main()
