"""Brief 39: draft10-preserving polish, native local-GPU 4K, paired page assets.

Use the bundled Blender with --background --factory-startup --python-exit-code 1
--python this.py -- --preview / --render / --package. All writes are in roxy3d.
Coverage is rendered in small deterministic batches to fit the laptop's 6GB GPU.
No page, cloud service, earlier source, or earlier blend is written.
"""
import sys
sys.dont_write_bytecode = True
import os, json, math, time, copy, hashlib, struct, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUN = QA/'runtime11'
OUT = QA/'draft11'
RUN.mkdir(parents=True, exist_ok=True)
for key, folder in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),
                    ('OPTIX_CACHE_PATH','optix'),('BLENDER_USER_CONFIG','config'),
                    ('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts'),
                    ('BLENDER_USER_EXTENSIONS','extensions'),('XDG_CACHE_HOME','xdg')]:
    p=RUN/folder;p.mkdir(exist_ok=True);os.environ[key]=str(p)

# Evaluate draft10 as helpers, redirecting its nested helper side effects too.
# Its main/package/preservation routines are never called.
TEN={'__file__':str(ROOT/'build_cinema_draft10.py'),'__name__':'draft10_helpers_for_draft11'}
source=(ROOT/'build_cinema_draft10.py').read_text(encoding='utf-8').replace('runtime10','runtime11')
exec(compile(source,'draft10_helpers_redirected_to_runtime11','exec'),TEN)
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
D=TEN['D']
W,H=1920,1080
BASE=json.loads((QA/'cinema_layout_10.json').read_text())
EDGES=BASE['page_layers']['coverage']['edges']
NBANDS=len(EDGES)-1
IMAGE=QA/'cinema_draft_11.png'
IMAGE2=QA/'cinema_draft_11@2x.png'
LAYOUT=QA/'cinema_layout_11.json'
TARGET=ROOT/'roxy_cinema_draft11.blend'
REPORT=QA/'CINEMA-DRAFT-11.md'
pngwrite,fast_png,read_exr=TEN['pngwrite'],TEN['fast_png'],TEN['read_exr']


def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory():
    out={}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUN in p.parents:continue
        s=p.stat();out[p.relative_to(ROOT.parent).as_posix()]=[s.st_size,s.st_mtime_ns]
    return out


def begin():
    if not (RUN/'preservation_before.json').exists():save(RUN/'preservation_before.json',inventory())
    paths=[ROOT/'BRIEF-39-cinema-draft11-final4k.md',ROOT/'build_cinema_draft10.py',
           ROOT/'roxy_cinema_draft10.blend',QA/'CINEMA-DRAFT-10.md',QA/'cinema_layout_10.json',
           QA/'cinema_draft_10.png',QA/'page_draft10_live.png']
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    p=RUN/'input_hashes.json'
    if p.exists():assert json.loads(p.read_text())==hashes,'Draft10 inputs changed'
    else:save(p,hashes)


def preserved():
    before=json.loads((RUN/'preservation_before.json').read_text());after=inventory()
    current={'roxy3d/build_cinema_draft11.py','roxy3d/roxy_cinema_draft11.blend',
             'roxy3d/qa11/CINEMA-DRAFT-11.md','roxy3d/qa11/cinema_draft_11.png',
             'roxy3d/qa11/cinema_draft_11@2x.png','roxy3d/qa11/cinema_layout_11.json'}
    # Concurrent lobby delivery is updating out10/cloud state. This program
    # never opens these paths for writing; retain the complete external list.
    def concurrent(p):
        return p.startswith(('roxy3d/out10/','roxy3d/out10.stale-20261102/','roxy3d/cloud/backup-run2/')) or p in {
            'roxy3d/cloud/cloud-state-full.json','roxy3d/cloud/result-full.tar.gz','roxy3d/qa10/final/out10-full-1080p.png',
            'roxy3d/BRIEF-40-auditorium-names-neighbours.md','roxy3d/codex-final-38.md','roxy3d/codex-final-40.md',
            'roxy3d/qa11/PAGE-38.md','roxy3d/qa11/PAGE-40.md'}
    changed=[p for p,v in before.items() if after.get(p)!=v]
    old_changes=[p for p in changed if p.startswith('roxy3d/') and p not in current and not p.endswith('.log')
                 and p!='roxy3d/PROGRESS.md' and not concurrent(p)]
    assert not old_changes,old_changes
    new=[p for p in after if p not in before]
    unexpected=[p for p in new if p.startswith('roxy3d/') and p not in current
                and not p.startswith('roxy3d/qa11/draft11/') and not p.endswith('.log') and not concurrent(p)]
    assert not unexpected,unexpected
    begin()
    return {'passed':True,'prior_files':len(before),'prior_pages':sum(p.endswith(('.html','.htm')) for p in before),
            'protected_roxy3d_changes':old_changes,'external_changes':[p for p in changed if p not in current],
            'concurrent_lobby_changes':[p for p in changed if concurrent(p)],
            'concurrent_lobby_new_files':[p for p in new if concurrent(p)],
            'draft10_inputs_sha256_unchanged':True,'whole_workspace_unchanged':not bool(changed or new),
            'new_files_outside_runtime11':new,'builder_page_writes':0,
            'method':'Size/mtime inventory plus SHA256 of all specified draft10 inputs; independently active lobby out10/cloud-state changes, page changes and logs listed separately. Builder writes only draft11 paths.'}


