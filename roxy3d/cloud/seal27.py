"""Seal Brief 27 only after bounded rendering and the complete packaging tail pass."""
import ast,json,hashlib,shutil,tarfile,subprocess
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE/'bundle';SRC=HERE.parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def seal():
    info=read(ROOT/'bundle.json');report=read(ROOT/'smoke/validation.json');fast=read(ROOT/'smoke/fast-validation.json')
    assert info['scene_source']=='approved Draft 13'
    assert sha(SRC/'roxy_pass10_draft.blend')==info['source_sha256']
    assert sha(ROOT/'scene.blend')==info['scene_sha256']==report['scene_sha256']==fast['scene_sha256']
    assert not (ROOT/'out10').exists(),'Local production render is forbidden'
    assert sha(SRC.parent/'roxy.html')=='da58b5efef3729ffe4e14966de0d904d7f672d01df5129dee3b1d75e3cbe7179','The consumer page changed'
    assert report['selected']=={'adaptive':True,'threshold':.01,'split':False,'persistent':True}
    assert report['quality']['persistent']['passed'] and report['quality']['adaptive_001']['passed']
    assert report['video_smoke']['passed'] # The codec's per-frame allowance is authoritative.
    assert fast['passed'] and fast['downscale']['passed'] and fast['wet_frames']['cadence_checks_passed']
    assert fast['wet_frames']['default']==24 and fast['wet_frames']['optional']==48
    cadence=read(ROOT/'fast_contracts.json')
    assert cadence['passed'] and cadence['default']==24 and cadence['override']==48
    assert any(c['environment'] is None and c['unique_frames']==24 for c in cadence['cases'])
    assert any(c['environment']==48 and c['unique_frames']==48 for c in cadence['cases'])
    assert fast['runtime_sha256']==sha(ROOT/'runtime.py') and fast['fast_pipeline_sha256']==sha(ROOT/'fast_pipeline.py')
    groups=read(ROOT/'smoke/group-comparison.json');assert groups['complete'] and len(groups['groups'])==39
    assert groups['runtime_sha256']==sha(ROOT/'runtime.py')
    for g in groups['groups']:
        expected=all(g['difference'][k]<=g['noise'][k]+1e-7 for k in ['mean','p99','alpha_mean','alpha_p99'])
        assert g['accepted']==expected
        assert (g['name'] in fast['fallback_groups'])== (not expected)
    pack=read(ROOT/'smoke/packaging27.json');assert pack['passed'] and pack['validation']['passed'] and pack['cleanup_proved'] and pack['archive']['member_hashes_verified']
    assert sha(ROOT/'work/smoke_tail/out10.tar.gz')==pack['archive']['sha256']
    draft=read(ROOT/'smoke/draft27.json');assert sha(SRC/draft['file'])==draft['sha256'] and draft['size']==[1280,720]
    assert read(ROOT/'smoke/visual27.json')['passed']
    for name in ['preflight.json','contract_checks.json','watchdog_checks.json','fast_contracts.json']:assert read(ROOT/name)['passed']
    for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
    tags=['baseline_seed_a','baseline_seed_b','persistent_seed_a','adaptive_threshold_001','fast27_combined_720','fast27_native1080_a','fast27_native1080_b','fast27_native4k','fast27_filter_3_0','fast27_filter_2_5','fast27_draft_background','fast27_draft_wc','smoke_weather']
    tags += ['fast27_'+kind+'_'+g['name'] for g in groups['groups'] for kind in ['ref','noise']]
    tags += [f'fast27_{kind}_timing_{f}' for kind in ['old','new'] for f in [0,2]]
    tags += [f'bus_{direction}{opened}_2x' for direction in ['plus','minus'] for opened in ['','_open']]
    receipts={}
    for tag in tags:
        receipt=read(ROOT/'work/buffers'/(tag+'.json'));key=receipt['key']
        assert key['scene'].startswith(info['scene_sha256'])
        assert key['runtime']==sha(ROOT/('runtime_reference.py' if '_old_timing_' in tag else 'runtime.py')),(tag,'runtime')
        assert receipt['sha256']==sha(ROOT/'work/buffers'/(tag+'.exr'))
        if key.get('position_aov'):assert receipt['uv_sha256']==sha(ROOT/'work/positions'/(tag+'.npz'))
        if key.get('cryptomatte_groups'):assert receipt['masks_sha256']==sha(ROOT/'work/positions'/(tag+'_masks.npz'))
        receipts[tag]=receipt
    reused=0
    for p in (ROOT/'reuse').rglob('*'):
        if p.is_file():assert sha(p)==sha(SRC/'out9'/p.relative_to(ROOT/'reuse'));reused+=1
    proof=ROOT/'proof/fast27';proof.mkdir(parents=True,exist_ok=True)
    smoke_files=['validation.json','fast-validation.json','group-comparison.json','downscale-comparison.json','quality27.json','timing27.json','draft27.json','packaging27.json','projection27.json','filter27.json','visual27.json']
    for name in smoke_files:shutil.copyfile(ROOT/'smoke'/name,proof/name)
    checks=['preflight.json','contract_checks.json','watchdog_checks.json','fast_contracts.json','speed_plan.json']
    for name in checks:shutil.copyfile(ROOT/name,proof/name)
    (proof/'render_receipts.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    shutil.copyfile(SRC/'NOTES-FAST-PIPELINE.md',ROOT/'NOTES-FAST-PIPELINE.md')
    shutil.copyfile(HERE/'README-CLOUD.md',ROOT/'README.md')
    allowed_proof=set(smoke_files+checks+['render_receipts.json'])
    portable=[];immutable=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT);s=rel.as_posix()
        if any(part in ['work','__pycache__','.runtime','out10'] for part in rel.parts):continue
        if rel.name in ['progress.log','BUNDLE-SHA256SUMS','DONE','FAILED','probe27.py','reduction27.py','inspect_depth27.py','cap27.py','finish27.py'] or rel.suffix=='.blend1' or '.orig-' in rel.name:continue
        if rel.parts[0]=='smoke' and (len(rel.parts)!=2 or rel.name not in smoke_files):continue
        if rel.parts[0]=='proof' and (len(rel.parts)!=3 or rel.parts[1]!='fast27' or rel.name not in allowed_proof):continue
        portable.append(p)
        if rel.parts[0]=='smoke' or s in checks:continue
        immutable.append(p)
    (ROOT/'BUNDLE-SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in immutable),encoding='utf-8',newline='\n')
    portable.append(ROOT/'BUNDLE-SHA256SUMS')
    gitbin=Path('C:/Program Files/Git/usr/bin')
    for script in ['run.sh','watchdog.sh']:subprocess.run([str(gitbin/'bash.exe'),'-n',str(ROOT/script)],check=True)
    subprocess.run([str(gitbin/'bash.exe'),'-n',str(HERE/'cloud-render.sh')],check=True)
    subprocess.run([str(gitbin/'sha256sum.exe'),'--check','--quiet','BUNDLE-SHA256SUMS'],cwd=ROOT,check=True)
    archive=HERE/'roxy-cloud-bundle.tar.gz';pending=archive.with_suffix('.gz.partial')
    def modes(member):member.mode=0o755 if member.name.endswith('.sh') else 0o644;return member
    with tarfile.open(pending,'w:gz',compresslevel=4) as tar:
        for p in portable:tar.add(p,arcname='bundle/'+p.relative_to(ROOT).as_posix(),recursive=False,filter=modes)
    expected={'bundle/'+p.relative_to(ROOT).as_posix():sha(p) for p in portable}
    with tarfile.open(pending,'r:gz') as tar:
        members=tar.getmembers();assert len(members)==len(expected)
        for member in members:
            assert member.isfile() and '..' not in Path(member.name).parts
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==expected[member.name]
    pending.replace(archive)
    inventory=dict(archive=archive.name,created_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),bytes=archive.stat().st_size,sha256=sha(archive),portable_files=len(portable),immutable_checksums=len(immutable),render_receipts_verified=len(receipts),reuse_sources_byte_identical=reused,source_blend_unchanged=True,archive_contents_verified=True,all_bundle_checksums_passed=True,local_smoke_only=True,full_render_run=False,cloud_pods_started=False,combined_groups=fast['combined_groups'],fallback_groups=fast['fallback_groups'],draft=draft['file'],smoke_pack_tail_passed=True,wet_frames_default=24,wet_frames_override=48,light_unique_frames=48,rain_unique_frames=48)
    (HERE/'bundle-delivery.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    with (SRC/'qa10/STATUS.md').open('a',encoding='utf-8') as f:f.write(f"\n{inventory['created_utc']} | STATUS: Brief 27 owner decision applied; wet/foreground DEFAULT 24 unique frames (ROXY_WET_FRAMES unset), 48 override retained; light/rain 48 unique and 2s/6s timing unchanged; affected no-render scheduling/cadence checks passed; bundle resealed SHA256 {inventory['sha256']}; existing draft unchanged, no new render or cloud pod, roxy.html unchanged. See NOTES-FAST-PIPELINE.md.\n")
    print(json.dumps(inventory,indent=2),flush=True)

if __name__=='__main__':seal()
