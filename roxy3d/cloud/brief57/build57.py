"""Build/seal Brief 57 without touching the stopped production workspace."""
import ast, hashlib, json, shutil, sys, tarfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUNDLE = HERE / 'upload' / 'bundle'
LOCAL = ROOT / 'out10i/_work'
ARCHIVE = ROOT / 'cloud/roxy-cloud-bundle-56.tar.gz'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def protected():
    paths = [ROOT/'out10', ROOT/'out10mist', LOCAL, ROOT/'cloud/bundle']
    files = [p for folder in paths for p in folder.rglob('*') if p.is_file()]
    files += [ROOT.parent/'roxy.html', ROOT/'cloud/roxy-cloud-bundle.tar.gz']
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else '../roxy.html': sha(p) for p in sorted(files)}

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

def prepare():
    assert not BUNDLE.exists(), 'Use the existing build; do not reset verification or work buffers.'
    write(HERE/'protected-before.json', protected())
    BUNDLE.mkdir(parents=True)
    # Preserve the original relative layout so production56.py is byte-identical.
    for name in ['production56.py', 'scene-verification.json', 'scene-edits.json', 'source-visibility-verification.json']:
        copy(LOCAL/name, BUNDLE/'out10i/_work'/name)
    for p in sorted((LOCAL/'pipeline').iterdir()):
        if p.suffix in ('.py', '.json', '.blend') and p.is_file():
            copy(p, BUNDLE/'out10i/_work/pipeline'/p.name)
    shutil.copytree(LOCAL/'pipeline/assets', BUNDLE/'out10i/_work/pipeline/assets')
    shutil.copytree(ROOT/'out10', BUNDLE/'out10')
    for name in ['render_mist.py', 'scene-inventory.json']:
        copy(ROOT/'cache/brief50'/name, BUNDLE/'cache/brief50'/name)
    # The unchanged driver verifies this historical source before restoring visibility.
    copy(ROOT/'cloud/bundle/scene.blend', BUNDLE/'cloud/bundle/scene.blend')
    for name in ['run.sh', 'watchdog.sh', 'blender-5.2.3.sha256']:
        copy(ROOT/'cloud/bundle'/name, BUNDLE/name)
    # Only the old fixed bulb-count assertion changes in the copied preflight.
    path=BUNDLE/'out10i/_work/pipeline/validation.py'
    src=path.read_text(); assert src.count('assert len(r.chase)==74')==1
    path.write_text(src.replace('assert len(r.chase)==74', 'assert len(r.chase)==78'), encoding='utf-8', newline='\n')
    info=json.loads((ROOT/'cloud/bundle/bundle.json').read_text())
    info.update(scene_source='Frozen Brief 56 / approved draft 23', scene_sha256=sha(LOCAL/'pipeline/scene.blend'))
    write(BUNDLE/'out10i/_work/pipeline/bundle.json', info)
    live={p.relative_to(ROOT/'out10').as_posix():sha(p) for p in sorted((ROOT/'out10').rglob('*')) if p.is_file()}
    write(BUNDLE/'baseline-sha256.json', live)
    write(BUNDLE/'brief57.json', {
        'brief':57, 'production_brief':56, 'scene_sha256':sha(LOCAL/'pipeline/scene.blend'),
        'runtime_sha256':sha(LOCAL/'pipeline/runtime.py'), 'driver_sha256':sha(LOCAL/'production56.py'),
        'wet_phases':24, 'background_phases':48, 'rain_phases':48, 'bell':'A12/B12',
        'sampling':{'size':[3840,2160], 'max':256,'min':64,'threshold':0.01,'seed':1701,'denoiser':'OPTIX','filter_width':2.5},
        'mist':{'maps':['catch','height','rim','light'],'scales':[1,2],'catch_samples':16,'light_samples':32},
        'local_fallback_included':False, 'baseline_files':len(live)})
    sync_code()
    print('PREPARED', BUNDLE)

def sync_code():
    for src,dst in [('pipeline57.py','pipeline.py'),('README-BUNDLE.md','README.md')]:
        copy(HERE/src, BUNDLE/dst)
    # The frozen copy retains Blender's rebased relative packed-asset paths.
    # Keep both the original fallback directory and the native pipeline assets.
    shutil.copytree(LOCAL/'pipeline/assets', BUNDLE/'cloud/bundle/assets', dirs_exist_ok=True)
    source=(LOCAL/'pipeline/validation.py').read_text()
    assert source.count('assert len(r.chase)==74')==1
    source=source.replace('assert len(r.chase)==74','assert len(r.chase)==78')
    for kind in ['im','font']:
        needle=kind+".filepath.startswith('//assets/')"
        assert source.count(needle)==1
        source=source.replace(needle, kind+".filepath.startswith(('//assets/', '//../../../cloud/bundle/assets/'))")
    (BUNDLE/'out10i/_work/pipeline/validation.py').write_text(source,encoding='utf-8',newline='\n')

def seal():
    sync_code()
    files=[p for p in sorted(BUNDLE.rglob('*')) if p.is_file() and p.name!='BUNDLE-SHA256SUMS']
    assert not any(p.suffix in ('.exr','.pyc') for p in files)
    assert not (BUNDLE/'out10i/_work/pipeline/work').exists(), 'Never ship smoke/render caches'
    for p in files:
        if p.suffix=='.py': ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    sums=''.join(sha(p)+'  '+p.relative_to(BUNDLE).as_posix()+'\n' for p in files)
    (BUNDLE/'BUNDLE-SHA256SUMS').write_text(sums, encoding='utf-8', newline='\n')
    temp=ARCHIVE.with_suffix('.tar.gz.partial')
    with tarfile.open(temp,'w:gz',compresslevel=6) as tar:
        for p in files+[BUNDLE/'BUNDLE-SHA256SUMS']:
            info=tar.gettarinfo(str(p),arcname='bundle/'+p.relative_to(BUNDLE).as_posix())
            info.mode=0o755 if p.suffix=='.sh' else 0o644
            info.uid=info.gid=0;info.uname=info.gname=''
            with p.open('rb') as f:tar.addfile(info,f)
    temp.replace(ARCHIVE)
    with tarfile.open(ARCHIVE) as tar:
        members=tar.getmembers();assert all(m.isfile() and not m.issym() for m in members)
        for m in members:
            assert m.name.startswith('bundle/') and '..' not in Path(m.name).parts
            assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==sha(BUNDLE/Path(m.name).relative_to('bundle'))
    report={'archive':str(ARCHIVE.relative_to(ROOT)),'bytes':ARCHIVE.stat().st_size,'sha256':sha(ARCHIVE),'files':len(files)+1,'all_member_hashes_verified':True}
    write(HERE/'bundle-delivery.json',report);print(json.dumps(report))

def extract():
    target=HERE/'verify'
    assert target.resolve().is_relative_to(HERE.resolve())
    with tarfile.open(ARCHIVE) as tar:tar.extractall(target,filter='data')
    print('EXTRACTED',target)

def preservation():
    old=json.loads((HERE/'protected-before.json').read_text());new=protected()
    changed=[p for p in old if new.get(p)!=old[p]];added=sorted(set(new)-set(old))
    report={'passed':not changed and not added,'files':len(old),'changed':changed,'added':added}
    write(HERE/'preservation.json',report);assert report['passed'],report;print(json.dumps(report))

if __name__=='__main__':
    {'prepare':prepare,'seal':seal,'extract':extract,'preservation':preservation}[sys.argv[1]]()
