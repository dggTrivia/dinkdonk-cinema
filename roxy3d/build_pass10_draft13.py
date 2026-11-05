"""Brief 25: practical marquee bulbs and local truss lighting; one draft."""
import sys, math, shutil, time
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
import build_scene as b
from common import ROOT, xyz, ZPP
from build_pass10_draft4 import quality
from build_pass10_draft7 import rain_layer
from pass8_common import gpu
from pngio import read, write

QA=ROOT/'qa10';TMP=ROOT/'cache'/'draft13';SOURCE=ROOT/'roxy_pass10_draft.blend'


def mat(name,color,rough=.4,metal=0,emit=0):
    ma=b.material('D13 '+name,color,rough,metal,emit)
    p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.55;p.inputs['Coat IOR'].default_value=1.33;p.inputs['Coat Roughness'].default_value=.035
    return ma


def line(name,points,material,r=.01):
    return b.line('D13 '+name,[xyz(*p) for p in points],material,r)


def center(o):
    ps=[o.matrix_world@Vector(p) for p in o.bound_box]
    return sum(ps,Vector())/8


def marquee(sc):
    b.layer('draft13_rooftop_marquee');original=set(sc.objects)
    steel=mat('aged black enamel bulb rail',(.045,.049,.045),.40,.65)
    brass=mat('aged lamp socket brass',(.22,.14,.065),.48,.70)
    ceramic=mat('weathered porcelain sockets',(.21,.18,.13),.63)
    rubber=mat('black insulated wiring',(.009,.012,.014),.78)
    reflector=mat('dull aluminium reflector',(.36,.34,.29),.29,.85)
    bulb=mat('dim amber incandescent envelopes',(1,.50,.19),.24,0,2.2)
    p=bulb.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.25
    lens=mat('warm floodlight glass',(1,.65,.33),.19,0,2.8)

    # Slightly outboard of the existing 322..421 truss, clear of the hood,
    # letter tubes and both raised/lowered arm-and-bell configurations.
    u0,u1=3.60,12.65;z0,z1=316,430;v=-.69
    for z in [z0,z1]:
        line('marquee perimeter rail',[(u0,v,z),(u1,v,z)],steel,.018)
        line('sheathed bulb bus wire',[(u0,v-.027,z),(u1,v-.027,z)],rubber,.007)
    for u in [u0,u1]:line('marquee perimeter upright',[(u,v,z0),(u,v,z1)],steel,.018)
    for u in [3.8,5.6,7.4,9.2,11,12.5]:
        for za,zb in [(322,z0),(421,z1)]:line('marquee rail fastening',[(u,v-.003,za),(u,v-.003,zb)],steel,.012)
    # A closed equal-spaced perimeter. Groups are tagged for a future slow
    # chase; this draft keeps every bulb steadily on, without keyframes.
    step=.30;nx=math.ceil((u1-u0)/step);nz=math.ceil(((z1-z0)/ZPP)/step)
    points=[]
    for j in range(nx):points.append((u0+(u1-u0)*j/nx,z1))
    for j in range(nz):points.append((u1,z1-(z1-z0)*j/nz))
    for j in range(nx):points.append((u1-(u1-u0)*j/nx,z0))
    for j in range(nz):points.append((u0,z0+(z1-z0)*j/nz))
    new_lights=[]
    for j,(u,z) in enumerate(points):
        b.cylinder('D13 small incandescent socket',xyz(u,v+.019,z),.021,.042,ceramic,(0,-1,0),12)
        b.cylinder('D13 socket brass collar',xyz(u,v+.043,z),.017,.018,brass,(0,-1,0),12)
        ob=b.ball('D13 marquee bulb %02d'%j,xyz(u,v+.067,z),.025,bulb,(1,1.25,1))
        ob['marquee_index']=j;ob['future_chase_group']=j%4;ob['draft_state']='steady warm dim on'
        lamp=b.point('D13 incandescent local spill %02d'%j,xyz(u,v+.075,z),.06,(1,.54,.23),.024);new_lights.append(lamp)

    # Fill the original few-pixel standoff below the sign feet with physical
    # base shoes and anchors; the old truss, braces and tube geometry stay put.
    for u in [3.8,5.6,7.4,9.2,11,12.5]:
        for vv,top in [(v,245),(-2.30,246)]:
            b.box('D13 roof support base plate',u-.13,vv-.11,u+.13,vv+.11,240.28,241.6,steel,.006)
            b.box('D13 anchored support shoe',u-.048,vv-.048,u+.048,vv+.048,241.6,top,steel,.006)
            for du in [-.085,.085]:b.cylinder('D13 roof anchor bolt',xyz(u+du,vv,242.1),.013,1.4/ZPP,brass,vertices=10)

    # Compact period-appropriate rectangular reflector floods. The actual
    # emitting aperture faces its target; the metal shell/yoke sits behind it.
    fixtures=[(4.25,-.33,247,5.10,-.69,366,28),(8.0,-2.60,247,8.70,-.69,363,24),(11.95,-.34,247,10.80,-.69,366,28)]
    for k,(u,vv,z,tu,tv,tz,power) in enumerate(fixtures):
        loc=xyz(u,vv,z);target=xyz(tu,tv,tz);direction=(target-loc).normalized();q=direction.to_track_quat('Z','Y')
        b.box('D13 floodlight roof shoe',u-.14,vv-.13,u+.14,vv+.13,240.28,242,steel,.006)
        line('floodlight adjustable yoke',[(u-.13,vv,241.5),(u-.13,vv,z),(u+.13,vv,z),(u+.13,vv,241.5)],steel,.014)
        b.cube('D13 compact floodlight housing',loc,(.34,.235,.11),steel,.014,q)
        b.cube('D13 recessed aluminium reflector',loc+direction*.057,(.29,.195,.012),reflector,.009,q)
        b.cube('D13 floodlight emitting glass',loc+direction*.066,(.245,.155,.006),lens,.006,q)
        # A wide reflector gives a gentle edge to the uplight; the rear unit
        # also catches the feet and wets the roof with a small warm light pool.
        lamp=b.area('D13 truss reflector flood %d'%k,loc+direction*.076,power,(1,.71,.43),.245,target=target,size_y=.155)
        lamp.data.spread=math.radians(112);new_lights.append(lamp)
        line('floodlight weatherproof cable',[(u,vv,241),(u-.14,vv-.11,241),(u-.30,vv-.11,240.4),(u-.30,-.77,240.4)],rubber,.007)

    # The new practicals illuminate their sign and adjacent roof only. This
    # leaves the accepted exterior/lobby/restroom lighting rigs untouched.
    receivers=bpy.data.collections.new('D13 sign and local roof light receivers');sc.collection.children.link(receivers)
    for ob in sc.objects:
        if ob.type not in ['MESH','CURVE','FONT'] or ob.hide_render:continue
        p=center(ob);u=p.x;vv=-p.y;z=p.z*ZPP
        local=3.3<u<13.1 and -3.1<vv<-.22 and 235<z<440
        large_roof=ob.name in ['P10 single multiplex wet roof','D10 standing water multiplex roof']
        if ob not in original or local or large_roof:receivers.objects.link(ob)
    for lamp in new_lights:lamp.light_linking.receiver_collection=receivers
    for ob in set(sc.objects)-original:
        if ob.type in ['MESH','CURVE'] and any(ma in [bulb,lens] for ma in ob.data.materials):ob.light_linking.receiver_collection=receivers
    print('D13 added',len(points),'dim incandescent bulbs; reflector floods',[f[-1] for f in fixtures],'W; anchored support shoes',flush=True)
    return len(points),[f[-1] for f in fixtures]