def gpu(sc):
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    found=[d for d in prefs.devices if d.type=='OPTIX' and 'RTX 3050' in d.name]
    assert len(found)==1,[(d.name,d.type) for d in prefs.devices]
    for d in prefs.devices:d.use=d in found
    sc.cycles.device='GPU';sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True
    sc['render_device']='OPTIX: '+found[0].name
    print('LOCAL_GPU_ONLY',sc['render_device'],'CPU device disabled',flush=True)
    return {'backend':'OPTIX','device':found[0].name,'cpu_render_device_enabled':False,'cloud_used':False}


def value(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return list(v)
    except TypeError:return str(v)


def material_state(ma):
    if not ma.use_nodes:return {'name':ma.name,'diffuse':list(ma.diffuse_color)}
    nodes=[]
    for n in ma.node_tree.nodes:
        if n.type=='GROUP' and n.node_tree and 'first-hit surface depth coverage' in n.node_tree.name:continue
        nodes.append({'name':n.name,'type':n.bl_idname,'inputs':{s.identifier:value(s.default_value) for s in n.inputs if hasattr(s,'default_value')}})
    links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in ma.node_tree.links]
    return {'nodes':nodes,'links':links}


def screen_state(sc):
    collection=bpy.data.collections['Receiver - screen only']
    obs=list(collection.objects)
    lights=[]
    for o in sc.objects:
        if o.type=='LIGHT' and o.light_linking.receiver_collection==collection:
            lights.append({'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'matrix':[list(r) for r in o.matrix_world],
                           'size':o.data.size,'size_y':o.data.size_y})
    return {'objects':{o.name:[material_state(m) for m in o.data.materials] for o in obs},'lights':lights,
            'exposure':sc.view_settings.exposure,'world':material_state(sc.world),
            'camera_matrix':[list(r) for r in sc.camera.matrix_world],'ortho':sc.camera.data.ortho_scale}


def strip_aovs(sc):
    for a in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(a)
    for ma in bpy.data.materials:
        if ma.use_nodes:
            for n in list(ma.node_tree.nodes):
                if n.type=='GROUP' and n.node_tree and 'first-hit surface depth coverage' in n.node_tree.name:
                    ma.node_tree.nodes.remove(n)
    sc.render.use_compositing=False;sc.compositing_node_group=None


def multiply_base(ma,factor,label):
    p=ma.node_tree.nodes.get('Principled BSDF')
    if not p:return
    n=ma.node_tree.nodes.new('ShaderNodeMixRGB');n.name=label;n.blend_type='MULTIPLY';n.inputs[0].default_value=1
    n.inputs[2].default_value=(factor,factor,factor,1)
    incoming=list(p.inputs['Base Color'].links)
    if incoming:ma.node_tree.links.new(incoming[0].from_socket,n.inputs[1])
    else:n.inputs[1].default_value=p.inputs['Base Color'].default_value
    ma.node_tree.links.new(n.outputs[0],p.inputs['Base Color'])


