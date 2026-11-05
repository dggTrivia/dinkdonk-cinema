"""Visual checks from delivered assets: actual depth sorting, lamps and cat cells."""
from pathlib import Path
import json,subprocess,argparse,math
import numpy as np
from pngio import read,write,predecode
from package_vehicles import blend,project,bounds

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa5';OUT=ROOT/'out5'

def annotate(source,target,items):
    path=QA/'annotation_job.json';path.write_text(json.dumps({'input':str(source),'output':str(target),'items':items}))
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass5.ps1'),'-Spec',str(path)],check=True)

def backing(w,h,color=(24,25,35)):
    a=np.full((h,w,4),255,np.uint8);a[:,:,:3]=color;return a

def walker(color):
    yy,xx=np.indices((52,42),dtype=np.float32);a=np.zeros((52,42,4),np.uint8)
    mask=((xx-21)**2+(yy-16)**2<15**2)|((xx>12)&(xx<30)&(yy>20)&(yy<46))
    a[mask,:3]=color;a[mask,3]=255
    for x in [16,26]:
        eye=(xx-x)**2+(yy-14)**2<4**2;a[eye,:3]=255;a[eye,3]=255
        pupil=(xx-x-1)**2+(yy-14)**2<2**2;a[pupil,:3]=15
    return a

def vehicle_scene(m,kind,direction,state='light',sliced=True,proxies=False,opened=False,spray_frame=None):
    a=read(OUT/'lit_bg.png');entry=m['vehicles'][kind][direction]
    variant=entry.get('door_open',entry) if opened else entry;u,v=6,11
    x,y=project(u,v)-entry['anchor'];blend(a,read(OUT/variant[state]),x,y,True)
    if spray_frame is not None:
        e=m['tyre_spray'][direction];f=1 if direction=='+u' else -1
        px,py=project(u-f*entry['length_tiles']*.32,v+entry['width_tiles']/2)
        blend(a,cell(e,spray_frame),px-e['anchor'][0],py-e['anchor'][1],True)
    stack=[(e['z_index'],e['x'],e['y'],read(OUT/e['file'])) for e in m['render_layers']]
    if sliced:
        for s in variant['slices']:stack.append((1000+round((u+s['du']+v)*100),x+s['x'],y+s['y'],read(OUT/s['file'])))
    else:stack.append((1000+round((u+v)*100),x,y,read(OUT/variant['file'])))
    if proxies:
        for uu,vv,color in [(6.85,10.55,(248,199,75)),(5.15,11.5,(107,236,220))]:
            px,py=project(uu,vv);stack.append((1000+round((uu+vv)*100),px-21,py-52,walker(color)))
    for z,xx,yy,im in sorted(stack,key=lambda e:e[0]):blend(a,im,xx,yy)
    return a

