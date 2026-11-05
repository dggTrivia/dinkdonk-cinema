import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft6_common import *
from build_pass10_draft import bounds
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
sc=bpy.context.scene;rows=[]
for name in ['P8 right service alley','D6 broken heaved alley ground','D6 uneven cold asphalt repair','D6 broken asphalt fissure','D6 wet newspaper spread','D6 water filled pothole','D6 flattened soggy cardboard']:
    o=sc.objects[name];ma=o.data.materials[0]
    row={'name':name,'bounds':bounds(o),'location':list(o.location),'mat':ma.name,'hide':o.hide_render,'visible_camera':o.visible_camera,'backface':ma.use_backface_culling,'nodes':[],'collections':[c.name for c in o.users_collection]}
    for n in ma.node_tree.nodes:
        if n.type in ['BSDF_PRINCIPLED','MIX_SHADER','OUTPUT_MATERIAL','ATTRIBUTE','DISPLACEMENT']:
            row['nodes'].append({'name':n.name,'type':n.type,'inputs':{i.name:([l.from_node.name for l in i.links] if i.is_linked else str(i.default_value) if hasattr(i,'default_value') else '') for i in n.inputs}})
    if o.type=='MESH':row['first_vertices']=[list(o.matrix_world@v.co) for v in list(o.data.vertices)[:5]];row['normals']=[list(p.normal) for p in list(o.data.polygons)[:2]]
    rows.append(row)
report('ground_inspect.json',rows)
