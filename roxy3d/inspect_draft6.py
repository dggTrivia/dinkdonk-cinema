import sys,shutil,hashlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft6_common import *
from build_pass10_draft import bounds
from common import xyz
src=ROOT/'roxy_pass10_draft.blend';backup=QA/'source_before_draft6.blend'
if not backup.exists():shutil.copy2(src,backup)
shutil.copy2(QA/'draft5/protected_before.json',WORK/'protected_before.json')
bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene
rows=[]
for o in sc.objects:
    if o.type not in ['MESH','CURVE','FONT','LIGHT']:continue
    keys=['shelter','bus route','bus stop','entrance_dinkdonk','rooftop_dinkdonk','entrance dd','noodle','take away','cabge','side route','destination','transit','number plate','future paste','art look','art conductor','art turf','right service alley']
    if any(k in o.name.lower() for k in keys) or (o.type=='FONT' and ('95' in o.data.body or 'NOODLES' in o.data.body)):
        rows.append({'name':o.name,'type':o.type,'bounds':bounds(o) if o.type!='LIGHT' else list(o.location),'body':o.data.body if o.type=='FONT' else '', 'materials':[m.name for m in o.data.materials] if hasattr(o.data,'materials') else [],'layer':o.get('layer'),'props':{k:str(o[k]) for k in o.keys() if k in ['bell_id','bell_id_disabled','draft5_bus']}})
report('source_inventory.json',rows)
report('source.json',{'draft5_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'backup':str(backup.relative_to(ROOT)),'objects':len(sc.objects),'camera_matrix':list(v for row in sc.camera.matrix_world for v in row),'camera_scale':sc.camera.data.ortho_scale})
status('Draft 5 source preserved; previous clip job is no longer running and its 25 completed frames are left as interrupted work; still-only Brief 17 begins')
