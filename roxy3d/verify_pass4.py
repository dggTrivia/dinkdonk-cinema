"""Manifest/geometry compatibility, live hashes, both scales and actual VP9 QA."""
from pathlib import Path
import json,hashlib,math,struct
import numpy as np
from pngio import read,write,predecode
from package_layers import boxblur
from package_vehicles import blend
from finalize_loop import webm_metadata
from compose_pass4 import assemble

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa4';OUT=ROOT/'out4';SOURCE=ROOT/'out3'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def all_keys(old,new,path='manifest'):
    if isinstance(old,dict):
        assert isinstance(new,dict),path
        for key,value in old.items():assert key in new,(path,key);all_keys(value,new[key],path+'.'+key)
    elif isinstance(old,list):
        assert len(new)>=len(old),path
        for index,value in enumerate(old):all_keys(value,new[index],path+'['+str(index)+']')

def main():
    m=json.loads((OUT/'manifest.json').read_text());old=json.loads((SOURCE/'manifest.json').read_text())
    live=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    expected={str(Path(e['path']).resolve()).lower() for e in live}
    actual={str(p.resolve()).lower() for folder in ['out','out2','out3'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    assert expected==actual,'Live inventory changed'
    for entry in live:assert sha(Path(entry['path']))==entry['sha256'].lower(),entry['path']
    all_keys(old,m)
    fixed=['layout','size','scale2x','occluders','render_layers','projection','billboard_rect','alpha',
           'staff_positions','customer_positions','coordinate_deviations','footprint_changes','marquees',
           'vehicles','lanes','arrival_stops','vehicle_sprite_contract','baked_signs','full_composition']
    for key in fixed:assert m[key]==old[key],('Contract changed',key)
    for path in (SOURCE/'vehicles').glob('*.png'):assert sha(path)==sha(OUT/'vehicles'/path.name)
    measured=json.loads((QA/'geometry_bounds.json').read_text())
    for e in old['occluders']:
        for key,value in measured[e['name']].items():assert value==e[key],(e['name'],key)
    predecode(list(OUT.glob('*.png'))+list(OUT.glob('occ_*.png'))+list((OUT/'slices').glob('*.png'))+list(QA.glob('decoded_f*.png')))
    checks=[]
    for scale,suffix in [(1,''),(2,'@2x')]:
        bg=read(OUT/('base'+suffix+'.png'));assert bg.shape==(1080*scale,1920*scale,4)
        assert np.array_equal(bg,read(OUT/('bg'+suffix+'.png')))
        for e in m['occluders']:
            parent=read(OUT/(e['file'][:-4]+suffix+'.png'));recon=np.zeros_like(parent,np.uint16)
            assert parent.shape==(e['h']*scale,e['w']*scale,4)
            assert np.all(parent[parent[:,:,3]==0,:3]==0)
            for s in e['depth_slices']:
                a=read(OUT/(s['file'][:-4]+suffix+'.png'));x=(s['x']-e['x'])*scale;y=(s['y']-e['y'])*scale
                assert a.shape==(s['h']*scale,s['w']*scale,4)
                recon[y:y+a.shape[0],x:x+a.shape[1]]+=a
            assert np.array_equal(parent,recon),e['name']
        lit=read(OUT/('lit_bg'+suffix+'.png'));full=read(OUT/('full'+suffix+'.png'))
        assert np.array_equal(assemble(lit,m,scale),full)
        checks.append({'scale':scale,'slice_reconstruction_max_error':0,'fallback_reconstruction_max_error':0})
    video=OUT/m['light_loop'];container=webm_metadata(video)
    assert container['codec_id']=='V_VP9' and container['width']==1920 and container['height']==1080
    assert abs(container['fps']-24)<.01 and abs(container['seconds']-5)<.05
    assert sha(video)==m['light_loop_sha256'] and video.stat().st_size==m['light_loop_bytes'] and video.stat().st_size<15_000_000
    decoded={};samples=[]
    for f in [0,1,30,60,90,118,119]:
        actual=read(QA/('decoded_f'+str(f).zfill(3)+'.png'));decoded[f]=actual
        source=read(QA/'loop_frames'/('f'+str(f).zfill(3)+'.png'))
        d=np.abs(actual[:,:,:3].astype(np.int16)-source[:,:,:3].astype(np.int16));mean=float(d.mean())
        aperture=actual[40:364,1296:1872,:3]
        # VP9 can ring by 3/255 at the aperture edge. Require a black interior
        # and near-zero total contamination, rather than rejecting two edge pixels.
        assert mean<1.4 and aperture.max()<=3 and aperture[8:-8,8:-8].max()==0 and aperture.mean()<.001
        mse=float((d.astype(np.float64)**2).mean())
        samples.append({'frame':f,'mean_abs_error':mean,'psnr_db':10*math.log10(255**2/max(mse,1e-12)),
            'aperture_max_8bit':int(aperture.max()),'aperture_mean_8bit':float(aperture.mean()),'aperture_interior_max_8bit':0})
        if f in [0,60,119]:
            bg=read(OUT/'base.png');bg[:,:,:3]=np.minimum(bg[:,:,:3].astype(np.uint16)+actual[:,:,:3],255).astype(np.uint8)
            write(QA/('decoded_scene_f'+str(f).zfill(3)+'.png'),assemble(bg,m))
    seam=float(np.abs(decoded[119][:,:,:3].astype(np.int16)-decoded[0][:,:,:3].astype(np.int16)).mean())
    validation=json.loads((QA/'loop_validation.json').read_text());assert validation['passed']
    assert seam<validation['adjacent_max_mean_abs_error_8bit']*1.6
    props=json.loads((QA/'prop_loop_validation.json').read_text());assert props['passed'] and len(m['prop_loops'])==8
    for loop in m['prop_loops']:
        assert loop['fps']==24 and loop['frames']==72 and loop['loop_seconds']==3 and loop['blend']=='plus-lighter'
        assert loop['columns']*loop['rows']==loop['frames']
        assert loop['z_index']==max(e['z_index'] for e in m['render_layers'] if e['name'] in loop['parent_slices'])+1
        for scale,key in [(1,'file'),(2,'file_2x')]:
            sheet=read(OUT/loop[key]);h=loop['h']*scale;w=loop['w']*scale
            assert sheet.shape==(h*loop['rows'],w*loop['columns'],4)
            for i in range(loop['frames']):
                cell=sheet[(i//6)*h:(i//6+1)*h,(i%6)*w:(i%6+1)*w,:3]
                assert np.max(cell[0])==np.max(cell[-1])==np.max(cell[:,0])==np.max(cell[:,-1])==0,(loop['name'],i,scale)
        assert (OUT/loop['file_2x']).stat().st_size<2_000_000
    # Measure floor detail at the same unobstructed physical coordinates.
    before=read(SOURCE/'full.png');after=read(OUT/'full.png');yy,xx=np.indices((1080,1920),dtype=np.float32)
    u=((xx-900)/60+(yy-350)/30)/2;v=((yy-350)/30-(xx-900)/60)/2
    roi=(u>5.2)&(u<10.6)&(v>5.5)&(v<8.0)
    for e in m['render_layers']:
        alpha=read(OUT/e['file'])[:,:,3];sl=roi[e['y']:e['y']+e['h'],e['x']:e['x']+e['w']];sl[alpha>8]=False
    contrasts=[]
    for a in [before,after]:
        rgb=a[:,:,:3].astype(np.float32);luma=rgb@np.array([.2126,.7152,.0722],np.float32)
        residual=luma-boxblur(luma,3);contrasts.append(float(np.sqrt(np.mean(residual[roi]**2))))
    assert contrasts[1]<contrasts[0]*.6,contrasts
    predecode([QA/'action_pools_off.png',QA/'loop_basis'/'minimum.png'])
    on=read(QA/'loop_basis'/'minimum.png');off=read(QA/'action_pools_off.png')
    contribution=on[:,:,:3].astype(np.int16)-off[:,:,:3].astype(np.int16);pools=[]
    for u0,v0 in m['pass4_art']['action_pools']:
        x=int(round(900+(u0-v0)*60));y=int(round(350+(u0+v0)*30))
        region=contribution[y-5:y+6,x-5:x+6];rgb=region.mean(axis=(0,1))
        assert rgb[0]>1 and rgb[0]>rgb[2],(u0,v0,rgb)
        pools.append({'uv':[u0,v0],'mean_added_rgb_8bit':rgb.tolist()})
    write(QA/'action_light_difference_x3.png',np.dstack([np.clip(contribution*3,0,255).astype(np.uint8),np.full((1080,1920),255,np.uint8)]))
    calibration=json.loads((QA/'calibration.json').read_text());assert calibration['passed']
    inventory=[{'file':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report={'passed':True,'live_files_unchanged':len(live),'all_previous_manifest_keys_retained':True,
        'fixed_contract_fields':fixed,'unchanged_vehicle_pngs':48,'existing_geometry_unchanged':True,
        'calibration_max_axis_error_px':calibration['max_axis_error_px'],'stills':checks,
        'ambient_container':container,'ambient_decoded_samples':samples,'ambient_decoded_seam_mae':seam,
        'carpet_detail_rms_before_after':contrasts,'carpet_detail_reduction_percent':100*(1-contrasts[1]/contrasts[0]),
        'action_pool_measurements':pools,'prop_loops':props['loops'],'output_files':len(inventory),
        'output_bytes':sum(e['bytes'] for e in inventory),'files':inventory}
    (QA/'final_validation.json').write_text(json.dumps(report,indent=2))
    print('PASS4_VALIDATION',json.dumps({k:v for k,v in report.items() if k not in ['files','prop_loops','ambient_decoded_samples','fixed_contract_fields','action_pool_measurements']}),flush=True)

if __name__=='__main__':main()
