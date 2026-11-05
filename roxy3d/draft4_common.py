from pathlib import Path
from datetime import datetime
import json,struct
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa10';WORK=QA/'draft4';WORK.mkdir(exist_ok=True)
W,H,N,FPS=1280,720,48,24
def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 4: '+s+'\n')
    print('DRAFT4_STAGE',s,flush=True)
def report(name,value):(WORK/name).write_text(json.dumps(value,indent=2))
def exr_header(path):
    data=Path(path).read_bytes();pos=8;attrs={};parts=[]
    def string():
        nonlocal pos
        end=data.index(b'\0',pos);s=data[pos:end].decode('utf-8');pos=end+1;return s
    multipart=bool(struct.unpack_from('<I',data,4)[0]&0x1000)
    while True:
        attrs={}
        while data[pos]:
            key=string();kind=string();size=struct.unpack_from('<I',data,pos)[0];pos+=4;v=data[pos:pos+size];pos+=size
            if kind=='chlist':
                names=[];i=0
                while i<len(v) and v[i]:
                    e=v.index(b'\0',i);names.append(v[i:e].decode());i=e+1+16
                attrs[key]=names
            elif kind=='box2i':attrs[key]=list(struct.unpack('<4i',v))
            elif kind=='string':attrs[key]=v.decode('utf-8','replace')
        pos+=1;parts.append(attrs)
        if not multipart or not data[pos]:break
    return {'multipart':multipart,'parts':parts,'channels':[c for part in parts for c in part.get('channels',[])]}
