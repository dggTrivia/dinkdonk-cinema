"""Fresh background, changed occluders and AOVs; only pass-9 destinations."""
import sys,json,time,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
import build_scene as b,build_pass8 as city,depth_pass
from common import render,NORMAL
from pass8_common import gpu
from pass9_common import ROOT,QA,OUT,LIVE,status

def load():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass9.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear()
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
    sc.render.use_compositing=False;sc.render.use_border=False;sc.render.use_crop_to_border=False
    return sc
def holdouts():
    for scale in [1,2]:
        sc=load();city.QA=QA;city.status=status;city.NEW.clear();city.REGIONS.clear()
        city.NEW.extend(o for o in sc.objects if o.get('pass8_surrounding') or o.get('pass8b_surrounding') or o.get('pass9_surrounding'))
        city.holdout(scale)
    status('Both independently rendered neighbourhood holdouts passed; intentional storefront occluders remain depth-sorted sprites')
def array(path):
    im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(h,w,4)[::-1].copy();bpy.data.images.remove(im)
    return np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-7)
def aov(sc,folder):
    for e in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(e)
    return depth_pass.configure(sc,folder)
def main():
    holdouts()
    meta=json.loads((QA/'scene_metadata.json').read_text());old=json.loads((LIVE/'manifest.json').read_text())
    sc=load();b.set_visibility('background');sc.cycles.samples=96;sc.cycles.adaptive_threshold=.012
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        folder=QA/('background_position'+suffix);aov(sc,folder);sc.render.use_compositing=True
        render(QA/('steady_bg'+suffix+'.png'));p=array(next(folder.glob('*.exr')));np.savez_compressed(QA/('world_positions'+suffix+'.npz'),position=p)
        status('Lit unanimated background and world-position AOV rendered at '+str(1920*scale)+'x'+str(1080*scale))
    sc=load();sc.cycles.samples=64;sc.cycles.adaptive_threshold=.015;records=[]
    names=meta['changed_groups']+['entrance_header']+[e['layer'] for e in meta['ad_surfaces']]
    for name in names:
        b.set_visibility(name);rect=b.bounds_for(name,6);x,y,x1,y1=rect;w=x1-x;h=y1-y
        previous=next((e for e in old['occluders'] if e['name']==name),None)
        fp=previous['footprint'] if previous else [8.4,8.95,10.6,9.05] if name=='entrance_header' else [-2.50,8.84,-1.54,8.96] if name=='paste_wall' else None
        e={'name':name,'file':'occ_'+name+'.png','x':x,'y':y,'w':w,'h':h}
        if fp:e.update(footprint=fp,height_px=151 if name.startswith(('glass','entrance')) else 40 if name=='paste_wall' else previous['height_px'],z_index=99 if name=='paste_wall' else previous['z_index'] if previous else 1000+round(sum(fp)*50))
        for scale,suffix in [(1,''),(2,'@2x')]:
            sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale;sc.render.use_border=True;sc.render.use_crop_to_border=True
            sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x1+.1)/1920;sc.render.border_min_y=(1080-y1+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
            folder=QA/'positions_exr'/(name+suffix);aov(sc,folder);sc.render.use_compositing=True
            render(OUT/('occ_'+name+suffix+'.png'))
            p=array(next(folder.glob('*.exr')));dest=QA/'positions'/(name+suffix+'.npz');dest.parent.mkdir(exist_ok=True);np.savez_compressed(dest,uv=p[:,:,:2])
        records.append(e);(QA/'rendered_occluders.json').write_text(json.dumps(records,indent=2));status('Native 1x/2x sprite and ownership AOV rendered: '+name)
    # Indicator variants share a native rect, projected onto the wall.
    from build_pass9 import UFACE
    sc=load();b.set_visibility('wc_indicator');b.GROUP='wc_indicator'
    plane=meta['wc_indicator_plane'];a,c=plane['along'];z0,z1=plane['z_px'];front=plane['front']
    cover=b.material('P9 indicator dark cover',(.005,.009,.012),.4)
    b.wallbox('P9 indicator dark face','u',a,c,z0,z1,cover,front,.003,0)
    glow=b.material('P9 indicator state',(.05,1,.22),.5,emit=2)
    label=b.text('P9 occupancy status','VACANT',b.wp('u',(a+c)/2,(z0+z1)/2,front+.005),.058,glow,UFACE)
    bpy.context.view_layer.update();rect=b.bounds_for('wc_indicator',8);x,y,x1,y1=rect
    states={}
    for name,body,color in [('vacant','VACANT',(.05,1,.22)),('occupied','OCCUPIED',(1,.035,.025))]:
        label.data.body=body;label.data.size=.058 if name=='vacant' else .045
        p=glow.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1)
        e={'x':x,'y':y,'w':x1-x,'h':y1-y,'z_index':901,'blend':'source-over','alpha':'straight'}
        for scale,suffix,key in [(1,'','file'),(2,'@2x','file_2x')]:
            sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale;sc.render.use_border=True;sc.render.use_crop_to_border=True
            sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x1+.1)/1920;sc.render.border_min_y=(1080-y1+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
            file='wc_'+name+suffix+'.png';render(OUT/file);e[key]=file
        states[name]=e
    (QA/'wc_indicator.json').write_text(json.dumps(states,indent=2));status('Vacant/occupied wall-indicator sprites rendered with a shared rectangle and straight RGBA')
if __name__=='__main__':main()
