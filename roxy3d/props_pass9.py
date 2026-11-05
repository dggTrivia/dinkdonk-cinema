"""Native 2x water, pane films, perspective chasing bulbs and neon halo."""
import json,math
import numpy as np
from pass9_common import ROOT,QA,OUT,LIVE,status
from pngio import write
from package_props_pass8 import sheet,validate
from package_cat_pass5 import down_rgba
from package_prop_loops import down
TAU=math.tau

def save(e,frames):
    for scale,key in [(1,'file'),(2,'file_2x')]:
        f='prop_loops/'+e['name']+('@2x' if scale==2 else '')+'.png';e[key]=f
        small=[(down_rgba(a) if a.shape[2]==4 else down(a)) for a in frames] if scale==1 else frames
        write(OUT/f,sheet(small,e['columns']))
    e.update(format='png-spritesheet',frame_width=e['w'],frame_height=e['h'],frame_order='row-major',loop_seconds=e['frames']/e['fps'])

def grid(e):
    yy,xx=np.indices((2*e['h'],2*e['w']),dtype=np.float32)
    sx=e['x']+(xx+.5)/2;sy=e['y']+(yy+.5)/2
    u=(sx-900)/60+9.052;z=350+(u+9.052)*30-sy
    return sx,sy,u,z

def water(e,i):
    sx,sy,u,z=grid(e);t=(i%72)/72;c=e['world_center_u'];phase=(t+e['water_phase'])%1
    inside=(z>5)&(z<140)&~((z>117.7)&(z<121.5))
    alpha=np.zeros_like(z);premul=np.zeros((*z.shape,3),np.float32)
    def layer(cov,col,opacity):
        nonlocal alpha,premul
        a=np.clip(cov*opacity,0,1)*inside;premul=np.array(col)*a[:,:,None]+premul*(1-a[:,:,None]);alpha=a+alpha*(1-a)
    for j,off in enumerate([-1.5,1.3]):
        ph=(phase+j*.43)%1;head=175-ph*225;dx=(u-c)*60-off-.35*np.sin(z*.12+j);length=22+18*j
        trail=np.clip((z-head)/2,0,1)*np.clip((head+length-z)/5,0,1)
        layer(np.exp(-(dx/.8)**2)*trail,[8,20,26],.32)
        layer(np.exp(-((dx+.4)/.26)**2)*trail,[155,185,192],.55)
        layer(np.exp(-(dx/1.05)**2-((z-head)/1.6)**2),[24,42,49],.55)
        layer(np.exp(-((dx+.34)/.35)**2-((z-head-.45)/.5)**2),[185,208,211],.75)
    rgb=np.divide(premul,alpha[:,:,None],out=np.zeros_like(premul),where=alpha[:,:,None]>1e-7)
    a=np.clip(np.rint(np.dstack([rgb,alpha*255])),0,255).astype(np.uint8);a[a[:,:,3]==0,:3]=0
    a[:2]=0;a[-2:]=0;a[:,:2]=0;a[:,-2:]=0
    return a

def film(e,lo,hi):
    sx,sy,u,z=grid(e)
    edge=np.clip((u-lo-.02)*90,0,1)*np.clip((hi-.02-u)*90,0,1)*np.clip(z-5,0,1)*np.clip(140-z,0,1)
    edge*=~((z>117.7)&(z<121.5))
    fine=(.5+.5*np.sin(u*73+np.sin(z*.2)))**8
    alpha=(.025+.035*fine)*edge;sill=np.exp(-((z-6)/.6)**2)*edge*.42
    alpha=np.maximum(alpha,sill);rgb=np.zeros((*z.shape,3),np.float32)+[67,91,106];rgb+=sill[:,:,None]*np.array([130,140,125])
    a=np.clip(np.rint(np.dstack([rgb,alpha*255])),0,255).astype(np.uint8);a[a[:,:,3]==0,:3]=0;return a

def bulbs(e,pts,i,chase):
    yy,xx=np.indices((e['h']*2,e['w']*2),dtype=np.float32);x=e['x']+(xx+.5)/2;y=e['y']+(yy+.5)/2;a=np.zeros((*x.shape,3),np.float32)
    for j,(px,py) in enumerate(pts):
        power=.45 if not chase else .20+.80*((j-(i%72)*60/72)%12<3)
        d=(x-px)**2+(y-py)**2
        a+=(np.exp(-d/.32)*170+np.exp(-d/5.2)*20)[:,:,None]*np.array([1,.62,.24])*power
    return np.clip(np.rint(a),0,255).astype(np.uint8)