def polish(sc):
    edits=[]
    floor=bpy.data.objects['Broad soft carpet and fascia readability']
    old=floor.data.energy;floor.data.energy=old*1.10
    edits.append({'object':floor.name,'field':'existing floor-only fill energy','before':old,'after':floor.data.energy})
    for name,factor in [('D10 accessibility plaque blue',.88),('D10 accessibility pictogram white',.84)]:
        ma=bpy.data.materials[name];multiply_base(ma,factor,'D11 restrained plaque value')
        edits.append({'material':name,'base_color_value_multiplier':factor,'hue_and_geometry_unchanged':True})
    # A dedicated material copy keeps the small fabric lift on the entrance only.
    leaves=[o for o in sc.objects if o.get('d10_leaf')]
    copied={};door_materials={}
    for o in leaves:
        for i,ma in enumerate(o.data.materials):
            if not ma:continue
            door_materials[ma.name]=material_state(ma)
            lowered=ma.name.lower()
            if any(word in lowered for word in ['velvet','upholster','burgundy']):
                if ma.name not in copied:
                    new=ma.copy();new.name='D11 entrance finish '+ma.name
                    multiply_base(new,1.14,'D11 entrance fabric detail');copied[ma.name]=new
                    edits.append({'material':ma.name,'entrance_only_copy':new.name,'base_color_value_multiplier':1.14})
                o.data.materials[i]=copied[ma.name]
            if 'porthole' in lowered and 'camera-only' in lowered:
                if ma.name not in copied:
                    new=ma.copy();new.name='D11 entrance amber '+ma.name
                    for n in new.node_tree.nodes:
                        if n.type=='EMISSION':n.inputs['Strength'].default_value*=.85
                    copied[ma.name]=new;edits.append({'material':ma.name,'camera_only_amber_multiplier':.85})
                o.data.materials[i]=copied[ma.name]
    # Keep the fascia plain and dark; 4% broad variation is not fine grain.
    cut=bpy.data.materials['D8 cut core #292632'].copy();cut.name='D11 subdued matte cut fascia'
    nt=cut.node_tree;p=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.85;tex.inputs['Detail'].default_value=1
    geo=nt.nodes.new('ShaderNodeNewGeometry');nt.links.new(geo.outputs['Position'],tex.inputs['Vector'])
    ramp=nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.90,.90,.90,1);ramp.color_ramp.elements[1].color=(.94,.94,.94,1)
    nt.links.new(tex.outputs['Fac'],ramp.inputs[0])
    mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    nt.links.new(ramp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],p.inputs['Base Color'])
    faces=[]
    for o in sc.objects:
        if o.name.startswith(('D10 rear cut wall','D10 right stepped cut wall')):
            for i,ma in enumerate(o.data.materials):o.data.materials[i]=cut
            faces.append(o.name)
    edits.append({'material':cut.name,'objects':faces,'broad_neutral_value_range':[.90,.94],
                  'relative_light_times_mean_material_value':1.10*.92,'bump_added':False})
    save(RUN/'entrance_materials_before.json',door_materials)
    return edits,leaves


def probes(sc,tree,owners,scale):
    route=BASE['walk_route']['rear_portal_to_cross_aisle']
    samples=[('route_%02d'%i,route[i],False) for i in [0,1,2,3,5,6,7,9,10,11,12,16,19]]
    samples.append(('stairs_C',[3.475,5.725,64],False))
    samples.extend(('seated_'+r['row'],[r['seat_u_by_block']['main'][0],r['v']+.2,r['floor_zpx_world']+36],True) for r in BASE['rows'])
    records=[]
    for name,p,seated in samples:
        px,py=[a*scale for a in TEN['project'](*p)];height=50*D['K']*scale;half=11.1*D['K']*scale
        tests=[]
        for y in range(math.ceil(py-height),math.floor(py)):
            for x in range(math.ceil(px-half),math.floor(px+half)):
                q=TEN['xyz'](*p)+TEN['RIGHT']*((x+.5-px)/(60*scale))+TEN['UP']*((py-y-.5)/(60*scale))
                hit=tree.ray_cast(q+TEN['NORMAL']*45,-TEN['NORMAL'],44.9998)
                tests.append([x,y,hit[2] is None,owners[hit[2]] if hit[2] is not None else None])
        records.append({'name':name,'uvzpx':p,'seated':seated,'key':TEN['depth'](*p),'z_index':TEN['zi'](TEN['depth'](*p)),
                        'ray_visible_fraction':sum(t[2] for t in tests)/len(tests),'pixels':tests})
    return records


def calibrate(sc):
    records=[]
    for p in [(0,0,0),(17.5,0,0),(0,14.9,0),(17.5,14.9,160),(0,0,500)]:
        expected=TEN['project'](*p);v=world_to_camera_view(sc,sc.camera,TEN['xyz'](*p))
        actual=[v.x*W,(1-v.y)*H]
        records.append({'uvzpx':p,'expected_1x':expected,'actual_1x':actual,'error_1x':[actual[i]-expected[i] for i in [0,1]]})
    error=max(abs(v) for r in records for v in r['error_1x'])
    assert error<.001
    return {'points':records,'max_axis_error_1x_px':error,'max_axis_error_2x_px':error*2,'passed':True}


def load_polished():
    begin();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft10.blend'))
    sc=bpy.context.scene;device=gpu(sc)
    bpy.context.view_layer.update()
    original=TEN['NINE']['geometry_signature'](list(sc.objects))
    before=screen_state(sc);camera=[list(r) for r in sc.camera.matrix_world]
    lights={o.name for o in sc.objects if o.type=='LIGHT'}
    strip_aovs(sc);edits,leaves=polish(sc)
    after=TEN['NINE']['geometry_signature'](list(sc.objects))
    assert original==after,'Geometry changed'
    assert before==screen_state(sc),'Screen settings changed'
    assert camera==[list(r) for r in sc.camera.matrix_world]
    assert lights=={o.name for o in sc.objects if o.type=='LIGHT'}
    sc.name='DINK DONK Screen 1 - draft11 final4k polish'
    sc['brief']='BRIEF-39-cinema-draft11-final4k.md';sc['draft11_source']='roxy_cinema_draft10.blend'
    data={'device':device,'polish':edits,'geometry_lock':{'passed':True,'objects_checked':len(original),'geometry_sha256':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest()},
          'screen_settings':before,'screen_settings_identical':True,'camera_identical':True,'new_lights':0,
          'calibration':calibrate(sc),'timings':[],'coverage':{'edges':EDGES,'bands':NBANDS,'batch_aovs':10}}
    return sc,leaves,data


