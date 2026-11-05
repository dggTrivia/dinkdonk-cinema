"""Compare actual saved carpet geometry and material graphs, and camera projection."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT,project,xyz
from bpy_extras.object_utils import world_to_camera_view

def value(v):
    if isinstance(v,(str,int,float,bool)):return v
    try:return list(v)
    except TypeError:return str(v)

def carpet(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));result={}
    for ob in bpy.context.scene.objects:
        if 'carpet' not in ob.name.lower() and not ob.name.startswith('Runner brass thread'):continue
        materials=[]
        for mat in ob.data.materials:
            nodes=[{'name':n.name,'type':n.bl_idname,'inputs':[(s.name,value(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],
                'options':{k:value(getattr(n,k)) for k in ['operation','blend_type','noise_dimensions','normalize'] if hasattr(n,k)}} for n in mat.node_tree.nodes]
            links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links]
            materials.append({'name':mat.name,'nodes':nodes,'links':links})
        geometry=[[float(x) for x in v.co] for v in ob.data.vertices] if ob.type=='MESH' else [[list(p.co) for p in s.points] for s in ob.data.splines]
        item={'matrix':[list(r) for r in ob.matrix_world],'geometry':geometry,'materials':materials}
        result[ob.name]=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
    return result

old=carpet(ROOT/'roxy_pass4.blend');new=carpet(ROOT/'roxy_pass6.blend');assert old==new,'Carpet changed'
sc=bpy.context.scene;checks=[]
for u,v,z in [(0,0,0),(13,9,0),(0,6.4,114),(4.8,0,114),(.35,9.6,84)]:
    p=world_to_camera_view(sc,sc.camera,xyz(u,v,z));xy=[p.x*1920,(1-p.y)*1080];expected=project(u,v,z)
    error=max(abs(a-b) for a,b in zip(xy,expected));assert error<.002
    checks.append({'uvz':[u,v,z],'projected':xy,'expected':expected,'error':error})
(ROOT/'qa6/scene_contract_validation.json').write_text(json.dumps({'passed':True,'carpet_objects':len(new),'carpet_hashes':new,'carpet_identical_to_pass4':True,'projection':checks},indent=2))
print('PASS6_CARPET_IDENTICAL',len(new),flush=True)
