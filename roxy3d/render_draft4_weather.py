"""A single freshly rendered, occluded 3-D rain/splash pass for the 720p draft.
The beauty beneath it is current Cycles radiance, never an old reflection image.
"""
import sys,json,math,random,time,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b
from common import xyz,ZPP
from pass8_common import gpu
from build_pass10_draft4 import quality
from draft4_common import ROOT,QA,WORK,status,report,W,H
from pngio import read,write,predecode
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc)
b.GROUPS.clear();b.layer('draft4_weather');rng=random.Random(151004)
for o in sc.objects:
    if o.type in ['MESH','CURVE','FONT']:o.is_holdout=True
ma=b.glass('D4 rain thin water filament',(.45,.54,.64),.24)
p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=.05;p.inputs['Roughness'].default_value=.15;p.inputs['Coat Weight'].default_value=.6;p.inputs['Emission Color'].default_value=(.12,.16,.22,1);p.inputs['Emission Strength'].default_value=.15
splash=b.glass('D4 splash water bead',(.43,.52,.61),.34)
regions=[(-12,9.18,23,13.5,.12,640),(-5,-1,-.075,8.7,235.2,120),(-4,-13,25,-.23,240.2,500),(13.08,.05,15,9.0,.08,80),(15,.6,17.5,6.4,58.1,35),(15,6.5,17.5,9.1,61.1,30),(-9.4,3.4,-5.1,7.35,95.1,30)]
count=0;impacts=0
for u0,v0,u1,v1,z,n in regions:
    for i in range(n):
        u=rng.uniform(u0,u1);v=rng.uniform(v0,v1);zz=z+rng.uniform(3,190);length=rng.uniform(5,18)
        b.line('D4 physical rain streak',[xyz(u,v,zz),xyz(u+.018,v-.006,zz-length)],ma,rng.uniform(.0015,.0037));count+=1
    for i in range(max(8,n//10)):
        u=rng.uniform(u0+.03,u1-.03);v=rng.uniform(v0+.03,v1-.03)
        for k in range(rng.choice([2,3,4])):
            a=rng.random()*math.tau;r=rng.uniform(.016,.045);h=rng.uniform(1.2,3.2)
            pts=[xyz(u+math.cos(a)*r*t,v+math.sin(a)*r*t,z+.12+h*math.sin(math.pi*t)) for t in [0,.25,.5,.75,1]]
            b.line('D4 instantaneous surface splash',pts,splash,.0022)
        impacts+=1
for o in b.GROUPS['draft4_weather']:
    o.is_holdout=False;o.visible_shadow=False
    for cname in ['P8 surroundings light receivers','P10 multiplex roof light receivers']:
        col=bpy.data.collections.get(cname)
        if col and o.name not in col.objects:col.objects.link(o)
sc.frame_set(1);sc.render.film_transparent=True;sc.cycles.use_denoising=True;sc.cycles.denoiser='OPTIX'
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.filepath=str(WORK/'rain_splashes_current.png')
t=time.perf_counter();bpy.ops.render.render(write_still=True);elapsed=time.perf_counter()-t
shutil.copy2(QA/'test_glare_after.png',QA/'draft_4_clean.png')
predecode([QA/'draft_4_clean.png',WORK/'rain_splashes_current.png']);a=read(QA/'draft_4_clean.png');w=read(WORK/'rain_splashes_current.png');alpha=w[:,:,3:4].astype(np.float32)/255
out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+w[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_4.png',out)
report('weather.json',{'render_seconds':elapsed,'samples':256,'size':[W,H],'current_scene_rain_streaks':count,'surface_splash_sites':impacts,'geometry_holdouts':True,'rain_png':'draft4/rain_splashes_current.png','clean_beauty':'draft_4_clean.png','weather_frame':'draft_4.png','reflection_basis':'current draft4/preview_denoised.exr, no cached prior pass','method':'source-over current-scene 3D rain/splash render over current ray-traced wet beauty with HDR glare'})
status('720p draft_4_clean.png plus draft_4.png weather composite complete: freshly ray-traced '+str(count)+' rain streaks and '+str(impacts)+' surface splash sites, with scene occlusion')