def render_one(sc,path,label,data):
    assert sc.cycles.device=='GPU'
    sc.render.filepath=str(path)
    t=time.perf_counter();bpy.ops.render.render(write_still=True)
    record={'pass':label,'seconds':time.perf_counter()-t,'resolution':[sc.render.resolution_x,sc.render.resolution_y],
            'border':sc.render.use_border,'device':sc['render_device'],'samples':sc.cycles.samples,
            'min_samples':sc.cycles.adaptive_min_samples,'threshold':sc.cycles.adaptive_threshold}
    data['timings'].append(record);save(RUN/'render_progress.json',data)
    print('D11_PASS',json.dumps(record),flush=True)


def setup_batch(sc,groups):
    strip_aovs(sc)
    group=bpy.data.node_groups.new('D11 first-hit surface depth coverage','ShaderNodeTree')
    nodes,links=group.nodes,group.links
    geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
    sub=nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';links.new(sep.outputs['X'],sub.inputs[0]);links.new(sep.outputs['Y'],sub.inputs[1])
    mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=D['ZPP']/90;links.new(sep.outputs['Z'],mul.inputs[0])
    add=nodes.new('ShaderNodeMath');add.operation='ADD';links.new(sub.outputs[0],add.inputs[0]);links.new(mul.outputs[0],add.inputs[1])
    for i in groups:
        name='D11mask%03d'%i;a=sc.view_layers[0].aovs.add();a.name=name;a.type='COLOR'
        combine=nodes.new('ShaderNodeCombineXYZ')
        for c in range(3):
            b=i*3+c
            if b>=NBANDS:continue
            low=nodes.new('ShaderNodeMath');low.operation='LESS_THAN';low.inputs[1].default_value=EDGES[b];links.new(add.outputs[0],low.inputs[0])
            high=nodes.new('ShaderNodeMath');high.operation='LESS_THAN';high.inputs[1].default_value=EDGES[b+1];links.new(add.outputs[0],high.inputs[0])
            diff=nodes.new('ShaderNodeMath');diff.operation='SUBTRACT';links.new(high.outputs[0],diff.inputs[0]);links.new(low.outputs[0],diff.inputs[1]);links.new(diff.outputs[0],combine.inputs[c])
        out=nodes.new('ShaderNodeOutputAOV');out.aov_name=name;links.new(combine.outputs[0],out.inputs['Color'])
    for ma in bpy.data.materials:
        if ma.use_nodes:n=ma.node_tree.nodes.new('ShaderNodeGroup');n.node_tree=group
    tree=bpy.data.node_groups.new('D11 coverage files','CompositorNodeTree');sc.compositing_node_group=tree
    rl=tree.nodes.new('CompositorNodeRLayers');rl.scene=sc
    out=tree.nodes.new('CompositorNodeOutputFile');out.directory=str(RUN/'coverage');out.file_name='coverage'
    out.format.media_type='IMAGE';out.format.file_format='OPEN_EXR';out.format.color_mode='RGB';out.format.color_depth='32';out.format.exr_codec='ZIP';out.save_as_render=False
    for i in groups:
        name='D11mask%03d'%i;out.file_output_items.new('RGBA',name);tree.links.new(rl.outputs[name],out.inputs[name])
    sc.render.use_compositing=True


def preview():
    sc,leaves,data=load_polished();sc.render.resolution_x=W;sc.render.resolution_y=H
    sc.render.use_border=False;sc.render.use_compositing=False
    render_one(sc,RUN/'polish_preview.png','1080p polish review',data)
    save(RUN/'preview_data.json',data)
    print('D11_PREVIEW_READY',flush=True)


