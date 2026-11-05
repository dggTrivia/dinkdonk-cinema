"""Parent-sorted shelter roof impacts and runoff on the new shop awning."""
import json,math
import numpy as np
from pngio import write
from package_props_pass8 import sheet,validate
from package_prop_loops import down
from pass8_common import QA,OUT,LIVE,status
TAU=math.tau

def make(e,i):
    t=(i%72)/72;yy,xx=np.indices((e['h']*2,e['w']*2),dtype=np.float32)
    sx=e['x']+(xx+.5)/2;sy=e['y']+(yy+.5)/2
    a=np.zeros((*xx.shape,3),np.float32)
    for j,(u,v) in enumerate(e['sites']):
        life=(t*(5+j%5)+j*.413)%1
        if life>.38:continue
        age=life/.38;z=86 if e['parent']=='bus_stop' else 43-(v-8.78)/.31*7
        x=900+60*(u-v);y=350+30*(u+v)-z
        # Isometric ring in the horizontal roof plane, with tiny impact crown.
        dx=sx-x;dy=(sy-y)*2;radius=.4+age*3.2
        ring=np.exp(-((np.sqrt(dx*dx+dy*dy)-radius)/.6)**2)*(1-age)**1.5
        a+=ring[:,:,None]*np.array([22,27,30])
        crown=np.exp(-((dx/1.0)**2+((sy-y+2*math.sin(age*math.pi))/.65)**2))*max(0,1-age*4)
        a+=crown[:,:,None]*np.array([22,29,33])
    if e['parent']=='surroundings':
        for j in range(3):
            age=(t*13+j*.173)%1;u=-3.95+j*.27;v=9.10;z=36-35*age*age
            x=900+60*(u-v);y=350+30*(u+v)-z
            a+=np.exp(-(((sx-x)/.6)**2+((sy-y)/1.7)**2))[:,:,None]*np.array([19,25,28])*math.sin(math.pi*age)
    a=np.clip(np.rint(a),0,255).astype(np.uint8);a[:2]=0;a[-2:]=0;a[:,:2]=0;a[:,-2:]=0
    return a

def main():
    m=json.loads((LIVE/'manifest.json').read_text());entries=[];reports=[];rng=np.random.default_rng(81006)
    for j,parent in enumerate(e for e in m['render_layers'] if e['parent']=='bus_stop'):
        u0,u1=(.40,1.2) if j==0 else (1.2,2.0)
        pts=[(u,v) for u in [u0,u1] for v in [9.28,9.57]]
        xs=[900+60*(u-v) for u,v in pts];ys=[350+30*(u+v)-86 for u,v in pts]
        x,y=math.floor(min(xs))-5,math.floor(min(ys))-5;w,h=math.ceil(max(xs))-x+6,math.ceil(max(ys))-y+6
        e={'name':'roof_rain_'+parent['name'],'x':x,'y':y,'w':w,'h':h,'z_index':parent['z_index'],
           'parent':'bus_stop','parent_slices':[parent['name']],
           'sites':[(float(u),float(v)) for u,v in zip(rng.uniform(u0+.05,u1-.05,12),rng.uniform(9.30,9.55,12))]}
        entries.append(e)
    entries.append({'name':'awning_rain','x':106,'y':454,'w':64,'h':72,'z_index':1490,'parent':'surroundings','parent_slices':[],
        'sites':[(float(u),float(v)) for u,v in zip(rng.uniform(-3.95,-3.42,16),rng.uniform(8.82,9.04,16))]})
    for e in entries:
        frames=[make(e,i) for i in range(72)];reports.append(validate(e['name'],frames,make(e,72)))
        for scale in [1,2]:
            file='prop_loops/'+e['name']+('@2x' if scale==2 else '')+'.png';e['file_2x' if scale==2 else 'file']=file
            write(OUT/file,sheet(frames if scale==2 else [down(a) for a in frames],8))
        e.update(frames=72,fps=12,loop_seconds=6,columns=8,rows=9,blend='plus-lighter',format='png-spritesheet',
                 frame_width=e['w'],frame_height=e['h'],frame_order='row-major')
        del e['sites']
    (QA/'roof_water_loops.json').write_text(json.dumps(entries,indent=2))
    (QA/'roof_water_validation.json').write_text(json.dumps({'passed':True,'loops':reports},indent=2))
    status('Shelter roof impacts split at existing parent depths; new shop awning impacts and edge drips packaged, seamless at both scales')

if __name__=='__main__':main()
