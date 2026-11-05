"""Brief 18: update the saved Draft 6 model; deliver exactly one draft image."""
import sys, math, random, shutil
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
import build_scene as b
from common import ROOT, xyz, ZPP
from build_pass10_draft import UFACE
from build_pass10_draft4 import quality
from render_draft5 import optical
from pass8_common import gpu
from pngio import read, write

QA = ROOT/'qa10'
TMP = ROOT/'cache'/'draft7'
TMP.mkdir(parents=True, exist_ok=True)
R = random.Random(181007)

def rm(o):
    bpy.data.objects.remove(o, do_unlink=True)

def box(n, *args):
    return b.box('D7 '+n, *args)

def line(n, points, ma, radius=.006):
    return b.line('D7 '+n, [xyz(*p) for p in points], ma, radius)

def material(n, color, rough=.5, metal=0, coat=0):
    ma=b.material('D7 '+n, color, rough, metal)
    p=ma.node_tree.nodes.get('Principled BSDF')
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.24
    return ma

def print_material(n, path):
    ma=material(n, (.5,.5,.5), .57, coat=.18)
    nodes=ma.node_tree.nodes; links=ma.node_tree.links; p=nodes.get('Principled BSDF')
    im=bpy.data.images.load(str(path), check_existing=True); im.pack()
    tex=nodes.new('ShaderNodeTexImage'); tex.image=im; tex.interpolation='Closest'
    links.new(tex.outputs['Color'], p.inputs['Base Color'])
    trans=nodes.new('ShaderNodeBsdfTransparent'); mix=nodes.new('ShaderNodeMixShader')
    links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1]);links.new(p.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
    return ma

def picture(n, pts, ma):
    ob=b.mesh('D7 '+n,[xyz(*p) for p in pts],[(0,1,2,3)],ma)
    uv=ob.data.uv_layers.new()
    for i,p in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=p
    return ob

def lettering(n, body, u,v,z,size,ma,axis='v',width=None):
    ob=b.text('D7 '+n,body,xyz(u,v,z),size,ma,UFACE if axis=='u' else b.FRONT_FACE,extrude=.0015)
    ob.data.bevel_depth=.0006; ob.data.bevel_resolution=2
    bpy.context.view_layer.update()
    if width:
        span=max(p[0] for p in ob.bound_box)-min(p[0] for p in ob.bound_box)
        if span>width:ob.data.size*=width/span
    return ob

def link_exterior(objects, apartment=False):
    names=['P8 surroundings light receivers','P9 west fill receivers' if apartment else 'P10 multiplex roof light receivers']
    for o in objects:
        if o.type not in ['MESH','CURVE','FONT']:continue
        for name in names:
            col=bpy.data.collections.get(name)
            if col and o.name not in col.objects:col.objects.link(o)

def billboards(sc):
    # The old frame stays on the cinema, now carrying EatFresh. WCAT gets its
    # own opposite-facing, braced installation on the apartment roof.
    for o in list(sc.objects):
        if o.name.startswith(('D5 art wcat','D6 art eatfresh','D6 EatFresh wall frame')):rm(o)
    b.layer('draft7_apartment_billboard');before=set(sc.objects)
    steel=material('weathered billboard steel',(.045,.05,.058),.40,.72,.25)
    navy=material('rich charcoal pinstripe enamel',(.020,.021,.029),.48,.15,.27)
    stripe=material('subtle pinstripe',(.029,.031,.043),.57,.1,.2)
    gold=material('antique gold foil',(.64,.39,.115),.27,.82,.18)
    patina=material('billboard weathering',(.039,.027,.022),.82)
    u=-.90; v0=3.60; v1=7.50; z0=266; z1=365
    box('WCAT steel back',u-.10,v0-.035,u-.006,v1+.035,z0-2,z1+2,steel,.012)
    box('WCAT dark sign face',u-.009,v0,u,v1,z0,z1,navy,.003)
    for v in np.arange(v0+.06,v1,.085):line('WCAT fine pinstripe',[(u+.002,float(v),z0+1),(u+.002,float(v),z1-1)],stripe,.0011)
    # UV proportions preserve the original square DGG emote without redrawing it.
    cat=print_material('actual supplied WCAT emote',ROOT/'ref/wcat-emote/wcat.png')
    a=7.34;c=a-83/ZPP
    picture('WCAT actual emote',[(u+.005,a,274),(u+.005,c,274),(u+.005,c,357),(u+.005,a,357)],cat)
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/georgiab.ttf')
    lettering('WCAT gold slogan top',"IT'S JUST",u+.009,4.94,333,.33,gold,'u',2.08)
    lettering('WCAT gold slogan bottom','BUSINESS.',u+.009,4.94,308,.34,gold,'u',2.14)
    line('WCAT thin gold rule',[(u+.010,3.83,288),(u+.010,6.05,288)],gold,.005)
    for v in [v0+.27,v1-.27]:
        box('WCAT roof anchor foot',u-.34,v-.12,u+.07,v+.12,235.18,238.3,steel,.008)
        line('WCAT upright',[(u-.05,v,238),(u-.05,v,366)],steel,.027)
        line('WCAT rear diagonal brace',[(u-1.05,v,236),(u-.06,v,350)],steel,.021)
        box('WCAT rear brace shoe',u-1.16,v-.11,u-.93,v+.11,235.18,237.5,steel,.006)
        for du in [-.25,-.03]:b.ball('D7 WCAT anchor bolt',xyz(u+du,v,239),.016,gold,(1,1,.45))
    # Curved goosenecks and warm downlights are real geometry/light sources.
    lampmat=material('warm lamp lens',(.83,.72,.45),.25)
    p=lampmat.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.74,.40,1);p.inputs['Emission Strength'].default_value=2
    for v in [4.35,6.60]:
        pts=[(u-.07,v,352),(u-.07,v,367),(u-.05,v,373),(u+.01,v,377),(u+.13,v,379),(u+.32,v,379),(u+.46,v,375),(u+.49,v,369)]
        line('WCAT gooseneck lamp arm',pts,steel,.017)
        b.ball('D7 WCAT lamp hood',xyz(u+.49,v,368),.10,steel,(1.35,1,.48))
        b.ball('D7 WCAT lamp lens',xyz(u+.49,v,365.8),.075,lampmat,(1.2,1,.14))
        b.area('D7 WCAT warm downlight',xyz(u+.49,v,365.1),14,(1,.78,.51),.32,target=xyz(u+.008,v,316))
    for j in range(28):
        v=R.uniform(v0+.03,v1-.03);zz=z1-R.uniform(0,2)
        line('WCAT rain patina',[(u+.012,v,zz),(u+.012,v+.007,zz-R.uniform(2,9))],patina,.0014)
    for v in [v0+.025,v1-.025]:line('WCAT foil border',[(u+.012,v,z0+2),(u+.012,v,z1-2)],gold,.004)
    for z in [z0+2,z1-2]:line('WCAT foil border',[(u+.012,v0+.025,z),(u+.012,v1-.025,z)],gold,.004)
    link_exterior(set(sc.objects)-before,True)

    b.layer('ad_rooftop');before=set(sc.objects)
    cream=material('EatFresh warm cream print',(.72,.64,.47),.65,coat=.18)
    coral=material('EatFresh coral print',(.46,.075,.06),.64)
    ink=material('EatFresh navy print',(.025,.028,.051),.60)
    blank=sc.objects.get('P10 roof billboard blank')
    if blank:blank.data.materials.clear();blank.data.materials.append(cream)
    # A new landscape layout fits the existing cinema billboard without
    # stretching the square approved emote or the former portrait poster.
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    for z in [288,352]:line('EatFresh coral rule',[(10.07,-3.524,z),(12.63,-3.524,z)],coral,.006)
    emote=print_material('actual supplied EatFresh emote',ROOT/'ref/eatfresh-emote/EatFresh.png')
    a=11.78;w=56/ZPP
    picture('EatFresh rooftop emote',[(a,-3.518,292),(a+w,-3.518,292),(a+w,-3.518,348),(a,-3.518,348)],emote)
    lettering('EatFresh roof heading','EAT OUR FRESH',10.91,-3.517,341,.18,coral,width=1.57)
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/impact.ttf')
    lettering('EatFresh roof main','NOTHING',10.91,-3.517,323,.30,ink,width=1.57)
    lettering('EatFresh roof lower','BURGERS',10.91,-3.517,303,.30,ink,width=1.57)
    link_exterior(set(sc.objects)-before)

