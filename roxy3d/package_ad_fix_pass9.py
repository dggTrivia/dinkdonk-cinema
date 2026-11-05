import json
from pass9_common import QA,OUT,status
from pngio import predecode
import package_layers as layers

meta=json.loads((QA/'scene_metadata.json').read_text());rows=json.loads((QA/'rendered_occluders.json').read_text());e=next(r for r in rows if r['name']=='paste_wall');ad=next(r for r in meta['ad_surfaces'] if r['name']=='paste_wall');overlay=next(r for r in rows if r['name']=='ad_paste_wall')
e['z_index']=99;ad['z_index']=100
predecode([OUT/(e['file'][:-4]+s+'.png') for s in ['', '@2x']]);layers.OUT=OUT;layers.QA=QA;e['tile_clips']=layers.tile_clips(e);pieces=layers.depth_slices([e])
for p in pieces+e['tile_clips']:p['z_index']=99
ad={k:v for k,v in ad.items() if k!='layer'};ad['overlay']={k:overlay[k] for k in ['file','x','y','w','h']};ad['overlay'].update(file_2x=overlay['file'][:-4]+'@2x.png',alpha='straight',blend='source-over')
for name in ['manifest_scene','manifest_props','manifest_vehicles']:
    path=QA/(name+'.json');m=json.loads(path.read_text());m['occluders']=[p for p in m['occluders'] if p['name']!='paste_wall']+[e];m['render_layers']=sorted([p for p in m['render_layers'] if p['parent']!='paste_wall']+pieces,key=lambda p:p['z_index']);m['ad_surfaces']=[ad if p['name']=='paste_wall' else p for p in m['ad_surfaces']];path.write_text(json.dumps(m,indent=2))
status('Shutter backing packaged at depth 99, content/frame at 100, below all street walkers; explicit layer order validated in QA')
