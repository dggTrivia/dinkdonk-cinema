"""Brief 15 model fixes and an independently implemented periodic ripple shader.

No GPL source is copied. The method uses hashed cell centres, a smooth travelling
radial wave envelope and circular 4-D noise, implemented with Blender nodes.
"""
import sys,json,math,time,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
import build_scene as b
import build_pass10_draft as d
import build_pass10_draft3 as d3
from common import xyz,ZPP,project,render
from pass8_common import gpu
from draft4_common import ROOT,QA,WORK,status,report,W,H,N,FPS
META={'brief':'BRIEF-15-draft4.md','draft_only':True,'removed':[],'roof_kit':[],'reflection_proxy_lights_removed':[]}
R=random.Random(101504)
def rm(o):META['removed'].append(o.name);d.rm(o)
def box(n,*args):return b.box('D4 '+n,*args)
def line(n,pts,ma,r=.012):return b.line('D4 '+n,[xyz(*q) for q in pts],ma,r)
def cyl(n,u,v,z,r,h,ma):return b.cylinder('D4 '+n,xyz(u,v,z+h/2),r,h/ZPP,ma,vertices=32)

def apartment(sc):
    b.layer('background');bpy.context.view_layer.update()
    for o in list(sc.objects):
        if o.type not in ['MESH','CURVE','FONT']:continue
        a,v,c,w,z,h=d.bounds(o)
        if a>=-5.22 and c<=-.01 and v>=-1.1 and w<=8.8 and z>=234:rm(o)
    ma=bpy.data.materials['D3 mottled mineral felt'];brick=bpy.data.materials['P8 brick'];metal=bpy.data.materials['D3 charcoal wet steel'];rust=bpy.data.materials['D3 rust'];concrete=bpy.data.materials['D3 aged limestone cut cap'];dark=bpy.data.materials['D3 ink'];glass=bpy.data.materials['P8 amber']
    # One single face: no join at the former extension boundary, no overlapped
    # surfaces, and no change of material. One connected ring parapet outside it.
    b.mesh('D4 one continuous apartment felt roof',[xyz(u,v,235.11) for u,v in [(-5,-1),(-.075,-1),(-.075,8.7),(-5,8.7)]],[(3,2,1,0)],ma)
    outer=[(-5,-1),(-.075,-1),(-.075,8.7),(-5,8.7)];inner=[(-4.88,-.88),(-.195,-.88),(-.195,8.58),(-4.88,8.58)]
    verts=[xyz(u,v,z) for z in [235,241] for path in [outer,inner] for u,v in path];faces=[]
    for k in range(4):
        j=(k+1)%4;faces.extend([(k,j,8+j,8+k),(4+j,4+k,12+k,12+j),(8+k,8+j,12+j,12+k)])
    b.mesh('D4 single perimeter apartment parapet',verts,faces,brick)
    b.mesh('D4 continuous perimeter stone cap',[xyz(u,v,242) for path in [outer,inner] for u,v in path],[(k,(k+1)%4,4+(k+1)%4,4+k) for k in range(4)],concrete)
    def unit(u,v,label):
        box(label+' feet',u-.47,v-.34,u+.47,v+.34,235.15,240,rust,.008)
        box(label+' AC case',u-.44,v-.31,u+.44,v+.31,240,262,metal,.008)
        for dx in [-.22,.22]:
            cyl(label+' fan well',u+dx,v,262,.175,.4,dark)
            for j in range(5):
                t=j*math.tau/5;pts=[xyz(u+dx+.025*math.cos(t),v+.025*math.sin(t),262.6),xyz(u+dx+.15*math.cos(t+.2),v+.15*math.sin(t+.2),262.6),xyz(u+dx+.14*math.cos(t+.9),v+.14*math.sin(t+.9),262.6)]
                b.mesh('D4 '+label+' fan vane',pts,[(0,1,2)],metal)
            for r in [.09,.15]:line(label+' fan guard',[(u+dx+r*math.cos(t),v+r*math.sin(t),263) for t in np.linspace(0,math.tau,33)],concrete,.0035)
        for u2 in np.arange(u-.37,u+.37,.09):box(label+' intake',float(u2),v+.312,float(u2)+.042,v+.319,244,256,dark,0)
        META['roof_kit'].append({'name':label,'uv':[u,v]})
    unit(-3.72,1.15,'north mechanical');unit(-1.02,6.48,'south mechanical')
    for u,v,label in [(-3.65,6.35,'southwest skylight'),(-1.15,1.65,'northeast skylight')]:
        box(label+' kerb',u-.38,v-.27,u+.38,v+.27,235.15,242,metal,.006)
        box(label+' wired glass',u-.34,v-.23,u+.34,v+.23,242,243,glass,.004)
        for dx in [-.21,0,.21]:box(label+' wire bars',u+dx-.008,v-.23,u+dx+.008,v+.23,243,243.5,metal,0)
        META['roof_kit'].append({'name':label,'uv':[u,v]})
    box('central roof access hatch',-2.95,3.95,-2.15,4.7,235.15,242,metal,.01)
    line('hatch handle',[(-2.66,4.25,242),(-2.66,4.25,245),(-2.45,4.25,245),(-2.45,4.25,242)],concrete,.011)
    META['roof_kit'].append({'name':'central hatch','uv':[-2.55,4.325]})
    for u,v,z in [(-.66,3.75,27),(-4.38,4.65,21),(-3.91,7.65,30)]:
        cyl('roof vent boot',u,v,235.15,.17,2,rust);cyl('roof ventilator',u,v,237,.085,z,metal);cyl('roof vent cap',u,v,237+z,.13,2,metal)
        META['roof_kit'].append({'name':'vent','uv':[u,v]})
    line('north extraction duct',[(-3.72,1.48,247),(-3.72,2.5,247),(-3.25,2.5,247),(-3.25,2.5,260)],metal,.08)
    line('south extraction duct',[(-1.02,6.15,248),(-1.02,5.40,248),(-1.55,5.40,248)],metal,.07)
    line('roof aerial',[(-.63,.15,235),(-.63,.15,279)],metal,.012)
    for z in [265,275]:line('roof aerial bars',[(-.92,.15,z),(-.34,.15,z)],metal,.007)
    for u,v in [(-3.0,.0),(-.60,7.9)]:cyl('chimney pot',u,v,235.15,.10,22,rust)
    # All roof wear is on this same felt face, lifted enough to avoid z fighting.
    d3.MA={m.name[3:]:m for m in bpy.data.materials if m.name.startswith('D3 ')}
    for u,v,rx,ry in [(-2.6,1.2,.50,.22),(-3.6,3.4,.35,.28),(-1.5,4.6,.45,.21),(-2.7,7.55,.55,.30),(-.5,2.55,.17,.4)]:
        d3.irregular('D4 apartment shallow reflective water',u,v,235.16,rx,ry,bpy.data.materials['D3 feathered reflective water'],.47)
    for u,v in [(-4.6,1.0),(-2.1,2.8),(-.8,5.0),(-4.1,7.8)]:
        b.mesh('D4 felt repair',[xyz(u+x,v+y,235.14) for x,y in [(-.25,-.22),(.27,-.20),(.25,.24),(-.21,.19)]],[(3,2,1,0)],bpy.data.materials['D3 patched felt'])
    bpy.context.view_layer.update()
    for o in sc.objects:
        if o.name.startswith(('D4 ','D3 D4 apartment')) and o.type in ['MESH','CURVE','FONT']:
            for cname in ['P8 surroundings light receivers','P9 west fill receivers']:
                col=bpy.data.collections.get(cname)
                if col and o.name not in col.objects:col.objects.link(o)
    META['apartment_roof']={'single_face':True,'uv':[-5,-1,-.075,8.7],'roof_z':235.11,'material':ma.name,'continuous_parapet':True}
    status('owner fix 29: single seamless felt roof and continuous perimeter parapet rebuilt; AC, vents, skylights, hatch and ducts spread across the entire apartment roof')

