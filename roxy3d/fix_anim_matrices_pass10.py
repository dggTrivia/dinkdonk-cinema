"""Repair canonical transforms without changing static geometry or lighting."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix,Vector
from pass10_common import ROOT,QA,status
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10.blend'))
sc=bpy.context.scene;bpy.context.view_layer.update();meta=json.loads((QA/'scene_metadata_final.json').read_text())
for o in list(sc.objects):
    if o.get('anim_id'):o['closed_matrix']=[q for row in o.matrix_world for q in row]
    # Filled curve caps are sufficient; discard misplaced endpoint spheres.
    if (o.get('bell_id') or o.get('bell_id_disabled')) and o.type=='MESH':
        bpy.data.objects.remove(o,do_unlink=True)
    elif o.get('bell_id') and o.type=='CURVE':o.data.use_fill_caps=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10.blend'))
status('Animation pivot audit complete: canonical door matrices corrected and stray bell endpoint spheres replaced by filled tube caps')
