import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10.blend'))
rows=[]
for o in bpy.context.scene.objects:
    if o.get('anim_id') or o.get('bell_id'):
        key='closed_matrix' if o.get('anim_id') else 'bell_original_matrix'
        a=list(o.get(key,[]));r={'name':o.name,'id':o.get('anim_id',o.get('bell_id')),'type':o.type,'stored_translation':[a[3],a[7],a[11]] if a else None,'current_translation':list(o.matrix_world.translation)}
        if o.type=='MESH':rows.append(r)
(ROOT/'qa10/animation_matrix_audit.json').write_text(json.dumps(rows,indent=2))
for r in rows:
    if 'closed ' in r['name'] or 'rounded tube end' in r['name']:print(r)
