"""Same HDR source, legacy 2-D halo versus optical compositor glare."""
import sys,time,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
from common import project,ZPP
from draft4_common import ROOT,QA,WORK,W,H,status,report
from pngio import read,write,predecode
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));source=bpy.context.scene
paths=[]
for o in source.objects:
    if o.type!='CURVE' or not ('luminous core' in o.name):continue
    if not o.data.materials:continue
    ma=o.data.materials[0];p=ma.node_tree.nodes.get('Principled BSDF')
    if not p or p.inputs['Emission Strength'].default_value<1:continue
    col=np.array(p.inputs['Emission Color'].default_value[:3]);col/=max(.001,col.max())
    for s in o.data.splines:
        pts=[o.matrix_world@Vector(q.co[:3]) for q in s.points]
        paths.append({'name':o.name,'points':[[x*2/3 for x in project(p.x,-p.y,p.z*ZPP)] for p in pts],'color':col.tolist()})
sc=bpy.data.scenes.new('Draft 4 optical compositor');sc.render.engine='BLENDER_WORKBENCH';sc.collection.objects.link(source.camera);sc.camera=source.camera
for k in ['view_transform','look','exposure','gamma']:setattr(sc.view_settings,k,getattr(source.view_settings,k))
sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100;sc.render.use_compositing=True;sc.render.use_sequencer=False
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
bpy.context.window.scene=sc
tree=bpy.data.node_groups.new('D4 physical lens scattering comparison','CompositorNodeTree');tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');sc.compositing_node_group=tree;n=tree.nodes;l=tree.links
im=bpy.data.images.load(str(WORK/'preview_denoised.exr'));node=n.new('CompositorNodeImage');node.image=im
out=n.new('NodeGroupOutput');base=node.outputs.get('Combined') or node.outputs[0]
def glare(kind,strength,size,threshold,tint=(1,1,1,1)):
    q=n.new('CompositorNodeGlare');q.inputs['Type'].default_value=kind;q.inputs['Quality'].default_value='High';q.inputs['Threshold'].default_value=threshold;q.inputs['Smoothness'].default_value=.15;q.inputs['Strength'].default_value=strength;q.inputs['Size'].default_value=size;q.inputs['Tint'].default_value=tint;l.new(base,q.inputs['Image']);return q
def add(a,c):
    q=n.new('ShaderNodeMix');q.data_type='RGBA';q.blend_type='ADD';q.clamp_result=False;q.inputs[0].default_value=1;l.new(a,q.inputs[6]);l.new(c,q.inputs[7]);return q.outputs[2]
bloom=glare('Bloom',.22,.025,2.8)
halo=glare('Fog Glow',.045,.012,3.2,(1,.34,.18,1))
streak=glare('Streaks',.018,.01,5.0);streak.inputs['Streaks'].default_value=4;streak.inputs['Streaks Angle'].default_value=math.pi/4;streak.inputs['Iterations'].default_value=2;streak.inputs['Fade'].default_value=.74;streak.inputs['Color Modulation'].default_value=.03
l.new(add(add(add(base,bloom.outputs['Glare']),halo.outputs['Glare']),streak.outputs['Glare']),out.inputs['Image'])
t=time.perf_counter();sc.render.filepath=str(QA/'test_glare_after.png');bpy.ops.render.render(write_still=True);dt=time.perf_counter()-t
# Preserve the same source radiometry before the legacy additive sprite halo.
source.render.image_settings.media_type='IMAGE';source.render.image_settings.file_format='PNG';source.render.image_settings.color_mode='RGBA';source.render.image_settings.color_depth='8';im.save_render(str(WORK/'beauty_no_glare.png'),scene=source)
predecode([WORK/'beauty_no_glare.png']);a=read(WORK/'beauty_no_glare.png');glow=np.zeros((H,W,3),np.float32)
for path in paths:
    col=np.array(path['color'],np.float32)
    for p,q in zip(path['points'],path['points'][1:]):
        x0=max(0,math.floor(min(p[0],q[0])-9));x1=min(W,math.ceil(max(p[0],q[0])+10));y0=max(0,math.floor(min(p[1],q[1])-9));y1=min(H,math.ceil(max(p[1],q[1])+10))
        if x0>=x1 or y0>=y1:continue
        yy,xx=np.indices((y1-y0,x1-x0),dtype=np.float32);xx+=x0+.5;yy+=y0+.5;dx=q[0]-p[0];dy=q[1]-p[1];t=np.clip(((xx-p[0])*dx+(yy-p[1])*dy)/(dx*dx+dy*dy+1e-6),0,1);dist=(xx-p[0]-t*dx)**2+(yy-p[1]-t*dy)**2
        glow[y0:y1,x0:x1]+=np.exp(-dist/(14*(2/3)**2))[:,:,None]*col*2.6
before=a.copy();before[:,:,:3]=np.clip(np.rint(a[:,:,:3].astype(float)+np.minimum(glow,60)),0,255).astype(np.uint8);write(QA/'test_glare_before.png',before)
report('glare.json',{'same_hdr_source':'draft4/preview_denoised.exr','legacy_baseline':'pass-9 style Gaussian additive 2-D tube halo, regenerated from CURRENT world-projected tubes and colours; no old sign art reused','physical_after':{'Bloom':{'strength':.22,'size':.025,'threshold':2.8},'red_weighted_FogGlow':{'strength':.045,'size':.012,'threshold':3.2,'tint':[1,.34,.18]},'small_four_streak_aperture':{'strength':.018,'iterations':2,'fade':.74,'threshold':5.0}},'compositor_seconds':dt,'current_tube_paths':len(paths),'optical_model_limit':'Blender HDR glare/scattering approximation, not a measured lens PSF or lens-element ray trace'})
status('test B before/after saved from one current-scene HDR frame: regenerated legacy 2D halo versus Bloom, small aperture streaks and slight red-weighted halation')
