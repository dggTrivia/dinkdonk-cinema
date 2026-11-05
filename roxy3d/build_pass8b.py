"""Targeted pass-8 polish: roof silhouette, wet material breakup, carpet repair."""
import sys,json,time,math,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
import build_scene as b
import build_pass8 as city
import depth_pass
from common import xyz,ZPP,render,project
from pass8b_common import ROOT,QA,OUT,LIVE,status,gpu

def mottled(name,color,rough=(.07,.62),scale=5):
    ma=b.material(name,color,.3,.08);n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.8
    l.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.23;ramp.color_ramp.elements[0].color=(.23,.27,.29,1)
    ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(1,1,1,1)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(*color,1)
    l.new(ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
    roughmap=n.new('ShaderNodeMapRange');roughmap.inputs['From Min'].default_value=.30;roughmap.inputs['From Max'].default_value=.66
    roughmap.inputs['To Min'].default_value=rough[0];roughmap.inputs['To Max'].default_value=rough[1]
    l.new(noise.outputs['Fac'],roughmap.inputs[0]);l.new(roughmap.outputs[0],p.inputs['Roughness'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=82;fine.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],fine.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.008
    l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    p.inputs['Coat Weight'].default_value=.28;p.inputs['Coat Roughness'].default_value=.12
    return ma

def assign(ob,ma):ob.data.materials.clear();ob.data.materials.append(ma)

def build():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.GROUP='background';QA.mkdir(exist_ok=True)
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(ob.get('layer','background'),[]).append(ob)
    removed=[]
    for ob in list(sc.objects):
        if ob.name.startswith('Worn carpet diamond'):
            removed.append(ob.name);b.GROUPS['background'].remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    assert len(removed)==18,removed
    # The existing diamonds project to horizontal rectangles under this camera.
    # Remove the outlined motifs; original weave, worn route and medallion stay.
    road=mottled('P8B rough wet asphalt',(.016,.021,.028),(.10,.63),7.8)
    alley=mottled('P8B stained wet alley concrete',(.018,.022,.026),(.18,.86),3.7)
    alley.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.10
    alley.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.24
    roof=mottled('P8B dark weathered annex felt',(.033,.034,.031),(.11,.68),6.4)
    for ob in sc.objects:
        if ob.name.startswith('Wet street'):assign(ob,road)
        if ob.name.startswith('P8 right service alley'):assign(ob,alley)
        if ob.name.startswith(('P8 gravel roof','P8 roof felt patch')) and ob.location.x>13:assign(ob,roof)
    # Existing water pools get broken coverage and rough islands, preserving
    # transparent boundaries while revealing the actual asphalt below them.
    ma=bpy.data.materials['P8 feathered rainwater film'];n=ma.node_tree.nodes;l=ma.node_tree.links
    p=n.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.28
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9.1;noise.inputs['Detail'].default_value=4
    l.new(geo.outputs['Position'],noise.inputs['Vector']);ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.30;ramp.inputs['From Max'].default_value=.65
    ramp.inputs['To Min'].default_value=.10;ramp.inputs['To Max'].default_value=.85;l.new(noise.outputs['Fac'],ramp.inputs[0])
    attr=next(x for x in n if x.type=='ATTRIBUTE');mix=next(x for x in n if x.type=='MIX_SHADER')
    mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(attr.outputs['Color'],mult.inputs[0]);l.new(ramp.outputs[0],mult.inputs[1]);l.new(mult.outputs[0],mix.inputs[0])
    rough=n.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.06;rough.inputs['To Max'].default_value=.34
    l.new(noise.outputs['Fac'],rough.inputs[0]);l.new(rough.outputs[0],p.inputs['Roughness'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=65;l.new(geo.outputs['Position'],fine.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.006
    l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    joint=b.material('P8B concrete joint dirt',(.010,.014,.015),.98)
    new=[]
    for u in np.arange(13.12,23,.78):new.append(b.line('P8B alley expansion joint',[xyz(u,-.9,-.31),xyz(u,9.11,-.31)],joint,.006))
    for v in np.arange(-.9,9.1,.78):new.append(b.line('P8B alley transverse joint',[xyz(13.1,v,-.31),xyz(23,v,-.31)],joint,.006))
    rng=random.Random(81020)
    for i in range(18):
        u=rng.uniform(13.15,17.8);v=rng.uniform(3,9.05);r=rng.uniform(.12,.35)
        # Small irregular water films, with feathered vertex coverage.
        pts=[xyz(u,v,-.29)]+[xyz(u+math.cos(k*math.tau/20)*r*(.7+rng.random()*.5),v+math.sin(k*math.tau/20)*r*.65,-.29) for k in range(20)]
        ob=b.mesh('P8B alley puddle',pts,[(0,1+k,1+(k+1)%20) for k in range(20)],ma);new.append(ob)
        att=ob.data.color_attributes.new(name='WaterCoverage',type='FLOAT_COLOR',domain='POINT')
        for j,c in enumerate(att.data):c.color=(.9,.9,.9,1) if j==0 else (0,0,0,1)
    # Low, irregular distant roofs sit wholly behind v=0. They intercept the
    # formerly ruler-straight rear terrain boundary without entering action rays.
    brick=b.material('P8B distant rain brick',(.030,.034,.052),.91,texture=46)
    tar=b.material('P8B distant felt roof',(.022,.028,.043),.47,texture=65)
    coping=b.material('P8B haze lit coping',(.065,.065,.085),.71)
    warm=b.material('P8B distant dim window',(.14,.09,.045),.8,emit=.32)
    blocks=[(-2.6,-4.6,-1.2,-2.8,108),(-1.3,-5.0,.1,-3.25,155),(.2,-4.8,1.6,-3.4,189),(1.6,-4.5,3.15,-2.8,162),(3.0,-3.5,4.45,-1.95,140)]
    for i,(u0,v0,u1,v1,h) in enumerate(blocks):
        new.append(b.box('P8B irregular distant masonry',u0,v0,u1,v1,-160,h,brick,.015))
        new.append(b.box('P8B distant sloped-height roof',u0,v0,u1,v1,h,h+2,tar,.004))
        for a,c in [(u0,u0+.045),(u1-.045,u1)]:new.append(b.box('P8B distant coping',a,v0,c,v1,h,h+5,coping,.005))
        new.append(b.box('P8B roof stair head',u0+.15,v0+.15,u0+.65,v0+.65,h,h+23,brick,.012))
        new.append(b.cylinder('P8B distant roof chimney',xyz(u1-.22,v0+.35,h+16),.07,32/ZPP,tar,vertices=12))
        for uu in np.arange(u0+.18,u1-.1,.32):
            for zz in np.arange(h-55,h-10,22):
                if rng.random()<.35:new.append(b.box('P8B hazy distant window',uu,v1,uu+.10,v1+.005,zz,zz+9,warm,0))
    receivers=bpy.data.collections.new('P8B distant fill receivers');sc.collection.children.link(receivers)
    for ob in new:
        ob['pass8b_surrounding']=True
        if ob.name.startswith('P8B distant') or ob.name.startswith('P8B irregular') or ob.name.startswith('P8B roof stair'):
            receivers.objects.link(ob);ob.visible_shadow=False
    light=b.area('P8B hazy roof fill',xyz(1,-7,480),700,(.52,.39,.64),14,target=xyz(1,-3,120));light.light_linking.receiver_collection=receivers
    light=b.area('P8B distant facade haze fill',xyz(1,3,300),550,(.48,.45,.63),12,target=xyz(1,-3,80));light.light_linking.receiver_collection=receivers
    # More uneven cloud illumination; the original dome/projection remains.
    sky=bpy.data.materials['P8 indigo cloud dome'];n=sky.node_tree.nodes
    noise=next(x for x in n if x.type=='TEX_NOISE');noise.inputs['Scale'].default_value=.22;noise.inputs['Detail'].default_value=4
    mix=next(x for x in n if x.type=='MIX_RGB');mix.inputs[0].default_value=.78
    fog=bpy.data.materials['P8 distant rain haze'];vol=next(x for x in fog.node_tree.nodes if x.type=='PRINCIPLED_VOLUME')
    vol.inputs['Density'].default_value=.0055;vol.inputs['Emission Strength'].default_value=.0032
    volume=bpy.data.objects['P8 distant atmospheric volume']
    # Extend the rear atmosphere up to, but never into, the cinema v=0 wall.
    volume.location.y=(80+.05)/2;volume.scale.y=(80-.05)/(80-6)
    # Local warm spill creates real soft reflections on the darker forecourt.
    lamp=b.area('P8B records sign ground spill',xyz(16.2,6.7,46),8,(.80,.65,.42),1.9,target=xyz(14.2,8.3,-.3))
    alley_receiver=bpy.data.collections.new('P8B alley light receiver');sc.collection.children.link(alley_receiver)
    for ob in sc.objects:
        if ob.name.startswith(('P8 right service alley','P8B alley')):alley_receiver.objects.link(ob)
    lamp.light_linking.receiver_collection=alley_receiver
    sc.render.use_compositing=False;sc.render.use_border=False;sc.render.use_crop_to_border=False
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.cycles.samples=64;sc.cycles.adaptive_threshold=.016
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'))
    (QA/'scene_changes.json').write_text(json.dumps({'removed_carpet_outline_objects':removed,'new_geometry':len(new),'rear_blocks':blocks,
        'unchanged_camera':True,'material_targets':['road','existing water films','right forecourt','right roofs'],'source':'roxy_pass8.blend'},indent=2))
    status('Distant roofs/cloud light/haze modelled; asphalt/puddle breakup and darker jointed alley/roof materials applied; 18 screen-aligned carpet outlines removed')
    return sc

def holdout(scale):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'))
    city.QA=QA;city.status=status;city.NEW.clear();city.REGIONS.clear()
    city.NEW.extend(ob for ob in bpy.context.scene.objects if ob.get('pass8_surrounding') or ob.get('pass8b_surrounding'))
    city.REGIONS.extend(json.loads((ROOT/'qa8/surroundings_regions.json').read_text()))
    city.holdout(scale)

def main():
    sc=build();render(QA/'preview_surroundings.png');status('Lit polish preview rendered before weather loops')
    for scale in [1,2]:holdout(scale)
    if '--preview' in sys.argv:return
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear()
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(ob.get('layer','background'),[]).append(ob)
    b.set_visibility('background');sc.cycles.samples=96;sc.cycles.adaptive_threshold=.012
    times=[]
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        if scale==1:
            for aov in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(aov)
            depth_pass.configure(sc,QA/'position_exr');sc.render.use_compositing=True
        else:sc.render.use_compositing=False
        t=time.perf_counter();render(QA/('steady_bg'+suffix+'.png'));times.append({'scale':scale,'seconds':time.perf_counter()-t})
        if scale==1:
            path=next((QA/'position_exr').glob('*.exr'));im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size
            a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(h,w,4)[::-1].copy()
            position=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-7)
            np.savez_compressed(QA/'world_positions.npz',position=position)
        status('Weather-free lit background rendered at '+str(1920*scale)+'x'+str(1080*scale))
    (QA/'render_times.json').write_text(json.dumps(times,indent=2))

if __name__=='__main__':main()
