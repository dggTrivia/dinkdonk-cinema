"""Straight-alpha doors, janitor, umbrellas and the seamless shelter drip."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from pngio import read,write,predecode
from package_cat_pass5 import down_rgba,sheets
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa6';OUT=ROOT/'out6'

def shadow(a,anchor):
    h,w=a.shape[:2];yy,xx=np.indices((h,w),dtype=np.float32)
    dx=(xx+.5)/2-anchor[0];dy=(yy+.5)/2-anchor[1];u=dx/120+dy/60;v=dy/60-dx/120
    s=.27*np.exp(-2*((u/.23)**2+(v/.19)**2));s[s<.004]=0
    alpha=a[:,:,3]/255.;aa=alpha+s*(1-alpha);rgb=a[:,:,:3]*alpha[:,:,None]/np.maximum(aa[:,:,None],1e-8)
    out=np.rint(np.dstack([rgb,aa*255])).astype(np.uint8);out[out[:,:,3]==0,:3]=0;return out

def entry(file,meta,n,cols,fps,loop):
    return {'file':file+'.png','file_2x':file+'@2x.png','frames':n,'columns':cols,'rows':math.ceil(n/cols),'fps':fps,
        'frame_width':meta['frame_width'],'frame_height':meta['frame_height'],'anchor':meta['anchor'],'loop':loop,'seconds':n/fps}

def save(e,frames):
    write(OUT/e['file'],sheets([down_rgba(a) for a in frames],e['columns']));write(OUT/e['file_2x'],sheets(frames,e['columns']))

def characters(m):
    meta=json.loads((QA/'characters_metadata.json').read_text());validation=[]
    for kind in ['janitor','umbrella']:predecode(list((QA/(kind+'_raw')).rglob('*.png')))
    m['janitor']={}
    for name in ['walk_plus_u','walk_minus_u','walk_plus_v','walk_minus_v','sweep','idle']:
        n,fps=(12,12) if name.startswith('walk') else (48,16);info=meta['janitor'];frames=[]
        for i in range(n+1):frames.append(shadow(read(QA/'janitor_raw'/name/('f'+str(i).zfill(3)+'.png')),info['anchor']))
        assert np.array_equal(frames[0],frames[-1]),name
        diffs=[float(np.abs(frames[i].astype(np.int16)-frames[i-1].astype(np.int16)).mean()) for i in range(1,n+1)]
        assert diffs[-1]<=max(diffs[:-1])*1.8+.01,name
        e=entry('janitor/'+name,info,n,6 if n==12 else 8,fps,True)
        if n==12:e.update(stride_tiles=.48,direction={'walk_plus_u':'+u','walk_minus_u':'-u','walk_plus_v':'+v','walk_minus_v':'-v'}[name])
        save(e,frames[:-1]);m['janitor'][name]=e
        validation.append({'kind':'janitor','name':name,'endpoint_error':0,'seam_mae':diffs[-1],'adjacent_max_mae':max(diffs),'unique_frames':len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames[:-1]})})
    m['janitor_contract']={'character':'Original cap, short-sleeve work shirt, stitched blue overalls, work boots, straw broom, metal pail and wristwatch.',
        'placement':'Top-left = P(u,v)-anchor. Sort at 1000+round((u+v)*100), just like cat. Contact shadow included.',
        'frames':'Straight RGBA; row-major; floor(elapsedSeconds*fps)%frames. All coordinates are 1x; @2x doubles source cells.',
        'walk':'12 frames at 12fps; translate 0.48 tiles per cycle (0.48 tiles/second). Stance feet counter-travel at that speed.',
        'walk_mapping':{'+u':'walk_plus_u','-u':'walk_minus_u','+v':'walk_plus_v','-v':'walk_minus_v'},
        'sweep':'Three-second repeating sweep; pail rests next to janitor.',
        'idle':'Three-second breathing/leaning loop with a wristwatch check; pail rests next to janitor.'}
    m['umbrella']={'colors':['red','blue','yellow','black'],'open':{},'fold':{}}
    for color in m['umbrella']['colors']:
        info=meta['umbrella'];frames=[read(QA/'umbrella_raw'/color/('f'+str(i).zfill(3)+'.png')) for i in range(6)]
        for a in frames:a[a[:,:,3]==0,:3]=0
        name='umbrella/'+color+'_open';write(OUT/(name+'.png'),down_rgba(frames[0]));write(OUT/(name+'@2x.png'),frames[0])
        m['umbrella']['open'][color]={'file':name+'.png','file_2x':name+'@2x.png','anchor':info['anchor'],'w':info['frame_width'],'h':info['frame_height']}
        e=entry('umbrella/'+color+'_fold',info,6,6,12,False);save(e,frames);m['umbrella']['fold'][color]=e
        validation.append({'kind':'umbrella','name':color,'open_matches_fold_start':True,'fold_frames':6})
    m['umbrella_contract']={'anchor':'The curved handle grip, not the umbrella centre. For a 50px emote, suggested grip=P(u,v,40)+[10,0]; top-left=grip-anchor.',
        'placement':'Keep with its owner, immediately above the owner in depth order; never use a global foreground layer.',
        'fold':'Six frames at 12fps, 0.5s one-shot. Clamp at frame 5, then remove or hold the folded umbrella. Frame 0 equals open.',
        'resolution':'Straight RGBA, shaded 3D fabric and ribs. 88x80 logical cells; @2x doubles all source dimensions.'}
    (QA/'characters_validation.json').write_text(json.dumps({'passed':True,'checks':validation,'render_scale':2},indent=2))

def doors(m):
    meta=json.loads((QA/'doors_metadata.json').read_text());predecode(list((QA/'doors_raw').rglob('*.png')))
    bg=read(OUT/'lit_bg@2x.png')[:,:,:3].astype(np.float32);m['door_anims']=[];checks=[]
    for info in meta['doors']:
        x,y,w,h=[info[k]*2 for k in ['x','y','frame_width','frame_height']];base=bg[y:y+h,x:x+w]
        raw0=read(QA/'doors_raw'/str(info['door'])/'f000.png')[:,:,:3].astype(np.float32)
        yy,xx=np.indices((h,w),dtype=np.float32);feather=np.clip((np.minimum.reduce([xx,yy,w-1-xx,h-1-yy])-3)/12,0,1)
        # Limit replacements to the doorway and its floor. Movie posters/titles
        # are supplied dynamically by the page and must never be painted over.
        gx=(xx+x+.5)/2;gy=(yy+y+.5)/2
        floor_u=((gx-900)/60+(gy-350)/30)/2;floor_v=((gy-350)/30-(gx-900)/60)/2
        floor=(floor_u if info['wall']=='u0' else floor_v)>=0
        at=info['at'];half=.4 if info['door']=='wc' else .55;height=104 if info['door']=='wc' else 114
        def pt(t,z):return (900-60*t,350+30*t-z) if info['wall']=='u0' else (900+60*t,350+30*t-z)
        poly=[pt(at-half-.03,-1),pt(at+half+.03,-1),pt(at+half+.03,height+2),pt(at-half-.03,height+2)]
        cross=[(c[0]-a[0])*(gy-a[1])-(c[1]-a[1])*(gx-a[0]) for a,c in zip(poly,poly[1:]+poly[:1])]
        opening=np.logical_and.reduce([q>=0 for q in cross])|np.logical_and.reduce([q<=0 for q in cross])
        distance=np.minimum.reduce([np.abs(q)/math.hypot(c[0]-a[0],c[1]-a[1]) for q,(a,c) in zip(cross,zip(poly,poly[1:]+poly[:1]))])
        cover=np.clip(distance/1.25,0,1)*opening
        feather*=floor|opening
        frames=[];errs=[]
        for i in range(16):
            raw=read(QA/'doors_raw'/str(info['door'])/('f'+str(i).zfill(3)+'.png'))[:,:,:3].astype(np.float32)
            delta=raw-raw0;delta[np.max(np.abs(delta),axis=2)<3]=0;delta*=feather[:,:,None]
            if i in [0,15]:delta[:]=0
            target=np.clip(base+delta,0,255)
            if i not in [0,15]:target=target*(1-cover[:,:,None])+raw*cover[:,:,None]
            delta=target-base
            # Minimum source-over coverage capable of reproducing the signed change.
            required=np.where(delta>=0,delta/np.maximum(255-base,1),-delta/np.maximum(base,1))
            alpha=np.clip(required.max(axis=2)*1.02,0,1);alpha=np.where(alpha>0,np.maximum(alpha,.12),0)
            if i not in [0,15]:alpha=np.maximum(alpha,cover)
            rgb=base+np.divide(delta,alpha[:,:,None],out=np.zeros_like(delta),where=alpha[:,:,None]>0)
            out=np.rint(np.dstack([np.clip(rgb,0,255),alpha*255])).astype(np.uint8);out[out[:,:,3]==0,:3]=0
            recon=out[:,:,:3].astype(np.float32)*out[:,:,3:4]/255.+base*(1-out[:,:,3:4]/255.)
            errs.append(float(np.abs(recon-target).max()));frames.append(out)
        e={k:v for k,v in info.items() if k not in ['wall','at']};e.update(file='doors/door_'+str(info['door'])+'.png',file_2x='doors/door_'+str(info['door'])+'@2x.png')
        save(e,frames);m['door_anims'].append(e)
        checks.append({'door':info['door'],'first_last_transparent':True,'frames':16,'poster_title_planes_excluded':True,'max_source_over_rounding_error':max(errs)})
    m['door_anim_contract']={'playback':'16 frames at 18fps (0.889s), row-major, open-hold-close. Clamp at frame 15 and remove. Both endpoints transparent.',
        'composition':'Straight RGBA source-over at x,y, z_index=900, above base+ambient and below all walkers and occluders. Never plus-lighter.',
        'background':'Opaque rendered doorway core erases closed leaves and their ambient porthole glow; signed source-over floor changes add spill. Designed over this pack base+ambient or lit_bg.',
        'mask':'Doorway and floor only; neighbouring wall posters and title planes are excluded from the RGBA replacement.',
        'resolution':'frame_width/frame_height and positions are 1x; file_2x doubles cells only.',
        'doors':'Door pivots and opening positions are unchanged. Screen leaves swing inward 79 degrees; WC is a single inward leaf.'}
    (QA/'doors_validation.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2))

def drip_frames():
    w,h=52,112;yy,xx=np.indices((h*2,w*2),dtype=np.float32);xx=(xx+.5)/2;yy=(yy+.5)/2
    result=[]
    for i in range(73):
        t=(i%72)/24;a=np.zeros((h*2,w*2,3),np.float32)
        # Floor puddle, centred under the front-left roof corner (.35,9.6).
        dx=xx-25;dy=yy-91.5;puddle=np.exp(-2*((dx/12)**2+(dy/4.5)**2))
        a+=puddle[:,:,None]*np.array([3,6,8])
        for start in [0,.98,2.03]:
            age=(t-start)%3
            if age<.56:
                z=84*(1-(age/.56)**2);py=91.5-z
                g=np.exp(-((dx/.55)**2+((yy-py)/(1+age*4))**2)*2)
                a+=g[:,:,None]*np.array([82,116,130])
            ring_age=age-.56
            if 0<=ring_age<.78:
                radius=1+12*ring_age/.78;dist=np.sqrt(dx*dx+(dy*2.65)**2)
                ring=np.exp(-((dist-radius)/.65)**2)*math.sin(math.pi*ring_age/.78)**.7*(1-ring_age/.78)
                a+=ring[:,:,None]*np.array([30,56,68])
        a[:3]=0;a[-3:]=0;a[:,:3]=0;a[:,-3:]=0
        rgb=np.rint(np.clip(a,0,255)).astype(np.uint8);result.append(np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)]))
    assert np.array_equal(result[0],result[-1]);return result[:-1]

def drip(m):
    parents=[e for e in m['render_layers'] if e['name'].startswith('bus_stop_')]
    frames=drip_frames();e={'name':'shelter_drip','file':'prop_loops/shelter_drip.png','file_2x':'prop_loops/shelter_drip@2x.png',
        'x':320,'y':557,'w':52,'h':112,'z_index':max(e['z_index'] for e in parents)+1,'blend':'plus-lighter','format':'png-spritesheet',
        'fps':24,'frames':72,'loop_seconds':3,'columns':6,'rows':12,'frame_width':52,'frame_height':112,'frame_order':'row-major','parent':'bus_stop',
        'parent_slices':[e['name'] for e in parents],'roof_uvz':[.35,9.6,84],'puddle_uv':[.35,9.6]}
    save(e,frames);m['prop_loops'].append(e)
    m['shelter_drip_contract']={'placement':'One front-left roof corner at P(0.35,9.6,84)=[345,564.5]; puddle centre P(0.35,9.6)=[345,648.5].',
        'playback':'Same 72-frame, 24fps, three-second additive contract as the inherited prop loops. Frame 72 regenerated equal to frame 0.',
        'style':'Three gravity-accelerating drops per period with spreading perspective rings over a small blue-grey puddle.'}
    diffs=[float(np.abs(frames[(i+1)%72].astype(np.int16)-frames[i].astype(np.int16)).mean()) for i in range(72)]
    (QA/'drip_validation.json').write_text(json.dumps({'passed':True,'endpoint_error':0,'seam_mae':diffs[-1],'adjacent_max_mae':max(diffs),'rect':[320,557,52,112]},indent=2))

def main():
    from compose_pass6 import surface_metadata,preserve_billboard
    preserve_billboard()
    m=json.loads((QA/'manifest_stills_ready.json').read_text());surface_metadata(m);characters(m);doors(m);drip(m)
    video=json.loads((QA/'video_metadata.json').read_text());m['light_loop_bytes']=video['bytes'];m['light_loop_sha256']=video['sha256']
    m['pass6_validation']='../qa6/final_validation.json';m['validation']['pass6']='../qa6/final_validation.json';m['status']='complete'
    p=OUT/'manifest.pending.json';p.write_text(json.dumps(m,indent=2));p.replace(OUT/'manifest.json')
    print('PASS6_COMPLETE_MANIFEST',flush=True)

if __name__=='__main__':main()
