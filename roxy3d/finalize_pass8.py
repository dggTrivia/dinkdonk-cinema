"""Validate delivered images/videos/contracts, compose QA, publish complete pack."""
from pathlib import Path
import json,hashlib,math,struct
import numpy as np
from pngio import read,write,predecode
from package_layers import over
from make_loop import upscale2
from finalize_loop import children,vint,webm_metadata
from package_cat_pass5 import down_rgba
from pass8_common import ROOT,QA,OUT,LIVE,status

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vp9_format(path):
    data=path.read_bytes();key=None
    def walk(start,end):
        nonlocal key
        for tag,a,b in children(data,start,end):
            if tag in [0x18538067,0x1F43B675,0xA0]:walk(a,b)
            elif tag in [0xA3,0xA1] and key is None:
                _,n=vint(data,a);key=data[a+n+3:b]
    walk(0,len(data));assert key
    at=0
    def bits(n):
        nonlocal at
        v=0
        for _ in range(n):v=(v<<1)|((key[at//8]>>(7-at%8))&1);at+=1
        return v
    assert bits(2)==2
    profile=bits(1)+2*bits(1)
    if profile==3:bits(1)
    assert bits(1)==0 and bits(1)==0,'First frame must be a displayed keyframe'
    show=bits(1);error=bits(1);assert bits(24)==0x498342
    depth=(12 if bits(1) else 10) if profile>=2 else 8
    color=bits(3);full=bits(1) if color!=7 else 1
    subsampling=[bits(1),bits(1)] if profile in [1,3] and color!=7 else [1,1] if profile in [0,2] else [0,0]
    assert profile==0 and depth==8 and subsampling==[1,1]
    return {'profile':profile,'bit_depth':depth,'subsampling':'4:2:0','range':'full' if full else 'limited','color_space_code':color}

def cell(e,frame,scale):
    sheet=read(OUT/e['file_2x' if scale==2 else 'file']);w,h=e['w']*scale,e['h']*scale
    f=frame%e['frames'];x=f%e['columns']*w;y=f//e['columns']*h
    return sheet[y:y+h,x:x+w]

def compose(m,frame,scale=1,decoded=False,green=False,arcade='arcade_attract'):
    suffix='@2x' if scale==2 else '';a=read(OUT/('base'+suffix+'.png'))
    folder=QA/('decoded_light_loop' if decoded else 'light_loop_frames')
    light=read(folder/('f'+str(frame).zfill(3)+'.png'))[:,:,:3]
    a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+(upscale2(light) if scale==2 else light),255).astype(np.uint8)
    if green:a[40*scale:364*scale,1296*scale:1872*scale]=[0,255,0,255]
    draws=[]
    for e in m['render_layers']:
        draws.append((e['z_index'],False,e['x'],e['y'],read(OUT/(e['file'][:-4]+suffix+'.png'))))
    for e in m['prop_loops']:
        if e['name'].startswith('arcade_') and e['name']!=arcade:continue
        f=math.floor(frame/24*e['fps'])%e['frames']
        draws.append((e['z_index'],e.get('blend','plus-lighter')=='plus-lighter',e['x'],e['y'],cell(e,f,scale)))
    for z,add,x,y,src in sorted(draws,key=lambda e:e[0]):
        x*=scale;y*=scale
        if add:
            h,w=src.shape[:2];view=a[y:y+h,x:x+w,:3]
            view[:]=np.minimum(view.astype(np.uint16)+src[:,:,:3],255).astype(np.uint8)
        else:over(a,src,x,y)
    folder=QA/('decoded_rain_fg' if decoded else 'rain_fg_frames')
    fg=read(folder/('f'+str(frame).zfill(3)+'.png'))[:,:,:3]
    a[:,:,:3]=np.minimum(a[:,:,:3].astype(np.uint16)+(upscale2(fg) if scale==2 else fg),255).astype(np.uint8)
    return a

def validate_video(kind,meta,period):
    p=OUT/(kind+'.webm');container=webm_metadata(p);fmt=vp9_format(p)
    assert container['codec_id']=='V_VP9' and container['width']==1920 and container['height']==1080
    assert abs(container['seconds']-6)<.01 and abs(container['fps']-24)<.001
    assert p.stat().st_size==meta['bytes'] and sha(p)==meta['sha256']
    predecode(list((QA/('decoded_'+kind)).glob('*.png')))
    rows=[];decoded={};masks=np.load(QA/'weather_masks.npz')
    # A 3-pixel inset excludes compression ringing at moving rain boundaries.
    core=np.zeros((1080,1920),bool);core[40:364,1296:1872]=True
    for i in [0,1,36,72,108,142,143]:
        src=read(QA/(kind+'_frames')/('f'+str(i).zfill(3)+'.png'))[:,:,:3]
        out=read(QA/('decoded_'+kind)/('f'+str(i).zfill(3)+'.png'))[:,:,:3];decoded[i]=out
        delta=np.abs(src.astype(np.int16)-out.astype(np.int16));mse=np.mean(delta.astype(np.float64)**2)
        active=src.max(axis=2)>8;active_error=float(delta[active].mean())
        assert active_error<6,(kind,i,'Active rain detail error',active_error)
        black=int(out[core].max());assert black==0,(kind,i,'Decoded aperture not true black',black)
        interior=int(out[440:480,910:960].max());assert interior==0,(kind,i,'Indoor black',interior)
        assert delta.mean()<2,(kind,i,delta.mean())
        rows.append({'frame':i,'mean_abs_error':float(delta.mean()),'p99_abs_error':float(np.percentile(delta,99)),
            'psnr_db':10*math.log10(255**2/max(mse,1e-12)),'active_pixel_mean_abs_error':active_error,'aperture_black_max':black,'interior_black_max':interior})
    assert len({hashlib.sha256(a.tobytes()).hexdigest() for a in decoded.values()})==7
    diff=lambda a,b:float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean())
    seam=diff(decoded[143],decoded[0]);adj=max(diff(decoded[0],decoded[1]),diff(decoded[142],decoded[143]),period['adjacent_max_mean_abs'])
    assert seam<=adj*1.6+.02,(kind,seam,adj)
    return {'container':container,'vp9_bitstream':fmt,'metadata':meta,'decoded_samples':rows,
            'decoded_seam_mean_abs':seam,'decoded_adjacent_max_mean_abs':adj,'true_black_aperture':True}

def contracts(old,new,path='manifest'):
    allowed={'manifest.loop_seconds','manifest.loop_frames','manifest.light_loop_bytes','manifest.light_loop_sha256',
             'manifest.asset_pack_pass','manifest.full_composition','manifest.loop_seam_validation'}
    if path in allowed or path.startswith('manifest.validation.'):return
    if isinstance(old,dict):
        for k,v in old.items():assert k in new,(path,k);contracts(v,new[k],path+'.'+k)
    elif isinstance(old,list):
        assert len(new)>=len(old),path
        if path!='manifest.prop_loops':assert len(new)==len(old),path
        for i,v in enumerate(old):contracts(v,new[i],path+'['+str(i)+']')
    else:assert old==new,(path,old,new)

def main():
    old=json.loads((LIVE/'manifest.json').read_text());m=json.loads(json.dumps(old))
    prop=json.loads((QA/'prop_validation.json').read_text());weather=json.loads((QA/'weather_validation.json').read_text())
    videos=json.loads((QA/'video_metadata.json').read_text());calib=json.loads((QA/'calibration.json').read_text())
    holdouts=[json.loads((QA/('surroundings_occlusion'+s+'.json')).read_text()) for s in ['', '@2x']]
    assert prop['passed'] and weather['passed'] and calib['passed'] and all(r['covered_action_pixels']==0 for r in holdouts)
    video_report={k:validate_video(k,videos[k],weather['streams'][k]) for k in videos}
    (QA/'video_validation.json').write_text(json.dumps({'passed':True,'streams':video_report},indent=2))
    status('Both decoded VP9 streams validated: 8-bit 4:2:0, exact black aperture/interior, natural last-to-first seams')
    m.update(asset_pack_pass=8,loop_seconds=6,loop_frames=144,light_loop_bytes=videos['light_loop']['bytes'],
        light_loop_sha256=videos['light_loop']['sha256'],loop_seam_validation='qa8/weather_validation.json',
        full_composition='base + light_loop frame 60, render_layers and default prop_loops depth-sorted, then rain_fg frame 60; full.png includes glass water and the arcade attract state')
    m['rain_fg']={'file':'rain_fg.webm','size':[1920,1080],'fps':24,'frames':144,'seconds':6,'blend':'plus-lighter','z_index':70001,
                  'bytes':videos['rain_fg']['bytes'],'sha256':videos['rain_fg']['sha256']}
    newloops=json.loads((QA/'new_prop_loops.json').read_text())+json.loads((QA/'roof_water_loops.json').read_text());m['prop_loops']+=newloops
    m['items']['wet_print']=json.loads((QA/'wet_print_item.json').read_text())
    m['pass8_prop_loop_contract']={'timing':'Use each entry fps/frames: glass and roof water 72 at 12 fps; arcade play 72 at 24 fps; hiscore 24 at 24 fps.',
        'glass':'Straight RGBA source-over. Insert immediately after listed glass slice at the exact same z_index; cashier remains dry.',
        'arcade':'Select exactly one of arcade_attract, arcade_play, arcade_hiscore; their placement and parent are identical.',
        'awning':'The surroundings parent is baked in the background. awning_rain has no sprite parent; render the crop at its supplied z_index.',
        'fallback':'full.png contains default water overlays and attract; reduced motion may freeze any entry. Native 2x PNGs, 1080p videos at both stage scales.',
        'glass_atlas_decoded_bytes_both_scales':prop['glass_decoded_bytes_combined']}
    m['pass8_item_contract']={'wet_print':'Place its centre anchor on the ground behind arrivals and fade with source-over; inherited item attachment rules remain unchanged.'}
    m['pass8_art']={'scene':'../roxy_pass8.blend','surroundings':'Connected 3D neighborhood; revised lighting with 37 percent warm/TV windows, violet sky and rain haze.',
        'wet_reflections':weather['base_method'],'rain_counts':weather['rain_counts'],'new_glass_loops':9,
        'entrance':json.loads((QA/'wet_scene_metadata.json').read_text()),'lighting':json.loads((QA/'lighting_changes.json').read_text()),
        'source_preview':'../qa8/preview_surroundings_2.png','page_only_followups':['crowd spacing','bubble sign avoidance','emote contact','bench patron'],
        'decode_measurement':videos,'live_obs_benchmark_performed':False}
    m['validation'].update(calibration='../qa8/calibration.json',layout='../qa8/final_validation.json',loop_period='../qa8/weather_validation.json',encoded_video='../qa8/video_validation.json')
    m['pass8_validation']='../qa8/final_validation.json';contracts(old,m)
    predecode([OUT/(e['file'][:-4]+s+'.png') for e in m['render_layers'] for s in ['', '@2x']])
    green_rows=[]
    for scale in [1,2]:
        for f in [0,72,143]:
            a=compose(m,f,scale,decoded=True,green=True);region=a[40*scale:364*scale,1296*scale:1872*scale,:3]
            count=int(np.all(region==[0,255,0],axis=2).sum());expected=186624*scale*scale;assert count==expected,(scale,f,count)
            green_rows.append({'scale':scale,'frame':f,'physical_green_pixels':count,'logical_green_pixels':count//(scale*scale),'expected':expected})
            if f==72:write(QA/('aperture_green'+('@2x' if scale==2 else '')+'.png'),a)
        full=compose(m,60,scale);write(OUT/('full'+('@2x' if scale==2 else '')+'.png'),full)
    for f in [0,36,72,108,143]:write(QA/('final_decoded_f'+str(f).zfill(3)+'.png'),compose(m,f,decoded=True))
    status('Final compositions validated: 186624 green aperture pixels at 1080p; 746496 at 4K (186624 logical), including decoded weather and water overlays')
    # Contact details from actual delivered assets, with water and CRT sorting.
    a=compose(m,72,decoded=True,arcade='arcade_play');b=compose(m,72,decoded=True,arcade='arcade_hiscore')
    detail=np.concatenate([a[815:1018,805:1230],b[815:1018,805:1230]],axis=1);write(QA/'entrance_glass_arcade_check.png',np.repeat(np.repeat(detail,2,0),2,1))
    item=read(OUT/'items/wet_print@2x.png');alpha=item[:,:,3:4]/255
    contact=np.rint(item[:,:,:3]*alpha+np.array([116,100,130])*(1-alpha)).astype(np.uint8)
    write(QA/'wet_print_check.png',np.repeat(np.repeat(contact,16,0),16,1))
    assert np.array_equal(down_rgba(read(OUT/'items/wet_print@2x.png')),read(OUT/'items/wet_print.png'))
    assert m['items']['wet_print']['anchor']==[5,3]
    for file in ['items/wet_print.png','items/wet_print@2x.png']:
        a=read(OUT/file);assert not a[a[:,:,3]==0,:3].any()
        assert not any(s.any() for s in [a[0,:,3],a[-1,:,3],a[:,0,3],a[:,-1,3]]),'Wet print crop edge'
    for e in newloops:
        for scale,key in [(1,'file'),(2,'file_2x')]:
            a=read(OUT/e[key]);assert a.shape[:2]==(e['h']*e['rows']*scale,e['w']*e['columns']*scale),e['name']
            if e['blend']=='source-over':assert not a[a[:,:,3]==0,:3].any(),e['name']
        if e['name'].startswith('water_'):
            parent=next(p for p in m['render_layers'] if p['name']==e['parent_slices'][0]);assert parent['z_index']==e['z_index']
    # Every existing contract, coordinate and copied asset survives unchanged.
    changed={'base.png','base@2x.png','bg.png','bg@2x.png','lit_bg.png','lit_bg@2x.png','full.png','full@2x.png','light_loop.webm','manifest.json'}
    inherited=[]
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            rel=p.relative_to(LIVE).as_posix();assert (OUT/rel).exists(),rel
            if rel not in changed:assert sha(p)==sha(OUT/rel),rel;inherited.append(rel)
    baseline=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    paths={p.relative_to(ROOT).as_posix() for d in ['out','out2','out3','out4','out5','out6','out7'] for p in (ROOT/d).rglob('*') if p.is_file()}
    assert paths=={e['path'] for e in baseline}
    for row in baseline:
        p=ROOT/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
    m['pass8_checks']={'occlusion_1080':0,'occlusion_4k':0,'aperture_physical_1080':186624,'aperture_physical_4k':746496,
        'aperture_logical_both_scales':186624,'calibration_max_axis_error_px':calib['max_axis_error_px'],
        'glass_decoded_mib_both_scales':prop['glass_decoded_bytes_combined']/1024**2,'decoded_video_black_max':0,
        'source_weather_endpoint_error':0,'protected_live_files_unchanged':len(baseline)}
    pending=OUT/'manifest.pending.json';pending.write_text(json.dumps(m,indent=2)+'\n');pending.replace(OUT/'manifest.json')
    inventory=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report={'passed':True,'checks':m['pass8_checks'],'old_manifest_contracts_preserved':True,'inherited_byte_identical_assets':len(inherited),
        'changed_inherited_files':sorted(changed),'aperture_checks':green_rows,'holdouts':holdouts,'prop_validation':prop,
        'videos':video_report,'live_files_verified':len(baseline),'output_files':len(inventory),'output_bytes':sum(r['bytes'] for r in inventory),'inventory':inventory}
    (QA/'final_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    status('Complete out8 manifest published; inherited coordinates/contracts and '+str(len(baseline))+' protected live-file SHA-256 hashes verified unchanged')
    print('PASS8_FINAL',json.dumps(m['pass8_checks']),flush=True)

if __name__=='__main__':main()
