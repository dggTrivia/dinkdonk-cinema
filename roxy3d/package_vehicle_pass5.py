"""Copy the live pack read-only; add lossless vehicle slices and lamp states."""
from pathlib import Path
import json,math,shutil,time
import numpy as np
from pngio import read,write,predecode
from package_vehicles import road_light,bounds,project

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa5';OUT=ROOT/'out5';LIVE=ROOT/'out4'

def slice_vehicle(entry,variant,name,direction):
    f=1 if direction=='+u' else -1;footprint=variant.get('geometry_local_footprint',entry['geometry_local_footprint'])
    lo,hi=sorted([footprint[0]*f,footprint[2]*f]);count=math.ceil(hi-lo);edges=np.linspace(lo,hi,count+1)
    owners={};bodies={};rects=[]
    for scale,key,suffix in [(1,'file',''),(2,'file_2x','@2x')]:
        body=read(OUT/variant[key]);h,w=body.shape[:2];bodies[scale]=body
        x0=300-entry['anchor'][0];y0=230-entry['anchor'][1]
        uv=np.load(QA/'positions'/(name+suffix+'.npz'))['uv'][y0*scale:y0*scale+h,x0*scale:x0*scale+w]
        yy,xx=np.indices((h,w),dtype=np.float32)
        dx=(xx+.5)/scale-entry['anchor'][0];dy=(yy+.5)/scale-entry['anchor'][1]
        ground=dx/120+dy/60
        du=np.where((uv[:,:,0]>3)&(uv[:,:,0]<9),uv[:,:,0]-6,ground)
        owners[scale]=np.clip(np.searchsorted(edges,du,side='right')-1,0,count-1)
    slices=[];proof=[]
    for i in range(count):
        union=(bodies[1][:,:,3]>0)&(owners[1]==i)
        high=(bodies[2][:,:,3]>0)&(owners[2]==i)
        union |= high.reshape(entry['h'],2,entry['w'],2).any(axis=(1,3))
        x0,y0,x1,y1=bounds(union,2)
        info={'file':f'vehicles/slices/{name}_{i:02d}.png','file_2x':f'vehicles/slices/{name}_{i:02d}@2x.png',
              'x':x0,'y':y0,'w':x1-x0,'h':y1-y0,'du':round(float((edges[i]+edges[i+1])/2),6),
              'u_range':[round(float(edges[i]),6),round(float(edges[i+1]),6)]}
        for scale,key in [(1,'file'),(2,'file_2x')]:
            a=bodies[scale][y0*scale:y1*scale,x0*scale:x1*scale].copy()
            a[owners[scale][y0*scale:y1*scale,x0*scale:x1*scale]!=i]=0;a[a[:,:,3]==0,:3]=0
            write(OUT/info[key],a)
        slices.append(info)
    variant['slices']=slices
    for scale in [1,2]:
        recon=np.zeros_like(bodies[scale],dtype=np.uint16)
        for e in slices:
            a=read(OUT/e['file' if scale==1 else 'file_2x']);x=e['x']*scale;y=e['y']*scale
            recon[y:y+a.shape[0],x:x+a.shape[1]]+=a
        error=int(np.abs(recon.astype(np.int16)-bodies[scale].astype(np.int16)).max())
        assert error==0,(name,scale,error)
        proof.append({'name':name,'scale':scale,'pieces':count,'max_error':error,'max_section_tiles':float(np.diff(edges).max())})
    return proof

