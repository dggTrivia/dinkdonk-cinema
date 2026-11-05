"""Brief 50: approved Brief49 V2 scene, isolated local-GPU full pass."""
import sys
sys.dont_write_bytecode=True
import os,json,copy,hashlib,math,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa11';RUN=QA/'runtime13_full';RUN.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
N={'__file__':str(ROOT/'build_cinema_draft13.py'),'__name__':'brief50_helpers'}
src=(ROOT/'build_cinema_draft12.py').read_text(encoding='utf-8')
src=src.replace('runtime12_full','runtime13_full').replace('draft12','draft13').replace('draft_12','draft_13').replace('DRAFT-12','DRAFT-13').replace('cinema_layout_12','cinema_layout_13')
exec(compile(src,'brief50_redirected_helpers','exec'),N)
bpy=N['bpy'];np=N['np'];B=N['B'];save=N['save'];sha=N['sha'];read=N['read'];area2=N['area2'];pngwrite=N['pngwrite']
assert B['RUN']==RUN and B['IMAGE2']==QA/'cinema_draft_13@2x.png' and B['LAYOUT']==QA/'cinema_layout_13.json' and B['TARGET']==ROOT/'roxy_cinema_draft13.blend'
SOURCE_LAYOUT=RUN/'source_cinema_layout_12.json'
if SOURCE_LAYOUT.exists():
    assert sha(SOURCE_LAYOUT)==json.loads((RUN/'protected_before.json').read_text())['qa11/cinema_layout_12.json']
ORIGINAL=json.loads((SOURCE_LAYOUT if SOURCE_LAYOUT.exists() else QA/'cinema_layout_12.json').read_text())
BASE=copy.deepcopy(ORIGINAL);N['strip_pieces'](BASE)
N['ORIGINAL']=ORIGINAL;N['BASE']=BASE;B['BASE']=BASE
MATERIALS={'D8 red dot #D94B32':('Principled BSDF','Emission Strength'),'D09 camera-only inherited red-orange indicator':('Emission','Strength')}
STEP=QA/'draft13_stepdots'
pure={'value','tree','lock','band_stats'}
syntax=ast.parse((STEP/'build_stepdots.py').read_text())
exec(compile(ast.Module(body=[n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name in pure],type_ignores=[]),'read_only_scene_lock_helpers','exec'),globals())

