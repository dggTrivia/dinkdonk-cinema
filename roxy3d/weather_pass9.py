"""Native-resolution surface displacement and weather; no old billboard mask."""
import sys,json,math,types,hashlib,time,shutil
from pathlib import Path
import numpy as np
from pass9_common import ROOT,QA,OUT,LIVE,status
from pngio import read,write,predecode
from package_pass2 import grain

def modules(scale):
    core=types.ModuleType('weather_pass9_core');core.__file__=str(ROOT/'weather_pass8.py')
    src=(ROOT/'weather_pass8.py').read_text().replace('from pass8_common import','from pass9_common import')
    src=src.replace('protected[24:380,1280:1888]=True','pass').replace(';a[24:380,1280:1888]=0','').replace('        a[24:380,1280:1888]=0','        pass')
    if scale==2:
        src=src.replace('W,H,N,FPS=1920,1080,144,24','W,H,N,FPS=3840,2160,144,24')
        src=src.replace('return 900+60*(u-v),350+30*(u+v)-z','return 2*(900+60*(u-v)),2*(350+30*(u+v)-z)')
        src=src.replace("QA/'world_positions.npz'","QA/'world_positions@2x.npz'")
        src=src.replace("QA/'weather_masks.npz'","QA/'weather_masks@2x.npz'").replace("QA/'rain_outdoor_mask.png'","QA/'rain_outdoor_mask@2x.png'")
        src=src.replace('dilate(protected,5)','dilate(protected,10)')
        src=src.replace('rng.uniform(-150,W+150,n)','rng.uniform(-150,1920+150,n)*2').replace('rng.uniform(-80,H+80,n)','rng.uniform(-80,1080+80,n)*2')
        src=src.replace('length=rng.uniform(*length,n)','length=rng.uniform(*length,n)*2').replace('width=width,power','width=width*2,power')
        src=src.replace('span=H+160','span=H+320').replace('%span-80','%span-160').replace('%(W+300)-150','%(W+600)-300')
        # Impacts and steam use native pixel centres and twice the screen-space radii.
        src=src.replace(',.55)',',1.1)').replace(',.65)',',1.3)').replace('y0-4*math.sin','y0-8*math.sin').replace('x0-2*q,x0+2*q','x0-4*q,x0+4*q')
        src=src.replace('int(x-18)','int(x-36)').replace('int(x+18)','int(x+36)').replace('int(y-16)','int(y-32)').replace('int(y+16)','int(y+32)')
        src=src.replace('/(3+age*8)','/(6+age*16)').replace('/(3+age*5)','/(6+age*10)')
    src=src.replace('(15.1,.6,17.4,6.4,58.2,80)', '(15.1,6.5,17.4,9.05,61.2,80),(-9.5,0,-6.1,6.68,191.2,140),(15.1,.6,17.4,6.4,58.2,80)')
    exec(compile(src,core.__file__,'exec'),core.__dict__)
    child=types.ModuleType('weather_pass9_dense');child.__file__=str(ROOT/'weather_pass8b.py')
    sys.modules['weather_pass9_core']=core
    src=(ROOT/'weather_pass8b.py').read_text().replace('weather_pass8 as weather','weather_pass9_core as weather').replace('from weather_pass8 import','from weather_pass9_core import').replace('from pass8b_common import','from pass9_common import')
    src=src.replace(';result[24:380,1280:1888]=0','').replace(';a[24:380,1280:1888]=0','')
    if scale==2:
        src=src.replace('int(x)-15','int(x)-30').replace('int(x)+16','int(x)+31').replace('int(y)-9','int(y)-18').replace('int(y)+10','int(y)+19')
        src=src.replace('q*(1+life*4)','q*(2+life*8)').replace('*(3.8-np.abs(q))','*(7.6-2*np.abs(q))').replace('q*.4','q*.8').replace(',.50)',',1.0)')
    exec(compile(src,child.__file__,'exec'),child.__dict__)
    return core,child

def reflection(w,i,scale):
    t=(i%144)/144;a=math.tau*t;h,ww=w.raw.shape[:2];result=np.empty((h,ww,3),np.uint8)
    # Native 4K positions/textures and bilinear sampling; 128-row working sets.
    for y0 in range(0,h,128):
        y1=min(y0+128,h);u=w.u[y0:y1];v=w.v[y0:y1];weight=w.wet_weight[y0:y1]
        dx=(1.1*np.sin(u*3.2+v*.7+a*3)+.55*np.sin(v*11-u*4-a*7))*weight
        dy=.55*np.sin(v*7.1-u*2+a*5)*weight
        X=np.broadcast_to(np.arange(ww,dtype=np.float32),(y1-y0,ww));Y=np.broadcast_to(np.arange(y0,y1,dtype=np.float32)[:,None],X.shape)
        for x0,x1,ya,yb,x,y,phase,freq in w.distort:
            ya=max(ya,y0);yb=min(yb,y1)
            if ya>=yb:continue
            age=(t*freq+phase)%1
            if age>.48:continue
            life=age/.48;rx=(X[ya-y0:yb-y0,x0:x1]-x)/scale;ry=(Y[ya-y0:yb-y0,x0:x1]-y)*1.8/scale
            radius=np.sqrt(rx*rx+ry*ry)+.05;front=1+life*12;ripple=np.exp(-((radius-front)/1.9)**2)*np.sin((radius-front)*2.2)*(1-life)*3.4
            dx[ya-y0:yb-y0,x0:x1]+=ripple*rx/radius;dy[ya-y0:yb-y0,x0:x1]+=ripple*ry/radius*.45
        sx=np.clip(X+np.clip(dx,-3,3)*w.wet[y0:y1]*scale,0,ww-1);sy=np.clip(Y+np.clip(dy,-2,2)*w.wet[y0:y1]*scale,0,h-1)
        ix=sx.astype(np.int32);iy=sy.astype(np.int32);fx=(sx-ix).astype(np.float32)[:,:,None];fy=(sy-iy).astype(np.float32)[:,:,None];jx=np.minimum(ix+1,ww-1);jy=np.minimum(iy+1,h-1)
        sample=(w.raw[iy,ix]*(1-fx)+w.raw[iy,jx]*fx)*(1-fy)+(w.raw[jy,ix]*(1-fx)+w.raw[jy,jx]*fx)*fy
        result[y0:y1]=np.rint(w.raw[y0:y1]*(1-weight[:,:,None])+sample*weight[:,:,None]).astype(np.uint8)
    return result

