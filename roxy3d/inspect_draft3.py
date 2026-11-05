import sys,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT
from build_pass10_draft import bounds,status
QA=ROOT/'qa10'
protected={}
for folder in ROOT.glob('out*'):
    if folder.is_dir():
        for p in folder.rglob('*'):
            if p.is_file():protected[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['roxy_pass9.blend','roxy_pass10.blend']:
    p=ROOT/n;protected[n]=hashlib.sha256(p.read_bytes()).hexdigest()
(QA/'draft3_protected_before.json').write_text(json.dumps(protected,indent=2))
backup=QA/'source_before_draft3.blend'
if not backup.exists():shutil.copy2(ROOT/'roxy_pass10_draft.blend',backup)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
bpy.context.view_layer.update()
rows=[]
for o in bpy.context.scene.objects:
    rows.append(dict(name=o.name,type=o.type,layer=o.get('layer'),bounds=[round(v,4) for v in bounds(o)],materials=[m.name for m in getattr(o.data,'materials',[]) if m],text=o.data.body if o.type=='FONT' else None))
(QA/'inventory_before_draft3.json').write_text(json.dumps(rows,indent=2))
status('Brief 14 draft-only boundary recorded; prior out10 attempt parked, no production process active; live packs and partial out10 checksummed before draft 3')
print('DRAFT3_BASELINE',len(protected),'OBJECTS',len(rows))
