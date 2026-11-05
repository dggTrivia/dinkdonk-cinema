"""Brief 19: relocate EatFresh; one fixed-camera weather-composited draft."""
import sys, math, shutil
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Matrix, Vector
import build_scene as b
from common import ROOT, xyz, ZPP
from build_pass10_draft4 import quality
from build_pass10_draft7 import rain_layer, link_exterior
from pass8_common import gpu
from pngio import read, write

QA=ROOT/'qa10'
TMP=ROOT/'cache'/'draft8'

def move_eatfresh(sc):
    # Old face: v=-3.55, u=10..12.7. New face: u=-.7,
    # v=3.15..0.45 (left to right), beside WCAT's v=7.5..3.6.
    # The shorter supports put every corner inside the unchanged camera.
    turn=Matrix.Translation(Vector((2.85,-13.15,-29/ZPP))) @ Matrix.Rotation(math.pi/2,4,'Z')
    moved=[]
    for o in list(sc.objects):
        if o.name.startswith(('P10 roof billboard leg','P10 roof billboard rear brace')):
            bpy.data.objects.remove(o,do_unlink=True)
        elif o.name.startswith(('P10 roof billboard','D7 EatFresh')):
            o.matrix_world=turn @ o.matrix_world
            o['layer']='draft8_apartment_eatfresh'
            moved.append(o)
            col=bpy.data.collections.get('P10 multiplex roof light receivers')
            if col and o.name in col.objects:col.objects.unlink(o)
    # Surface water belonging to the moved billboard follows its geometry.
    # Rooftop HVAC water below the board is outside this selection.
    def on_old_board(p):
        return 9.94<=p.x<=12.76 and -3.71<=-p.y<=-3.47 and 279<=p.z*ZPP<=363
    for name in ['D5 physical surface beads','D5 periodic wet micro impacts']:
        ob=sc.objects.get(name)
        if ob and ob.type=='MESH':
            inv=ob.matrix_world.inverted()
            for vertex in ob.data.vertices:
                p=ob.matrix_world@vertex.co
                if on_old_board(p):vertex.co=inv@(turn@p)
            ob.data.update()
    for name in ['D5 metal and cap splash crowns','D5 hem edge drips and glass runnels']:
        ob=sc.objects.get(name)
        if ob and ob.type=='CURVE':
            inv=ob.matrix_world.inverted()
            for spline in ob.data.splines:
                points=list(spline.points)
                if points and any(on_old_board(ob.matrix_world@Vector(p.co[:3])) for p in points):
                    for p in points:p.co=(*(inv@(turn@(ob.matrix_world@Vector(p.co[:3])))),1)
    b.layer('draft8_apartment_eatfresh');before=set(sc.objects)
    steel=bpy.data.materials['D7 weathered billboard steel']
    brass=bpy.data.materials['D7 antique gold foil']
    lens=bpy.data.materials['D7 warm lamp lens']
    def box(n,*a):return b.box('D8 EatFresh '+n,*a)
    def line(n,pts,r=.02):return b.line('D8 EatFresh '+n,[xyz(*p) for p in pts],steel,r)
    for v in [.70,2.90]:
        box('bolted roof foot',-.95,v-.12,-.57,v+.12,235.18,238.0,steel,.008)
        line('upright',[(-.75,v,238),(-.75,v,328)],.025)
        line('rear diagonal brace',[(-1.65,v,237),(-.76,v,323)],.018)
        box('brace anchor',-1.78,v-.11,-1.54,v+.11,235.18,237.5,steel,.006)
        for u in [-.90,-.62]:b.ball('D8 EatFresh roof anchor bolt',xyz(u,v,239),.015,brass,(1,1,.45))
    # The existing downlight moves with the sign; give it a visible mounting.
    line('gooseneck lamp arm',[(-.77,1.80,321),(-.77,1.80,337),(-.74,1.80,343),(-.65,1.80,347),(-.48,1.80,347),(-.33,1.80,344),(-.25,1.80,340)],.016)
    b.ball('D8 EatFresh lamp shade',xyz(-.25,1.8,341.2),.105,steel,(1.35,1,.45))
    b.ball('D8 EatFresh lamp lens',xyz(-.25,1.8,338.8),.075,lens,(1.2,1,.14))
    lamp=sc.objects.get('P10 roof billboard lamp')
    if lamp:
        lamp.name='D8 EatFresh apartment billboard downlight'
        lamp.data.energy=14;lamp.data.size=.60
        lamp.location=xyz(-.25,1.8,338.1)
        lamp.rotation_euler=(xyz(-.69,1.8,290)-lamp.location).to_track_quat('-Z','Y').to_euler()
    link_exterior(moved+list(set(sc.objects)-before),apartment=True)

def main():
    TMP.mkdir(parents=True,exist_ok=True)
    source=ROOT/'roxy_pass10_draft.blend';backup=TMP/'source_draft7.blend'
    if not backup.exists():shutil.copy2(source,backup)
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
    b.GROUPS.clear();b.M.clear()
    move_eatfresh(sc)
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    # Retain Draft 7's approved HDR compositor verbatim.
    sc.render.use_compositing=True
    sc['draft8_only']=True;sc['draft8_brief']='BRIEF-19-draft8.md'
    sc.render.filepath=str(QA/'draft_8.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    print('D8 model saved; rendering one fixed-camera draft and its weather layer',flush=True)
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png'
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True)
    rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True)
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False)
    alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8)
    write(QA/'draft_8.png',out)
    beauty.unlink();weather.unlink()
    (QA/'DRAFT-8.md').write_text(
        '# Draft 8\n\n'
        'Built from the saved Draft 7 scene; updated `roxy_pass10_draft.blend`.\n'
        'Moved the complete EatFresh billboard to the right of WCAT on the apartment roof, with matching facing, a clear gap, fitted uprights, bolted feet, rear braces and a mounted downlight. Its artwork and proportions are preserved; the cinema-roof billboard and supports are gone.\n'
        'Delivered one fixed-camera `draft_8.png`: 1280×720, Cycles 256 samples, retained wet materials, soft ray-traced ripples/reflections and HDR glare, with the current-scene occluded weather frame composited.\n'
        'Stopped after this image, this note and one STATUS line; no additional views, clips, audits, rerenders or out10 work.\n',encoding='utf-8')
    stamp=datetime.now().astimezone().isoformat(timespec='seconds')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:
        f.write(stamp+' | Finished: Draft 8 owner fix 47; EatFresh beside WCAT on the apartment roof; saved draft model and one 1280×720 / 256-sample weather-composited draft_8.png; DRAFT-8.md written; stopped.\n')
    print('D8 COMPLETE: qa10/draft_8.png, DRAFT-8.md, one STATUS line. STOP.',flush=True)

if __name__=='__main__':main()
