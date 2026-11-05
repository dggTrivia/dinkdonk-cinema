import sys,time,random,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b
from common import xyz
from build_pass10_draft4 import quality
from pass8_common import gpu
from draft6_common import *
from pngio import read,write,predecode
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc);sc.cycles.use_denoising=True
for o in sc.objects:
    if o.type in ['MESH','CURVE','FONT']:o.is_holdout=True
b.GROUPS.clear();b.layer('draft6_weather');rng=random.Random(161005)
ma=b.glass('D6 airborne rain',(.45,.54,.64),.24);p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.15;p.inputs['Coat Weight'].default_value=.6;p.inputs['Emission Color'].default_value=(.12,.16,.22,1);p.inputs['Emission Strength'].default_value=.15
regions=[(-12,9.18,23,13.5,.12,640),(-5,-1,-.075,8.7,235.2,120),(-4,-13,25,-.23,240.2,500),(13.08,.05,15,9,.08,80),(15,.6,17.5,6.4,58.1,35),(15,6.5,17.5,9.1,61.1,30),(-9.4,3.4,-5.1,7.35,95.1,30)]
for u0,v0,u1,v1,z,n in regions:
    for i in range(n):
        u=rng.uniform(u0,u1);v=rng.uniform(v0,v1);zz=z+rng.uniform(3,190);length=rng.uniform(5,18)
        o=b.line('D6 airborne current rain',[xyz(u,v,zz),xyz(u+.018,v-.006,zz-length)],ma,rng.uniform(.0015,.0037));o.is_holdout=False;o.visible_shadow=False
        for cname in ['P8 surroundings light receivers','P10 multiplex roof light receivers']:
            col=bpy.data.collections.get(cname)
            if col and o.name not in col.objects:col.objects.link(o)
sc.render.film_transparent=True;sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.filepath=str(WORK/'weather_overlay.png');st=time.perf_counter();bpy.ops.render.render(write_still=True)
predecode([QA/'draft_6_clean.png',WORK/'weather_overlay.png']);a=read(QA/'draft_6_clean.png');rain=read(WORK/'weather_overlay.png');alpha=rain[:,:,3:4].astype(np.float32)/255;out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+rain[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_6.png',out)
report('weather.json',{'source_sha256':hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest(),'seconds':time.perf_counter()-st,'samples':256,'current_scene_occlusion':True,'airborne_streaks':sum(q[-1] for q in regions),'splashes':'physical beads/crowns/drips already rendered in the current clean beauty, no old splash plate','beauty':'draft_6_clean.png','final':'draft_6.png'})
status('draft_6.png weather composite finished over the current 256-sample clean frame, with freshly occluded 3D airborne rain')
