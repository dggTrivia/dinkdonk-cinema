"""Independent delivered-file checks, including live preservation and compatibility."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from pngio import read,predecode

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa5';OUT=ROOT/'out5';LIVE=ROOT/'out4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def inherited(old,new,path='manifest'):
    if path=='manifest.pass':assert new==5;return
    if isinstance(old,dict):
        assert isinstance(new,dict),path
        for key,value in old.items():assert key in new,(path,key);inherited(value,new[key],path+'.'+key)
    elif isinstance(old,list):
        assert len(old)==len(new),path
        for i,value in enumerate(old):inherited(value,new[i],path+'['+str(i)+']')
    else:assert old==new,(path,old,new)

def frames(entry,scale):
    a=read(OUT/entry['file' if scale==1 else 'file_2x']);w=entry['frame_width']*scale;h=entry['frame_height']*scale
    assert a.shape==(entry['rows']*h,entry['columns']*w,4)
    return [a[i//entry['columns']*h:(i//entry['columns']+1)*h,i%entry['columns']*w:(i%entry['columns']+1)*w] for i in range(entry['frames'])]

def main():
    m=json.loads((OUT/'manifest.json').read_text());old=json.loads((LIVE/'manifest.json').read_text());inherited(old,m)
    baseline=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    actual={str(p.resolve()).lower() for folder in ['out','out2','out3','out4'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    assert actual=={str(Path(e['path']).resolve()).lower() for e in baseline}
    for entry in baseline:assert sha(Path(entry['path']))==entry['sha256'].lower(),entry['path']
    inherited_files=[]
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            target=OUT/p.relative_to(LIVE);assert sha(target)==sha(p),p.name;inherited_files.append(str(p.relative_to(LIVE)))
    predecode(list((OUT/'vehicles').glob('*.png')))
    slices=[];lamps=[];names=set()
    for kind,directions in m['vehicles'].items():
        assert set(directions)=={'+u','-u'}
        for direction,entry in directions.items():
            for opened,variant in [(False,entry)]+([(True,entry['door_open'])] if 'door_open' in entry else []):
                assert len(variant['slices'])>=2
                previous=None
                for s in variant['slices']:
                    assert s['u_range'][0]<=s['du']<=s['u_range'][1]
                    assert 0<s['u_range'][1]-s['u_range'][0]<=1.000001
                    if previous is not None:assert abs(previous-s['u_range'][0])<.00001
                    previous=s['u_range'][1]
                for scale,bodykey in [(1,'file'),(2,'file_2x')]:
                    body=read(OUT/variant[bodykey]);assert body.shape==(entry['h']*scale,entry['w']*scale,4)
                    recon=np.zeros_like(body,dtype=np.uint16);coverage=np.zeros(body.shape[:2],np.uint8)
                    for s in variant['slices']:
                        tile=read(OUT/s[bodykey]);x=s['x']*scale;y=s['y']*scale
                        assert tile.shape==(s['h']*scale,s['w']*scale,4)
                        assert x>=0 and y>=0 and x+tile.shape[1]<=body.shape[1] and y+tile.shape[0]<=body.shape[0]
                        assert np.all(tile[tile[:,:,3]==0,:3]==0)
                        recon[y:y+tile.shape[0],x:x+tile.shape[1]]+=tile
                        coverage[y:y+tile.shape[0],x:x+tile.shape[1]]+=(tile[:,:,3]>0)
                        names.add(s[bodykey])
                    assert coverage.max()==1 and np.array_equal(body,recon),(kind,direction,opened,scale)
                    slices.append({'kind':kind,'direction':direction,'door_open':opened,'scale':scale,'pieces':len(variant['slices']),'max_rgba_error':0})
                    normal=read(OUT/variant['light_2x' if scale==2 else 'light'])
                    for state in ['brake']+(['indicator'] if kind in ['bus','taxi'] else []):
                        a=read(OUT/variant['light_'+state+('_2x' if scale==2 else '')]);assert a.shape==normal.shape
                        d=a[:,:,:3].astype(np.int16)-normal[:,:,:3].astype(np.int16)
                        assert d.min()>=0 and d.max()>20
                        assert max(a[0,:,:3].max(),a[-1,:,:3].max(),a[:,0,:3].max(),a[:,-1,:3].max())==0
                        total=d.sum(axis=(0,1));assert total[0]>total[2]*2
                        lamps.append({'kind':kind,'direction':direction,'door_open':opened,'scale':scale,'state':state,'added_rgb':total.tolist()})
    cats=[]
    expected={'sleep','sit','walk_plus_u','walk_minus_u','walk_plus_v','walk_minus_v','stretch'}
    assert set(m['cat'])==expected
    catproof=json.loads((QA/'cat_validation.json').read_text());assert catproof['passed']
    for name,e in m['cat'].items():
        assert e['anchor']==[32,44]
        if name in ['sleep','sit']:assert 2<=e['frames']/e['fps']<=4 and e['loop']
        if name.startswith('walk'):assert 8<=e['frames']<=12 and e['stride_tiles']==.32 and e['loop']
        if name=='stretch':assert e['loop'] is False
        for scale in [1,2]:
            sequence=frames(e,scale)
            for i,a in enumerate(sequence):
                alpha=a[:,:,3]
                assert alpha.max()>200 and (alpha>0).sum()<alpha.size*.6,(name,i,scale)
                assert np.all(a[alpha==0,:3]==0)
                assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())==0
            # Native-scale shape remains small: no hidden off-canvas feet/ears/tail.
            cats.append({'name':name,'scale':scale,'frames':len(sequence),'clear_cell_border':True})
    sprays=[]
    assert set(m['tyre_spray'])=={'+u','-u'}
    for direction,e in m['tyre_spray'].items():
        assert e['frames']==12 and e['fps']==24 and e['loop'] is False and e['blend']=='plus-lighter'
        for scale in [1,2]:
            sequence=frames(e,scale)
            assert sequence[0][:,:,:3].max()==sequence[-1][:,:,:3].max()==0
            assert max(a[:,:,:3].max() for a in sequence)>30
            for a in sequence:assert max(a[0,:,:3].max(),a[-1,:,:3].max(),a[:,0,:3].max(),a[:,-1,:3].max())==0
            sprays.append({'direction':direction,'scale':scale,'first_last_black':True})
    calibration=json.loads((QA/'calibration.json').read_text());assert calibration['passed']
    depth=json.loads((QA/'depth_overlap_validation.json').read_text());assert depth['passed']
    preview=json.loads((QA/'preview_metadata.json').read_text())
    assert preview['frames']==360 and preview['fps']==24 and preview['size']==[1280,720]
    assert (QA/'cat_preview.mp4').stat().st_size==preview['bytes']
    predecode([QA/('preview_decoded_f'+str(f).zfill(3)+'.png') for f in preview['decoded_frames']])
    preview_errors=[]
    for f in preview['decoded_frames']:
        a=read(QA/('preview_decoded_f'+str(f).zfill(3)+'.png'));source=read(QA/'preview_frames'/('f'+str(f).zfill(3)+'.png'))
        assert a.shape==source.shape==(720,1280,4)
        error=float(np.abs(a[:,:,:3].astype(np.int16)-source[:,:,:3].astype(np.int16)).mean())
        assert error<2,error
        preview_errors.append({'frame':f,'mean_absolute_rgb_error':error})
    inventory=[{'file':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report={'passed':True,'live_files_unchanged':len(baseline),'inherited_assets_byte_identical':len(inherited_files),
        'all_inherited_contract_values_preserved_except_pass_number':True,'layout':m['layout'],
        'calibration_max_axis_error_px':calibration['max_axis_error_px'],'vehicle_slice_pngs':len(names),'slices':slices,
        'lamp_variants':lamps,'cat_animations':cats,'spray':sprays,'depth_overlap':depth,
        'preview':preview,'preview_decoded_errors':preview_errors,
        'files':inventory,'file_count':len(inventory),'bytes':sum(e['bytes'] for e in inventory)}
    (QA/'final_validation.json').write_text(json.dumps(report,indent=2))
    print('PASS5_VALIDATION',json.dumps({k:v for k,v in report.items() if k not in ['files','slices','lamp_variants','cat_animations','spray','depth_overlap']}),flush=True)

if __name__=='__main__':main()
