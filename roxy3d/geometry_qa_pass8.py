import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import build_pass8 as b
from common import ZPP
from pass8_common import ROOT,QA,status
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8.blend'))
tv=[]
for ob in bpy.context.scene.objects:
    if ob.get('pass8_tv'):
        points=[ob.matrix_world@Vector(p) for p in ob.bound_box]
        rows=[(p.x,-p.y,p.z*ZPP) for p in points]
        tv.append({'name':ob.name,'min':[min(p[i] for p in rows) for i in range(3)],'max':[max(p[i] for p in rows) for i in range(3)]})
(QA/'tv_window_bounds.json').write_text(json.dumps(tv,indent=2))
b.NEW.extend(ob for ob in bpy.context.scene.objects if ob.get('pass8_surrounding'))
b.REGIONS.extend(json.loads((QA/'surroundings_regions.json').read_text()))
b.holdout(2)
status('4K surroundings holdout finished; TV receiver positions exported from final scene')
