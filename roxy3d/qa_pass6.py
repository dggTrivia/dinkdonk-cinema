"""Review the delivered sheets in contact sheets and a composited motion reel."""
from pathlib import Path
import json,subprocess,math
import numpy as np
from pngio import read,write,predecode
from package_vehicles import blend,project
from package_cat_pass5 import down_rgba
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa6';OUT=ROOT/'out6';CACHE={}

def asset(file):
    if file not in CACHE:CACHE[file]=read(OUT/file)
    return CACHE[file]
def cell(e,i,scale=1):
    a=asset(e['file_2x'] if scale==2 else e['file']);w=e['frame_width']*scale;h=e['frame_height']*scale
    x=i%e['columns']*w;y=i//e['columns']*h;return a[y:y+h,x:x+w]
def canvas(w,h):
    a=np.empty((h,w,4),np.uint8);a[:]=[25,29,39,255];return a
def annotate(name,a,items):
    source=QA/(name+'_plain.png');target=QA/(name+'.png');write(source,a)
    spec=QA/(name+'_labels.json');spec.write_text(json.dumps({'input':str(source),'output':str(target),'items':items}))
    subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass6.ps1'),'-Spec',str(spec)],check=True,capture_output=True)
    return read(target)
def text(x,y,s,size=16):return {'x':x,'y':y,'text':s,'size':size}

def contacts(m):
    a=canvas(1000,6*212);labels=[]
    for row,(name,e) in enumerate(m['janitor'].items()):
        labels.append(text(10,row*212+190,name+' | '+str(e['frames'])+' frames @ '+str(e['fps'])+'fps'))
        for j,t in enumerate([0,.2,.4,.6,.8]):blend(a,cell(e,int(t*e['frames']),2),j*200,row*212)
    annotate('janitor_contact_sheet',a,labels)
    a=canvas(1240,4*188);labels=[]
    for row,color in enumerate(m['umbrella']['colors']):
        e=m['umbrella']['fold'][color];op=m['umbrella']['open'][color]
        blend(a,asset(op['file_2x']),0,row*188)
        labels.append(text(4,row*188+165,color+' open'))
        for j in range(6):blend(a,cell(e,j,2),(j+1)*176,row*188);labels.append(text((j+1)*176+4,row*188+165,'fold '+str(j)))
    annotate('umbrella_contact_sheet',a,labels)
    a=canvas(1264,6*434);labels=[];bg=asset('lit_bg@2x.png')
    for row,e in enumerate(m['door_anims']):
        x,y,w,h=[e[k]*2 for k in ['x','y','frame_width','frame_height']]
        for col,i in enumerate([0,4,8,15]):
            panel=bg[y:y+h,x:x+w].copy();blend(panel,cell(e,i,2),0,0);blend(a,panel,col*316,row*434)
            labels.append(text(col*316+4,row*434+410,'Door '+str(e['door'])+' / frame '+str(i)))
    annotate('door_contact_sheet',a,labels)
    full=asset('full.png').copy();labels=[]
    for e in m['marquees']:
        x,y=e['bottom_center'];labels.append(text(x-68,y-75,'SCREEN '+str(e['screen']),18))
        labels.append(text(x-68,y-47,str(e['bottom_center']),12))
    for e in m['poster_frames']:
        t=sum(e['along'])/2;u,v=(0,t) if e['wall']=='u0' else (t,0);x,y=project(u,v,sum(e['z_px'])/2)
        labels.append(text(x-7,y-7,str(e['screen']),14))
    annotate('stack_layout_check',full,labels)
    # Detailed before/after counters and door thresholds for art review.
    old=read(ROOT/'out5/full@2x.png');new=asset('full@2x.png');a=canvas(1500,1000);labels=[]
    for row,(x,y,w,h,label) in enumerate([(580,620,290,125,'Ticket counter wear'),(990,638,375,125,'Snack counter wear'),(470,445,150,125,'Threshold and kickplate'),(430,770,260,125,'Pavement wear')]):
        for col,im in enumerate([old,new]):
            patch=im[y*2:(y+h)*2,x*2:(x+w)*2];blend(a,patch,col*750,row*250)
            labels.append(text(col*750+5,row*250+5,label+(' / pass5' if col==0 else ' / pass6')))
    annotate('wear_comparison',a,labels)
    drip=m['prop_loops'][-1];a=canvas(1100,400);labels=[]
    for j,i in enumerate([0,8,16,30,55]):
        panel=asset('full@2x.png')[550*2:680*2,310*2:410*2].copy()
        blend(panel,cell(drip,i,2),(drip['x']-310)*2,(drip['y']-550)*2,True)
        blend(a,panel,j*220,40);labels.append(text(j*220+5,8,'Drip frame '+str(i)))
    annotate('shelter_drip_check',a,labels)