def lamp_variant(entry,variant,name,row,state,scale):
    suffix='@2x' if scale==2 else '';key='light_2x' if scale==2 else 'light'
    base=read(OUT/variant[key]);normal=road_light(read(QA/'light_raw'/(name+'_normal'+suffix+'.png')),row)
    changed=road_light(read(QA/'light_raw'/(name+'_'+state+suffix+'.png')),row)
    x0=300-entry['anchor'][0];y0=230-entry['anchor'][1];h,w=base.shape[:2]
    delta=np.maximum(changed[:,:,:3].astype(np.int16)-normal[:,:,:3].astype(np.int16),0)
    delta=delta[y0*scale:y0*scale+h,x0*scale:x0*scale+w].astype(np.float32)
    yy,xx=np.indices((h,w),dtype=np.float32)
    gx=(xx+.5)/scale+600-entry['anchor'][0];gy=(yy+.5)/scale+860-entry['anchor'][1]
    f=1 if row['direction']=='+u' else -1;L=row['length_tiles'];width=row['width_tiles'];bus=row['kind']=='bus'
    lamps=[]
    if state=='brake':
        for vv in [-width*.3,width*.3]:lamps.append((-L/2,vv,30 if bus else 15,[1,.018,.025],76,5.2))
    else:
        for uu in [-L/2+.08,L/2-.08]:lamps.append((uu,-width/2-.025,31 if bus else 13,[1,.32,.015],65,4.6))
    for u,v,z,color,power,radius in lamps:
        p=project(6+f*u,11+f*v,z);d=(gx-p[0])**2+(gy-p[1])**2
        delta += np.exp(-d[:,:,None]/(2*radius**2))*np.array(color)*power
    # Additions must fit the published light canvas without a hard rectangle.
    edge=np.minimum.reduce([xx/scale,yy/scale,(w-1-xx)/scale,(h-1-yy)/scale])
    delta*=np.clip((edge-1)/5,0,1)[:,:,None]
    result=np.minimum(255,base[:,:,:3].astype(np.float32)+delta).round().astype(np.uint8)
    result[result.max(axis=2)<2]=0
    file='vehicles/'+name+'_light_'+state+suffix+'.png';write(OUT/file,result)
    variant['light_'+state+('_2x' if scale==2 else '')]=file
    diff=result.astype(np.int16)-base[:,:,:3].astype(np.int16)
    assert diff.max()>20 and diff.min()>=0,(name,state,scale)
    return {'name':name,'state':state,'scale':scale,'added_rgb_sum':diff.sum(axis=(0,1)).tolist(),'max_added':int(diff.max())}

def main():
    start=time.perf_counter();OUT.mkdir(exist_ok=True)
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            target=OUT/p.relative_to(LIVE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    m=json.loads((LIVE/'manifest.json').read_text());rows=json.loads((ROOT/'qa3'/'render_vehicles.json').read_text())['renders']
    predecode(list((QA/'light_raw').glob('*.png'))+list((OUT/'vehicles').glob('*.png')))
    slices=[];lamps=[]
    for kind,directions in m['vehicles'].items():
        for direction,entry in directions.items():
            for opened,variant in [(False,entry)]+([(True,entry['door_open'])] if 'door_open' in entry else []):
                name=kind+('_plus' if direction=='+u' else '_minus')+('_open' if opened else '')
                slices+=slice_vehicle(entry,variant,name,direction)
                for state in ['brake']+(['indicator'] if kind in ['bus','taxi'] else []):
                    for scale in [1,2]:
                        row=next(r for r in rows if r['name']==name and r['scale']==scale)
                        lamps.append(lamp_variant(entry,variant,name,row,state,scale))
    m['pass']=5
    m['vehicle_slice_contract']={
        'placement':'Whole top-left = P(u,v)-direction.anchor. Slice top-left = whole top-left + [slice.x,slice.y].',
        'depth':'For each slice use 1000 + round((u + slice.du + v) * 100). du is signed world-u offset, including -u vehicles.',
        'resolution':'x/y/w/h remain logical 1x pixels. file_2x has exactly double the dimensions. Slices replace the whole body, not its lights.',
        'reconstruction':'Disjoint surface-owned pixels reconstruct the inherited straight RGBA body exactly, including its contact shadow.',
        'sections':'World-space longitudinal bins no longer than one tile, from actual geometry bounds; shadow-only pixels use their floor position.',
        'door_open':'Use door_open.slices with the same parent anchor and dimensions when the door is open.',
        'fallback':'The inherited whole-body sprite and centre-depth contract remain available for consumers without slice support.'}
    m['vehicle_lamp_variant_contract']={
        'composition':'Each new light is a complete replacement for light, on black for plus-lighter below all bodies. Do not add normal and variant together.',
        'brake':'Brighter red tail halo and ray-traced wet-road reflection; available for every direction and closed/open body.',
        'indicator':'Bus/taxi curb-side amber signal ON, including road reflections. Blink by alternating this complete light with normal.',
        'combined':'For simultaneous braking and indicator, add max(indicator-normal,0) to brake, clamped to 255; do not double headlights.',
        'anchor':'All variants preserve the published light dimensions and the direction anchor.'}
    (QA/'manifest_vehicles.json').write_text(json.dumps(m,indent=2))
    (QA/'vehicle_additions_validation.json').write_text(json.dumps({'passed':True,'slices':slices,'lights':lamps,'seconds':round(time.perf_counter()-start,3)},indent=2))
    print('PASS5_VEHICLES_PACKAGED',len(slices),len(lamps),flush=True)

if __name__=='__main__':main()
