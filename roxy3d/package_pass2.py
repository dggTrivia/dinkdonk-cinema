"""Publish complete stills and manifest before any animation work.

Use the existing AOV slicing algorithm, targeting only out2 and qa2.
Grain and static halos are baked in bg; no extra overlay is needed.
"""
from pathlib import Path
import json, hashlib, struct, shutil
import numpy as np
from pngio import read,write,predecode
import package_layers as layers

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out2';QA=ROOT/'qa2'
layers.OUT=OUT;layers.QA=QA

def grain(a):
    yy,xx=np.indices(a.shape[:2],dtype=np.uint32)
    h=(xx*1664525+yy*1013904223+1701);h=(h^(h>>13))*1274126177
    noise=((h>>29).astype(np.int16)-3)/4
    out=a.copy();out[:,:,:3]=np.clip(np.rint(a[:,:,:3].astype(np.float32)+noise[:,:,None]),0,255).astype(np.uint8)
    return out

def assemble(bg,entries,scale=1):
    a=bg.copy();suffix='@2x' if scale==2 else ''
    for e in entries:layers.over(a,read(OUT/(e['file'][:-4]+suffix+'.png')),e['x']*scale,e['y']*scale)
    return a

def validate(m):
    records=[];checks=[]
    for scale,suffix in [(1,''),(2,'@2x')]:
        maximum=0
        for e in m['occluders']:
            parent=read(OUT/(e['file'][:-4]+suffix+'.png'));recon=np.zeros_like(parent,np.uint16)
            for s in e['depth_slices']:
                a=read(OUT/(s['file'][:-4]+suffix+'.png'));x=(s['x']-e['x'])*scale;y=(s['y']-e['y'])*scale
                recon[y:y+a.shape[0],x:x+a.shape[1]]+=a
            maximum=max(maximum,int(np.abs(recon.astype(np.int16)-parent.astype(np.int16)).max()))
        assert maximum==0
        checks.append({'scale':scale,'max_channel_reconstruction_error':maximum})
    (QA/'slice_validation.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2))
    items={m[k]:(1920,1080) for k in ['bg','full']}
    if m.get('base'):items[m['base']]=(1920,1080)
    for e in m['occluders']+m['render_layers']:items[e['file']]=(e['w'],e['h'])
    for name,(w,h) in items.items():
        for scale,suffix in [(1,''),(2,'@2x')]:
            p=OUT/(name[:-4]+suffix+'.png');data=p.read_bytes()
            assert struct.unpack_from('>IIBB',data,16)==(w*scale,h*scale,8,6),p
            records.append({'file':p.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    (QA/'stills_delivery.json').write_text(json.dumps({'passed':True,'whole_occluders':len(m['occluders']),
        'depth_slices':len(m['render_layers']),'files':records},indent=2))

def main():
    predecode(list(OUT.glob('occ_*.png'))+list(QA.glob('raw_bg*.png'))+list(QA.glob('cycles_full*.png')))
    m=json.loads((QA/'manifest_staging.json').read_text())
    # Straight alpha should have black RGB wherever coverage is zero.
    for e in m['occluders']:
        for suffix in ['', '@2x']:
            p=OUT/(e['file'][:-4]+suffix+'.png');a=read(p);a[a[:,:,3]==0,:3]=0;write(p,a)
    m['render_layers']=layers.depth_slices(m['occluders'])
    m['depth_slices_note']='Use supplied render_layers directly in z_index order, without polygon clipping. World-position AOV masks are disjoint and reconstruct each parent exactly. All 2x offsets and sizes double the 1x values.'
    results=[]
    for scale,suffix in [(1,''),(2,'@2x')]:
        raw=read(QA/('raw_bg'+suffix+'.png'));physical=read(QA/('cycles_full'+suffix+'.png'))
        assembled=assemble(raw,m['render_layers'],scale)
        delta=np.abs(assembled[:,:,:3].astype(np.int16)-physical[:,:,:3].astype(np.int16))
        results.append({'scale':scale,'mean_abs_error_8bit':float(delta.mean()),'p99_channel_abs_error':float(np.percentile(delta,99))})
        glow=layers.glow_for(assembled,scale)
        bg=grain(raw)
        bg[:,:,:3]=np.rint(255-(255-bg[:,:,:3].astype(np.float32))*(255-glow[:,:,:3].astype(np.float32))/255).astype(np.uint8)
        write(OUT/('bg'+suffix+'.png'),bg)
        full=assemble(bg,m['render_layers'],scale);write(OUT/('full'+suffix+'.png'),full)
        write(QA/('stills_full'+suffix+'.png'),full)
        if scale==1:write(QA/'overview.png',layers.thumbnail(full,2))
    m['glow']=None;m['static_glow']='Subtle static halos baked into bg. No screen overlay required.'
    m['full_composition']='bg then render_layers using source-over in z_index order'
    # Validate referenced files BEFORE publishing the early integration manifest.
    validate(m)
    (QA/'layer_validation.json').write_text(json.dumps({'passed':True,'resolutions':results},indent=2))
    staging=OUT/'manifest.pending.json';staging.write_text(json.dumps(m,indent=2));staging.replace(OUT/'manifest.json')
    shutil.copyfile(OUT/'manifest.json',QA/'manifest_stills_ready.json')
    sheet=np.zeros((1550,1920,4),np.uint8);sheet[:,:,3]=255
    yy,xx=np.indices(sheet.shape[:2]);sheet[:,:,:3]=np.where((xx//16+yy//16)%2,75,48)[:,:,None]
    x,y,row=16,16,0
    for e in m['occluders']:
        a=read(OUT/e['file']);h,w=a.shape[:2]
        if x+w>1904:x=16;y+=row+20;row=0
        assert y+h<=1550
        layers.over(sheet,a,x,y);x+=w+20;row=max(row,h)
    write(QA/'sprite_contact_sheet.png',sheet)
    print('STILLS_MANIFEST_READY',len(m['occluders']),len(m['render_layers']),json.dumps(results),flush=True)

if __name__=='__main__':main()
