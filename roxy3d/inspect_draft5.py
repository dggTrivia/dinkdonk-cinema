import sys,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_pass10_draft as d
from draft5_common import *
backup=QA/'source_before_draft5.blend'
if not backup.exists():shutil.copy2(ROOT/'roxy_pass10_draft.blend',backup)
base=WORK/'protected_before.json'
if not base.exists():
    files=[p for folder in ROOT.glob('out*') if folder.is_dir() for p in folder.rglob('*') if p.is_file()]
    files.extend(ROOT/p for p in ['roxy_pass9.blend','roxy_pass10.blend'])
    report('protected_before.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene
rows=[]
for o in sc.objects:
    if o.type not in ['MESH','FONT','CURVE']:continue
    rows.append({'name':o.name,'type':o.type,'bounds':list(d.bounds(o)),'materials':[m.name for m in o.data.materials if m],'hidden':o.hide_render})
report('inventory.json',rows)
for r in rows:
    if any(s in r['name'].lower() for s in ['shelter','shop','awning','puddle','skylight','billboard','double programme','board heading','board listings','board foot']):print(json.dumps(r))
report('disk.json',dict(zip(['total','used','free'],shutil.disk_usage(ROOT))))
status('draft 4 source backed up; live packs fingerprinted; scene inventory and available disk recorded')