def scene(m,frame):
    t=frame/24;bg=asset('base.png').copy();light=read(QA/'loop_frames'/('f'+str(frame%120).zfill(3)+'.png'))
    bg[:,:,:3]=np.minimum(bg[:,:,:3].astype(np.uint16)+light[:,:,:3],255).astype(np.uint8)
    door=m['door_anims'][(frame//24)%6];blend(bg,cell(door,min(15,int((frame%24)*18/24))),door['x'],door['y'])
    draw=[]
    for e in m['render_layers']:draw.append((e['z_index'],asset(e['file']),e['x'],e['y'],False))
    for e in m['prop_loops']:draw.append((e['z_index'],cell(e,frame%72),e['x'],e['y'],True))
    # Janitor takes three seconds across the lobby, then reverses for three.
    u=8.1+.48*(t if t<3 else 6-t);v=7.3;name='walk_plus_u' if t<3 else 'walk_minus_u';e=m['janitor'][name]
    x,y=project(u,v)-np.array(e['anchor']);z=1000+round((u+v)*100)
    draw.append((z,cell(e,int(t*12)%12),x,y,False))
    ue=m['umbrella']['open']['red'];grip=project(u,v,40)+[10,0];draw.append((z+1,asset(ue['file']),grip[0]-ue['anchor'][0],grip[1]-ue['anchor'][1],False))
    # A resting janitor for the sweep and prop-depth context.
    e=m['janitor']['sweep'];u,v=6.1,8.2;x,y=project(u,v)-np.array(e['anchor'])
    draw.append((1000+round((u+v)*100),cell(e,int(t*16)%48),x,y,False))
    e=m['cat']['sit'];x,y=project(10.75,7.75)-np.array(e['anchor']);draw.append((2850,cell(e,int(t*16)%48),x,y,False))
    for z,a,x,y,add in sorted(draw,key=lambda q:q[0]):blend(bg,a,x,y,add)
    return bg

def preview(m):
    labels=[text(8,215,'Delivered sheets: moving janitor at 0.48 tiles/s; doors, shelter drip and inherited loops',17)]
    for i,name in enumerate(m['janitor']):labels.append(text(i*208+5,193,name,14))
    labels+=[text(972,655,'Doors 1-5 + WC',16),text(972,778,'4 umbrella colours',14)]
    template=annotate('preview_template',canvas(1280,800),labels)
    for frame in range(144):
        a=template.copy();t=frame/24
        for i,e in enumerate(m['janitor'].values()):blend(a,cell(e,int(t*e['fps'])%e['frames'],2),i*208,0)
        world=scene(m,frame);blend(a,down_rgba(world),0,240)
        e=m['door_anims'][(frame//24)%6];x,y,w,h=[e[k]*2 for k in ['x','y','frame_width','frame_height']]
        panel=asset('lit_bg@2x.png')[y:y+h,x:x+w].copy();blend(panel,cell(e,min(15,int((frame%24)*18/24)),2),0,0);blend(a,panel,964,240)
        for i,color in enumerate(m['umbrella']['colors']):
            e=m['umbrella']['fold'][color];f=0 if frame%72<48 else min(5,(frame%72-48)//2)
            blend(a,cell(e,f),954+i*80,684)
        write(QA/'preview_frames'/('f'+str(frame).zfill(3)+'.png'),a)
        if frame in [0,24,48,71,100,143]:write(QA/('scene_f'+str(frame).zfill(3)+'.png'),world)
        if frame%24==0:print('PASS6_QA_FRAME',frame,flush=True)

def main():
    m=json.loads((OUT/'manifest.json').read_text());predecode(list(OUT.rglob('*.png')))
    contacts(m);preview(m)

if __name__=='__main__':main()
