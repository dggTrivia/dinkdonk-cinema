"""Three-second 24fps additive PNG sheets, with native 2x images and exact rects."""
from pathlib import Path
import json,math,hashlib,subprocess
import numpy as np
from pngio import read,write,predecode
from package_layers import boxblur
from package_vehicles import blend

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa4';OUT=ROOT/'out4'
N=72;COLS=6;ROWS=12;TAU=math.tau
FONT={
 'I':['111','010','010','010','111'],'N':['101','111','111','111','101'],
 'S':['111','100','111','001','111'],'E':['111','100','110','100','111'],
 'R':['110','101','110','101','101'],'T':['111','010','010','010','010'],
 'C':['111','100','100','100','111'],'O':['111','101','101','101','111'],
 ' ':['000']*5,
}

def text_pixels(a,text,x,y,color):
    for ch in text:
        glyph=FONT[ch]
        for j,row in enumerate(glyph):
            for i,on in enumerate(row):
                if on=='1' and 0<=y+j<a.shape[0] and 0<=x+i<a.shape[1]:a[y+j,x+i]=color
        x+=4

def arcade_art(frame):
    t=(frame%N)/N;a=np.zeros((24,24,3),np.float32)
    # A crisp, original tiny arcade scene, using two lines to fit the physical CRT.
    blink=.35+.65*(.5+.5*math.cos(TAU*t))**.7
    text_pixels(a,'INSERT',0,1,np.array([90,185,165])*blink)
    text_pixels(a,'COIN',4,18,np.array([210,135,50])*blink)
    invader=['00100100','00011000','00111100','01111110','11011011','01111110','01000010']
    centre=8+int(round(2*math.sin(TAU*t)))
    for j,row in enumerate(invader):
        for i,on in enumerate(row):
            if on=='1':a[8+j,centre+i]=[130,65+35*math.sin(TAU*t)**2,170]
    # Stars scroll and wrap beneath the instruction, never outside the CRT.
    for i in range(4):
        x=(i*7+3)%24;y=7+(int((frame%N)*9/N)+i*3)%9
        a[y,x]=np.maximum(a[y,x],[35,75,95])
    return a

def frame2(spec,index,mask,popcorn=None):
    t=(index%N)/N;angle=TAU*t;x,y,w,h=spec['rect'];kind=spec['kind']
    yy,xx=np.indices((h*2,w*2),dtype=np.float32);sx=x+(xx+.5)/2;sy=y+(yy+.5)/2
    if kind=='popcorn':
        ox=(x-1048)*2;oy=(y-553)*2
        rgb=popcorn[oy:oy+h*2,ox:ox+w*2,:3].copy()
        # Remove the renderer's 1/255 black dither outside the kernels and
        # preserve a black gutter so adjacent sheet cells cannot bleed.
        rgb[rgb<=1]=0
        rgb[:2]=0;rgb[-2:]=0;rgb[:,:2]=0;rgb[:,-2:]=0
        return rgb
    coverage=mask[:,:,:3].max(axis=2).astype(np.float32)/255
    if kind=='arcade':
        v=12.712-(sx-900)/60;z=350+(12.712+v)*30-sy
        s=(8.02-v)/.37;q=(67-z)/21
        ix=np.floor(s*24).astype(int);iy=np.floor(q*24).astype(int)
        inside=(ix>=0)&(ix<24)&(iy>=0)&(iy<24)
        sampled=arcade_art(index)[np.clip(iy,0,23),np.clip(ix,0,23)]
        rgb=sampled*inside[:,:,None]*coverage[:,:,None]
        rgb+=coverage[:,:,None]*np.array([1.5,4.5,6.5])
    elif kind=='menu':
        phase={'menu_popcorn':.0,'menu_soda':1.7,'menu_nachos':3.2}[spec['name']]
        amount=6+4*(.5+.5*math.sin(angle+phase))+2*math.sin(angle*19+phase)**2
        rgb=coverage[:,:,None]*np.array([1,.77,.44])*amount
    elif kind=='soda':
        u=(sx-900)/60+3.449;z=350+(u+3.449)*30-sy
        amount=.76+.15*math.cos(angle)+.035*math.sin(angle*13)**2
        color=np.where((z>61)[:,:,None],np.array([60,150,170]),np.array([23,28,25]))
        rgb=coverage[:,:,None]*color*amount
    else:
        # One worn E gets a brief intermittent amber afterglow once per cycle.
        distance=lambda c:((t-c+.5)%1)-.5
        pulse=math.exp(-(distance(.64)/.025)**2)+.65*math.exp(-(distance(.715)/.014)**2)
        rgb=coverage[:,:,None]*np.array([50,28,9])*pulse
    # Very local phosphor/filament bloom, leaving the border exactly black.
    rgb+=boxblur(rgb.astype(np.float32),2)*.08
    rgb=np.clip(np.rint(rgb),0,255).astype(np.uint8)
    rgb[:2]=0;rgb[-2:]=0;rgb[:,:2]=0;rgb[:,-2:]=0
    return rgb