def signs_and_cuts(sc):
    for o in list(sc.objects):
        if o.name.startswith(('P9 hanging wayfinding','P9 suspension rod')):rm(o)
    b.layer('draft7_interior')
    steel=material('wayfinding dark enamel',(.025,.035,.038),.36,.45)
    ivory=material('wayfinding warm white',(.78,.77,.62),.46)
    brass=material('interior brass fixings',(.42,.28,.10),.33,.78)
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    # Flat wall plates: thickness and four visible screw heads sit against
    # existing masonry. Neither sign depends on a cut-away ceiling.
    box('WC wall plaque backing',.012,2.30,.064,2.96,130,145,steel,.007)
    lettering('WC wall directions','WC <',.071,2.63,137.3,.139,ivory,'u',.57)
    for v in [2.34,2.92]:
        for z in [132.2,142.8]:b.ball('D7 WC plaque screw',xyz(.073,v,z),.011,brass,(.4,1,1))
    box('screens wall plaque backing',3.025,.014,3.875,.066,132,147,steel,.007)
    lettering('screens wall directions','> 1-3',3.45,.073,139.5,.15,ivory,width=.74)
    for u in [3.065,3.835]:
        for z in [134.2,144.8]:b.ball('D7 screens plaque screw',xyz(u,.075,z),.011,brass,(1,.4,1))
    # The existing double-faced RESTROOM plaque already has a full lintel;
    # wrap its jamb/lintel connection with an explicit metal mounting surround.
    for u in [.94,1.82]:box('restroom plaque jamb mounting',u,2.876,u+.04,3.128,104,123,steel,.004)
    box('restroom plaque fixed top rail',.94,2.876,1.86,3.128,122,123.4,steel,.004)
    for u in [1.00,1.80]:
        for v in [2.873,3.132]:
            for z in [111,120]:b.ball('D7 restroom plaque screw',xyz(u,v,z),.009,brass,(1,.4,1))
    # One 88-unit partition section continues around the ticket/restroom
    # return and service divider. Full doorway walls remain full doorway walls.
    for o in list(sc.objects):
        if o.name.startswith(('P10 restroom cutaway right nib','P10 closet divider cutaway','D3 restroom low return cut','D3 restroom service end cut','D3 ticket partition cut')):rm(o)
    core=bpy.data.materials['D3 cut plaster core']
    plaster=bpy.data.materials['old plaster']
    teal=bpy.data.materials['P10 restroom teal partitions']
    purple=bpy.data.materials['wall plum']
    box('restroom aligned partition return',2.90,3.08,3.10,4.40,0,88,plaster,.008)
    box('restroom service divider',.02,8.35,2.90,8.44,0,88,teal,.006)
    def cap(name,a,v,c,w,axis,inside):
        box(name+' exposed core',a,v,c,w,88,89.6,core,.002)
        if axis=='u':
            box(name+' room finish',a,v,a+.024,w,89.6,89.9,teal,0)
            box(name+' lobby finish',c-.024,v,c,w,89.6,89.9,inside,0)
        else:
            box(name+' room finish',a,v,c,v+.024,89.6,89.9,teal,0)
            box(name+' outer finish',a,w-.024,c,w,89.6,89.9,inside,0)
    cap('continuous ticket restroom cap',2.90,3.08,3.10,8.90,'u',purple)
    cap('matching service divider cap',.02,8.35,2.90,8.44,'v',teal)

