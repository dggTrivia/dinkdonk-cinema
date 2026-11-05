"""Read-only audit of the saved editable draft's geometry and shader contract."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft4_common import ROOT,WORK,report,status
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
sc=bpy.context.scene;roof=bpy.data.objects['D4 one continuous apartment felt roof'];parapet=bpy.data.objects['D4 single perimeter apartment parapet']
assert len(roof.data.vertices)==4 and len(roof.data.polygons)==1
assert roof.data.materials[0].name=='D3 mottled mineral felt'
adj={i:set() for i in range(len(parapet.data.vertices))}
for edge in parapet.data.edges:
    a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
seen=set();todo=[0]
while todo:
    a=todo.pop()
    if a in seen:continue
    seen.add(a);todo.extend(adj[a]-seen)
assert len(seen)==len(parapet.data.vertices)
group=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals']
hashed_periods=[n for n in group.nodes if n.bl_idname=='ShaderNodeMath' and n.operation=='GREATER_THAN']
assert len(hashed_periods)==9
assert all(n.inputs[0].is_linked and n.inputs[0].links[0].from_node.bl_idname=='ShaderNodeTexWhiteNoise' for n in hashed_periods)
materials=[]
for ma in bpy.data.materials:
    if ma.node_tree and any(n.type=='GROUP' and n.node_tree==group for n in ma.node_tree.nodes):materials.append(ma.name)
sidewalk=[o for o in sc.objects if o.name.startswith('Wet paving slab')]
assert sidewalk and all(any(ma.name in materials for ma in o.data.materials if ma) for o in sidewalk)
animated=[]
for block in list(bpy.data.objects)+list(bpy.data.materials)+list(bpy.data.node_groups)+[sc]:
    ad=getattr(block,'animation_data',None)
    if ad and (ad.action or len(ad.drivers)):animated.append({'name':block.name,'action':ad.action.name if ad.action else None,'drivers':len(ad.drivers)})
result={'roof_vertices':4,'roof_faces':1,'roof_material':roof.data.materials[0].name,'parapet_connected_vertices':len(seen),'parapet_total_vertices':len(parapet.data.vertices),'hashed_cell_periods':len(hashed_periods),'ripple_materials':materials,'wet_sidewalk_slabs_with_ripple_normals':len(sidewalk),'scene_image_sources':[im.filepath for im in bpy.data.images if im.filepath],'saved_scene_animation_blocks':animated,'ripple_time_control':'explicit Time seconds value set by the render script; no baked 2D frames','source_sha256':hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest(),'samples':sc.cycles.samples,'size':[sc.render.resolution_x,sc.render.resolution_y],'passed':True}
report('source_audit.json',result);status('saved source audit passed: single-face apartment roof, connected parapet, cell-global ripple periods and all %d wet sidewalk slabs driven by ripple normals'%len(sidewalk))
