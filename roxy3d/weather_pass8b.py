"""Denser fine/medium weather and local impact-driven reflection disturbance."""
import sys,json,math,shutil
import numpy as np
import weather_pass8 as weather
from weather_pass8 import rain_seed,rain,points,project,rgba,X,Y,W,H,N,TAU
from pngio import read,write,predecode
from package_pass2 import grain
from pass8b_common import ROOT,QA,OUT,LIVE,status
weather.QA=QA;weather.OUT=OUT;weather.LIVE=LIVE;weather.status=status
BaseWeather=weather.Weather

class Weather(BaseWeather):
    def __init__(self,m,raw):
        super().__init__(m,raw)
        self.distant=rain_seed(1800,(8,20),.95,(15,38),88031)
        self.middle=rain_seed(700,(15,30),1.30,(18,43),88032)
        self.foreground=rain_seed(950,(20,36),1.65,(20,50),88033)
        self.fg_fine=rain_seed(1800,(8,18),.90,(14,32),88133)
        # 24 nearest drops stay exactly as sparse and bright as pass 8.
        alley=(self.u>13.06)&(self.v<9.15)&(self.z>-.7)&(self.z<.1)&self.outside
        self.wet|=alley
        self.wet_weight=np.maximum(self.wet_weight,alley.astype(np.float32)*.72)
        self.impacts=[(u,v,z,phase,freq,radius,power*(1.35 if z<3 else 1.05)) for u,v,z,phase,freq,radius,power in self.impacts]
        # Use visible ground impacts to perturb small local patches, not the
        # whole street in synchrony. Cached patch bounds keep the loop cheap.
        self.distort=[]
        for j,(u,v,z,phase,freq,radius,power) in enumerate(self.impacts):
            if z>3 or j%3:continue
            x,y=project(u,v,z);x0,x1=max(0,int(x)-15),min(W,int(x)+16);y0,y1=max(0,int(y)-9),min(H,int(y)+10)
            if x0<x1 and y0<y1:self.distort.append((x0,x1,y0,y1,x,y,phase,freq))
        rng=np.random.default_rng(88122);self.spray=[]
        for j in range(600):
            if j<400:u=rng.uniform(-12,23);v=(10.57 if j%2 else 13.48)+rng.uniform(-.10,.10)
            else:u=rng.normal(5.1,1.6);v=rng.uniform(10.6,13.4)
            x,y=project(u,v,.2);ix,iy=int(x),int(y)
            if 4<ix<W-4 and 4<iy<H-4 and self.outside[iy,ix] and abs(self.u[iy,ix]-u)<.25 and abs(self.v[iy,ix]-v)<.25:
                self.spray.append((x,y,rng.random(),int(rng.integers(7,16)),rng.uniform(20,44),rng.uniform(.7,1.2)))

    def reflection(self,index):
        t=(index%N)/N;a=TAU*t
        dx=(1.1*np.sin(self.u*3.2+self.v*.7+a*3)+.55*np.sin(self.v*11-self.u*4-a*7))*self.wet_weight
        dy=(.55*np.sin(self.v*7.1-self.u*2+a*5))*self.wet_weight
        for x0,x1,y0,y1,x,y,phase,freq in self.distort:
            age=(t*freq+phase)%1
            if age>.48:continue
            life=age/.48;rx=X[y0:y1,x0:x1]-x;ry=(Y[y0:y1,x0:x1]-y)*1.8
            radius=np.sqrt(rx*rx+ry*ry)+.05;front=1+life*12
            ripple=np.exp(-((radius-front)/1.9)**2)*np.sin((radius-front)*2.2)*(1-life)*2.7
            dx[y0:y1,x0:x1]+=ripple*rx/radius;dy[y0:y1,x0:x1]+=ripple*ry/radius*.45
        dx=np.clip(dx,-3,3)*self.wet;dy=np.clip(dy,-2,2)*self.wet
        sx=np.clip(X+dx,0,W-1);sy=np.clip(Y+dy,0,H-1);ix=sx.astype(int);iy=sy.astype(int)
        fx=(sx-ix)[:,:,None];fy=(sy-iy)[:,:,None];jx=np.minimum(ix+1,W-1);jy=np.minimum(iy+1,H-1)
        sample=(self.raw[iy,ix]*(1-fx)+self.raw[iy,jx]*fx)*(1-fy)+(self.raw[jy,ix]*(1-fx)+self.raw[jy,jx]*fx)*fy
        return np.rint(self.raw*(1-self.wet_weight[:,:,None])+sample*self.wet_weight[:,:,None]).astype(np.uint8)

    def base_effects(self,index):
        result=super().base_effects(index).astype(np.float32);spray=np.zeros_like(result);t=(index%N)/N
        for x,y,phase,freq,power,spread in self.spray:
            age=(t*freq+phase)%1
            if age>.30:continue
            life=age/.30;q=np.array([-1,-.45,.1,.6,1.1])
            xx=x+q*(1+life*4)*spread;yy=y-np.sin(life*math.pi)*(3.8-np.abs(q))+q*.4
            points(spray,xx,yy,[.69,.79,.86],power*(1-life)**1.6,.50)
        spray*=self.outside[:,:,None];result+=spray;result[24:380,1280:1888]=0
        return np.clip(np.rint(result),0,255).astype(np.uint8)

    def foreground_frame(self,index):
        t=(index%N)/N;a=np.zeros((H,W,3),np.float32)
        rain(a,self.fg_fine,t);rain(a,self.foreground,t);rain(a,self.near,t)
        a*=self.outside[:,:,None];a[24:380,1280:1888]=0
        return np.clip(np.rint(a),0,255).astype(np.uint8)