def padded_doors(sc):
    b.layer('draft7_theatre_doors')
    leather=material('oxblood leather upholstery',(.19,.018,.028),.43,coat=.27)
    nodes=leather.node_tree.nodes;links=leather.node_tree.links;p=nodes.get('Principled BSDF')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=185;noise.inputs['Detail'].default_value=2
    bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.0007;bump.inputs['Strength'].default_value=.22
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
    thread=material('burgundy upholstery stitching',(.075,.008,.014),.75)
    brass=material('worn theatre brass plates',(.46,.29,.095),.31,.82)
    for o in list(sc.objects):
        if o.name.startswith(('Porthole chrome','Porthole amber','Polished door pull','Door diamond stitching')):rm(o)
        elif o.name.startswith('Door brass kickplate'):
            o.data.materials.clear();o.data.materials.append(brass)
    leaves=[o for o in sc.objects if o.name.startswith('Upholstered cinema door')]
    for leaf in leaves:
        leaf.data.materials.clear();leaf.data.materials.append(leather)
        transform=leaf.matrix_world.copy();did=leaf.get('door_id');side=leaf.get('door_side')
        zc=54.75/ZPP;x0=-.202;x1=.202;za=17/ZPP-zc;zb=105/ZPP-zc
        def pos(x,y,z):return transform@Vector((x,y,z))
        def add_tags(o):
            o['door_id']=did;o['door_side']=side;o['draft7_padded_door']=True
            return o
        nx=28;nz=84;verts=[];faces=[]
        for j in range(nz+1):
            z=za+(zb-za)*j/nz
            for i in range(nx+1):
                x=x0+(x1-x0)*i/nx
                a=x/.19+z/.27;c=x/.19-z/.27
                bulge=.021*(max(0,math.sin(math.pi*a)**2*math.sin(math.pi*c)**2)**.38)
                verts.append(pos(x,-.024-bulge,z))
        for j in range(nz):
            for i in range(nx):
                k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
        ob=add_tags(b.mesh('D7 tufted diamond leather panel',verts,faces,leather))
        for poly in ob.data.polygons:poly.use_smooth=True
        for direction in [-1,1]:
            for k in range(-5,6):
                pts=[]
                for x in np.linspace(x0,x1,61):
                    z=(k-x/.19)*.27*direction
                    if za<=z<=zb:pts.append(pos(float(x),-.025,z))
                if len(pts)>1:add_tags(b.line('D7 diagonal upholstery seam',pts,thread,.0011))
        for a in range(-5,6):
            for c in range(-5,6):
                x=.095*(a+c);z=.135*(a-c)
                if x0+.01<x<x1-.01 and za+.02<z<zb-.02:
                    ob=add_tags(b.ball('D7 leather covered tuft button',pos(x,-.033,z),.012,leather,(1,.50,1)))
                    ob.rotation_mode='QUATERNION';ob.rotation_quaternion=transform.to_quaternion()
        # Push plates are on the latch edge of each existing leaf. Mapping
        # through its saved matrix also preserves the open second screen.
        latch=.15 if str(side) in ['-1','left','L'] else -.15
        if side in [None,'']:latch=.15 if int(leaf.name.split('.')[-1])%2==0 else -.15
        ob=box('brass push plate',latch-.036,.051,latch+.036,.064,49-54.75,76-54.75,brass,.004)
        ob.matrix_world=transform@ob.matrix_world;add_tags(ob)
        for z in [51,74]:
            ob=add_tags(b.ball('D7 push plate screw',pos(latch,-.066,(z-54.75)/ZPP),.006,brass,(1,.4,1)))