def reflections(sc):
    explicit=['P10 sign street green reflection','P10 entrance frog green spill','P10 entrance triangle yellow spill','P10 rooftop neon cyan cast','P10 rooftop frog warm cast','D3 alley wet neon bounce']
    for o in list(sc.objects):
        if o.type=='LIGHT' and (o.name in explicit or o.name.startswith(('P9 blue neon wall spill','P9 mint neon sidewalk spill','Neon storefront reflected glow'))):
            META['reflection_proxy_lights_removed'].append(o.name);rm(o)
    changed=[]
    for o in sc.objects:
        if o.type=='LIGHT' and any(s in o.name.lower() for s in ['fill','bounce','spill','pool']):
            # Scene-lighting helpers may illuminate architecture but should not
            # appear as invented rectangular/neon sources in wet reflections.
            o.data.specular_factor=0;changed.append(o.name)
        if o.type in ['MESH','CURVE','FONT']:o.visible_glossy=True
    # The actual small luminous tubes are the reflection sources. Preserve
    # their geometry and colour, with a radiance suitable for physical bounce.
    emissive=[]
    for ma in bpy.data.materials:
        if not ma.node_tree:continue
        p=ma.node_tree.nodes.get('Principled BSDF')
        if not p:continue
        if ma.name.startswith('P10 ') and any(k in ma.name for k in ['tube core','white eye tube','cyan rooftop letter core','neon lips','bell gold neon']):
            old=p.inputs['Emission Strength'].default_value;p.inputs['Emission Strength'].default_value=max(old,18 if 'lips' not in ma.name else 9)
            emissive.append({'material':ma.name,'radiance_before':old,'radiance_after':p.inputs['Emission Strength'].default_value})
    META['reflection_sources']={'new_cycles_beauty_only':True,'prior_reflection_frames_used':False,'scene_images':[im.filepath for im in bpy.data.images if im.filepath],'helper_specular_disabled':changed,'actual_tube_materials':emissive}
    status('owner fix 31: obsolete broad neon/reflection helper lights removed; current tube geometry supplies coloured reflections, with no prior rendered reflection basis reused')

