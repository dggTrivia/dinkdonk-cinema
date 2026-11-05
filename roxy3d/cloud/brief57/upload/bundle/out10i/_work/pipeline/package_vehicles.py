"""Crop, package, and inspect pass 3 without writing either live output folder."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import numpy as np
from pngio import read, write, predecode
from package_layers import boxblur

ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa3';LIVE=ROOT/'out2';OUT=ROOT/'out3'

def at2(name):return name[:-4]+'@2x.png'
def project(u,v,z=0):return np.array([900+(u-v)*60,350+(u+v)*30-z])

def blend(dst,src,x,y,add=False):
    x,y=int(round(x)),int(round(y));h,w=src.shape[:2]
    dx,dy=max(0,x),max(0,y);ex,ey=min(dst.shape[1],x+w),min(dst.shape[0],y+h)
    if ex<=dx or ey<=dy:return
    a=src[dy-y:ey-y,dx-x:ex-x];target=dst[dy:ey,dx:ex]
    if add:target[:,:,:3]=np.minimum(255,target[:,:,:3].astype(np.uint16)+a[:,:,:3]).astype(np.uint8)
    else:
        alpha=a[:,:,3:4].astype(np.float32)/255
        target[:,:,:3]=np.rint(a[:,:,:3]*alpha+target[:,:,:3]*(1-alpha)).astype(np.uint8)
    target[:,:,3]=255

def shadow_body(body,row):
    """Soft neutral contact shadow in straight RGBA, attached to ground anchor."""
    scale=row['scale'];x0,y0,_,_=row['border'];ax,ay=row['anchor_global']
    yy,xx=np.indices(body.shape[:2],dtype=np.float32)
    dx=(xx+.5)/scale+x0-ax;dy=(yy+.5)/scale+y0-ay
    u=dx/120+dy/60;v=dy/60-dx/120
    q=(u/(row['length_tiles']*.49))**8+(v/(row['width_tiles']*.50))**6
    shadow=.43*np.exp(-np.clip(q,0,50))
    alpha=body[:,:,3].astype(np.float32)/255
    combined=alpha+shadow*(1-alpha)
    rgb=body[:,:,:3].astype(np.float32)*alpha[:,:,None]/np.maximum(combined[:,:,None],1e-9)
    result=np.dstack([np.rint(rgb),np.rint(combined*255)]).astype(np.uint8)
    result[result[:,:,3]==0,:3]=0
    return result

def road_light(raw,row):
    """Finite moving light pool, retaining Cycles shadows and wet-road reflections."""
    scale=row['scale'];x0,y0,_,_=row['border'];ax,ay=row['anchor_global']
    yy,xx=np.indices(raw.shape[:2],dtype=np.float32)
    dx=(xx+.5)/scale+x0-ax;dy=(yy+.5)/scale+y0-ay
    u=dx/120+dy/60;v=dy/60-dx/120
    # Lighting cannot drag a broad rectangular receiver across the scene.
    # Smooth cutoff lies beyond the useful headlight cone, avoiding sprite edges.
    f=1 if row['direction']=='+u' else -1
    localu=u*f
    fade=np.clip((4.3-np.abs(localu))/1.3,0,1)*np.clip((1.7-np.abs(v))/.6,0,1)
    rgb=raw[:,:,:3].astype(np.float32)*fade[:,:,None]
    # Tiny lens halos, placed by the same projection as the actual lamps.
    L=row['length_tiles'];bus=row['kind']=='bus';popup=row['kind']=='sedan_b'
    for front in [True,False]:
        x=(L/2-(.11 if popup and front else 0))*(1 if front else -1)
        z=(28 if bus else 22.5 if popup else 15) if front else (30 if bus else 15)
        for vpos in [(-.27 if bus else -row['width_tiles']*.3),(.27 if bus else row['width_tiles']*.3)]:
            pos=project(6+f*x,11+f*vpos,z)
            dist=((xx+.5)/scale+x0-pos[0])**2+((yy+.5)/scale+y0-pos[1])**2
            color=np.array([1,.68,.3] if front else [1,.018,.025])
            rgb+=np.exp(-dist[:,:,None]/(2*3.2**2))*color*(23 if front else 17)
    rgb=np.clip(np.rint(rgb),0,255).astype(np.uint8)
    rgb[rgb.max(axis=2)<2]=0
    return np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)])

def bounds(mask,pad=4):
    yy,xx=np.nonzero(mask)
    assert len(xx)
    return [max(0,int(xx.min())-pad),max(0,int(yy.min())-pad),
            min(mask.shape[1],int(xx.max())+1+pad),min(mask.shape[0],int(yy.max())+1+pad)]

def crop_assets(rows,out):
    grouped={}
    predecode([QA/r.get('raw_dir','raw')/(r['name']+s+('@2x' if r['scale']==2 else '')+'.png') for r in rows for s in ['', '_light']])
    for row in rows:
        suffix='@2x' if row['scale']==2 else ''
        body=shadow_body(read(QA/row.get('raw_dir','raw')/(row['name']+suffix+'.png')),row)
        light=road_light(read(QA/row.get('raw_dir','raw')/(row['name']+'_light'+suffix+'.png')),row)
        grouped.setdefault((row['kind'],row['direction']),[]).append((row,body,light))
    vehicles={};records=[]
    for (kind,direction),variants in grouped.items():
        # Closed/open and both resolutions all share the identical logical canvas.
        union=np.zeros((400,610),bool)
        for row,body,light in variants:
            mask=(body[:,:,3]>0)|(light[:,:,:3].max(axis=2)>0)
            if row['scale']==2:mask=mask.reshape(400,2,610,2).any(axis=(1,3))
            union|=mask
        x0,y0,x1,y1=bounds(union)
        assert x0>0 and y0>0 and x1<610 and y1<400,('working border too small',kind,direction,[x0,y0,x1,y1])
        entry={'file':None,'light':None,'anchor':[300-x0,230-y0],
               'length_tiles':variants[0][0]['length_tiles'],'width_tiles':variants[0][0]['width_tiles'],
               'w':x1-x0,'h':y1-y0,'height_px':variants[0][0]['height_px'],
               'geometry_local_footprint':variants[0][0].get('geometry_local_footprint')}
        for row,body,light in variants:
            scale=row['scale'];suffix='@2x' if scale==2 else ''
            fn='vehicles/'+row['name']+suffix+'.png';ln='vehicles/'+row['name']+'_light'+suffix+'.png'
            a=body[y0*scale:y1*scale,x0*scale:x1*scale];l=light[y0*scale:y1*scale,x0*scale:x1*scale]
            write(out/fn,a);write(out/ln,l[:,:,:3])
            records.append({'file':fn,'light':ln,'scale':scale,'anchor':[v*scale for v in entry['anchor']],
                            'size':[a.shape[1],a.shape[0]],'crop_global':[300+x0,630+y0]})
            target=entry.setdefault('door_open',{}) if row['door_open'] else entry
            if row['door_open']:target['geometry_local_footprint']=row.get('geometry_local_footprint')
            if scale==1:target.update(file=fn,light=ln)
            else:target.update(file_2x=fn,light_2x=ln)
        if kind in ['bus','taxi']:
            f=1 if direction=='+u' else -1
            entry['door_ground_offset_tiles']=[f*(1.04 if kind=='bus' else -.23),f*(-.40 if kind=='bus' else -.31)]
            if 'door_open' in entry:
                entry['door_open'].update(anchor=entry['anchor'],w=entry['w'],h=entry['h'])
        vehicles.setdefault(kind,{})[direction]=entry
    (QA/'vehicle_crops.json').write_text(json.dumps(records,indent=2))
    return vehicles

def upscale2(a):
    # CSS pixel-centre bilinear enlargement, matching the existing pass-2 loop.
    h,w=a.shape[:2];ys=(np.arange(h*2)+.5)/2-.5;xs=(np.arange(w*2)+.5)/2-.5
    y0=np.floor(ys).astype(int);x0=np.floor(xs).astype(int)
    fy=(ys-y0).astype(np.float32);fx=(xs-x0).astype(np.float32)
    y1=np.clip(y0+1,0,h-1);x1=np.clip(x0+1,0,w-1);y0=np.clip(y0,0,h-1);x0=np.clip(x0,0,w-1)
    horiz=a[:,x0].astype(np.float32)*(1-fx[None,:,None])+a[:,x1].astype(np.float32)*fx[None,:,None]
    return np.rint(horiz[y0]*(1-fy[:,None,None])+horiz[y1]*fy[:,None,None]).astype(np.uint8)

def lit_background(scale=1):
    base=read(LIVE/('base@2x.png' if scale==2 else 'base.png'))
    loop=read(ROOT/'qa2'/'loop_frames'/'f060.png')
    if scale==2:loop=upscale2(loop)
    base[:,:,:3]=np.minimum(base[:,:,:3].astype(np.uint16)+loop[:,:,:3],255).astype(np.uint8)
    return base

def annotate(source,target,items):
    spec=QA/'annotation_job.json'
    spec.write_text(json.dumps({'input':str(source),'output':str(target),'items':items}))
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_vehicles.ps1'),'-Spec',str(spec)],check=True)

def checks(m,out,preview=False):
    entries=m['vehicles'];bg=lit_background();prefix='preview_' if preview else ''
    predecode([LIVE/e['file'] for e in m['render_layers']])
    placements=[];panels=[]
    # Three distinct positions for all eight model/direction combinations.
    for step in range(3):
        a=bg.copy();points=[]
        for direction,lane in [('+u',11),('-u',12)]:
            for i,kind in enumerate(['bus','taxi','sedan_a','sedan_b']):
                u=[-.3,3.05,6.0,8.85][i]+(-.65+step*.65)+(0.7 if direction=='-u' else 0)
                entry=entries[kind][direction];pos=project(u,lane)
                x,y=np.rint(pos-np.array(entry['anchor'])).astype(int)
                blend(a,read(out/entry['light']),x,y,True)
                points.append({'kind':kind,'direction':direction,'uv':[u,lane],'screen':pos.tolist(),
                    'sprite_xy':[int(x),int(y)],'anchor':entry['anchor'],
                    'placement_error_px':(np.array([x,y])+entry['anchor']-pos).tolist(),
                    'z_index':1000+round((u+lane)*100),'file':entry['file']})
        layers=[{'x':e['x'],'y':e['y'],'z_index':e['z_index'],'path':LIVE/e['file']} for e in m['render_layers']]
        layers += [{'x':p['sprite_xy'][0],'y':p['sprite_xy'][1],'z_index':p['z_index'],'path':out/p['file']} for p in points]
        for layer in sorted(layers,key=lambda e:e['z_index']):blend(a,read(layer['path']),layer['x'],layer['y'])
        write(QA/(prefix+f'scene_{step}.png'),a)
        panels.append(a);placements.append(points)
    # Full first scene plus two street close-ups: all 24 placements in one check.
    sheet=np.concatenate([panels[0],panels[1][480:],panels[2][480:]],axis=0)
    raw=QA/(prefix+'vehicles_check_unmarked.png');write(raw,sheet)
    annotations=[]
    for step,points in enumerate(placements):
        offset=0 if step==0 else 1080+(step-1)*600-480
        annotations.append({'type':'text','x':32,'y':(24 if step==0 else 1096+(step-1)*600),
            'text':f'PASS 3 | LANE / ANCHOR CHECK {step+1} | +u: v11.0   -u: v12.0','size':19})
        for lane,color in [(11,'#75fff0'),(12,'#ff78bd')]:
            start=project(-4,lane);end=project(13,lane)
            annotations.append({'type':'line','x':float(start[0]),'y':float(start[1]+offset),'x2':float(end[0]),'y2':float(end[1]+offset),'color':color})
        for p in points:
            x,y=p['screen'];y+=offset
            annotations.append({'type':'cross','x':x,'y':y,'color':'#ffffff'})
            annotations.append({'type':'text','x':x+10,'y':y+7,'text':p['kind']+' '+p['direction']+'  u='+str(round(p['uv'][0],2)),'size':11})
    annotate(raw,QA/(prefix+'vehicles_check.png'),annotations)
    (QA/(prefix+'placements.json')).write_text(json.dumps({'source':'out2/base.png + lossless light loop frame 60 + out2/render_layers',
        'panels':placements,'max_anchor_rounding_error_px':max(abs(v) for ps in placements for p in ps for v in p['placement_error_px'])},indent=2))
    # Tight, enlarged views on a neutral backing make vehicle details inspectable.
    cells=[];labels=[]
    for i,kind in enumerate(['bus','taxi','sedan_a','sedan_b']):
        for j,direction in enumerate(['+u','-u']):
            entry=entries[kind][direction];a=read(out/entry['file'])
            x0,y0,x1,y1=bounds(a[:,:,3]>8,5);a=a[y0:y1,x0:x1]
            a=np.repeat(np.repeat(a,2,axis=0),2,axis=1)
            cells.append((i,j,a));labels.append({'type':'text','x':j*540+20,'y':i*350+15,'text':kind+'  '+direction,'size':20})
    contact=np.full((1400,1080,4),255,np.uint8);contact[:,:,:3]=(30,31,42)
    for i,j,a in cells:blend(contact,a,j*540+(540-a.shape[1])//2,i*350+45)
    write(QA/(prefix+'contact_raw.png'),contact)
    annotate(QA/(prefix+'contact_raw.png'),QA/(prefix+'vehicle_contact_sheet.png'),labels)
    if not preview:
        arrivals=[];arrival_labels=[]
        for state in ['closed','open']:
            a=bg.copy();layers=[{'x':e['x'],'y':e['y'],'z_index':e['z_index'],'path':LIVE/e['file']} for e in m['render_layers']]
            for kind,stop in m['arrival_stops'].items():
                entry=entries[kind]['+u'];variant=entry if state=='closed' else entry['door_open']
                u,v=stop['vehicle_centre'];x,y=project(u,v)-entry['anchor']
                blend(a,read(out/variant['light']),x,y,True)
                layers.append({'x':x,'y':y,'z_index':1000+round((u+v)*100),'path':out/variant['file']})
            for layer in sorted(layers,key=lambda e:e['z_index']):blend(a,read(layer['path']),layer['x'],layer['y'])
            # Crop to the street, retaining both the shelter and cinema entrance.
            arrivals.append(a[490:1080,:1250])
            offset=(0 if state=='closed' else 590)-490
            arrival_labels.append({'type':'text','x':20,'y':20+(0 if state=='closed' else 590),'size':18,'text':'ARRIVALS | '+state.upper()+' | curb-side boarding points'})
            for kind,stop in m['arrival_stops'].items():
                pos=project(*stop['boarding_point']);x,y=pos.tolist()
                arrival_labels.append({'type':'cross','x':x,'y':y+offset,'color':'#75fff0'})
                arrival_labels.append({'type':'text','x':x+12,'y':y+offset-18,'size':12,'text':kind+' boarding '+str(stop['boarding_point'])})
        write(QA/'arrivals_raw.png',np.concatenate(arrivals,axis=0))
        annotate(QA/'arrivals_raw.png',QA/'arrivals_check.png',arrival_labels)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');args=ap.parse_args()
    rows=json.loads((QA/('render_preview.json' if args.preview else 'render_vehicles.json')).read_text())['renders']
    out=QA/'preview_assets' if args.preview else OUT;out.mkdir(exist_ok=True)
    if not args.preview:
        for path in LIVE.rglob('*'):
            if path.is_file() and path.name!='manifest.json':
                dest=out/path.relative_to(LIVE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    m=json.loads((LIVE/'manifest.json').read_text());m['vehicles']=crop_assets(rows,out)
    m['lanes']={'near':11.0,'far':12.0}
    m['vehicle_sprite_contract']={
        'anchor':'Ground point at middle of vehicle / lane centre, in logical 1x pixels. Position top-left at P(u,v)-anchor.',
        'resolution':'@2x images have exactly twice the pixels. Use the 1x CSS w/h and anchor, or multiply all coordinates by two on a 2x canvas.',
        'alpha':'Body: straight RGBA with soft contact shadow. Light: RGB on black, plus-lighter under all vehicles and walkers.',
        'crop':'Closed body, open body and their light images share w/h and anchor within each direction. The common tight crop includes the light reach.',
        'depth':'Place body with z_index = 1000 + round((u+v)*100); road-light layers go below all bodies and static occluders.',
        'direction':'True 180-degree 3D rotation, not mirrored images; destination and TAXI text remain legible.',
        'door':'Optional door_open files replace the closed pair at the identical anchor. The entry is on local -v (curb side for +u).'}
    m['arrival_stops']={'bus':{'direction':'+u','vehicle_centre':[.16,11.0],'door_ground':[1.20,10.60],
                             'boarding_point':[1.20,10.75]},
                        'taxi':{'direction':'+u','vehicle_centre':[9.73,11.0],'door_ground':[9.50,10.69],
                                'boarding_point':[9.50,10.75]}}
    m['vehicle_baked_signs']=['bus front and rear: 95 ROXY','bus sides: 95 / ROXY TRANSIT','taxi roof: TAXI','sedan number plates: RXY 95']
    if not args.preview:
        for scale,suffix in [(1,''),(2,'@2x')]:write(out/('lit_bg'+suffix+'.png'),lit_background(scale))
        m['lit_bg']='lit_bg.png';m['lit_bg_2x']='lit_bg@2x.png';m['lit_bg_reference_frame']=60
        m['lit_bg_composition']='base + lossless light-loop frame 60, without occluders. Use instead of base+loop when video cannot play; still draw the occluders.'
        m['pass']=3;m['status']='complete'
        m['validation']['vehicles']='../qa3/vehicle_validation.json'
        m['validation']['vehicle_camera']='../qa3/calibration.json'
    checks(m,out,args.preview)
    target=out/'manifest.pending.json';target.write_text(json.dumps(m,indent=2));target.replace(out/'manifest.json')
    print('PACKAGED',out,flush=True)

if __name__=='__main__':main()
