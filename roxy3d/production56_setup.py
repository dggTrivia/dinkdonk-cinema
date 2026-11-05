"""Isolate Brief 56 production, preserving the current live payload and references."""
import hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out10i'
WORK=OUT/'_work'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def main():
    assert not OUT.exists(), 'Existing staging must be resumed, never overwritten.'
    paths=[]
    for folder in ['out10','out10mist','out10h']:
        paths += [p for p in (ROOT/folder).rglob('*') if p.is_file()]
    paths += [ROOT.parent/'roxy.html',ROOT/'cloud/bundle/scene.blend']
    paths += list((ROOT/'cloud/bundle').glob('*.py'))
    before={p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else '../'+p.name:sha(p) for p in paths}
    shutil.copytree(ROOT/'out10',OUT)
    WORK.mkdir(exist_ok=True)
    (WORK/'protected-before.json').write_text(json.dumps(before,indent=2))
    pipe=WORK/'pipeline';pipe.mkdir()
    for p in (ROOT/'cloud/bundle').glob('*.py'):shutil.copy2(p,pipe/p.name)
    for name in ['production.json','manifest.template.json','speed_plan.json']:shutil.copy2(ROOT/'cloud/bundle'/name,pipe/name)
    shutil.copytree(ROOT/'cloud/bundle/assets',pipe/'assets')
    shutil.copytree(ROOT/'cloud/bundle/smoke',pipe/'smoke',ignore=shutil.ignore_patterns('*.exr','*.png','*.webm','*.blend','*.tar.gz'))
    src=(pipe/'runtime.py').read_text();assert "(frame%48)//6%2" in src
    src=src.replace('(frame%48)//6%2','(frame%48)//12%2').replace('CLOUD_PROGRESS ','LOCAL56_PROGRESS ')
    (pipe/'runtime.py').write_text(src)
    inventory={p.relative_to(ROOT/'out10').as_posix():sha(p) for p in (ROOT/'out10').rglob('*') if p.is_file()}
    (WORK/'live-before.json').write_text(json.dumps(inventory,indent=2))
    print(json.dumps({'copied_live_files':len(inventory),'protected_files':len(before),'pipeline':str(pipe)}))
if __name__=='__main__':main()
