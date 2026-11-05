"""Five-second periodic ambient loop, composed as positive sRGB light on black.

The delivered page contract is display-space plus-lighter. Fixed Cycles light
bases prevent temporal denoiser shimmer. Rain and splashes are separate analytic
emission passes projected through the same dimetric camera. No raster assets
are downloaded or synthesized by an image model.
"""
from pathlib import Path
import json,math,shutil,time,hashlib
import numpy as np
from pngio import read,write,predecode
import package_layers as layers
from package_pass2 import assemble,grain

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out2';QA=ROOT/'qa2'
BASIS=QA/'loop_basis';FRAMES=QA/'loop_frames'
N=120;FPS=24;TAU=math.tau
H=1080;W=1920
Y,X=np.indices((H,W),dtype=np.float32)
U=((X-900)/60+(Y-350)/30)/2
V=((Y-350)/30-(X-900)/60)/2

def polygon_mask(points):
    inside=np.zeros((H,W),bool)
    for (x0,y0),(x1,y1) in zip(points,points[1:]+points[:1]):
        if y0==y1:continue
        inside^=((y0>Y)!=(y1>Y))&(X<(x1-x0)*(Y-y0)/(y1-y0)+x0)
    return inside

def project(u,v,z=0):return (900+(u-v)*60,350+(u+v)*30-z)

