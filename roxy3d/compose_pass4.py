"""Self-contained out4 packaging, retaining all prior metadata and fixed crops."""
from pathlib import Path
import json,shutil,math,hashlib,time
import numpy as np
from pngio import read,write,predecode
import package_layers as layers
from package_pass2 import grain
import make_loop as motion

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa4';OUT=ROOT/'out4';SOURCE=ROOT/'out3'
def at2(name):return name[:-4]+'@2x.png'
def rgba(a):return np.dstack([a,np.full(a.shape[:2],255,np.uint8)])

def assemble(bg,m,scale=1):
    result=bg.copy()
    for e in m['render_layers']:
        layers.over(result,read(OUT/(at2(e['file']) if scale==2 else e['file'])),e['x']*scale,e['y']*scale)
    return result

def fixed_slices(m):
    """Use the original AOV owner field with the original published rectangles."""
    report=[]
    for e in m['occluders']:
        u0,v0,u1,v1=e['footprint'];nu=max(1,math.ceil(u1-u0-.01));nv=max(1,math.ceil(v1-v0-.01))
        for scale,suffix in [(1,''),(2,'@2x')]:
            a=read(QA/'minimum_sprites'/(e['file'][:-4]+suffix+'.png'));a[a[:,:,3]==0,:3]=0
            assert a.shape==(e['h']*scale,e['w']*scale,4)
            write(OUT/(e['file'][:-4]+suffix+'.png'),a)
            uv=np.load(ROOT/'qa2'/'positions'/(e['name']+suffix+'.npz'))['uv']
            i=np.clip(np.floor((uv[:,:,0]-u0)/(u1-u0)*nu),0,nu-1).astype(np.int16)
            j=np.clip(np.floor((uv[:,:,1]-v0)/(v1-v0)*nv),0,nv-1).astype(np.int16);owner=i*nv+j
            reconstructed=np.zeros_like(a,np.uint16)
            for s in e['depth_slices']:
                idx=int(Path(s['file']).stem.rsplit('_',1)[1]);x=(s['x']-e['x'])*scale;y=(s['y']-e['y'])*scale
                h=s['h']*scale;w=s['w']*scale
                piece=a[y:y+h,x:x+w].copy();piece[owner[y:y+h,x:x+w]!=idx]=0;piece[piece[:,:,3]==0,:3]=0
                write(OUT/(s['file'][:-4]+suffix+'.png'),piece);reconstructed[y:y+h,x:x+w]+=piece
            error=int(np.abs(reconstructed.astype(np.int16)-a.astype(np.int16)).max())
            assert error==0,(e['name'],scale,error)
            report.append({'name':e['name'],'scale':scale,'max_reconstruction_error':error})
    (QA/'slice_validation.json').write_text(json.dumps({'passed':True,'fixed_rectangles':True,'checks':report},indent=2))

def main():
    start=time.perf_counter();OUT.mkdir(exist_ok=True)
    m=json.loads((SOURCE/'manifest.json').read_text())
    for source in SOURCE.rglob('*'):
        if source.is_file() and source.name!='manifest.json':
            dest=OUT/source.relative_to(SOURCE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    predecode(list((QA/'minimum_sprites').glob('*.png'))+list((QA/'loop_basis').glob('*.png')))
    fixed_slices(m);bases_image={}
    for scale,suffix in [(1,''),(2,'@2x')]:
        raw=read(QA/'loop_basis'/('minimum'+suffix+'.png'));a=assemble(raw,m,scale)
        glow=layers.glow_for(a,scale);base=grain(raw)
        base[:,:,:3]=np.rint(255-(255-base[:,:,:3].astype(np.float32))*(255-glow[:,:,:3].astype(np.float32))/255).astype(np.uint8)
        write(OUT/('base'+suffix+'.png'),base);write(OUT/('bg'+suffix+'.png'),base);bases_image[scale]=base
        write(QA/('minimum_full'+suffix+'.png'),assemble(base,m,scale))
    raw=read(QA/'loop_basis'/'minimum.png')[:,:,:3].astype(np.float32)
    bases={name:motion.blur_light(np.maximum(read(QA/'loop_basis'/(name+'.png'))[:,:,:3].astype(np.float32)-raw,0)) for name in ['neon','billboard','projector','reflections']}
    for a in bases.values():a[a.max(axis=2)<1.5]=0;a[40:364,1296:1872]=0
    first=None;previous=None;changes=[];hashes=[]
    for index in range(motion.N+1):
        positive=motion.frame(index,bases)
        animated=np.minimum(bases_image[1][:,:,:3].astype(np.uint16)+positive,255).astype(np.uint8)
        additive=np.clip(animated.astype(np.int16)-bases_image[1][:,:,:3],0,255).astype(np.uint8)
        if index==motion.N:assert np.array_equal(additive,first);break
        if first is None:first=additive.copy()
        if previous is not None:changes.append(float(np.abs(additive.astype(np.int16)-previous.astype(np.int16)).mean()))
        previous=additive
        write(QA/'loop_frames'/('f'+str(index).zfill(3)+'.png'),rgba(additive))
        hashes.append(hashlib.sha256(additive.tobytes()).hexdigest())
        if index in [0,30,60,90,119]:
            complete=assemble(rgba(animated),m);write(QA/('loop_f'+str(index).zfill(3)+'.png'),complete)
            if index==60:
                write(OUT/'full.png',complete);write(OUT/'lit_bg.png',rgba(animated))
                doubled=motion.upscale2(additive);background=bases_image[2].copy()
                background[:,:,:3]=np.minimum(background[:,:,:3].astype(np.uint16)+doubled,255).astype(np.uint8)
                write(OUT/'lit_bg@2x.png',background);write(OUT/'full@2x.png',assemble(background,m,2))
        if index%24==0:print('PASS4_AMBIENT_FRAME',index,flush=True)
    seam=float(np.abs(previous.astype(np.int16)-first.astype(np.int16)).mean());assert seam<max(changes)*1.35
    (QA/'loop_validation.json').write_text(json.dumps({'passed':True,'frames':120,'fps':24,'seconds':5,
        'period_endpoint_max_channel_error':0,'last_to_first_mean_abs_error_8bit':seam,
        'adjacent_mean_abs_error_8bit':float(np.mean(changes)),'adjacent_max_mean_abs_error_8bit':max(changes),
        'frame_hashes':hashes,'composition_seconds':round(time.perf_counter()-start,3)},indent=2))
    m['pass']=4
    m['pass4_art']={'carpet':'Much lower saturation and contrast; darker worn entrance path.',
        'action_pools':[[4.85,6],[4.85,7.4],[6.6,5.05],[8.2,5.05],[9.8,5.05],[3.7,3.7]],
        'screen_spill':'Steady warm floor spill from all five screen doors, plus the existing periodic projector variation.',
        'countertops':'Darkened stone; reduced counter and partition trim emission; modest warm menu backlights.',
        'layout':'All prior geometry, rectangles, depth slices, vehicles, apertures and footprint contracts retained.'}
    (QA/'manifest_art.json').write_text(json.dumps(m,indent=2))
    print('PASS4_ART_READY',round(time.perf_counter()-start,3),flush=True)

if __name__=='__main__':main()
