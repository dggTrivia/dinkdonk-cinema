"""Original CRT states and restrained straight-alpha glass water, native 2x."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from pngio import read,write,predecode
from package_prop_loops import FONT,text_pixels,down
from package_cat_pass5 import down_rgba
from pass8_common import ROOT,QA,OUT,LIVE,status
TAU=math.tau
FONT.update({'H':['101','101','111','101','101'], '-':['000','000','111','000','000'],
 '0':['111','101','101','101','111'],'8':['111','101','111','101','111']})

def sheet(frames,cols):
    h,w,c=frames[0].shape;rows=math.ceil(len(frames)/cols);out=np.zeros((h*rows,w*cols,c),np.uint8)
    for i,a in enumerate(frames):out[(i//cols)*h:(i//cols+1)*h,(i%cols)*w:(i%cols+1)*w]=a
    return out

def validate(name,frames,endpoint):
    assert np.array_equal(frames[0],endpoint),name
    def visible(a):
        if a.shape[2]==4:return np.dstack([a[:,:,:3].astype(np.float32)*a[:,:,3:4]/255,a[:,:,3]])
        return a.astype(np.float32)
    diff=lambda a,b:float(np.abs(visible(a)-visible(b)).mean())
    adj=[diff(a,b) for a,b in zip(frames,frames[1:])];seam=diff(frames[-1],frames[0])
    assert seam<=max(adj)*1.6+.01,(name,seam,max(adj))
    return {'name':name,'endpoint_max_error':0,'last_to_first_mean_abs':seam,'adjacent_max_mean_abs':max(adj),
            'adjacent_mean_abs':float(np.mean(adj)),'unique_frames':len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames})}

def glass_frame(e,i):
    t=(i%72)/72;x,y,w,h=e['x'],e['y'],e['w'],e['h']
    yy,xx=np.indices((h*2,w*2),dtype=np.float32);sx=x+(xx+.5)/2;sy=y+(yy+.5)/2
    u=(sx-900)/60+9.052;z=350+(u+9.052)*30-sy
    center=e['world_center_u'];inside=(z>3.7)&(z<27.4)
    # Transparent water has a dark refracting edge and a narrow warm/cool glint.
    alpha=np.zeros_like(z);premul=np.zeros((*z.shape,3),np.float32)
    def layer(coverage,color,opacity):
        nonlocal alpha,premul
        a=np.clip(coverage*opacity,0,1)*inside;premul=np.asarray(color)*a[:,:,None]+premul*(1-a[:,:,None]);alpha=a+alpha*(1-a)
    for j,offset in enumerate([-6.3,0.2,6.5]):
        phase=(t*(j%2+1)+e['water_phase']+j*.283)%1
        length=8+j*6;head=29-phase*(31+length)
        dx=(u-center)*60-offset-.45*np.sin(z*.4+j)
        trail=np.clip((z-head)/1.5,0,1)*np.clip((head+length-z)/2,0,1)
        layer(np.exp(-(dx/1.15)**2)*trail,[9,20,27],.28)
        layer(np.exp(-((dx+.55)/.30)**2)*trail,[118,150,162],.34)
        bead=np.exp(-((dx/1.35)**2+((z-head)/1.8)**2))
        layer(bead,[11,25,32],.55)
        layer(np.exp(-(((dx+.45)/.48)**2+((z-head-.55)/.55)**2)),[173,185,184],.60)
        # A bead that pauses before merging with the descending runnel.
        merge=math.sin(math.pi*phase)**2
        layer(np.exp(-(((dx-1.3)/.8)**2+((z-(19+j*2))/.95)**2)),[130,158,169],.22*merge)
    sill=np.exp(-((z-4.15)/.55)**2)*np.exp(-(((u-center)*60)/8.7)**8)
    layer(sill,[91,116,130],.14+.04*math.sin(TAU*t))
    # Faint moving street reflection, confined to the wet cluster, never opaque.
    reflection=np.exp(-(((u-center)*60-2*math.sin(TAU*t))/5.5)**2-((z-13)/9)**2)
    layer(reflection,[88,77,111],.035)
    rgb=np.divide(premul,alpha[:,:,None],out=np.zeros_like(premul),where=alpha[:,:,None]>1e-6)
    a=np.clip(np.rint(np.dstack([rgb,alpha*255])),0,255).astype(np.uint8);a[a[:,:,3]==0,:3]=0
    a[:2]=0;a[-2:]=0;a[:,:2]=0;a[:,-2:]=0
    return a

def arcade_art(kind,i):
    n=72 if kind=='arcade_play' else 24;t=(i%n)/n;a=np.zeros((24,24,3),np.float32)
    if kind=='arcade_hiscore':
        intensity=.28+.72*(.5+.5*math.cos(TAU*t))**.7
        text_pixels(a,'HI',8,1,np.array([170,185,65])*intensity)
        text_pixels(a,'SCORE',2,8,np.array([90,190,158])*intensity)
        text_pixels(a,'00880',2,17,[163,100,170])
        return a
    # Original orbit-breaker: a paddle banks a cyan ball through colored targets.
    for r in range(2):
        for c in range(5):
            hit=(c+r*5+1)/12
            power=1 if t<hit or t>.92 else .14
            a[2+r*3:4+r*3,2+c*4:5+c*4]=np.array([170-r*70,95+r*65,95+r*55])*power
    px=10+int(round(6*math.sin(TAU*t)))
    a[21:23,px-3:px+4]=[145,145,185]
    bx=12+8*math.sin(TAU*t);by=14+5*math.cos(TAU*t*2)
    yy,xx=np.indices((24,24));a+=np.exp(-((xx-bx)**2+(yy-by)**2)/.8)[:,:,None]*np.array([65,195,185])
    a[:,0]=[12,35,40];a[:,-1]=[12,35,40]
    return a

def arcade_frame(e,i,mask):
    x,y,w,h=e['x'],e['y'],e['w'],e['h'];yy,xx=np.indices((h*2,w*2),dtype=np.float32)
    sx=x+(xx+.5)/2;sy=y+(yy+.5)/2;v=12.712-(sx-900)/60;z=350+(12.712+v)*30-sy
    ix=np.floor((8.02-v)/.37*24).astype(int);iy=np.floor((67-z)/21*24).astype(int)
    inside=(ix>=0)&(ix<24)&(iy>=0)&(iy<24);coverage=mask[:,:,:3].max(2)/255
    a=arcade_art(e['name'],i)[np.clip(iy,0,23),np.clip(ix,0,23)]*inside[:,:,None]*coverage[:,:,None]
    a+=coverage[:,:,None]*np.array([1.5,4.5,6.5]);a=np.clip(np.rint(a),0,255).astype(np.uint8)
    a[:2]=0;a[-2:]=0;a[:,:2]=0;a[:,-2:]=0
    return a

def main():
    m=json.loads((LIVE/'manifest.json').read_text());loops=[];reports=[];contacts=[]
    (OUT/'prop_loops').mkdir(exist_ok=True,parents=True)
    for j,parent in enumerate(e for e in m['render_layers'] if e['parent'] in ['glass_left','glass_right']):
        u=(parent['footprint'][0]+parent['footprint'][2])/2;cx=900+60*(u-9.052);cy=350+30*(u+9.052)-15.5
        e={'name':'water_'+parent['name'],'x':round(cx)-11,'y':round(cy)-20,'w':22,'h':40,'z_index':parent['z_index'],
           'parent':parent['parent'],'parent_slices':[parent['name']],'frames':72,'fps':12,'loop_seconds':6,'columns':8,'rows':9,
           'blend':'source-over','alpha':'straight','world_center_u':u,'water_phase':j*.217%1}
        frames=[glass_frame(e,i) for i in range(72)];r=validate(e['name'],frames,glass_frame(e,72))
        for scale in [1,2]:
            file='prop_loops/'+e['name']+('@2x' if scale==2 else '')+'.png';e['file_2x' if scale==2 else 'file']=file
            write(OUT/file,sheet(frames if scale==2 else [down_rgba(a) for a in frames],8))
        e.update(format='png-spritesheet',frame_width=22,frame_height=40,frame_order='row-major')
        r['decoded_bytes_both_scales']=22*40*72*4*5;reports.append(r);loops.append(e)
        # Enlarged contact cells on neutral glass, with alpha correctly composited.
        tiles=[]
        for i in [0,18,36,54,71]:
            a=frames[i];al=a[:,:,3:4]/255;bg=np.full_like(a[:,:,:3],48)
            tiles.append(np.rint(a[:,:,:3]*al+bg*(1-al)).astype(np.uint8))
        contacts.append(np.concatenate(tiles,axis=1))
    budget=sum(r['decoded_bytes_both_scales'] for r in reports);assert budget<=16*1024**2,budget
    write(QA/'glass_water_contact.png',np.repeat(np.repeat(np.concatenate(contacts,axis=0),2,0),2,1))
    status('Nine glass-water depth-slice atlases packaged: 72 frames at 12 fps; '+str(round(budget/1024**2,2))+' MiB decoded for both scales combined')
    old=next(e for e in m['prop_loops'] if e['name']=='arcade_attract');path=ROOT/'qa4/prop_masks/arcade_attract@2x.png';predecode([path]);mask=read(path)
    art=[]
    for kind,n in [('arcade_play',72),('arcade_hiscore',24)]:
        e=old.copy();e.update(name=kind,frames=n,rows=n//6,loop_seconds=n/24)
        frames=[arcade_frame(e,i,mask) for i in range(n)];reports.append(validate(kind,frames,arcade_frame(e,n,mask)))
        for scale in [1,2]:
            file='prop_loops/'+kind+('@2x' if scale==2 else '')+'.png';e['file_2x' if scale==2 else 'file']=file
            write(OUT/file,sheet(frames if scale==2 else [down(a) for a in frames],6))
        loops.append(e)
        art.append(np.concatenate([np.clip(arcade_art(kind,i),0,255).astype(np.uint8) for i in [0,n//4,n//2,3*n//4,n-1]],axis=1))
    write(QA/'arcade_states_contact.png',np.repeat(np.repeat(np.concatenate(art,axis=0),6,0),6,1))
    (QA/'new_prop_loops.json').write_text(json.dumps(loops,indent=2))
    (QA/'prop_validation.json').write_text(json.dumps({'passed':True,'loops':reports,'glass_decoded_bytes_combined':budget,'cashier_water_entries':0},indent=2))
    status('Arcade play and HI-SCORE states packaged at the unchanged attract rect, z-index and parent; all new prop periods and seams validated')

if __name__=='__main__':main()