def main():
    start=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);backup=TMP/'source_draft12.blend'
    if not backup.exists():shutil.copy2(SOURCE,backup)
    assert not (TMP/'render_started').exists(),'Strict draft: do not repeat a started render'
    bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene;assert sc.get('draft12_brief')
    b.GROUPS.clear();b.M.clear();bpy.context.view_layer.update();bulbs,powers=marquee(sc)
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    sc.render.use_compositing=True;sc.render.filepath=str(QA/'draft_13.png');sc['draft13_brief']='BRIEF-25-draft13.md'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    (TMP/'render_started').write_text(datetime.now().astimezone().isoformat(),encoding='utf-8')
    print('D13 rooftop sign additions saved; rendering one exposure and matching weather',flush=True)
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png';t=time.perf_counter()
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True);beauty_seconds=time.perf_counter()-t
    t=time.perf_counter();rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True);weather_seconds=time.perf_counter()-t
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False);alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_13.png',out);beauty.unlink();weather.unlink()
    (QA/'DRAFT-13.md').write_text(
        '# Draft 13\n\n'
        'Built from saved Draft 12; updated `roxy_pass10_draft.blend`. Rooftop sign additions only; both A/B emote tube sets, lettering, their materials/emission and all prior scene lighting remain unchanged.\n'
        f'Added {bulbs} small incandescent bulbs on a wired perimeter rail just outside the truss, with ceramic sockets/brass collars; warm emission 2.2 and local spill 0.06 W each, below the neon. All lit for this still; four chase groups tagged for future animation, no loop rendered.\n'
        f'Added three modelled rectangular roof reflector floods ({powers[0]}/{powers[1]}/{powers[2]} W, warm RGB 1/0.71/0.43), aimed at the truss/legs/cross-bracing from front and rear, with real wet-roof reflections and local spill. Receiver linking confines them to the sign and nearby roof. Base plates, shoes and bolts connect existing front/rear support feet to the roof; no neon geometry moved.\n'
        f'One delivered image: `draft_13.png`, 1280 x 720, Cycles 256 fixed samples, OptiX denoising, current-scene occluded weather and retained HDR glare. Render time {beauty_seconds:.1f} s beauty + {weather_seconds:.1f} s weather = {beauty_seconds+weather_seconds:.1f} s; total build/composite {time.perf_counter()-start:.1f} s. Inherited drip/crown motion-blur limitation remains unchanged. One STATUS line; stopped.\n',encoding='utf-8')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 13 DINK DONK sign grounded with dim incandescent perimeter, three local reflector floods and anchored feet; neon A/B and letters unchanged; one 720p/256-sample weather-composited draft_13.png; DRAFT-13.md written; stopped.\n')
    print('D13 COMPLETE. ONE IMAGE. STOP.',flush=True)


if __name__=='__main__':main()