def ripple_group():
    g=bpy.data.node_groups.new('D4 periodic ray-traced rain ripple normals','ShaderNodeTree');n=g.nodes;l=g.links
    g.interface.new_socket(name='Normal In',in_out='INPUT',socket_type='NodeSocketVector')
    s=g.interface.new_socket(name='Strength',in_out='INPUT',socket_type='NodeSocketFloat');s.default_value=.6
    g.interface.new_socket(name='Normal',in_out='OUTPUT',socket_type='NodeSocketVector');g.interface.new_socket(name='Height',in_out='OUTPUT',socket_type='NodeSocketFloat')
    gi=n.new('NodeGroupInput');go=n.new('NodeGroupOutput')
    def mathn(op,a,bv=None):
        q=n.new('ShaderNodeMath');q.operation=op
        for i,val in enumerate([a,bv]):
            if val is None:continue
            if isinstance(val,(int,float)):q.inputs[i].default_value=val
            else:l.new(val,q.inputs[i])
        return q.outputs[0]
    def vec(op,a,bv=None):
        q=n.new('ShaderNodeVectorMath');q.operation=op
        for i,val in enumerate([a,bv]):
            if val is None:continue
            if isinstance(val,(tuple,list)):q.inputs[i].default_value=val
            else:l.new(val,q.inputs[i])
        return q.outputs['Value'] if op in ['LENGTH','DISTANCE','DOT_PRODUCT'] else q.outputs['Vector']
    time=n.new('ShaderNodeValue');time.name='Time seconds';time.outputs[0].default_value=0
    geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0]);flat=n.new('ShaderNodeCombineXYZ');l.new(sep.outputs['X'],flat.inputs[0]);l.new(sep.outputs['Y'],flat.inputs[1])
    coord=vec('MULTIPLY',flat.outputs[0],(1/.62,1/.62,0));grid=vec('FLOOR',coord)
    height=None
    for ix in [-1,0,1]:
        for iy in [-1,0,1]:
            cell=vec('ADD',grid,(ix,iy,0));rnd=n.new('ShaderNodeTexWhiteNoise');rnd.noise_dimensions='3D';l.new(cell,rnd.inputs['Vector'])
            cs=n.new('ShaderNodeSeparateXYZ');l.new(rnd.outputs['Color'],cs.inputs[0]);centre=n.new('ShaderNodeCombineXYZ')
            for k in range(2):l.new(mathn('ADD',mathn('MULTIPLY',cs.outputs[k],.58),.21),centre.inputs[k])
            dist=vec('LENGTH',vec('SUBTRACT',coord,vec('ADD',cell,centre.outputs[0])))
            # Independent hashed phases; both periods divide the six-second
            # target, and the two-second proof loop closes without a reset.
            # The period must depend on the GLOBAL cell, not its relative
            # neighbour slot, otherwise the same ring changes at cell edges.
            period=mathn('ADD',1.0,mathn('GREATER_THAN',rnd.outputs['Value'],.5))
            phase=mathn('FRACT',mathn('ADD',mathn('DIVIDE',time.outputs[0],period),rnd.outputs['Value']))
            radius=mathn('ADD',mathn('MULTIPLY',phase,.48),.025);delta=mathn('SUBTRACT',dist,radius)
            ring=mathn('SINE',mathn('MULTIPLY',delta,78.0))
            envelope=mathn('EXPONENT',mathn('MULTIPLY',mathn('POWER',mathn('DIVIDE',delta,.075),2),-1))
            fade=mathn('POWER',mathn('SINE',mathn('MULTIPLY',phase,math.pi)),2)
            value=mathn('MULTIPLY',mathn('MULTIPLY',ring,envelope),fade)
            height=value if height is None else mathn('ADD',height,value)
    # Circular 4-D noise, including both cosine and sine coordinates, makes
    # wind/drizzle continuous through the two-second / six-second boundary.
    angle=mathn('MULTIPLY',time.outputs[0],math.tau/2)
    noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.6
    nc=n.new('ShaderNodeCombineXYZ');l.new(mathn('MULTIPLY',sep.outputs['X'],11),nc.inputs[0]);l.new(mathn('MULTIPLY',sep.outputs['Y'],11),nc.inputs[1]);l.new(mathn('MULTIPLY',mathn('COSINE',angle),.8),nc.inputs[2]);l.new(nc.outputs[0],noise.inputs['Vector']);l.new(mathn('MULTIPLY',mathn('SINE',angle),.8),noise.inputs['W'])
    height=mathn('ADD',mathn('MULTIPLY',height,.70),mathn('MULTIPLY',mathn('SUBTRACT',noise.outputs['Fac'],.5),.17))
    bump=n.new('ShaderNodeBump');bump.name='Ray traced ripple normal';bump.inputs['Distance'].default_value=.012;l.new(gi.outputs['Strength'],bump.inputs['Strength']);l.new(gi.outputs['Normal In'],bump.inputs['Normal']);l.new(height,bump.inputs['Height']);l.new(bump.outputs['Normal'],go.inputs['Normal']);l.new(height,go.inputs['Height'])
    return g

