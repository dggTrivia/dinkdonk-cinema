"""Brief 46: isolated draft11 door replacement; two local-GPU 1080p captures only."""
import sys
sys.dont_write_bytecode=True
import os, json, math, hashlib, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa11'; RUN=QA/'runtime12'
RUN.mkdir(exist_ok=True)
for key,folder in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),('OPTIX_CACHE_PATH','optix'),('BLENDER_USER_CONFIG','config'),('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts'),('BLENDER_USER_EXTENSIONS','extensions'),('XDG_CACHE_HOME','xdg')]:
    p=RUN/folder;p.mkdir(exist_ok=True);os.environ[key]=str(p)
sys.path.insert(0,str(ROOT))
import bpy
import numpy as np
from mathutils import Matrix,Vector
from pngio import read,write
ZPP=60*math.sqrt(2)*math.cos(math.pi/6)
S=139/114
CENTER=1.45
OPEN0=CENTER-.55*S; OPEN1=CENTER+.55*S

def dump(name,data):
    (RUN/name).write_text(json.dumps(data,indent=2,default=str)+'\n')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def state(o):
    return dict(matrix=[list(r) for r in o.matrix_world],data=o.data.name if o.data else None,
                materials=[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],
                hidden=o.hide_render, camera=o.visible_camera,
                light=dict(energy=o.data.energy,color=list(o.data.color)) if o.type=='LIGHT' else None)

protected=[ROOT/'roxy_cinema_draft11.blend',ROOT/'build_cinema_draft11.py',ROOT/'roxy_pass10_draft.blend',ROOT/'out10/manifest.json',ROOT/'out10/NOTES-PASS10.md',QA/'cinema_layout_11.json']
protected+=list((QA/'draft11').rglob('*'))+list((QA/'draft11_dim').rglob('*'))
protected+=[p for p in ROOT.parent.rglob('*.html')]
hashes={str(p.relative_to(ROOT.parent)):digest(p) for p in protected if p.is_file()}
dump('protected_before.json',hashes)
inspection=json.loads((QA/'door12_inspection.json').read_text())
source_names=[r['name'] for r in inspection['roxy_pass10_draft.blend']]
frame_names=[r['name'] for r in inspection['roxy_pass10_draft.blend_frames']]
assert len(source_names)==102 and len(frame_names)==3,(len(source_names),frame_names)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11.blend'))
sc=bpy.context.scene;bpy.context.view_layer.update()
old=[o for o in sc.objects if o.get('d10_leaf')]
unchanged={o.name:state(o) for o in sc.objects if o not in old}
camera=[list(r) for r in sc.camera.matrix_world]
exposure=sc.view_settings.exposure
for o in old:bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('Draft12 current lobby padded entrance');sc.collection.children.link(col)
with bpy.data.libraries.load(str(ROOT/'roxy_pass10_draft.blend'),link=False) as (a,b):
    b.objects=source_names+frame_names
imported=[o for o in b.objects if o]
for o in imported:col.objects.link(o)
bpy.context.view_layer.update()
# Match the lobby's 1.1 x 114 opening at 139 zpx high using ONE scale.
# Lobby y=-.008 leaf plane maps to auditorium v=14.868.
transform=Matrix.Translation((CENTER,-14.868,0))@Matrix.Scale(S,4)@Matrix.Translation((-4.8,.008,0))
source_matrices={o.name:o.matrix_world.copy() for o in imported}
source_materials={o.name:[m.name for m in o.data.materials] for o in imported}
leaves=[]
for o in imported:
    name=o.name
    o.matrix_world=transform@source_matrices[name]
    o['draft12_lobby_source_object']=name
    o.name='D12 lobby '+name
    o.hide_render=False;o.visible_camera=True
    if name in source_names:o['d12_leaf']=True;leaves.append(o)
bpy.context.view_layer.update()

# Only close the spare width of the old portal with the existing cut-wall finish.
template=bpy.data.objects['D10 rear cut wall left of portal']
def infill(name,a,c,z0,z1):
    o=template.copy();o.data=template.data.copy();o.name='D12 '+name;col.objects.link(o)
    # Preserve the original material and bevel; replace only the box vertices.
    pts=[Vector((a,-14.90,z0/ZPP)),Vector((c,-14.94,z1/ZPP))]
    oldpoints=[v.co.copy() for v in o.data.vertices]
    low=Vector(tuple(min(p[i] for p in oldpoints) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in oldpoints) for i in range(3)))
    targetlow=Vector((a,-14.94,z0/ZPP));targethigh=Vector((c,-14.90,z1/ZPP))
    for v in o.data.vertices:
        v.co=Vector(tuple(targetlow[i]+(v.co[i]-low[i])/(high[i]-low[i])*(targethigh[i]-targetlow[i]) for i in range(3)))
    return o
