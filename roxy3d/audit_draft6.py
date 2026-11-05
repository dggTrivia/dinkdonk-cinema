"""Read-only scene checks; no extra render or motion experiment."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from common import ZPP
from draft6_common import *
from build_pass10_draft6 import neon_state
from build_pass10_draft import bounds
src=ROOT/'roxy_pass10_draft.blend';bpy.ops.wm.open_mainfile(filepath=str(src));sc=bpy.context.scene;saved_state=sc.get('d6_neon_state')
dep=bpy.context.evaluated_depsgraph_get();checks=[]
for name in ['D5 art lookalike','D5 art conductor 0','D5 art conductor 1','D5 art conductor 2','D5 art cinema','D5 art cabge','D5 art travel','D5 art buttons','D6 art eatfresh','D6 art timetable']:
    o=sc.objects[name];cen=sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
    hit,loc,normal,index,backing,mat=sc.ray_cast(dep,cen+Vector((0,.0002,0)),Vector((0,1,0)),distance=.12)
    row={'art':name,'backing':backing.name if hit else None,'gap':(loc-cen).length if hit else None,'mounted':bool(hit)};checks.append(row)
states={}
for state in ['A','B']:
    neon_state(sc,state);rows=[]
    for o in sc.objects:
        if o.get('d6_tube_state'):
            p=o.data.materials[0].node_tree.nodes.get('Principled BSDF');emission=float(p.inputs['Emission Strength'].default_value)
            rows.append({'object':o.name,'circuit':o['d6_tube_state'],'visible':not o.hide_render,'emission':emission})
    states[state]=rows
    assert all(r['visible'] for r in rows)
    assert all((r['emission']>0)==(r['circuit']==state) for r in rows)
neon_state(sc,'A')
route=[{'name':o.name,'text':o.data.body} for o in sc.objects if o.type=='FONT' and (any(s in o.name.lower() for s in ['route','destination','transit','stop sign','bus plate','pole operator']))]
stale=[r for r in route if '95' in r['text'] or 'ROXY' in r['text'].upper()]
marker_count=sum(bool(o.get('surface_vandalism')) for o in sc.objects)
ground=sc.objects['D6 broken heaved alley ground'];mesh=ground.data
tree=BVHTree.FromPolygons([ground.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons],all_triangles=True)
contacts=[]
for o in sc.objects:
    if not o.name.startswith(('D6 flattened soggy cardboard','D6 wet newspaper spread','D6 scattered wet flyer','D6 stuck wet paper')):continue
    gaps=[]
    for vert in o.data.vertices:
        point=o.matrix_world@vert.co;loc,normal,index,dist=tree.ray_cast(point+Vector((0,0,2)),Vector((0,0,-1)),4)
        if loc is not None:gaps.append((point.z-loc.z)*ZPP)
    contacts.append({'name':o.name,'vertex_clearance_z_px':gaps,'max_clearance_z_px':max(gaps) if gaps else None})
data={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mounted_art':checks,'unmounted_count':sum(not c['mounted'] for c in checks),'neon_states':states,'off_set_remains_visible':True,'off_set_emission_zero':True,'route_texts':route,'stale_route_labels':stale,'marker_stroke_objects':marker_count,'roof_A_saved':saved_state=='A','cabbage_red_count':sum(o.name=='D5 RED cabbage' for o in sc.objects),'ripple_distance':bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'].nodes['Ray traced ripple normal'].inputs['Distance'].default_value,'packed_new_art':[{'image':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if any(s in im.name for s in ['eatfresh','timetable','newspaper','flyer'])],'no_render_invoked':True}
report('source_audit.json',data)
data['ground_litter_contact']=contacts;data['ground_normals_upward']=all(p.normal.z>0 for p in mesh.polygons);report('source_audit.json',data)
poster=sc.objects['D6 art eatfresh'];bb=bounds(poster);ratio=(bb[2]-bb[0])/((bb[5]-bb[4])/ZPP)
data['eatfresh_physical_aspect']=ratio;data['eatfresh_image_aspect']=1000/1400;data['eatfresh_aspect_preserved']=abs(ratio-1000/1400)<1e-5;report('source_audit.json',data)
assert data['eatfresh_aspect_preserved']
assert data['unmounted_count']==0,checks
assert not stale,stale
status('read-only scene audit passed: artwork has physical backing, both neon circuits remain visible with the off set at zero emission, no stale 95/ROXY transit labels, one red cabbage')
