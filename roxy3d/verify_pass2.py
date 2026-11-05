"""Layout, depth, aperture and live-output protection checks for pass 2."""
from pathlib import Path
import sys,json,hashlib,math,struct
import numpy as np
from pngio import read,write,predecode
from package_pass2 import assemble,validate
from package_layers import over

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out2';QA=ROOT/'qa2'
EXPECTED={'partition_left':[2.9,4.4,3.1,9],'partition_right':[4.4,2.9,13,3.1],
 'boxoffice':[3.8,5,4.4,8.4],'snack':[5.6,4,11.6,4.6],'podium':[4.55,3.55,5,4],
 'bench':[11.2,6,12.6,6.4],'arcade':[12,7.5,12.7,8.2],
 'standee_1':[12.2,5,12.62,5.06],'standee_2':[7.2,8.5,7.62,8.56],
 'palm':[12.3,3.4,12.8,3.9]}

def p(u,v,z=0):return np.array([900+(u-v)*60,350+(u+v)*30-z])
def line(im,a,b,color,width=0):
    for t in np.linspace(0,1,max(2,int(np.linalg.norm(np.array(b)-a)*2))):
        x,y=np.round(np.array(a)+(np.array(b)-a)*t).astype(int)
        im[max(0,y-width):min(im.shape[0],y+width+1),max(0,x-width):min(im.shape[1],x+width+1),:3]=color
def poly(im,pts,color):
    for a,b in zip(pts,pts[1:]+pts[:1]):line(im,a,b,color)
def cross(im,pt,color):
    line(im,pt+[-5,0],pt+[5,0],color);line(im,pt+[0,-5],pt+[0,5],color)

def avatar(color):
    a=np.zeros((52,42,4),np.uint8);yy,xx=np.indices(a.shape[:2])
    head=((xx-21)/18)**2+((yy-19)/18)**2<1
    body=(yy>28)&(yy<48)&(abs(xx-21)<12-(yy-32)*.12)
    a[head|body,:3]=color;a[head|body,3]=255
    for x in [15,27]:a[((xx-x)**2+(yy-17)**2)<6,:3]=[20,20,30]
    return a

def main():
    m=json.loads((OUT/'manifest.json').read_text());assert m['layout']==2
    entries={e['name']:e for e in m['occluders']}
    for name,fp in EXPECTED.items():assert np.allclose(entries[name]['footprint'],fp,rtol=0,atol=1e-9),(name,entries[name]['footprint'])
    for name in ['partition_left','partition_right']:assert entries[name]['height_px']==90
    assert entries['snack']['height_px']==44 and entries['boxoffice']['height_px']==84
    assert len(entries)==18
    calibration=json.loads((QA/'calibration.json').read_text());assert calibration['passed']
    before=json.loads((QA/'live_out_before.json').read_text(encoding='utf-8-sig'));after=[]
    for e in before:
        path=Path(e['path']);digest=hashlib.sha256(path.read_bytes()).hexdigest().upper()
        assert digest==e['hash'] and path.stat().st_size==e['length'],str(path)
        after.append(path)
    assert len([p for p in (ROOT/'out').rglob('*') if p.is_file()])==len(before),'Live output inventory changed'
    validate(m)
    im=read(OUT/'full.png')
    for name,fp in EXPECTED.items():
        a,c,d,e=fp;poly(im,[p(a,c),p(d,c),p(d,e),p(a,e)],[255,210,70])
    for wall,at in [('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)]:
        c=p(0,at,124) if wall=='u' else p(at,0,124)
        poly(im,[c+[-88,0],c+[-88,-92],c+[88,-92],c+[88,0]],[255,255,0])
        a=at-1.55 if wall=='u' else at+.75
        pts=[p(0,a,23),p(0,a,128),p(0,a+.8,128),p(0,a+.8,23)] if wall=='u' else [p(a,0,23),p(a,0,128),p(a+.8,0,128),p(a+.8,0,23)]
        poly(im,pts,[60,255,110])
    poly(im,[[1296,40],[1872,40],[1872,364],[1296,364]],[255,235,0])
    positions=m['staff_positions']['cashiers']+m['staff_positions']['snack_clerks']+[m['staff_positions']['usher']]
    for u,v in positions:cross(im,p(u,v),[255,255,255])
    write(QA/'registration.png',im)
    # Concrete DOM-stack witness using 50px stand-ins at all staff/customer points.
    bg=read(OUT/m.get('base',m['bg']));draw=[]
    for e in m['render_layers']:draw.append((e['z_index'],read(OUT/e['file']),e['x'],e['y']))
    positions+=[(4.85,7.4),(4.85,6),(5.85,7.4),(6.85,7.4),(6.6,5.05),(8.2,5.05),(9.8,5.05),(1.4,6.4),(8.2,1.4)]
    for i,(u,v) in enumerate(positions):
        x,y=p(u,v).astype(int);draw.append((1000+round((u+v)*100),avatar([240,183,65] if i<6 else [117,214,171]),x-21,y-50))
    for _,a,x,y in sorted(draw,key=lambda t:t[0]):over(bg,a,x,y)
    write(QA/'staff_depth_witness.png',bg)
    big=read(OUT/'full@2x.png')
    for name,bounds in [('tickets',[580,495,875,755]),('snack',[950,505,1450,835]),('palm_bench',[1160,710,1500,970]),('street',[210,650,960,1040])]:
        x,y,x1,y1=bounds;write(QA/('detail_'+name+'.png'),big[y*2:y1*2,x*2:x1*2])
    report={'passed':True,'layout':2,'exact_requested_footprints':list(EXPECTED),'whole_occluders':len(entries),
        'depth_slices':len(m['render_layers']),'calibration_max_axis_error_px':calibration['max_axis_error_px'],
        'live_out_unchanged':True,'live_files_verified':len(before)}
    (QA/'layout_validation.json').write_text(json.dumps(report,indent=2));print('PASS2_QA',json.dumps(report),flush=True)
    if m.get('status')=='complete':
        inventory=[]
        for path in sorted(OUT.rglob('*')):
            if path.is_file():
                data=path.read_bytes();inventory.append({'file':path.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        expected={'manifest.json','light_loop.webm','bg.png','bg@2x.png','base.png','base@2x.png','full.png','full@2x.png'}
        for e in m['occluders']+m['render_layers']:
            expected.add(e['file']);expected.add(e['file'][:-4]+'@2x.png')
        assert {e['file'] for e in inventory}==expected,'Unexpected or missing final output'
        delivery={'passed':True,**report,'status':m['status'],'files':inventory,
            'png_count':sum(e['file'].endswith('.png') for e in inventory),
            'total_bytes':sum(e['bytes'] for e in inventory),'loop_bytes':m['light_loop_bytes'],
            'loop_seconds':m['loop_seconds'],'fps':m['fps'],
            'video_validation':json.loads((QA/'video_validation.json').read_text())}
        (QA/'final_delivery.json').write_text(json.dumps(delivery,indent=2))
        print('FINAL_INVENTORY',delivery['png_count'],len(inventory),delivery['total_bytes'],flush=True)

if __name__=='__main__':main()
