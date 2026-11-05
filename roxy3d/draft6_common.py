from pathlib import Path
from datetime import datetime
import json
ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa10'; WORK=QA/'draft6'; WORK.mkdir(exist_ok=True)
def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 6: '+s+'\n')
    print('DRAFT6_STAGE',s,flush=True)
def report(name,value):(WORK/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
