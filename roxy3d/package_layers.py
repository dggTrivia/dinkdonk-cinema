"""Offline packaging and QA, using Blender's bundled Python + NumPy.

Verifies both resolutions and straight alpha, creates a screen-blend glow layer,
checks source-over assembly against the independent Cycles full render, and emits
integration clipping polygons matching roxy.html's existing tile-depth strategy.
The delivered full.png is the reproducible layer assembly with glow. The original
independent full render is preserved as qa/cycles_full[ @2x ].png.
"""
from pathlib import Path
import json
import math
import shutil
import numpy as np
from pngio import read,write,predecode

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'; QA=ROOT/'qa'

def over(dst,src,x,y):
    h,w=src.shape[:2]
    target=dst[y:y+h,x:x+w]
    alpha=src[:,:,3:4].astype(np.float32)/255
    target[:,:,:3]=np.rint(src[:,:,:3]*alpha+target[:,:,:3]*(1-alpha)).astype(np.uint8)
    target[:,:,3]=255

def boxblur(a,r):
    for axis in [0,1]:
        pad=[(0,0)]*a.ndim;pad[axis]=(r,r)
        b=np.pad(a,pad,mode='edge')
        zshape=list(b.shape);zshape[axis]=1
        c=np.concatenate([np.zeros(zshape,np.float32),np.cumsum(b,axis=axis,dtype=np.float32)],axis=axis)
        left=[slice(None)]*a.ndim;right=left.copy()
        left[axis]=slice(0,-(2*r+1));right[axis]=slice(2*r+1,None)
        a=(c[tuple(right)]-c[tuple(left)])/(2*r+1)
    return a

def glow_for(a,scale):
    rgb=a[:,:,:3].astype(np.float32)/255
    light=np.clip((rgb.max(axis=2,keepdims=True)-.74)/.26,0,1)**2
    # Keep the intentionally empty billboard aperture empty.
    light[40*scale:364*scale,1296*scale:1872*scale]=0
    bright=rgb*light
    bloom=np.zeros_like(bright)
    for radius,strength in [(3,.25),(10,.30),(25,.16)]:
        b=bright
        for j in range(3):b=boxblur(b,radius*scale)
        bloom+=b*strength
    bloom[40*scale:364*scale,1296*scale:1872*scale]=0
    return np.dstack([np.clip(bloom*255,0,255).astype(np.uint8),np.full(a.shape[:2],255,np.uint8)])

def point(u,v,z=0):return [900+(u-v)*60,350+(u+v)*30-z]

def tile_clips(entry):
    u0,v0,u1,v1=entry['footprint'];height=entry['height_px']
    nu=max(1,math.ceil(u1-u0-.01));nv=max(1,math.ceil(v1-v0-.01))
    clips=[]
    for i in range(nu):
        for j in range(nv):
            a=u0+(u1-u0)*i/nu;b=u0+(u1-u0)*(i+1)/nu
            c=v0+(v1-v0)*j/nv;d=v0+(v1-v0)*(j+1)/nv
            poly=[point(a,c,height),point(b,c,height),point(b,c),point(b,d),point(a,d),point(a,d,height)]
            clips.append({'footprint':[a,c,b,d],'z_index':1000+round((a+b+c+d)*50),
                          'polygon_px':poly})
    return clips

