import sys,json,hashlib,struct,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft6_common import *
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
baseline=json.loads((WORK/'protected_before.json').read_text(encoding='utf-8'));bad=[];missing=[]
for key,value in baseline.items():
    p=ROOT/key
    if not p.exists():missing.append(key)
    elif sha(p)!=value:bad.append(key)
packdirs=sorted({Path(k).parts[0] for k in baseline if Path(k).parts[0].startswith('out')})
added=[str(p.relative_to(ROOT)) for folder in packdirs for p in (ROOT/folder).rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in baseline]
result={'protected_files':len(baseline),'modified':bad,'missing':missing,'added_pack_files':added,'packs':packdirs}
report('preservation.json',result);assert not bad and not missing and not added,result
status('preservation hashes passed for %d protected files; no changed, missing or added pack files'%len(baseline))
if '--preserve-only' in sys.argv:sys.exit(0)
source=sha(ROOT/'roxy_pass10_draft.blend');renders=json.loads((WORK/'renders.json').read_text(encoding='utf-8'));audit=json.loads((WORK/'source_audit.json').read_text(encoding='utf-8'));scene=json.loads((WORK/'scene.json').read_text(encoding='utf-8'))
expected=['preview','restroom','restroom_mirror','alley','alley_ground','bus_stop','roof_A','roof_B','eatfresh','frontage','greengrocer','entrance_script']
images=[]
for key in expected:
    r=renders[key];assert r['source_sha256']==source,(key,'stale source');assert r['samples']==256
    p=QA/r['file'];buf=p.read_bytes();assert buf[:8]==b'\x89PNG\r\n\x1a\n';size=list(struct.unpack_from('>II',buf,16));assert size==r['size'];images.append({'file':r['file'],'size':size,'sha256':sha(p)})
final=QA/'draft_6.png';size=list(struct.unpack_from('>II',final.read_bytes(),16));assert size==[1280,720];images.append({'file':final.name,'size':size,'sha256':sha(final)})
assert source==audit['source_sha256']==scene['source_sha256']
weather=json.loads((WORK/'weather.json').read_text(encoding='utf-8'));assert source==weather['source_sha256']
assert not scene['checks']['boarding_path_solid_hits'];assert audit['unmounted_count']==0
assert renders['roof_A']['camera_matrix']==renders['roof_B']['camera_matrix']
started=(WORK/'source.json').stat().st_mtime
videos=[str(p.relative_to(ROOT)) for p in QA.rglob('*') if p.is_file() and p.suffix.lower() in ['.webm','.mp4','.mkv','.mov','.avi'] and p.stat().st_mtime>started]
assert not videos,videos
data={'source_sha256':source,'images':images,'same_source_all_stills':True,'main_camera_unchanged':scene['checks']['main_camera_unchanged'],'matched_neon_cameras':True,'boarding_path_solid_hits':0,'unmounted_art_count':0,'clips_generated_this_draft':len(videos),'new_video_files':videos,'out10_build_invoked':False,'protected':result,'quality':{'samples':256,'native_draft':[1280,720],'native_closeups':[1280,960],'ray_traced_reflections':True,'retained_periodic_ripple_group':True,'hdr_glare':True,'denoiser':'OptiX per frame'}}
report('validation.json',data);status('delivery validation passed: all stills match the saved Draft 6 source and final quality; both neon views use the same camera; no clips or pack build')