def rain_layer(sc):
    # A single current-scene weather frame uses the changed geometry as its
    # holdout, then is alpha-composited over the single beauty exposure.
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:o.is_holdout=True
    b.layer('draft7_weather');rng=random.Random(161005)
    ma=b.glass('D7 airborne rain',(.45,.54,.64),.24)
    p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.15;p.inputs['Coat Weight'].default_value=.6
    p.inputs['Emission Color'].default_value=(.12,.16,.22,1);p.inputs['Emission Strength'].default_value=.15
    regions=[(-12,9.18,23,13.5,.12,640),(-5,-1,-.075,8.7,235.2,120),(-4,-13,25,-.23,240.2,500),(13.08,.05,15,9,.08,80),(15,.6,17.5,6.4,58.1,35),(15,6.5,17.5,9.1,61.1,30),(-9.4,3.4,-5.1,7.35,95.1,30)]
    for u0,v0,u1,v1,z,n in regions:
        for i in range(n):
            u=rng.uniform(u0,u1);v=rng.uniform(v0,v1);zz=z+rng.uniform(3,190);length=rng.uniform(5,18)
            ob=line('airborne rain',[(u,v,zz),(u+.018,v-.006,zz-length)],ma,rng.uniform(.0015,.0037));ob.is_holdout=False;ob.visible_shadow=False
            link_exterior([ob])
    sc.render.use_compositing=False;sc.render.film_transparent=True

