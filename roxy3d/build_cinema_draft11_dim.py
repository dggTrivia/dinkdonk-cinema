"""Brief42: lighting-only dim variant of saved draft11. All writes under roxy3d."""
import sys
sys.dont_write_bytecode=True
import os,json,math,time,hashlib,struct,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa11'; RUN=QA/'runtime11_dim'; OUT=QA/'draft11_dim'
RUN.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
import bpy
import numpy as np
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
from pngio import write as pngwrite

def save(p,obj):
    Path(p).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def readpng(p):
    im=bpy.data.images.load(str(p),check_existing=False);im.colorspace_settings.name='Non-Color'
    a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a)
    a=np.rint(a.reshape(im.size[1],im.size[0],4)[::-1]*255).clip(0,255).astype(np.uint8)
    bpy.data.images.remove(im);return a

def area2(a):
    h,w=a.shape[:2]
    return ((a.reshape(h//2,2,w//2,2,*a.shape[2:]).astype(np.uint16).sum(axis=(1,3))+2)//4).astype(np.uint8)

def geometry(sc):
    dep=bpy.context.evaluated_depsgraph_get(); result={}
    for ob in sc.objects:
        if ob.type not in ['MESH','CURVE','FONT']:continue
        ev=ob.evaluated_get(dep);me=ev.to_mesh();h=hashlib.sha256()
        for v in me.vertices:h.update(struct.pack('<3d',*(ev.matrix_world@v.co)))
        for p in me.polygons:
            h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        result[ob.name]=h.hexdigest();ev.to_mesh_clear()
    return result

def camera(sc):return {'matrix':[list(r) for r in sc.camera.matrix_world],'ortho':sc.camera.data.ortho_scale,'lens':sc.camera.data.lens,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]}

def load_dim():
    protected=[ROOT/'build_cinema_draft11.py',ROOT/'roxy_cinema_draft11.blend',QA/'CINEMA-DRAFT-11.md',QA/'cinema_draft_11.png',QA/'cinema_draft_11@2x.png']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    if (RUN/'source_hashes.json').exists():assert hashes==json.loads((RUN/'source_hashes.json').read_text())
    else:save(RUN/'source_hashes.json',hashes)
    lp=QA/'cinema_layout_11.json'
    if not (RUN/'cinema_layout_11_before.json').exists():(RUN/'cinema_layout_11_before.json').write_bytes(lp.read_bytes())
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11.blend'))
    sc=bpy.context.scene;bpy.context.view_layer.update();before=geometry(sc);cam=camera(sc)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    found=[d for d in prefs.devices if d.type=='OPTIX' and 'RTX 3050' in d.name];assert len(found)==1
    for d in prefs.devices:d.use=d in found
    sc.cycles.device='GPU';sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True
    print('LOCAL_GPU_ONLY',found[0].name,'CPU render disabled',flush=True)
    edits=[]
    for ob in sc.objects:
        if ob.type!='LIGHT':continue
        n=ob.name
        if n.startswith('Low warm seating pool'):f=.06
        elif n.startswith('Warm isolated sconce pool'):f=.035
        elif n.startswith('Soft narrow pleat wash'):f=.02
        elif n.startswith('Broad row '):f=.32
        elif n=='Broad soft carpet and fascia readability':f=.45
        elif n=='Subtle cool velvet edge bounce':f=.10
        elif n=='Broad dim indirect screen ambient':f=0
        else:f=1 # All tunnel/arrival/reveal spills stay intact.
        old=ob.data.energy;ob.data.energy=old*f
        edits.append({'light':n,'before_W':old,'after_W':ob.data.energy,'factor':f,'receiver':ob.light_linking.receiver_collection.name if ob.light_linking.receiver_collection else None})
    # Dim the actual visible sconce cores; all safety-sign/step emitters retained.
    ma=bpy.data.materials['D8 ivory core #F4DDB0'];p=ma.node_tree.nodes.get('Principled BSDF')
    old=p.inputs['Emission Strength'].default_value;p.inputs['Emission Strength'].default_value=old*.04
    edits.append({'material':ma.name,'emission_before':old,'emission_after':p.inputs['Emission Strength'].default_value})
    # Keep the camera backdrop; remove the ceiling-less world's illumination.
    nt=sc.world.node_tree;bg=nt.nodes.get('Background');old=bg.inputs['Strength'].default_value
    ray=nt.nodes.new('ShaderNodeLightPath');mul=nt.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=old
    nt.links.new(ray.outputs['Is Camera Ray'],mul.inputs[0]);nt.links.new(mul.outputs[0],bg.inputs['Strength'])
    edits.append({'world_camera_strength':old,'world_non_camera_strength':0})
    assert geometry(sc)==before;assert camera(sc)==cam
    # Strip coverage-only nodes; reuse delivered masks instead of re-rendering them.
    for a in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(a)
    for m in bpy.data.materials:
        if m.use_nodes:
            for n in list(m.node_tree.nodes):
                if n.type=='GROUP' and n.node_tree and 'first-hit surface depth coverage' in n.node_tree.name:m.node_tree.nodes.remove(n)
    sc.render.use_compositing=False;sc.compositing_node_group=None
    data={'device':found[0].name,'backend':'OPTIX','cpu_render_enabled':False,'cloud_used':False,'geometry_objects_unchanged':len(before),'geometry_signature':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'camera_unchanged':True,'exposure':sc.view_settings.exposure,'edits':edits,'timings':[]}
    save(RUN/'dim_settings.json',data)
    return sc,data

def render_one(sc,path,data,label):
    assert sc.cycles.device=='GPU';sc.render.filepath=str(path)
    start=time.perf_counter();bpy.ops.render.render(write_still=True)
    data['timings'].append({'pass':label,'seconds':time.perf_counter()-start,'samples':sc.cycles.samples,'minimum_samples':sc.cycles.adaptive_min_samples,'threshold':sc.cycles.adaptive_threshold,'seed':sc.cycles.seed})
    save(RUN/'render_data.json',data)

def render(preview=False):
    sc,data=load_dim();sc.render.resolution_percentage=100
    sc.render.resolution_x=1920 if preview else 3840;sc.render.resolution_y=1080 if preview else 2160
    sc.render.use_border=False;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='8'
    if preview:
        render_one(sc,RUN/'preview.png',data,'1080p lights-down review');return
    sc.render.use_persistent_data=True
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_cinema_draft11_dim.blend'),compress=True)
    render_one(sc,QA/'cinema_draft_11_dim@2x.png',data,'native4k dim beauty')
    layout=json.loads((RUN/'cinema_layout_11_before.json').read_text());door=layout['page_layers']['entrance_door']
    x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=x/1920;sc.render.border_max_x=(x+w)/1920
    sc.render.border_min_y=1-(y+h)/1080;sc.render.border_max_y=1-y/1080
    leaves=[o for o in sc.objects if o.get('d10_leaf')];original={o.name:o.matrix_world.copy() for o in leaves}
    for i in range(1,6):
        amount=.5-.5*math.cos(math.pi*i/5)
        for o in leaves:
            side=o['door_side'];hinge=Vector((1.475-side*1.175,-14.868,0))
            o.matrix_world=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(79)*amount*side,4,'Z')@Matrix.Translation(-hinge)@original[o.name]
        bpy.context.view_layer.update()
        render_one(sc,RUN/('door_pose_%02d@2x.png'%i),data,'native4k dim entrance pose %d/5'%i)
    for o in leaves:o.matrix_world=original[o.name]
    print('DIM_RENDER_COMPLETE',flush=True)

def screen_pixels(rgb,scale,layout):
    corners=layout['screen']['corners_1920x1080']
    poly=[corners[k] for k in ['TL','TR','BR','BL']]
    # Pixel centres >2 stage pixels inside every screen edge exclude AA borders.
    yy,xx=np.indices(rgb.shape[:2]);gx=(xx+.5)/scale;gy=(yy+.5)/scale
    crosses=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        crosses.append(((b[0]-a[0])*(gy-a[1])-(b[1]-a[1])*(gx-a[0]))/math.hypot(b[0]-a[0],b[1]-a[1]))
    mask=np.logical_and.reduce([c>2 for c in crosses])|np.logical_and.reduce([c< -2 for c in crosses])
    p=rgb[mask][:,:3];lum=p@np.array([.2126,.7152,.0722])
    result={'interior_pixels':int(mask.sum()),'mean_luminance_0_255':float(lum.mean()),'maximum_channel_byte':int(p.max()),'p99_luminance_0_255':float(np.percentile(lum,99))}
    assert result['maximum_channel_byte']<=1,('Screen is illuminated',result)
    return result

def luminance(sc,up,dim):
    from mathutils.bvhtree import BVHTree
    deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];owners=[]
    for ob in sc.objects:
        if ob.type not in ['MESH','CURVE','FONT'] or ob.hide_render:continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh();offset=len(verts)
        verts.extend(ev.matrix_world@v.co for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
        owners.extend([ob.name]*len(me.polygons));ev.to_mesh_clear()
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=False)
    right=sc.camera.matrix_world.to_3x3()@Vector((1,0,0));vertical=sc.camera.matrix_world.to_3x3()@Vector((0,1,0));normal=sc.camera.matrix_world.to_3x3()@Vector((0,0,1))
    labels=np.zeros((1080,1920),np.uint8);row_ids={r:i+1 for i,r in enumerate('BCDEFGHI')}
    for y in range(0,1080,2):
        for x in range(0,1920,2):
            origin=sc.camera.location-normal*2+right*((x+.5-960)*32/1920)+vertical*((540-y-.5)*32/1920)
            hit=tree.ray_cast(origin,-normal,100)
            if hit[2] is None:continue
            n=owners[hit[2]]
            if n.startswith('Row ') and 'purple backs - future occluder' in n:labels[y,x]=row_ids[n[4]]
            elif 500<=x<1450 and y>=500 and 'carpet' in n.lower():labels[y,x]=20
            elif 'tread' in n.lower() or 'riser' in n.lower():labels[y,x]=21
    def stats(a):
        v=a[:,:,:3]@np.array([.2126,.7152,.0722]);res={}
        for k,mask in [('all_seat_backs',(labels>0)&(labels<10)),('audience_carpet',labels==20),('stairs',labels==21)]+[('row_'+r,labels==i) for r,i in row_ids.items()]:
            p=v[mask]
            res[k]={'samples':len(p),'mean':float(p.mean()),'median':float(np.median(p)),'p10':float(np.percentile(p,10)),'p90':float(np.percentile(p,90))} if len(p) else None
        return res
    np.save(RUN/'luminance_sample_labels.npy',labels)
    return {'method':'Rec709 weights of decoded display-sRGB RGB8 bytes, no re-encoding; every second x/y first-camera-hit evaluated BVH ray. Seat-back meshes only, excludes seams on separate meshes; carpet restricted to audience x500:1450/y500:1080. Identical sample labels for up and dim.','up':stats(up),'dim':stats(dim)}

