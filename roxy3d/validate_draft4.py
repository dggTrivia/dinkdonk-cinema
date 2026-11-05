"""Measure the delivered comparison, create contact sheets and a local viewer."""
import sys,json,hashlib,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from pngio import predecode,read,write
from draft4_common import ROOT,QA,WORK,N,FPS,status,report

ROIS={'dry_interior_control':[590,165,80,25],
      'blade_reflection':[175,105,70,115],
      'wet_sidewalk':[470,190,100,55],
      'street_reflections':[80,100,390,160]}

def label_sheet(base,target,labels):
    spec={'input':str(base),'output':str(target),'items':[{'type':'text','x':x,'y':y,'size':22,'text':s,'color':'#e5f3ff','width':1} for x,y,s in labels]}
    job=WORK/(target.stem+'_labels.json');job.write_text(json.dumps(spec))
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass10_draft.ps1'),'-Spec',str(job)],check=True)

def comparison_glare():
    paths=[QA/'test_glare_before.png',QA/'test_glare_after.png'];predecode(paths);a,b=[read(p) for p in paths]
    full=np.concatenate([a,b],axis=1);canvas=np.full((770,2560,4),[12,19,29,255],np.uint8);canvas[50:]=full
    base=WORK/'glare_full_unlabelled.png';write(base,canvas)
    label_sheet(base,QA/'test_glare_comparison.png',[(20,14,'BEFORE: current 2D halo'),(1300,14,'AFTER: HDR optical glare')])
    # Pixel-doubled QA close-ups are explicitly labelled; delivery stills are native 720p.
    rows=[]
    for x,y,w,h in [(760,25,350,210),(150,230,120,155)]:
        pair=np.concatenate([a[y:y+h,x:x+w],b[y:y+h,x:x+w]],axis=1)
        pair=np.repeat(np.repeat(pair,2,axis=0),2,axis=1)
        row=np.full((pair.shape[0]+44,1400,4),[12,19,29,255],np.uint8);row[44:,:pair.shape[1]]=pair;rows.append(row)
    base=WORK/'glare_details_unlabelled.png';write(base,np.concatenate(rows,axis=0))
    label_sheet(base,QA/'test_glare_details.png',[(10,10,'Roof sign, 2x pixels: BEFORE (left) / AFTER (right)'),(10,474,'Blade sign, 2x pixels: BEFORE (left) / AFTER (right)')])
    status('test B full-frame and labelled 2x detail comparisons assembled from the same current HDR frame')

def sequence_metrics(folder):
    files=[folder/('f%03d.png'%f) for f in range(N)];predecode(files)
    roi_values={k:[] for k in ROIS};full=[]
    for p in files:
        a=read(p);assert a.shape==(360,1280,4)
        lum=np.einsum('ijk,k->ij',a[:,:,:3].astype(np.float32),np.array([.2126,.7152,.0722],np.float32))
        full.append(lum)
        for k,(x,y,w,h) in ROIS.items():roi_values[k].append(lum[y:y+h,x:x+w])
    result={}
    for k,seq in {'full_crop':full,**roi_values}.items():
        arr=np.stack(seq);delta=np.abs(np.roll(arr,-1,axis=0)-arr).mean(axis=(1,2));std=arr.std(axis=0)
        result[k]={'temporal_std_mean':float(std.mean()),'temporal_std_p90':float(np.percentile(std,90)),
                   'adjacent_mean_abs_luma':float(delta[:-1].mean()),'cyclic_mean_abs_luma':float(delta.mean()),
                   'second_difference_mean_abs_luma':float(np.abs(np.roll(arr,-1,axis=0)-2*arr+np.roll(arr,1,axis=0)).mean()),
                   'seam_last_to_first_mean_abs_luma':float(delta[-1]),'seam_ratio_to_adjacent_mean':float(delta[-1]/max(delta[:-1].mean(),1e-9)),
                   'max_internal_adjacent_mean_abs_luma':float(delta[:-1].max()),'adjacent_values_with_wrap':delta.tolist()}
    return result

