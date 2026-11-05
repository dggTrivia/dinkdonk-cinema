"""Local GPU production driver. All writes belong to out10i, with receipt-based resumption."""
import sys,os,json,time,math,hashlib,copy
from pathlib import Path
sys.dont_write_bytecode=True
WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[1]
OUT=WORK.parent
PIPE=WORK/'pipeline'
sys.path.insert(0,str(PIPE))
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
MODE=sys.argv[sys.argv.index('--')+1]
def record(name,value):
    p=WORK/(name+'.json');tmp=p.with_suffix('.partial');tmp.write_text(json.dumps(value,indent=2));os.replace(tmp,p)
def setup():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'out10h/draft23/draft23-cinemas.blend'))
    sc=bpy.context.scene
    for asset in list(bpy.data.images)+list(bpy.data.fonts):
        if asset.filepath.startswith('//'):asset.filepath=asset.filepath.replace('\\','/')
    housing=sc.objects['D13 compact floodlight housing.001'];pivot=housing.location.copy()
    target=Vector((9.70,.69,244/(60*math.sqrt(2)*math.cos(math.pi/6))))
    # The old housing orientation is baked into its mesh, so infer its actual
    # aperture axis rather than treating the zero Euler rotation as its aim.
    olddirection=(sc.objects['D13 floodlight emitting glass.001'].location-pivot).normalized()
    direction=(target-pivot).normalized();newq=direction.to_track_quat('Z','Y')
    rot=olddirection.rotation_difference(direction)
    head=['D13 compact floodlight housing.001','D13 recessed aluminium reflector.001','D13 floodlight emitting glass.001','D13 truss reflector flood 1']
    old={n:{'location':list(sc.objects[n].location),'rotation':list(sc.objects[n].rotation_euler)} for n in head}
    for n in head:
        ob=sc.objects[n];q=ob.matrix_world.to_quaternion();ob.location=pivot+rot@(ob.location-pivot)
        ob.rotation_mode='QUATERNION';ob.rotation_quaternion=rot@q
    # Four actual matte-black snoot walls shield the lens at oblique viewing angles.
    steel=housing.data.materials[0].copy();steel.name='B56 central flood matte hood'
    for node in steel.node_tree.nodes:
        if node.type=='BSDF_PRINCIPLED':
            node.inputs['Base Color'].default_value=(.012,.013,.012,1);node.inputs['Roughness'].default_value=.8;node.inputs['Metallic'].default_value=.15
    panels=[('top',(0,.088,.11),(.27,.012,.10)),('bottom',(0,-.088,.11),(.27,.012,.10)),('left',(-.132,0,.11),(.012,.18,.10)),('right',(.132,0,.11),(.012,.18,.10))]
    panels += [(f'louver {i}',(x,0,.112),(.002,.17,.09)) for i,x in enumerate(np.arange(-.11,.12,.022))]
    panels += [(f'cross louver {i}',(0,y,.112),(.26,.002,.09)) for i,y in enumerate(np.arange(-.066,.07,.022))]
    for tag,center,size in panels:
        bpy.ops.mesh.primitive_cube_add(size=1,location=pivot+newq@Vector(center));o=bpy.context.object;o.name='B56 central flood hood '+tag;o.rotation_euler=newq.to_euler();o.scale=size;o.data.materials.append(steel);o['cloud_group']='background';o.visible_shadow=False
        bpy.data.collections['D13 sign and local roof light receivers'].objects.link(o)
    # The prior live-video repair resolved roof/body ties in display space. Remove
    # the covered top face in this saved copy so native renders have a sole receiver.
    annex=sc.objects['P8 record and repair annex'];bm=bmesh.new();bm.from_mesh(annex.data)
    bm.normal_update()
    faces=[f for f in bm.faces if all(abs((annex.matrix_world@v.co).z*73.4846922835-58)<.01 for v in f.verts)]
    assert len(faces)==1,len(faces)
    bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(annex.data);bm.free();annex.data.update()
    sc['brief56_production']=True;sc['brief56_bell_timing']='A12/B12, 144 frames at 24 fps, six seconds'
    sc.render.use_border=False;sc.render.use_crop_to_border=False
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(PIPE/'scene.blend'),compress=True)
    record('scene-edits',{'reference':'out10h/draft23/draft23-cinemas.blend','flood_head_before':old,'target_world':list(target),'flood_head_after':{n:{'location':list(sc.objects[n].location),'rotation':list(sc.objects[n].rotation_euler)} for n in head},'hood_objects':len(panels),'lamp_power_unchanged':sc.objects['D13 truss reflector flood 1'].data.energy,'removed_covered_annex_faces':len(faces),'source_sha256':hashlib.sha256((ROOT/'cloud/bundle/scene.blend').read_bytes()).hexdigest()})
    print('BRIEF56 setup complete',flush=True)
