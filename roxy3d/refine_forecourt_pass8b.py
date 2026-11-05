"""Material-only correction following the final forecourt comparison."""
import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_scene as b
from common import render
from pass8b_common import ROOT,QA,status,gpu

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'))
sc=bpy.context.scene;gpu(sc)
ma=bpy.data.materials['P8B stained wet alley concrete'];n=ma.node_tree.nodes
next(x for x in n if x.type=='MIX_RGB').inputs[1].default_value=(.018,.022,.026,1)
rough=next(x for x in n if x.type=='MAP_RANGE')
rough.inputs['To Min'].default_value=.18;rough.inputs['To Max'].default_value=.86
p=n.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.10;p.inputs['Coat Roughness'].default_value=.24
sc.render.use_compositing=False
if '--4k-only' not in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'))
    render(QA/'preview_surroundings.png')
    status('Forecourt sheen reduced after final comparison: darker concrete and rougher thin wet coat; corrected lit preview rendered before regenerated loops')
b.GROUPS.clear()
for ob in sc.objects:
    if ob.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(ob.get('layer','background'),[]).append(ob)
b.set_visibility('background');sc.cycles.samples=96;sc.cycles.adaptive_threshold=.012
times=[]
for scale,suffix in [(1,''),(2,'@2x')]:
    if '--4k-only' in sys.argv and scale==1:continue
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    t=time.perf_counter();render(QA/('steady_bg'+suffix+'.png'));times.append({'scale':scale,'seconds':time.perf_counter()-t})
    status('Corrected darker forecourt background rendered at '+str(1920*scale)+'x'+str(1080*scale)+'; geometry and holdout masks unchanged')
(QA/'render_times.json').write_text(json.dumps(times,indent=2))
