import sys,json,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from draft5_common import *
from pngio import read,write,predecode

def main():
    raw=[WORK/'sparkle_frames'/('f%03d.png'%i) for i in range(N)];decoded=[WORK/'decoded'/('f%03d.png'%i) for i in range(N)]
    predecode(raw+decoded+[WORK/'sparkle_endpoint.png',WORK/'sparkle_off.png',QA/'draft_5.png',QA/'draft_5_clean.png'])
    a=np.stack([read(p)[:,:,:3] for p in raw]);v=np.stack([read(p)[:,:,:3] for p in decoded]);endpoint=read(WORK/'sparkle_endpoint.png')[:,:,:3];off=read(WORK/'sparkle_off.png')[:,:,:3]
    def delta(x,y):
        d=np.abs(x.astype(np.float32)-y.astype(np.float32));return {'mean_0_255':float(d.mean()),'p99_0_255':float(np.quantile(d,.99)),'max_0_255':float(d.max())}
    steps=[delta(v[i],v[i-1])['mean_0_255'] for i in range(1,N)];wrap=delta(v[-1],v[0]);canonical=delta(a[0],endpoint)
    # Dry cinema interior lies inside the matched native crop, above the arcade.
    dry=v[:,30:120,760:970].astype(np.float32);wet=v[:,145:300,165:435].astype(np.float32)
    metrics={'frames':N,'fps':FPS,'size':[1280,360],'canonical_endpoint':canonical,'decoded_wrap':wrap,'ordinary_step_mean':float(np.mean(steps)),'ordinary_step_max':float(max(steps)),'decoded_wrap_to_max_step':wrap['mean_0_255']/max(steps),'compression':delta(a,v),'dry_interior_temporal_std':float(dry.std(axis=0).mean()),'wet_street_temporal_std':float(wet.std(axis=0).mean()),'sparkle_on_off':delta(a[0],off),'decoded_min_channel':int(v.min()),'decoded_max_channel':int(v.max()),'native_720p_stills':list(read(QA/'draft_5.png').shape[:2])==[720,1280]}
    report('metrics.json',metrics)
    assert canonical['mean_0_255']<.5,canonical
    assert metrics['native_720p_stills']
    # Matched magnifications from the delivered, decoded video (nearest neighbour
    # is deliberate, to expose individual pinpricks instead of smoothing them).
    panels=[]
    for f in [0,7,15,23,31,47]:
        tile=v[f,120:300,140:460];tile=np.repeat(np.repeat(tile,2,axis=0),2,axis=1);panels.append(tile)
    sheet=np.concatenate([np.concatenate(panels[:3],axis=1),np.concatenate(panels[3:],axis=1)],axis=0);rgba=np.dstack([sheet,np.full(sheet.shape[:2],255,np.uint8)]);write(WORK/'sparkle_decoded_contact.png',rgba)
    status('all 48 decoded sparkle frames checked: endpoint, frame-to-frame changes, compression and wet/dry variation measured; decoded street detail contact sheet saved')
    before=json.loads((WORK/'protected_before.json').read_text());changed=[]
    for path,sha in before.items():
        p=ROOT/path
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:changed.append(path)
    now={str(p.relative_to(ROOT)) for folder in ROOT.glob('out*') if folder.is_dir() for p in folder.rglob('*') if p.is_file()};added=sorted(now-set(before));assert not changed and not added,(changed,added)
    report('preservation.json',{'passed':True,'protected_files':len(before),'changed':changed,'added_pack_files':added,'out10':'parked and untouched'})
    status('preservation check passed: %d protected files unchanged, no files added to any output pack; out10 untouched'%len(before))
    html='''<!doctype html><html><head><meta charset="utf-8"><title>Draft 5 review</title><style>body{margin:24px;background:#142029;color:#e9e3d1;font:16px system-ui}h1{font-size:26px}h2{font-size:18px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}video,img{width:100%;background:#080f16}a{color:#b9ddc6}button,input{margin:12px 12px 12px 0}small{color:#b6c8c9}details{margin:20px 0}pre{white-space:pre-wrap}</style></head><body><h1>Draft 5 / wet materials, physical sparkle, the approved twelve</h1><p>Draft only. Native 720p / Cycles 256 samples / fixed seed / per-frame OptiX. The videos share the same 1280 × 360 street crop and 48 frames at 24 fps.</p><div class="pair"><section><h2>Draft 4 — per-frame denoised baseline</h2><video id="old" src="test_ripples_clip_noTD.webm" controls muted loop playsinline preload="auto"></video></section><section><h2>Draft 5 — wet-only physical micro-impacts</h2><video id="fresh" src="test_sparkle_clip.webm" controls muted loop playsinline preload="auto"></video></section></div><button id="play">Play both</button><button id="pause">Pause both</button><label>Frame <input id="seek" type="range" min="0" max="47" value="0"><span id="f">0</span></label><p><small>This is the requested previous-draft comparison, not an isolated denoiser experiment: road materials, rain details, art and the parked bus also changed. The controlled current-scene sparkle-off still below uses the same seed and materials.</small></p><div class="pair"><section><h2>Current frame 0 — sparkle on</h2><img src="draft5/sparkle_frames/f000.png"></section><section><h2>Current frame 0 — sparkle off control</h2><img src="draft5/sparkle_off.png"></section></div><h2>Weather still</h2><a href="draft_5.png"><img src="draft_5.png"></a><p><a href="draft_5_clean.png">Clean still</a> · <a href="DRAFT-5.md">Report</a> · <a href="water_coverage.png">Water coverage</a> · <a href="draft5_approved_art.png">Twelve artwork sources</a></p><h2>Surface response map</h2><a href="water_coverage.png"><img src="water_coverage.png"></a><h2>In-world details</h2><div class="pair">DETAILS</div><details><summary>Numerical checks</summary><pre>METRICS</pre></details><script>const a=document.getElementById('old'),b=document.getElementById('fresh'),s=document.getElementById('seek');document.getElementById('play').onclick=()=>{a.currentTime=b.currentTime=s.value/24;a.play();b.play()};document.getElementById('pause').onclick=()=>{a.pause();b.pause()};s.oninput=()=>{a.pause();b.pause();a.currentTime=b.currentTime=s.value/24;document.getElementById('f').textContent=s.value};setInterval(()=>{if(!b.paused&&Math.abs(a.currentTime-b.currentTime)>.07)a.currentTime=b.currentTime},250)</script></body></html>'''
    detail=''.join('<section><h2>'+name.replace('_',' ').title()+'</h2><a href="draft5/'+name+'.png"><img src="draft5/'+name+'.png"></a></section>' for name in ['shelter_bus','alley','service_art','service_art_front','rooftop_ac','inside','billboard','cabge'])
    (QA/'draft5_comparison.html').write_text(html.replace('DETAILS',detail).replace('METRICS',json.dumps(metrics,indent=2)),encoding='utf-8')
    status('local comparison viewer complete: synchronized draft 4 / draft 5 clips, frame seek, current sparkle on/off, coverage map and in-world detail renders')
if __name__=='__main__':main()