BUILDING=polygon_mask([[900,180],[1680,570],[1680,740],[1140,1010],[360,620],[360,450]])
OUTSIDE=~BUILDING
for wall,t in [('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)]:
    x,y=project(0,t,124) if wall=='u' else project(t,0,124)
    OUTSIDE[max(0,int(y-100)):int(y+6),int(x-95):int(x+95)]=False
OUTSIDE[40:364,1296:1872]=False
STREET=(V>=9.15)&(V<=13.5)&(U>=-12)&(U<=23)
PAVEMENT=(V>=9.15)&(V<=10.5)

def blur_light(delta):
    bright=np.maximum(delta.max(axis=2,keepdims=True)-45,0)/210
    glow=delta*bright
    glow=layers.boxblur(layers.boxblur(glow,5),5)*.25+layers.boxblur(layers.boxblur(glow,17),17)*.16
    return np.maximum(delta+glow,0)

def upscale2(a):
    """Bilinear 2x, matching CSS video scaling with pixel-centre coordinates."""
    h,w=a.shape[:2];yy=np.clip((np.arange(h*2)+.5)/2-.5,0,h-1);xx=np.clip((np.arange(w*2)+.5)/2-.5,0,w-1)
    y0=yy.astype(int);x0=xx.astype(int);y1=np.minimum(y0+1,h-1);x1=np.minimum(x0+1,w-1)
    fy=(yy-y0)[:,None,None];fx=(xx-x0)[None,:,None]
    return np.rint((a[y0[:,None],x0]*(1-fx)+a[y0[:,None],x1]*fx)*(1-fy)+(a[y1[:,None],x0]*(1-fx)+a[y1[:,None],x1]*fx)*fy).astype(np.uint8)

def add_points(canvas,x,y,color,brightness,width=.65):
    x=np.asarray(x).ravel();y=np.asarray(y).ravel();br=np.broadcast_to(brightness,np.shape(x)).ravel()
    ix=np.floor(x).astype(np.int32);iy=np.floor(y).astype(np.int32)
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:
            xx=ix+dx;yy=iy+dy
            valid=(xx>=0)&(xx<W)&(yy>=0)&(yy<H)
            if not np.any(valid):continue
            weight=np.exp(-((xx[valid]+.5-x[valid])**2+(yy[valid]+.5-y[valid])**2)/(2*width**2))*br[valid]
            for channel in range(3):np.add.at(canvas[:,:,channel],(yy[valid],xx[valid]),weight*color[channel])

def rain_setup():
    rng=np.random.default_rng(199704)
    return {'x':rng.uniform(-160,1940,250),'y':rng.uniform(0,H+60,250),'speed':rng.integers(3,7,250),
        'phase':rng.uniform(0,TAU,250),'length':rng.uniform(9,21,250),'strength':rng.uniform(18,50,250),
        'su':rng.uniform(-7,19,145),'sv':rng.uniform(9.2,13.4,145),
        'sp':rng.random(145),'sf':rng.integers(2,6,145),'sr':rng.uniform(.06,.19,145)}

RAIN=rain_setup()
DOORS=[project(0,6.4),project(0,4),project(4.8,0),project(8.2,0),project(11.2,0)]
NEAREST=np.argmin(np.stack([(X-x)**2+(Y-y)**2 for x,y in DOORS]),axis=0)

def billboard_phase():
    left,right,top,bottom=1284.,1884.,28.,376.
    distance=np.stack([abs(Y-top),abs(X-right),abs(Y-bottom),abs(X-left)])
    edge=np.argmin(distance,axis=0);w=right-left;h=bottom-top
    s=np.choose(edge,[X-left,w+Y-top,w+h+right-X,2*w+h+bottom-Y])/(2*w+2*h)
    return s
CHASE=billboard_phase()

def frame(index,bases):
    t=(index%N)/N;angle=TAU*t
    # Circuit warms up and falls back to its actual rendered minimum once/loop.
    neon=(.5-.5*math.cos(angle))*(.94+.04*math.cos(7*angle)+.02*math.cos(23*angle))
    tint=np.array([.94+.06*math.cos(angle),.95+.05*math.cos(angle+1.7),1.0],np.float32)
    light=bases['neon']*(neon*tint)
    chase=(.5+.5*np.cos(TAU*(CHASE*8-t*2)))**10
    light+=bases['billboard']*chase[:,:,None]
    projector=np.array([np.clip(.49+.29*math.cos(angle*(11+2*j)+j)+.16*math.cos(angle*3+j*.7)+.06*math.cos(angle*23),0,1) for j in range(5)],np.float32)
    light+=bases['projector']*projector[NEAREST,None]
    # Stable positive reflected-light image, warped by two periodic wave trains.
    displacement=(2.6*np.sin(X*.033+angle*2)+1.1*np.sin(Y*.065-angle*3))*STREET
    sy=np.clip(Y+displacement,0,H-1);iy=sy.astype(np.int32);fy=(sy-iy)[:,:,None]
    ix=X.astype(np.int32)
    reflection=bases['reflections'][iy,ix]*(1-fy)+bases['reflections'][np.minimum(iy+1,H-1),ix]*fy
    light+=reflection*(.5-.5*math.cos(angle))
    emission=np.zeros((H,W,3),np.float32)
    y=(RAIN['y']+t*(H+60)*RAIN['speed'])%(H+60)-30
    x=(RAIN['x']+y*.12+15*np.sin(angle+RAIN['phase']))%(W+40)-20
    samples=np.linspace(0,1,18)
    rx=(x[:,None]+samples*RAIN['length'][:,None]*.16).ravel()
    ry=(y[:,None]+samples*RAIN['length'][:,None]).ravel()
    strength=(RAIN['strength'][:,None]*(.3+.7*np.sin(samples*math.pi))).ravel()
    add_points(emission,rx,ry,[.53,.69,.88],strength,.62)
    emission*=OUTSIDE[:,:,None]
    light+=emission
    splashes=np.zeros_like(emission)
    life=(t*RAIN['sf']+RAIN['sp'])%1
    active=life<.30
    for i in np.flatnonzero(active):
        age=life[i]/.30;u=RAIN['su'][i];v=RAIN['sv'][i];r=RAIN['sr'][i]*(.12+.88*age)
        theta=np.linspace(0,TAU,42,endpoint=False)
        px,py=project(u+np.cos(theta)*r,v+np.sin(theta)*r,.15)
        add_points(splashes,px,py,[.60,.72,.84],np.full(theta.shape,24*(1-age)**1.3),.55)
        if age<.28:
            x0,y0=project(u,v);a=age/.28
            for sign in [-1,1]:
                add_points(splashes,[x0+sign*2*a],[y0-4*math.sin(a*math.pi)],[.65,.76,.92],[36*(1-a)],.57)
    splashes*=STREET[:,:,None];light+=splashes
    # A restrained off-screen vehicle headlight sweep, no car baked into art.
    head_u=-8+30*t
    fade=math.sin(math.pi*t)**4
    head=np.exp(-((U-head_u)/1.35)**2-((V-11.5)/.65)**2)*fade*STREET*13
    light+=head[:,:,None]*np.array([1,.84,.59],np.float32)
    # Tiny deterministic dither only where light exists. It also wraps exactly.
    xx=X.astype(np.uint32);yy=Y.astype(np.uint32)
    h=(xx*1664525+yy*1013904223+np.uint32(((index%N)*2654435761)&0xffffffff))
    h=(h^(h>>13))*1274126177
    dither=(((h>>29).astype(np.float32)-3.5)/10)[:,:,None]
    light=np.maximum(0,light+dither*(light.max(axis=2,keepdims=True)>.5))
    # Two-pixel dark collar prevents VP9 4:2:0 chroma/DCT ringing from the
    # bright bezel crossing the exact DOM billboard rectangle after decoding.
    light[38:366,1294:1874]=0
    return np.clip(np.rint(light),0,255).astype(np.uint8)

def rgba(rgb):return np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)])

