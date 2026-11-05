"""Complete-pack acceptance, scoped contract comparison, pixels and live hashes."""
import json,hashlib,math
import numpy as np
import finalize_pass8 as core
from pngio import read,write,predecode
from package_layers import over
from package_pass2 import grain
from pass8b_common import ROOT,QA,OUT,LIVE,status
core.QA=QA;core.OUT=OUT;core.LIVE=LIVE;core.status=status

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def contracts(old,new,path='manifest'):
    allowed={'manifest.light_loop_bytes','manifest.light_loop_sha256','manifest.rain_fg.bytes','manifest.rain_fg.sha256',
             'manifest.loop_seam_validation','manifest.pass8_prop_loop_contract.glass_atlas_decoded_bytes_both_scales'}
    if path in allowed or path.startswith('manifest.validation.'):return
    if isinstance(old,dict):
        for k,v in old.items():assert k in new,(path,k);contracts(v,new[k],path+'.'+k)
    elif isinstance(old,list):
        assert len(new)>=len(old),path
        if path!='manifest.prop_loops':assert len(new)==len(old),path
        for i,v in enumerate(old):contracts(v,new[i],path+'['+str(i)+']')
    else:assert old==new,(path,old,new)

def full_dry(m,scale=1,green=False):
    suffix='@2x' if scale==2 else '';a=read(OUT/('lit_bg_dry'+suffix+'.png'))
    if green:a[40*scale:364*scale,1296*scale:1872*scale]=[0,255,0,255]
    for e in sorted(m['render_layers'],key=lambda e:e['z_index']):over(a,read(OUT/(e['file'][:-4]+suffix+'.png')),e['x']*scale,e['y']*scale)
    return a

