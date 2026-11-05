"""Review the actual delivered pixels at native size, on owners, and on the road."""
from pathlib import Path
import json, subprocess, math
import numpy as np
from pngio import read, write, predecode
from package_vehicles import blend
from package_pass7 import vehicle_variants

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa7';OUT=ROOT/'out7';CACHE={}

def asset(file):
    if file not in CACHE:CACHE[file]=read(OUT/file)
    return CACHE[file]

def canvas(w,h,color=(24,28,38)):
    a=np.empty((h,w,4),np.uint8);a[:]=[*color,255];return a

def text(x,y,s,size=16):return {'x':x,'y':y,'text':s,'size':size}

def annotate(name,a,items):
    source=QA/(name+'_plain.png');target=QA/(name+'.png');write(source,a)
    spec=QA/(name+'_labels.json');spec.write_text(json.dumps({'input':str(source),'output':str(target),'items':items}))
    subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass7.ps1'),'-Spec',str(spec)],check=True,capture_output=True)
    return read(target)

def zoom(a,n):return np.repeat(np.repeat(a,n,0),n,1)

def checker(w,h,step=8):
    yy,xx=np.indices((h,w));a=canvas(w,h);v=((xx//step+yy//step)%2)*16+45;a[:,:,:3]=v[:,:,None];return a

def contacts(m):
    a=canvas(1140,600);labels=[text(18,12,'PASS 7 / delivered item pixels - native, 2x, nearest-neighbour detail',21)]
    for i,(name,e) in enumerate(m['items'].items()):
        x=i%3*380;y=55+i//3*270
        labels += [text(x+12,y,name+'   '+str(e['w'])+' x '+str(e['h']),18),text(x+12,y+25,'attach '+str(e['anchor'])+' / '+e['attach_point'],12)]
        blend(a,checker(352,190),x+12,y+52)
        one=asset(e['file']);two=asset(e['file_2x'])
        blend(a,one,x+32,y+90);blend(a,two,x+82,y+80)
        # 4x enlargement of the supplied @2x, no interpolation.
        xx=x+156;yy=y+70;blend(a,zoom(two,4),xx,yy)
        labels += [text(x+23,y+205,'1x',12),text(x+82,y+205,'2x',12),text(x+157,y+205,'8x view / cyan = attach',12)]
        labels += [{'type':'cross','x':xx+e['anchor'][0]*8,'y':yy+e['anchor'][1]*8,'color':'#75eee7'}]
    return annotate('item_contact_sheet',a,labels)

def proxy():
    """Only a QA ruler for a 50px emote, never a delivered art asset."""
    yy,xx=np.indices((50,50),dtype=float);x=(xx-24.5)/23;y=(yy-24.5)/24
    r=x*x+y*y;a=np.zeros((50,50,4),np.uint8)
    mask=r<1;a[:,:,3]=np.clip((1-r)*1200,0,255).astype(np.uint8)
    shade=np.maximum(0,1-r)**.5*.55+.23+(-x-y)*.06
    a[:,:,:3]=np.minimum(255,shade[:,:,None]*np.array([116,157,166])).astype(np.uint8)
    for ex in [16,33]:
        eye=(xx-ex)**2+(yy-22)**2<4;a[eye,:3]=[23,28,34]
    a[(yy>32)&(yy<35)&(xx>19)&(xx<31),:3]=[23,28,34]
    a[~mask]=0;return a

def attach(dst,e,point):
    blend(dst,asset(e['file']),point[0]-e['anchor'][0],point[1]-e['anchor'][1])

def owners(m,t=0):
    # A native-size crop from the delivered carpet, with labelled size proxies.
    a=asset('full.png')[690:970,770:1170].copy();avatar=proxy()
    for x,name in [(65,'popcorn'),(165,'soda'),(265,'stub')]:
        y=116;blend(a,avatar,x-25,y-50);attach(a,m['items'][name],(x+23,y-2 if name!='stub' else y-17))
    for x,name in [(105,'cap_cashier'),(255,'cap_usher')]:
        y=227;blend(a,avatar,x-25,y-50);attach(a,m['items'][name],(x,y-50))
    # The flight is deliberately a consumer transform of the centred still.
    u=(t%2)/2;attach(a,m['items']['ticket'],(105+150*u,163-38*math.sin(math.pi*u)))
    return a

def vehicle_panel(name,parent,e,mode):
    w,h=parent['w'],parent['h'];ax,ay=parent['anchor'];sx,sy=600-ax,860-ay
    panel=asset('full.png')[sy:sy+h,sx:sx+w].copy()
    if mode=='only':
        panel=canvas(w,h,(0,0,0));blend(panel,asset(e['light_indicator_only']),0,0,True)
    else:
        blend(panel,asset(e['light_brake' if mode.startswith('brake') else 'light']),0,0,True)
        if mode.endswith('on'):blend(panel,asset(e['light_indicator_only']),0,0,True)
        blend(panel,asset(e['file']),0,0)
    return panel

def lights(m):
    # Every state appears; the standalone difference is deliberately unboosted.
    a=canvas(1800,8*300+55);labels=[text(12,12,'PASS 7 / exact indicator-only additions, all directions and door states',22)]
    modes=['normal','only','normal_on','brake_on']
    for row,(name,parent,e) in enumerate(vehicle_variants(m)):
        y=55+row*300
        for col,mode in enumerate(modes):
            p=vehicle_panel(name,parent,e,mode);blend(a,p,col*450,y+25)
            labels.append(text(col*450+6,y,name+' / '+mode.replace('_',' + '),14))
    annotate('indicator_contact_sheet',a,labels)

def main():
    m=json.loads((OUT/'manifest.json').read_text())
    needed=[OUT/'full.png']+[OUT/e[k] for e in m['items'].values() for k in ['file','file_2x']]
    needed += [OUT/e[k] for _,_,e in vehicle_variants(m) for k in ['file','light','light_indicator_only','light_brake']]
    predecode(needed)
    contacts(m);lights(m)
    owners_image=owners(m,.6);a=canvas(1200,650)
    blend(a,owners_image,0,60);blend(a,zoom(owners_image,2),400,60)
    annotate('attachment_check',a,[text(15,10,'50px emote proxies / native on left, nearest-neighbour 2x on right',21),
                                 text(10,360,'QA size rulers only;',16),text(10,385,'the page supplies real emotes.',16),
                                 text(10,420,'Cups: lower right.',16),text(10,445,'Caps: top centre.',16),text(10,470,'Tickets: centre pivot.',16)])
    # Four seconds showing on/off over a normal bus and braking open taxi,
    # plus the single centred ticket sprite moving between staff proxies.
    frames=QA/'preview_frames';frames.mkdir(exist_ok=True)
    bus=m['vehicles']['bus']['+u'];taxi=m['vehicles']['taxi']['-u'];toe=taxi['door_open']
    blank=annotate('preview_template',canvas(1280,720),[
        text(20,12,'ROXY / PASS 7 / carried props + amber-only lights',25),
        text(20,56,'Delivered pixels on 50px emote proxies (2x review)',16),
        text(20,663,'Preview transforms are illustrative; sprites impose no blink or ticket-flight timing.',15),
        text(830,56,'Bus +u / normal + blinking indicator',16),text(830,367,'Taxi -u / door open / brake + indicator',16)])
    for i in range(96):
        t=i/24;on=i%24<12;a=blank.copy()
        blend(a,zoom(owners(m,t),2),20,90)
        blend(a,vehicle_panel('bus_plus',bus,bus,'normal_on' if on else 'normal'),830,90)
        blend(a,vehicle_panel('taxi_minus_open',taxi,toe,'brake_on' if on else 'brake'),830,400)
        write(frames/('f'+str(i).zfill(3)+'.png'),a)
    print('PASS7_QA_CONTACTS_AND_96_FRAMES',flush=True)

if __name__=='__main__':main()
