"""Create Brief 53 staging without modifying any existing source or pack."""
import sys,json,hashlib,shutil,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out10g';WORK=OUT/'_work'
assert not OUT.exists(), 'Refuse to overwrite an existing staging pack'
started=time.time()
protected=[]
for pack in ['out10','out10e','out10f']:
    protected.extend(p for p in (ROOT/pack).rglob('*') if p.is_file())
protected += [ROOT/'NOTES-51.md',ROOT/'NOTES-52.md',ROOT/'BRIEF-53-production-rain-umb-veh-tyre.md',ROOT.parent/'roxy.html']
receipt=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in protected]
shutil.copytree(ROOT/'out10',OUT)
WORK.mkdir()
(WORK/'protected-before.json').write_text(json.dumps(receipt,indent=2)+'\n')
(WORK/'prior-validation.json').write_bytes((ROOT/'out10/validation.json').read_bytes())
for p in (ROOT/'out10f/_work/studio').glob('*'):
    if p.is_file():
        (WORK/'studio').mkdir(exist_ok=True);shutil.copy2(p,WORK/'studio'/p.name)
for source,dest in [('reference_renderer.py','reference_renderer.py'),('render.py','draft21.py'),('grade.json','draft21-grade.json'),('street-lights.json','street-lights.json')]:
    shutil.copy2(ROOT/'out10f/_work'/source,WORK/dest)
(WORK/'temp').mkdir();(WORK/'config').mkdir()
(WORK/'studio/cache/temp').mkdir(parents=True,exist_ok=True)
(WORK/'setup.json').write_text(json.dumps(dict(started_epoch=started,protected=len(receipt),free_disk_bytes=shutil.disk_usage(ROOT).free,source='out10',reference='out10f'),indent=2))
print('STAGING_CREATED',len(receipt),'protected files; free bytes',shutil.disk_usage(ROOT).free)