def protected():
    paths=[]
    for pattern in ['*draft11*.blend','*draft12*.blend','build_cinema_draft11*.py','build_cinema_draft12*.py']:
        paths+=list(ROOT.glob(pattern))
    paths+=list(QA.glob('cinema_draft_1[12]*.png'))+list(QA.glob('cinema_layout_1[12]*.json'))
    for folder in ['draft11','draft11_dim','draft12','draft12_dim']:
        paths+=list((QA/folder).rglob('*'))
    paths+=list(STEP.glob('*.blend'))+list(STEP.glob('*.py'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.is_file()}

def begin():
    if not (RUN/'protected_before.json').exists():
        save(RUN/'protected_before.json',protected());save(RUN/'bands_before.json',band_stats())
        save(RUN/'pages_before.json',{str(p):sha(p) for p in ROOT.parent.rglob('*.html')})
    if not SOURCE_LAYOUT.exists():SOURCE_LAYOUT.write_bytes((QA/'cinema_layout_12.json').read_bytes())
    save(RUN/'input_hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in [STEP/'roxy_cinema_draft13_placement_v2.blend',STEP/'roxy_cinema_draft13_placement_v2_dim.blend',ROOT/'build_cinema_draft11.py',ROOT/'build_cinema_draft12.py',ROOT/'build_cinema_draft13.py',QA/'cinema_layout_12.json']})

def preserved():
    before=json.loads((RUN/'protected_before.json').read_text());assert before==protected(),'Protected source/asset changed'
    bands=json.loads((RUN/'bands_before.json').read_text());assert bands=={k:list(v) for k,v in band_stats().items()},'Protected bands changed'
    pages=json.loads((RUN/'pages_before.json').read_text())
    result=dict(passed=True,protected_files_sha256_unchanged=len(before),protected_band_files_metadata_unchanged=len(bands),page_writes=0,cloud_used=False,concurrent_external_page_changes={p:dict(before=h,after=sha(Path(p))) for p,h in pages.items() if Path(p).is_file() and sha(Path(p))!=h})
    save(RUN/'preservation_verification.json',result);return result

def load_selected(state='lit'):
    begin();suffix='' if state=='lit' else '_dim'
    source=ROOT/('roxy_cinema_draft12'+suffix+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;bpy.context.view_layer.update()
    prior=lock(sc);oldgeom=N['snapshot'](sc)[0]
    selected=STEP/('roxy_cinema_draft13_placement_v2'+suffix+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(selected));sc=bpy.context.scene;bpy.context.view_layer.update()
    current=lock(sc);geom=N['snapshot'](sc)[0]
    names={o.name for o in sc.objects if hasattr(o.data,'materials') and any(m and m.name in MATERIALS for m in o.data.materials)}
    assert len(names)==67
    for name in names:
        assert bpy.data.objects[name].type=='MESH' and len(bpy.data.objects[name].data.polygons)==1
    for mat,(node,socket) in MATERIALS.items():
        p=bpy.data.materials[mat].node_tree.nodes[node].inputs[socket]
        assert abs(p.default_value-1.71)<1e-6
        p.default_value=3.8
    restored=lock(sc)
    for item in [prior,restored]:
        for name in names:item['objects'].pop(name);item['geometry'].pop(name)
    assert prior==restored,'Non-marker scene/material/world/camera/view changed'
    for name in oldgeom:
        if name not in names:assert oldgeom[name]==geom[name],name
    for mat,(node,socket) in MATERIALS.items():bpy.data.materials[mat].node_tree.nodes[node].inputs[socket].default_value=1.71
    assert lock(sc)==current
    source_lock_hash=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest()
    B['strip_aovs'](sc);N['quality'](sc);device=B['gpu'](sc)
    data=dict(device=device,geometry_lock=dict(passed=True,marker_objects_changed=67,non_marker_objects_checked=len(prior['objects']),non_marker_evaluated_geometry_checked=len(geom)-67,geometry_sha256=hashlib.sha256(json.dumps(geom,sort_keys=True).encode()).hexdigest()),approved_scene=str(selected.relative_to(ROOT)),approved_scene_sha256=sha(selected),approved_scene_lock_sha256=source_lock_hash,screen_settings=B['screen_state'](sc),screen_settings_identical=True,camera_identical=True,new_lights=0,emission=1.7100000381469727,calibration=B['calibrate'](sc),timings=[],coverage=dict(edges=B['EDGES'],bands=B['NBANDS'],batch_aovs=10),door_mask_polygon=BASE['page_layers']['entrance_door']['static_slice_cutout']['polygon_1920x1080'])
    save(RUN/('scene_lock.json' if state=='lit' else 'dim_scene_lock.json'),{k:v for k,v in data.items() if k!='screen_settings'})
    return sc,[o for o in sc.objects if o.get('d12_leaf')],data

N.update(begin=begin,preserved=preserved)
B.update(begin=begin,preserved=preserved,load_polished=load_selected)
# Screen statistics use Draft12's corresponding still, with unchanged screen settings.
code=ast.parse((ROOT/'build_cinema_draft12.py').read_text())
screen_src=ast.Module(body=[n for n in code.body if isinstance(n,ast.FunctionDef) and n.name in ['screen_compare','screen_mask']],type_ignores=[])
exec(compile(ast.unparse(screen_src).replace('cinema_draft_11.png','cinema_draft_12.png'),'draft13_screen_checks','exec'),globals())
B['screen_compare']=screen_compare

def remap_paths(obj):
    if isinstance(obj,str):
        # Asset references only: all other Draft12 metadata stays an exact copy.
        if obj.endswith(('.png','.blend')) or obj.startswith(('draft12/','draft12_dim/')):
            return obj.replace('draft12','draft13').replace('draft_12','draft_13')
        return obj
    if isinstance(obj,dict):return {k:remap_paths(v) for k,v in obj.items()}
    if isinstance(obj,list):return [remap_paths(v) for v in obj]
    return obj

def package_lit():
    B['package']()
    generated=json.loads(B['LAYOUT'].read_text());new=generated['page_layers'];fixed=remap_paths(copy.deepcopy(BASE))
    old_slices=fixed['page_layers']['slices'];new_slices=new['slices']
    assert [s['name'] for s in old_slices]==[s['name'] for s in new_slices]
    backgrounds={1:read(B['IMAGE']),2:read(B['IMAGE2'])}
    changes=[]
    for index,(old,cur) in enumerate(zip(old_slices,new_slices)):
        assert all(old[k]==cur[k] for k in ['name','z_index','key_min','key_max'])
        for scale in [1,2]:
            fk='file' if scale==1 else 'file_2x';a=read(QA/cur[fk]);x,y,w,h=[old[k]*scale for k in ['x','y','w','h']];cx,cy=[cur[k]*scale for k in ['x','y']]
            # Preserve the existing rectangles while replacing coverage for the new geometry.
            result=np.zeros((h,w,4),np.uint8);bg=backgrounds[scale];result[:,:,:3]=bg[y:y+h,x:x+w,:3]
            yy,xx=np.nonzero(a[:,:,3]);assert np.all((xx+cx>=x)&(xx+cx<x+w)&(yy+cy>=y)&(yy+cy<y+h)),('New coverage outside locked rectangle',old['name'],scale)
            result[yy+cy-y,xx+cx-x,3]=a[yy,xx,3]
            old_path=QA/ORIGINAL['page_layers']['slices'][index][fk]
            changes.append(dict(name=old['name'],scale=scale,changed_alpha_pixels=int(np.count_nonzero(result[:,:,3]!=read(old_path)[:,:,3]))))
            pngwrite(QA/old[fk],result)
    door=fixed['page_layers']['entrance_door'];assert door['static_slice_cutout']['slices']==new['entrance_door']['static_slice_cutout']['slices']
    for fk in ['file','file_2x']:assert (QA/door['static_slice_cutout'][fk]).read_bytes()==(QA/ORIGINAL['page_layers']['entrance_door']['static_slice_cutout'][fk]).read_bytes()
    save(RUN/'coverage_changes.json',changes)
    save(B['LAYOUT'],fixed)

def dim_render():
    sc,leaves,data=load_selected('dim')
    sc.render.resolution_x=3840;sc.render.resolution_y=2160;sc.render.resolution_percentage=100;sc.render.use_persistent_data=True
    sc.render.filepath=str(QA/'cinema_draft_13_dim@2x.png');bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_cinema_draft13_dim.blend'),compress=True)
    B['render_one'](sc,QA/'cinema_draft_13_dim@2x.png','native4k dim beauty',data)
    door=BASE['page_layers']['entrance_door'];x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=x/1920;sc.render.border_max_x=(x+w)/1920;sc.render.border_min_y=1-(y+h)/1080;sc.render.border_max_y=1-y/1080
    originals={o.name:o.matrix_world.copy() for o in leaves}
    for i in range(1,6):
        N['pose'](leaves,originals,.5-.5*math.cos(math.pi*i/5));B['render_one'](sc,RUN/('dim_door_pose_%02d@2x.png'%i),'native4k dim entrance pose %d/5'%i,data)
    save(RUN/'dim_render_data.json',data)

def package_dim():
    expected=remap_paths(copy.deepcopy(BASE))
    N['package_dim']()
    actual=json.loads(B['LAYOUT'].read_text())
    assert actual['page_layers']['dim']==expected['page_layers']['dim']
    assert actual==expected,'Layout must be exact Draft12 copy minus pieces and asset path switches'
    preserved()

if __name__=='__main__':
    if '--render' in sys.argv:B['render']()
    elif '--package' in sys.argv:package_lit()
    elif '--dim-render' in sys.argv:dim_render()
    elif '--dim-package' in sys.argv:package_dim()
    else:raise SystemExit('Choose --render, --package, --dim-render, --dim-package')
