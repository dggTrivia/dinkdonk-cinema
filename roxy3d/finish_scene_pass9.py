"""Final roof readability and a real neighbouring neon tube, before loops."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_scene as b
from common import xyz,render,project
from pass9_common import ROOT,QA,status
from render_scene_pass9 import load,aov,array
import numpy as np

sc=load();b.layer('background')
ma=b.material('P9 readable wet roof felt',(.09,.105,.145),.78,emit=.08,texture=60)
p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.14;p.inputs['Coat Roughness'].default_value=.22
for o in sc.objects:
    if o.name.startswith('P8 gravel roof') and o.location.x<0:
        o.data.materials.clear();o.data.materials.append(ma)
neon=b.material('P9 neighbour neon dim tube',(.03,.22,.13),.3,emit=.4)
ob=bpy.data.objects.get('P9 neighbouring green neon tube') or b.line('P9 neighbouring green neon tube',[xyz(-4.4,8.84,46),xyz(-3.65,8.84,46)],neon,.013)
ob['pass9_surrounding']=True
meta=json.loads((QA/'scene_metadata.json').read_text());meta['neighbour_tube']={'world':[[-4.4,8.84,46],[-3.65,8.84,46]],'points_px':[project(-4.4,8.84,46),project(-3.65,8.84,46)]}
(QA/'scene_metadata.json').write_text(json.dumps(meta,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'))
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.cycles.samples=64
render(QA/'preview_1.png')
status('Final lit preview refined: readable west roof felt and a physical neighbour neon tube; saved before weather loops')
from render_scene_pass9 import holdouts
holdouts()
sc=load();b.set_visibility('background');sc.cycles.samples=96;sc.cycles.adaptive_threshold=.012
for scale,suffix in [(1,''),(2,'@2x')]:
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    aov(sc,QA/('background_position'+suffix));sc.render.use_compositing=True
    render(QA/('steady_bg'+suffix+'.png'))
    np.savez_compressed(QA/('world_positions'+suffix+'.npz'),position=array(next((QA/('background_position'+suffix)).glob('*.exr'))))
    status('Final native background and surface positions refreshed at '+str(1920*scale)+'x'+str(1080*scale))
