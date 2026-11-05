from pathlib import Path
from datetime import datetime
import json
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa10'; WORK=QA/'draft5'; WORK.mkdir(exist_ok=True)
N=48;FPS=24;W=1280;H=720
def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 5: '+s+'\n')
    print('DRAFT5_STAGE',s,flush=True)
def report(name,value):(WORK/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