def validation():
    results={'metric_units':'luma values on 0..255 display-referred sRGB scale; same mask/frames for both versions',
             'roi_coordinates_native_video_xywh':ROIS,
             'interpretation':'Dry interior variation is a flicker proxy, not ground-truth error. Wet ROI metrics include intentional moving reflections and rain ripples. Fixed sampling seed holds much noise stationary, so low temporal variation alone does not prove image accuracy or detail retention.',
             'sequences':{}}
    for kind in ['noTD','TD']:
        source=sequence_metrics(WORK/('ripples_'+kind));decoded=sequence_metrics(WORK/('decoded_'+kind))
        errors=[];max_errors=[]
        for f in range(N):
            a=read(WORK/('ripples_'+kind)/('f%03d.png'%f));b=read(WORK/('decoded_'+kind)/('f%03d.png'%f));err=np.abs(a[:,:,:3].astype(np.int16)-b[:,:,:3].astype(np.int16));errors.append(float(err.mean()));max_errors.append(int(err.max()))
        results['sequences'][kind]={'source_png':source,'decoded_webm':decoded,'decoded_vs_source_rgb_mae':float(np.mean(errors)),'decoded_vs_source_rgb_max':max(max_errors)}
    rows=[]
    for f in [0,12,24,36]:
        pieces=[]
        for kind in ['noTD','TD']:
            a=read(WORK/('decoded_'+kind)/('f%03d.png'%f));pieces.append(a[100:260,80:470])
        pair=np.repeat(np.repeat(np.concatenate(pieces,axis=1),2,axis=0),2,axis=1)
        row=np.full((360,1560,4),[12,19,29,255],np.uint8);row[40:]=pair;rows.append(row)
    base=WORK/'ripple_contact_unlabelled.png';write(base,np.concatenate(rows,axis=0))
    label_sheet(base,QA/'test_ripples_comparison.png',[(10,360*i+8,'Frame %02d: per-frame OptiX (left) / temporal OptiX (right), decoded 2x crop'%f) for i,f in enumerate([0,12,24,36])])
    report('metrics.json',results)
    status('test A all decoded frames measured for temporal variation, compression error and wrap continuity; matched detail contact sheet saved')
    return results

def viewer(metrics):
    rows=''.join('<tr><td>'+kind+'</td><td>%.4f</td><td>%.4f</td><td>%.3f</td></tr>'%(metrics['sequences'][kind]['decoded_webm']['dry_interior_control']['temporal_std_mean'],metrics['sequences'][kind]['decoded_webm']['street_reflections']['cyclic_mean_abs_luma'],metrics['sequences'][kind]['decoded_webm']['full_crop']['seam_ratio_to_adjacent_mean']) for kind in ['noTD','TD'])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Roxy draft 4 comparisons</title>