def render():
    sc,leaves,data=load_polished()
    assert not IMAGE2.exists(),'Do not overwrite an existing final 4K render'
    if (RUN/'preview_data.json').exists():data['timings']=json.loads((RUN/'preview_data.json').read_text())['timings']
    tree,owners=TEN['tree_for'](sc)
    data['closed_probes']={str(s):probes(sc,tree,owners,s) for s in [1,2]}
    sc.render.resolution_x=W*2;sc.render.resolution_y=H*2;sc.render.resolution_percentage=100
    sc.render.use_border=False;sc.render.use_compositing=False;sc.render.use_persistent_data=True
    sc.render.filepath=str(IMAGE2)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    # A 58-AOV 4K buffer alone exceeds this GPU's memory. Ten RGB AOVs per
    # deterministic render keep rendering on the GPU. Seed, adaptive sampling,
    # filter, scene, lighting and camera are identical across all six batches.
    batches=[list(range(i,min(i+10,math.ceil(NBANDS/3)))) for i in range(0,math.ceil(NBANDS/3),10)]
    for i,groups in enumerate(batches):
        setup_batch(sc,groups)
        path=IMAGE2 if i==0 else RUN/('coverage_beauty_%02d.png'%i)
        render_one(sc,path,'native4k beauty + coverage batch %d/%d'%(i+1,len(batches)),data)
    strip_aovs(sc)
    door=copy.deepcopy(BASE['page_layers']['entrance_door'])
    x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=x/W;sc.render.border_max_x=(x+w)/W
    sc.render.border_min_y=1-(y+h)/H;sc.render.border_max_y=1-y/H
    originals={o.name:o.matrix_world.copy() for o in leaves}
    for i in range(1,6):
        amount=.5-.5*math.cos(math.pi*i/5)
        TEN['door_pose'](leaves,originals,amount)
        render_one(sc,RUN/('door_pose_%02d@2x.png'%i),'native4k entrance pose %d/5'%i,data)
    tree,owners=TEN['tree_for'](sc)
    data['open_probes']={str(s):probes(sc,tree,owners,s) for s in [1,2]}
    TEN['door_pose'](leaves,originals,0)
    data['door']=door;data['coverage']['method']='Batched Cycles first-camera-hit Position masks; deterministic identical beauty sampling in each batch, same filter, full float RGB EXR, no mask denoising.'
    save(RUN/'build_data.json',data)
    print('D11_RENDER_COMPLETE',flush=True)


