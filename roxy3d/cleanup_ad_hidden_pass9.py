import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from render_scene_pass9 import load
from pass9_common import ROOT,QA,OUT,status
from pngio import read,predecode
sc=load();rows=json.loads((QA/'rendered_occluders.json').read_text());overlay=next(e for e in rows if e['name']=='ad_paste_wall')
for s,suffix in [(1,''),(2,'@2x')]:
    p=OUT/('occ_ad_paste_wall'+suffix+'.png');predecode([p]);a=read(p)
    # Former proposal is wholly hidden by the old facade; retain the larger
    # transparent crop so no published native sprite bounds need changing.
    x0=max(0,123-overlay['x'])*s;x1=min(overlay['w'],186-overlay['x'])*s;y0=max(0,305-overlay['y'])*s;y1=min(overlay['h'],396-overlay['y'])*s
    assert a[y0:y1,x0:x1,3].max(initial=0)==0
removed=[]
for o in list(sc.objects):
    if o.name.startswith('P9 ad ') and 'paste_wall' in o.name and o.location.x<-3:
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
meta=json.loads((QA/'scene_metadata.json').read_text());meta['paste_wall_surface']['z_index']=99
for e in meta['ad_surfaces']:
    if e['name']=='paste_wall':e['z_index']=99
meta['removed_hidden_ad_frames']=removed;(QA/'scene_metadata.json').write_text(json.dumps(meta,indent=2))
for e in rows:
    if e['name']=='paste_wall':e['z_index']=100
(QA/'rendered_occluders.json').write_text(json.dumps(rows,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'))
status('Invisible remnants of the discarded alley ad removed from the source scene; their delivered overlay pixels verified fully transparent at both resolutions')