def vehicle_checks(m):
    predecode([OUT/e['file'] for e in m['render_layers']])
    cells=[];labels=[];stats=[]
    for row,(kind,direction) in enumerate((k,d) for k in m['vehicles'] for d in ['+u','-u']):
        for col,state in enumerate(['light','light_brake','light_indicator']):
            if state not in m['vehicles'][kind][direction]:state='light_brake'
            a=vehicle_scene(m,kind,direction,state);cell=a[700:1030,315:915]
            cells.append(cell);labels.append({'type':'text','x':col*600+8,'y':row*330+8,'text':kind+' '+direction+' | '+state,'size':16})
    grid=np.concatenate([np.concatenate(cells[i:i+3],axis=1) for i in range(0,len(cells),3)],axis=0)
    write(QA/'lamps_raw.png',grid);annotate(QA/'lamps_raw.png',QA/'vehicle_lights_check.png',labels)
    panels=[];labels=[]
    for row,direction in enumerate(['+u','-u']):
        before=vehicle_scene(m,'bus',direction,proxies=True,sliced=False)
        after=vehicle_scene(m,'bus',direction,proxies=True,sliced=True)
        changed=int(np.any(before!=after,axis=2).sum());assert changed>30,(direction,changed)
        stats.append({'direction':direction,'changed_pixels_with_52px_proxies':changed})
        for col,(label,a) in enumerate([('CENTRE SORT',before),('LENGTH SLICES',after)]):
            panels.append(np.repeat(np.repeat(a[740:960,415:790],2,axis=0),2,axis=1))
            labels.append({'type':'text','x':col*750+10,'y':row*440+10,'text':direction+' | '+label,'size':19})
    grid=np.concatenate([np.concatenate(panels[:2],axis=1),np.concatenate(panels[2:],axis=1)],axis=0)
    write(QA/'depth_raw.png',grid);annotate(QA/'depth_raw.png',QA/'vehicle_depth_check.png',labels)
    (QA/'depth_overlap_validation.json').write_text(json.dumps({'passed':True,'proxy_height_px':52,'positions':[[6.85,10.55],[5.15,11.5]],'checks':stats},indent=2))
    # All twelve closed/open variants, with colours showing ownership along u.
    cells=[];labels=[];colors=[(242,143,80),(91,213,197),(167,138,239)]
    for kind,directions in m['vehicles'].items():
        for direction,e in directions.items():
            for variant,label in [(e,'closed')]+([(e['door_open'],'open')] if 'door_open' in e else []):
                a=np.zeros((e['h'],e['w'],4),np.uint8)
                for i,s in enumerate(variant['slices']):
                    tile=read(OUT/s['file']);tile[:,:,:3]=colors[i%3];tile[tile[:,:,3]==0,:3]=0
                    blend(a,tile,s['x'],s['y'])
                body=read(OUT/variant['file']);x0,y0,x1,y1=bounds(body[:,:,3]>12,3)
                # Reset background opacity introduced by compositing to opaque chart backing.
                a[:,:,3]=body[:,:,3];a=a[y0:y1,x0:x1]
                tile=backing(520,420);blend(tile,np.repeat(np.repeat(a,2,0),2,1),20,45)
                i=len(cells);labels.append({'type':'text','x':i%3*520+12,'y':i//3*420+10,'text':kind+' '+direction+' '+label,'size':18});cells.append(tile)
    grid=np.concatenate([np.concatenate(cells[i:i+3],1) for i in range(0,len(cells),3)],0)
    write(QA/'slices_raw.png',grid);annotate(QA/'slices_raw.png',QA/'vehicle_slices_check.png',labels)

def cell(e,index,scale=1):
    a=read(OUT/e['file' if scale==1 else 'file_2x']);w=e['frame_width']*scale;h=e['frame_height']*scale
    x=index%e['columns']*w;y=index//e['columns']*h
    return a[y:y+h,x:x+w]

def cat_checks(m):
    cells=[];labels=[]
    for row,(name,e) in enumerate(m['cat'].items()):
        for col,f in enumerate([0,e['frames']//4,e['frames']//2,e['frames']*3//4,e['frames']-1]):
            a=backing(256,280);im=cell(e,f,2);blend(a,np.repeat(np.repeat(im,2,0),2,1),0,24)
            labels.append({'type':'text','x':col*256+6,'y':row*280+5,'text':name+' '+str(f),'size':14});cells.append(a)
    grid=np.concatenate([np.concatenate(cells[i:i+5],1) for i in range(0,len(cells),5)],0)
    write(QA/'cat_contact_raw.png',grid);annotate(QA/'cat_contact_raw.png',QA/'cat_contact_sheet.png',labels)
    bg=read(OUT/'lit_bg.png');stack=[(e['z_index'],e['x'],e['y'],read(OUT/e['file'])) for e in m['render_layers']]
    positions=[('sleep',10.75,7.75),('sit',5.5,8.25),('walk_plus_u',8.3,7.1),('walk_plus_v',10.9,6.5)]
    for name,u,v in positions:
        e=m['cat'][name];x,y=project(u,v)-e['anchor'];stack.append((1000+round((u+v)*100),x,y,cell(e,0)))
    for z,x,y,a in sorted(stack,key=lambda e:e[0]):blend(bg,a,x,y)
    write(QA/'cats_in_scene.png',bg)
    spray_panels=[];spray_labels=[]
    for row,direction in enumerate(['+u','-u']):
        for col,f in enumerate([3,5,8]):
            a=vehicle_scene(m,'taxi',direction,spray_frame=f)
            spray_panels.append(a[760:990,415:795])
            spray_labels.append({'type':'text','x':col*380+8,'y':row*230+8,'text':direction+' | spray '+str(f),'size':16})
    grid=np.concatenate([np.concatenate(spray_panels[:3],1),np.concatenate(spray_panels[3:],1)],0)
    write(QA/'spray_raw.png',grid);annotate(QA/'spray_raw.png',QA/'tyre_spray_check.png',spray_labels)
    # Fifteen seconds is a common period of the 3s idles and 10-frame/12fps walks.
    still=read(OUT/'full.png')
    coverage=np.zeros((128,128),bool)
    for e in m['cat'].values():
        sheet=read(OUT/e['file_2x']);coverage|=(sheet[:,:,3].reshape(e['rows'],128,e['columns'],128)>0).any(axis=(0,2))
    cx0,cy0,cx1,cy1=bounds(coverage,2)
    factor=min(160/(cx1-cx0),145/(cy1-cy0))
    xs=np.minimum(cx1-cx0-1,(np.arange(int((cx1-cx0)*factor))/factor).astype(int))
    ys=np.minimum(cy1-cy0-1,(np.arange(int((cy1-cy0)*factor))/factor).astype(int))
    overlay=np.zeros((720,1280,4),np.uint8);write(QA/'preview_labels_raw.png',overlay)
    labels=[{'type':'text','x':j*180+12,'y':8,'text':name.replace('walk_','').replace('_',' '),'size':16} for j,name in enumerate(m['cat'])]
    labels += [{'type':'text','x':24,'y':210,'text':'WHEEL SPRAY +u / -u','size':17},
               {'type':'text','x':330,'y':185,'text':'NATIVE STRIDE: 0.32 TILES / CYCLE','size':14}]
    annotate(QA/'preview_labels_raw.png',QA/'preview_labels.png',labels);predecode([QA/'preview_labels.png']);overlay=read(QA/'preview_labels.png')
    for i in range(360):
        panel=backing(1280,720);blend(panel,still[::2,::2],320,180)
        for j,(name,e) in enumerate(m['cat'].items()):
            e=m['cat'][name];f=min(e['frames']-1,int(i/24*e['fps'])) if not e['loop'] else int(i/24*e['fps'])%e['frames']
            im=cell(e,f,2)[cy0:cy1,cx0:cx1];im=im[ys[:,None],xs[None,:]]
            blend(panel,im,j*180+(180-im.shape[1])//2,30)
        # Native-size cat actually translates by stride_tiles each cycle.
        e=m['cat']['walk_plus_u'];f=int(i/24*e['fps'])%e['frames'];u=6+i/24*e['stride_tiles']*e['fps']/e['frames']
        px,py=project(u,8.35)/2+np.array([320,180]);im=cell(e,f)[::2,::2]
        blend(panel,im,px-e['anchor'][0]/2,py-e['anchor'][1]/2)
        for direction,y in [('+u',260),('-u',420)]:
            e=m['tyre_spray'][direction];f=i%24
            if f<12:blend(panel,cell(e,f,2),50,y,True)
        blend(panel,overlay,0,0)
        write(QA/'preview_frames'/('f'+str(i).zfill(3)+'.png'),panel)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--vehicles-only',action='store_true');ap.add_argument('--cat-only',action='store_true');args=ap.parse_args()
    m=json.loads(((QA/'manifest_vehicles.json') if args.vehicles_only else OUT/'manifest.json').read_text())
    if not args.cat_only:vehicle_checks(m)
    if not args.vehicles_only:cat_checks(m)
    print('PASS5_VISUAL_QA_READY',flush=True)

if __name__=='__main__':main()