def main():
    source=ROOT/'roxy_pass10_draft.blend'
    backup=TMP/'source_draft6.blend'
    if not backup.exists():shutil.copy2(source,backup)
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
    b.GROUPS.clear();b.M.clear()
    billboards(sc);signs_and_cuts(sc);padded_doors(sc)
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    optical(sc);sc.compositing_node_group.name='D7 retained approved HDR glare'
    sc['draft7_only']=True;sc['draft7_brief']='BRIEF-18-draft7.md'
    sc.render.filepath=str(QA/'draft_7.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    print('D7 model saved; rendering the one fixed-camera draft and its weather layer',flush=True)
    # Intermediate render buffers stay in cache and are removed immediately
    # after composition; the only delivered image is qa10/draft_7.png.
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png'
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True)
    rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True)
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False)
    alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8)
    write(QA/'draft_7.png',out)
    beauty.unlink();weather.unlink()
    stamp=datetime.now().astimezone().isoformat(timespec='seconds')
    (QA/'DRAFT-7.md').write_text(
        '# Draft 7\n\n'
        'Built from the saved Draft 6 scene; updated `roxy_pass10_draft.blend`.\n'
        'WCAT now faces the other isometric direction on the apartment roof: actual supplied emote, dark pinstripe ground, gold serif business slogan, braced supports and gooseneck lamps. EatFresh occupies the freed cinema billboard.\n'
        'Wayfinding is screwed flat to the walls; the restroom plaque is visibly fixed to its doorway. The low ticket/restroom return and service divider share the 88-unit cut and wall-thickness cap. Theatre leaves have tufted diamond leather, covered buttons and brass push/kick plates; portholes removed.\n'
        'Delivered only `draft_7.png`: fixed camera, 1280×720, Cycles 256 samples, retained wet materials/ray-traced reflections/soft ripples/HDR glare, with one current-scene holdout-occluded rain frame composited. No review views, clips, audits, rerenders or out10 work.\n',encoding='utf-8')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:
        f.write(stamp+' | Finished: Draft 7 owner fixes 43–46; saved draft model and one 1280×720 / 256-sample weather-composited draft_7.png; DRAFT-7.md written; stopped.\n')
    print('D7 COMPLETE: qa10/draft_7.png, DRAFT-7.md, one STATUS line. STOP.',flush=True)

if __name__=='__main__':main()
