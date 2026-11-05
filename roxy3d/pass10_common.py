from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa10';OUT=ROOT/'out10';LIVE=ROOT/'out9'
def status(s):
    QA.mkdir(exist_ok=True)
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: '+s+'\n')
    print('PASS10_STAGE',s,flush=True)
def baseline():
    import json,hashlib,shutil
    QA.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    target=QA/'live_before_final.json'
    if not target.exists():
        packs=['out','out2','out3','out4','out5','out6','out7','out8','out8b','out9']
        target.write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for n in packs for p in sorted((ROOT/n).rglob('*')) if p.is_file()],indent=2))
    # Never overwrite later production stages on resume.
    if not (QA/'baseline_final_complete.json').exists():
        for p in LIVE.rglob('*'):
            if p.is_file() and p.name!='manifest.json':
                q=OUT/p.relative_to(LIVE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        (QA/'baseline_final_complete.json').write_text(json.dumps({'source':'out9','files':len([p for p in OUT.rglob('*') if p.is_file()])}))
        status('Complete out9 baseline copied to out10; all ten live packs protected by SHA-256 inventory')
if __name__=='__main__':baseline()
