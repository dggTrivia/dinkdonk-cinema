"""Read-only source inventory for the layout-3 draft."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from common import ROOT,ZPP
QA=ROOT/'qa10';QA.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass9.blend'))
bpy.context.view_layer.update()
rows=[]
for o in bpy.context.scene.objects:
    if o.type in ['MESH','CURVE','FONT']:
        pts=[o.matrix_world@Vector(c) for c in o.bound_box]
        bb=[min(p.x for p in pts),min(-p.y for p in pts),max(p.x for p in pts),max(-p.y for p in pts),min(p.z for p in pts)*ZPP,max(p.z for p in pts)*ZPP]
    else:bb=[o.location.x,-o.location.y,o.location.x,-o.location.y,o.location.z*ZPP,o.location.z*ZPP]
    rows.append({'name':o.name,'type':o.type,'layer':o.get('layer'),'bounds':[round(x,4) for x in bb],
                 'text':o.data.body if o.type=='FONT' else None,'door_id':o.get('door_id')})
(QA/'source_inventory.json').write_text(json.dumps(rows,indent=2))
files={}
for pack in [ROOT/'out']+sorted(ROOT.glob('out[0-9]*')):
    if not pack.is_dir():continue
    for p in pack.rglob('*'):
        if p.is_file():files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [ROOT/'roxy_pass9.blend',ROOT/'roxy_vehicles_pass9.blend']:
    files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(QA/'protected_sha256.json').write_text(json.dumps(files,indent=2))
print('SOURCE_OBJECTS',len(rows),'PROTECTED_FILES',len(files))