def package():
    layout=json.loads((RUN/'cinema_layout_11_before.json').read_text());layers=layout['page_layers'];door=layers['entrance_door']
    data=json.loads((RUN/'render_data.json').read_text());OUT.mkdir(parents=True,exist_ok=True);(OUT/'slices').mkdir(exist_ok=True)
    bg2=readpng(QA/'cinema_draft_11_dim@2x.png');assert bg2.shape==(2160,3840,4)
    bg=area2(bg2);pngwrite(QA/'cinema_draft_11_dim.png',bg[:,:,:3]);assert np.array_equal(readpng(QA/'cinema_draft_11_dim.png'),bg)
    checks={};new_slices=copy.deepcopy(layers['slices'])
    for s in new_slices:
        s['file']=s['file'].replace('draft11/','draft11_dim/');s['file_2x']=s['file_2x'].replace('draft11/','draft11_dim/')
    delivered=[QA/'cinema_draft_11_dim.png',QA/'cinema_draft_11_dim@2x.png']
    for scale,rgb in [(1,bg),(2,bg2)]:
        recon=rgb[:,:,:3].copy();mask_count=0
        for orig,s in zip(layers['slices'],new_slices):
            assert {k:v for k,v in orig.items() if k not in ['file','file_2x']}=={k:v for k,v in s.items() if k not in ['file','file_2x']}
            fk='file' if scale==1 else 'file_2x';old=readpng(QA/orig[fk]);x,y,w,h=[s[k]*scale for k in ['x','y','w','h']]
            assert old.shape==(h,w,4)
            a=np.dstack([rgb[y:y+h,x:x+w,:3],old[:,:,3]])
            path=QA/s[fk];pngwrite(path,a);decoded=readpng(path);delivered.append(path)
            assert np.array_equal(decoded[:,:,3],old[:,:,3]);assert np.array_equal(decoded[:,:,:3],rgb[y:y+h,x:x+w,:3]);mask_count+=1
            alpha=decoded[:,:,3:4].astype(np.float32)/255
            recon[y:y+h,x:x+w]=np.rint(decoded[:,:,:3]*alpha+recon[y:y+h,x:x+w]*(1-alpha)).astype(np.uint8)
        diff=int(np.abs(recon.astype(np.int16)-rgb[:,:,:3].astype(np.int16)).max());assert diff==0
        fk='file' if scale==1 else 'file_2x';x,y,w,h=[door[k]*scale for k in ['x','y','frame_width','frame_height']]
        base=rgb[y:y+h,x:x+w];poses=[base]
        for i in range(1,6):
            p=readpng(RUN/('door_pose_%02d@2x.png'%i));p=area2(p) if scale==1 else p
            assert p.shape==base.shape;poses.append(p)
        original_sheet=readpng(QA/door[fk]);sheet=np.zeros_like(original_sheet)
        for f in range(16):
            patch=poses[min(f,15-f,5)];sl=np.s_[(f//4)*h:(f//4+1)*h,(f%4)*w:(f%4+1)*w]
            sheet[sl][:,:,:3]=patch[:,:,:3];sheet[sl][:,:,3]=original_sheet[sl][:,:,3]
        path=OUT/('door_entrance'+('@2x' if scale==2 else '')+'.png');pngwrite(path,sheet);delivered.append(path)
        sheet=readpng(path);assert np.array_equal(sheet[:,:,3],original_sheet[:,:,3])
        assert np.array_equal(sheet[:h,:w],sheet[3*h:4*h,3*w:4*w])
        alpha=sheet[:h,:w,3:4].astype(float)/255
        assert np.array_equal(np.rint(sheet[:h,:w,:3]*alpha+base[:,:,:3]*(1-alpha)).astype(np.uint8),base[:,:,:3])
        for f in range(16):
            cell=sheet[(f//4)*h:(f//4+1)*h,(f%4)*w:(f%4+1)*w]
            assert np.array_equal(cell[:,:,:3],poses[min(f,15-f,5)][:,:,:3])
        cut=door['static_slice_cutout'];cutpath=OUT/('door_static_cutout'+('@2x' if scale==2 else '')+'.png')
        cutpath.write_bytes((QA/cut[fk]).read_bytes());assert sha(cutpath)==sha(QA/cut[fk]);delivered.append(cutpath)
        checks[str(scale)]={'image_pixels':[rgb.shape[1],rgb.shape[0]],'slices':mask_count,'slice_names_order_xywh_z_indices_unchanged':True,'all_slice_alpha_masks_byte_identical':True,'background_plus_slices_max_RGB_byte_difference':diff,'door_sheet_alpha_identical':True,'door_cells':[w,h],'closed_endpoints_exact':True,'all_16_frame_RGB_match_dim_GPU_poses':True,'cutout_file_byte_identical':True,'screen':screen_pixels(rgb,scale,layout)}
    # Fresh saved-scene comparison proves unchanged geometry/camera/screen shader.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
    original_geometry=geometry(sc);original_camera=camera(sc)
    screen=bpy.data.objects['SCREEN clean unchanged 16 by 9 quad']
    def mat_inputs(o):
        return [(m.name,[(n.name,n.bl_idname,[(i.identifier,list(i.default_value) if hasattr(i.default_value,'__iter__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes if n.type!='GROUP']) for m in o.data.materials]
    shader=mat_inputs(screen)
    lum=luminance(sc,readpng(QA/'cinema_draft_11.png'),bg)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11_dim.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
    assert geometry(sc)==original_geometry;assert camera(sc)==original_camera
    assert mat_inputs(bpy.data.objects['SCREEN clean unchanged 16 by 9 quad'])==shader
    assert sc.cycles.device=='GPU';assert sc.world.node_tree.nodes.get('Background').inputs['Strength'].is_linked
    # Preserve every pre-existing layout byte; insert only the new dim member.
    dim={'image':'cinema_draft_11_dim.png','image_2x':'cinema_draft_11_dim@2x.png','slices_dir':'draft11_dim/slices','slices_dir_2x':'draft11_dim/slices','slices':new_slices,'door_file':'draft11_dim/door_entrance.png','door_file_2x':'draft11_dim/door_entrance@2x.png','door_static_cutout_file':'draft11_dim/door_static_cutout.png','door_static_cutout_file_2x':'draft11_dim/door_static_cutout@2x.png'}
    before=(RUN/'cinema_layout_11_before.json').read_bytes();current=(QA/'cinema_layout_11.json').read_bytes()
    text=before.decode('utf-8');needle='"page_layers": {';assert text.count(needle)==1
    insertion='\n    "dim": '+json.dumps(dim,indent=2).replace('\n','\n    ')+','
    updated=text.replace(needle,needle+insertion,1).encode('utf-8')
    assert current in [before,updated],'Concurrent layout edit; do not overwrite'
    parsed=json.loads(updated);assert parsed['page_layers'].pop('dim')==dim;assert parsed==layout
    (QA/'cinema_layout_11.json').write_bytes(updated)
    assert (QA/'cinema_layout_11.json').read_bytes().replace(insertion.encode(),b'',1)==before
    for p,h in json.loads((RUN/'source_hashes.json').read_text()).items():assert sha(ROOT/p)==h
    # PNG chunk CRCs independent of Blender's decoder.
    import zlib
    for p in delivered:
        buf=p.read_bytes();pos=8
        while pos<len(buf):
            n=struct.unpack_from('>I',buf,pos)[0];chunk=buf[pos+4:pos+8+n];crc=struct.unpack_from('>I',buf,pos+8+n)[0]
            assert zlib.crc32(chunk)&0xffffffff==crc,(p,pos);pos+=n+12
        assert pos==len(buf)
    result={'checks':checks,'luminance':lum,'geometry_unchanged':len(original_geometry),'camera_unchanged':True,'screen_shader_unchanged':True,'layout_only_dim_added_original_bytes_preserved':True,'source_inputs_sha256_unchanged':True,'pngs_decoded_and_crc_checked':len(delivered),'render':data,'page_writes':0}
    save(RUN/'verification.json',result)
    # Native-pixel crops for final inspection; no gain/exposure adjustment.
    for name,(x,y,w,h) in {'tiers':(875,690,560,265),'entrance':(250,535,210,215),'plaques':(940,470,440,240),'screen':(1095,145,390,460)}.items():
        pngwrite(RUN/('review_'+name+'@2x.png'),bg2[y*2:(y+h)*2,x*2:(x+w)*2,:3])
    pngwrite(RUN/'review_door_sheet.png',readpng(OUT/'door_entrance.png'))
    print('DIM_ASSETS_VERIFIED',json.dumps({'checks':checks,'luminance':lum,'png_count':len(delivered)}),flush=True)

def review():
    bg2=readpng(QA/'cinema_draft_11_dim@2x.png')
    for name,(x,y,w,h) in {'tiers':(875,690,560,265),'entrance':(250,535,210,215),'plaques':(940,470,440,240),'screen':(1095,145,390,460)}.items():
        pngwrite(RUN/('review_'+name+'@2x.png'),bg2[y*2:(y+h)*2,x*2:(x+w)*2,:3])
    pngwrite(RUN/'review_door_sheet.png',readpng(OUT/'door_entrance.png'))

def inspect():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_cinema_draft11.blend'))
    sc=bpy.context.scene
    result={'lights':[], 'emissions':[], 'world':[], 'collections':[], 'render':{}}
    for o in sc.objects:
        if o.type=='LIGHT':result['lights'].append({'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'receiver':o.light_linking.receiver_collection.name if o.light_linking.receiver_collection else None})
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        for n in m.node_tree.nodes:
            if n.type=='EMISSION':result['emissions'].append({'material':m.name,'node':n.name,'strength':n.inputs['Strength'].default_value,'linked':bool(n.inputs['Strength'].links)})
            if n.type=='BSDF_PRINCIPLED' and (n.inputs['Emission Strength'].default_value or n.inputs['Emission Strength'].links):result['emissions'].append({'material':m.name,'node':n.name,'strength':n.inputs['Emission Strength'].default_value,'linked':bool(n.inputs['Emission Strength'].links)})
    result['world']=[{'name':n.name,'type':n.type,'strength':n.inputs['Strength'].default_value if 'Strength' in n.inputs else None} for n in sc.world.node_tree.nodes]
    result['collections']=[c.name for c in bpy.data.collections]
    result['render']={k:getattr(sc.cycles,k) for k in ['samples','adaptive_min_samples','adaptive_threshold','seed','device']}
    result['seat_backs']=[o.name for o in sc.objects if 'back' in o.name.lower()][:50]
    result['screen_materials']=[m.name for m in bpy.data.objects['SCREEN clean unchanged 16 by 9 quad'].data.materials]
    save(RUN/'inspection.json',result)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    if '--inspect' in sys.argv:inspect()
    elif '--preview' in sys.argv:render(True)
    elif '--render' in sys.argv:render()
    elif '--package' in sys.argv:package()
    elif '--review' in sys.argv:review()
