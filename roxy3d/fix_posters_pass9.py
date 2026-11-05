"""Place complete one-sheets ahead of the wainscot; rerender native static patches."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
import build_scene as b
from common import render
from render_scene_pass9 import load,aov,array
from build_pass9 import quad
from pass9_common import ROOT,QA,status
from pngio import read,write,predecode

sc=load();meta=json.loads((QA/'scene_metadata.json').read_text())
if not sc.get('pass9_posters_forward'):
    for o in sc.objects:
        if o.name.startswith(('P9 one-sheet aperture','P9 one-sheet frame','P9 poster bulb socket')):
            shift=.06 if o.name.startswith('P9 one-sheet aperture') else .05
            if o.location.x<.5:o.location.x+=shift
            else:o.location.y-=shift
    for e in meta['poster_frames']:
        e['offset']=.072;e['quad_px']=quad(e['wall'][0],*e['along'],*e['z_px'],.072)
    for e,p in zip(meta['poster_bulbs'],meta['poster_frames']):
        dx=3 if p['wall']=='u0' else -3
        e['points_px']=[[x+dx,y+1.5] for x,y in e['points_px']]
    sc['pass9_posters_forward']=True
    (QA/'scene_metadata.json').write_text(json.dumps(meta,indent=2))
    m=json.loads((QA/'manifest_scene.json').read_text());m['poster_frames']=meta['poster_frames'];(QA/'manifest_scene.json').write_text(json.dumps(m,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'))
sc.cycles.samples=64;sc.render.resolution_x=1920;sc.render.resolution_y=1080
render(QA/'preview_1.png')
status('Poster faces/frames moved ahead of wainscot; full 27:40 apertures now visible in revised lit preview')
b.set_visibility('background');sc.cycles.samples=96;rects=[]
for e in meta['poster_frames']:
    q=e['quad_px'];xs,ys=zip(*q);x=math.floor(min(xs))-14;y=math.floor(min(ys))-14;x1=math.ceil(max(xs))+14;y1=math.ceil(max(ys))+14
    rects.append([x,y,x1,y1])
for scale,suffix in [(1,''),(2,'@2x')]:
    predecode([QA/('steady_bg'+suffix+'.png')]);bg=read(QA/('steady_bg'+suffix+'.png'));pos=np.load(QA/('world_positions'+suffix+'.npz'))['position']
    for j,(x,y,x1,y1) in enumerate(rects):
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale;sc.render.use_border=True;sc.render.use_crop_to_border=True
        sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x1+.1)/1920;sc.render.border_min_y=(1080-y1+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
        folder=QA/'poster_patch_positions'/('p'+str(j)+suffix);aov(sc,folder);sc.render.use_compositing=True
        target=QA/'poster_patches'/('p'+str(j)+suffix+'.png');render(target);predecode([target]);p=read(target)
        bg[y*scale:y1*scale,x*scale:x1*scale]=p;pos[y*scale:y1*scale,x*scale:x1*scale]=array(next(folder.glob('*.exr')))
    pending=QA/('steady_bg'+suffix+'.pending.png');write(pending,bg);pending.replace(QA/('steady_bg'+suffix+'.png'))
    pending=QA/('world_positions'+suffix+'.pending.npz');np.savez_compressed(pending,position=pos);pending.replace(QA/('world_positions'+suffix+'.npz'))
(QA/'poster_patch_rects.json').write_text(json.dumps(rects))
status('Five corrected poster surfaces rerendered at native 1x/2x into static background and surface-position patches; outdoor weather remains unchanged')