def install_ripples(sc):
    group=ripple_group();rows=[]
    for ma in bpy.data.materials:
        if not ma.node_tree:continue
        name=ma.name.lower();strength=None
        if 'feathered reflective water' in name:strength=.8
        elif 'rough wet asphalt' in name or 'patched alley asphalt' in name:strength=.42
        elif 'mottled mineral felt' in name or 'wet mineral felt' in name:strength=.24
        elif 'wet finish' in name and any(x in name for x in ['stone','concrete','gravel']):strength=.25
        elif name in ['paving','paving dark','paving light'] or ('wet paving' in name):strength=.25
        if strength is None:continue
        n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
        if not p:continue
        old=list(p.inputs['Normal'].links);node=n.new('ShaderNodeGroup');node.node_tree=group;node.name='D4 periodic ripple normals';node.inputs['Strength'].default_value=strength
        if old:l.new(old[0].from_socket,node.inputs['Normal In'])
        else:
            geo=n.new('ShaderNodeNewGeometry');l.new(geo.outputs['Normal'],node.inputs['Normal In'])
        l.new(node.outputs['Normal'],p.inputs['Normal']);rows.append({'material':ma.name,'strength':strength})
    # Wet pavement shader names can vary between passes; inspect actual slabs.
    for o in sc.objects:
        if o.name.startswith('Wet paving slab'):
            for ma in o.data.materials:
                if not ma or any(q['material']==ma.name for q in rows):continue
                n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
                if p:
                    old=list(p.inputs['Normal'].links);node=n.new('ShaderNodeGroup');node.node_tree=group;node.name='D4 periodic ripple normals';node.inputs['Strength'].default_value=.28
                    if old:l.new(old[0].from_socket,node.inputs['Normal In'])
                    else:
                        geo=n.new('ShaderNodeNewGeometry');l.new(geo.outputs['Normal'],node.inputs['Normal In'])
                    l.new(node.outputs['Normal'],p.inputs['Normal']);rows.append({'material':ma.name,'strength':.28})
    META['ripples']={'method':'original node implementation; no copied OpenMW code','cells':'3x3 neighbours, 0.62 world-tile grid, independent hashed centres/phases','drop_periods_seconds':[1,2],'test_period_seconds':2,'canonical_six_second_cycles':3,'wind':'4D noise: XY spatial, Z=0.8 cos(2pi t/2), W=0.8 sin(2pi t/2)','materials':rows,'fixed_seed':1701,'frames':N,'fps':FPS}
    status('test A periodic ripple normal group installed on puddles, asphalt, sidewalk and roofs; 1s/2s cell phases and circular 4D wind close exactly inside the six-second contract')

