"""Fail-closed contract checks, independent of image generation stages."""
import json,math,hashlib,struct
from pathlib import Path
import bpy,numpy as np
from common import ROOT
from runtime import WORK,sha,rgba8,atomic_json,log,within

def dimensions(path):
    with Path(path).open('rb') as f:h=f.read(24)
    assert h[:8]==b'\x89PNG\r\n\x1a\n',path
    return list(struct.unpack('>II',h[16:24]))

def routes(m):
    colliders=json.loads((ROOT/'assets/restroom_colliders.json').read_text());paths=[s['route_points'] for s in m['restroom']['stalls']]+m['restroom']['route_points']['sinks']+[m['restroom']['route_points']['dryer']];hits=[];points=0
    for index,path in enumerate(paths):
        for a,b in zip(path,path[1:]):
            # At most .02 tile between probes; conservative AABBs inflated by
            # .07 tile represent a standing agent's radius at fixture height.
            for q in np.linspace(a,b,max(2,math.ceil(math.dist(a,b)/.02)+1)):
                points+=1
                for o in colliders:
                    x,y,r,d,z,h=o['bounds']
                    if x-.07<q[0]<r+.07 and y-.07<q[1]<d+.07:hits.append({'route':index,'fixture':o['name'],'point':q.tolist()})
    return {'passed':not hits,'route_count':len(paths),'sample_count':points,'agent_radius_tiles':.07,'max_sample_spacing_tiles':.02,'fixture_aabb_collisions':hits}

