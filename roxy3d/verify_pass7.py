"""Acceptance checks on delivered pixels, inherited contracts, and live SHA-256s."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from pngio import read,predecode
from package_cat_pass5 import down_rgba
from package_pass7 import vehicle_variants
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa7';OUT=ROOT/'out7'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def additive_contract(old,new,path='manifest'):
    """Every inherited value remains identical, not just its key or type."""
    if isinstance(old,dict):
        assert isinstance(new,dict),path
        for k,v in old.items():
            assert k in new,(path,k);additive_contract(v,new[k],path+'.'+k)
    elif isinstance(old,list):
        assert isinstance(new,list) and len(old)==len(new),path
        for i,v in enumerate(old):additive_contract(v,new[i],path+'['+str(i)+']')
    else:assert old==new,(path,old,new)

def main():
    m=json.loads((OUT/'manifest.json').read_text());old=json.loads((ROOT/'out6/manifest.json').read_text())
    additive_contract(old,m);assert m['asset_pack_pass']==7 and m['layout']==2 and m['status']=='complete'
    baseline=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    paths={p.relative_to(ROOT).as_posix() for f in ['out','out2','out3','out4','out5','out6'] for p in (ROOT/f).rglob('*') if p.is_file()}
    assert paths=={e['path'] for e in baseline},'Live inventory changed'
    for e in baseline:
        p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
    inherited=[]
    for p in (ROOT/'out6').rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            rel=p.relative_to(ROOT/'out6');assert sha(p)==sha(OUT/rel),str(rel);inherited.append(rel.as_posix())
    required={'popcorn':(16,20,[8,18]),'soda':(12,18,[6,16]),'stub':(12,8,[6,4]),'ticket':(18,11,[9,5.5]),'cap_cashier':(28,12,[14,10]),'cap_usher':(28,12,[14,10])}
    assert set(m['items'])==set(required)
    new_files=[];item_rows=[]
    meta=json.loads((QA/'items_metadata.json').read_text())
    predecode(list((QA/'items_raw').glob('*.png'))+list(QA.glob('preview_decoded_f*.png')))
    for name,e in m['items'].items():
        w,h,anchor=required[name];assert (e['w'],e['h'],e['anchor'])==(w,h,anchor)
        lo=read(OUT/e['file']);hi=read(OUT/e['file_2x']);raw=read(QA/'items_raw'/(name+'@4x.png'))
        assert raw.shape==(h*4,w*4,4) and hi.shape==(h*2,w*2,4) and lo.shape==(h,w,4),name
        assert np.array_equal(down_rgba(raw),hi) and np.array_equal(down_rgba(hi),lo),name
        row={'name':name,'w':w,'h':h,'anchor':anchor,'scales':[]}
        for scale,key,a in [(1,'file',lo),(2,'file_2x',hi)]:
            assert np.count_nonzero(a[:,:,3])>10 and a[:,:,3].max()==255,name
            assert not a[a[:,:,3]==0,:3].any(),name
            border=np.concatenate([a[0,:,3],a[-1,:,3],a[:,0,3],a[:,-1,3]])
            assert not border.any(),('Nontransparent item border',name,scale,int(border.max()))
            yy,xx=np.where(a[:,:,3]>16)
            bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
            assert abs((bbox[0]+bbox[2])/2/scale-anchor[0])<1,name
            if name in ['stub','ticket']:
                assert abs((bbox[1]+bbox[3])/2/scale-anchor[1])<.6,name
            else:
                assert abs(bbox[3]/scale-anchor[1])<.6,name
                x=int(anchor[0]*scale);y=int(anchor[1]*scale)-1
                assert a[y,max(0,x-scale):x+scale+1,3].max()>100,('Missing attachment edge',name,scale)
            row['scales'].append({'scale':scale,'visible_bbox_alpha_gt_16':bbox,'transparent_border':True})
            new_files.append(e[key])
        item_rows.append(row)
    lamp_rows=[]
    for name,parent,e in vehicle_variants(m):
        assert e['anchor']==parent['anchor'] and e['w']==parent['w'] and e['h']==parent['h']
        for scale,key in [(1,''),(2,'_2x')]:
            normal=read(OUT/e['light'+key])[:,:,:3].astype(np.int16)
            indicator=read(OUT/e['light_indicator'+key])[:,:,:3].astype(np.int16)
            brake=read(OUT/e['light_brake'+key])[:,:,:3].astype(np.int16)
            a=read(OUT/e['light_indicator_only'+key]);delta=a[:,:,:3].astype(np.int16)
            assert a.shape==(parent['h']*scale,parent['w']*scale,4),name
            assert np.all(a[:,:,3]==255) and delta.max()>20,name
            assert np.array_equal(delta,np.maximum(indicator-normal,0)),name
            assert np.array_equal(np.minimum(normal+delta,255),indicator),name
            assert not delta[(indicator==normal).all(axis=2)].any(),name
            combined=np.minimum(brake+delta,255)
            assert np.array_equal(combined,np.minimum(brake+np.maximum(indicator-normal,0),255)),name
            assert not any(v.any() for v in [delta[0],delta[-1],delta[:,0],delta[:,-1]]),name
            energy=delta.sum(axis=(0,1));assert energy[0]>energy[1]>energy[2],name
            lamp_rows.append({'name':name,'scale':scale,'w':parent['w']*scale,'h':parent['h']*scale,
                              'anchor':parent['anchor'],'difference_max_error':0,'normal_reconstruction_max_error':0,
                              'brake_combination_max_error':0,'rgb_energy':energy.tolist()})
            new_files.append(e['light_indicator_only'+key])
    assert len(set(new_files))==28
    actual={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}
    assert actual==set(inherited+new_files+['manifest.json']),('Unexpected or missing output',actual.symmetric_difference(set(inherited+new_files+['manifest.json'])))
    calib=json.loads((QA/'calibration.json').read_text());assert calib['passed'] and calib['max_axis_error_px']<1
    movie=json.loads((QA/'preview_metadata.json').read_text());assert movie['frames']==96 and movie['fps']==24 and movie['size']==[1280,720]
    decoded=[]
    for i in movie['decoded_frames']:
        actual_frame=read(QA/('preview_decoded_f'+str(i).zfill(3)+'.png'))
        source=read(QA/'preview_frames'/('f'+str(i).zfill(3)+'.png'))
        error=np.abs(actual_frame[:,:,:3].astype(float)-source[:,:,:3])
        assert error.mean()<5,(i,error.mean())
        decoded.append({'frame':i,'mean_rgb_error_255':float(error.mean()),'p99_rgb_error_255':float(np.percentile(error,99))})
    inventory=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report={'passed':True,'layout':2,'asset_pack_pass':7,'all_inherited_manifest_values_unchanged':True,
            'live_files_verified':len(baseline),'inherited_assets_byte_identical':len(inherited),'new_pngs':len(new_files),
            'output_files':len(inventory),'output_bytes':sum(e['bytes'] for e in inventory),
            'items':item_rows,'indicators':lamp_rows,'calibration_max_axis_error_px':calib['max_axis_error_px'],
            'preview':movie,'decoded_preview_checks':decoded,'inventory':inventory}
    (QA/'final_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS7_VALIDATED',json.dumps({k:v for k,v in report.items() if k not in ['items','indicators','preview','decoded_preview_checks','inventory']}),flush=True)

if __name__=='__main__':main()