def main():
    m=json.loads((QA/'manifest_scene.json').read_text());meta=json.loads((QA/'scene_metadata.json').read_text());loops=[];checks=[];budget=0
    for j,p in enumerate(e for e in m['render_layers'] if e['parent'] in ['glass_left','glass_right']):
        lo,hi=p['footprint'][0],p['footprint'][2];u=(lo+hi)/2;cx=900+60*(u-9.052)
        e=dict(name='water_'+p['name'],x=round(cx)-4,y=math.floor(350+30*(u+9.052)-142),w=8,h=142,z_index=p['z_index'],parent=p['parent'],parent_slices=[p['name']],world_center_u=u,water_phase=j*.217%1,frames=72,columns=8,rows=9,fps=12,blend='source-over',alpha='straight')
        frames=[water(e,i) for i in range(72)];checks.append(validate(e['name'],frames,water(e,72)));save(e,frames);loops.append(e);budget+=8*142*72*4*5
        x=math.floor(900+60*(lo-9.052))-1;y=math.floor(350+30*(lo+9.052)-141)-1
        w=math.ceil(900+60*(hi-9.052))-x+2;h=math.ceil(350+30*(hi+9.052)-4)-y+2
        f=dict(name='film_'+p['name'],x=x,y=y,w=w,h=h,z_index=p['z_index'],parent=p['parent'],parent_slices=[p['name']],frames=1,columns=1,rows=1,fps=12,blend='source-over',alpha='straight')
        save(f,[film(f,lo,hi)]);loops.append(f);budget+=w*h*4*5
    assert budget<=16*1024**2,budget
    status('Tall storefront runnels and pane-wide films packaged at nine slice depths; '+str(round(budget/1024**2,3))+' MiB decoded for both resolutions')
    for p in meta['poster_bulbs']:
        pts=p['points_px'];xs,ys=zip(*pts);x=math.floor(min(xs))-5;y=math.floor(min(ys))-5;w=math.ceil(max(xs))-x+5;h=math.ceil(max(ys))-y+5
        for kind in ['idle','chase']:
            n=1 if kind=='idle' else 72
            e=dict(name='poster_bulbs_'+str(p['door'])+'_'+kind,x=x,y=y,w=w,h=h,z_index=p['z_index'],frames=n,columns=1 if n==1 else 8,rows=1 if n==1 else 9,fps=12,blend='plus-lighter',alpha='none; black is zero',variant_group='poster_bulbs_'+str(p['door']),default_enabled=kind=='idle')
            frames=[bulbs(e,pts,i,kind=='chase') for i in range(n)];save(e,frames);loops.append(e)
            if n>1:checks.append(validate(e['name'],frames,bulbs(e,pts,n,True)))
    # Local halo around physical tube paths. It is sorted at the blade depth.
    paths=meta['neon_paths'];points=[p for path in paths for p in path['points_px']];xs,ys=zip(*points)
    x=math.floor(min(xs))-10;y=math.floor(min(ys))-10;w=math.ceil(max(xs))-x+10;h=math.ceil(max(ys))-y+10
    e=dict(name='dgg_neon_halo',x=x,y=y,w=w,h=h,z_index=1880,frames=1,columns=1,rows=1,fps=24,blend='plus-lighter',alpha='none; black is zero')
    yy,xx=np.indices((h*2,w*2),dtype=np.float32);xx=x+(xx+.5)/2;yy=y+(yy+.5)/2;a=np.zeros((*xx.shape,3),np.float32)
    for path in paths:
        col=np.array([.2,.58,1] if 'lowercase d ' in path['name'] else [1,.2,.5] if 'dot' in path['name'] else [.12,1,.6])
        for p,q in zip(path['points_px'],path['points_px'][1:]):
            dx=q[0]-p[0];dy=q[1]-p[1];t=np.clip(((xx-p[0])*dx+(yy-p[1])*dy)/(dx*dx+dy*dy+1e-5),0,1);d=(xx-p[0]-t*dx)**2+(yy-p[1]-t*dy)**2
            a+=np.exp(-d/14)[:,:,None]*col*2.6
    save(e,[np.clip(np.rint(a),0,60).astype(np.uint8)]);loops.append(e)
    m['prop_loops']=[e for e in m['prop_loops'] if not e['name'].startswith(('water_glass_','film_glass_'))]+loops
    (QA/'manifest_props.json').write_text(json.dumps(m,indent=2));(QA/'prop_validation.json').write_text(json.dumps(dict(passed=True,loops=checks,glass_decoded_bytes_both_scales=budget),indent=2))
    status('Five perspective poster idle/chase bulb pairs and bent-tube neon halo packaged; exact periodic endpoints and seams validated')
if __name__=='__main__':main()