def main():
    old=json.loads((LIVE/'manifest.json').read_text());m=json.loads(json.dumps(old))
    periods=json.loads((QA/'weather_validation.json').read_text());videos=json.loads((QA/'video_metadata.json').read_text())
    glass=json.loads((QA/'glass_validation.json').read_text());films=json.loads((QA/'film_loops.json').read_text())
    scene=json.loads((QA/'scene_changes.json').read_text());calib=json.loads((QA/'calibration.json').read_text())
    assert periods['passed'] and glass['passed'] and calib['passed']
    assert len(scene['removed_carpet_outline_objects'])==18
    holds=[json.loads((QA/('surroundings_occlusion'+s+'.json')).read_text()) for s in ['', '@2x']]
    assert all(e['covered_action_pixels']==0 for e in holds)
    vr={kind:core.validate_video(kind,videos[kind],periods['streams'][kind]) for kind in ['light_loop','rain_fg']}
    (QA/'video_validation.json').write_text(json.dumps({'passed':True,'streams':vr},indent=2))
    status('Both encoded videos passed profile/format, sampled true-black and active-rain accuracy checks; source and decoded seams passed')
    m.update(asset_pack_revision='8b',light_loop_bytes=videos['light_loop']['bytes'],light_loop_sha256=videos['light_loop']['sha256'],
             loop_seam_validation='qa8b/weather_validation.json',lit_bg_dry='lit_bg_dry.png',lit_bg_dry_2x='lit_bg_dry@2x.png')
    m['rain_fg'].update(bytes=videos['rain_fg']['bytes'],sha256=videos['rain_fg']['sha256'])
    m['prop_loops']+=films
    m['pass8_prop_loop_contract']['glass_atlas_decoded_bytes_both_scales']=glass['glass_decoded_bytes_both_scales']
    m['pass8b_art']={'scene':'../roxy_pass8b.blend','source_pack':'out8','preview':'../qa8b/preview_surroundings.png',
        'scene_changes':scene,'rain_counts':periods['rain_counts'],'local_impact_reflection_distortion':True,
        'glass':'Existing animated crops/depths unchanged; brighter runnels and nine pane-wide static film/sill entries added at the same slice depths.',
        'fallback':'lit_bg_dry and lit_bg_dry_2x are fully lit wet-surface backgrounds without baked falling rain, impacts, spray, animated runoff or steam.',
        'historical_metadata':'pass8_art and prior pass validation records describe the source pack; pass8b_art and pass8b_checks describe this revision.',
        'decode_measurement':videos,'live_obs_benchmark_performed':False}
    m['pass8b_fallback_contract']={'file':'lit_bg_dry.png','file_2x':'lit_bg_dry@2x.png','scope':'background only; place inherited render_layers above it',
        'weather':'No baked rain or impacts. The page supplies procedural rain and coordinates both video failure states.',
        'surfaces':'Wetness, puddles, fixed real lighting and reflections remain present.'}
    m['pass8b_glass_contract']={'film':'Nine one-cell straight-RGBA static surface films; same parent slice and exact z_index as each dynamic runnel crop.',
        'timing':'Dynamic water remains 72 frames / 12 fps / 6 seconds. Static film entries have frames=columns=rows=1.',
        'decoded_bytes_both_scales':glass['glass_decoded_bytes_both_scales']}
    m['validation'].update(calibration='../qa8b/calibration.json',layout='../qa8b/final_validation.json',loop_period='../qa8b/weather_validation.json',encoded_video='../qa8b/video_validation.json')
    m['pass8b_validation']='../qa8b/final_validation.json';contracts(old,m)
    predecode([OUT/(e['file'][:-4]+s+'.png') for e in m['render_layers'] for s in ['', '@2x']]+[QA/('steady_bg'+s+'.png') for s in ['', '@2x']])
    green=[];drychecks=[]
    for scale,suffix in [(1,''),(2,'@2x')]:
        raw=grain(read(QA/('steady_bg'+suffix+'.png')));inherited=read(LIVE/('base'+suffix+'.png'))
        raw[40*scale:364*scale,1296*scale:1872*scale]=inherited[40*scale:364*scale,1296*scale:1872*scale]
        dry=read(OUT/('lit_bg_dry'+suffix+'.png'));assert np.array_equal(raw,dry),'Weather-free fallback differs from the unanimated render'
        drychecks.append({'scale':scale,'unanimated_render_reconstruction_max_error':0,'size':[1920*scale,1080*scale]})
        for f in [0,72,143]:
            a=core.compose(m,f,scale,decoded=True,green=True);region=a[40*scale:364*scale,1296*scale:1872*scale,:3]
            count=int(np.all(region==[0,255,0],axis=2).sum());assert count==186624*scale*scale
            green.append({'scale':scale,'frame':f,'physical_green_pixels':count,'logical_green_pixels':count//scale**2})
            if f==72:write(QA/('aperture_green'+suffix+'.png'),a)
        a=full_dry(m,scale,green=True);region=a[40*scale:364*scale,1296*scale:1872*scale,:3]
        assert np.all(region==[0,255,0])
        write(QA/('fallback_dry_full'+suffix+'.png'),full_dry(m,scale))
        write(OUT/('full'+suffix+'.png'),core.compose(m,60,scale))
    status('Weather-free fallback and 1080p/4K aperture compositions validated; final full stills rebuilt with revised water')
    for f in [0,36,72,108,143]:write(QA/('final_decoded_f'+str(f).zfill(3)+'.png'),core.compose(m,f,decoded=True))
    # Targeted comparison figures use the delivered pixels, without retouching.
    before=read(LIVE/'full.png');after=read(QA/'final_decoded_f072.png')
    for name,(x0,y0,x1,y1) in {'backdrop':(880,0,1280,270),'rain_depth':(0,400,350,1050),
        'right_forecourt':(1150,720,1700,1080),'road_reflection':(130,620,520,870),'glass_in_scene':(525,675,875,880)}.items():
        write(QA/(name+'_before_after.png'),np.concatenate([before[y0:y1,x0:x1],after[y0:y1,x0:x1]],axis=1))
    predecode([LIVE/'base@2x.png']);a=read(LIVE/'base@2x.png');b=read(OUT/'base@2x.png')
    write(QA/'carpet_before_after_4k.png',np.concatenate([a[1300:1800,1500:2300],b[1300:1800,1500:2300]],axis=1))
    # Actual pane crops, alpha hygiene, exact original runnel coordinates.
    actual_budget=0
    for e in [e for e in m['prop_loops'] if e['name'].startswith(('water_glass_','film_glass_'))]:
        parent=next(p for p in m['render_layers'] if p['name']==e['parent_slices'][0]);assert e['z_index']==parent['z_index']
        for scale,key in [(1,'file'),(2,'file_2x')]:
            a=read(OUT/e[key]);assert a.shape==(e['h']*e['rows']*scale,e['w']*e['columns']*scale,4),e['name']
            assert not a[a[:,:,3]==0,:3].any();actual_budget+=a.size
    assert actual_budget==glass['glass_decoded_bytes_both_scales'] and actual_budget<=16*1024**2
    # Quantify darker physical forecourt, and density in the actual foreground.
    pos=np.load(QA/'world_positions.npz')['position'];mask=(pos[:,:,0]>13.12)&(pos[:,:,0]<17.8)&(pos[:,:,1]>6.6)&(pos[:,:,1]<9.1)&(pos[:,:,2]<0)
    oldbg=read(ROOT/'qa8/steady_bg.png');newbg=read(QA/'steady_bg.png');luma=lambda a:a[:,:,:3]@np.array([.2126,.7152,.0722])
    alley={'pixels':int(mask.sum()),'old_mean_luma':float(luma(oldbg)[mask].mean()),'new_mean_luma':float(luma(newbg)[mask].mean())}
    assert alley['pixels']>1000 and alley['new_mean_luma']<alley['old_mean_luma']*.85,alley
    rain_metrics=[]
    for f in [0,38,60,143]:
        oldfg=read(ROOT/'qa8/rain_fg_frames'/('f'+str(f).zfill(3)+'.png'))[:,:,:3]
        newfg=read(QA/'rain_fg_frames'/('f'+str(f).zfill(3)+'.png'))[:,:,:3]
        oldcount=int((oldfg.max(2)>8).sum());newcount=int((newfg.max(2)>8).sum());assert newcount>oldcount*1.7
        rain_metrics.append({'frame':f,'old_active_pixels_gt8':oldcount,'new_active_pixels_gt8':newcount,'density_ratio':newcount/oldcount})
    (QA/'polish_validation.json').write_text(json.dumps({'passed':True,'alley_luminance':alley,'foreground_rain_density':rain_metrics,'dry_fallback':drychecks,'carpet_outlines_removed':18},indent=2))
    status('Polish checks passed: darker forecourt, denser fine/medium foreground rain, clean carpet, pane-wide wetness and 16 MiB glass budget')
    # Assets outside the requested scope remain byte-identical to out8.
    changed={'base.png','base@2x.png','bg.png','bg@2x.png','lit_bg.png','lit_bg@2x.png','full.png','full@2x.png','light_loop.webm','rain_fg.webm','manifest.json'}
    changed.update(e[key] for e in old['prop_loops'] if e['name'].startswith('water_glass_') for key in ['file','file_2x'])
    inherited=[]
    for p in LIVE.rglob('*'):
        if p.is_file():
            rel=p.relative_to(LIVE).as_posix()
            if rel not in changed:assert sha(p)==sha(OUT/rel),rel;inherited.append(rel)
    baseline=json.loads((QA/'live_before.json').read_text())
    paths={p.relative_to(ROOT).as_posix() for d in ['out','out2','out3','out4','out5','out6','out7','out8'] for p in (ROOT/d).rglob('*') if p.is_file()}
    assert paths=={e['path'] for e in baseline}
    for e in baseline:
        p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
    m['pass8b_checks']={'occlusion_1080':0,'occlusion_4k':0,'aperture_physical_1080':186624,'aperture_physical_4k':746496,
        'aperture_logical_both_scales':186624,'decoded_video_black_max':0,'source_weather_endpoint_error':0,
        'glass_decoded_mib_both_scales':actual_budget/1024**2,'protected_live_files_unchanged':len(baseline),
        'calibration_max_axis_error_px':calib['max_axis_error_px'],'carpet_outlines_removed':18,'weather_free_fallback_verified':True}
    pending=OUT/'manifest.pending.json';pending.write_text(json.dumps(m,indent=2)+'\n');pending.replace(OUT/'manifest.json')
    inventory=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    expected={p.relative_to(LIVE).as_posix() for p in LIVE.rglob('*') if p.is_file()}|{'lit_bg_dry.png','lit_bg_dry@2x.png'}|{e[k] for e in films for k in ['file','file_2x']}
    assert {e['path'] for e in inventory}==expected,'Unexpected/missing pack files'
    report={'passed':True,'checks':m['pass8b_checks'],'live_files_verified':len(baseline),'inherited_byte_identical_assets':len(inherited),
        'inherited_manifest_contracts_preserved':True,'changed_inherited_files':sorted(changed),'aperture_checks':green,'videos':vr,
        'dry_fallback':drychecks,'polish':{'alley':alley,'rain_density':rain_metrics},'glass':glass,'holdouts':holds,
        'output_files':len(inventory),'output_bytes':sum(e['bytes'] for e in inventory),'inventory':inventory}
    (QA/'final_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    status('Complete out8b manifest published; all '+str(len(baseline))+' live-file hashes and unchanged asset contracts verified')
    print('PASS8B_COMPLETE',json.dumps(m['pass8b_checks']),flush=True)

if __name__=='__main__':main()