def main():
    started=time.perf_counter();FRAMES.mkdir(exist_ok=True)
    assert (QA/'loop_basis.json').exists()
    m=json.loads((QA/'manifest_stills_ready.json').read_text())
    inputs=list(BASIS.glob('*.png'))+list((QA/'minimum_sprites').glob('*.png'));predecode(inputs)
    # Recut every sprite from minimum-light renders, using unchanged geometry AOVs.
    backup=QA/'stills_sprites';backup.mkdir(exist_ok=True)
    for e in m['occluders']:
        for suffix in ['', '@2x']:
            name=e['file'][:-4]+suffix+'.png'
            if not (backup/name).exists():shutil.copyfile(OUT/name,backup/name)
            a=read(QA/'minimum_sprites'/name);a[a[:,:,3]==0,:3]=0;write(OUT/name,a)
    layers.OUT=OUT;layers.QA=QA;m['render_layers']=layers.depth_slices(m['occluders'])
    base_images={}
    for scale,suffix in [(1,''),(2,'@2x')]:
        raw=read(BASIS/('minimum'+suffix+'.png'));a=assemble(raw,m['render_layers'],scale)
        glow=layers.glow_for(a,scale);bg=grain(raw)
        bg[:,:,:3]=np.rint(255-(255-bg[:,:,:3].astype(np.float32))*(255-glow[:,:,:3].astype(np.float32))/255).astype(np.uint8)
        write(OUT/('base'+suffix+'.png'),bg);write(OUT/('bg'+suffix+'.png'),bg);base_images[scale]=bg
        write(QA/('minimum_full'+suffix+'.png'),assemble(bg,m['render_layers'],scale))
    raw=read(BASIS/'minimum.png')[:,:,:3].astype(np.float32)
    bases={name:blur_light(np.maximum(read(BASIS/(name+'.png'))[:,:,:3].astype(np.float32)-raw,0)) for name in ['neon','billboard','projector','reflections']}
    # Restrict negligible denoising residuals to zero; bases never shimmer.
    for a in bases.values():a[a.max(axis=2)<1.5]=0;a[40:364,1296:1872]=0
    first=frame(0,bases);endpoint=frame(N,bases);assert np.array_equal(first,endpoint)
    changes=[];previous=None;hashes=[]
    previews={0,30,60,90,119}
    for i in range(N):
        a=frame(i,bases)
        # Explicit reference-minus-base contract, including saturated pixels.
        animated=np.minimum(base_images[1][:,:,:3].astype(np.uint16)+a,255).astype(np.uint8)
        additive=(animated.astype(np.int16)-base_images[1][:,:,:3]).clip(0,255).astype(np.uint8)
        write(FRAMES/('f'+str(i).zfill(3)+'.png'),rgba(additive))
        hashes.append(hashlib.sha256(additive.tobytes()).hexdigest())
        if previous is not None:changes.append(float(np.abs(additive.astype(np.int16)-previous.astype(np.int16)).mean()))
        previous=additive
        if i==0:first=additive.copy()
        if i in previews:
            composed=assemble(rgba(animated),m['render_layers']);write(QA/('loop_f'+str(i).zfill(3)+'.png'),composed)
            if i==60:
                write(OUT/'full.png',composed)
                doubled=upscale2(additive)
                full2=base_images[2].copy();full2[:,:,:3]=np.minimum(full2[:,:,:3].astype(np.uint16)+doubled,255).astype(np.uint8)
                write(OUT/'full@2x.png',assemble(full2,m['render_layers'],2))
        if i%24==0:print('LOOP_FRAME',i,'/',N,flush=True)
    seam=float(np.abs(previous.astype(np.int16)-first.astype(np.int16)).mean())
    endpoint_bg=np.minimum(base_images[1][:,:,:3].astype(np.uint16)+endpoint,255).astype(np.uint8)
    endpoint_add=(endpoint_bg.astype(np.int16)-base_images[1][:,:,:3]).clip(0,255).astype(np.uint8)
    assert np.array_equal(first,endpoint_add)
    assert seam<max(changes)*1.35,(seam,max(changes))
    report={'passed':True,'fps':FPS,'frames':N,'seconds':N/FPS,'period_endpoint_max_channel_error':0,
        'last_to_first_mean_abs_error_8bit':seam,'adjacent_mean_abs_error_8bit':float(np.mean(changes)),
        'adjacent_max_mean_abs_error_8bit':max(changes),'frame_hashes':hashes,
        'composition_seconds':round(time.perf_counter()-started,3),
        'additive_contract':'RGB = clamp(animated_background - base, 0, 255) in sRGB display space. Opaque black background.',
        'independent_denoised_frames':False}
    (QA/'loop_validation.json').write_text(json.dumps(report,indent=2))
    m.update(base='base.png',bg='bg.png',glow=None,light_loop='light_loop.webm',loop_seconds=N/FPS,fps=FPS,
        loop_frames=N,loop_blend_mode='plus-lighter',loop_size=[1920,1080],loop_codec='VP9',status='loop_pending_encode',
        full_reference_frame=60,full_composition='base + light_loop frame 60 with plus-lighter, then render_layers source-over in z_index order',
        loop_static_prop_lights=json.loads((QA/'loop_basis.json').read_text())['static_prop_lights'],
        loop_note='The video sits below walkers and sprites. Sprite lights stay static at their minimum-scene render values. Rain is masked off the indoor building, blank marquees and billboard aperture. Thin glass may reveal video behind it. Use full.png as a flattened still fallback, without redrawing sprites.',
        loop_seam_validation='qa2/loop_validation.json',
        notes=[n for n in m['notes'] if 'Loop will be added' not in n])
    (QA/'manifest_loop_pending.json').write_text(json.dumps(m,indent=2))
    print('LOOP_COMPOSITION_QA',json.dumps({k:v for k,v in report.items() if k!='frame_hashes'}),flush=True)

if __name__=='__main__':main()
