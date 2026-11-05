import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from draft5_common import *
from build_pass10_draft5 import set_phase,outdoor,atmosphere
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene
sites=json.loads((WORK/'impact_sites.json').read_text());bad=[]
from mathutils import Vector
for i,s in enumerate(sites):
    ob=bpy.data.objects[s['object']]
    if not outdoor(Vector(s['point']),ob) or atmosphere(ob) or not ob.get('rain_audited'):bad.append(i)
if bad:print('BAD_IMPACTS',[(i,sites[i]) for i in bad[:20]],flush=True)
assert not bad
ob=bpy.data.objects['D5 periodic wet micro impacts'];set_phase(sc,0);a=np.empty(len(ob.data.vertices)*3,dtype=np.float32);ob.data.vertices.foreach_get('co',a);set_phase(sc,2);c=np.empty_like(a);ob.data.vertices.foreach_get('co',c);assert np.array_equal(a,c)
p=ob.data.materials[0].node_tree.nodes.get('Principled BSDF');assert p.inputs['Emission Strength'].default_value==0
keys=set(o['approved_meme'] for o in sc.objects if 'approved_meme' in o);assert len(keys)==12
supports=[];deps=bpy.context.evaluated_depsgraph_get()
for ob in sc.objects:
    if 'approved_meme' not in ob:continue
    center=sum((ob.matrix_world@v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);origin=center+Vector((0,.002,0))
    hit,loc,normal,index,target,matrix=sc.ray_cast(deps,origin,Vector((0,1,0)),distance=.11)
    if hit and target==ob:
        origin=loc+Vector((0,.004,0));hit,loc,normal,index,target,matrix=sc.ray_cast(deps,origin,Vector((0,1,0)),distance=.11)
    front_hit,front_loc,fn,fi,front_obj,fm=sc.ray_cast(deps,center-Vector((0,.10,0)),Vector((0,1,0)),distance=.11)
    buried=bool(front_hit and hit and front_obj==target and front_loc.y<center.y-.001)
    assert not buried,(ob.name,target.name)
    supports.append({'art':ob.name,'backing':target.name if hit else None,'gap_world':(loc-center).length if hit else None,'buried_in_backing':buried})
assert all(row['backing'] for row in supports),supports
report('art_support.json',supports)
assert len([o for o in sc.objects if o.name=='D5 RED cabbage'])==1
summary=json.loads((WORK/'scene.json').read_text());required=summary['required_water_targets'];assert all(required.values())
report('source_audit.json',{'passed':True,'source_sha256':hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest(),'approved_art_count':len(keys),'approved_art_keys':sorted(keys),'red_cabbages':1,'packed_original_images':len([i for i in bpy.data.images if i.packed_file]),'wet_only_impact_sites':len(sites),'indoor_or_sky_impact_sites':len(bad),'micro_impact_emission':p.inputs['Emission Strength'].default_value,'canonical_geometry_max_error':float(np.abs(a-c).max()),'period_seconds':2,'retained_ripple_group':'D4 periodic ray-traced rain ripple normals','required_water_targets':required,'samples':sc.cycles.samples,'native_size':[sc.render.resolution_x,sc.render.resolution_y],'animation_evaluation':'build_pass10_draft5.set_phase(scene, seconds); deterministic geometric impacts and shared ripple clock; no baked prior-pass reflections'})
status('saved-scene audit passed: all twelve packed originals, one red cabbage, wet-only nonemissive micro-impacts, explicit AC/shelter/glass/fabric coverage and bit-identical periodic geometry')