def area2(a):
    h,w=a.shape[:2]
    if a.dtype==np.uint8:
        return ((a.reshape(h//2,2,w//2,2,*a.shape[2:]).astype(np.uint16).sum(axis=(1,3))+2)//4).astype(np.uint8)
    return a.reshape(h//2,2,w//2,2,*a.shape[2:]).mean(axis=(1,3))


def emit_png(path,arr):
    # Resume a packaging audit without recompressing already-correct PNGs.
    # Decode and compare every pixel before reusing any existing output.
    path=Path(path)
    if '--reuse-png' in sys.argv and path.exists():
        actual=fast_png(path)
        assert actual.shape[:2]==arr.shape[:2] and np.array_equal(actual[:,:,:arr.shape[2]],arr),path
    else:pngwrite(path,arr)


def layer_checks(records,slices,masks,scale,door=None,cut=None):
    results=[]
    for p in records:
        above=[s for s in slices if s['z_index']>p['z_index']];near=[];total=0.
        for x,y,*unused in p['pixels']:
            trans=1.;cp=0.
            if cut is not None:
                dx,dy=door['x']*scale,door['y']*scale
                if dx<=x<dx+cut.shape[1] and dy<=y<dy+cut.shape[0]:cp=float(cut[y-dy,x-dx])/255
            for s in above:
                ax,ay=s['x']*scale,s['y']*scale;a=masks[s['name']]
                if ax<=x<ax+a.shape[1] and ay<=y<ay+a.shape[0]:
                    alpha=float(a[y-ay,x-ax])/255
                    if cut is not None and s['name'] in door['static_slice_cutout']['slices']:alpha*=1-cp
                    trans*=1-alpha
                    if alpha and s['name'] not in near:near.append(s['name'])
            if cut is not None and door['z_index']>p['z_index']:trans*=1-cp
            total+=trans
        fraction=total/len(p['pixels'])
        results.append({k:v for k,v in p.items() if k!='pixels'}|{'layer_visible_fraction':fraction,
                       'absolute_fraction_error':abs(fraction-p['ray_visible_fraction']),
                       'above_slices':[s['name'] for s in above],'below_slices':[s['name'] for s in slices if s['z_index']<=p['z_index']],
                       'overlapping_above_slices':near})
    return results


def screen_compare(rgb):
    old=fast_png(QA/'cinema_draft_10.png')[:,:,:3]
    mask=np.zeros((H,W),bool);corners=BASE['screen']['corners_1920x1080']
    for x in range(math.ceil(corners['TL'][0]+8),math.floor(corners['TR'][0]-8)):
        top=370+.5*(x+.5-890)-460*D['K'];bottom=370+.5*(x+.5-890)-90*D['K']
        mask[math.ceil(top+8):math.floor(bottom-8),x]=True
    delta=rgb[mask].astype(float)-old[mask].astype(float)
    result={'pixels_1x':int(mask.sum()),'mean_luminance_delta_0_255':float((delta@np.array([.2126,.7152,.0722])).mean()),
            'max_channel_difference':int(np.abs(delta).max()),'mean_absolute_channel_difference':float(np.abs(delta).mean()),
            'settings_identical':True,'mean_tolerance':.5}
    result['passed']=abs(result['mean_luminance_delta_0_255'])<=.5
    assert result['passed'],result
    return result,mask,old


def png_check(path):
    buf=path.read_bytes();assert buf[:8]==b'\x89PNG\r\n\x1a\n';offset=8;chunks=0
    while offset<len(buf):
        n=struct.unpack_from('>I',buf,offset)[0];typ=buf[offset+4:offset+8];payload=buf[offset+8:offset+8+n]
        assert zlib.crc32(typ+payload)&0xffffffff==struct.unpack_from('>I',buf,offset+8+n)[0],path
        offset+=n+12;chunks+=1
    assert offset==len(buf)
    return {'file':path.relative_to(QA).as_posix(),'sha256':hashlib.sha256(buf).hexdigest(),'size':list(struct.unpack_from('>II',buf,16)),'chunks_crc_checked':chunks}


def package():
    begin();data=json.loads((RUN/'build_data.json').read_text());OUT.mkdir(exist_ok=True)
    beauty2=fast_png(IMAGE2);beauty=area2(beauty2)
    emit_png(IMAGE,beauty[:,:,:3])
    # Check repeated beauty pixels as well as fixed camera/seed/settings. GPU
    # accumulation/denoising can vary by one display byte; report that honestly.
    batch_checks=[]
    for p in sorted(RUN.glob('coverage_beauty_*.png')):
        a=fast_png(p);delta=np.abs(a[:,:,:3].astype(np.int16)-beauty2[:,:,:3].astype(np.int16));diff=int(delta.max())
        batch_checks.append({'file':p.name,'maximum_rgb_byte_difference_from_first_batch':diff,
                             'mean_absolute_rgb_byte_difference':float(delta.mean()),'changed_rgb_channels':int(np.count_nonzero(delta))})
        assert diff<=1,('Coverage batch beauty changed beyond one byte',p,diff)
    files=sorted((RUN/'coverage').glob('*.exr'));assert len(files)==math.ceil(NBANDS/3),(len(files),NBANDS)
    slices=[];masks={1:{},2:{}};sums={1:np.zeros((H,W),np.float32),2:np.zeros((2*H,2*W),np.float32)}
    coverage_bounds={}
    for i in range(len(files)-1,-1,-1):
        a=read_exr(files[i]);assert a.shape[:2]==(H*2,W*2)
        for c in range(2,-1,-1):
            b=i*3+c
            if b>=NBANDS:continue
            exclusive={2:a[:,:,c],1:area2(a[:,:,c])};alphas={}
            for scale in [1,2]:
                remaining=np.maximum(1-sums[scale],1e-7)
                alphas[scale]=np.rint(np.clip(exclusive[scale]/remaining,0,1)*255).astype(np.uint8)
                sums[scale]+=exclusive[scale]
            y2,x2=np.nonzero(alphas[2]);y1,x1=np.nonzero(alphas[1])
            if not len(x2) and not len(x1):continue
            xs=[int(x1.min())] if len(x1) else [];xe=[int(x1.max())+1] if len(x1) else []
            ys=[int(y1.min())] if len(y1) else [];ye=[int(y1.max())+1] if len(y1) else []
            if len(x2):xs.append(int(x2.min())//2);xe.append((int(x2.max())+2)//2);ys.append(int(y2.min())//2);ye.append((int(y2.max())+2)//2)
            x0,xend,y0,yend=min(xs),max(xe),min(ys),max(ye)
            name='depth_%03d'%b
            entry={'file':'draft11/slices/'+name+'.png','file_2x':'draft11/slices/'+name+'@2x.png',
                   'x':x0,'y':y0,'w':xend-x0,'h':yend-y0,'z_index':TEN['zi'](EDGES[b]),
                   'key_min':EDGES[b],'key_max':EDGES[b+1],'name':name}
            for scale,img in [(1,beauty),(2,beauty2)]:
                sl=np.s_[y0*scale:yend*scale,x0*scale:xend*scale]
                crop=np.dstack([img[sl][:,:,:3],alphas[scale][sl]])
                emit_png(QA/entry['file' if scale==1 else 'file_2x'],crop)
                masks[scale][name]=crop[:,:,3].copy()
            slices.append(entry)
        print('D11_PACK_COVERAGE',i,flush=True)
    slices.sort(key=lambda s:s['key_min']);assert len(slices)<200
    checks={}
    for scale,img in [(1,beauty),(2,beauty2)]:
        excess=float(np.maximum(sums[scale]-1,0).max())
        assert excess<.0001,('Batched exclusive coverage is not a partition',scale,excess)
        # Every source-over operation is checked against the actual decoded
        # delivered slice bytes over the delivered background.
        recon=img[:,:,:3].copy();rgb=img[:,:,:3]
        for s in slices:
            a=fast_png(QA/s['file' if scale==1 else 'file_2x'])
            x,y,w,h=[s[k]*scale for k in ['x','y','w','h']]
            assert a.shape==(h,w,4)
            assert np.array_equal(a[:,:,:3],rgb[y:y+h,x:x+w])
            aa=a[:,:,3:4].astype(np.float32)/255
            recon[y:y+h,x:x+w]=np.rint(a[:,:,:3]*aa+recon[y:y+h,x:x+w]*(1-aa)).astype(np.uint8)
        diff=int(np.abs(recon.astype(np.int16)-rgb.astype(np.int16)).max());assert diff==0
        tests=layer_checks(data['closed_probes'][str(scale)],slices,masks[scale],scale)
        error=max(p['absolute_fraction_error'] for p in tests)
        assert error<.025,(scale,error)
        assert all(p['layer_visible_fraction']==0 for p in tests if p['ray_visible_fraction']==0)
        checks[str(scale)]={'background_plus_slices_max_absolute_rgb_difference':diff,'walker_samples':tests,
                            'max_absolute_fraction_error':error,'coverage_sum_range':[float(sums[scale].min()),float(sums[scale].max())],
                            'exclusive_coverage_max_excess_above_one':excess}
    door=copy.deepcopy(data['door']);door['file']='draft11/door_entrance.png';door['file_2x']='draft11/door_entrance@2x.png'
    x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    doorchecks={};cutmasks={}
    for scale,img in [(1,beauty),(2,beauty2)]:
        sx,sy,sw,sh=[v*scale for v in [x,y,w,h]]
        base=img[sy:sy+sh,sx:sx+sw].copy();poses=[base]
        for i in range(1,6):
            p=fast_png(RUN/('door_pose_%02d@2x.png'%i))
            if scale==1:p=area2(p)
            assert p.shape==base.shape,(p.shape,base.shape);poses.append(p)
        yy,xx=np.indices((sh,sw));gx=(xx+.5)/scale+x;gy=(yy+.5)/scale+y
        poly=[TEN['project'](.25,14.95,-2),TEN['project'](2.70,14.95,-2),TEN['project'](2.70,14.95,142),TEN['project'](.25,14.95,142)]
        cross=[(b[0]-a[0])*(gy-a[1])-(b[1]-a[1])*(gx-a[0]) for a,b in zip(poly,poly[1:]+poly[:1])]
        portal=np.logical_and.reduce([v>=0 for v in cross])|np.logical_and.reduce([v<=0 for v in cross])
        alpha=portal.astype(np.uint8)*255;cutmasks[scale]=alpha
        sheet=np.zeros((sh*4,sw*4,4),np.uint8)
        for f in range(16):
            p=poses[min(f,15-f,5)].copy();p[:,:,3]=alpha
            sheet[(f//4)*sh:(f//4+1)*sh,(f%4)*sw:(f%4+1)*sw]=p
        path=QA/door['file' if scale==1 else 'file_2x'];emit_png(path,sheet)
        first=sheet[:sh,:sw];last=sheet[3*sh:4*sh,3*sw:4*sw]
        assert np.array_equal(first,last)
        aa=alpha[:,:,None].astype(float)/255
        endpoint=np.rint(first[:,:,:3]*aa+base[:,:,:3]*(1-aa)).astype(np.uint8)
        assert np.array_equal(endpoint,base[:,:,:3])
        file='draft11/door_static_cutout'+('@2x' if scale==2 else '')+'.png'
        cut=np.full((sh,sw,4),255,np.uint8);cut[:,:,3]=alpha;emit_png(QA/file,cut)
        # Verify RGB of every canonical pose against its actual GPU patch.
        assert all(np.array_equal(sheet[(f//4)*sh:(f//4+1)*sh,(f%4)*sw:(f%4+1)*sw,:3],poses[min(f,15-f,5)][:,:,:3]) for f in range(16))
        affected=[]
        for s in slices:
            if s['z_index']<=door['z_index']:continue
            ax,ay=s['x']*scale,s['y']*scale;am=masks[scale][s['name']]
            x0=max(sx,ax);x1=min(sx+sw,ax+am.shape[1]);y0=max(sy,ay);y1=min(sy+sh,ay+am.shape[0])
            if x0<x1 and y0<y1 and np.any((am[y0-ay:y1-ay,x0-ax:x1-ax]>0)&portal[y0-sy:y1-sy,x0-sx:x1-sx]):affected.append(s['name'])
        doorchecks[str(scale)]={'first_last_identical':True,'closed_composite_max_rgb_difference':0,'affected_static_slices':affected,
                                'canonical_poses_match_gpu_patch':True,'sheet_pixels':[sw*4,sh*4],'cell_pixels':[sw,sh]}
    affected=sorted(set(doorchecks['1']['affected_static_slices']+doorchecks['2']['affected_static_slices']))
    door['static_slice_cutout'].update(file='draft11/door_static_cutout.png',file_2x='draft11/door_static_cutout@2x.png',slices=affected)
    for scale in [1,2]:
        doorchecks[str(scale)]['open_route_checks_with_cutout']=layer_checks(data['open_probes'][str(scale)],slices,masks[scale],scale,door,cutmasks[scale])
        assert all(p['absolute_fraction_error']<.025 for p in doorchecks[str(scale)]['open_route_checks_with_cutout'][:4])
    screen,screenmask,old=screen_compare(beauty[:,:,:3])
    mask2=np.repeat(np.repeat(screenmask,2,axis=0),2,axis=1)
    old2=np.repeat(np.repeat(old,2,axis=0),2,axis=1)
    delta2=beauty2[:,:,:3][mask2].astype(float)-old2[mask2].astype(float)
    screen['native4k_vs_draft10_same_footprint_reference']={
        'pixels':int(mask2.sum()),'mean_luminance_delta_0_255':float((delta2@np.array([.2126,.7152,.0722])).mean()),
        'max_channel_difference':int(np.abs(delta2).max()),'mean_absolute_channel_difference':float(np.abs(delta2).mean()),
        'reference':'Draft10 pixels repeated 2x2 for same-footprint statistics; screen settings checked separately.'}
    assert abs(screen['native4k_vs_draft10_same_footprint_reference']['mean_luminance_delta_0_255'])<=.5
    layout=copy.deepcopy(BASE);layout['brief']='BRIEF-39-cinema-draft11-final4k.md'
    layout['page_layers'].update(image='cinema_draft_11.png',image_2x='cinema_draft_11@2x.png',slices=slices,entrance_door=door)
    layout['page_layers']['coverage']=copy.deepcopy(BASE['page_layers']['coverage'])|data['coverage']|{'maximum_band_width':.25,'mask_aovs':math.ceil(NBANDS/3),
            'one_x_mask_method':'Exact float 2x2 area mean of native4k exclusive coverage, then conditional source-over alpha at each scale.'}
    layout['render'].update(image='qa11/cinema_draft_11.png',image_2x='qa11/cinema_draft_11@2x.png',blend='roxy_cinema_draft11.blend',
                            seconds=data['timings'][1 if data['timings'][0]['pass']=='1080p polish review' else 0]['seconds'],
                            image_sha256=sha(IMAGE),image_2x_sha256=sha(IMAGE2),resolution=[W,H],resolution_2x=[W*2,H*2])
    layout['approved_layout_source']='qa11/cinema_layout_10.json'
    for k in ['camera','room','rows','row_pairs','total_seats','aisles','stairs','screen','walk_route']:
        assert layout[k]==BASE[k],k
    pngchecks=[png_check(p) for p in [IMAGE,IMAGE2]+sorted(OUT.rglob('*.png'))]
    result={k:v for k,v in data.items() if k not in ['closed_probes','open_probes','door']}
    result.update(layer_validation=checks,door_validation=doorchecks,screen_comparison=screen,
                  batch_beauty_identity=batch_checks,png_validation=pngchecks,
                  downscale={'method':'Native3840x2160 8-bit display PNG; exact 2x2 area average per RGB channel, integer (sum+2)//4; no resize filter, sharpening or AI upscale.',
                             'verified_from_decoded_final_pngs':bool(np.array_equal(fast_png(IMAGE)[:,:,:3],area2(beauty2)[:,:,:3]))},
                  input_sha256=json.loads((RUN/'input_hashes.json').read_text()),
                  source_sha256=sha(Path(__file__)),review_still_visually_inspected=False,
                  inherited_metadata_notice='draft10 and older fields are retained for provenance. Current draft11 acceptance is in draft11; page_layers paths refer only to draft11.')
    save(RUN/'artifact_checks_checkpoint.json',result)
    save(RUN/'layout_checkpoint.json',layout|{'draft11':result})
    result['preservation']=preserved()
    layout['draft11']=result
    layout['limitations']=['No page file edited and no live-browser/chatter acceptance claimed.',
        'The page must apply entrance_door.static_slice_cutout while its sheet plays.',
        'The inherited fixed-z door sheet cannot encode every moving-leaf/tunnel-surface depth; full open-state sample discrepancies are retained at both scales.']
    save(LAYOUT,layout);save(RUN/'layer_checks.json',result)
    print('D11_PACKAGE_COMPLETE',len(slices),'slices per scale',len(pngchecks),'PNG files',flush=True)


if __name__=='__main__':
    if '--preview' in sys.argv:preview()
    elif '--render' in sys.argv:render()
    elif '--package' in sys.argv:package()
    else:raise SystemExit('Choose --preview, --render, or --package')
