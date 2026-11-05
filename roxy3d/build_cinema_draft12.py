"""Brief 47. Approved door scene, unchanged room; local RTX3050 full asset pass.

Reuse the proven Brief39 coverage/packaging functions in an isolated namespace.
Never call their scene-polish or preservation writers. All caches stay here.
"""
import sys
sys.dont_write_bytecode=True
import os,json,math,copy,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa11'; RUN=QA/'runtime12_full'
RUN.mkdir(parents=True,exist_ok=True)
for key,folder in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),('OPTIX_CACHE_PATH','optix'),('BLENDER_USER_CONFIG','config'),('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts'),('BLENDER_USER_EXTENSIONS','extensions'),('XDG_CACHE_HOME','xdg')]:
    p=RUN/folder;p.mkdir(exist_ok=True);os.environ[key]=str(p)
sys.path.insert(0,str(ROOT))
import bpy
import numpy as np
from mathutils import Vector,Matrix
from pngio import write as pngwrite
B={'__file__':str(ROOT/'build_cinema_draft11.py'),'__name__':'brief47_helpers'}
src=(ROOT/'build_cinema_draft11.py').read_text(encoding='utf-8')
src=src.replace('runtime11','runtime12_full').replace('draft11','draft12').replace('draft_11','draft_12').replace('cinema_layout_11','cinema_layout_12').replace('CINEMA-DRAFT-11','CINEMA-DRAFT-12')
# Coverage identifiers remain internally consistent; original sources stay read-only.
src=src.replace("poly=[TEN['project'](.25,14.95,-2),TEN['project'](2.70,14.95,-2),TEN['project'](2.70,14.95,142),TEN['project'](.25,14.95,142)]", "poly=data['door_mask_polygon']")
exec(compile(src,'brief47_redirected_helpers','exec'),B)
assert B['RUN']==RUN and B['OUT']==QA/'draft12'
assert B['LAYOUT']==QA/'cinema_layout_12.json' and B['TARGET']==ROOT/'roxy_cinema_draft12.blend'
assert B['IMAGE']==QA/'cinema_draft_12.png' and B['IMAGE2']==QA/'cinema_draft_12@2x.png'
S=139/114; CENTER=1.45; OPEN0=CENTER-.55*S; OPEN1=CENTER+.55*S
ORIGINAL=json.loads((QA/'cinema_layout_11.json').read_text())
BASE=copy.deepcopy(ORIGINAL)
def strip_pieces(obj):
    if isinstance(obj,dict):
        for k in list(obj):
            if k in ['pieces','pieces_note']:del obj[k]
            else:strip_pieces(obj[k])
    elif isinstance(obj,list):
        for v in obj:strip_pieces(v)
strip_pieces(BASE)
B['BASE']=BASE;B['pngwrite']=pngwrite
save=B['save'];sha=B['sha'];read=B['fast_png'];area2=B['area2']

def protected():
    paths=[ROOT/'roxy_cinema_draft11.blend',ROOT/'roxy_cinema_draft11_dim.blend',ROOT/'roxy_cinema_draft12_door.blend',ROOT/'build_cinema_draft11.py',ROOT/'build_cinema_draft11_dim.py',ROOT/'build_cinema_draft12_door.py',ROOT/'roxy_pass10_draft.blend',QA/'cinema_layout_11.json']
    paths+=list(QA.glob('cinema_draft_11*.png'))+list((QA/'draft11').rglob('*.png'))+list((QA/'draft11_dim').rglob('*.png'))
    paths+=list(ROOT.parent.rglob('*.html'))
    return {str(p.relative_to(ROOT.parent)):sha(p) for p in paths if p.is_file()}
def begin():
    p=RUN/'protected_before.json'
    if not p.exists():save(p,protected())
    save(RUN/'input_hashes.json',{name:sha(ROOT/name) for name in ['roxy_cinema_draft11.blend','roxy_cinema_draft12_door.blend','build_cinema_draft11.py','build_cinema_draft12_door.py']})
def preserved():
    before=json.loads((RUN/'protected_before.json').read_text());after=protected()
    changed={k:dict(before=v,after=after.get(k)) for k,v in before.items() if after.get(k)!=v}
    page_changes={k:v for k,v in changed.items() if k.endswith('.html')}
    assert all(k.endswith('.html') for k in changed),('Protected source or Draft11 asset/layout changed',changed)
    # Only task outputs under roxy3d are written by this builder. The live page
    # is concurrently maintained outside that write root; never restore it.
    result=dict(passed=True,protected_files_sha256_unchanged=len(before)-len(changed),protected_sources_and_draft11_assets_unchanged=True,page_writes=0,concurrent_external_page_changes=page_changes,cloud_used=False)
    save(RUN/'preservation_verification.json',result)
    return result