def renderer():
    from fast_pipeline import NativeRenderer
    r=NativeRenderer(3840,2160)
    # Draft 23 saved a background-only capture configuration. Restore the
    # original production visibility for independent foreground/weather/door
    # passes. Background selection still excludes those same camera rays.
    reference=json.loads((ROOT/'cache/brief50/scene-inventory.json').read_text())
    assert hashlib.sha256((ROOT/'cloud/bundle/scene.blend').read_bytes()).hexdigest()=='0fa1c86fb297079b0b0b1944cad5d9ae08f6a8babaf2bd558c9a43d35417ef24'
    restored=[]
    for row in reference:
        name=row['name']
        if name in r.visible:
            value=(row['camera'],row['hide'],row['holdout'])
            if r.visible[name]!=value:restored.append(name)
            r.visible[name]=value
    record('restored-production-visibility',{'source_sha256':hashlib.sha256((ROOT/'cloud/bundle/scene.blend').read_bytes()).hexdigest(),'restored_names':restored,'background_camera_selection_unchanged':True})
    r._visibility=None
    bpy.context.preferences.filepaths.temporary_directory=str(WORK/'temp')
    return r
def inspect():
    r=renderer();sc=r.sc
    names=['D13 sign and local roof light receivers','P10 multiplex roof light receivers']
    record('scene-inspection',{'devices':r.devices,'lights':[{ 'name':o.name,'receiver':o.light_linking.receiver_collection.name if o.light_linking.receiver_collection else None,'power':o.data.energy} for o in sc.objects if o.type=='LIGHT' and ('D13' in o.name or 'roof' in o.name)],'collections':{n:[{'name':o.name,'group':o.get('cloud_group','background')} for o in bpy.data.collections[n].objects] for n in names if n in bpy.data.collections},'roofs':[{'name':o.name,'bounds':[[float(v) for v in o.matrix_world@Vector(p)] for p in o.bound_box]} for o in sc.objects if 'gravel roof' in o.name],'groups':[{ 'name':s['name'],'rect':r.rect([sc.objects[n] for n in s['objects']],8),'wet':any(n in r.wet for n in s['objects'])} for s in r.meta['groups']]})
def probe():
    from fast_pipeline import area2
    r=renderer()
    for f in [0,12]:
        a,_=r.capture('sign_probe_'+str(f),part='background',frame=f,rect=[1020,0,840,650],adaptive=True,threshold=.01)
        canvas=np.zeros((2160,3840,4),np.float32);canvas[:1300,2040:3720]=a
        for scale,buf in [(2,canvas),(1,area2(canvas))]:r.display(buf,WORK/f'probe-{f}-{scale}.png',True)
def floodprobe():
    from fast_pipeline import area2
    r=renderer();a,_=r.capture('flood_probe',part='background',frame=0,rect=[1380,145,310,290],adaptive=True,threshold=.01)
    canvas=np.zeros((2160,3840,4),np.float32);canvas[290:870,2760:3380]=a
    r.display(canvas,WORK/'flood-probe.png',True)