def quality(sc):
    sc.render.engine='CYCLES';sc.cycles.samples=256;sc.cycles.use_adaptive_sampling=False;sc.cycles.use_denoising=False;sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True;sc.cycles.seed=1701;sc.cycles.use_animated_seed=False
    sc.cycles.max_bounces=10;sc.cycles.diffuse_bounces=4;sc.cycles.glossy_bounces=6;sc.cycles.transmission_bounces=8;sc.cycles.transparent_max_bounces=24;sc.cycles.sample_clamp_direct=0;sc.cycles.sample_clamp_indirect=0
    sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100;sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.use_compositing=False;sc.render.use_sequencer=False;sc.render.use_persistent_data=True
    sc.render.fps=FPS;sc.render.fps_base=1;sc.render.film_transparent=False
    vl=sc.view_layers[0];vl.cycles.denoising_store_passes=True;vl.use_pass_vector=True;vl.use_pass_normal=True;vl.use_pass_emit=True;vl.use_pass_z=True
    sc.render.image_settings.media_type='MULTI_LAYER_IMAGE';sc.render.image_settings.file_format='OPEN_EXR_MULTILAYER';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='32';sc.render.image_settings.exr_codec='ZIP'

def main():
    bpy.ops.wm.open_mainfile(filepath=str(QA/'source_before_draft4.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.M.clear()
    for ma in bpy.data.materials:b.M[ma.name]=ma
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:
            b.GROUPS.setdefault(o.get('layer','background'),[]).append(o);o.visible_camera=True;o.hide_render=False;o.is_holdout=False
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf');apartment(sc);reflections(sc);install_ripples(sc);quality(sc)
    sc['draft_number']=4;sc['draft_brief']='BRIEF-15-draft4.md';sc['draft_only']=True;sc['draft_standard']='1280x720 / 256 samples / actual Cycles wet reflections'
    bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));report('scene.json',META)
    status('draft source saved with final-quality 720p settings, fixed seed, Denoising Data + Vector passes; no output pack pipeline invoked')
    t=time.perf_counter();sc.frame_set(1);sc.render.filepath=str(WORK/'preview_raw.exr');bpy.ops.render.render(write_still=True)
    report('preview_render.json',{'seconds':time.perf_counter()-t,'samples':256,'size':[W,H]});status('first 720p final-quality ray-traced ripple still rendered in %.1f s'%(time.perf_counter()-t))
    sc.cycles.use_denoising=True;bpy.ops.cycles.denoise_animation(input_filepath=str(WORK/'preview_raw.exr'),output_filepath=str(WORK/'preview_denoised.exr'))
    im=bpy.data.images.load(str(WORK/'preview_denoised.exr'));sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';im.save_render(str(QA/'test_ripples_still.png'),scene=sc)
    status('per-frame OptiX proof still saved for visual inspection before the short comparison clip')
if __name__=='__main__':main()
