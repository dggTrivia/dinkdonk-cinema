"""Six-second world-projected downpour and minimum-base wet reflections.

Cycles supplies the fixed lighting and visible surface positions. Periodic
analytic emission layers avoid per-frame denoiser noise. No downloaded art.
"""
from pathlib import Path
import json,math,time,hashlib,shutil,argparse
import numpy as np
from pngio import read,write,predecode
from package_pass2 import grain
from package_layers import over,boxblur
from make_loop import upscale2
from pass8_common import ROOT,QA,OUT,LIVE,status
W,H,N,FPS=1920,1080,144,24
Y,X=np.indices((H,W),dtype=np.float32);TAU=math.tau;ZPP=73.4846922835

def project(u,v,z=0):return 900+60*(u-v),350+30*(u+v)-z

def poly(points):
    inside=np.zeros((H,W),bool)
    for (x0,y0),(x1,y1) in zip(points,points[1:]+points[:1]):
        if y0!=y1:inside ^= ((y0>Y+.5)!=(y1>Y+.5))&(X+.5<(x1-x0)*(Y+.5-y0)/(y1-y0)+x0)
    return inside

def hull(points):
    ps=sorted(set(tuple(p) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in ps:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(ps):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]

def volume_mask(u0,v0,u1,v1,z0,z1):return poly(hull([project(u,v,z) for u in [u0,u1] for v in [v0,v1] for z in [z0,z1]]))

def dilate(mask,r):
    out=mask.copy()
    for d in range(1,r+1):
        out[d:] |= mask[:-d];out[:-d] |= mask[d:];out[:,d:] |= mask[:,:-d];out[:,:-d] |= mask[:,d:]
    # Include diagonal corners of the collar as well.
    first=out.copy()
    for d in range(1,r+1):out[d:] |= first[:-d];out[:-d] |= first[d:]
    return out

def masks(m):
    indoor=volume_mask(0,0,13,9,0,170)
    sheltered=volume_mask(.35,9.25,2.05,9.60,0,80)|volume_mask(-4.82,8.78,-2.62,9.09,0,36)
    protected=indoor|sheltered
    for e in m['marquees']:
        x,y=e['bottom_center'];w,h=e['inner_size'];protected[max(0,int(y-h-7)):int(y+7),int(x-w/2-7):int(x+w/2+7)]=True
    protected[24:380,1280:1888]=True
    outside=~dilate(protected,5)
    np.savez_compressed(QA/'weather_masks.npz',indoor=indoor,sheltered=sheltered,protected=protected,outside=outside)
    write(QA/'rain_outdoor_mask.png',np.repeat((outside*255).astype(np.uint8)[:,:,None],3,2))
    return outside,indoor,sheltered

def points(canvas,x,y,color,brightness,width=.7):
    x=np.asarray(x).ravel();y=np.asarray(y).ravel();br=np.broadcast_to(brightness,np.shape(x)).ravel()
    ix=np.floor(x).astype(np.int32);iy=np.floor(y).astype(np.int32);rad=max(1,int(math.ceil(width*2)))
    for dy in range(-rad,rad+1):
        for dx in range(-rad,rad+1):
            xx=ix+dx;yy=iy+dy;valid=(xx>=0)&(xx<W)&(yy>=0)&(yy<H)
            if not valid.any():continue
            weight=np.exp(-((xx[valid]+.5-x[valid])**2+(yy[valid]+.5-y[valid])**2)/(2*width**2))*br[valid]
            for c in range(3):np.add.at(canvas[:,:,c],(yy[valid],xx[valid]),weight*color[c])

def rain_seed(n,length,width,power,seed):
    rng=np.random.default_rng(seed)
    return dict(x=rng.uniform(-150,W+150,n),y=rng.uniform(-80,H+80,n),
                cycles=rng.integers(4,9,n),length=rng.uniform(*length,n),
                width=width,power=rng.uniform(*power,n),phase=rng.random(n))

def rain(a,row,t):
    # Integer whole traversals per period, fixed slant and independent phases.
    span=H+160;yy=(row['y']+t*span*row['cycles'])%span-80
    xx=(row['x']+yy*.19)%(W+300)-150
    samples=np.linspace(0,1,32)
    x=(xx[:,None]+row['length'][:,None]*samples*.19).ravel()
    y=(yy[:,None]+row['length'][:,None]*samples).ravel()
    brightness=(row['power'][:,None]*(.15+.85*np.sin(samples*math.pi))*(row['length'][:,None]/32)).ravel()
    points(a,x,y,[.78,.86,.94],brightness,row['width']/2)

class Weather:
    def __init__(self,m,raw):
        self.m=m;self.raw=raw[:,:,:3].astype(np.float32)
        self.outside,self.indoor,self.sheltered=masks(m)
        pos=np.load(QA/'world_positions.npz')['position'];self.pos=pos
        self.u=pos[:,:,0];self.v=pos[:,:,1];self.z=pos[:,:,2]*ZPP
        self.wet=(self.z>-1)&(self.z<3)&(self.v>9.15)&(self.v<16.4)&self.outside
        # Reflection movement stays on actual horizontal outdoor surfaces.
        edge=np.clip(np.minimum(self.v-9.15,16.4-self.v)*6,0,1)
        puddle=(.45+.55*(.5+.5*np.sin(self.u*1.73+self.v*.91)*np.sin(self.v*2.4-self.u*.6)))
        self.wet_weight=(self.wet*edge*puddle).astype(np.float32)
        self.distant=rain_seed(600,(10,24),1.0,(18,49),88031)
        self.middle=rain_seed(180,(18,32),1.35,(20,57),88032)
        self.foreground=rain_seed(300,(24,45),2.0,(25,69),88033)
        self.near=rain_seed(24,(45,70),3.5,(30,72),88034)
        rng=np.random.default_rng(88035);candidates=[]
        surfaces=[(-12,10.65,23,13.45,.16,800),(-12,9.17,23,10.48,.18,360),(-20,13.7,25,16.2,.18,300),
                  (-4.85,-.8,-1.35,8.55,235.2,160),(-1.0,.15,-.17,8.5,205.2,60),
                  (-1.8,16.65,3.0,20.8,91.2,120),(3.4,16.65,7.9,20.8,100.2,120),(8.3,16.65,13.8,20.8,107.2,120),
                  (15.1,.6,17.4,6.4,58.2,80),(18.1,-.8,21.9,6.4,192.2,100),(6.1,-4.8,15.8,-1.1,465.2,100)]
        for u0,v0,u1,v1,z,n in surfaces:
            for u,v in zip(rng.uniform(u0,u1,n),rng.uniform(v0,v1,n)):
                x,y=project(u,v,z);ix,iy=int(x),int(y)
                if 4<=ix<W-4 and 4<=iy<H-4 and self.outside[iy,ix]:
                    here=pos[iy,ix]
                    if abs(here[0]-u)<.24 and abs(here[1]-v)<.24 and abs(here[2]*ZPP-z)<7:
                        candidates.append((u,v,z,rng.random(),int(rng.integers(4,13)),rng.uniform(.055,.18),rng.uniform(17,43)))
        self.impacts=candidates
        # Runoff points on existing roofs, gutter edges and downspouts.
        self.drips=[(-4.7+j*.24,9.09,36,0,(j*.173)%1) for j in range(9)]
        self.drips += [(u,16.48,z,0,(u*.417)%1) for u,z in [(-1.85,94),(3.05,94),(3.35,103),(7.95,103),(8.25,110),(13.85,110)]]
        self.drips += [(-4.7,8.76,232,4,.3),(-1.35,8.76,232,4,.7),(.35,9.6,84,0,.17)]
        self.rng=rng
        self.tv=[]
        for row in json.loads((QA/'tv_window_bounds.json').read_text()):
            lo=row['min'];hi=row['max']
            mask=(self.u>=lo[0]-.005)&(self.u<=hi[0]+.005)&(self.v>=lo[1]-.005)&(self.v<=hi[1]+.005)&(self.z>=lo[2]-.2)&(self.z<=hi[2]+.2)
            self.tv.append(mask)

    def reflection(self,index):
        t=(index%N)/N;a=TAU*t
        dx=(1.9*np.sin(self.u*3.2+self.v*.7+a*3)+.7*np.sin(self.v*8-a*7))*self.wet_weight
        dy=(.9*np.sin(self.v*4.1-self.u+a*5))*self.wet_weight
        sx=np.clip(X+dx,0,W-1);sy=np.clip(Y+dy,0,H-1);ix=sx.astype(int);iy=sy.astype(int)
        fx=(sx-ix)[:,:,None];fy=(sy-iy)[:,:,None];jx=np.minimum(ix+1,W-1);jy=np.minimum(iy+1,H-1)
        sample=(self.raw[iy,ix]*(1-fx)+self.raw[iy,jx]*fx)*(1-fy)+(self.raw[jy,ix]*(1-fx)+self.raw[jy,jx]*fx)*fy
        return np.rint(self.raw*(1-self.wet_weight[:,:,None])+sample*self.wet_weight[:,:,None]).astype(np.uint8)

    def base_effects(self,index):
        t=(index%N)/N;a=np.zeros((H,W,3),np.float32)
        rain(a,self.distant,t);rain(a,self.middle,t)
        theta=np.linspace(0,TAU,28,endpoint=False)
        for u,v,z,phase,freq,radius,power in self.impacts:
            life=(t*freq+phase)%1
            if life>.32:continue
            age=life/.32;r=radius*(.10+.90*age)
            x,y=project(u+np.cos(theta)*r,v+np.sin(theta)*r,z)
            points(a,x,y,[.70,.79,.88],power*(1-age)**1.5,.55)
            if age<.20:
                x0,y0=project(u,v,z);q=age/.2
                points(a,[x0-2*q,x0+2*q],[y0-4*math.sin(q*math.pi)]*2,[.8,.87,.94],power*(1-q),.65)
        for u,v,top,bottom,phase in self.drips:
            age=(t*12+phase)%1;z=top-(top-bottom)*age*age;x,y=project(u,v,z)
            points(a,[x,x+.3],[y,y+2.4],[.69,.79,.85],25*math.sin(math.pi*age)**.4,.65)
        gutter=np.exp(-((self.v-10.56)/.045)**2)+np.exp(-((self.v-13.56)/.045)**2)
        flow=(6+9*(.5+.5*np.sin(self.u*11-TAU*t*12))**4)*gutter*(self.z<3)
        a+=flow[:,:,None]*np.array([.62,.75,.80])
        # Umbrella runoff collects outside the entrance and drains toward curb.
        run=np.exp(-((self.u-9.45)/.60)**2-((self.v-9.65)/.35)**2)*(self.z<3)
        a+=run[:,:,None]*(2+3*np.sin(self.v*24-TAU*t*8)**2)[:,:,None]*np.array([.7,.8,.85])
        # Restrained periodic vapour at a real roof outlet, with no denoising.
        for j in range(4):
            age=(t+j/4)%1;x,y=project(-3.8+age*.12,3.7,264+age*28)
            x0,x1=max(0,int(x-18)),min(W,int(x+18));y0,y1=max(0,int(y-16)),min(H,int(y+16))
            if x0<x1 and y0<y1:
                d=((X[y0:y1,x0:x1]-x)/(3+age*8))**2+((Y[y0:y1,x0:x1]-y)/(3+age*5))**2
                a[y0:y1,x0:x1]+=np.exp(-d)[:,:,None]*np.array([7,7,8])*math.sin(math.pi*age)**2
        a*=self.outside[:,:,None];a[24:380,1280:1888]=0
        for j,mask in enumerate(self.tv):
            a[mask]+=(1+math.sin(TAU*t*(7+j)+j))**2*np.array([1.0,1.9,2.8])
        a[24:380,1280:1888]=0
        return np.clip(np.rint(a),0,255).astype(np.uint8)

    def foreground_frame(self,index):
        t=(index%N)/N;a=np.zeros((H,W,3),np.float32)
        rain(a,self.foreground,t);rain(a,self.near,t);a*=self.outside[:,:,None]
        a[24:380,1280:1888]=0
        return np.clip(np.rint(a),0,255).astype(np.uint8)

def rgba(a):return np.dstack([a,np.full(a.shape[:2],255,np.uint8)])

def compose(bg,m,scale=1):
    a=bg.copy()
    for e in sorted(m['render_layers'],key=lambda e:e['z_index']):
        file=e['file'][:-4]+('@2x' if scale==2 else '')+'.png'
        over(a,read(OUT/file),e['x']*scale,e['y']*scale)
    return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');args=ap.parse_args()
    assert json.loads((QA/'surroundings_occlusion.json').read_text())['covered_action_pixels']==0
    start=time.perf_counter();OUT.mkdir(exist_ok=True)
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            dest=OUT/p.relative_to(LIVE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    m=json.loads((LIVE/'manifest.json').read_text())
    predecode([QA/'steady_bg.png',QA/'steady_bg@2x.png']+[OUT/e['file'] for e in m['render_layers']])
    raw=grain(read(QA/'steady_bg.png'));raw2=grain(read(QA/'steady_bg@2x.png'))
    for scale,a in [(1,raw),(2,raw2)]:
        old=read(LIVE/('base'+('@2x' if scale==2 else '')+'.png'))
        a[40*scale:364*scale,1296*scale:1872*scale]=old[40*scale:364*scale,1296*scale:1872*scale]
    weather=Weather(m,raw)
    if args.preview:
        a=weather.reflection(38);b=weather.base_effects(38);fg=weather.foreground_frame(38)
        a=compose(rgba(np.minimum(a.astype(np.uint16)+b,255).astype(np.uint8)),m)
        a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+fg,255).astype(np.uint8)
        write(QA/'preview_heavy_rain.png',a);write(QA/'preview_rain_fg.png',fg)
        (QA/'rain_preview_metadata.json').write_text(json.dumps({'visible_impact_sites':len(weather.impacts)},indent=2))
        print('PASS8_RAIN_PREVIEW',len(weather.impacts),flush=True);return
    # Actual temporal minimum of all 144 displaced surfaces, not a darker guess.
    minimum=np.full((H,W,3),255,np.uint8)
    for i in range(N):
        minimum=np.minimum(minimum,weather.reflection(i))
        if i%36==0:print('PASS8_REFLECTION_MINIMUM',i,flush=True)
    np.savez_compressed(QA/'minimum_reflection_base.npz',minimum=minimum)
    base=rgba(minimum);write(OUT/'base.png',base);write(OUT/'bg.png',base)
    removal=np.maximum(raw[:,:,:3].astype(np.int16)-minimum.astype(np.int16),0).astype(np.uint8)
    base2=raw2.copy();base2[:,:,:3]=np.maximum(base2[:,:,:3].astype(np.int16)-upscale2(removal).astype(np.int16),0).astype(np.uint8)
    write(OUT/'base@2x.png',base2);write(OUT/'bg@2x.png',base2)
    status('Wet reflection minimum base computed from all 144 displaced frames; 1x/2x base and background packaged')
    reports={}
    for kind in ['light_loop','rain_fg']:
        previous=None;first=None;diffs=[];hashes=[];folder=QA/(kind+'_frames');folder.mkdir(exist_ok=True)
        def generate(index):
            if kind=='rain_fg':return weather.foreground_frame(index)
            reflected=weather.reflection(index).astype(np.uint16);effects=weather.base_effects(index).astype(np.uint16)
            return (np.minimum(reflected+effects,255).astype(np.int16)-minimum.astype(np.int16)).clip(0,255).astype(np.uint8)
        for i in range(N):
            a=generate(i);write(folder/('f'+str(i).zfill(3)+'.png'),a)
            if i==0:first=a.copy()
            if previous is not None:diffs.append(float(np.abs(a.astype(np.int16)-previous.astype(np.int16)).mean()))
            previous=a;hashes.append(hashlib.sha256(a.tobytes()).hexdigest())
            if i in [0,38,60,143]:
                if kind=='light_loop':
                    bg=base.copy();bg[:,:,:3]=np.minimum(minimum.astype(np.uint16)+a,255).astype(np.uint8)
                    write(QA/('weather_base_f'+str(i).zfill(3)+'.png'),compose(bg,m))
                    if i==60:
                        write(OUT/'lit_bg.png',bg);write(OUT/'full.png',compose(bg,m))
                        hi=base2.copy();hi[:,:,:3]=np.minimum(hi[:,:,:3].astype(np.uint16)+upscale2(a),255).astype(np.uint8)
                        write(OUT/'lit_bg@2x.png',hi);write(OUT/'full@2x.png',compose(hi,m,2))
                else:
                    scene=read(QA/('weather_base_f'+str(i).zfill(3)+'.png'));scene[:,:,:3]=np.minimum(scene[:,:,:3].astype(np.uint16)+a,255).astype(np.uint8)
                    write(QA/('weather_full_f'+str(i).zfill(3)+'.png'),scene)
            if i%24==0:print('PASS8_WEATHER_FRAME',kind,i,flush=True)
        endpoint=generate(N);assert np.array_equal(endpoint,first),kind
        seam=float(np.abs(previous.astype(np.int16)-first.astype(np.int16)).mean());assert seam<=max(diffs)*1.4,(kind,seam,max(diffs))
        reports[kind]={'frames':N,'fps':FPS,'seconds':6,'endpoint_max_error':0,'seam_mean_abs':seam,'adjacent_mean_abs':float(np.mean(diffs)),
                       'adjacent_max_mean_abs':max(diffs),'unique_frames':len(set(hashes)),'frame_sha256':hashes,'source_aperture_max':0}
        status(('Heavy base rain, roof impacts, drainage/runoff and wet reflection loop' if kind=='light_loop' else 'Foreground heavy rain loop')+' rendered: 144 frames / 6 seconds / 24 fps; exact period endpoint')
    (QA/'weather_validation.json').write_text(json.dumps({'passed':True,'streams':reports,'visible_impact_sites':len(weather.impacts),
        'rain_counts':{'distant':600,'middle':180,'foreground':300,'near_camera':24},'reflective_displacement_px':[-2.6,2.6],
        'base_method':'Per-channel temporal minimum of all 144 displaced Cycles wet-surface images; nonnegative differences restore each frame exactly.',
        'seconds':round(time.perf_counter()-start,3)},indent=2))
    (QA/'manifest_weather_base.json').write_text(json.dumps(m,indent=2))

if __name__=='__main__':main()
