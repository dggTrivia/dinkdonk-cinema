"""Cat sheets, optional wheel spray, and the complete additive pass-5 manifest."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from pngio import read,write,predecode

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa5';OUT=ROOT/'out5'

def down_rgba(a):
    h,w,_=a.shape;rgb=a[:,:,:3].astype(np.float32);alpha=a[:,:,3:4].astype(np.float32)/255
    average=lambda v:v.reshape(h//2,2,w//2,2,v.shape[2]).mean(axis=(1,3))
    aa=average(alpha);color=np.divide(average(rgb*alpha),aa,out=np.zeros_like(average(rgb*alpha)),where=aa>0)
    result=np.rint(np.concatenate([color,aa*255],axis=2)).astype(np.uint8);result[result[:,:,3]==0,:3]=0
    return result

def contact_shadow(a,anim):
    h,w,_=a.shape;yy,xx=np.indices((h,w),dtype=np.float32)
    dx=(xx+.5)/2-32;dy=(yy+.5)/2-44;u=dx/120+dy/60;v=dy/60-dx/120
    ru,rv=(.16,.115) if anim=='sleep' else (.10,.082) if anim=='sit' else (.18,.075)
    shadow=.30*np.exp(-2*((u/ru)**2+(v/rv)**2));shadow[shadow<.004]=0
    alpha=a[:,:,3].astype(np.float32)/255;combined=alpha+shadow*(1-alpha)
    rgb=a[:,:,:3]*alpha[:,:,None]/np.maximum(combined[:,:,None],1e-8)
    result=np.rint(np.dstack([rgb,combined*255])).astype(np.uint8);result[result[:,:,3]==0,:3]=0
    return result

def sheets(frames,cols):
    h,w,c=frames[0].shape;rows=math.ceil(len(frames)/cols);a=np.zeros((h*rows,w*cols,c),np.uint8)
    for i,frame in enumerate(frames):a[(i//cols)*h:(i//cols+1)*h,(i%cols)*w:(i%cols+1)*w]=frame
    return a

def spray(direction):
    rng=np.random.default_rng(9505);particles=[]
    for i in range(44):particles.append((rng.uniform(.015,.16),rng.uniform(.18,.34),rng.uniform(.7,1.8),rng.uniform(-.42,.42),rng.uniform(.55,1.25),rng.uniform(.25,.65)))
    frames=[];h,w=56,96;yy,xx=np.indices((h*2,w*2),dtype=np.float32);xx=(xx+.5)/2;yy=(yy+.5)/2
    f=1 if direction=='+u' else -1;anchor=[48,31]
    for index in range(12):
        t=index/24;a=np.zeros((h*2,w*2,3),np.float32)
        for start,life,speed,side,vz,radius in particles:
            age=t-start
            if age<=0 or age>=life:continue
            gain=math.sin(math.pi*age/life)**1.3*max(0,min(1,(11-index)/2))
            u=-f*speed*age;v=side*age;z=max(0,vz*age-2.8*age*age)
            px=48+60*(u-v);py=31+30*(u+v)-73.484692*z
            dx=xx-px;dy=yy-py;gauss=np.exp(-(dx*dx+(dy*.7)**2)/(2*radius*radius))
            a+=gauss[:,:,None]*np.array([70,109,139])*gain
        a=np.minimum(a,220);a[:2]=0;a[-2:]=0;a[:,:2]=0;a[:,-2:]=0
        frame=np.rint(a).astype(np.uint8);frame[frame.max(axis=2)<2]=0
        if index in [0,11]:frame[:]=0
        frames.append(frame)
    return frames,anchor

def main():
    m=json.loads((QA/'manifest_vehicles.json').read_text());meta=json.loads((QA/'cat_metadata.json').read_text())
    paths=list((QA/'cat_raw').rglob('*.png'));predecode(paths);entries={};reports=[]
    for info in meta['animations']:
        name=info['name'];n=info['frames'];fps=info['fps'];frames=[]
        for i in range(n):frames.append(contact_shadow(read(QA/'cat_raw'/name/('f'+str(i).zfill(3)+'.png')),name))
        if info['loop']:
            endpoint=contact_shadow(read(QA/'cat_raw'/name/('f'+str(n).zfill(3)+'.png')),name)
            error=int(np.abs(endpoint.astype(np.int16)-frames[0].astype(np.int16)).max())
            assert error==0,(name,'period',error)
        else:error=None
        differences=[float(np.abs(frames[i].astype(np.int16)-frames[i-1].astype(np.int16)).mean()) for i in range(1,n)]
        seam=float(np.abs(frames[-1].astype(np.int16)-frames[0].astype(np.int16)).mean())
        if info['loop']:assert seam<=max(differences)*1.8+.01,(name,seam,max(differences))
        cols=5 if name.startswith('walk') else 8;rows=math.ceil(n/cols)
        filename='cat/'+name+'.png';filename2='cat/'+name+'@2x.png'
        write(OUT/filename,sheets([down_rgba(a) for a in frames],cols));write(OUT/filename2,sheets(frames,cols))
        entry={'file':filename,'file_2x':filename2,'frames':n,'columns':cols,'rows':rows,'fps':fps,
            'frame_width':64,'frame_height':64,'anchor':[32,44],'loop':info['loop'],'seconds':n/fps}
        if info['stride_tiles']:
            entry['stride_tiles']=info['stride_tiles'];entry['direction']={'walk_plus_u':'+u','walk_minus_u':'-u','walk_plus_v':'+v','walk_minus_v':'-v'}[name]
        entries[name]=entry
        reports.append({'name':name,'frames':n,'endpoint_max_error':error,'last_to_first_mae':seam,
            'adjacent_max_mae':max(differences),'unique_frames':len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames}),
            'bytes_1x':(OUT/filename).stat().st_size,'bytes_2x':(OUT/filename2).stat().st_size})
    m['cat']=entries
    m['cat_contract']={
        'character':'Original small ginger tabby with cream paws and chest, about 0.45 tiles long including tail; stylized to read beside 50px emotes.',
        'placement':'Frame top-left = P(u,v) - anchor; anchor is ground under body centre. Sort the cat at 1000 + round((u+v)*100).',
        'frames':'RGBA, straight alpha, row-major. frame=floor(timeSeconds*fps)%frames for loops. Clamp at frames-1 for stretch.',
        'resolution':'Coordinates and 64x64 frame size are 1x; @2x doubles every cell and sheet. Keep 1x CSS placement.',
        'lighting':'Rendered inside the unchanged pass-4 scene at (10.75,7.75), with the exact camera and its existing lighting. Soft contact shadow included.',
        'walk':'Four actual 3D orientations. Advance 0.32 tiles per 10-frame cycle; stance feet move backward at the corresponding speed. No travel is baked into the frame.',
        'walk_mapping':{'+u':'walk_plus_u','-u':'walk_minus_u','+v':'walk_plus_v','-v':'walk_minus_v'},
        'idle':'sleep and sit are three-second loops; stretch is an optional two-second one-shot, standing to stretch to standing.',
        'recommended_rest_uv':[10.75,7.75]}
    m['tyre_spray']={}
    for direction,slug in [('+u','plus_u'),('-u','minus_u')]:
        frames,anchor=spray(direction);file='tyre_spray/'+slug+'.png';file2='tyre_spray/'+slug+'@2x.png'
        low=[np.rint(a.reshape(56,2,96,2,3).mean(axis=(1,3))).astype(np.uint8) for a in frames]
        write(OUT/file,sheets(low,6));write(OUT/file2,sheets(frames,6))
        m['tyre_spray'][direction]={'file':file,'file_2x':file2,'frames':12,'columns':6,'rows':2,'fps':24,
            'frame_width':96,'frame_height':56,'anchor':anchor,'seconds':.5,'loop':False,'blend':'plus-lighter'}
    m['tyre_spray_contract']={'placement':'P(wheel_u,wheel_v)-anchor, at ground contact. Add below vehicle bodies and walkers.',
        'playback':'One-shot 12 frames at 24fps; first and last frames black. Emit while moving on wet road. Direction is vehicle travel direction.',
        'style':'Original deterministic ballistic droplets, cool wet-road highlights, on black; @2x doubles each source cell.'}
    m['pass5_validation']='../qa5/final_validation.json';m['status']='complete'
    m['validation']['pass5']='../qa5/final_validation.json'
    m['validation']['vehicle_slices']='../qa5/vehicle_additions_validation.json'
    m['validation']['cat']='../qa5/cat_validation.json'
    (QA/'cat_validation.json').write_text(json.dumps({'passed':True,'animations':reports,'native_render_scale':2,'alpha':'straight RGBA; 1x derived with premultiplied area averaging'},indent=2))
    pending=OUT/'manifest.pending.json';pending.write_text(json.dumps(m,indent=2));pending.replace(OUT/'manifest.json')
    print('PASS5_COMPLETE_MANIFEST',len(entries),'cat animations; 2 spray sheets',flush=True)

if __name__=='__main__':main()
