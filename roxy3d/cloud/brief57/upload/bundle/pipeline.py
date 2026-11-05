"""Portable orchestration of the byte-identical Brief 56 production driver."""
import hashlib, json, os, runpy, shutil, subprocess, sys, tarfile, time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parent
W=ROOT/'out10i/_work'; PIPE=W/'pipeline'; OUT=W.parent
sys.path.insert(0,str(PIPE))
import bpy, numpy as np
from runtime import atomic_json, sha, rgba8, png
from fast_pipeline import area2
from mathutils import Vector

STAGES=['backgrounds','weather','foreground','doors','mist','package','videos']
MIST=[n+s+'.png' for n in ['catch','height','rim','light'] for s in ['', '@2x']]

def event(stage,**data):
    line=json.dumps({'time':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'stage':stage,**data})
    print('BRIEF57 '+line,flush=True)
    with (ROOT/'progress.log').open('a',encoding='utf-8') as f:f.write(line+'\n')

def driver(mode):
    saved=sys.argv[:]
    try:
        sys.argv=[str(W/'production56.py'),'--',mode]
        return runpy.run_path(str(W/'production56.py'),run_name='__main__')
    finally:sys.argv=saved

def integrity():
    count=0
    for line in (ROOT/'BUNDLE-SHA256SUMS').read_text().splitlines():
        digest,rel=line.split('  ',1);p=ROOT/rel
        assert p.resolve().is_relative_to(ROOT) and sha(p)==digest,rel
        count+=1
    info=json.loads((ROOT/'brief57.json').read_text())
    assert sha(PIPE/'scene.blend')==info['scene_sha256']
    assert sha(PIPE/'runtime.py')==info['runtime_sha256']
    assert sha(W/'production56.py')==info['driver_sha256']
    assert os.environ.get('ROXY_WET_FRAMES','24')=='24','Brief 56 fixes 24 wet phases'
    return info,count

def preflight():
    info,count=integrity()
    api=driver('inspect');r=api['renderer']()
    from validation import preflight as existing_preflight
    report=existing_preflight(r)
    fallback_paths=[]
    for asset in list(bpy.data.images)+list(bpy.data.fonts):
        if asset.filepath.startswith('//'):
            path=Path(bpy.path.abspath(asset.filepath)).resolve()
            assert path.is_relative_to(ROOT) and path.is_file(),(asset.name,str(path))
            fallback_paths.append(path.relative_to(ROOT).as_posix())
    assert r.sc.get('brief56_production')
    glyphs=sorted({o.name.split()[3] for o in r.sc.objects if o.name.startswith('B54 CINEMAS ') and ' glass ' in o.name})
    assert glyphs==sorted(set('CINEMAS')),glyphs
    proof=json.loads((W/'scene-verification.json').read_text());assert proof['passed']
    assert sorted(o.name for o in r.sc.objects if o.name.startswith('B56 central flood hood '))==proof['new_shield_objects']
    target=Vector(json.loads((W/'scene-edits.json').read_text())['target_world'])
    lamp=r.sc.objects['D13 truss reflector flood 1']
    aim=lamp.matrix_world.to_quaternion()@Vector((0,0,-1))
    dot=aim.normalized().dot((target-lamp.location).normalized());assert dot>.9999
    states=[]
    # Assert actual selected tube materials, including the 143 -> 0 boundary.
    for f in range(145):
        r.phase(f);expected='A' if f//12%2==0 else 'B'
        for ob in r.circuits:
            key=ob['d6_on_material'] if ob['d6_tube_state']==expected else 'D6 unlit neon glass'
            assert r.original[ob.name][0]==r.circuit_materials[key],(f,ob.name)
        states.append(expected)
    assert states[143]=='B' and states[144]=='A'
    assert r.sc.cycles.samples==256 and r.sc.cycles.adaptive_min_samples==64
    assert r.sc.cycles.denoiser=='OPTIX' and r.sc.cycles.seed==1701
    report.update(brief=57,production=56,sign='CINEMAS',bell_states=states,
                  A12_B12_passed=True,central_lamp_aim_dot=dot,bundle_files_verified=count,
                  exact_frozen_scene=True,exact_driver=True,exact_runtime=True,
                  production_settings=info['sampling'],wet_unique_phases=24,
                  fallback_asset_paths_verified=fallback_paths)
    atomic_json(ROOT/'preflight.json',report)
    event('preflight_passed',files=count,sign='CINEMAS',bell='A12/B12',mist_included=True)
    r.phase(0)
    return r,report

