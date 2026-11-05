"""Delivery validation: live hashes, portable assets, shared anchors, both scales."""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np
from pngio import read,predecode
from package_vehicles import blend,at2,project

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa3';OUT=ROOT/'out3'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    live=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    expected={str(Path(e['path']).resolve()).lower() for e in live}
    actual={str(p.resolve()).lower() for folder in ['out','out2'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    assert actual==expected,'Live folder file inventory changed'
    for entry in live:
        path=Path(entry['path']);assert sha(path)==entry['sha256'].lower(),path
        assert path.stat().st_size==entry['bytes'],path
    preserved=[]
    for path in (ROOT/'out2').rglob('*'):
        if path.is_file() and path.name!='manifest.json':
            dest=OUT/path.relative_to(ROOT/'out2');assert sha(path)==sha(dest),dest
            preserved.append(dest.relative_to(OUT).as_posix())
    m=json.loads((OUT/'manifest.json').read_text());assert m['layout']==2 and m['lanes']=={'near':11.0,'far':12.0}
    assert set(m['vehicles'])=={'bus','taxi','sedan_a','sedan_b'}
    predecode(list((OUT/'vehicles').glob('*.png'))+[OUT/'lit_bg.png',OUT/'lit_bg@2x.png',OUT/'full.png',OUT/'full@2x.png'])
    results=[];used=set()
    for kind,directions in m['vehicles'].items():
        assert set(directions)=={'+u','-u'}
        for direction,e in directions.items():
            assert 0<e['anchor'][0]<e['w'] and 0<e['anchor'][1]<e['h']
            if kind=='bus':assert e['length_tiles']==2.6
            if kind in ['bus','taxi']:assert 'door_open' in e
            for state,v in [('closed',e)]+([('open',e['door_open'])] if 'door_open' in e else []):
                if state=='open':assert v['anchor']==e['anchor'] and v['w']==e['w'] and v['h']==e['h']
                for scale in [1,2]:
                    suffix='_2x' if scale==2 else ''
                    body_path=OUT/v['file'+suffix];light_path=OUT/v['light'+suffix]
                    assert body_path.resolve().is_relative_to(OUT.resolve()) and light_path.resolve().is_relative_to(OUT.resolve())
                    body=read(body_path);light=read(light_path)
                    assert body.shape==light.shape==(e['h']*scale,e['w']*scale,4),(kind,direction,state,scale,body.shape)
                    assert struct.unpack_from('>IIBB',body_path.read_bytes(),16)==(e['w']*scale,e['h']*scale,8,6)
                    assert (body[body[:,:,3]==0,:3]==0).all(),'RGB leak in zero-alpha texels'
                    assert 0<body[:,:,3].max() and 0<light[:,:,:3].max()
                    border_body=np.concatenate([body[0,:,3],body[-1,:,3],body[:,0,3],body[:,-1,3]])
                    border_light=np.concatenate([light[0,:,:3].ravel(),light[-1,:,:3].ravel(),light[:,0,:3].ravel(),light[:,-1,:3].ravel()])
                    assert border_body.max()==0 and border_light.max()==0,'Sprite reaches crop edge'
                    for path in [body_path,light_path]:
                        used.add(path.name)
                        assert path.stat().st_size<600_000,('Unexpectedly large sprite',path)
                    results.append({'kind':kind,'direction':direction,'state':state,'scale':scale,
                        'w':body.shape[1],'h':body.shape[0], 'body_bytes':body_path.stat().st_size,
                        'light_bytes':light_path.stat().st_size,'body_sha256':sha(body_path),'light_sha256':sha(light_path)})
                    if state=='open':
                        closed=read(OUT/e['file'+suffix]);assert np.any(body!=closed),'Door variant is identical'
    assert len(used)==48 and len(results)==24
    for row in json.loads((QA/'vehicle_crops.json').read_text()):
        logical_anchor=np.array(row['anchor'])/row['scale']
        assert np.array_equal(np.array(row['crop_global'])+logical_anchor,project(6,11))
    placements=json.loads((QA/'placements.json').read_text());assert placements['max_anchor_rounding_error_px']<=.5
    fallback=[]
    for scale in [1,2]:
        suffix='@2x' if scale==2 else '';a=read(OUT/('lit_bg'+suffix+'.png'))
        predecode([OUT/(at2(e['file']) if scale==2 else e['file']) for e in m['render_layers']])
        for e in m['render_layers']:blend(a,read(OUT/(at2(e['file']) if scale==2 else e['file'])),e['x']*scale,e['y']*scale)
        full=read(OUT/('full'+suffix+'.png'));diff=np.abs(a.astype(np.int16)-full.astype(np.int16))
        assert diff.max()==0,('Fallback reconstruction',scale,int(diff.max()))
        fallback.append({'scale':scale,'max_channel_error':int(diff.max())})
    calibration=json.loads((QA/'calibration.json').read_text());assert calibration['passed']
    inventory=[{'file':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report={'passed':True,'live_files_unchanged':len(live),'copied_assets_byte_identical':len(preserved),
        'vehicle_pngs':len(used),'vehicle_pairs_at_both_scales':len(results),
        'calibration_max_axis_error_px':calibration['max_axis_error_px'],
        'shared_crop_anchor_error_px':0,'scene_anchor_rounding_error_px':placements['max_anchor_rounding_error_px'],
        'fallback_reconstruction':fallback,'vehicle_checks':results,'files':inventory,
        'output_files':len(inventory),'output_bytes':sum(e['bytes'] for e in inventory),
        'vehicle_bytes':sum(e['bytes'] for e in inventory if e['file'].startswith('vehicles/'))}
    (QA/'vehicle_validation.json').write_text(json.dumps(report,indent=2))
    print('VEHICLE_VALIDATION',json.dumps({k:v for k,v in report.items() if k not in ['vehicle_checks','files']}),flush=True)

if __name__=='__main__':main()
