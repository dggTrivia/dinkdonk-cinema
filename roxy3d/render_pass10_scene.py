"""Native backgrounds, foreground parents and ownership AOVs for layout 3."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b,build_pass8 as city,depth_pass
from common import render
from pass8_common import gpu
from pass10_common import ROOT,QA,OUT,LIVE,status
from render_scene_pass9 import array

def load():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10.blend'));sc=bpy.context.scene;gpu(sc);b.GROUPS.clear()
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o);o.hide_render=False;o.visible_camera=True;o.is_holdout=False
    sc.render.use_compositing=False;sc.render.use_border=False;sc.render.use_crop_to_border=False
    return sc
def aov(sc,folder):
    for e in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(e)
    return depth_pass.configure(sc,folder)
def crop(sc,r,scale):
    x,y,w,h=r
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x+w+.1)/1920
    sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
def holdouts():
    for scale in [1,2]:
        sc=load();city.QA=QA;city.status=status;city.NEW.clear();city.REGIONS.clear()
        city.NEW.extend(o for o in sc.objects if o.get('pass10_surrounding'))
        city.REGIONS.append({'name':'single multiplex roof','polygon_uv':json.loads((QA/'scene_metadata_final.json').read_text())['multiplex']['footprint_polygon_uv'],'roof_z':240})
        def fast_render(p):sc.cycles.device='GPU';render(p)
        city.render=fast_render;city.holdout(scale)
    status('Independent 1080p/4K holdouts passed for the expanded multiplex and retained surroundings')
def backgrounds():
    sc=load();b.set_visibility('background');sc.cycles.samples=64;sc.cycles.adaptive_threshold=.015
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        folder=QA/('background_position_final'+suffix);aov(sc,folder);sc.render.use_compositing=True
        render(QA/('steady_bg'+suffix+'.png'));p=array(next(folder.glob('*.exr')))
        np.savez_compressed(QA/('world_positions'+suffix+'.npz'),position=p)
        status('Native %dx%d lit background and world-position AOV rendered'%(1920*scale,1080*scale))
def foreground():
    meta=json.loads((QA/'scene_metadata_final.json').read_text());sc=load();sc.cycles.samples=48;sc.cycles.adaptive_threshold=.018
    specs=meta['production_occluders']+[dict(name=e['layer']) for e in meta['ad_surfaces']]
    records=json.loads((QA/'rendered_occluders_final.json').read_text()) if (QA/'rendered_occluders_final.json').exists() else []
    done={e['name'] for e in records}
    for spec in specs:
        name=spec['name']
        if name in done:continue
        b.set_visibility(name);bpy.context.view_layer.update();x,y,x1,y1=b.bounds_for(name,6);w=x1-x;h=y1-y
        if w<=0 or h<=0:raise RuntimeError(('empty crop',name,x,y,w,h))
        e=dict(spec,file='occ_'+name+'.png',file_2x='occ_'+name+'@2x.png',x=x,y=y,w=w,h=h)
        for scale,suffix in [(1,''),(2,'@2x')]:
            crop(sc,[x,y,w,h],scale);folder=QA/'positions_exr_final'/(name+suffix);aov(sc,folder);sc.render.use_compositing=True
            render(OUT/('occ_'+name+suffix+'.png'));p=array(next(folder.glob('*.exr')))
            dest=QA/'positions'/(name+suffix+'.npz');dest.parent.mkdir(exist_ok=True);np.savez_compressed(dest,uv=p[:,:,:2])
        records.append(e);(QA/'rendered_occluders_final.json').write_text(json.dumps(records,indent=2));status('Foreground parent + native 1x/2x ownership AOV complete: '+name)
def main():
    mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
    if mode in ['all','background']:holdouts();backgrounds()
    if mode in ['all','foreground']:foreground()
if __name__=='__main__':main()