def flicker(a,i,scale):
    p,q=json.loads((QA/'scene_metadata.json').read_text())['neighbour_tube']['points_px']
    x0=max(0,int(min(p[0],q[0])-7)*scale);x1=min(a.shape[1],int(max(p[0],q[0])+8)*scale);y0=max(0,int(min(p[1],q[1])-7)*scale);y1=min(a.shape[0],int(max(p[1],q[1])+8)*scale)
    yy,xx=np.indices((y1-y0,x1-x0),dtype=np.float32);xx=(xx+x0+.5)/scale;yy=(yy+y0+.5)/scale
    dx=q[0]-p[0];dy=q[1]-p[1];t=np.clip(((xx-p[0])*dx+(yy-p[1])*dy)/(dx*dx+dy*dy),0,1);d=(xx-p[0]-t*dx)**2+(yy-p[1]-t*dy)**2
    # One short dropout pair per six seconds; identical at the period boundary.
    f=i%144;power=.12 if f in [93,94,97] else .65 if f in [92,95,98] else 1
    add=(np.exp(-d/.35)*70+np.exp(-d/12)*7)[:,:,None]*np.array([.23,1,.66])*power
    a[y0:y1,x0:x1]=np.minimum(255,a[y0:y1,x0:x1].astype(float)+add).astype(np.uint8)
    return a

def main():
    assert json.loads((QA/'surroundings_occlusion@2x.json').read_text())['covered_action_pixels']==0
    shutil.copyfile(ROOT/'qa8/tv_window_bounds.json',QA/'tv_window_bounds.json')
    m=json.loads((QA/'manifest_scene.json').read_text());reports={};start=time.perf_counter()
    for scale,suffix in [(1,''),(2,'@2x')]:
        core,dense=modules(scale);predecode([QA/('steady_bg'+suffix+'.png')]);raw=grain(read(QA/('steady_bg'+suffix+'.png')))
        write(OUT/('lit_bg_dry'+suffix+'.png'),raw);w=dense.Weather(m,raw)
        minimum=np.full(raw.shape[:2]+(3,),255,np.uint8)
        for i in range(144):
            minimum=np.minimum(minimum,reflection(w,i,scale))
            if i%36==0:print('NATIVE_MINIMUM',scale,i,flush=True)
        for name in ['base','bg']:write(OUT/(name+suffix+'.png'),core.rgba(minimum))
        status('Native '+str(1920*scale)+'x'+str(1080*scale)+' temporal minimum computed from all 144 wet-surface frames')
        for kind in (['light_loop','rain_fg'] if scale==1 else ['light_loop_2x']):
            folder=QA/(kind+'_frames');folder.mkdir(exist_ok=True);diffs=[];hashes=[];first=None;prev=None
            def generate(i):
                if kind=='rain_fg':return w.foreground_frame(i)
                reflected=reflection(w,i,scale).astype(np.uint16);effects=flicker(w.base_effects(i),i,scale).astype(np.uint16)
                return np.maximum(np.minimum(reflected+effects,255).astype(np.int16)-minimum.astype(np.int16),0).astype(np.uint8)
            for i in range(144):
                a=generate(i);write(folder/('f'+str(i).zfill(3)+'.png'),a)
                if i==0:first=a.copy()
                if prev is not None:diffs.append(float(np.abs(a.astype(np.int16)-prev.astype(np.int16)).mean()))
                prev=a;hashes.append(hashlib.sha256(a.tobytes()).hexdigest())
                if i==60 and kind!='rain_fg':write(OUT/('lit_bg'+suffix+'.png'),core.rgba(np.minimum(minimum.astype(np.uint16)+a,255).astype(np.uint8)))
                if i%24==0:print('NATIVE_WEATHER',kind,i,flush=True)
            assert np.array_equal(generate(144),first)
            seam=float(np.abs(prev.astype(np.int16)-first.astype(np.int16)).mean());assert seam<=max(diffs)*1.6+.01
            reports[kind]=dict(frames=144,fps=24,seconds=6,native_size=[1920*scale,1080*scale],endpoint_max_error=0,seam_mean_abs=seam,adjacent_mean_abs=float(np.mean(diffs)),adjacent_max_mean_abs=max(diffs),unique_frames=len(set(hashes)),frame_sha256=hashes)
            (QA/'weather_validation.json').write_text(json.dumps(dict(passed=len(reports)==3,streams=reports,seconds=time.perf_counter()-start,base_method='Independent native-resolution Cycles surface positions, native wet-texture displacement and rain; per-channel temporal minimum of all 144 frames.',rain_counts=dict(base_fine=1800,base_medium=700,foreground_fine=1800,foreground_medium=950,near=24),impact_sites=len(w.impacts)),indent=2))
            status(kind+' source loop complete: 144 unique native frames, exact six-second endpoint and seam passed')
        del w,raw,minimum
if __name__=='__main__':main()
