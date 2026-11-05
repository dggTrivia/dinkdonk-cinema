"""Bounded final-quality samples, never a production animation or out10 render."""
import sys,json,time,shutil,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from common import ROOT
from runtime import Renderer,WORK,atomic_json,sha,log,diff,within,rgba8,png
from fast_pipeline import combined,cut,crop,rect_for,compare_rgba,accepted,area2,profile_capture,native_capture

SMOKE=ROOT/'smoke';SMOKE.mkdir(exist_ok=True)
OPTS=dict(adaptive=True,threshold=.01,persistent=True)

def groups():
    r=Renderer(1280,720);beauty,maskpath,uv=combined(r,'fast27_combined_720')
    results=[]
    with np.load(maskpath) as masks:
        for spec in r.meta['groups']:
            name=spec['name'];x,y,w,h=rect_for(r,spec)
            rect=[x//3*3,y//3*3,(x+w+2)//3*3-x//3*3,(y+h+2)//3*3-y//3*3]
            a,ta=r.capture('fast27_ref_'+name,part=name,rect=rect,aov=True,**OPTS)
            b,tb=r.capture('fast27_noise_'+name,part=name,rect=rect,seed=2701,**OPTS)
            proposed=cut(crop(beauty,rect,r.width),crop(masks[name],rect,r.width))
            assert proposed.shape==a.shape,(name,proposed.shape,a.shape)
            noise=compare_rgba(a,b);delta=compare_rgba(a,proposed);ok=accepted(delta,noise)
            result=dict(name=name,rect=rect,noise=noise,difference=delta,accepted=ok,reference_seconds=ta,noise_seconds=tb)
            results.append(result);atomic_json(SMOKE/'group-comparison.json',dict(groups=results,complete=False));log('group_comparison',**result)
    atomic_json(SMOKE/'group-comparison.json',dict(groups=results,complete=True,scene_sha256=r.signature,runtime_sha256=sha(ROOT/'runtime.py')))

def quality():
    r=Renderer(1280,720)
    a,ta=r.capture('baseline_seed_a',seed=1701,persistent=False)
    b,tb=r.capture('baseline_seed_b',seed=2701,persistent=False)
    p,tp=r.capture('persistent_seed_a',seed=1701,persistent=True)
    c,tc=r.capture('adaptive_threshold_001',**OPTS)
    noise=diff(a,b);dp=diff(a,p);dc=diff(a,c)
    assert within(dp,noise) and within(dc,noise),(noise,dp,dc)
    report=dict(scene_sha256=r.signature,selected={'adaptive':True,'threshold':.01,'split':False,'persistent':True},quality={'noise_baseline':noise,'persistent':dict(**dp,passed=True),'adaptive_001':dict(**dc,passed=True)},times_seconds=dict(baseline_a=ta,baseline_b=tb,persistent=tp,adaptive_threshold_001=tc,trace_sum=ta+tb+tp+tc))
    atomic_json(SMOKE/'quality27.json',report)
    # Real native 1080p and 4K pixels, bounded to one detailed camera region.
    # Border stays aligned to the full 3840/1920 camera grids, without rescaling.
    rect=[660,230,660,390]
    r.width=1920;r.height=1080
    lo,tlo=r.capture('fast27_native1080_a',part='background',rect=rect,**OPTS)
    lb,tlb=r.capture('fast27_native1080_b',part='background',rect=rect,seed=2701,**OPTS)
    r.width=3840;r.height=2160
    hi,thi=native_capture(r,'fast27_filter_2_5',part='background',rect=rect,**OPTS)
    down=area2(hi);nd=diff(lo,lb);dd=diff(lo,down)
    reduction=dict(passed=within(dd,nd),noise=nd,difference=dd,rect_1080=rect,native1080_seconds=tlo,native1080_seed_b_seconds=tlb,native4k_seconds=thi,high_size=[hi.shape[1],hi.shape[0]],low_size=[lo.shape[1],lo.shape[0]],native_filter='BLACKMAN_HARRIS 1.5',high_filter='BLACKMAN_HARRIS 2.5',scope='Native camera pixel grids, one 660x390 logical crop; matched antialias footprint; no full production frame or animation')
    atomic_json(SMOKE/'downscale-comparison.json',reduction)
    assert reduction['passed'],reduction

def timing():
    import runtime_reference
    legacy=runtime_reference.Renderer(1280,720);before=[];references=[]
    rect=[600,540,450,240]
    for f in [0,2]:
        a,t=profile_capture(legacy,f'fast27_old_timing_{f}',part='queue_front',rect=rect,frame=f,**OPTS);before.append(t);references.append(a)
    start=time.perf_counter();legacy.display(a,WORK/'fast27_timing_before.png',glare=False);display_before=time.perf_counter()-start
    new=Renderer(1280,720);after=[];differences=[]
    for f in [0,2]:
        a,_=new.capture(f'fast27_new_timing_{f}',part='queue_front',rect=rect,frame=f,force=True,**OPTS)
        after.append(json.loads((WORK/'buffers'/f'fast27_new_timing_{f}.json').read_text())['timing'])
        differences.append(compare_rgba(references[len(differences)],a))
    # Same input buffer and output transform on each renderer.
    start=time.perf_counter();new.display(a,WORK/'fast27_timing_after.png',glare=False);displays=[display_before,time.perf_counter()-start]
    noise=json.loads((SMOKE/'quality27.json').read_text())['quality']['noise_baseline'];assert all(within(d,noise) for d in differences)
    atomic_json(SMOKE/'timing27.json',dict(before=before,after=after,display_seconds=displays,rect_1080=rect,frames=[0,2],same_quality=True,linear_differences=differences,scope='Sequential matched 720p camera crops on RTX 3050; no cloud timing claim'))

def draft():
    import package_layers as layers
    from runtime import pixels
    r=Renderer(1280,720)
    checks=json.loads((SMOKE/'group-comparison.json').read_text());assert checks['complete']
    beauty,maskpath,uv=combined(r,'fast27_combined_720')
    bg,tbg=r.capture('fast27_draft_background',part='background',**OPTS)
    r.display(bg,WORK/'fast27_draft_background.png');canvas=rgba8(WORK/'fast27_draft_background.png');canvas[:,:,3]=255
    stack=[];decisions=[]
    with np.load(maskpath) as masks:
        for result in checks['groups']:
            name=result['name'];rect=result['rect'];spec=next(s for s in r.meta['groups'] if s['name']==name)
            if result['accepted']:
                a=cut(crop(beauty,rect,r.width),crop(masks[name],rect,r.width));position=crop(uv,rect,r.width)
            else:
                a=pixels(WORK/'buffers'/('fast27_ref_'+name+'.exr'));position=np.load(WORK/'positions'/('fast27_ref_'+name+'.npz'))['uv']
            r.display(a,WORK/('draft_cut_'+name+'.png'),glare=False);p=rgba8(WORK/('draft_cut_'+name+'.png'));p[p[:,:,3]==0,:3]=0
            owner=layers.owners(spec,position)
            reconstructed=np.zeros_like(p,np.uint16)
            for i,tile in enumerate(layers.tile_clips(spec)):
                piece=p.copy();piece[owner!=i]=0;reconstructed+=piece
                if np.any(piece[:,:,3]):stack.append((99 if name=='paste_wall' else tile['z_index'],piece,round(rect[0]*2/3),round(rect[1]*2/3)))
            assert np.array_equal(reconstructed,p)
            decisions.append(dict(name=name,combined_cut=result['accepted']))
    for z,p,x,y in sorted(stack,key=lambda item:item[0]):layers.over(canvas,p,x,y)
    obs=[o for o in r.sc.objects if o.get('cloud_group')=='wc_dynamic'];x,y,w,h=r.rect(obs,5)
    rect=[x//3*3,y//3*3,(x+w+2)//3*3-x//3*3,(y+h+2)//3*3-y//3*3]
    wc,_=r.capture('fast27_draft_wc',part='wc_dynamic',rect=rect,**OPTS);r.display(wc,WORK/'fast27_draft_wc.png',glare=False)
    layers.over(canvas,rgba8(WORK/'fast27_draft_wc.png'),round(rect[0]*2/3),round(rect[1]*2/3))
    rain,tr=r.capture('smoke_weather',part='weather',rain=True,**OPTS);r.display(rain,WORK/'fast27_draft_weather.png',glare=False)
    p=rgba8(WORK/'fast27_draft_weather.png');rgb=np.rint(p[:,:,:3]*(p[:,:,3:4]/255)).astype(np.uint8)
    canvas[:,:,:3]=np.minimum(canvas[:,:,:3].astype(np.uint16)+rgb,255).astype(np.uint8)
    target=ROOT.parent.parent/'qa10/draft14-fast.png';png(target,canvas)
    atomic_json(SMOKE/'draft27.json',dict(file='qa10/draft14-fast.png',size=[1280,720],sha256=sha(target),groups=decisions,depth_slices=len(stack),depth_reconstruction_exact=True,weather_blend='plus-lighter',background_seconds=tbg,weather_seconds=tr,scope='Single phase 0, approved fixed camera and final quality; source-over depth slices plus phase-0 wet contribution and additive weather'))

def tail():
    import copy
    import production,validation,package_layers as layers
    from runtime import pixels
    from video import encode_and_validate
    out=WORK/'smoke_tail/pack';qa=WORK/'smoke_tail/qa';out.mkdir(parents=True,exist_ok=True);(qa/'positions').mkdir(parents=True,exist_ok=True)
    # Real rendered sprite/AOV; exact 2x2 reduction supplies both packing scales.
    high=rgba8(WORK/'draft_cut_queue_front.png');uv=np.load(WORK/'positions/fast27_ref_queue_front.npz')['uv']
    # Odd cropped dimensions are padded transparently, never stretched.
    h,w=high.shape[:2];ph=h%2;pw=w%2;high=np.pad(high,((0,ph),(0,pw),(0,0)));uv=np.pad(uv,((0,ph),(0,pw),(0,0)))
    from fast_pipeline import position2
    for scale,p,pos in [(2,high,uv),(1,np.rint(area2(high)).astype(np.uint8),position2(uv,high[:,:,3]/255))]:
        p[p[:,:,3]==0,:3]=0
        png(out/production.filename('occ_fixture',scale),p);np.savez_compressed(qa/'positions'/('fixture'+('@2x' if scale==2 else '')+'.npz'),uv=pos)
    spec=next(s for s in json.loads((ROOT/'production.json').read_text())['groups'] if s['name']=='queue_front')
    entry=dict(name='fixture',x=0,y=0,w=high.shape[1]//2,h=high.shape[0]//2,file='occ_fixture.png',file_2x='occ_fixture@2x.png',footprint=spec['footprint'],height_px=spec['height_px'])
    layers.OUT=out;layers.QA=qa;pieces=layers.depth_slices([entry])
    for p in pieces:p['file_2x']=p['file'][:-4]+'@2x.png'
    # Exercise both sheet layouts using real pixels, not a delivered test clip.
    sprites=[]
    for name,columns,rows,frames in [('door_fixture',4,4,16),('wet_fixture',8,6,48)]:
        e=dict(id=name,name=name,file=name+'.png',file_2x=name+'@2x.png',frame_width=entry['w'],frame_height=entry['h'],columns=columns,rows=rows,frames=frames)
        for scale,key in [(1,'file'),(2,'file_2x')]:production.sheet([rgba8(out/entry[key])]*frames,out/e[key],columns)
        sprites.append(e)
    original=json.loads((ROOT/'manifest.template.json').read_text());restroom=copy.deepcopy(original['restroom'])
    restroom['door_anim']=sprites[0]
    for s in restroom['stalls']:s['door_anim']=sprites[0]
    m=dict(layout=3,status='validation_pending',doors=original['doors'],door_anims=[sprites[0]]*3,restroom=restroom,occluders=[entry],render_layers=pieces,prop_loops=[sprites[1]],vehicles=copy.deepcopy(original['vehicles']))
    # Real bus captures exercise the new 4K-only render, 1x reduction and slicing.
    from vehicles import rebuild_bus
    rebuild_bus(m,out,qa)
    # Retain only bus in this fixture, and supply its unchanged compatible lights.
    m['vehicles']={'bus':m['vehicles']['bus']}
    for file in production.referenced_files(m):
        if not (out/file).exists() and (ROOT/'reuse'/file).exists():
            (out/file).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'reuse'/file,out/file)
    full=rgba8(ROOT.parent.parent/'qa10/draft14-fast.png')
    for scale,buffer in [(2,np.rint(area2(full)).astype(np.uint8)),(1,np.rint(area2(area2(full))).astype(np.uint8))]:
        for stem in ['bg','base','lit_bg','lit_bg_dry','full']:png(out/production.filename(stem,scale),buffer);m[stem+('_2x' if scale==2 else '')]=production.filename(stem,scale)
    weather=rgba8(WORK/'fast27_draft_weather.png');rgb=np.rint(weather[:,:,:3]*(weather[:,:,3:4]/255)).astype(np.uint8)
    folder=WORK/'smoke_tail/video_frames';folder.mkdir(exist_ok=True);small=np.rint(area2(area2(rgb))).astype(np.uint8)
    for f in range(48):png(folder/f'f{f:03d}.png',small)
    video=encode_and_validate('smoke_pack_weather',folder,out,frames=144);m['rain_fg']=dict(file=video['file'])
    atomic_json(qa/'videos.json',{'rain_fg':video});atomic_json(qa/'periodic_endpoints.json',[dict(scale=1,wrapped_linear_difference={'mean':0,'p99':0,'max':0},noise_baseline={'mean':0,'p99':0,'max':0},scope='Repeated real smoke frame; temporal loop not claimed')])
    atomic_json(out/'manifest.json',m)
    report=validation.validate(m,out,qa,smoke_size=[320,180]);assert report['passed'],report
    atomic_json(out/'validation.json',report);m.update(status='complete',validation='validation.json',notes='NOTES-PASS10.md');atomic_json(out/'manifest.json',m)
    (out/'NOTES-PASS10.md').write_text('Smoke packaging fixture. Real single-time smoke pixels, repeated sheets/video; four real bus states. No full production animation.\n')
    (out/'unreferenced_fixture.txt').write_text('must be removed')
    archive=production.finish_archive(m,out,WORK/'smoke_tail/out10.tar.gz');assert not (out/'unreferenced_fixture.txt').exists()
    atomic_json(SMOKE/'packaging27.json',dict(passed=True,validation=report,archive=archive,cleanup_proved=True,video=video))

def finish():
    from fast_pipeline import wet_frames,wet_phase
    env=os.environ.get('ROXY_WET_FRAMES')
    try:
        os.environ.pop('ROXY_WET_FRAMES',None);assert wet_frames()==24
        for count in [24,48]:
            os.environ['ROXY_WET_FRAMES']=str(count);phases=[wet_phase(f) for f in range(48)]
            assert len(set(phases))==count and all((p//6)%2==(f//6)%2 for f,p in enumerate(phases))
            assert [wet_phase(f%48) for f in range(144)]==phases*3
        os.environ['ROXY_WET_FRAMES']='25'
        try:wet_frames()
        except ValueError:pass
        else:raise AssertionError('Invalid wet count accepted')
    finally:
        if env is None:os.environ.pop('ROXY_WET_FRAMES',None)
        else:os.environ['ROXY_WET_FRAMES']=env
    comparison=json.loads((SMOKE/'group-comparison.json').read_text());assert comparison['complete'] and len(comparison['groups'])==39
    q=json.loads((SMOKE/'quality27.json').read_text());down=json.loads((SMOKE/'downscale-comparison.json').read_text());pack=json.loads((SMOKE/'packaging27.json').read_text());timing=json.loads((SMOKE/'timing27.json').read_text())
    assert down['passed'] and pack['passed']
    fast=dict(passed=True,scene_sha256=sha(ROOT/'scene.blend'),runtime_sha256=sha(ROOT/'runtime.py'),fast_pipeline_sha256=sha(ROOT/'fast_pipeline.py'),fallback_groups=[g['name'] for g in comparison['groups'] if not g['accepted']],combined_groups=[g['name'] for g in comparison['groups'] if g['accepted']],groups=comparison['groups'],downscale=down,timing=timing,packaging=pack['archive'],wet_frames=dict(default=24,optional=48,slots=48,columns=8,rows=6,fps=24,period_seconds=2,video_seconds=6,cadence_checks_passed=True),scope='Single phase per group at 720p; native 4K/1080 crop comparison; matched laptop timings; real bus captures and complete smoke packaging tail; no cloud benchmark or full animation')
    atomic_json(SMOKE/'fast-validation.json',fast)
    q.update(video_smoke=pack['video'],fast_pipeline=fast,scope=fast['scope']);atomic_json(SMOKE/'validation.json',q);atomic_json(ROOT/'speed_plan.json',q['selected'])
    log('smoke_complete',passed=True,combined_groups=fast['combined_groups'],fallback_groups=fast['fallback_groups']);print('SUCCESS mode=smoke',flush=True)

def smoke():
    from validation import preflight
    from contracts27 import run
    preflight();groups();quality();timing();draft();tail();run();finish()

def main():
    mode=sys.argv[-1]
    if mode=='groups':groups()
    elif mode=='quality':quality()
    elif mode=='timing':timing()
    elif mode=='draft':draft()
    elif mode=='tail':tail()
    elif mode=='finish':finish()
    else:raise ValueError(mode)

if __name__=='__main__':main()
