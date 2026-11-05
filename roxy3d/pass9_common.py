from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa9';OUT=ROOT/'out9';LIVE=ROOT/'out8b'
PACKS=['out','out2','out3','out4','out5','out6','out7','out8','out8b']
def status(s):
    QA.mkdir(exist_ok=True)
    line=datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: '+s
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(line+'\n')
    print('PASS9_STAGE',s,flush=True)
def baseline():
    import hashlib,json,shutil
    QA.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    p=QA/'live_before.json'
    if not p.exists():p.write_text(json.dumps([{'path':f.relative_to(ROOT).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for d in PACKS for f in sorted((ROOT/d).rglob('*')) if f.is_file()],indent=2))
    for f in LIVE.rglob('*'):
        if f.is_file() and f.name!='manifest.json':
            dest=OUT/f.relative_to(LIVE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
    status('Brief 11 read; nine live packs protected by SHA-256 inventory; complete out8b baseline copied into out9')
if __name__=='__main__':baseline()
