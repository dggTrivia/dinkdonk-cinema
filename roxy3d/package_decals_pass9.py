import json
from pass9_common import QA,OUT,status
from pngio import predecode
import package_layers as layers
e=next(e for e in json.loads((QA/'rendered_occluders.json').read_text()) if e['name']=='glass_left')
predecode([OUT/(e['file'][:-4]+s+'.png') for s in ['', '@2x']]);layers.OUT=OUT;layers.QA=QA;e['tile_clips']=layers.tile_clips(e);pieces=layers.depth_slices([e])
for name in ['manifest_scene','manifest_props','manifest_vehicles']:
    path=QA/(name+'.json');m=json.loads(path.read_text());m['occluders']=[e if p['name']=='glass_left' else p for p in m['occluders']];m['render_layers']=sorted([p for p in m['render_layers'] if p['parent']!='glass_left']+pieces,key=lambda p:p['z_index']);path.write_text(json.dumps(m,indent=2))
status('Refined glass pixels resliced from native ownership AOVs; water loops retain their established pane depths')
