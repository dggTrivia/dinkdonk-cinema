"""QA-only test content, placed using exactly the public wall and bus contracts."""
import json,math
import numpy as np
from pass9_common import ROOT,QA,OUT,status
from pngio import read,write,predecode
from package_vehicles import blend,project
from compose_pass9 import compose

def quad_art(q,scale=1):
    q=np.array(q,float);x=math.floor(q[:,0].min());y=math.floor(q[:,1].min());w=math.ceil(q[:,0].max())-x+1;h=math.ceil(q[:,1].max())-y+1
    yy,xx=np.indices((h*scale,w*scale),dtype=np.float32);xx=x+(xx+.5)/scale;yy=y+(yy+.5)/scale
    basis=np.stack([q[1]-q[0],q[3]-q[0]],axis=1);inv=np.linalg.inv(basis)
    u=inv[0,0]*(xx-q[0,0])+inv[0,1]*(yy-q[0,1]);v=inv[1,0]*(xx-q[0,0])+inv[1,1]*(yy-q[0,1]);inside=(u>=0)&(u<=1)&(v>=0)&(v<=1)
    parity=(np.floor(u*8)+np.floor(v*8)).astype(int)%2
    rgb=np.where(parity[:,:,None],np.array([82,149,184]),np.array([219,184,105]));rgb=np.broadcast_to(rgb,(*u.shape,3)).copy()
    arrow=(np.abs(v-.5)<.025)&(u>.10)&(u<.90);arrow|=(np.abs(v-.5)<(.90-u)*.65)&(u>.70)&(u<.90);rgb[arrow]=[238,244,230]
    a=np.dstack([rgb,inside*255]).astype(np.uint8);a[~inside,:3]=0
    return x,y,a

GLYPHS={'D':['11110','10001','10001','10001','10001','10001','11110'],'G':['01110','10001','10000','10111','10001','10001','01110'],'9':['01110','10001','10001','01111','00001','00001','01110'],'5':['11111','10000','10000','11110','00001','00001','11110'],' ':['00000']*7,'.':['00000']*5+['00100']*2}
def led_dots(canvas,e,scale):
    count=0
    for line,top,color in [('DGG 95',e['rows_px'][0][0],[255,145,35]),('9.5',e['rows_px'][1][0],[255,45,32])]:
        for j,char in enumerate(line):
            for row,bits in enumerate(GLYPHS[char]):
                for col,bit in enumerate(bits):
                    if bit!='1':continue
                    c=3+j*6+col;along=e['along'][1]-(c+.5)/73.4846922835 if e['wall']=='u0' else e['along'][0]+(c+.5)/73.4846922835
                    u,v=(e['offset'],along) if e['wall']=='u0' else (along,e['offset']);x,y=project(u,v,top-row-.5);xx=int(x*scale);yy=int(y*scale)
                    for dy in range(-2*scale,2*scale+1):
                        for dx in range(-2*scale,2*scale+1):
                            power=math.exp(-(((xx+dx+.5)/scale-x)**2+((yy+dy+.5)/scale-y)**2)/.25)
                            if 0<=yy+dy<canvas.shape[0] and 0<=xx+dx<canvas.shape[1]:canvas[yy+dy,xx+dx,:3]=np.minimum(255,canvas[yy+dy,xx+dx,:3].astype(float)+np.array(color)*power).astype(np.uint8)
                    count+=1
    return count

def main():
    manifest=OUT/'manifest.json' if (OUT/'manifest.json').exists() else QA/'manifest_vehicles.json'
    scale=2 if (QA/'decoded_light_loop_2x/f072.png').exists() else 1
    m=json.loads(manifest.read_text());a=compose(m,72,scale,True,test_ads=True);plain=compose(m,72,scale,True);pixel_checks=[]
    for ad in m['ad_surfaces']:
        q=np.array(ad['quad_px']);d=[]
        for s in [.15,.325,.5,.675,.85]:
            for t in [.15,.325,.5,.675,.85]:
                x,y=q[0]+(q[1]-q[0])*s+(q[3]-q[0])*t;ix=int(x*scale);iy=int(y*scale);d.append(float(np.abs(a[iy,ix,:3].astype(float)-plain[iy,ix,:3]).mean()))
        assert min(d)>5 and np.mean(d)>15,(ad['name'],d)
        pixel_checks.append(dict(name=ad['name'],visible_content_samples=25,min_mean_rgb_change=min(d),average_rgb_change=float(np.mean(d))))
    dots=sum(led_dots(a,e,scale) for e in m['led_signs']);write(QA/('interface_test_content'+('@2x' if scale==2 else '')+'.png'),a)
    canvas=np.zeros((900,1800,4),np.uint8);canvas[:,:,:3]=[29,35,43];canvas[:,:,3]=255;proof=[]
    for j,(direction,e) in enumerate(m['vehicles']['bus'].items()):
        for row,(name,v) in enumerate([('closed',e),('open',e['door_open'])]):
            body=read(OUT/v['file_2x']);x,y,art=quad_art(v['ad_panel_quad'],2);inside=art[:,:,3]>0
            target=body[y*2:y*2+art.shape[0],x*2:x*2+art.shape[1]];assert target.shape==art.shape
            covered=int(((target[:,:,3]>240)&inside).sum());total=int(inside.sum());assert covered/total>.98,(direction,name,covered,total)
            target[inside,:3]=art[inside,:3]
            blend(canvas,body,j*900+10,row*440+10);proof.append(dict(direction=direction,state=name,panel_pixels=total,opaque_body_coverage=covered/total))
    ownership=[]
    for name in ['tower','paste_wall']:
        ad=next(e for e in m['ad_surfaces'] if e['name']==name);q=np.array(ad['quad_px'])
        if name=='tower':uv=np.load(QA/'world_positions@2x.npz')['position'][:,:,:2];origin=[0,0]
        else:
            p=next(e for e in m['occluders'] if e['name']=='paste_wall');uv=np.load(QA/'positions/paste_wall@2x.npz')['uv'];origin=[p['x']*2,p['y']*2]
        errors=[]
        for s in [.15,.325,.5,.675,.85]:
            for t in [.15,.325,.5,.675,.85]:
                x,y=q[0]+(q[1]-q[0])*s+(q[3]-q[0])*t;point=uv[int(y*2)-origin[1],int(x*2)-origin[0]]
                errors.append(abs(float(point[1])-ad['offset']))
        assert max(errors)<.025,(name,max(errors));ownership.append(dict(name=name,visible_face_samples=25,max_plane_error_tiles=max(errors)))
    write(QA/'bus_ad_panel_check.png',canvas);(QA/'interface_validation.json').write_text(json.dumps(dict(passed=True,ads=3,led_signs=5,test_lit_dots=dots,bus_panels=proof,visible_ad_ownership=ownership,composited_ad_visibility=pixel_checks,content='QA checker/arrow and sample dots only; published ad/LED surfaces remain blank'),indent=2));status('QA content mapped through all three ad quads, five LED planes and four bus panel states; rendered ownership, composited content visibility and panel coverage validated')
if __name__=='__main__':main()
