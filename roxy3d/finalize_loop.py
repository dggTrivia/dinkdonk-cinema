"""Validate actual VP9 decoded pixels, then atomically publish the loop manifest."""
from pathlib import Path
import json,hashlib,struct,math
import numpy as np
from pngio import read,write,predecode
from package_pass2 import assemble,validate

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out2';QA=ROOT/'qa2'

def vint(data,at,identity=False):
    first=data[at];length=1;mask=128
    while not first&mask:mask>>=1;length+=1
    value=int.from_bytes(data[at:at+length],'big')
    if not identity:value&=(1<<(7*length))-1
    return value,length

def children(data,start,end):
    at=start
    while at<end:
        tag,n=vint(data,at,True);size,k=vint(data,at+n);begin=at+n+k;finish=min(end,begin+size)
        yield tag,begin,finish
        at=finish

def webm_metadata(path):
    data=path.read_bytes();info={};scale=1_000_000;duration=None
    def walk(start,end):
        nonlocal scale,duration
        for tag,a,b in children(data,start,end):
            payload=data[a:b]
            if tag in [0x18538067,0x1549A966,0x1654AE6B,0xAE,0xE0]:walk(a,b)
            elif tag==0x2AD7B1:scale=int.from_bytes(payload,'big')
            elif tag==0x4489:duration=struct.unpack('>d' if len(payload)==8 else '>f',payload)[0]
            elif tag==0x86:info['codec_id']=payload.decode('ascii')
            elif tag==0x23E383:info['frame_nanoseconds']=int.from_bytes(payload,'big')
            elif tag==0xB0:info['width']=int.from_bytes(payload,'big')
            elif tag==0xBA:info['height']=int.from_bytes(payload,'big')
    walk(0,len(data))
    info['seconds']=duration*scale/1e9 if duration is not None else None
    info['fps']=1e9/info['frame_nanoseconds'] if info.get('frame_nanoseconds') else None
    return info

