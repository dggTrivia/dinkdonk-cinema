"""A genuine flat water tread rendered through the unchanged dimetric camera."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_scene as b
from common import xyz,render
from pass8_common import ROOT,QA,OUT,gpu,status
from pngio import read,write,predecode
from package_cat_pass5 import down_rgba
import numpy as np
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8.blend'));sc=bpy.context.scene;gpu(sc)
for ob in sc.objects:
    if ob.type in ['MESH','CURVE','FONT']:ob.visible_camera=False
b.GROUP='wet_print';b.GROUPS.clear()
ma=b.material('P8 transparent wet sole',(.002,.003,.005),.22,0)
n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.12;p.inputs['Specular IOR Level'].default_value=.15
trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.75
l.new(trans.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs[0])
# Disconnected heel and forefoot lobes, with narrow tread gaps. The print is
# ground-plane geometry, projected by the same camera as all other assets.
for k,(offset,ru,rv) in enumerate([(-.045,.018,.022),(.025,.035,.026)]):
    for side in [-1,1]:
        vs=[]
        for j in range(33):
            angle=(j/32*math.pi)+(0 if side==1 else math.pi)
            vs.append(xyz(9.5+.70*(offset+ru*math.cos(angle)),8.7+.70*(rv*math.sin(angle)+side*.0025),1.0))
        ob=b.mesh('P8 wet tread lobe',vs,[list(range(len(vs)))],ma)
sc.render.use_compositing=False;sc.render.use_sequencer=False;sc.render.film_transparent=True
sc.cycles.samples=128;sc.cycles.use_denoising=False
sc.render.resolution_x=1920*4;sc.render.resolution_y=1080*4;sc.render.resolution_percentage=100
sc.render.use_border=True;sc.render.use_crop_to_border=True
sc.render.border_min_x=943/1920;sc.render.border_max_x=953/1920
sc.render.border_min_y=1-898/1080;sc.render.border_max_y=1-892/1080
path=QA/'wet_print_4x.png';render(path);predecode([path]);a=read(path)
assert a.shape==(24,40,4),a.shape
(OUT/'items').mkdir(exist_ok=True,parents=True)
a2=down_rgba(a);a1=down_rgba(a2)
for scale,img in [(1,a1),(2,a2)]:
    img[img[:,:,3]==0,:3]=0;write(OUT/('items/wet_print'+('@2x' if scale==2 else '')+'.png'),img)
assert a1[:,:,3].max()>0 and np.any(a1[:,:,3]==0)
item={'file':'items/wet_print.png','file_2x':'items/wet_print@2x.png','w':10,'h':6,'anchor':[5,3],
      'alpha':'straight','attach_point':'centre of wet ground footprint','render':'4x Cycles water tread, area reduced in premultiplied space; unchanged dimetric camera'}
(QA/'wet_print_item.json').write_text(json.dumps(item,indent=2))
status('Wet-print item rendered and packaged: 10x6 / 20x12, centre anchor, straight RGBA')
