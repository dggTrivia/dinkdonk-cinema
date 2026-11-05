"""Normalize packed paths and audit geometry without rendering."""
import sys,json,re,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE/'bundle';sys.path.insert(0,str(ROOT))
from common import ZPP
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'));sc=bpy.context.scene
sc.render.filepath='//work/render'
for group in bpy.data.node_groups:
    if group.bl_idname=='CompositorNodeTree':
        for n in group.nodes:
            if n.type=='OUTPUT_FILE':n.directory='//work/compositor'
for o in bpy.data.objects:
    for k in list(o.keys()):
        if isinstance(o[k],str) and re.search(r'[A-Za-z]:[\\/]',o[k]):del o[k]
for k in list(sc.keys()):
    if isinstance(sc[k],str) and re.search(r'[A-Za-z]:[\\/]',sc[k]):del sc[k]
for im in bpy.data.images:
    if im.source=='FILE':
        im.filepath=im.filepath.replace('\\','/');assert im.packed_file and im.filepath.startswith('//assets/'),(im.name,im.filepath)
for f in bpy.data.fonts:
    if f.filepath!='<builtin>':
        f.filepath=f.filepath.replace('\\','/');assert f.packed_file and f.filepath.startswith('//assets/'),(f.name,f.filepath)
assert not bpy.data.libraries
colliders=[]
for o in sc.objects:
    if o.type not in ['MESH','CURVE','FONT']:continue
    g=o.get('cloud_group','background')
    if not g.startswith('restroom_') or o.get('anim_id'):continue
    p=[o.matrix_world@Vector(c) for c in o.bound_box];bounds=[min(t.x for t in p),min(-t.y for t in p),max(t.x for t in p),max(-t.y for t in p),min(t.z for t in p)*ZPP,max(t.z for t in p)*ZPP]
    if bounds[5]>8:colliders.append({'name':o.name,'group':g,'bounds':bounds})
(ROOT/'assets/restroom_colliders.json').write_text(json.dumps(colliders,indent=2),encoding='utf-8')
sc.render.use_file_extension=True;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scene.blend'),relative_remap=False)
info=json.loads((ROOT/'bundle.json').read_text());info['scene_sha256']=hashlib.sha256((ROOT/'scene.blend').read_bytes()).hexdigest();info['paths_relative']=True;info['linked_libraries']=0
(ROOT/'bundle.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print('PORTABILITY_NORMALIZED',json.dumps(info),flush=True)