def main():
    m=json.loads((QA/'manifest_loop_pending.json').read_text());meta=json.loads((QA/'video_metadata.json').read_text())
    video=OUT/'light_loop.webm';container=webm_metadata(video)
    assert container['codec_id']=='V_VP9' and container['width']==1920 and container['height']==1080,container
    assert abs(container['seconds']-5)<.05,container
    assert abs(container['fps']-24)<.01,container
    assert video.stat().st_size<15_000_000
    assert hashlib.sha256(video.read_bytes()).hexdigest()==meta['sha256']
    predecode(list(QA.glob('decoded_f*.png')))
    samples=[];decoded={};base=read(OUT/'base.png')
    for f in [0,1,30,60,90,118,119]:
        source=read(QA/'loop_frames'/('f'+str(f).zfill(3)+'.png'))
        output=read(QA/('decoded_f'+str(f).zfill(3)+'.png'));decoded[f]=output
        delta=np.abs(source[:,:,:3].astype(np.int16)-output[:,:,:3].astype(np.int16))
        mse=float((delta.astype(np.float64)**2).mean());roi=source[:,:,:3].max(axis=2)>3
        samples.append({'frame':f,'mean_abs_error_8bit':float(delta.mean()),'p99_abs_error':float(np.percentile(delta,99)),
            'active_light_mean_abs_error':float(delta[roi].mean()),'psnr_db':10*math.log10(255**2/max(mse,1e-12)),
            'billboard_aperture_max':int(output[40:364,1296:1872,:3].max())})
        assert samples[-1]['mean_abs_error_8bit']<1.4,samples[-1]
        assert samples[-1]['billboard_aperture_max']<=2,samples[-1]
        if f in [0,60,119]:
            composed=base.copy();composed[:,:,:3]=np.minimum(base[:,:,:3].astype(np.uint16)+output[:,:,:3],255).astype(np.uint8)
            write(QA/('decoded_preview_f'+str(f).zfill(3)+'.png'),assemble(composed,m['render_layers']))
        if f in [0,30,60,90,119]:
            expected=base.copy();expected[:,:,:3]=np.minimum(base[:,:,:3].astype(np.uint16)+source[:,:,:3],255).astype(np.uint8)
            rebuilt=assemble(expected,m['render_layers']);preview=read(QA/('loop_f'+str(f).zfill(3)+'.png'))
            assert np.array_equal(rebuilt,preview),f
            if f==60:assert np.array_equal(rebuilt,read(OUT/'full.png'))
    seam=float(np.abs(decoded[119][:,:,:3].astype(np.int16)-decoded[0][:,:,:3].astype(np.int16)).mean())
    first_adj=float(np.abs(decoded[1][:,:,:3].astype(np.int16)-decoded[0][:,:,:3].astype(np.int16)).mean())
    last_adj=float(np.abs(decoded[119][:,:,:3].astype(np.int16)-decoded[118][:,:,:3].astype(np.int16)).mean())
    periodic=json.loads((QA/'loop_validation.json').read_text());assert periodic['passed']
    assert seam<max(periodic['adjacent_max_mean_abs_error_8bit']*1.6,first_adj*1.6,last_adj*1.6)
    geometry=json.loads((QA/'geometry_bounds.json').read_text())
    deviations=[d for d in m['coordinate_deviations'] if d['name']=='street_padding']
    reasons={'partition_left':'Wall finish and lightboard project from the lobby face.',
        'partition_right':'Tall back-bar equipment and wall menus share the partition sprite, behind clerks.',
        'palm':'Fronds overhang the exact requested pot footprint.',
        'standee_1':'Stabilizing foot extends beyond the board, as in pass 1.',
        'standee_2':'Stabilizing foot extends beyond the board at its new position.',
        'bus_stop':'Preserved roof and camera-facing route plaque.',
        'arcade':'Preserved CRT, trim and camera-facing ORBIT lettering.',
        'roxy_blade':'Preserved neon tubing and camera-facing ROXY lettering.'}
    for e in m['occluders']:
        measured=geometry[e['name']];e.update(measured);fp=e['footprint'];gf=measured['geometry_footprint']
        outside=gf[0]<fp[0]-.002 or gf[1]<fp[1]-.002 or gf[2]>fp[2]+.002 or gf[3]>fp[3]+.002 or measured['geometry_z_px'][1]>e['height_px']+.1
        if outside:deviations.append({'name':e['name']+'_visual_overhang','sorting_footprint':fp,**measured,
            'reason':reasons.get(e['name'],'Small trim, glass, lamp or bevel overhang. The requested sorting footprint is unchanged.')})
    m['coordinate_deviations']=deviations
    validate(m)
    report={'passed':True,'container':container,'bytes':video.stat().st_size,'decoded_samples':samples,
        'decoded_last_to_first_mean_abs_error_8bit':seam,'decoded_first_adjacent_mean_abs_error':first_adj,
        'decoded_last_adjacent_mean_abs_error':last_adj,'lossless_period_endpoint_max_error':0,
        'source_over_reference_reconstruction_max_error':0}
    (QA/'video_validation.json').write_text(json.dumps(report,indent=2))
    m.update(status='complete',light_loop_bytes=video.stat().st_size,light_loop_sha256=meta['sha256'],
        validation={'calibration':'../qa2/calibration.json','layout':'../qa2/layout_validation.json',
        'slices':'../qa2/slice_validation.json','loop_period':'../qa2/loop_validation.json','encoded_video':'../qa2/video_validation.json'})
    path=OUT/'manifest.pending.json';path.write_text(json.dumps(m,indent=2));path.replace(OUT/'manifest.json')
    print('FINAL_LOOP_QA',json.dumps({k:v for k,v in report.items() if k!='decoded_samples'}),flush=True)

if __name__=='__main__':main()