def quality(sc):
    sc.cycles.samples=384;sc.cycles.adaptive_min_samples=64;sc.cycles.adaptive_threshold=.007;sc.cycles.seed=341997
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    sc.render.use_border=False;sc.render.use_crop_to_border=False
def snapshot(sc):
    geometry=B['TEN']['NINE']['geometry_signature'](list(sc.objects))
    states={o.name:dict(matrix=[list(r) for r in o.matrix_world],data=o.data.name if o.data else None,materials=[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],hidden=o.hide_render,camera=o.visible_camera,light=dict(energy=o.data.energy,color=list(o.data.color),receiver=o.light_linking.receiver_collection.name if o.light_linking.receiver_collection else None) if o.type=='LIGHT' else None) for o in sc.objects}
    return geometry,states,B['screen_state'](sc)
def pose(leaves,originals,amount):
    for o in leaves:
        side=int(o['door_side']);hinge=Vector((CENTER+side*.465*S,-14.868,0))
        o.matrix_world=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(-79*side)*amount,4,'Z')@Matrix.Translation(-hinge)@originals[o.name]
    bpy.context.view_layer.update()
def hull(points):
    points=sorted(set(map(tuple,points)))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]
def load_approved():
    begin();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
    oldgeom,oldstates,oldscreen=snapshot(sc)
    oldnames={o.name for o in sc.objects if o.get('d10_leaf')}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft12_door.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
    geom,states,screen=snapshot(sc)
    unchanged=[n for n in oldstates if n not in oldnames]
    assert all(states[n]==oldstates[n] for n in unchanged),'Non-door transform/material/light changed'
    assert all(geom[n]==oldgeom[n] for n in oldgeom if n not in oldnames),'Non-door evaluated geometry changed'
    assert screen==oldscreen,'Screen/camera/world/exposure changed'
    assert set(states)-set(oldstates)=={n for n in states if n.startswith('D12 ')},'Unexpected added object'
    B['strip_aovs'](sc);quality(sc);device=B['gpu'](sc)
    leaves=[o for o in sc.objects if o.get('d12_leaf')];assert len(leaves)==102
    data=dict(device=device,geometry_lock=dict(passed=True,non_door_objects_checked=len(unchanged),non_door_evaluated_geometry_checked=sum(n not in oldnames for n in oldgeom),removed_old_door_objects=len(oldnames),added_approved_door_frame_infill_objects=len(set(states)-set(oldstates)),geometry_sha256=hashlib.sha256(json.dumps(geom,sort_keys=True).encode()).hexdigest()),screen_settings=screen,screen_settings_identical=True,camera_identical=True,new_lights=0,calibration=B['calibrate'](sc),timings=[],coverage=dict(edges=B['EDGES'],bands=B['NBANDS'],batch_aovs=10))
    # Swept-door envelope plus the new aperture; fixed old portal width is excluded.
    polygon=hull([B['TEN']['project'](u,v,z) for u in [OPEN0-.025,OPEN1+.025] for v in [14.16,14.95] for z in [-2,142]])
    data['door_mask_polygon']=polygon
    save(RUN/'scene_lock.json',{k:v for k,v in data.items() if k!='screen_settings'})
    return sc,leaves,data
def screen_compare(rgb):
    old=read(QA/'cinema_draft_11.png')[:,:,:3]
    mask=screen_mask(rgb.shape[:2],1)
    delta=rgb[mask].astype(float)-old[mask].astype(float)
    result=dict(pixels_1x=int(mask.sum()),mean_luminance_delta_0_255=float((delta@np.array([.2126,.7152,.0722])).mean()),max_channel_difference=int(np.abs(delta).max()),mean_absolute_channel_difference=float(np.abs(delta).mean()),settings_identical=True,mean_tolerance=.5,passed=True)
    assert abs(result['mean_luminance_delta_0_255'])<=.5,result
    return result,mask,old
