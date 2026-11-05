"""Wet material/entrance pass, final background stills, and world-position AOV."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
import build_scene as b
import depth_pass
from common import ROOT,xyz,ZPP,render
from pass8_common import status,gpu
QA=ROOT/'qa8'

def wet_material():
    ma=b.material('P8 rain-soaked asphalt',(.017,.024,.031),.17,.12)
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');geo=n.new('ShaderNodeNewGeometry')
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.8;noise.inputs['Detail'].default_value=4
    l.new(geo.outputs['Position'],noise.inputs['Vector'])
    rough=n.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.065;rough.inputs['To Max'].default_value=.31
    l.new(noise.outputs['Fac'],rough.inputs[0]);l.new(rough.outputs[0],p.inputs['Roughness'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=105;fine.inputs['Detail'].default_value=2
    l.new(geo.outputs['Position'],fine.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0035
    l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    p.inputs['Coat Weight'].default_value=.65;p.inputs['Coat Roughness'].default_value=.07
    return ma

def pool_material():
    ma=b.material('P8 feathered rainwater film',(.014,.024,.031),.055,.22)
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.7
    attr=n.new('ShaderNodeAttribute');attr.attribute_name='WaterCoverage'
    trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(attr.outputs['Color'],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs[0])
    return ma

def build():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8_surroundings_lit.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.GROUP='background'
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(ob.get('layer','background'),[]).append(ob)
    asphalt=wet_material();water=pool_material()
    for ob in sc.objects:
        if ob.name.startswith('Wet street'):ob.data.materials.clear();ob.data.materials.append(asphalt)
        if ob.name.startswith('Rainwater pool'):
            ob.data.materials.clear();ob.data.materials.append(water)
            att=ob.data.color_attributes.new(name='WaterCoverage',type='FLOAT_COLOR',domain='POINT')
            for i,c in enumerate(att.data):c.color=(.88,.88,.88,1) if i==0 else (0,0,0,1)
        if ob.name.startswith(('Wet paving slab','Curb stone','P8 opposite paved sidewalk','P8 gravel roof')):
            old=ob.data.materials[0];name='P8 wet finish '+old.name
            ma=bpy.data.materials.get(name) or old.copy();ma.name=name;ob.data.materials[0]=ma
            p=ma.node_tree.nodes.get('Principled BSDF')
            if p:p.inputs['Coat Weight'].default_value=.42;p.inputs['Coat Roughness'].default_value=.10
    # A recessed mat is flush with the old floor. The slim frame is its high edge.
    rim=b.material('P8 threshold rubbed pewter',(.21,.20,.17),.43,.5,texture=65)
    rubber=b.material('P8 entrance charcoal coir',(.032,.035,.029),.98,texture=120)
    dark=b.material('P8 mat drainage grooves',(.012,.017,.016),.87)
    for u0,v0,u1,v1 in [(8.52,8.45,10.48,8.48),(8.52,8.93,10.48,8.96),(8.52,8.48,8.55,8.93),(10.45,8.48,10.48,8.93)]:
        b.box('P8 recessed mat border',u0,v0,u1,v1,.025,.24,rim,.009)
    b.box('P8 recessed entrance mat',8.55,8.48,10.45,8.93,.07,.15,rubber,.008)
    for i in range(24):
        u=8.59+i*.077;b.line('P8 coir mat rib',[xyz(u,8.50,.17),xyz(u,8.91,.17)],dark,.006)
    b.box('P8 worn entrance threshold',8.43,9.015,10.57,9.13,.04,.22,rim,.009)
    for i in range(26):
        u=8.50+i*.077;b.line('P8 threshold scratch',[xyz(u,9.03,.25),xyz(u+.025,9.10,.25)],dark,.0018)
    # Drainage is actual geometry at the curb, outside the vehicle/walking strip.
    for v in [10.56,13.56]:
        b.box('P8 wet gutter channel',-12,v-.025,23,v+.025,.07,.10,bpy.data.materials['P8 wet'],0)
        for u in [2.8,8,14]:
            b.box('P8 additional drain bed',u,v-.09,u+.46,v+.06,.12,.15,dark,.004)
            for i in range(9):b.box('P8 drain grille bar',u+i*.052,v-.09,u+i*.052+.016,v+.06,.15,.21,rim,.002)
    sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.use_compositing=False
    sc.cycles.samples=96;sc.cycles.adaptive_threshold=.012;sc.cycles.use_denoising=True
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass8.blend'))
    status('Wet street/roof materials, feathered water films, curb drains, recessed entrance mat and worn threshold modelled')
    return sc

def main():
    assert json.loads((QA/'surroundings_occlusion.json').read_text())['covered_action_pixels']==0
    started=time.perf_counter();sc=build();timings=[]
    # Camera-invisible old occluders continue casting shadows and bouncing light;
    # their original whole sprites/depth slices remain unchanged in the pack.
    b.set_visibility('background')
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        if scale==1:
            for aov in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(aov)
            depth_pass.configure(sc,QA/'position_exr');sc.render.use_compositing=True
        else:sc.render.use_compositing=False
        t=time.perf_counter();render(QA/('steady_bg'+suffix+'.png'));timings.append({'scale':scale,'seconds':round(time.perf_counter()-t,3)})
        if scale==1:
            files=list((QA/'position_exr').glob('*.exr'));assert len(files)==1,files
            im=bpy.data.images.load(str(files[0]),check_existing=False);w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a)
            a=a.reshape(h,w,4)[::-1].copy();position=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-7)
            np.savez_compressed(QA/'world_positions.npz',position=position)
        status('Final steady wet background rendered at '+str(1920*scale)+'x'+str(1080*scale))
    (QA/'wet_scene_metadata.json').write_text(json.dumps({'timings':timings,'seconds':round(time.perf_counter()-started,3),
        'entrance_mat_uv':[8.52,8.45,10.48,8.96],'threshold_uv':[8.43,9.015,10.57,9.13],
        'unchanged_published_footprints':True,'surface_changes_only':True},indent=2))

if __name__=='__main__':main()