def inventory(out,work=False):
    return {p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*'))
            if p.is_file() and (work or '_work' not in p.relative_to(out).parts) and p.name!='checksums.json'}

def seal_result(out,target,evidence=None):
    """One shared smoke/full checksum and archive member verification path."""
    out=Path(out);target=Path(target)
    assert out.resolve().is_relative_to(ROOT) and target.resolve().is_relative_to(ROOT)
    files={rel:out/rel for rel in inventory(out)}
    if evidence:
        for rel,p in evidence.items():
            name='_work/cloud57/'+rel
            assert '..' not in Path(name).parts and name not in files
            files[name]=p
    rows=[{'file':rel,'bytes':p.stat().st_size,'sha256':sha(p)} for rel,p in sorted(files.items())]
    atomic_json(out/'checksums.json',rows);files['checksums.json']=out/'checksums.json'
    temp=target.with_suffix('.partial')
    with tarfile.open(temp,'w:gz',compresslevel=3) as tar:
        for rel,p in sorted(files.items()):tar.add(p,arcname='out10/'+rel,recursive=False)
    expected={rel:sha(p) for rel,p in files.items()}
    with tarfile.open(temp) as tar:
        members=tar.getmembers();assert len(members)==len(expected)
        assert {m.name for m in members}=={'out10/'+r for r in expected}
        for m in members:
            assert m.isfile() and hashlib.sha256(tar.extractfile(m).read()).hexdigest()==expected[m.name[6:]],m.name
    os.replace(temp,target)
    result={'passed':True,'archive':target.name,'files':len(files),'bytes':target.stat().st_size,'sha256':sha(target),'member_hashes_verified':True}
    event('archive_verified',**result);return result

def smoke_mist():
    # Apply exactly production56.mist's source/visibility/hood substitutions,
    # then bound only this diagnostic's dimensions and output directories.
    src=(ROOT/'cache/brief50/render_mist.py').read_text()
    src=src.replace("WORK=ROOT/'cache/brief50'; OUT=ROOT/'out10mist'", "WORK=ROOT/'out10i/_work/mist-smoke'; OUT=ROOT/'smoke/mist'")
    src=src.replace("ROOT/'cloud/bundle/scene.blend'", "ROOT/'out10i/_work/pipeline/scene.blend'")
    src=src.replace(' phase(sc)\n rows=[]', " for row in json.loads((ROOT/'cache/brief50/scene-inventory.json').read_text()):\n  o=sc.objects.get(row['name'])\n  if o:o.visible_camera=row['camera'];o.hide_render=row['hide'];o.is_holdout=row['holdout']\n phase(sc)\n rows=[]")
    src=src.replace(" for o in sc.objects:\n  if o.type=='LIGHT':o.hide_render=True", " for o in sc.objects:\n  if o.name.startswith('B56 central flood hood '):o.visible_shadow=True\n  if o.type=='LIGHT':o.hide_render=True")
    src=src.replace('def config(sc,w=3840,h=2160,', 'def config(sc,w=320,h=180,')
    src=src.replace('resolution=[3840,2160]', 'resolution=[320,180]')
    folder=W/'mist-smoke';(folder/'temp').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'cache/brief50/scene-inventory.json',folder/'scene-inventory.json')
    script=W/'mist-smoke57.py';script.write_text(src,encoding='utf-8')
    saved=sys.argv[:]
    try:
        for mode in ['catch','light']:
            sys.argv=[str(script),'--',mode];runpy.run_path(str(script),run_name='__main__')
    finally:sys.argv=saved
    for suffix in ['', '@2x']:
        c=rgba8(ROOT/'smoke/mist'/('catch'+suffix+'.png'))[:,:,0]
        assert c.max()>0
        assert np.all(rgba8(ROOT/'smoke/mist'/('rim'+suffix+'.png'))[:,:,0]<=c)
        for name in ['height','light']:assert np.all(rgba8(ROOT/'smoke/mist'/(name+suffix+'.png'))[:,:,:3][c==0]==0)