fills=[infill('matching wall infill left',.30,OPEN0,-8,140),infill('matching wall infill right',OPEN1,2.65,-8,140),infill('matching wall over lintel',OPEN0,OPEN1,139,140)]
receivers=bpy.data.collections.get('Fill receivers floor and cut structure')
for o in imported+fills:
    if receivers:receivers.objects.link(o)
bpy.context.view_layer.update()
assert all(state(bpy.data.objects[n])==v for n,v in unchanged.items()),'Non-door object changed'
assert camera==[list(r) for r in sc.camera.matrix_world] and exposure==sc.view_settings.exposure
assert abs((OPEN0+OPEN1)/2-CENTER)<1e-9
assert not any('Porthole' in o.name for o in imported)
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
devices=[d for d in prefs.devices if d.type=='OPTIX' and 'RTX 3050' in d.name]
assert len(devices)==1,[(d.name,d.type) for d in prefs.devices]
for d in prefs.devices:d.use=d in devices
sc.cycles.device='GPU';sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True
sc.cycles.samples=24;sc.cycles.adaptive_min_samples=8;sc.cycles.adaptive_threshold=.06
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.use_compositing=False;sc.compositing_node_group=None
for a in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(a)
# Remove dormant coverage outputs, with no effect on surface appearance.
for ma in bpy.data.materials:
    if ma.use_nodes:
        for n in list(ma.node_tree.nodes):
            if n.type=='GROUP' and n.node_tree and 'first-hit surface depth coverage' in n.node_tree.name:ma.node_tree.nodes.remove(n)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
sc.render.use_border=False;sc.render.use_crop_to_border=False
sc.name='DINK DONK Screen 1 - draft12 door review only'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_cinema_draft12_door.blend'),compress=True)
times=[]
def render(path,label):
    assert sc.cycles.device=='GPU' and not any(d.use and d.type=='CPU' for d in prefs.devices)
    print('LOCAL_RTX3050_ONLY',label,'24 samples',flush=True)
    sc.render.filepath=str(path);start=time.perf_counter();bpy.ops.render.render(write_still=True)
    times.append(dict(label=label,seconds=time.perf_counter()-start))
    dump('render_progress.json',times)
render(QA/'cinema_draft_12_door.png','closed 1920x1080')
x,y,w,h=247,539,201,217
closed=read(QA/'cinema_draft_12_door.png',use_cache=False)[y:y+h,x:x+w]
write(QA/'cinema_draft_12_door_crop.png',np.repeat(np.repeat(closed,4,0),4,1))
originals={o.name:o.matrix_world.copy() for o in leaves}
for o in leaves:
    side=int(o['door_side'])
    hinge=transform@Vector((4.8+side*.465,-.008,0))
    o.matrix_world=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(-79*side),4,'Z')@Matrix.Translation(-hinge)@originals[o.name]
bpy.context.view_layer.update()
sc.render.use_border=True;sc.render.use_crop_to_border=True
sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x+w+.1)/1920
sc.render.border_min_y=1-(y+h-.1)/1080;sc.render.border_max_y=1-(y-.1)/1080
render(RUN/'door_open_native.png','fully open 79 degrees, sheet held pose frames 5-10')
opened=read(RUN/'door_open_native.png',use_cache=False)
assert opened.shape[:2]==(h,w),opened.shape
write(QA/'cinema_draft_12_door_open_crop.png',np.repeat(np.repeat(opened,4,0),4,1))
after={str(p.relative_to(ROOT.parent)):digest(p) for p in protected if p.is_file()}
assert hashes==after,'Protected input changed'
body=[o for o in leaves if o['draft12_lobby_source_object'].startswith('Upholstered cinema door')]
points=[o.matrix_world@Vector(c) for o in body for c in o.bound_box]
# Report closed leaf bounds from their saved matrices, not the open render pose.
points=[originals[o.name]@Vector(c) for o in body for c in o.bound_box]
bounds=dict(u=[min(p.x for p in points),max(p.x for p in points)],zpx=[min(p.z for p in points)*ZPP,max(p.z for p in points)*ZPP])
data=dict(source='roxy_pass10_draft.blend',source_objects=source_names,frame_objects=frame_names,source_materials=source_materials,uniform_scale=S,opening_u=[OPEN0,OPEN1],opening_zpx=[0,139],closed_leaf_bounds=bounds,center_u=CENTER,plane_v=14.868,open_degrees=79,crop_native=[x,y,w,h],crop_zoom='4x nearest-neighbour from native 1080p pixels',device=devices[0].name,cpu_render_enabled=False,timings=times,unchanged_non_door_objects=len(unchanged),protected_files_sha256_unchanged=len(hashes))
dump('draft12_door_evidence.json',data)
print('DRAFT12_RENDER_COMPLETE',json.dumps(data|{'source_objects':len(source_names),'source_materials':'see evidence'}),flush=True)