def preflight(r=None):
    from runtime import Renderer
    if r is None:r=Renderer()
    m=json.loads((ROOT/'manifest.template.json').read_text());info=json.loads((ROOT/'bundle.json').read_text());assert sha(ROOT/'scene.blend')==info['scene_sha256']
    packed=[]
    for im in bpy.data.images:
        if im.source=='FILE':assert im.packed_file and im.filepath.startswith(('//assets/', '//../../../cloud/bundle/assets/')) and '\\' not in im.filepath,(im.name,im.filepath);packed.append(im.name)
    for font in bpy.data.fonts:
        if font.filepath!='<builtin>':assert font.packed_file and font.filepath.startswith(('//assets/', '//../../../cloud/bundle/assets/')) and '\\' not in font.filepath,(font.name,font.filepath)
    assert not bpy.data.libraries
    assert m['layout']==3 and [d['screen'] for d in m['doors']]==[1,2,3]
    assert [d['at'] for d in m['doors']]==[4.8,8.2,11.2]
    assert [e['door'] for e in m['led_signs']]==[1,2,3] and [e['screen'] for e in m['poster_frames']]==[1,2,3]
    assert len(r.meta['animations'])==8 and len(m['restroom']['stalls'])==4 and len(m['queue']['slots'])==7
    assert {'wcat','eatfresh','shelter','paste_wall'}<=set(a['name'] for a in m['ad_surfaces'])
    assigned={n for e in r.meta['groups'] for n in e['objects']}
    assert len(assigned)==sum(len(e['objects']) for e in r.meta['groups'])
    assert all(n in r.sc.objects for n in assigned)
    for e in r.meta['animations']:assert any(o.get('anim_id')==e['id'] for o in r.sc.objects),e['id']
    def phase_digest(f):
        r.phase(f);coords=np.empty(len(r.sc.objects['D5 periodic wet micro impacts'].data.vertices)*3,np.float32);r.sc.objects['D5 periodic wet micro impacts'].data.vertices.foreach_get('co',coords)
        state=[(o.name,o.data.materials[0].name) for o in r.sc.objects if o.get('d6_tube_state')]
        state+= [(o.name,ma.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value) for o,ma,g in r.chase]
        # Evaluated pour geometry proves Scene Time, beyond a frame counter.
        deps=bpy.context.evaluated_depsgraph_get();pour=r.sc.objects['D10 stateless gutter and AC pours'].evaluated_get(deps);mesh=pour.to_mesh()
        pp=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',pp);pour.to_mesh_clear();assert len(pp)>0
        instances=[]
        for inst in deps.object_instances:
            if inst.is_instance and inst.parent and inst.parent.original.name=='D10 stateless edge drips and impact crowns':instances.append([v for row in inst.matrix_world for v in row])
        assert instances,'GN drips/crowns have no evaluated instances'
        data=coords.tobytes()+pp.tobytes()+np.asarray(instances,np.float32).tobytes()+np.array([list(o.location) for o,_,_,_ in r.rain],np.float32).tobytes()+json.dumps(state).encode();return hashlib.sha256(data).hexdigest()
    p0=phase_digest(0);p6=phase_digest(6);p48=phase_digest(48);assert p0==p48 and p0!=p6
    r.visibility('weather',rain=True);bad=[];volumes=[]
    for name in r.original:
        o=r.sc.objects[name]
        camera,hidden,original_holdout=r.visible[name]
        if hidden or not camera:
            if o.hide_render!=hidden or (not camera and o.visible_camera):bad.append(name)
            continue
        outputs=[n for ma in o.data.materials if ma and ma.node_tree for n in ma.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output]
        if outputs and all(not n.inputs['Surface'].links for n in outputs):
            volumes.append(name)
            if o.visible_camera:bad.append(name)
            continue
        if not o.visible_camera or (not o.is_holdout and (not o.data.materials or any(not any(n.type=='HOLDOUT' for n in ma.node_tree.nodes) for ma in o.data.materials if ma))):bad.append(name)
    assert not bad,('Weather holdout missing',bad)
    route=routes(m);assert route['passed'],route
    r.visibility();r.phase(0)
    assert len(r.chase)==78
    floods=[o for o in r.sc.objects if o.name.startswith('D13 truss reflector flood ')]
    assert sorted(round(o.data.energy) for o in floods)==[24,28,28]
    assert round(r.sc.objects['P10 restroom soft ceiling'].data.energy)==44
    for name in ['D10 stateless edge drips and impact crowns','D10 stateless gutter and AC pours']:assert not r.sc.objects[name].cycles.use_motion_blur
    assert r.sc.objects['D10 static model raycast target'].hide_render
    catchers=[o for o in r.sc.objects if o.get('reflection_only')]
    assert catchers and all(not o.visible_camera and o.visible_glossy for o in catchers)
    assert all('D10 wet ' in o.data.materials[0].name for o in r.sc.objects if o.get('d6_tube_state'))
    report={'passed':True,'blender':bpy.app.version_string,'devices':r.devices,'packed_images':len(packed),'linked_libraries':0,'relative_paths':True,'foreground_groups':len(r.meta['groups']),'foreground_objects':len(assigned),'doors':8,'periodic_state_sha256':p0,'phase_6_differs':p0!=p6,'phase_48_equals_0':p0==p48,'weather_holdout_objects':len(r.original)-len(volumes),'weather_excluded_volume_objects':volumes,'weather_holdout_mismatches':len(bad),'restroom_routes':route,'aperture':{'applicable':False,'reason':'out9 retired the green aperture; layout 3 uses perspective ad surfaces.'},'scope':'Geometry, paths, state periodicity and contracts only; no production frames rendered.'}
    report['draft13']={'marquee_bulbs':len(r.chase),'flood_watts':[o.data.energy for o in floods],'restroom_watts':44,'hidden_reflection_catchers':len(catchers),'gn_rain_sharp':True,'gn_pours_and_drip_instances_in_periodic_digest':True,'neon_wet_layer_retained':True}
    report['scene_sha256']=r.signature
    report['weather_preserved_hidden_objects']=[name for name,(camera,hidden,holdout) in r.visible.items() if hidden]
    report['weather_camera_invisible_objects']=[name for name,(camera,hidden,holdout) in r.visible.items() if not camera and not hidden]
    report['weather_holdout_objects']=sum(camera and not hidden and name not in volumes for name,(camera,hidden,holdout) in r.visible.items())
    atomic_json(ROOT/'preflight.json',report);log('preflight_passed',foreground_groups=report['foreground_groups'],doors=8);return report

