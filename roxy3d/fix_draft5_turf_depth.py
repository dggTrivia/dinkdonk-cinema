import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft5_common import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
o=bpy.data.objects['D5 art turf']
for v in o.data.vertices:v.co.y=.048
o.data.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
meta=json.loads((WORK/'scene.json').read_text())
for row in meta['art']:
    if row['key']=='turf':row['wall_extent'][2]=-.048
report('scene.json',meta)
status('turf-war paint moved 0.012 world units onto the front of the existing paste-up panel; physical wet geometry and all other scene content unchanged')
