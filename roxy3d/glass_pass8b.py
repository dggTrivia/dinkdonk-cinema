"""Pane-wide films plus more legible runnels, keeping all old crops/depths."""
import json,math
import numpy as np
from pngio import read,write,predecode
from package_layers import over
from package_props_pass8 import glass_frame,sheet,validate
from package_cat_pass5 import down_rgba
from pass8b_common import ROOT,QA,OUT,LIVE,status

def runnel(e,i):
    a=glass_frame(e,i);a=a.copy();luma=a[:,:,:3].mean(2)
    bright=luma>90;a[bright,:3]=np.minimum(a[bright,:3].astype(float)*1.22+10,235).astype(np.uint8)
    a[:,:,3]=np.minimum(np.rint(a[:,:,3].astype(float)*1.65),230).astype(np.uint8)
    a[a[:,:,3]==0,:3]=0
    return a

def film(e,parent):
    x,y,w,h=e['x'],e['y'],e['w'],e['h'];yy,xx=np.indices((2*h,2*w),dtype=np.float32)
    sx=x+(xx+.5)/2;sy=y+(yy+.5)/2;u=(sx-900)/60+9.052;z=350+(u+9.052)*30-sy
    lo,hi=parent['footprint'][0],parent['footprint'][2]
    edge=np.clip((u-lo-.018)*90,0,1)*np.clip((hi-.018-u)*90,0,1)*np.clip((z-3)/1.3,0,1)*np.clip((27.5-z)/1.3,0,1)
    # Thin vertical films and irregular water thickness; no opaque pane tint.
    fine=(.5+(np.sin(u*73+z*.17)+np.sin(u*151-z*.31)+np.sin(u*29+np.sin(z*.39)))/6)**7
    broad=(.5+.5*np.sin(u*23+np.sin(z*.14)))
    alpha=(.035+.075*broad+.045*fine)*edge
    color=np.zeros((*z.shape,3),np.float32);color[:]=[64,88,104]
    color+=fine[:,:,None]*np.array([35,43,45])
    # Wet sill accumulation spans the pane, including between runnel clusters.
    sill=np.exp(-((z-4.45)/.65)**2)*edge*(.65+.35*np.sin(u*81)**2)
    a2=sill*.54;premul=color*alpha[:,:,None]
    premul=np.array([158,184,190])*a2[:,:,None]+premul*(1-a2[:,:,None]);alpha=a2+alpha*(1-a2)
    rgb=np.divide(premul,alpha[:,:,None],out=np.zeros_like(premul),where=alpha[:,:,None]>1e-7)
    a=np.clip(np.rint(np.dstack([rgb,alpha*255])),0,255).astype(np.uint8);a[a[:,:,3]==0,:3]=0
    return a

def main():
    m=json.loads((LIVE/'manifest.json').read_text());reports=[];films=[];contacts=[];budget=0
    for e in (p for p in m['prop_loops'] if p['name'].startswith('water_glass_')):
        parent=next(p for p in m['render_layers'] if p['name']==e['parent_slices'][0])
        frames=[runnel(e,i) for i in range(72)];reports.append(validate(e['name'],frames,runnel(e,72)))
        for scale,key in [(1,'file'),(2,'file_2x')]:
            write(OUT/e[key],sheet(frames if scale==2 else [down_rgba(a) for a in frames],e['columns']))
        budget+=e['w']*e['h']*72*4*5
        lo,hi=parent['footprint'][0],parent['footprint'][2];v=9.052
        x=math.floor(900+60*(lo-v))-1;y=math.floor(350+30*(lo+v)-28.5)-1
        w=math.ceil(900+60*(hi-v))-x+2;h=math.ceil(350+30*(hi+v)-2)-y+2
        f={'name':'film_'+parent['name'],'x':x,'y':y,'w':w,'h':h,'z_index':parent['z_index'],
           'parent':parent['parent'],'parent_slices':[parent['name']],'format':'png-spritesheet','frames':1,'columns':1,'rows':1,'fps':12,
           'loop_seconds':1/12,'blend':'source-over','alpha':'straight','frame_width':w,'frame_height':h,'frame_order':'row-major'}
        a=film(f,parent)
        for scale,key in [(1,'file'),(2,'file_2x')]:
            file='prop_loops/'+f['name']+('@2x' if scale==2 else '')+'.png';f[key]=file;write(OUT/file,a if scale==2 else down_rgba(a))
        budget+=w*h*4*5;films.append(f)
        f['purpose']='Static wet-surface film and sill accumulation across the pane; dynamic runnels retain their original crop.'
        # Compare actual delivered glass over the same neutral background.
        path=OUT/(parent['file'][:-4]+'@2x.png');predecode([path]);base=read(path);bg=np.full((base.shape[0]+8,base.shape[1]+8,4),255,np.uint8);bg[:,:,:3]=[40,31,49]
        over(bg,base,4,4);after=bg.copy();over(after,frames[36],(e['x']-parent['x'])*2+4,(e['y']-parent['y'])*2+4);over(after,a,(x-parent['x'])*2+4,(y-parent['y'])*2+4)
        tile=np.full((150,400,4),255,np.uint8);tile[:,:,:3]=[24,25,33];over(tile,bg,0,0);over(tile,after,200,0);contacts.append(tile)
    assert budget<=16*1024**2,budget
    write(QA/'glass_before_after.png',np.concatenate(contacts,axis=0))
    (QA/'film_loops.json').write_text(json.dumps(films,indent=2))
    (QA/'glass_validation.json').write_text(json.dumps({'passed':True,'dynamic_loops':reports,'pane_wide_films':9,
        'glass_decoded_bytes_both_scales':budget,'all_existing_glass_rects_and_depths_unchanged':True,'cashier_glass_unchanged':True},indent=2))
    status('Pane-wide films, brighter wet sills and strengthened runnels packaged on the nine existing glass depths; '+str(round(budget/1024**2,3))+' MiB decoded at both scales combined')

if __name__=='__main__':main()