def backgrounds():
    from fast_pipeline import area2
    from runtime import WORK as CACHE,rgba8,png,atomic_json,diff
    r=renderer();proof=[]
    for f in list(range(48))+[144]:
        a,secs=r.capture(f'background_2_{f:03}',part='background',frame=f,adaptive=True,threshold=.01)
        for scale,buf in [(2,a),(1,area2(a))]:
            folder=CACHE/f'background_{scale}';folder.mkdir(exist_ok=True);path=folder/f'f{f:03}.png'
            if not path.exists():r.display(buf,path,True)
        if f==144:
            from runtime import pixels
            d=diff(a,pixels(CACHE/'buffers/background_2_000.exr'));proof.append({'endpoint':144,'reference':0,'linear_diff':d});assert d['mean']<.0001 and d['p99']<.001,d
    excludes=[n for n in ['D5 periodic wet micro impacts','D3 thin steam plume','D10 stateless edge drips and impact crowns','D10 stateless gutter and AC pours'] if n in r.sc.objects]
    dry,_=r.capture('dry_fallback_2',part='background',exclude=excludes,adaptive=True,threshold=.01)
    for scale in [1,2]:
        folder=CACHE/f'background_{scale}';minimum=None
        for f in range(48):
            p=rgba8(folder/f'f{f:03}.png');p[:,:,3]=255;minimum=p.copy() if minimum is None else np.minimum(minimum,p)
        suffix='@2x' if scale==2 else ''
        for stem in ['base','bg']:png(OUT/(stem+suffix+'.png'),minimum)
        import shutil
        shutil.copyfile(folder/'f000.png',OUT/('lit_bg'+suffix+'.png'))
        r.display(dry if scale==2 else area2(dry),OUT/('lit_bg_dry'+suffix+'.png'),True)
        dest=CACHE/f'light_loop_{scale}';dest.mkdir(exist_ok=True)
        for f in range(48):
            p=rgba8(folder/f'f{f:03}.png');delta=np.maximum(p[:,:,:3].astype(np.int16)-minimum[:,:,:3],0).astype(np.uint8);png(dest/f'f{f:03}.png',delta)
            assert np.array_equal(minimum[:,:,:3].astype(np.uint16)+delta,p[:,:,:3])
    atomic_json(CACHE/'background-endpoints.json',proof)
def foreground():
    from fast_pipeline import area2
    from runtime import WORK as CACHE,rgba8,png,pixels,diff,atomic_json
    from production import INTERIOR_STATIC,sheet
    r=renderer();m=json.loads((OUT/'manifest.json').read_text());proof=[]
    for e in m['occluders']:
        name=e['name'];rect=[e[k] for k in ['x','y','w','h']]
        wet=[p for p in m['prop_loops'] if p['name'].startswith('wet_') and p['parent']==name]
        phases=list(range(0,48,2)) if wet else [0]
        for f in phases+([144] if wet else []):
            a,_=r.capture(f'fg_{name}_{f:03}',part=name,frame=f,rect=rect,adaptive=True,threshold=.01)
            for scale,buf in [(2,a),(1,area2(a))]:
                folder=CACHE/f'fg_{name}_{scale}';folder.mkdir(exist_ok=True);p=folder/f'f{f:03}.png'
                if not p.exists():r.display(buf,p,False)
            if f==144:
                d=diff(a,pixels(CACHE/f'buffers/fg_{name}_000.exr'));assert d['mean']<.0001 and d['p99']<.001,(name,d)
                proof.append({'parent':name,'endpoint144':d})
        for scale,key in [(1,'file'),(2,'file_2x')]:
            folder=CACHE/f'fg_{name}_{scale}';original=rgba8(ROOT/'out10'/e[key]);minimum=None
            for f in phases:
                a=rgba8(folder/f'f{f:03}.png');assert a.shape==original.shape,(name,a.shape,original.shape)
                minimum=a.copy() if minimum is None else np.minimum(minimum,a)
            # Geometry/crop/ownership is unchanged. Preserve the exact live edge
            # coverage and disjoint AOV-derived depth ownership at each resolution.
            minimum[:,:,3]=original[:,:,3];minimum[minimum[:,:,3]==0]=0;png(OUT/e[key],minimum)
            reconstructed=np.zeros_like(minimum)
            for piece in e['depth_slices']:
                old=rgba8(ROOT/'out10'/piece[key]);x=(piece['x']-e['x'])*scale;y=(piece['y']-e['y'])*scale;h,w=old.shape[:2]
                new=minimum[y:y+h,x:x+w].copy();new[old[:,:,3]==0]=0;new[:,:,3]=old[:,:,3]
                png(OUT/piece[key],new)
                region=reconstructed[y:y+h,x:x+w];assert not np.any((region[:,:,3]>0)&(new[:,:,3]>0));region+=new
            if e['depth_slices']:assert np.array_equal(reconstructed,minimum),('slice reconstruction',name,scale)
            for p in wet:
                piece=next(q for q in e['depth_slices'] if q['name']==p['parent_slices'][0]);mask=rgba8(ROOT/'out10'/piece[key])[:,:,3]
                x=(piece['x']-e['x'])*scale;y=(piece['y']-e['y'])*scale;h,w=mask.shape;base=minimum[y:y+h,x:x+w,:3];frames=[]
                for f in range(48):
                    a=rgba8(folder/f'f{f//2*2:03}.png')[y:y+h,x:x+w,:3]
                    rgb=np.rint(np.maximum(a.astype(np.int16)-base,0).astype(np.float32)*(mask[:,:,None]/255)).astype(np.uint8)
                    frames.append(np.dstack([rgb,np.full((h,w),255,np.uint8)]))
                sheet(frames,OUT/p[key])
        atomic_json(CACHE/'foreground-endpoints.json',proof)
        print('BRIEF56 foreground delivered',name,flush=True)
