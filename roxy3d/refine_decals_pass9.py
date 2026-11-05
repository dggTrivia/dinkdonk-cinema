import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b
from render_scene_pass9 import load,aov,array
from common import render
from pass9_common import ROOT,QA,OUT,status
sc=load()
for name in ['P9 opening hours','P9 no smoking']:bpy.data.objects[name].location.x=6.8
sc.cycles.samples=64;sc.render.resolution_x=1920;sc.render.resolution_y=1080
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'));render(QA/'preview_1.png')
b.set_visibility('glass_left');x,y,x1,y1=b.bounds_for('glass_left',6)
rows=json.loads((QA/'rendered_occluders.json').read_text());e=next(e for e in rows if e['name']=='glass_left');assert [x,y,x1-x,y1-y]==[e[k] for k in ['x','y','w','h']]
for scale,suffix in [(1,''),(2,'@2x')]:
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale;sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x1+.1)/1920;sc.render.border_min_y=(1080-y1+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
    folder=QA/'positions_exr'/('glass_left'+suffix);aov(sc,folder);sc.render.use_compositing=True;render(OUT/('occ_glass_left'+suffix+'.png'))
    np.savez_compressed(QA/'positions'/('glass_left'+suffix+'.npz'),uv=array(next(folder.glob('*.exr')))[:,:,:2])
status('Hours/no-smoking decals moved into a clear glass pane; lit preview and native glass sprites refreshed without changing footprints or canvases')
