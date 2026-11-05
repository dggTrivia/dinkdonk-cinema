"""Brief 23: lighting-only dark-night revision; one final camera/weather image."""
import sys, shutil, time, math
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
from screen_door_fix import is_screen_door, repair_screen_doors

QA=ROOT/'qa10';TMP=ROOT/'cache'/'draft11';SOURCE=ROOT/'roxy_pass10_draft.blend'


def light_changes(sc):
    rows=[]
    # No exposure / tone-map adjustment: the cinema and emissive artwork keep
    # their approved values. Remove illumination in the exterior itself.
    bg=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND')
    old=bg.inputs['Strength'].default_value;bg.inputs['Strength'].default_value=.004
    rows.append(f'World background strength {old:g} -> 0.004 (colour unchanged).')

    sky=bpy.data.materials['P8 indigo cloud dome'].node_tree.nodes.get('Principled BSDF')
    old=sky.inputs['Emission Strength'].default_value;sky.inputs['Emission Strength'].default_value=.025
    rows.append(f'Cloud-dome emission {old:g} -> 0.025; retained its existing low-horizon gradient.')
    haze=bpy.data.materials.get('P8 distant rain haze')
    if haze and haze.node_tree:
        volume=next((n for n in haze.node_tree.nodes if n.type=='PRINCIPLED_VOLUME'),None)
        if volume:
            old=volume.inputs['Emission Strength'].default_value;volume.inputs['Emission Strength'].default_value=.00005
            rows.append(f'Distant-haze emission {old:g} -> 0.00005; density unchanged.')

    # These linked exterior readability sources must contribute no light.
    exterior=[
        'P8 indigo sky bounce','P8 street horizon fill','P8 opposite wet roof fill',
        'P8 rear horizon bounce','P8B hazy roof fill','P8B distant facade haze fill',
        'P9 west facade and roof fill','P10 broad multiplex roof fill','D3 alley bounced sky',
    ]
    changes=[]
    for name in exterior:
        o=sc.objects.get(name)
        if o:
            old=o.data.energy;o.data.energy=0;changes.append(f'{name}: {old:g} -> 0 W')
    rows.append('Exterior ambient/readability fills: '+'; '.join(changes)+'.')

    # Preserve the existing cinema illumination rather than lowering exposure.
    # Receiver linking confines the cutaway's otherwise missing ceiling to its
    # indoor surfaces, so broad lamps cannot illuminate neighbouring roofs.
    indoors=bpy.data.collections.new('D11 cinema interior light receivers');sc.collection.children.link(indoors)
    for o in list(sc.objects):
        if o.type not in ['MESH','CURVE','FONT'] or o.hide_render:continue
        points=[o.matrix_world@Vector(p) for p in o.bound_box]
        lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
        u=(lo[0]+hi[0])*.5;v=-(lo[1]+hi[1])*.5;z=(lo[2]+hi[2])*.5*ZPP
        if is_screen_door(o) or (-.02<=u<=13.10 and -.02<=v<=9.36 and z<205 and hi[0]-lo[0]<13.5 and hi[1]-lo[1]<10):
            indoors.objects.link(o)
    repair_screen_doors(sc)
    # These three unlinked generic sources also contributed to the approved
    # lobby. Keep their interior contribution, remove their entire exterior one.
    retained=['Cool street sky reflection','P10 broad roof moon fill','P10 auditorium facade fill']
    retained_values=[]
    for name in retained:
        o=sc.objects.get(name)
        if o:
            o.light_linking.receiver_collection=indoors
            retained_values.append(f'{name}: {o.data.energy:g} W retained indoors, exterior receive on -> off')
    rows.append('Interior brightness preservation: '+'; '.join(retained_values)+'.')
    ceiling=['Large soft cinema key','Warm lobby pool','Concession warm ceiling bounce','Corridor left blue fill','Corridor right fill','P10 restroom soft ceiling']
    ceiling_values=[]
    for name in ceiling:
        o=sc.objects.get(name)
        if o:
            o.light_linking.receiver_collection=indoors
            ceiling_values.append(f'{name} {o.data.energy:g} -> {o.data.energy:g} W')
    rows.append('Existing cinema ceiling sources now receive indoors only: '+', '.join(ceiling_values)+'. Light colours, positions and falloff are unchanged; interior indirect spill can still exit the glass frontage.')

    # Real visible bulbs get physical point-light reflections again. D4 had
    # suppressed the specular factor on all lights with "pool" in their name.
    practical=[]
    for o in sc.objects:
        if o.type!='LIGHT' or o.data.type!='POINT':continue
        if any(s in o.name for s in ['Warm street lamp pool','P8 far sidewalk warm pool','D3 alley service pool','D3 cafe window pool']):
            old=o.data.specular_factor;o.data.specular_factor=1
            practical.append(f'{o.name} {old:g} -> 1')
    rows.append('Practical point-light specular factors: '+', '.join(practical)+'. Practical powers, neon emission, lit windows, shop/billboard lamps, bus headlights and all interior action lights retain their Draft 10 values.')

    # Broad luminous sky was making the roof water look self-lit. Retain only
    # faint sky and narrow, lower-radiance city highlights at street distance.
    catcher_changes=[]
    for ma in bpy.data.materials:
        if not ma.name.startswith('D10 catcher ') or not ma.node_tree:continue
        n=ma.node_tree.nodes;l=ma.node_tree.links;em=next(q for q in n if q.type=='EMISSION')
        if ma.name.endswith('sky glow'):
            ramp=em.inputs['Strength'].links[0].from_node
            oldlo=ramp.inputs['To Min'].default_value;oldhi=ramp.inputs['To Max'].default_value
            ramp.inputs['To Min'].default_value=.002;ramp.inputs['To Max'].default_value=.012
            catcher_changes.append(f'sky {oldlo:g}..{oldhi:g} -> 0.002..0.012')
        else:
            old=em.inputs['Strength'].default_value
            new=4.0 if 'pink' in ma.name else 4.4 if 'cyan' in ma.name else 1.6
            em.inputs['Strength'].default_value=new
            # In this fixed orthographic scene, these cards were placed 35-37
            # units along the street reflection ray. Roof hits arrive 6+ units
            # sooner; smooth distance gating restricts them to street pools.
            mix=next(q for q in n if q.type=='MIX_SHADER');gate=mix.inputs[0].links[0].from_socket
            path=next(q for q in n if q.type=='LIGHT_PATH')
            near=n.new('ShaderNodeMapRange');near.name='D11 local street reflection distance';near.interpolation_type='SMOOTHSTEP';near.clamp=True
            near.inputs['From Min'].default_value=31;near.inputs['From Max'].default_value=33
            l.new(path.outputs['Ray Length'],near.inputs['Value'])
            mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(gate,mult.inputs[0]);l.new(near.outputs[0],mult.inputs[1]);l.new(mult.outputs[0],mix.inputs[0])
            catcher_changes.append(f'{ma.name.removeprefix("D10 catcher ")}: {old:g} -> {new:g}')
    rows.append('Glossy-only hidden catchers: '+ '; '.join(catcher_changes)+'. Coloured/window catchers additionally fade out at ray lengths below 31-33 scene units, localising them to street-height reflections; visibility restrictions remain intact.')
    return rows