def screen_mask(shape,scale):
    corners=BASE['screen']['corners_1920x1080'];poly=[corners[k] for k in ['TL','TR','BR','BL']]
    yy,xx=np.indices(shape);gx=(xx+.5)/scale;gy=(yy+.5)/scale
    crosses=[((b[0]-a[0])*(gy-a[1])-(b[1]-a[1])*(gx-a[0]))/math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(poly,poly[1:]+poly[:1])]
    return np.logical_and.reduce([c>8 for c in crosses])|np.logical_and.reduce([c< -8 for c in crosses])
B.update(begin=begin,preserved=preserved,load_polished=load_approved,screen_compare=screen_compare)
B['TEN']['door_pose']=pose

def remap(obj):
    if isinstance(obj,str):return obj.replace('draft11_dim','draft12_dim').replace('draft11','draft12').replace('draft_11','draft_12').replace('DRAFT-11','DRAFT-12')
    if isinstance(obj,list):return [remap(v) for v in obj]
    if isinstance(obj,dict):return {k:remap(v) for k,v in obj.items()}
    return obj
def package_lit():
    if '--resume-package' in sys.argv:
        checkpoint=json.loads((RUN/'layout_checkpoint.json').read_text())
        checkpoint['draft12']['preservation']=preserved()
        save(B['LAYOUT'],checkpoint)
    else:B['package']()
    layout=json.loads(B['LAYOUT'].read_text());layout=remap(layout);strip_pieces(layout)
    layout['brief']='BRIEF-47-cinema-draft12-full.md';layout['image']='qa11/cinema_draft_12.png'
    door=layout['page_layers']['entrance_door']
    door['geometry']=dict(center_u=CENTER,plane_v=14.868,uniform_lobby_scale=S,frame_opening_u=[OPEN0,OPEN1],frame_height_zpx=139,clear_aperture_u=[.846447,2.053553],clear_aperture_zpx=[0,132.903509],closed_leaf_u=[.883026,2.016974],closed_leaf_zpx=[1.828947,131.684205],hinges_u=[CENTER-.465*S,CENTER+.465*S],open_degrees=79)
    door['static_slice_cutout']['polygon_1920x1080']=json.loads((RUN/'build_data.json').read_text())['door_mask_polygon']
    # The same five opening intervals and held poses retain the conservative wait.
    layout['page_layers']['spawn']['wait_seconds']=5/18
    layout['page_layers']['spawn']['wait_reason']='New narrower leaves use the same 0-79 degree five-interval opening at 18 fps; wait for held-open frame 5. Straight u=1.45 route retained.'
    layout['tunnel']['rear_portal']['door_opening_u']=[OPEN0,OPEN1]
    layout['tunnel']['rear_portal']['door_opening_zpx_world']=[0,139]
    layout['tunnel']['rear_portal']['clear_door_aperture_u']=[.846447,2.053553]
    layout['tunnel']['rear_portal']['fixed_infill_u']=[[.30,OPEN0],[OPEN1,2.65]]
    layout['approved_layout_source']='qa11/cinema_layout_11.json (read-only source; inherited historical evidence is provenance only)'
    layout['draft12']['inherited_metadata_notice']='Draft10/draft11 evidence retained as historical provenance. Draft12 current verification lives in qa11/runtime12_full; current asset paths in page_layers point only to draft12. No pieces; Claude runs band-slices after this delivery.'
    layout['draft12']['source_sha256']=sha(ROOT/'build_cinema_draft12.py')
    layout['draft12']['read_only_helper_sha256']=sha(ROOT/'build_cinema_draft11.py')
    # The dim entry is finalized only when its matching new assets are complete.
    layout['page_layers'].pop('dim',None)
    save(B['LAYOUT'],layout)