<style>body{margin:0;background:#10151e;color:#e2ecf4;font:16px system-ui}main{max-width:1800px;margin:auto;padding:24px}h1{margin:0 0 8px}h2{margin-top:40px}p{max-width:1000px;line-height:1.5;color:#b9cad9}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;min-width:0}img,video{width:100%;background:#05090d;display:block}figcaption{padding:10px 0}button,a{color:#b8e5ff}button{background:#23364b;border:1px solid #61788a;border-radius:5px;padding:8px 16px;cursor:pointer}.controls{display:flex;align-items:center;gap:16px;margin:16px 0}input{flex:1}table{border-collapse:collapse}td,th{padding:10px;text-align:left;border-bottom:1px solid #3c4b59}small{color:#9dafbf}.hero{max-width:1280px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>
<main><h1>Roxy · draft 4</h1><p>720p, final-quality Cycles draft. Apartment roof unified and dressed across its full area. Wet reflections are rendered from the current neon sources. This is a draft review; no production pack has been built.</p>
<a href="DRAFT-4.md">Read the measurements and recommendation</a>
<h2>Current weather frame</h2><a href="draft_4.png"><img class="hero" src="draft_4.png" alt="Current cinema with wet roofs, rain and current neon reflections"></a>
<p><a href="draft_4_clean.png">Open clean frame</a> · <a href="test_ripples_still.png">Open ray-traced ripple still</a></p>
<h2>A · Ray-traced ripples</h2><p>Same 48 raw Cycles frames, 256 samples, fixed seed. Native 1280 × 360 street crop from the 1280 × 720 camera, 24 fps, two seconds. The left clip uses separate per-frame OptiX denoising. The right uses OptiX temporal history after one full warm-up period.</p>
<div class="pair"><figure><video id="a" preload="auto" muted loop playsinline src="test_ripples_clip_noTD.webm"></video><figcaption>Per-frame OptiX · no temporal denoising</figcaption></figure><figure><video id="b" preload="auto" muted loop playsinline src="test_ripples_clip.webm"></video><figcaption>Temporal OptiX · padded and trimmed</figcaption></figure></div>
<div class="controls"><button id="play">Loop both</button><button id="pause">Pause</button><input id="seek" aria-label="Frame" type="range" min="0" max="47" step="1" value="0"><output id="frame">Frame 0</output></div>
<small>The slider pauses and seeks both clips to the same frame. Open either video directly for full native size.</small>
<p><a href="test_ripples_clip_noTD.webm">Per-frame video</a> · <a href="test_ripples_clip.webm">Temporal video</a> · <a href="test_ripples_comparison.png">Matched decoded detail sheet</a></p>
<table><thead><tr><th>Version</th><th>Dry control σ</th><th>Wet motion + variation</th><th>Wrap / typical step</th></tr></thead><tbody>'''+rows+'''</tbody></table><p>Values are display luma levels on a 0–255 scale. The dry interior measurement is a flicker proxy. Wet-area differences include intended ripple motion; a smaller value can also mean lost detail. Inspect both clips before choosing.</p>
<h2>B · Neon glow</h2><p>The same current HDR render feeds both treatments. Left: current 2D Gaussian halo method. Right: HDR Bloom, faint red halation and restrained four-point aperture streaks.</p>
<div class="pair"><figure><a href="test_glare_before.png"><img src="test_glare_before.png" alt="Current two-dimensional neon halo"></a><figcaption>Before · 2D halo</figcaption></figure><figure><a href="test_glare_after.png"><img src="test_glare_after.png" alt="HDR compositor glare"></a><figcaption>After · HDR glare</figcaption></figure></div><p><a href="test_glare_comparison.png">Full comparison</a> · <a href="test_glare_details.png">2× pixel details</a></p><img class="hero" src="test_glare_details.png" alt="Labelled enlarged neon comparisons">
<p>Glare is an HDR lens-scattering approximation, not a measured physical lens simulation. The owner chooses the preferred look.</p></main>
<script>const a=document.querySelector('#a'),b=document.querySelector('#b'),seek=document.querySelector('#seek'),label=document.querySelector('#frame');document.querySelector('#play').onclick=async()=>{b.currentTime=a.currentTime;await Promise.all([a.play(),b.play()]);};document.querySelector('#pause').onclick=()=>{a.pause();b.pause();};seek.oninput=()=>{a.pause();b.pause();a.currentTime=b.currentTime=(Number(seek.value)+.1)/24;label.textContent='Frame '+seek.value;};function tick(){if(!a.paused){if(Math.abs(a.currentTime-b.currentTime)>.065)b.currentTime=a.currentTime;const f=Math.min(47,Math.floor(a.currentTime*24));seek.value=f;label.textContent='Frame '+f;}requestAnimationFrame(tick);}tick();</script></html>'''
    (QA/'draft4_comparison.html').write_text(page,encoding='utf-8')
    status('local side-by-side review viewer complete, with synchronized looping clips, frame seeking, stills and measurements')

def preservation():
    before=json.loads((QA/'draft4_protected_before.json').read_text());changed=[];missing=[]
    for name,expected in before.items():
        p=ROOT/name
        if not p.exists():missing.append(name)
        elif hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=expected:changed.append(name)
    current={str(p.relative_to(ROOT)) for folder in ROOT.glob('out*') if folder.is_dir() for p in folder.rglob('*') if p.is_file()}
    old={name for name in before if Path(name).parts[0].startswith('out')};added=sorted(current-old)
    render=json.loads((WORK/'ripples_render.json').read_text());source_audit=json.loads((WORK/'source_audit.json').read_text())
    source_hash=hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest()
    assert source_hash==render['source_sha256']==source_audit['source_sha256']
    stills=['draft_4.png','draft_4_clean.png','test_ripples_still.png','test_glare_before.png','test_glare_after.png']
    predecode([QA/name for name in stills])
    for name in stills:
        a=read(QA/name);assert a.shape==(720,1280,4) and np.all(a[:,:,3]==255),name
    metrics=json.loads((WORK/'metrics.json').read_text());seams={}
    for kind in ['noTD','TD']:
        d=metrics['sequences'][kind]['decoded_webm']['full_crop']
        seams[kind]={'wrap_mean_abs_luma':d['seam_last_to_first_mean_abs_luma'],'largest_internal_step':d['max_internal_adjacent_mean_abs_luma'],'criterion':'wrap <= 1.25 * largest internal step + 0.01 display-luma units','passed':d['seam_last_to_first_mean_abs_luma']<=1.25*d['max_internal_adjacent_mean_abs_luma']+.01}
    result={'protected_files_checked':len(before),'changed':changed,'missing':missing,'added_pack_files':added,'source_matches_render_and_audit':True,'native_opaque_720p_stills':stills,'decoded_seam_checks':seams,'passed':not(changed or missing or added) and all(s['passed'] for s in seams.values()),'out10_build_invoked':False}
    (QA/'draft4_validation.json').write_text(json.dumps(result,indent=2));assert result['passed'],result
    status('preservation check passed: %d protected files unchanged, no pack files added; out10 remains parked'%len(before))

if __name__=='__main__':
    comparison_glare();m=validation();viewer(m);preservation()