def thumbnail(a,factor):
    h,w=a.shape[:2];h=h//factor*factor;w=w//factor*factor
    return a[:h,:w].reshape(h//factor,factor,w//factor,factor,4).mean(axis=(1,3)).astype(np.uint8)

def depth_slices(entries):
    """Assign every pixel to one tile using the actual rendered surface position.

    The two resolutions share integer 1x bounds, so all 2x offsets and dimensions
    are exact doubles. Masks are disjoint, preserving the parent sprite's alpha.
    """
    flattened=[]
    for e in entries:
        arrays=[];bins=[]
        u0,v0,u1,v1=e['footprint']
        nu=max(1,math.ceil(u1-u0-.01));nv=max(1,math.ceil(v1-v0-.01))
        for scale,suffix in [(1,''),(2,'@2x')]:
            a=read(OUT/(Path(e['file']).stem+suffix+'.png'))
            assert a.shape==(e['h']*scale,e['w']*scale,4),(e['name'],a.shape)
            uv=np.load(QA/'positions'/(e['name']+suffix+'.npz'))['uv']
            assert uv.shape==a.shape[:2]+(2,),(e['name'],uv.shape,a.shape)
            i=np.clip(np.floor((uv[:,:,0]-u0)/(u1-u0)*nu),0,nu-1).astype(np.int16)
            j=np.clip(np.floor((uv[:,:,1]-v0)/(v1-v0)*nv),0,nv-1).astype(np.int16)
            arrays.append(a);bins.append(i*nv+j)
        slices=[]
        for idx,tile in enumerate(tile_clips(e)):
            regions=[]
            for scale,a,owner in zip([1,2],arrays,bins):
                yy,xx=np.where((owner==idx)&(a[:,:,3]>0))
                if len(xx):regions.append([int(xx.min()//scale),int(yy.min()//scale),math.ceil((int(xx.max())+1)/scale),math.ceil((int(yy.max())+1)/scale)])
            if not regions:continue
            x0=max(0,min(r[0] for r in regions)-1);y0=max(0,min(r[1] for r in regions)-1)
            x1=min(e['w'],max(r[2] for r in regions)+1);y1=min(e['h'],max(r[3] for r in regions)+1)
            filename='slices/occ_'+e['name']+'_'+str(idx).zfill(2)+'.png'
            for scale,suffix,a,owner in zip([1,2],['','@2x'],arrays,bins):
                piece=a[y0*scale:y1*scale,x0*scale:x1*scale].copy()
                ids=owner[y0*scale:y1*scale,x0*scale:x1*scale]
                piece[ids!=idx]=0
                piece[piece[:,:,3]==0,:3]=0
                write(OUT/(filename[:-4]+suffix+'.png'),piece)
            tile.update({'name':e['name']+'_'+str(idx).zfill(2),'parent':e['name'],'file':filename,
                         'x':e['x']+x0,'y':e['y']+y0,'w':x1-x0,'h':y1-y0,
                         'height_px':e['height_px']})
            slices.append(tile);flattened.append(tile)
        e['depth_slices']=slices
        print('SLICES',e['name'],len(slices),flush=True)
    return sorted(flattened,key=lambda e:e['z_index'])

def main():
    predecode(list(OUT.glob('*.png'))+list(QA.glob('cycles_full*.png')))
    manifest=json.loads((OUT/'manifest.json').read_text())
    manifest['baked_signs']=['tickets','snackbar','gate','restroom','roxy','bus95','arcade_orbit','popcorn','standee_midnight','standee_voyager']
    manifest['footprint_changes']=[{'name':'offscreen_street_and_sidewalk_padding',
        'original':[-9,9.15,19,13.5],'footprint':[-12,9.15,23,13.5],
        'reason':'Padding is wholly outside the image. Visible walkable areas and every prop footprint remain unchanged.'}]
    entries=manifest['occluders']; results=[]
    render_layers=depth_slices(entries)
    for scale in [1,2]:
        suffix='@2x' if scale==2 else ''
        bg=read(OUT/('bg'+suffix+'.png'))
        assert bg.shape==(1080*scale,1920*scale,4),bg.shape
        assembly=bg.copy()
        rawpath=QA/('cycles_full'+suffix+'.png')
        if not rawpath.exists():shutil.copyfile(OUT/('full'+suffix+'.png'),rawpath)
        physical=read(rawpath)
        layer_results=[]
        for e in entries:
            path=OUT/(Path(e['file']).stem+suffix+'.png')
            a=read(path);expected=(e['h']*scale,e['w']*scale,4)
            assert a.shape==expected,(path,a.shape,expected)
            assert a[:,:,3].max()>0,path
            assert a[:,:,3].min()==0,path
            mask=a[:,:,3]>0;yy,xx=np.where(mask)
            layer_results.append({'name':e['name'],'size':[a.shape[1],a.shape[0]],
                                  'alpha_bounds':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],
                                  'fractional_alpha_pixels':int(((a[:,:,3]>0)&(a[:,:,3]<255)).sum())})
            # Explicitly clear RGB in fully transparent pixels; no dark fringe is introduced.
            a[a[:,:,3]==0,:3]=0
            write(path,a)
        for e in render_layers:
            a=read(OUT/(e['file'][:-4]+suffix+'.png'))
            over(assembly,a,e['x']*scale,e['y']*scale)
        delta=np.abs(assembly[:,:,:3].astype(np.int16)-physical[:,:,:3].astype(np.int16))
        result={'scale':scale,'layers':layer_results,'comparison_to_independent_cycles':{
                'mean_abs_error_8bit':float(delta.mean()),'p99_channel_abs_error':float(np.percentile(delta,99)),
                'pixels_any_channel_over_16':int((delta.max(axis=2)>16).sum()),
                'note':'Independent denoising and display-space alpha can cause small differences.'}}
        results.append(result)
        write(QA/('assembled_without_glow'+suffix+'.png'),assembly)
        write(QA/('difference_x4'+suffix+'.png'),np.dstack([np.minimum(delta*4,255).astype(np.uint8),np.full(delta.shape[:2],255,np.uint8)]))
        glow=glow_for(assembly,scale)
        write(OUT/('glow'+suffix+'.png'),glow)
        full=assembly.copy()
        full[:,:,:3]=np.rint(255-(255-assembly[:,:,:3].astype(np.float32))*(255-glow[:,:,:3].astype(np.float32))/255).astype(np.uint8)
        write(OUT/('full'+suffix+'.png'),full)
        if scale==1:
            write(QA/'overview.png',thumbnail(full,2))
        print('QA_SCALE',scale,json.dumps(result['comparison_to_independent_cycles']),flush=True)
    manifest['render_layers']=render_layers
    manifest['glow']='glow.png'
    manifest['glow_blend_mode']='screen'
    manifest['full']='full.png'
    manifest['full_composition']='bg, then render_layers in listed z_index order using source-over, then glow using screen'
    manifest['depth_slices_note']='Use supplied render_layers sprites directly, without additional polygon clipping. Disjoint masks are derived from a Cycles world-position AOV, using the same tile subdivision and z_index as original addProp(). Each pixel belongs to exactly one piece. polygon_px is retained for reference only. Full parent sprites are also included as requested.'
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (QA/'layer_validation.json').write_text(json.dumps({'passed':True,'resolutions':results},indent=2))
    # Contact sheet over checkerboard, at 1:1 scale, for all sprite edge inspection.
    sheet=np.zeros((1200,1920,4),np.uint8);sheet[:,:,3]=255
    yy,xx=np.indices(sheet.shape[:2]);shade=np.where((xx//16+yy//16)%2,75,48)
    sheet[:,:,:3]=shade[:,:,None]
    x,y,row_h=16,16,0
    for e in entries:
        a=read(OUT/e['file']);h,w=a.shape[:2]
        if x+w>1904:x=16;y+=row_h+20;row_h=0
        if y+h>1200:break
        over(sheet,a,x,y);x+=w+20;row_h=max(row_h,h)
    write(QA/'sprite_contact_sheet.png',sheet)

if __name__=='__main__':main()
