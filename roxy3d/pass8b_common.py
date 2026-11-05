from pathlib import Path
from datetime import datetime
from pass8_common import gpu
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa8b';OUT=ROOT/'out8b';LIVE=ROOT/'out8'
def status(stage):
    QA.mkdir(exist_ok=True)
    line=datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Pass 8b — '+stage
    with (ROOT/'qa8/STATUS.md').open('a',encoding='utf-8') as f:f.write(line+'\n')
    print('PASS8B_STAGE',stage,flush=True)

def baseline():
    import json,hashlib,shutil
    QA.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    target=QA/'live_before.json'
    if not target.exists():
        rows=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
              for folder in ['out','out2','out3','out4','out5','out6','out7','out8'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file()]
        target.write_text(json.dumps(rows,indent=2))
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            dest=OUT/p.relative_to(LIVE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    status('Brief/review read; protected eight live packs with SHA-256 inventory; copied complete out8 asset baseline')
if __name__=='__main__':baseline()
