"""An exposed shutter ad replaces the hidden alley proposal; native sprite layer."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b
import build_pass9 as model
from render_scene_pass9 import load,aov,array,holdouts
from common import render
from pass9_common import ROOT,QA,OUT,status

sc=load();meta=json.loads((QA/'scene_metadata.json').read_text())
for o in list(sc.objects):
    if o.name.startswith('P9 ad ') and 'paste_wall' in o.name:model.rm(o)
for var,name in [('metal','graphite enamel'),('paper','blank poster stock'),('paperlit','backlit blank panel'),('glint','glass glint'),('adglass','advertising glass')]:setattr(model,var,bpy.data.materials['P9 '+name])
b.layer('paste_wall',[-2.50,8.84,-1.54,8.96],40);model.ad('paste_wall','v',-2.42,-1.62,5,37,8.89,False,100,'paste_wall')
ad=model.META['ad_surfaces'][-1];meta['ad_surfaces']=[ad if e['name']=='paste_wall' else e for e in meta['ad_surfaces']]
if 'paste_wall' not in meta['changed_groups']:meta['changed_groups'].append('paste_wall')
for o in sc.objects:
    if o.get('layer') in ['paste_wall','ad_paste_wall']:o['pass9_surrounding']=True
meta['paste_wall_surface']={'footprint':[-2.50,8.84,-1.54,8.96],'height_px':40,'z_index':99}
(QA/'scene_metadata.json').write_text(json.dumps(meta,indent=2));sc.render.use_compositing=False;sc.render.use_border=False;sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.cycles.samples=64
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'));render(QA/'preview_1.png')
status('Hidden alley ad replaced with an exposed NOODLES shutter paste-up surface; final lit preview refreshed')
rows=json.loads((QA/'rendered_occluders.json').read_text())
for name in ['paste_wall','ad_paste_wall']:
    b.set_visibility(name);x,y,x1,y1=b.bounds_for(name,6);entry=dict(name=name,file='occ_'+name+'.png',x=x,y=y,w=x1-x,h=y1-y)
    if name=='paste_wall':entry.update(meta['paste_wall_surface'])
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale;sc.render.use_border=True;sc.render.use_crop_to_border=True
        sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x1+.1)/1920;sc.render.border_min_y=(1080-y1+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
        folder=QA/'positions_exr'/(name+suffix);aov(sc,folder);sc.render.use_compositing=True;render(OUT/('occ_'+name+suffix+'.png'))
        np.savez_compressed(QA/'positions'/(name+suffix+'.npz'),uv=array(next(folder.glob('*.exr')))[:,:,:2])
    rows=[r for r in rows if r['name']!=name]+[entry]
(QA/'rendered_occluders.json').write_text(json.dumps(rows,indent=2))
status('Exposed shutter ad surface and frame/glass overlay rendered at native 1x/2x with ownership positions')
holdouts()
