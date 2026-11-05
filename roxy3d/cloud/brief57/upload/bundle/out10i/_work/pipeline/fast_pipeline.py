"""Brief 27: measured group cuts, linear 2x2 reduction and unchanged sheet cadence."""
import json,math,time,os
from pathlib import Path
import numpy as np
from common import ROOT
from runtime import WORK,atomic_json,sha,diff,within,log,Renderer as BaseRenderer

def native_capture(r,*args,**kwargs):
    # Match the approved logical-pixel footprint after the 2x2 box reduction.
    # 1.5 at 4K was measurably too sharp; 2.5 passed the native-1080 noise gate.
    # Record this rendering choice in every receipt, including posed sprites.
    if r.width==3840:
        r.sc.cycles.pixel_filter_type='BLACKMAN_HARRIS';r.sc.cycles.filter_width=2.5
        kwargs['state']={**(kwargs.get('state') or {}),'pixel_filter_width':2.5}
    return BaseRenderer.capture(r,*args,**kwargs)

class NativeRenderer(BaseRenderer):
    capture=native_capture

def area2(a):
    h,w=a.shape[:2]
    assert h%2==w%2==0,(h,w)
    return a.reshape(h//2,2,w//2,2,*a.shape[2:]).mean(axis=(1,3),dtype=np.float32)

def position2(uv,alpha):
    weight=area2(alpha[:,:,None])
    return np.divide(area2(uv*alpha[:,:,None]),weight,out=np.zeros_like(uv[::2,::2]),where=weight>1e-7)

def wet_frames():
    n=int(os.environ.get('ROXY_WET_FRAMES','24'))
    if n not in (24,48):raise ValueError('ROXY_WET_FRAMES must be 24 or 48')
    return n

def wet_phase(f):
    # Keep the 48 slots, 24fps, 8x6 sheets and 2s/6s contract. At 24,
    # render even phases and repeat each slot twice. A/B changes at 6 slots
    # remain exact; chase and ripples complete the same 2s cycle three times.
    step=48//wet_frames();return f//step*step

def rect_for(r,spec):return r.rect([r.sc.objects[n] for n in spec['objects']],8)

def crop(a,rect,width):
    x,y,w,h=[round(v*width/1920) for v in rect]
    return a[y:y+h,x:x+w].copy()

def cut(beauty,mask):
    # Coverage comes from antialiased Cryptomatte, never a hard object index.
    mask=np.clip(mask,0,1)
    fraction=np.divide(mask,beauty[:,:,3],out=np.zeros_like(mask),where=beauty[:,:,3]>1e-7)
    return np.dstack([beauty[:,:,:3]*fraction[:,:,None],mask])

def combined(r,tag,frame=0):
    a,_=r.capture(tag,part='foreground',frame=frame,aov=True,mattes=True,adaptive=True,threshold=.01)
    return a,WORK/'positions'/(tag+'_masks.npz'),np.load(WORK/'positions'/(tag+'.npz'))['uv']

def policy():
    report=json.loads((ROOT/'smoke/fast-validation.json').read_text())
    assert report['scene_sha256']==sha(ROOT/'scene.blend')
    assert report['runtime_sha256']==sha(ROOT/'runtime.py')
    assert report['fast_pipeline_sha256']==sha(Path(__file__))
    assert report['passed']
    return report

def compare_rgba(a,b):
    d=diff(a,b);alpha=np.abs(a[:,:,3]-b[:,:,3]);d.update(alpha_mean=float(alpha.mean()),alpha_p99=float(np.percentile(alpha,99)))
    return d

def accepted(d,noise):
    return within(d,noise) and d['alpha_mean']<=noise['alpha_mean']+1e-7 and d['alpha_p99']<=noise['alpha_p99']+1e-7

def profile_capture(r,tag,**kwargs):
    """Wrap the untouched legacy path without moving its writes or toggles."""
    import runtime_reference as ref
    times={};originals={}
    def wrap(obj,name,label):
        original=getattr(obj,name);originals[(obj,name)]=original
        def run(*a,**kw):
            start=time.perf_counter()
            try:return original(*a,**kw)
            finally:times[label]=times.get(label,0)+time.perf_counter()-start
        setattr(obj,name,run)
    for obj,name,label in [(r,'phase','phase'),(r,'visibility','visibility'),(ref,'sha','hash'),(ref,'pixels','exr_read')]:wrap(obj,name,label)
    start=time.perf_counter()
    try:a,seconds=r.capture(tag,force=True,**kwargs)
    finally:
        for (obj,name),original in originals.items():setattr(obj,name,original)
    times['total']=time.perf_counter()-start;times['render_sync_trace_exr']=seconds
    atomic_json(WORK/(tag+'_profile.json'),times)
    return a,times