def validate(m,out,qa,smoke_size=None):
    from production import referenced_files
    failures=[];checks={};files=referenced_files(m)
    missing=[f for f in files if not (out/f).is_file()];checks['missing_files']=missing
    if missing:failures.append('Missing referenced assets')
    assert not missing,missing
    checks['layout_3']=m['layout']==3 and len(m['doors'])==3 and len(m['door_anims'])==3 and len(m['restroom']['stalls'])==4
    checks['routes']=routes(m)
    if not checks['layout_3'] or not checks['routes']['passed']:failures.append('Layout or reachable routes failed')
    dimensions_checked=0;max_slice_error=0
    for e in m['occluders']:
        for scale,key in [(1,'file'),(2,'file_2x')]:
            parent=rgba8(out/e[key]);assert parent.shape==(e['h']*scale,e['w']*scale,4);recon=np.zeros_like(parent,np.uint16)
            for s in e['depth_slices']:
                a=rgba8(out/s[key]);x=(s['x']-e['x'])*scale;y=(s['y']-e['y'])*scale;assert a.shape==(s['h']*scale,s['w']*scale,4);recon[y:y+a.shape[0],x:x+a.shape[1]]+=a;dimensions_checked+=1
            error=int(np.abs(recon.astype(np.int32)-parent.astype(np.int32)).max());max_slice_error=max(error,max_slice_error)
    checks['depth_slice_reconstruction_max_error']=max_slice_error
    if max_slice_error:failures.append('Depth slices do not reconstruct their parents')
    sheets=m['prop_loops']+m['door_anims']+[m['restroom']['door_anim']]+[s['door_anim'] for s in m['restroom']['stalls']]
    for e in sheets:
        for scale,key in [(1,'file'),(2,'file_2x')]:
            assert dimensions(out/e[key])==[e['frame_width']*e['columns']*scale,e['frame_height']*e['rows']*scale],e['file'];dimensions_checked+=1
        assert e['frames']<=e['columns']*e['rows']
    for e in m['door_anims']+[m['restroom']['door_anim']]+[s['door_anim'] for s in m['restroom']['stalls']]:
        a=rgba8(out/e['file']);w=e['frame_width'];h=e['frame_height'];assert np.array_equal(a[:h,:w],a[3*h:4*h,3*w:4*w]),('Door endpoints differ',e['id'])
    for stem in ['bg','base','lit_bg','lit_bg_dry','full']:
        size=smoke_size or [1920,1080]
        assert dimensions(out/(stem+'.png'))==size;assert dimensions(out/(stem+'@2x.png'))==[v*2 for v in size];dimensions_checked+=2
    checks['png_dimensions_checked']=dimensions_checked
    endpoints=json.loads((qa/'periodic_endpoints.json').read_text());checks['periodic_endpoints']=endpoints
    for e in endpoints:
        if not within(e['wrapped_linear_difference'],e['noise_baseline']):failures.append('Periodic endpoint exceeds noise baseline')
    videos=json.loads((qa/'videos.json').read_text());checks['videos']=videos
    for name,v in videos.items():
        if not v['passed'] or v['frames']!=144 or sha(out/v['file'])!=v['sha256']:failures.append('Video failed '+name)
    bus=json.loads((qa/'bus_validation.json').read_text());checks['bus_depth_slices']=bus
    if len(bus)!=8 or any(e['max_error']!=0 for e in bus):failures.append('Bus body depth slice validation failed')
    scene=json.loads((ROOT/'preflight.json').read_text());checks['scene_preflight']=scene
    checks['referenced_files']=len(files);checks['native_resolutions']=[[1920,1080],[3840,2160]] if smoke_size is None else None
    return {'passed':not failures,'failures':failures,'checks':checks,'scope':'Full production pack, native images, sprite reconstruction, periodic endpoints, VP9 decoding and black levels. Not a browser playback test.' if smoke_size is None else 'Bounded smoke packaging: real still pixels with repeated-frame codec and sheet fixtures; no animation or native full-pack proof.'}
