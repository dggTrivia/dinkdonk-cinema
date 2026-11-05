"""Complete layout-3 pack. Called only by explicit pipeline.py -- full.

All persistent output lives under this bundle. Intermediate EXRs have content
receipts; display assets are deterministic rebuilds of those buffers.
"""
import json,math,os,shutil,time,tarfile,hashlib,copy
from functools import lru_cache
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from common import ROOT,project,ZPP
from runtime import Renderer,WORK,atomic_json,log,sha,pixels,rgba8,png,diff,within
import package_layers as layers
from fast_pipeline import area2,position2,wet_frames,wet_phase,policy,combined,cut,crop,rect_for
from fast_pipeline import NativeRenderer as Renderer

OUT=ROOT/'out10';QA=WORK/'qa';QA.mkdir(exist_ok=True)

def filename(stem,scale=1):return stem+('@2x' if scale==2 else '')+'.png'
@lru_cache(maxsize=1)
def plan():
    p=json.loads((ROOT/'speed_plan.json').read_text());proof=json.loads((ROOT/'smoke/validation.json').read_text())
    assert p==proof['selected'],'Speed plan must come from the measured smoke result'
    assert p=={'adaptive':True,'threshold':.01,'split':False,'persistent':True},'Approved quality plan is fixed'
    assert proof['scene_sha256']==sha(ROOT/'scene.blend'),'Smoke evidence belongs to another scene'
    return p
def opts():
    p=plan();return dict(adaptive=p['adaptive'],threshold=p['threshold'],persistent=p['persistent'])
def save_manifest(m):atomic_json(OUT/'manifest.json',m)
def fingerprint():
    paths=[ROOT/'scene.blend',ROOT/'production.json',ROOT/'manifest.template.json',ROOT/'speed_plan.json']+sorted(ROOT.glob('*.py'))
    return hashlib.sha256((''.join(p.name+sha(p) for p in paths)+str(wet_frames())).encode()).hexdigest()
def initialize():
    # An existing output from a different source cannot silently be mixed in.
    ident=fingerprint();marker=OUT/'.cloud-build.json'
    if OUT.exists():
        if not marker.exists() or json.loads(marker.read_text())['fingerprint']!=ident:raise RuntimeError('out10 belongs to another build. Use a fresh bundle folder; no output was removed.')
    else:
        OUT.mkdir();atomic_json(marker,{'fingerprint':ident,'source':'packed approved Draft 13'})
    reuse=[]
    for src in (ROOT/'reuse').rglob('*'):
        if not src.is_file() or src.suffix.lower() not in ['.png','.webm']:continue
        rel=src.relative_to(ROOT/'reuse');dst=OUT/rel
        if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        reuse.append({'file':rel.as_posix(),'sha256':sha(src)})
    atomic_json(QA/'reuse_sources.json',reuse)
    log('output_initialized',source=fingerprint(),reuse_candidates=len(reuse))
    return json.loads((ROOT/'manifest.template.json').read_text())

def display_cached(r,a,path,glare=True):
    # No GPU tracing in this pass: HDR composite and approved view transform.
    r.display(a,path,glare=glare);return rgba8(path)

def loop_frame(r,tag,part,frame,rect=None,aov=False):
    if plan()['split']:
        dry,_=r.capture(tag+'_dry',part=part,split='dry',rect=rect,**opts())
        wet,_=r.capture(tag+f'_wet_{frame:03d}',part=part,split='wet',frame=frame,rect=rect,**opts())
        a=dry+wet;a[:,:,3]=np.clip(a[:,:,3],0,1)
        # Ownership must come from the complete surface, not a complementary mask.
        if aov:r.capture(tag+'_ownership',part=part,frame=0,rect=rect,aov=True,**opts())
    else:a,_=r.capture(tag+f'_{frame:03d}',part=part,frame=frame,rect=rect,aov=aov,**opts())
    return a

def ownership_tag(tag):return tag+'_ownership' if plan()['split'] else tag+'_000'