def down(a):
    h,w,c=a.shape;return np.rint(a.reshape(h//2,2,w//2,2,c).mean(axis=(1,3))).astype(np.uint8)

def depth(spec,m):
    x,y,w,h=spec['rect'];overlaps=[]
    for e in m['render_layers']:
        if e['parent']!=spec['parent']:continue
        if min(x+w,e['x']+e['w'])>max(x,e['x']) and min(y+h,e['y']+e['h'])>max(y,e['y']):overlaps.append(e)
    assert overlaps,spec
    return max(e['z_index'] for e in overlaps)+1,[e['name'] for e in overlaps]

def annotate(source,target,items):
    spec=QA/'annotation_job.json';spec.write_text(json.dumps({'input':str(source),'output':str(target),'items':items}))
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass4.ps1'),'-Spec',str(spec)],check=True)

def main():
    config=json.loads((QA/'prop_specs.json').read_text());m=json.loads((QA/'manifest_art.json').read_text())
    predecode(list((QA/'prop_masks').glob('*.png'))+list((QA/'popcorn_raw').glob('*.png')))
    assert np.array_equal(read(QA/'popcorn_raw'/'f000@2x.png'),read(QA/'popcorn_raw'/'f072@2x.png')),'Popcorn period differs'
    specs=config['specs'];loops=[];reports=[];frames_for_qa={f:[] for f in [0,9,18,27,36,45,54,63,71]}
    all_source={}
    for spec in specs:
        name=spec['name'];x,y,w,h=spec['rect'];mask=None if spec['kind']=='popcorn' else read(QA/'prop_masks'/(name+'@2x.png'))
        frames=[]
        for i in range(N):
            popcorn=read(QA/'popcorn_raw'/('f'+str(i).zfill(3)+'@2x.png')) if spec['kind']=='popcorn' else None
            a=frame2(spec,i,mask,popcorn);assert a.shape==(h*2,w*2,3),(name,a.shape)
            frames.append(a)
        endpoint=frame2(spec,N,mask,read(QA/'popcorn_raw'/'f072@2x.png') if spec['kind']=='popcorn' else None)
        assert np.array_equal(endpoint,frames[0]),name
        differences=[float(np.abs(frames[i].astype(np.int16)-frames[i-1].astype(np.int16)).mean()) for i in range(1,N)]
        seam=float(np.abs(frames[-1].astype(np.int16)-frames[0].astype(np.int16)).mean())
        assert seam<=max(differences)*1.6+.01,(name,seam,max(differences))
        assert max(differences)>0,('Static loop',name)
        sheets={1:np.zeros((h*ROWS,w*COLS,3),np.uint8),2:np.zeros((h*ROWS*2,w*COLS*2,3),np.uint8)}
        for i,a in enumerate(frames):
            for scale,b in [(2,a),(1,down(a))]:
                sy=(i//COLS)*h*scale;sx=(i%COLS)*w*scale;sheets[scale][sy:sy+h*scale,sx:sx+w*scale]=b
            if i in frames_for_qa:frames_for_qa[i].append((spec,down(a)))
        file='prop_loops/'+name+'.png';file2='prop_loops/'+name+'@2x.png'
        write(OUT/file,sheets[1]);write(OUT/file2,sheets[2]);all_source[name]=frames
        z,parents=depth(spec,m)
        loops.append({'name':name,'file':file,'file_2x':file2,'x':x,'y':y,'w':w,'h':h,'z_index':z,'blend':'plus-lighter',
            'format':'png-spritesheet','fps':24,'frames':N,'loop_seconds':3,'columns':COLS,'rows':ROWS,
            'frame_width':w,'frame_height':h,'frame_order':'row-major','parent':spec['parent'],'parent_slices':parents})
        reports.append({'name':name,'period_endpoint_max_error':0,'last_to_first_mean_abs_error':seam,
            'adjacent_mean_abs_error':float(np.mean(differences)),'adjacent_max_mean_abs_error':max(differences),
            'unique_frames':len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames}),
            'bytes_1x':(OUT/file).stat().st_size,'bytes_2x':(OUT/file2).stat().st_size})
    m['prop_loops']=loops
    m['prop_loop_contract']={'format':'Opaque RGB PNG sprite sheets on black. Add each selected cell with plus-lighter.',
        'playback':'frame = floor(elapsedSeconds * fps) % frames; source cell (frame % columns, floor(frame / columns)).',
        'resolution':'All rects, frame_width/frame_height and z_index use the 1920x1080 coordinate system. @2x doubles each cell and the sheet, not CSS placement.',
        'sorting':'Insert each crop at its z_index in the same walker/prop stack, immediately above its listed parent_slices. Do not place below occluder sprites.',
        'phase':'All sheets are 72 frames / 3 seconds / 24 fps, seamless. Endpoint frame 72 was independently regenerated and matches frame 0.',
        'fallback':'Pause at any cell for reduced motion. Omit sheets if unsupported; the static props remain complete.',
        'popcorn':'Native 2x Cycles geometry, rotating lobed kernels on periodic arcs, attenuated through the existing glass and occluded by kettle/cabinet geometry.',
        'signs':'Three menu backlights, soda logo and selections, a single E in TICKETS, and original INSERT COIN arcade pixel art.'}
    meta=json.loads((QA/'video_metadata.json').read_text())
    m.update(light_loop_bytes=meta['bytes'],light_loop_sha256=meta['sha256'])
    m['validation'].update(calibration='../qa4/calibration.json',layout='../qa4/final_validation.json',
        slices='../qa4/slice_validation.json',loop_period='../qa4/loop_validation.json',encoded_video='../qa4/final_validation.json')
    m['loop_seam_validation']='qa4/loop_validation.json'
    m['pass4_validation']='../qa4/final_validation.json'
    m['pass4_prop_reference_frame']=18
    m['pass4_extra_lettering']=['SODA on the fountain (animated overlay)','INSERT / COIN on the arcade (animated overlay)']
    (QA/'prop_loop_validation.json').write_text(json.dumps({'passed':True,'loops':reports,'fps':24,'frames':72,'seconds':3},indent=2))
    pending=OUT/'manifest.pending.json';pending.write_text(json.dumps(m,indent=2));pending.replace(OUT/'manifest.json')
    # Source-over sorted scene plus the additive prop crops, from the delivered sheets.
    base=read(OUT/'lit_bg.png');predecode([OUT/e['file'] for e in m['render_layers']])
    images=[]
    for f,items in frames_for_qa.items():
        a=base.copy();draw=[{'z':e['z_index'],'x':e['x'],'y':e['y'],'src':read(OUT/e['file']),'add':False} for e in m['render_layers']]
        for spec,frame in items:
            entry=next(l for l in loops if l['name']==spec['name']);x,y,w,h=spec['rect']
            draw.append({'z':entry['z_index'],'x':x,'y':y,'src':np.dstack([frame,np.full((h,w),255,np.uint8)]),'add':True})
        for item in sorted(draw,key=lambda e:e['z']):blend(a,item['src'],item['x'],item['y'],item['add'])
        write(QA/('props_f'+str(f).zfill(3)+'.png'),a);images.append((f,a))
    # Inspect nine times at 2x enlargement of the machine/menu area and actual CRT.
    tiles=[];labels=[]
    for f,a in images:
        snack=a[535:730,1025:1435];ticket=a[535:660,590:800];arcade=a[880:950,1160:1225]
        tile=np.full((280,480,4),255,np.uint8);tile[:,:,:3]=(20,21,30)
        blend(tile,snack,0,25);blend(tile,ticket,0,155);blend(tile,np.repeat(np.repeat(arcade,2,axis=0),2,axis=1),320,140)
        tiles.append(tile)
    sheet=np.concatenate([np.concatenate(tiles[i:i+3],axis=1) for i in range(0,9,3)],axis=0)
    write(QA/'prop_contact_raw.png',sheet)
    for i,(f,a) in enumerate(images):labels.append({'type':'text','x':(i%3)*480+8,'y':(i//3)*280+4,'text':f'FRAME {f:02d} / 72 | {f/24:.3f}s','size':15})
    annotate(QA/'prop_contact_raw.png',QA/'prop_loops_check.png',labels)
    # A before/after image at identical resolution and projection.
    before=read(ROOT/'out3'/'full.png');after=read(QA/'props_f018.png')
    comparison=np.concatenate([before,after],axis=0);write(QA/'before_after_raw.png',comparison)
    annotate(QA/'before_after_raw.png',QA/'before_after.png',[
        {'type':'text','x':30,'y':25,'size':23,'text':'PASS 3 | LIVE REFERENCE'},
        {'type':'text','x':30,'y':1105,'size':23,'text':'PASS 4 | CALMER CARPET + WARM SERVICE LIGHT + PROP LOOPS'}])
    print('PROP_LOOPS_READY',len(loops),sum(r['bytes_1x']+r['bytes_2x'] for r in reports),flush=True)

if __name__=='__main__':main()