def smoke():
    start=time.perf_counter();r,proof=preflight()
    folder=ROOT/'smoke';folder.mkdir(exist_ok=True)
    r.width=640;r.height=360;shots=[]
    for f in [0,12]:
        a,_=r.capture('brief57_smoke_sign_'+str(f),part='background',frame=f,rect=[1020,0,840,648],adaptive=True,threshold=.01)
        assert a.shape[:2]==(216,280),a.shape
        r.display(a,folder/f'sign-{f}.png',True);shots.append(rgba8(folder/f'sign-{f}.png'))
    assert float(np.abs(shots[0].astype(float)-shots[1]).mean())>.01
    from production import sheet
    pack=folder/'pack';pack.mkdir(exist_ok=True)
    sheet([shots[i//12%2] for i in range(48)],pack/'wet_fixture.png')
    sheet([shots[0]]*16,pack/'door_fixture.png',4)
    # Actual A/B sign deltas with a wide black border exercise the existing codec
    # path and all six-second/repetition branches, without production pixels.
    minimum=np.minimum(shots[0][:,:,:3],shots[1][:,:,:3])
    frames=folder/'frames';frames.mkdir(exist_ok=True)
    for f in range(48):
        delta=shots[f//12%2][:,:,:3]-minimum
        png(frames/f'f{f:03}.png',np.pad(delta,((32,32),(32,32),(0,0))))
    from video import encode_and_validate
    video=encode_and_validate('brief57_smoke',frames,pack)
    smoke_mist()
    for name in MIST:shutil.copyfile(folder/'mist'/name,pack/name)
    atomic_json(pack/'manifest.json',{'scope':'Tiny diagnostic only','wet':'wet_fixture.png','door':'door_fixture.png','video':video['file'],'mist':MIST})
    archive=seal_result(pack,folder/'out10.tar.gz')
    report={'passed':True,'scope':'Tiny local smoke only; no full production, Linux or visual/page acceptance claimed',
            'sign_crop_size':[280,216],'mist_2x_size':[320,180],'A12_B12_passed':proof['A12_B12_passed'],
            'video':video,'archive':archive,'mist_maps':MIST,'seconds':time.perf_counter()-start}
    atomic_json(folder/'validation.json',report);event('smoke_complete',seconds=report['seconds'])

def initialize():
    info,count=integrity();identity=sha(ROOT/'BUNDLE-SHA256SUMS')
    state=W/'cloud57-state.json'
    if state.exists():assert json.loads(state.read_text())['identity']==identity,'Foreign production output; use a fresh bundle'
    else:
        for p in (ROOT/'out10').rglob('*'):
            if p.is_file():
                dest=OUT/p.relative_to(ROOT/'out10');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        atomic_json(state,{'identity':identity,'production':56,'created':time.time()})
        atomic_json(OUT/'validation.json',{'passed':False,'brief':56,'status':'cloud_render_pending'})
    (W/'mist/temp').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'cache/brief50/scene-inventory.json',W/'mist/scene-inventory.json')
    return identity

def audit():
    from production import referenced_files
    m=json.loads((OUT/'manifest.json').read_text());old=json.loads((ROOT/'out10/manifest.json').read_text())
    baseline=json.loads((ROOT/'baseline-sha256.json').read_text());payload=inventory(OUT)
    assert m.keys()==old.keys()
    assert {k for k in m if m[k]!=old[k]}<={'baked_signs','asset_pack_revision','loop_note','cloud_contract','full_composition','status'}
    assert set(baseline)-{'checksums.json'}<=set(payload)
    assert not [f for f in referenced_files(m) if not (OUT/f).is_file()]
    for rel in payload:
        if rel in baseline and rel.endswith('.png'):
            assert (OUT/rel).read_bytes()[16:24]==(ROOT/'out10'/rel).read_bytes()[16:24],rel
    for e in m['occluders']:
        for scale,key in [(1,'file'),(2,'file_2x')]:
            parent=rgba8(OUT/e[key]);recon=np.zeros_like(parent);count=np.zeros(parent.shape[:2],np.uint8)
            for q in e['depth_slices']:
                a=rgba8(OUT/q[key]);x=(q['x']-e['x'])*scale;y=(q['y']-e['y'])*scale;h,w=a.shape[:2]
                recon[y:y+h,x:x+w]+=a;count[y:y+h,x:x+w]+=(a[:,:,3]>0).astype(np.uint8)
            if e['depth_slices']:assert np.array_equal(recon,parent) and count.max()<=1,e['name']
            assert np.array_equal(parent[:,:,3],rgba8(ROOT/'out10'/e[key])[:,:,3]),e['name']
    loops=[]
    for e in m['prop_loops']:
        if not e['name'].startswith('wet_'):continue
        for scale,key in [(1,'file'),(2,'file_2x')]:
            a=rgba8(OUT/e[key]);h=e['frame_height']*scale;w=e['frame_width']*scale
            seq=[a[f//8*h:(f//8+1)*h,f%8*w:(f%8+1)*w,:3].astype(np.int16) for f in range(48)]
            assert all(np.array_equal(seq[f],seq[f+1]) for f in range(0,48,2))
            steps=[float(np.abs(seq[(f+1)%48]-seq[f]).mean()) for f in range(48)]
            assert steps[-1]<=max(.05,max(steps[:-1])*1.35),e['name']
            loops.append({'file':e[key],'wrap':steps[-1],'max_ordinary':max(steps[:-1]),'paired_frames':True})
    for suffix in ['', '@2x']:
        c=rgba8(OUT/('catch'+suffix+'.png'))[:,:,0]
        for name in ['rim','height','light']:
            a=rgba8(OUT/(name+suffix+'.png'))
            if name=='rim':assert np.all(a[:,:,0]<=c)
            else:assert np.all(a[:,:,:3][c==0]==0)
    inherited=[p for p in payload if p.startswith(('vehicles/','umbrella/'))]
    assert all(payload[p]==baseline[p] for p in inherited)
    receipts=[]
    expected={f'background_2_{f:03}' for f in list(range(48))+[144]}|{'dry_fallback_2'}
    expected|={f'weather_{f:03}' for f in list(range(48))+[144]}
    for e in m['occluders']:
        wet=any(p['name'].startswith('wet_') and p['parent']==e['name'] for p in m['prop_loops'])
        expected|={f"fg_{e['name']}_{f:03}" for f in (list(range(0,48,2))+[144] if wet else [0])}
    for e in m['door_anims']+[m['restroom']['door_anim']]+[s['door_anim'] for s in m['restroom']['stalls']]:
        expected|={f"door_{e['id']}_{f}" for f in range(6)}
    expected|={'wc_vacant','wc_occupied'}
    for p in sorted((PIPE/'work/buffers').glob('*.json')):
        row=json.loads(p.read_text())
        if not p.stem.startswith(('background_','dry_fallback','fg_','weather_','door_','wc_')):continue
        assert row['key']['scene']==sha(PIPE/'scene.blend') and row['sha256']==sha(p.with_suffix('.exr')),p
        key=row['key']
        assert key['size']==[3840,2160] and key['seed']==1701 and key['adaptive'] and key['threshold']==.01,p
        assert key['state']['pixel_filter_width']==2.5 and key['runtime']==sha(PIPE/'runtime.py'),p
        receipts.append({'tag':p.stem,'sha256':row['sha256'],'seconds':row['seconds'],'total':row['timing']['total']})
    videos={n:json.loads((PIPE/'work'/(n+'_video.json')).read_text()) for n in ['light_loop','light_loop_2x','rain_fg']}
    for n,v in videos.items():assert v['passed'] and v['frames']==144 and v['sha256']==sha(OUT/(n+'.webm'))
    endpoints={p.name:json.loads(p.read_text()) for p in (PIPE/'work').glob('*endpoint*.json')}
    assert len(endpoints)==3 and {r['tag'] for r in receipts}==expected
    report={'passed':True,'brief':56,'rendered_on':'cloud GPU','acceptance':'home decoded 144-frame and visual/page QA pending',
            'scene_sha256':sha(PIPE/'scene.blend'),'wet_loop_checks':loops,'render_receipts_verified_on_pod':receipts,
            'videos':videos,'endpoints':endpoints,'inherited_vehicle_umbrella_files':len(inherited),
            'same':[p for p in payload if payload[p]==baseline.get(p)],'changed':[p for p in payload if payload[p]!=baseline.get(p)]}
    atomic_json(W/'cloud57-audit.json',report);return report

def full():
    started=time.perf_counter();identity=initialize()
    preflight()
    for stage in STAGES:
        marker=W/('cloud57-'+stage+'.json')
        if marker.exists():
            done=json.loads(marker.read_text())
            if done['identity']==identity and all((OUT/p).is_file() and sha(OUT/p)==h for p,h in done['outputs'].items()):
                event('stage_reused',name=stage);continue
        before=inventory(OUT);t=time.perf_counter();event('stage_start',name=stage)
        with (W/('cloud57-'+stage+'.log')).open('a',encoding='utf-8') as log:
            proc=subprocess.run([bpy.app.binary_path,'-b','--factory-startup','--python-exit-code','1','--python',str(W/'production56.py'),'--',stage],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if proc.returncode:raise RuntimeError(f'Stage {stage} failed ({proc.returncode}); logs and buffers retained')
        after=inventory(OUT);outputs={p:h for p,h in after.items() if before.get(p)!=h}
        atomic_json(marker,{'identity':identity,'seconds':time.perf_counter()-t,'outputs':outputs})
        event('stage_done',name=stage,seconds=time.perf_counter()-t)
    report=audit()
    atomic_json(OUT/'validation.json',report)
    atomic_json(OUT/'.cloud-build.json',{'fingerprint':identity,'source':'Frozen Brief 56 rendered by Brief 57 cloud bundle','home_acceptance_pending':True})
    (OUT/'NOTES-PASS10.md').write_text('Brief 56 draft 23 production via Brief 57 cloud bundle. A12/B12; 24 wet phases; 48 background/rain phases. Eight companion mist maps at root. See _work/cloud57/cloud57-audit.json. Home decoded-video, visual and page QA remain pending. No live promotion.\n',encoding='utf-8')
    evidence={'preflight.json':ROOT/'preflight.json','brief57.json':ROOT/'brief57.json','baseline-sha256.json':ROOT/'baseline-sha256.json'}
    for p in W.glob('*.json'):evidence[p.name]=p
    for p in W.glob('cloud57-*.log'):evidence[p.name]=p
    for p in (W/'mist').glob('*.json'):evidence['mist/'+p.name]=p
    for p in (PIPE/'work').rglob('*.json'):evidence['pipeline/work/'+p.relative_to(PIPE/'work').as_posix()]=p
    for name in ['background_1','background_2','light_loop_1','light_loop_2','rain_fg_1']:
        for p in (PIPE/'work'/name).glob('*.png'):evidence['pipeline/work/'+name+'/'+p.name]=p
    seal_result(OUT,ROOT/'out10.tar.gz',evidence)
    event('production_pack_complete',seconds=time.perf_counter()-started)

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1]
    (W/'temp').mkdir(exist_ok=True)
    bpy.context.preferences.filepaths.temporary_directory=str(W/'temp')
    {'preflight':preflight,'smoke':smoke,'full':full,'validate-only':audit}[mode]()