def dim_render():
    # Use exactly the saved BRIEF42 lighting settings, applied to the approved D12 scene.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11_dim.blend'));sc=bpy.context.scene
    lights={o.name:float(o.data.energy) for o in sc.objects if o.type=='LIGHT'}
    strength=bpy.data.materials['D8 ivory core #F4DDB0'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value
    world_nodes=[n for n in sc.world.node_tree.nodes if n.type=='MATH' and n.operation=='MULTIPLY'];assert len(world_nodes)==1
    world_strength=world_nodes[0].inputs[1].default_value
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft12.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
    before=B['TEN']['NINE']['geometry_signature'](list(sc.objects))
    for o in sc.objects:
        if o.type=='LIGHT':o.data.energy=lights[o.name]
    bpy.data.materials['D8 ivory core #F4DDB0'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=strength
    nt=sc.world.node_tree;bg=nt.nodes['Background'];ray=nt.nodes.new('ShaderNodeLightPath');mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=world_strength
    nt.links.new(ray.outputs['Is Camera Ray'],mul.inputs[0]);nt.links.new(mul.outputs[0],bg.inputs['Strength'])
    B['strip_aovs'](sc);quality(sc);device=B['gpu'](sc)
    assert before==B['TEN']['NINE']['geometry_signature'](list(sc.objects))
    data=dict(device=device,timings=[],same_geometry_as_lit=True,lighting_source='roxy_cinema_draft11_dim.blend',lights=lights,sconce_emission=strength,world_camera_strength=world_strength,world_non_camera_strength=0)
    bpy.context.preferences.filepaths.save_version=0
    sc.render.filepath=str(QA/'cinema_draft_12_dim@2x.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_cinema_draft12_dim.blend'),compress=True)
    B['render_one'](sc,QA/'cinema_draft_12_dim@2x.png','native4k dim beauty',data)
    door=json.loads(B['LAYOUT'].read_text())['page_layers']['entrance_door'];x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=x/1920;sc.render.border_max_x=(x+w)/1920;sc.render.border_min_y=1-(y+h)/1080;sc.render.border_max_y=1-y/1080
    leaves=[o for o in sc.objects if o.get('d12_leaf')];originals={o.name:o.matrix_world.copy() for o in leaves}
    for i in range(1,6):
        pose(leaves,originals,.5-.5*math.cos(math.pi*i/5))
        B['render_one'](sc,RUN/('dim_door_pose_%02d@2x.png'%i),'native4k dim entrance pose %d/5'%i,data)
    save(RUN/'dim_render_data.json',data)

def package_dim():
    layout=json.loads(B['LAYOUT'].read_text());layers=layout['page_layers'];door=layers['entrance_door']
    bg2=read(QA/'cinema_draft_12_dim@2x.png');bg=area2(bg2);pngwrite(QA/'cinema_draft_12_dim.png',bg[:,:,:3])
    slices=copy.deepcopy(layers['slices'])
    for s in slices:
        for k in ['file','file_2x']:s[k]=s[k].replace('draft12/','draft12_dim/')
    for scale,rgb in [(1,bg),(2,bg2)]:
        fk='file' if scale==1 else 'file_2x'
        for orig,s in zip(layers['slices'],slices):
            a=read(QA/orig[fk]);x,y,w,h=[s[k]*scale for k in ['x','y','w','h']]
            pngwrite(QA/s[fk],np.dstack([rgb[y:y+h,x:x+w,:3],a[:,:,3]]))
        x,y,w,h=[door[k]*scale for k in ['x','y','frame_width','frame_height']]
        base=rgb[y:y+h,x:x+w];poses=[base]
        for i in range(1,6):
            a=read(RUN/('dim_door_pose_%02d@2x.png'%i));poses.append(area2(a) if scale==1 else a)
        lit=read(QA/door[fk]);sheet=np.zeros_like(lit)
        for f in range(16):
            sl=np.s_[(f//4)*h:(f//4+1)*h,(f%4)*w:(f%4+1)*w];sheet[sl]=poses[min(f,15-f,5)];sheet[sl][:,:,3]=lit[sl][:,:,3]
        suffix='@2x' if scale==2 else '';pngwrite(QA/('draft12_dim/door_entrance'+suffix+'.png'),sheet)
        (QA/('draft12_dim/door_static_cutout'+suffix+'.png')).write_bytes((QA/door['static_slice_cutout'][fk]).read_bytes())
    layers['dim']=dict(image='cinema_draft_12_dim.png',image_2x='cinema_draft_12_dim@2x.png',slices_dir='draft12_dim/slices',slices_dir_2x='draft12_dim/slices',slices=slices,door_file='draft12_dim/door_entrance.png',door_file_2x='draft12_dim/door_entrance@2x.png',door_static_cutout_file='draft12_dim/door_static_cutout.png',door_static_cutout_file_2x='draft12_dim/door_static_cutout@2x.png')
    save(B['LAYOUT'],layout);preserved()

if __name__=='__main__':
    if '--render' in sys.argv:B['render']()
    elif '--package' in sys.argv or '--resume-package' in sys.argv:package_lit()
    elif '--dim-render' in sys.argv:dim_render()
    elif '--dim-package' in sys.argv:package_dim()
    else:raise SystemExit('Choose --render, --package, --dim-render, --dim-package')
