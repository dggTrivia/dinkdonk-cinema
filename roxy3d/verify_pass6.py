"""Pass-6 artifact acceptance: contracts, sheets, projection, video and live hashes."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from pngio import read,predecode
from package_cat_pass5 import down_rgba
from finalize_loop import webm_metadata
import compose_pass4 as composition
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa6';OUT=ROOT/'out6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def keys(a,b,path='manifest'):
    if isinstance(a,dict):
        for k,v in a.items():assert k in b,(path,k);keys(v,b[k],path+'.'+k)
    elif isinstance(a,list):
        assert len(b)>=len(a),path
        for i,v in enumerate(a):keys(v,b[i],path+'['+str(i)+']')
def rectpoly(x,y,w,h):return np.array([[x,y],[x+w,y],[x+w,y+h],[x,y+h]],float)
def project(u,v,z):return [900+60*(u-v),350+30*(u+v)-z]
def overlaps(a,b):
    for p in [a,b]:
        for i in range(len(p)):
            edge=p[(i+1)%len(p)]-p[i];axis=np.array([-edge[1],edge[0]]);aa=a@axis;bb=b@axis
            if aa.max()<=bb.min() or bb.max()<=aa.min():return False
    return True

def main():
    m=json.loads((OUT/'manifest.json').read_text());old=json.loads((ROOT/'out5/manifest.json').read_text());keys(old,m)
    allowed={'pass','status','marquees','occluders','light_loop_bytes','light_loop_sha256','validation','prop_loops'}
    for k,v in old.items():
        if k not in allowed:assert m[k]==v,('old contract changed',k)
    assert m['prop_loops'][:-1]==old['prop_loops']
    for before,after in zip(old['occluders'],m['occluders']):
        expected=dict(before)
        if before['name']=='snack':expected['geometry_z_px']=[0.0,44.172]
        assert after==expected,('occluder contract changed',before['name'])
    measured=json.loads((QA/'geometry_bounds.json').read_text())
    for e in m['occluders']:
        for k,v in measured[e['name']].items():assert e[k]==v,('geometry bounds changed',e['name'],k)
    for k,v in old['validation'].items():assert m['validation'][k]==v
    baseline=json.loads((QA/'live_before.json').read_text(encoding='utf-8-sig'))
    actual={p.relative_to(ROOT).as_posix() for f in ['out','out2','out3','out4','out5'] for p in (ROOT/f).rglob('*') if p.is_file()}
    assert actual=={e['path'] for e in baseline}
    for e in baseline:assert sha(ROOT/e['path'])==e['sha256'],e['path']
    inherited=[];changed=[]
    for p in (ROOT/'out5').rglob('*'):
        if not p.is_file() or p.name=='manifest.json':continue
        rel=p.relative_to(ROOT/'out5');assert (OUT/rel).exists()
        (inherited if sha(p)==sha(OUT/rel) else changed).append(rel.as_posix())
        if rel.parts[0] in ['vehicles','vehicle_slices','cat','tyre_spray','prop_loops']:assert sha(p)==sha(OUT/rel),rel
    predecode(list(OUT.rglob('*.png'))+list(QA.glob('*decoded_f*.png')))
    composition.OUT=OUT
    for scale,suffix in [(1,''),(2,'@2x')]:
        base=read(OUT/('base'+suffix+'.png'));assert base.shape==(1080*scale,1920*scale,4)
        assert np.array_equal(base,read(OUT/('bg'+suffix+'.png')))
        assert np.array_equal(composition.assemble(read(OUT/('lit_bg'+suffix+'.png')),m,scale),read(OUT/('full'+suffix+'.png')))
        oldbase=read(ROOT/'out5'/('base'+suffix+'.png'))
        assert np.array_equal(base[40*scale:364*scale,1296*scale:1872*scale],oldbase[40*scale:364*scale,1296*scale:1872*scale]),'Billboard aperture changed'
        for e in m['occluders']:
            parent=read(OUT/(e['file'][:-4]+suffix+'.png'));recon=np.zeros_like(parent,np.uint16)
            for s in e['depth_slices']:
                a=read(OUT/(s['file'][:-4]+suffix+'.png'));x=(s['x']-e['x'])*scale;y=(s['y']-e['y'])*scale
                recon[y:y+a.shape[0],x:x+a.shape[1]]+=a
            assert np.array_equal(parent,recon),e['name']
    shapes=[];gaps=[]
    for e in m['marquees']:
        x,y=e['bottom_center'];w,h=e['inner_size'];shapes.append((e['screen'],'marquee',rectpoly(x-w/2-3,y-h-3,w+6,h+6)))
    for e in m['poster_frames']:
        a,c=e['along'];z0,z1=e['z_px'];a-=.035;c+=.035;z0-=3;z1+=3
        p=lambda t,z:project(0,t,z) if e['wall']=='u0' else project(t,0,z)
        shapes.append((e['screen'],'poster',np.array([p(a,z0),p(c,z0),p(c,z1),p(a,z1)])))
    for i,(wall,t) in enumerate([('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)],1):
        p=lambda a,z:project(0,a,z) if wall=='u' else project(a,0,z)
        poly=np.array([p(t-.55,0),p(t+.55,0),p(t+.55,114),p(t-.55,114)])
        shapes.append((i,'door',poly));mar=m['marquees'][i-1];gaps.append({'screen':i,'marquee_to_door_vertical_gap_px':float(poly[:,1].min()-mar['bottom_center'][1]-3)})
    for i,a in enumerate(shapes):
        for b in shapes[i+1:]:assert not overlaps(a[2],b[2]),('overlapping stack geometry',a[:2],b[:2])
    assert min(e['marquee_to_door_vertical_gap_px'] for e in gaps)>=10
    sheets=[]
    for kind,entries in [('door',m['door_anims']),('janitor',list(m['janitor'].values())),('umbrella',list(m['umbrella']['fold'].values())),('drip',[m['prop_loops'][-1]])]:
        for e in entries:
            lo=read(OUT/e['file']);hi=read(OUT/e['file_2x']);w=e['frame_width'];h=e['frame_height'];rows=math.ceil(e['frames']/e['columns'])
            assert lo.shape==(h*rows,w*e['columns'],4) and hi.shape==(h*rows*2,w*e['columns']*2,4),e['file']
            assert np.array_equal(down_rgba(hi),lo),('2x filter',e['file'])
            for i in range(e['frames']):
                x=i%e['columns']*w;y=i//e['columns']*h;a=lo[y:y+h,x:x+w]
                assert np.all(a[a[:,:,3]==0,:3]==0)
                if kind!='drip':assert max(a[0,:,3].max(),a[-1,:,3].max(),a[:,0,3].max(),a[:,-1,3].max())==0,('cell clipping',e['file'],i)
                if kind=='door' and i in [0,15]:assert a[:,:,3].max()==0
                if kind=='drip':assert max(a[0,:,:3].max(),a[-1,:,:3].max(),a[:,0,:3].max(),a[:,-1,:3].max())==0
            sheets.append({'file':e['file'],'frames':e['frames'],'dimensions_1x':[lo.shape[1],lo.shape[0]],'native_2x_verified':True})
    for color,e in m['umbrella']['open'].items():
        a=read(OUT/e['file']);fold=read(OUT/m['umbrella']['fold'][color]['file']);assert np.array_equal(a,fold[:e['h'],:e['w']])
    door_replacements=[]
    for e in m['door_anims']:
        if e['door']=='wc':continue
        sheet=read(OUT/e['file_2x']);w=e['frame_width']*2;h=e['frame_height']*2;opened=sheet[h*2:h*3,:w]
        raw=read(QA/'doors_raw'/str(e['door'])/'f008.png')
        wall,at=[('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)][e['door']-1]
        for side in [-1,1]:
            px,py=project(.078,at+side*.24,79) if wall=='u' else project(at+side*.24,.078,79)
            x=int((px-e['x'])*2);y=int((py-e['y'])*2)
            assert opened[y,x,3]==255 and np.array_equal(opened[y,x,:3],raw[y,x,:3]),('closed porthole ghost',e['door'],side)
        poster=m['poster_frames'][e['door']-1];t=sum(poster['along'])/2;z=sum(poster['z_px'])/2
        px,py=project(0,t,z) if wall=='u' else project(t,0,z);x=int((px-e['x'])*2);y=int((py-e['y'])*2)
        if 0<=x<w and 0<=y<h:assert opened[y,x,3]==0,('poster painted over',e['door'])
        door_replacements.append({'door':e['door'],'old_porthole_positions_match_open_render':True,'poster_excluded':True})
    for e in m['janitor'].values():
        if 'stride_tiles' in e:assert e['stride_tiles']==.48 and e['frames']/e['fps']==1
    checks={}
    for name in ['characters_validation','doors_validation','drip_validation','slice_validation','loop_validation','scene_contract_validation','calibration']:
        report=json.loads((QA/(name+'.json')).read_text());assert report['passed'],name;checks[name]=report
    video=webm_metadata(OUT/m['light_loop']);assert video['codec_id']=='V_VP9' and video['width']==1920 and video['height']==1080 and abs(video['seconds']-5)<.05
    assert sha(OUT/m['light_loop'])==m['light_loop_sha256'] and (OUT/m['light_loop']).stat().st_size==m['light_loop_bytes']
    video_checks=[]
    for f in [0,1,30,60,90,118,119]:
        a=read(QA/('decoded_f'+str(f).zfill(3)+'.png'));src=read(QA/'loop_frames'/('f'+str(f).zfill(3)+'.png'))
        error=float(np.abs(a[:,:,:3].astype(np.int16)-src[:,:,:3]).mean());ap=a[40:364,1296:1872,:3]
        interior=ap[8:-8,8:-8]
        assert error<1.4 and ap.max()<=3 and ap.mean()<.001 and interior.max()<=1 and interior.mean()<.0001
        video_checks.append({'frame':f,'mae_8bit':error,'billboard_max_8bit':int(ap.max()),
            'billboard_mean_8bit':float(ap.mean()),'billboard_interior_max_8bit':int(interior.max()),'billboard_interior_mean_8bit':float(interior.mean())})
    preview=[]
    for f in [0,24,48,71,100,143]:
        a=read(QA/('preview_decoded_f'+str(f).zfill(3)+'.png'));src=read(QA/'preview_frames'/('f'+str(f).zfill(3)+'.png'))
        error=float(np.abs(a[:,:,:3].astype(np.int16)-src[:,:,:3]).mean());assert error<2.5
        preview.append({'frame':f,'mae_8bit':error})
    inventory=[{'file':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    result={'passed':True,'live_files_verified_unchanged':len(baseline),'previous_keys_preserved':True,'unchanged_inherited_assets':inherited,'updated_inherited_assets':changed,
        'static_rectangles_footprints_and_slices_unchanged':True,'stack_geometry_overlap':False,'marquee_door_gaps':gaps,'sheet_checks':sheets,
        'calibration_max_axis_error_px':checks['calibration']['max_axis_error_px'],'carpet_identical_to_pass4':True,'carpet_objects':checks['scene_contract_validation']['carpet_objects'],
        'door_replacement_checks':door_replacements,'ambient_decode':video_checks,'preview_decode':preview,'output_file_count':len(inventory),'output_bytes':sum(e['bytes'] for e in inventory),'inventory':inventory}
    (QA/'final_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k in ['passed','live_files_verified_unchanged','output_file_count','output_bytes','calibration_max_axis_error_px']}),flush=True)

if __name__=='__main__':main()
