import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from common import NORMAL
from pass9_common import ROOT,QA
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'))
rows=[]
for o in bpy.context.scene.objects:
    if o.type=='FONT' or any(s in o.name.lower() for s in ['billboard','restroom sign','marquee','gate cyan','route enamel','roxy','records']):
        rows.append({'name':o.name,'type':o.type,'layer':o.get('layer'),'loc':list(o.location),'body':o.data.body if o.type=='FONT' else '',
        'camera_facing':float((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(NORMAL))})
(QA/'scene_inventory.json').write_text(json.dumps(rows,indent=2))
for r in rows:print(r['name'],r['layer'],r['body'],round(r['camera_facing'],3),flush=True)