def backgrounds(r,m):
    proof=[]
    r.width=3840;r.height=2160
    for f in range(48):
        a=loop_frame(r,'background_2','background',f)
        for scale,buffer in [(2,a),(1,area2(a))]:
            folder=WORK/f'background_{scale}';folder.mkdir(exist_ok=True)
            display_cached(r,buffer,folder/f'f{f:03d}.png')
    excludes=[name for name in ['D5 periodic wet micro impacts','D3 thin steam plume','D10 stateless edge drips and impact crowns','D10 stateless gutter and AC pours'] if name in r.sc.objects]
    dry_fallback,_=r.capture('dry_fallback_2',part='background',exclude=excludes,**opts())
    endpoint,_=r.capture('endpoint_background_2',part='background',frame=48,**opts())
    reference,_=r.capture('background_2_000',part='background',frame=0,**opts())
    for scale in [1,2]:
        folder=WORK/f'background_{scale}'
        minimum=None
        for f in range(48):
            p=rgba8(folder/f'f{f:03d}.png');p[:,:,3]=255
            minimum=p.copy() if minimum is None else np.minimum(minimum,p)
        for stem in ['bg','base']:png(OUT/filename(stem,scale),minimum)
        shutil.copyfile(folder/'f000.png',OUT/filename('lit_bg',scale))
        display_cached(r,dry_fallback if scale==2 else area2(dry_fallback),OUT/filename('lit_bg_dry',scale))
        deltafolder=WORK/f'light_loop_{scale}';deltafolder.mkdir(exist_ok=True)
        for f in range(48):
            p=rgba8(folder/f'f{f:03d}.png');delta=np.maximum(p[:,:,:3].astype(np.int16)-minimum[:,:,:3],0).astype(np.uint8);png(deltafolder/f'f{f:03d}.png',delta)
        # Independent wrapped endpoint, rendered only on the explicitly requested cloud run.
        d=diff(reference if scale==2 else area2(reference),endpoint if scale==2 else area2(endpoint));noise=json.loads((ROOT/'smoke/validation.json').read_text())['quality']['noise_baseline'];assert within(d,noise),('Nonperiodic endpoint exceeds noise floor',scale,d)
        proof.append({'scale':scale,'wrapped_linear_difference':d,'noise_baseline':noise,'passed':within(d,noise)})
        log('background_cycle_complete',scale=scale,unique_frames=48,period_seconds=2)
    m.update(base='base.png',bg='bg.png',full_reference_frame=0,lit_bg_reference_frame=0,loop_size=[1920,1080],light_loop_2x_size=[3840,2160],loop_blend_mode='plus-lighter',static_glow=False,glow=None)
    m['lit_bg_composition']='Fully lit phase-0 background; draw render_layers and other foreground assets above it.'
    m['cloud_contract']['background_plate']='Per-channel cycle minimum in display space; positive delta reconstructs each rendered background exactly.'
    atomic_json(QA/'periodic_endpoints.json',proof);save_manifest(m)