def main():
    start=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);backup=TMP/'source_draft10.blend'
    if not backup.exists():shutil.copy2(SOURCE,backup)
    assert not (TMP/'render_started').exists(),'Strict draft: do not repeat a started render'
    bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene
    assert sc.get('draft10_brief'),'Draft 11 must start from saved Draft 10'
    b.GROUPS.clear();b.M.clear();bpy.context.view_layer.update();rows=light_changes(sc)
    for row in rows:print('D11',row,flush=True)
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    sc.render.use_compositing=True;sc.render.filepath=str(QA/'draft_11.png');sc['draft11_brief']='BRIEF-23-draft11.md'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    (TMP/'render_started').write_text(datetime.now().astimezone().isoformat(),encoding='utf-8')
    print('D11 lighting saved; rendering one fixed-camera exposure and matching weather',flush=True)
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png';t=time.perf_counter()
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True);beauty_seconds=time.perf_counter()-t
    t=time.perf_counter();rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True);weather_seconds=time.perf_counter()-t
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False);alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_11.png',out);beauty.unlink();weather.unlink()
    (QA/'DRAFT-11.md').write_text('# Draft 11\n\nLighting-only revision from saved Draft 10; updated `roxy_pass10_draft.blend`. Geometry, artwork, wet materials, water animation nodes, camera, exposure (+0.25), AgX and HDR glare are retained.\n\n'+'\n'.join(rows)+f'\n\nOne delivered 1280 x 720, 256-sample OptiX-denoised image with current-scene occluded weather: `draft_11.png`. Render time {beauty_seconds:.1f} s beauty + {weather_seconds:.1f} s weather = {beauty_seconds+weather_seconds:.1f} s; total build/composite {time.perf_counter()-start:.1f} s. The inherited changing-instance drip/crown object still has the Draft 10 deformation-motion-blur limitation. One STATUS line; stopped after this image.\n',encoding='utf-8')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 11 lighting-only dark night from D10; exterior ambient/readability fills removed, sky/catchers dimmed, interior lighting preserved and practical reflections enabled; one 720p/256-sample weather-composited draft_11.png; old/new light values in DRAFT-11.md; stopped.\n')
    print('D11 COMPLETE. ONE IMAGE. STOP.',flush=True)


if __name__=='__main__':main()