def main():
    QA.mkdir(exist_ok=True);shutil.copyfile(ROOT/'qa8/tv_window_bounds.json',QA/'tv_window_bounds.json')
    if '--preview' in sys.argv:
        from package_layers import over
        from finalize_pass8 import cell
        import finalize_pass8 as compositor
        compositor.OUT=OUT
        m=json.loads((LIVE/'manifest.json').read_text());predecode([QA/'steady_bg.png'])
        raw=grain(read(QA/'steady_bg.png'));old=read(LIVE/'base.png');raw[40:364,1296:1872]=old[40:364,1296:1872]
        w=Weather(m,raw);rgb=np.minimum(w.reflection(38).astype(np.uint16)+w.base_effects(38),255).astype(np.uint8)
        a=weather.compose(rgba(rgb),m)
        if (QA/'film_loops.json').exists():
            entries=[e for e in m['prop_loops'] if e['name'].startswith('water_glass_')]+json.loads((QA/'film_loops.json').read_text())
            for e in entries:over(a,cell(e,19,1),e['x'],e['y'])
        fg=w.foreground_frame(38);a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+fg,255).astype(np.uint8)
        write(QA/'preview_heavy_rain.png',a);write(QA/'preview_rain_fg.png',fg)
        status('Fine/medium downpour and pane-wide water composite preview rendered for visual inspection')
        return
    weather.Weather=Weather;weather.main()
    predecode([QA/'steady_bg.png',QA/'steady_bg@2x.png'])
    for scale,suffix in [(1,''),(2,'@2x')]:
        a=grain(read(QA/('steady_bg'+suffix+'.png')));original=read(LIVE/('base'+suffix+'.png'))
        a[40*scale:364*scale,1296*scale:1872*scale]=original[40*scale:364*scale,1296*scale:1872*scale]
        write(OUT/('lit_bg_dry'+suffix+'.png'),a)
    status('Weather-free fully lit fallback stills packaged at 1x/2x; wet surfaces retained, no rain/impact layers baked in')
    if '--preview' in sys.argv:return
    report=json.loads((QA/'weather_validation.json').read_text())
    report['rain_counts']={'base_fine':1800,'base_medium':700,'foreground_fine':1800,'foreground_medium':950,'near_camera':24}
    report['reflective_displacement_px']=[-3,3];report['local_impact_distortion']=True
    report['baseline_rain_counts']={'base':780,'foreground':324};report['source_pack']='out8'
    (QA/'weather_validation.json').write_text(json.dumps(report,indent=2))
    status('Downpour density and localized curb/lamp spray and reflection distortion recorded; 24 nearest streaks retained')

if __name__=='__main__':main()