def sheet(frames,path,columns=8):
    h,w=frames[0].shape[:2];rows=math.ceil(len(frames)/columns);result=np.zeros((h*rows,w*columns,4),np.uint8)
    for i,a in enumerate(frames):result[i//columns*h:(i//columns+1)*h,i%columns*w:(i%columns+1)*w]=a
    png(path,result)

# Cloud run 1 (02 Nov 2026): ~9 s/frame made 48-frame loops for every group exceed the
# 7 h / credit cap. Indoor groups see no rain and constant light, so they render one frame.
INTERIOR_STATIC={"podium","bench","arcade","standee_1","standee_2","palm","queue_front","queue_back","restroom_entry_wall","restroom_stall_1","restroom_stall_2","restroom_stall_3","restroom_stall_4","restroom_sinks","restroom_dryer","restroom_service","restroom_side_wall","restroom_closet_wall","restroom_entry_leaf","corridor_standee_1","corridor_standee_2","corridor_bench","corridor_fountain","corridor_bin","corridor_extinguisher"}

def foreground(r,m):
    prepare_foreground(r)
    parents=[];wet_names=[]
    for spec in r.meta['groups']:
        name=spec['name'];objects=[r.sc.objects[n] for n in spec['objects']];rect=r.rect(objects,8)
        if rect[2]<=0 or rect[3]<=0:raise RuntimeError('Offscreen foreground group: '+name)
        dynamic=any(o.name in r.wet for o in objects) and name not in INTERIOR_STATIC;count=48 if dynamic else 1
        entry={k:copy.deepcopy(v) for k,v in spec.items() if k!='objects'};entry.update(x=rect[0],y=rect[1],w=rect[2],h=rect[3],file=filename('occ_'+name),file_2x=filename('occ_'+name,2))
        for scale in [1,2]:
            tag=f'foreground_{name}_{scale}';folder=WORK/tag;minimum=None;alpha=None
            for f in range(count):
                p=rgba8(folder/f'f{f:03d}.png');p[p[:,:,3]==0,:3]=0
                if minimum is None:minimum=p.copy();alpha=p[:,:,3].copy()
                else:
                    # Geometry is stationary. Reflections may change RGB, but
                    # alpha must not be reduced by a cycle-minimum operation.
                    minimum[:,:,:3]=np.minimum(minimum[:,:,:3],p[:,:,:3])
            minimum[:,:,3]=alpha;png(OUT/entry['file' if scale==1 else 'file_2x'],minimum)
            posdir=QA/'positions';posdir.mkdir(exist_ok=True)
        entry['tile_clips']=layers.tile_clips(entry);parents.append(entry)
        if dynamic:wet_names.append(name)
        log('foreground_parent_complete',name=name,frames=count,native_scales=[2],derived_scales=[1])
    layers.OUT=OUT;layers.QA=QA;flat=layers.depth_slices(parents)
    for e in flat:
        e['file_2x']=e['file'][:-4]+'@2x.png'
        if e['parent']=='paste_wall':e['z_index']=99
    m['occluders']=parents;m['render_layers']=sorted(flat,key=lambda e:e['z_index'])
    # Split moving wet highlights by exactly the same AOV ownership as parents.
    # A separate additive prop for each slice retains the page's walker depth.
    for e in parents:
        if e['name'] not in wet_names:continue
        for piece in e['depth_slices']:
            n='wet_'+piece['name'];record=dict(name=n,file='prop_loops/'+n+'.png',file_2x='prop_loops/'+n+'@2x.png',x=piece['x'],y=piece['y'],w=piece['w'],h=piece['h'],z_index=piece['z_index']+1,blend='plus-lighter',format='png-spritesheet',fps=24,frames=48,loop_seconds=2,columns=8,rows=6,frame_width=piece['w'],frame_height=piece['h'],frame_order='row-major',parent=e['name'],parent_slices=[piece['name']])
            any_light=False
            for scale,key in [(1,'file'),(2,'file_2x')]:
                parent=rgba8(OUT/e[key]);mask=rgba8(OUT/piece[key])[:,:,3];x=(piece['x']-e['x'])*scale;y=(piece['y']-e['y'])*scale;w=piece['w']*scale;h=piece['h']*scale
                base=parent[y:y+h,x:x+w];frames=[]
                for f in range(48):
                    current=rgba8(WORK/f"foreground_{e['name']}_{scale}"/f'f{f:03d}.png')[y:y+h,x:x+w]
                    rgb=np.maximum(current[:,:,:3].astype(np.int16)-base[:,:,:3],0).astype(np.float32)*(mask[:,:,None]/255)
                    rgb=np.rint(rgb).astype(np.uint8);any_light|=bool(np.any(rgb));frames.append(np.dstack([rgb,np.full((h,w),255,np.uint8)]))
                sheet(frames,OUT/record[key])
            if any_light:m['prop_loops'].append(record)
        log('foreground_animation_sliced',name=e['name'])
    m['depth_slices_note']='Disjoint Cycles world-position AOV masks; render_layers reconstruct each parent exactly. 1x derives from linear 2x pixels with coverage-weighted positions. Wet highlights share the same ownership and depth.'
    atomic_json(QA/'foreground_metadata.json',parents);save_manifest(m)

def prepare_foreground(r):
    proof=policy();fallback=set(proof['fallback_groups']);r.width=3840;r.height=2160
    specs={s['name']:s for s in r.meta['groups']};rects={n:rect_for(r,s) for n,s in specs.items()}
    dynamic={n for n,s in specs.items() if n not in INTERIOR_STATIC and any(o in r.wet for o in s['objects'])}
    posdir=QA/'positions';posdir.mkdir(exist_ok=True)
    def store_frame(name,f,a,uv):
        for scale,p in [(2,a),(1,area2(a))]:
            folder=WORK/f'foreground_{name}_{scale}';folder.mkdir(exist_ok=True)
            display_cached(r,p,folder/f'f{f:03d}.png',glare=False)
            if wet_frames()==24 and name in dynamic:shutil.copyfile(folder/f'f{f:03d}.png',folder/f'f{f+1:03d}.png')
            if f==0:np.savez_compressed(posdir/(name+('@2x' if scale==2 else '')+'.npz'),uv=uv if scale==2 else position2(uv,a[:,:,3]))
    for f in range(0,48,48//wet_frames()):
        names=[n for n in specs if n not in fallback and (f==0 or n in dynamic)]
        if not names:continue
        a,maskpath,uv=combined(r,f'combined_fg_2_{f:03d}',f)
        with np.load(maskpath) as masks:
            for name in names:store_frame(name,f,cut(crop(a,rects[name],r.width),crop(masks[name],rects[name],r.width)),crop(uv,rects[name],r.width))
    # One visibility change per exceptional group, then all of its phases.
    for name in sorted(fallback):
        for f in (range(0,48,48//wet_frames()) if name in dynamic else [0]):
            tag=f'foreground_{name}_2_{f:03d}'
            a,_=r.capture(tag,part=name,frame=f,rect=rects[name],aov=f==0,**opts())
            uv=np.load(WORK/'positions'/f'foreground_{name}_2_000.npz')['uv']
            store_frame(name,f,a,uv)

def weather(r,m):
    r.width=3840;r.height=2160;folder=WORK/'rain_fg_1';folder.mkdir(exist_ok=True);masks=[]
    for f in range(48):
        a,_=r.capture(f'weather_{f:03d}',part='weather',rain=True,frame=f,**opts())
        p=display_cached(r,area2(a),WORK/'weather_display.png',glare=False);rgb=np.rint(p[:,:,:3]*(p[:,:,3:4]/255)).astype(np.uint8);png(folder/f'f{f:03d}.png',rgb)
    m['rain_fg']=dict(file='rain_fg.webm',size=[1920,1080],fps=24,frames=144,seconds=6,blend='plus-lighter',z_index=70001,holdout='All current scene geometry, including shelter and interior foreground.')
    log('weather_cycle_complete',unique_frames=48);save_manifest(m)

def matrix(a):return Matrix([a[i:i+4] for i in range(0,16,4)])
def pose(obs,amount):
    for o in obs:
        p=Vector(o['anim_pivot']);o.matrix_world=Matrix.Translation(p)@Matrix.Rotation(math.radians(o['anim_angle'])*amount,4,'Z')@Matrix.Translation(-p)@matrix(list(o['closed_matrix']))
    bpy.context.view_layer.update()
def polygon_mask(points,w,h):
    yy,xx=np.indices((h,w),dtype=np.float32);xx+=.5;yy+=.5;inside=np.zeros((h,w),bool)
    for i,(x0,y0) in enumerate(points):
        x1,y1=points[(i+1)%len(points)];inside^=((y0>yy)!=(y1>yy))&(xx<(x1-x0)*(yy-y0)/(y1-y0+1e-30)+x0)
    return inside

def doors_wc(r,m):
    records=[]
    for info in r.meta['animations']:
        obs=[o for o in r.sc.objects if o.get('anim_id')==info['id']];assert obs
        rects=[]
        for f in np.linspace(0,1,6):pose(obs,float(f));rects.append(r.rect(obs,16))
        pose(obs,0);pts=[project(*p) for p in info['opening_world']];rects.append([math.floor(min(p[0] for p in pts))-5,math.floor(min(p[1] for p in pts))-5,math.ceil(max(p[0] for p in pts)-min(p[0] for p in pts))+10,math.ceil(max(p[1] for p in pts)-min(p[1] for p in pts))+10])
        x=max(0,min(q[0] for q in rects));y=max(0,min(q[1] for q in rects));right=min(1920,max(q[0]+q[2] for q in rects));bottom=min(1080,max(q[1]+q[3] for q in rects));rect=[x,y,right-x,bottom-y]
        e=dict(info,x=x,y=y,w=rect[2],h=rect[3],frame_width=rect[2],frame_height=rect[3],frames=16,columns=4,rows=4,fps=18,seconds=16/18,loop=False,alpha='straight',blend='source-over',frame_order='row-major',file='doors/'+info['id']+'.png',file_2x='doors/'+info['id']+'@2x.png')
        r.width=3840;r.height=2160;linear=[]
        for f in range(6):
            pose(obs,.5-.5*math.cos(math.pi*f/5))
            a,_=r.capture(f"door_{info['id']}_2_{f}",part='all',rect=rect,state={'door':info['id'],'pose':f},**opts());linear.append(a)
        for scale,key in [(1,'file'),(2,'file_2x')]:
            frames=[display_cached(r,a if scale==2 else area2(a),WORK/'door_display.png',glare=False) for a in linear]
            # Opaque opening removes closed leaves; outside it retain only actual
            # moving-leaf / cast-shadow changes, without a rectangular patch.
            core=polygon_mask([((px-x)*scale,(py-y)*scale) for px,py in pts],rect[2]*scale,rect[3]*scale)
            changed=np.max(np.stack([np.abs(p[:,:,:3].astype(np.int16)-frames[0][:,:,:3]) for p in frames]),axis=(0,3))>6
            mask=core|changed
            for p in frames:p[:,:,3]=mask.astype(np.uint8)*255;p[~mask]=0
            sheet([frames[min(i,15-i,5)] for i in range(16)],OUT/e[key],4)
        pose(obs,0);records.append(e);log('door_complete',id=info['id'])
    m['door_anims']=[e for e in records if e['id'].startswith('screen_')]
    m['restroom']['door_anim']=next(e for e in records if e['id']=='restroom_entry')
    for i,stall in enumerate(m['restroom']['stalls'],1):stall['door_anim']=next(e for e in records if e['id']=='stall_'+str(i))
    obs=[o for o in r.sc.objects if o.get('cloud_group')=='wc_dynamic'];rect=r.rect(obs,5);labels=[o for o in obs if o.type=='FONT'];ma=bpy.data.materials['Cloud independent WC state'];p=ma.node_tree.nodes.get('Principled BSDF');states={}
    for state,text,color in [('vacant','VACANT',(.1,1,.25)),('occupied','OCCUPIED',(1,.035,.025))]:
        for o in labels:o.data.body=text;o.data.size=.058 if state=='vacant' else .0435
        p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=2
        e=dict(file='wc_'+state+'.png',file_2x='wc_'+state+'@2x.png',x=rect[0],y=rect[1],w=rect[2],h=rect[3],z_index=1550,alpha='straight',blend='source-over')
        parent=next(e for e in m['occluders'] if e['name']=='restroom_entry_wall');e['z_index']=max(q['z_index'] for q in parent['depth_slices'])+1
        r.width=3840;r.height=2160;a,_=r.capture(f'wc_{state}_2',part='wc_dynamic',rect=rect,state={'wc':state},**opts())
        for scale,key in [(1,'file'),(2,'file_2x')]:
            display_cached(r,a if scale==2 else area2(a),OUT/e[key],glare=False)
        states[state]=e
    m['wc_indicator']=states;save_manifest(m);log('wc_states_complete')

def full_stills_ads(r,m):
    # Rebuild a deterministic still using exactly the shipped consumer layers.
    for scale in [1,2]:
        a=rgba8(OUT/filename('lit_bg',scale));a[:,:,3]=255
        stack=[dict(e,cloud_kind='parent') for e in m['render_layers']]+[dict(e,cloud_kind='wet') for e in m['prop_loops'] if e['name'].startswith('wet_')]
        for e in sorted(stack,key=lambda e:e['z_index']):
            p=rgba8(OUT/e['file' if scale==1 else 'file_2x'])[:e['h']*scale,:e['w']*scale];x=e['x']*scale;y=e['y']*scale
            if e['cloud_kind']=='parent':layers.over(a,p,x,y)
            else:
                t=a[y:y+p.shape[0],x:x+p.shape[1],:3];t[:]=np.minimum(t.astype(np.uint16)+p[:,:,:3],255).astype(np.uint8)
        wc=m['wc_indicator']['vacant'];layers.over(a,rgba8(OUT/wc['file' if scale==1 else 'file_2x']),wc['x']*scale,wc['y']*scale)
        png(OUT/filename('full',scale),a)
    # Default art is baked. The overlay keeps the native rendered frame over a
    # replacement ad and leaves the perspective-mapped interior transparent.
    for ad in m['ad_surfaces']:
        pts=ad['quad_px'];x=max(0,math.floor(min(p[0] for p in pts))-3);y=max(0,math.floor(min(p[1] for p in pts))-3);right=min(1920,math.ceil(max(p[0] for p in pts))+3);bottom=min(1080,math.ceil(max(p[1] for p in pts))+3)
        overlay=dict(file='ads/'+ad['name']+'.png',file_2x='ads/'+ad['name']+'@2x.png',x=x,y=y,w=right-x,h=bottom-y,alpha='straight',blend='source-over')
        for scale,key in [(1,'file'),(2,'file_2x')]:
            a=rgba8(OUT/filename('full',scale))[y*scale:bottom*scale,x*scale:right*scale].copy();hole=polygon_mask([((px-x)*scale,(py-y)*scale) for px,py in pts],a.shape[1],a.shape[0]);a[hole]=0;png(OUT/overlay[key],a)
        ad['overlay']=overlay
    # Falling rain remains separate from the dry fallback background.
    rain=rgba8(WORK/'rain_fg_1/f000.png');a=rgba8(OUT/'full.png');a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+rain[:,:,:3],255).astype(np.uint8);png(OUT/'full.png',a)
    # Full 2x still uses the specified 1080p rain_fg presentation contract.
    rain2=np.repeat(np.repeat(rain[:,:,:3],2,axis=0),2,axis=1);a=rgba8(OUT/'full@2x.png');a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+rain2,255).astype(np.uint8);png(OUT/'full@2x.png',a)
    m['full_composition']='Native background phase 0, depth-sorted foreground and wet highlights, vacant WC, then 1080p rain_fg. No static glow overlay.'
    save_manifest(m);log('full_stills_and_ad_overlays_complete')

def full():
    if not (ROOT/'speed_plan.json').exists():raise RuntimeError('Missing measured speed plan; run smoke first.')
    policy();start=time.perf_counter();m=initialize();r=Renderer(3840,2160)
    from validation import preflight
    preflight(r)
    backgrounds(r,m);foreground(r,m);weather(r,m);doors_wc(r,m);full_stills_ads(r,m)
    from vehicles import rebuild_bus
    rebuild_bus(m,OUT,QA)
    from video import encode_and_validate
    videos={}
    for name,scale in [('light_loop',1),('light_loop_2x',2),('rain_fg',1)]:
        folder=WORK/(f'light_loop_{scale}' if name.startswith('light_loop') else 'rain_fg_1');videos[name]=encode_and_validate(name,folder,OUT,scale)
    atomic_json(QA/'videos.json',videos);m['status']='validation_pending';save_manifest(m)
    report=validate_only();m['status']='complete';m['validation']='validation.json';m['notes']='NOTES-PASS10.md';save_manifest(m)
    (OUT/'NOTES-PASS10.md').write_text('''# Pass 10 / layout 3

Approved Draft 13 scene: three screens with padded doors, restroom entrance/four animated stalls and reachable routes, rope queue, current LEDs/posters/WC states, WCAT/EatFresh boards, shelter seats and route 05 d.gg transit. Approved memes, neon, posters, alley and cafe remain in-world. Bus bodies include both approved boxing/courier artworks within their existing replacement-ad panels, plus 05 DINK DONK / d.gg TRANSIT / DGG 05 branding.

Draft 10 wet layers, standing water, physical drips/crowns/pours, curb flow and hidden reflection catchers are retained. GN rain emitter motion blur is disabled consistently to keep changing topology sharp. Draft 11 dark-night lighting, Draft 12 muted 44 W restroom, Draft 13 dim amber marquee chase and 28/24/28 W reflector floods are retained.

Background/light and rain loops keep 48 unique ray-traced frames, repeated three times in each six-second VP9 loop. Foreground wet loops default to 24 unique frames (ROXY_WET_FRAMES unset): even phases are doubled into the same 48-slot, 8x6 sheet. ROXY_WET_FRAMES=48 overrides this to render every phase. The physical DINK DONK circuits alternate every six output slots and marquee groups keep their two-second period. Persistent Data, adaptive 256/64/.01, OptiX denoising and approved HDR glare remain. No static/wet split. All new images render only on the 4K camera grid; 1080p derives by linear 2x2 area reduction. Validated groups use combined Cryptomatte cuts; groups exceeding the measured colour or alpha noise baseline keep isolated captures, ordered by pass. See bundled smoke/fast-validation.json for every group and limitation.

Reused assets retain out9 names and contracts. All foreground parents and position-AOV depth slices are rebuilt; wet/glass sheets share slice ownership. Bus branding, artwork and body slices are rebuilt; compatible road-light variants and other vehicles are reused. The green aperture was retired in out9; layout 3 uses ad quads.
''',encoding='utf-8')
    finish_archive(m,OUT,ROOT/'out10.tar.gz')
    log('pack_complete',seconds=time.perf_counter()-start,archive='out10.tar.gz')

def finish_archive(m,out,target):
    """Shared production/smoke tail: cleanup, checksums, tar and read-back."""
    out=Path(out).resolve();target=Path(target).resolve()
    assert out.is_relative_to(ROOT.resolve()) and target.is_relative_to(ROOT.resolve())
    # Remove unreferenced reuse candidates (only inside this build-owned output).
    refs=referenced_files(m)|{'manifest.json','validation.json','NOTES-PASS10.md','.cloud-build.json'}
    refs|={p[:-4]+'@2x.png' for p in list(refs) if p.endswith('.png') and (out/(p[:-4]+'@2x.png')).exists()}
    for p in out.rglob('*'):
        if p.is_file() and p.relative_to(out).as_posix() not in refs:p.unlink()
    inventory=[{'file':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]
    atomic_json(out/'checksums.json',inventory);temp=target.with_suffix(target.suffix+'.partial')
    with tarfile.open(temp,'w:gz',compresslevel=3) as archive:archive.add(out,arcname='out10')
    with tarfile.open(temp,'r:gz') as archive:
        expected={e['file']:e['sha256'] for e in inventory};expected['checksums.json']=sha(out/'checksums.json')
        files=[p for p in archive.getmembers() if p.isfile()]
        assert {p.name for p in files}=={'out10/'+s for s in expected}
        for member in files:assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==expected[member.name[6:]]
    os.replace(temp,target);log('archive_verified',archive=target.name,bytes=target.stat().st_size,sha256=sha(target))
    return dict(passed=True,archive=target.name,sha256=sha(target),files=len(inventory)+1,member_hashes_verified=True)

def referenced_files(value):
    found=set()
    if isinstance(value,dict):
        for v in value.values():found|=referenced_files(v)
    elif isinstance(value,list):
        for v in value:found|=referenced_files(v)
    elif isinstance(value,str) and value.lower().endswith(('.png','.webm','.json','.md')) and '\n' not in value and ' ' not in value:found.add(value)
    return found

def validate_only():
    from validation import validate
    m=json.loads((OUT/'manifest.json').read_text());report=validate(m,OUT,QA);atomic_json(OUT/'validation.json',report)
    if not report['passed']:raise RuntimeError('Production validation failed: '+json.dumps(report['failures']))
    log('validation_passed',checks=report['checks']);return report