def weather():
    from fast_pipeline import area2
    from runtime import WORK as CACHE,rgba8,png,pixels,diff,atomic_json
    r=renderer();folder=CACHE/'rain_fg_1';folder.mkdir(exist_ok=True)
    for f in list(range(48))+[144]:
        a,_=r.capture(f'weather_{f:03}',part='weather',rain=True,frame=f,adaptive=True,threshold=.01)
        dest=folder/f'f{f:03}.png'
        if not dest.exists():
            r.display(area2(a),CACHE/'weather_display.png',False);p=rgba8(CACHE/'weather_display.png');png(dest,np.rint(p[:,:,:3]*(p[:,:,3:4]/255)).astype(np.uint8))
        if f==144:
            d=diff(a,pixels(CACHE/'buffers/weather_000.exr'));assert d['mean']<.0001 and d['p99']<.001,d;atomic_json(CACHE/'weather-endpoint.json',d)
def doors():
    from fast_pipeline import area2
    from runtime import WORK as CACHE,rgba8,png
    from production import pose,sheet
    r=renderer();m=json.loads((OUT/'manifest.json').read_text())
    entries=m['door_anims']+[m['restroom']['door_anim']]+[s['door_anim'] for s in m['restroom']['stalls']]
    for e in entries:
        obs=[o for o in r.sc.objects if o.get('anim_id')==e['id']];assert obs,e['id']
        frames={1:[],2:[]};rect=[e[k] for k in ['x','y','w','h']]
        for f in range(6):
            pose(obs,.5-.5*math.cos(math.pi*f/5))
            a,_=r.capture(f"door_{e['id']}_{f}",part='all',rect=rect,state={'door':e['id'],'pose':f},adaptive=True,threshold=.01)
            for scale,buf in [(2,a),(1,area2(a))]:
                p=CACHE/f"door_{e['id']}_{f}_{scale}.png"
                if not p.exists():r.display(buf,p,False)
                frames[scale].append(rgba8(p))
        for scale,key in [(1,'file'),(2,'file_2x')]:
            old=rgba8(ROOT/'out10'/e[key]);h=e['h']*scale;w=e['w']*scale;seq=[]
            for i in range(16):
                a=frames[scale][min(i,15-i,5)].copy();a[:,:,3]=old[i//4*h:(i//4+1)*h,i%4*w:(i%4+1)*w,3];a[a[:,:,3]==0]=0;seq.append(a)
            sheet(seq,OUT/e[key],4)
        pose(obs,0)
    obs=[o for o in r.sc.objects if o.get('cloud_group')=='wc_dynamic'];labels=[o for o in obs if o.type=='FONT']
    ma=bpy.data.materials['Cloud independent WC state'];p=ma.node_tree.nodes.get('Principled BSDF')
    for state,text,color in [('vacant','VACANT',(.1,1,.25)),('occupied','OCCUPIED',(1,.035,.025))]:
        for o in labels:o.data.body=text;o.data.size=.058 if state=='vacant' else .0435
        p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=2
        e=m['wc_indicator'][state];a,_=r.capture('wc_'+state,part='wc_dynamic',rect=[e[k] for k in ['x','y','w','h']],state={'wc':state},adaptive=True,threshold=.01)
        for scale,key in [(1,'file'),(2,'file_2x')]:r.display(a if scale==2 else area2(a),OUT/e[key],False)
def package():
    import production as p
    p.OUT=OUT;p.QA=WORK/'qa';p.QA.mkdir(exist_ok=True)
    m=json.loads((OUT/'manifest.json').read_text());r=renderer()
    p.full_stills_ads(r,m)
    m['baked_signs']=[s if s!='DINK DONK' else 'DINK DONK CINEMAS' for s in m['baked_signs']]
    m['asset_pack_revision']='brief56-draft23-dinkdonk-cinemas'
    m['cloud_contract']['neon']='two separate physical tube circuits alternate every 12 frames (0.50 seconds); off circuit remains dark glass'
    m['cloud_contract']['approved_draft']=23
    m['loop_note'] += ' DINK DONK bell holds A12/B12 (0.50 seconds/state); CINEMAS and shielded central flood are baked into this pack.'
    p.save_manifest(m)
def videos():
    from video import encode_and_validate
    from runtime import WORK as CACHE
    for name,scale in [('light_loop',1),('light_loop_2x',2),('rain_fg',1)]:
        folder=CACHE/(f'light_loop_{scale}' if name.startswith('light') else 'rain_fg_1')
        encode_and_validate(name,folder,OUT,scale)
def mist():
    import runpy
    dest=WORK/'mist';dest.mkdir(exist_ok=True);(dest/'temp').mkdir(exist_ok=True)
    src=(ROOT/'cache/brief50/render_mist.py').read_text(encoding='utf-8')
    src=src.replace("WORK=ROOT/'cache/brief50'; OUT=ROOT/'out10mist'","WORK=ROOT/'out10i/_work/mist'; OUT=ROOT/'out10i'")
    src=src.replace("ROOT/'cloud/bundle/scene.blend'","ROOT/'out10i/_work/pipeline/scene.blend'")
    src=src.replace(' phase(sc)\n rows=[]'," for row in json.loads((ROOT/'cache/brief50/scene-inventory.json').read_text()):\n  o=sc.objects.get(row['name'])\n  if o:o.visible_camera=row['camera'];o.hide_render=row['hide'];o.is_holdout=row['holdout']\n phase(sc)\n rows=[]")
    src=src.replace(" for o in sc.objects:\n  if o.type=='LIGHT':o.hide_render=True"," for o in sc.objects:\n  if o.name.startswith('B56 central flood hood '):o.visible_shadow=True\n  if o.type=='LIGHT':o.hide_render=True")
    target=WORK/'mist56.py';target.write_text(src)
    for mode in ['catch','light']:
        sentinel=OUT/('height@2x.png' if mode=='catch' else 'light@2x.png')
        if sentinel.exists():continue
        sys.argv=[str(target),'--',mode];runpy.run_path(str(target),run_name='__main__')
if MODE=='setup':setup()
elif MODE=='inspect':inspect()
elif MODE=='probe':probe()
elif MODE=='floodprobe':floodprobe()
elif MODE=='backgrounds':backgrounds()
elif MODE=='foreground':foreground()
elif MODE=='weather':weather()
elif MODE=='doors':doors()
elif MODE=='package':package()
elif MODE=='videos':videos()
elif MODE=='mist':mist()
else:raise ValueError(MODE)
