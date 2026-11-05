"""THE ROXY. Procedural dimetric cinema, Blender 5.2.3 / Cycles.

All geometry, patterns, artwork and lights are generated here, with a fixed seed.
No network access or downloaded assets. Coordinates throughout are page tiles and
page z pixels. See NOTES.md for the layer contract and reproduction commands.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import math
import random
import json
import time
import argparse
import shutil
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from common import ROOT, PPU, ZPP, RIGHT, UP, NORMAL, xyz, project, screen_point, setup, render

RNG = random.Random(1997)
GROUP = 'background'
GROUPS = {}
META = {}
M = {}
FONT = None
FACING = Matrix((RIGHT, UP, NORMAL)).transposed().to_quaternion()
FRONT_FACE = Matrix(((1,0,0),(0,0,1),(0,-1,0))).transposed().to_quaternion()
TIMES = []

def register(obj, name, mat=None):
    obj.name = name
    obj['layer'] = GROUP
    GROUPS.setdefault(GROUP, []).append(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

def layer(name, footprint=None, height=0):
    global GROUP
    GROUP = name
    if footprint:
        META[name] = {'name':name,'footprint':footprint,'height_px':height,
                      'depth':sum(footprint)/2,
                      'z_index':1000+round(sum(footprint)*50)}

def material(name, color, rough=.5, metal=0, emit=0, texture=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    n = mat.node_tree.nodes
    p = n.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color,1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*color,1)
        p.inputs['Emission Strength'].default_value = emit
    if texture:
        noise = n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = texture
        noise.inputs['Detail'].default_value = 3
        tex = n.new('ShaderNodeTexCoord')
        mat.node_tree.links.new(tex.outputs['Object'],noise.inputs['Vector'])
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .15
        ramp.color_ramp.elements[0].color = (*(c*.6 for c in color),1)
        ramp.color_ramp.elements[1].position = .85
        ramp.color_ramp.elements[1].color = (*(min(1,c*1.25) for c in color),1)
        mat.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
        mat.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
        bump = n.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .22
        bump.inputs['Distance'].default_value = .015 if texture>10 else .035
        mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    M[name] = mat
    return mat

def glass(name, color, opacity=.16):
    mat = material(name,color,.12,.25)
    n = mat.node_tree.nodes
    p = n.get('Principled BSDF')
    trans = n.new('ShaderNodeBsdfTransparent')
    mix = n.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = opacity
    mat.node_tree.links.new(trans.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(p.outputs[0],mix.inputs[2])
    mat.node_tree.links.new(mix.outputs[0], n.get('Material Output').inputs['Surface'])
    return mat

def cube(name, loc, size, mat, bevel=.025, rotation=None):
    verts=[(x*size[0]/2,y*size[1]/2,z*size[2]/2) for x,y,z in
           [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    obj=mesh(name,verts,faces,mat)
    obj.location=loc
    if rotation:
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion = rotation
    if bevel:
        mod = obj.modifiers.new('Soft manufactured edges','BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod = obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return obj

def box(name,u0,v0,u1,v1,z0,z1,mat,bevel=.025):
    return cube(name,xyz((u0+u1)/2,(v0+v1)/2,(z0+z1)/2),
                (u1-u0,v1-v0,(z1-z0)/ZPP),mat,bevel)

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    return register(obj,name,mat)

def line(name, pts, mat, radius=.014, cyclic=False):
    data = bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'
    data.resolution_u=1
    data.bevel_depth=radius
    data.resolution_u=2
    data.bevel_resolution=2
    spline=data.splines.new('POLY')
    spline.points.add(len(pts)-1)
    for p,co in zip(spline.points,pts):
        p.co=(*co,1)
    spline.use_cyclic_u=cyclic
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    return register(obj,name,mat)

def cylinder(name,loc,radius,depth,mat,axis=None,vertices=20):
    verts=[(radius*math.cos(i*math.tau/vertices),radius*math.sin(i*math.tau/vertices),z) for z in [-depth/2,depth/2] for i in range(vertices)]
    faces=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]
    faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    obj=mesh(name,verts,faces,mat);obj.location=loc
    if axis is not None:
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis))
    mod=obj.modifiers.new('Edge bevel','BEVEL'); mod.width=.008; mod.segments=2
    for poly in obj.data.polygons: poly.use_smooth=True
    return obj

def ball(name,loc,radius,mat,scale=None):
    verts=[(radius*math.sin(j*math.pi/8)*math.cos(i*math.tau/16),radius*math.sin(j*math.pi/8)*math.sin(i*math.tau/16),radius*math.cos(j*math.pi/8)) for j in range(9) for i in range(16)]
    faces=[(j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i) for j in range(8) for i in range(16)]
    obj=mesh(name,verts,faces,mat);obj.location=loc
    if scale: obj.scale=scale
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def text(name,body,loc,size,mat,rotation=FACING,extrude=.001):
    data=bpy.data.curves.new(name,'FONT')
    data.body=body; data.align_x='CENTER'; data.align_y='CENTER'
    data.size=size; data.extrude=extrude; data.bevel_depth=.0008
    if FONT:data.font=FONT
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=loc; obj.rotation_mode='QUATERNION'; obj.rotation_quaternion=rotation
    return register(obj,name,mat)

def panel(name,center,width,height,mat,depth=.06,bevel=.018):
    return cube(name,center,(width/PPU,height/PPU,depth),mat,bevel,FACING)

def screen_frame(name,center,w,h,trim,base=None,thick=2):
    if base:panel(name+' backing',center-NORMAL*.035,w+thick*2,h+thick*2,base)
    for off in [-1,1]:
        panel(name+' horizontal',center+UP*(off*(h+thick)/2/PPU),w+thick*2,thick,trim,.035,.006)
        panel(name+' vertical',center+RIGHT*(off*(w+thick)/2/PPU),thick,h,trim,.035,.006)

def area(name,loc,power,color,size,target=None,size_y=None):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color
    data.shape='RECTANGLE' if size_y else 'DISK'; data.size=size
    if size_y:data.size_y=size_y
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    obj.location=loc
    if target is not None:obj.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    else:obj.rotation_euler=(0,0,0)
    return obj

def point(name,loc,power,color,radius=.2):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.location=loc
    return obj

def palette():
    material('wall plum',(.13,.062,.21),.75,texture=9)
    material('dark plum',(.025,.013,.043),.5,texture=18)
    material('display recess',(.006,.003,.014),.5)
    material('carpet aubergine',(.075,.034,.13),.96,texture=140)
    material('carpet midnight',(.022,.051,.086),.98,texture=140)
    material('carpet inset',(.034,.10,.12),.96,texture=130)
    material('velvet burgundy',(.24,.025,.065),.8,texture=95)
    material('velvet teal',(.014,.16,.17),.66,texture=80)
    material('black enamel',(.012,.018,.028),.27,.45)
    material('brushed nickel',(.32,.39,.45),.28,.8,texture=95)
    material('warm brass',(.42,.25,.085),.26,.75)
    material('counter stone',(.32,.30,.40),.24,.05,texture=16)
    material('red enamel',(.40,.018,.045),.24,.3)
    material('pink neon',(1,.085,.37),.2,emit=5)
    material('cyan neon',(.13,1,.85),.2,emit=4)
    material('warm light',(1,.58,.20),.3,emit=4)
    material('white light',(.72,.91,1),.3,emit=2)
    material('soft menu',(.72,.64,.43),.5,emit=1.2)
    material('ink',(.018,.014,.025),.8)
    material('door glow',(1,.37,.075),.3,emit=3)
    material('concrete',(.21,.23,.28),.22,texture=22)
    material('asphalt',(.025,.032,.045),.18,.15,texture=65)
    material('puddle',(.022,.031,.058),.055,.3,texture=3)
    material('lane paint',(.44,.37,.16),.36,texture=45)
    material('popcorn',(.9,.65,.24),.7)
    material('paper',(.72,.67,.51),.84)
    glass('glass',(.21,.57,.63),.13)
    glass('smoked glass',(.08,.18,.29),.20)
    for name,c in [('confetti pink',(.65,.12,.32)),('confetti cyan',(.12,.52,.46)),('confetti gold',(.65,.42,.10)),('confetti lilac',(.34,.17,.58))]:
        material(name,c,.95)

def backdrop():
    layer('background')
    sky=material('purple overcast sky',(.025,.021,.065),1,emit=.55,texture=.18)
    panel('Clouded night sky',screen_point(960,540,-34),2800,1800,sky,.1,0)
    city=[material('distant city '+str(i),c,.8,emit=.12) for i,c in enumerate([(.025,.029,.07),(.035,.038,.08),(.048,.04,.085)])]
    win=[material('window amber',(.35,.23,.10),.6,emit=.6),material('window blue',(.10,.26,.33),.6,emit=.5)]
    for tier,dep in [(0,-30),(1,-25),(2,-20)]:
        x=-100
        while x<2000:
            w=RNG.randint(65,155); top=RNG.randint(180,360)+tier*30
            h=1100-top
            panel('City masonry',screen_point(x+w/2,top+h/2,dep),w,h,city[tier],.45,.015)
            panel('Roof parapet',screen_point(x+w/2,top,dep+.27),w+5,4,city[tier],.09,.008)
            # Window faces are slightly recessed inside thick lintels.
            for wx in range(int(x+9),int(x+w-8),17):
                for wy in range(top+15,1050,24):
                    if RNG.random()<.23:
                        panel('Distant lit window',screen_point(wx,wy,dep+.24),5,9,RNG.choice(win),.01,0)
            if RNG.random()<.35:
                line('Roof antenna',[screen_point(x+w*.6,top,dep),screen_point(x+w*.6,top-34,dep)],M['black enamel'],.012)
                ball('Aviation beacon',screen_point(x+w*.6,top-34,dep),.017,M['red enamel'])
            x+=w+RNG.randint(5,24)
    tower=material('tower concrete',(.045,.038,.067),.6,.1,texture=20)
    panel('Billboard tower',screen_point(1595,550,-12),670,1300,tower,.9,.035)
    for x in range(1262,1930,36):
        panel('Tower vertical ribs',screen_point(x,550,-11.5),3,1250,M['black enamel'],.12,.003)
    for y in range(412,1100,36):
        for x in range(1274,1920,36):
            if RNG.random()<.22:panel('Tower windows',screen_point(x,y,-11.42),10,14,RNG.choice(win),.025,.006)
    center=screen_point(1584,202,-10.8)
    panel('Billboard black aperture',center,576,324,M['ink'],.2,.0)
    screen_frame('Billboard heavy bezel',center,580,328,M['brushed nickel'],M['black enamel'],10)
    screen_frame('Billboard cyan inner rail',center+NORMAL*.15,584,332,M['cyan neon'],thick=2)
    screen_frame('Billboard pink outer rail',center+NORMAL*.15,600,348,M['pink neon'],thick=2)
    for x in [1282,1886]:
        for y in [28,376]:ball('Billboard fixing',screen_point(x,y,-10.6),.033,M['brushed nickel'])

def carpet_pattern(u0,v0,u1,v1,density=26):
    verts=[];faces=[];indices=[]
    mats=[M['confetti pink'],M['confetti cyan'],M['confetti gold'],M['confetti lilac']]
    for i in range(int((u1-u0)*(v1-v0)*density)):
        u=RNG.uniform(u0+.04,u1-.04);v=RNG.uniform(v0+.04,v1-.04)
        theta=RNG.random()*math.tau
        c,s=math.cos(theta),math.sin(theta)
        if i%5==0: shape=[(-.03,-.022),(.04,0),(-.03,.022)]
        elif i%5==1: shape=[(-.035,-.007),(.035,-.007),(.035,.007),(-.035,.007)]
        else: shape=[(-.009,-.021),(.009,-.021),(.009,.021),(-.009,.021)]
        start=len(verts)
        for x,y in shape:verts.append(xyz(u+c*x-s*y,v+s*x+c*y,.06))
        faces.append(tuple(range(start,len(verts)))); indices.append(i%4)
    obj=mesh('Woven Memphis carpet flecks',verts,faces,mats[0])
    for m in mats[1:]:obj.data.materials.append(m)
    for p,idx in zip(obj.data.polygons,indices):p.material_index=idx

def ground():
    layer('background')
    box('Cinema structural slab',0,0,13,9,-10,-.08,M['black enamel'])
    box('Main lobby carpet',3,3,13,9,-.2,0,M['carpet aubergine'],.006)
    box('Left corridor carpet',0,0,3,9,-.2,0,M['carpet midnight'],.006)
    box('Right corridor carpet',3,0,13,3,-.2,0,M['carpet midnight'],.006)
    # Woven runner borders, with the original 1.4-tile route left clear.
    box('Left corridor runner',.76,.76,2.04,9,0,.035,M['carpet inset'],.002)
    box('Right corridor runner',2.04,.76,13,2.04,0,.035,M['carpet inset'],.002)
    for a in [.74,2.06]:
        line('Runner brass thread',[xyz(a,.75,.08),xyz(a,8.9,.08)],M['confetti gold'],.008)
        line('Runner brass thread',[xyz(2.05,a,.08),xyz(12.9,a,.08)],M['confetti gold'],.008)
    carpet_pattern(3.12,3.12,12.9,8.9,34)
    carpet_pattern(.8,.8,2,8.9,9)
    carpet_pattern(2.1,.8,12.9,2,9)
    for u0,v0,u1,v1 in [(3.2,3.2,12.8,3.23),(3.2,8.78,12.8,8.81),(3.2,3.2,3.23,8.8),(12.77,3.2,12.8,8.8)]:
        box('Lobby carpet piping',u0,v0,u1,v1,.02,.06,M['confetti lilac'],.002)
    box('Wet street',-12,10.6,23,13.5,-.20,-.05,M['asphalt'],0)
    for u in range(-12,23):
        for v in [9.15,9.825]:
            box('Wet paving slab',u+.012,v+.012,u+.988,v+.663,-.09,0,M['concrete'],.018)
    box('Threshold bridge',0,9,13,9.15,-.08,0,M['concrete'],.008)
    for u in range(-12,23):box('Curb stone',u+.015,10.5,u+.985,10.62,-6,1.7,M['concrete'],.015)
    for i in range(26):
        u=-10+i*1.4
        box('Worn lane dash',u,11.95,u+.7,12.05,0,.08,M['lane paint'],.003)
    for i in range(32):
        u=RNG.uniform(-7,20);v=RNG.uniform(10.8,13.3)
        length=RNG.uniform(.2,.65);width=RNG.uniform(.08,.25)
        verts=[xyz(u,v,.07)]
        for j in range(16):
            t=j*math.tau/16; rr=RNG.uniform(.85,1.12)
            verts.append(xyz(u+math.cos(t)*length*rr,v+math.sin(t)*width*rr,.07))
        mesh('Rainwater pool',verts,[(0,j+1,(j+1)%16+1) for j in range(16)],M['puddle'])
    for u in [2.8,8.0,14.0]:
        box('Storm drain',u,10.48,u+.6,10.6,1.75,1.8,M['black enamel'],.003)
        for j in range(11):box('Drain grille',u+j*.05,10.48,u+j*.05+.015,10.6,1.8,1.95,M['brushed nickel'],.002)

def wallbox(name,wall,a,b,z0,z1,mat,front=0,depth=.10,bevel=.012):
    if wall=='u':return box(name,front-depth,a,front,b,z0,z1,mat,bevel)
    return box(name,a,front-depth,b,front,z0,z1,mat,bevel)

def wp(wall,t,z,front=0):
    return xyz(front,t,z) if wall=='u' else xyz(t,front,z)

def wall_line(name,wall,pts,mat,radius=.01,front=.025):
    return line(name,[wp(wall,t,z,front) for t,z in pts],mat,radius)

def door(wall,at,number):
    wallbox('Door brushed frame',wall,at-.55,at+.55,0,114,M['brushed nickel'],.007,.11)
    wallbox('Door dark reveal',wall,at-.49,at+.49,.5,109,M['ink'],.015,.025)
    for side in [-1,1]:
        a,b=(at-.465,at-.014) if side<0 else (at+.014,at+.465)
        wallbox('Upholstered cinema door',wall,a,b,1.5,108,M['velvet burgundy'],.028,.04,.025)
        # Diamond stitching on the lower padded insert.
        for k in range(7):
            z=6+k*9
            wall_line('Door diamond stitching',wall,[(a+.04,z),(a+(b-a)/2,z+7),(b-.04,z),(a+(b-a)/2,z-7),(a+.04,z)],M['red enamel'],.003,.036)
        axis=(1,0,0) if wall=='u' else (0,-1,0)
        c=wp(wall,at+side*.24,79,.05)
        cylinder('Porthole chrome surround',c,.124,.045,M['brushed nickel'],axis)
        cylinder('Porthole amber glass',c+Vector(axis)*.028,.094,.012,M['door glow'],axis)
        wall_line('Polished door pull',wall,[(at+side*.07,43),(at+side*.07,59)],M['brushed nickel'],.019,.08)
        wallbox('Door brass kickplate',wall,a+.03,b-.03,3,15,M['warm brass'],.041,.013)
    wall_line('Light under auditorium door',wall,[(at-.45,.8),(at+.45,.8)],M['warm light'],.012,.022)
    point('Warm light leaking under screen '+str(number),wp(wall,at,4,.15),7,(1,.42,.12),.20)
    anchor=wp(wall,at,124)
    center=anchor+UP*(46/PPU)+NORMAL*1.9
    panel('Blank marquee interior '+str(number),center,176,92,M['display recess'],.10,.045)
    screen_frame('Marquee silver rim '+str(number),center+NORMAL*.06,176,92,M['brushed nickel'],thick=3)
    screen_frame('Marquee pink tube '+str(number),center+NORMAL*.09,180,96,M['pink neon'],thick=1.5)
    # Small supports sit behind the camera-facing boxes.
    line('Marquee bracket',[anchor-UP*.04,anchor+UP*.4-NORMAL*.15],M['black enamel'],.035)
    a,b=(at-1.55,at-.75) if wall=='u' else (at+.75,at+1.55)
    # The inner quad is exactly on the DOM poster projection plane.
    wallbox('Poster outer metal frame',wall,a-.045,b+.045,20,131,M['brushed nickel'],.001,.045)
    wallbox('Blank poster aperture',wall,a,b,23,128,M['dark plum'],.002,.001,0)
    for edge in [a-.027,b+.027]:wall_line('Poster perimeter glow',wall,[(edge,22),(edge,129)],M['white light'],.005,.012)
    wall_line('Poster top light',wall,[(a,130),(b,130)],M['warm light'],.009,.025)

def walls():
    layer('background')
    for wall,length,doors in [('u',9,[(4,1.1,114),(6.4,1.1,114),(8.3,.8,104)]),('v',13,[(4.8,1.1,114),(8.2,1.1,114),(11.2,1.1,114)])]:
        cursor=0
        solid=[]
        for at,width,height in doors:
            a,b=at-width/2,at+width/2
            solid.append((cursor,a))
            wallbox('Plastered cinema wall',wall,cursor,a,0,170,M['wall plum'],0,.22)
            wallbox('Lintel above doorway',wall,a,b,height,170,M['wall plum'],0,.22)
            cursor=b
        solid.append((cursor,length))
        wallbox('Plastered cinema wall',wall,cursor,length,0,170,M['wall plum'],0,.22)
        for a,b in solid:
            wallbox('Walnut wainscot',wall,a,b,0,44,M['dark plum'],.019,.04)
            wallbox('Wainscot brass cap',wall,a,b,42,45,M['warm brass'],.035,.05)
            wall_line('Cyan low wall tube',wall,[(a,47),(b,47)],M['cyan neon'],.009,.045)
            wall_line('Dark skirting',wall,[(a,4),(b,4)],M['black enamel'],.026,.026)
            for i in range(max(1,int((b-a)/.52))):
                t=a+(i+.5)*(b-a)/max(1,int((b-a)/.52))
                wall_line('Wainscot flute',wall,[(t,7),(t,38)],M['warm brass'],.005,.029)
        wallbox('Crown cornice',wall,0,length,160,170,M['dark plum'],.07,.34)
        wall_line('Crown brass ribbon',wall,[(0,162),(length,162)],M['warm brass'],.014,.085)
        wall_line('Pink perimeter neon',wall,[(0,150),(length,150)],M['pink neon'],.014,.06)
        # Deco grooves and sconces occupy unused wall intervals only.
        sconces=[1.4,2.4,7.45] if wall=='u' else [2.0,6.8,9.9,12.7]
        for t in sconces:
            wallbox('Sconce mounting',wall,t-.09,t+.09,75,98,M['warm brass'],.09,.12)
            wallbox('Opal sconce',wall,t-.055,t+.055,78,96,M['warm light'],.14,.08)
            point('Wall sconce pool',wp(wall,t,92,.25),15,(1,.57,.27),.22)
    for i,(wall,at) in enumerate([('u',6.4),('u',4.0),('v',4.8),('v',8.2),('v',11.2)],1):door(wall,at,i)
    wallbox('Restroom chrome frame','u',7.9,8.7,0,104,M['brushed nickel'],.02,.12)
    wallbox('Restroom teal door','u',7.95,8.65,.5,100,M['velvet teal'],.031,.03,.02)
    wallbox('Restroom inset panel','u',8.01,8.59,17,86,M['dark plum'],.041,.015,.03)
    ball('Restroom brass knob',wp('u',8.08,48,.09),.031,M['warm brass'])
    anchor=wp('u',8.3,132)+NORMAL*.45
    panel('Restroom sign',anchor+UP*.10,124,21,M['black enamel'],.05)
    text('Restroom text','RESTROOM',anchor+UP*.10+NORMAL*.05,.16,M['cyan neon'])

def low_wall(name,fp):
    layer(name,fp,34)
    a,b,c,d=fp
    box(name+' body',a,b,c,d,0,31,M['dark plum'],.015)
    box(name+' stone cap',a,b,c,d,31,34,M['counter stone'],.012)
    if c-a>d-b:
        line('Pink partition tube',[xyz(a,b+.018,32),xyz(c,b+.018,32)],M['pink neon'],.012)
        for u in range(math.ceil(a),math.floor(c)):
            box('Partition fluting',u-.012,d-.014,u+.012,d,5,27,M['warm brass'],.003)
    else:
        line('Pink partition tube',[xyz(a+.018,b,32),xyz(a+.018,d,32)],M['pink neon'],.012)
        for v in range(math.ceil(b),math.floor(d)):
            box('Partition fluting',c-.014,v-.012,c,v+.012,5,27,M['warm brass'],.003)

def storefront():
    low_wall('partition_left',[2.9,4.4,3.1,9])
    low_wall('partition_right',[4.4,2.9,13,3.1])
    low_wall('front_low_wall',[0,8.9,3,9.05])
    for name,a,b in [('glass_left',3,8.4),('glass_right',10.6,13)]:
        layer(name,[a,8.95,b,9.05],30)
        box('Glass bottom shoe',a,8.95,b,9.05,0,3,M['black enamel'],.005)
        box('Laminated low storefront',a,8.995,b,9.005,3,29,M['glass'],.002)
        box('Polished glass cap',a,8.95,b,9.05,28.5,30,M['brushed nickel'],.006)
        n=math.ceil((b-a)/1.05)
        for j in range(n+1):
            u=a+(b-a)*j/n
            box('Slim glass mullion',max(a,u-.012),8.98,min(b,u+.012),9.02,3,29,M['brushed nickel'],.004)
        for j in range(n):
            u=a+(b-a)*(j+.5)/n
            ball('Glass safety dot',xyz(u,9.011,15),.017,M['white light'],(1,.1,1))
    for i,u in enumerate([8.4,10.6],1):
        layer('entrance_post_'+str(i),[u-.07,8.93,u+.07,9.07],60)
        box('Entrance steel post',u-.07,8.93,u+.07,9.07,0,60,M['brushed nickel'],.02)
        box('Entrance post light',u-.034,9.052,u+.034,9.068,8,54,M['cyan neon'],.005)

def box_office():
    layer('boxoffice',[4,7,7,7.8],84)
    box('Ticket desk plinth',4,7,7,7.8,0,5,M['black enamel'])
    box('Ticket counter body',4.03,7.03,6.97,7.77,5,38,M['velvet teal'])
    for u in [4.1+i*.12 for i in range(24)]:
        box('Ticket counter vertical rib',u,7.76,u+.025,7.78,6,35,M['warm brass'],.004)
    box('Ticket counter stone',4,7,7,7.8,38,42,M['counter stone'],.025)
    line('Ticket counter cyan trim',[xyz(4,7.79,32),xyz(7,7.79,32),xyz(7,7,32)],M['cyan neon'],.012)
    # Two true openings below the glass, rather than painted slots.
    for a,b in [(4.05,4.59),(5.01,5.99),(6.41,6.95)]:
        box('Cashier safety glass lower',a,7.06,b,7.075,42,57,M['glass'],.003)
    box('Cashier safety glass upper',4.05,7.06,6.95,7.075,57,84,M['glass'],.003)
    for u in [4.05,5.5,6.95]:box('Cashier chrome upright',u,7.02,u+.025,7.12,42,84,M['brushed nickel'],.006)
    box('Cashier header rail',4.05,7.02,6.95,7.12,82,84,M['brushed nickel'],.005)
    for u in [4.8,6.2]:
        box('Ticket pass tray',u-.19,7.12,u+.19,7.44,42,43,M['brushed nickel'],.01)
        for i in range(4):box('Ticket stub',u-.1+i*.025,7.45,u+.05+i*.025,7.55,42.1+i*.5,42.5+i*.5,M['paper'],.001)
    box('Receipt terminal',6.55,7.3,6.82,7.55,42,54,M['black enamel'])
    box('Receipt terminal green display',6.57,7.548,6.80,7.556,48,52,M['cyan neon'],.002)
    layer('background')
    anchor=xyz(5.5,7.4,112)
    panel('Tickets dark mounting',anchor+UP*.13,168,34,M['black enamel'],.1,.035)
    text('Tickets neon','T I C K E T S',anchor+UP*.13+NORMAL*.07,.28,M['cyan neon'])

def concessions():
    layer('snack',[8.2,4.6,11.8,6],108)
    box('Snack base',8.2,4.6,11.8,6,0,6,M['black enamel'])
    box('Snack counter cabinet',8.23,4.63,11.77,5.97,6,38,M['dark plum'])
    box('Snack granite top',8.2,4.6,11.8,6,38,42,M['counter stone'],.028)
    for i in range(18):
        u=8.27+i*.195
        box('Snack cabinet flutes',u,5.97,u+.08,5.99,7,28,M['velvet burgundy'],.012)
    line('Snack pink edging',[xyz(8.2,6,32),xyz(11.8,6,32),xyz(11.8,4.6,32)],M['pink neon'],.012)
    # Popper: steel pan, glass shell, kettle, corn, cap and warming light.
    box('Popper metal base',9.6,4.9,10.4,5.5,42,51,M['red enamel'],.022)
    box('Popper glass front',9.62,5.478,10.38,5.49,51,100,M['glass'],.002)
    box('Popper glass side',10.38,4.92,10.39,5.48,51,100,M['glass'],.002)
    box('Popper glass back',9.62,4.91,10.38,4.922,51,100,M['glass'],.002)
    for u in [9.62,10.38]:
        for v in [4.92,5.48]:box('Popper corner post',u-.014,v-.014,u+.014,v+.014,49,101,M['warm brass'],.004)
    box('Popper red canopy',9.6,4.9,10.4,5.5,100,108,M['red enamel'],.018)
    box('Popper warming light',9.67,4.97,10.33,5.43,98,99,M['warm light'],.005)
    cylinder('Steel popping kettle',xyz(10,5.2,83),.19,.14,M['brushed nickel'])
    line('Kettle suspension',[xyz(10,5.2,90),xyz(10,5.2,99)],M['black enamel'],.018)
    for i in range(150):
        u=RNG.uniform(9.66,10.34);v=RNG.uniform(4.96,5.44)
        z=RNG.uniform(52,64)-abs(u-10)*12
        ball('Popped corn',xyz(u,v,z),RNG.uniform(.023,.039),M['popcorn'],(1,.8,1.1))
    point('Popcorn golden pool',xyz(10,5.2,75),12,(1,.51,.13),.22)
    text('Popcorn canopy label','POPCORN',xyz(10,5.51,103)+NORMAL*.16,.11,M['soft menu'])
    # Soda fountain, four branded-color buttons, spouts and drip tray.
    box('Soda dispenser',8.5,4.9,9.1,5.4,42,72,M['brushed nickel'],.025)
    box('Soda dispenser face',8.53,5.39,9.07,5.41,51,67,M['black enamel'],.01)
    for i,m in enumerate(['red enamel','cyan neon','confetti lilac','warm light']):
        u=8.60+i*.135
        box('Soda illuminated selection',u-.045,5.415,u+.045,5.425,59,65,M[m],.006)
        line('Soda nozzle',[xyz(u,5.43,57),xyz(u,5.46,53)],M['black enamel'],.018)
    box('Soda drip tray',8.5,5.4,9.1,5.55,42,44,M['black enamel'],.008)
    for i in range(8):box('Drip tray bars',8.54+i*.067,5.41,8.56+i*.067,5.54,44,44.3,M['brushed nickel'],.002)
    # Candy display contains individual wrapped rectangles on two shelves.
    box('Candy case base',10.9,4.9,11.5,5.4,42,44,M['warm brass'],.01)
    for u in [10.91,11.49]:
        box('Candy case mullion',u-.008,4.91,u+.008,5.39,44,60,M['brushed nickel'],.003)
    box('Candy glass lid',10.9,4.9,11.5,5.4,59.8,60,M['glass'],.002)
    box('Candy glass front',10.91,5.39,11.49,5.4,44,60,M['glass'],.002)
    for z in [45,52]:
        for i in range(4):
            for j in range(2):box('Candy wrapper',10.96+i*.13,4.97+j*.19,11.06+i*.13,5.10+j*.19,z,z+3,M[['confetti pink','confetti cyan','confetti gold','confetti lilac'][i]],.006)
    for i in range(5):
        cylinder('Paper drinks cup',xyz(9.30,5.03,46+i*1.8),.062,.09,M['paper'])
    layer('background')
    center=xyz(10,5.3,150)+UP*(42/PPU)
    panel('Snack menu black housing',center,166,84,M['black enamel'],.12,.035)
    panel('Snack backlit menu',center+NORMAL*.07,156,74,M['soft menu'],.01,.008)
    text('Snack menu heading','SNACK BAR',center+UP*.28+NORMAL*.09,.28,M['red enamel'])
    for i,row in enumerate(['Popcorn     $4.50','Soda        $2.75','Nachos      $3.25']):
        text('Snack menu prices',row,center+UP*(.07-i*.19)+NORMAL*.09,.185,M['ink'])

def furniture():
    layer('podium',[4.6,3.5,5.1,4],49)
    box('Usher podium',4.62,3.52,5.08,3.98,2,37,M['dark plum'])
    box('Podium brass base',4.6,3.5,5.1,4,0,3,M['warm brass'],.01)
    box('Podium teal top',4.6,3.5,5.1,4,37,40,M['velvet teal'],.01)
    cylinder('Podium lamp stem',xyz(4.9,3.64,44),.012,8/ZPP,M['warm brass'])
    ball('Podium green lamp shade',xyz(4.9,3.64,48),.082,M['cyan neon'],(1,.7,.45))
    box('Usher ticket ledger',4.67,3.74,4.86,3.91,40,40.7,M['paper'],.004)
    point('Usher lamp glow',xyz(4.9,3.7,46),3,(.16,1,.8),.10)
    layer('bench',[6.4,3.25,7.9,3.75],28)
    for u in [6.52,7.78]:
        for v in [3.34,3.65]:cylinder('Bench leg',xyz(u,v,6),.03,12/ZPP,M['warm brass'])
    box('Bench seat',6.4,3.25,7.9,3.75,10,18,M['velvet teal'],.055)
    box('Bench padded back',6.4,3.25,7.9,3.34,18,28,M['velvet teal'],.035)
    for u in [6.7,7.15,7.6]:
        line('Bench upholstery seam',[xyz(u,3.27,18.1),xyz(u,3.72,18.1)],M['carpet inset'],.004)
        ball('Bench button',xyz(u,3.34,23),.012,M['warm brass'])
    # A sculpted side profile distinguishes the cabinet from a block.
    layer('arcade',[12,7.5,12.7,8.2],82)
    profile=[(7.5,0),(8.2,0),(8.2,40),(8.02,44),(7.94,65),(8.13,73),(8.13,82),(7.5,82)]
    verts=[xyz(u,v,z) for u in [12,12.7] for v,z in profile]
    n=len(profile);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=mesh('Arcade shaped cabinet',verts,faces,M['black enamel'])
    mod=obj.modifiers.new('Arcade edge rounding','BEVEL');mod.width=.015;mod.segments=2
    box('Arcade CRT bezel',12.685,7.62,12.704,8.05,43,70,M['brushed nickel'],.01)
    box('Arcade CRT dark glass',12.705,7.65,12.712,8.02,46,67,M['ink'],.01)
    # Procedural tiny pixel game in the actual visible side plane.
    for j in range(12):
        for i in range(15):
            if ((i-7)**2+(j-5)**2<12 and (i+j)%3) or (j==2 and i%4==0):
                box('CRT game pixels',12.714,7.68+i*.021,12.717,7.697+i*.021,48+j*1.4,49+j*1.4,M['cyan neon' if j>3 else 'pink neon'],.001)
    box('Arcade control shelf',12.1,7.94,12.65,8.2,39,43,M['velvet burgundy'],.013)
    for u in [12.2,12.47]:
        cylinder('Arcade joystick',xyz(u,8.09,46),.012,5/ZPP,M['brushed nickel'])
        ball('Arcade joystick ball',xyz(u,8.09,49),.035,M['red enamel'])
    for u in [12.3,12.36,12.56]:cylinder('Arcade button',xyz(u,8.14,44),.024,.015,M['cyan neon'])
    for v in [7.52,8.16]:line('Arcade cabinet pink edge',[xyz(12.71,v,3),xyz(12.71,v,80)],M['pink neon'],.009)
    text('Arcade header','ORBIT',xyz(12.4,8.1,77)+NORMAL*.2,.12,M['white light'])
    point('Arcade screen spill',xyz(12.9,7.9,55),6,(.12,.5,1),.18)
    standee('standee_1',12.2,5.0,False)
    standee('standee_2',6,6.3,True)
    layer('background')
    center=xyz(3.2,3.2,178)+UP*(14/PPU)
    panel('Usher gate hanging sign',center,160,28,M['black enamel'],.09)
    screen_frame('Gate cyan rim',center+NORMAL*.06,158,26,M['cyan neon'],thick=1.3)
    text('Gate lettering','1-2   \u00b7   3-5',center+NORMAL*.07,.235,M['white light'])
    # Geometric arrow triangles avoid relying on non-ASCII glyph availability.
    for sign in [-1,1]:
        p=center+RIGHT*(sign*.79)+NORMAL*.075
        mesh('Gate directional arrow',[p+RIGHT*(sign*.075),p-RIGHT*(sign*.04)+UP*.07,p-RIGHT*(sign*.04)-UP*.07],[(0,1,2)],M['white light'])

def standee(name,u,v,teal):
    # Preserve the existing rendered standee base extension; record it separately.
    fp=[u,v,u+.42,v+.06]
    layer(name,fp,92)
    META[name]['geometry_footprint']=[u-.05,v-.08,u+.47,v+.14]
    box('Cardboard standee foot',u-.05,v-.08,u+.47,v+.14,0,6,M['black enamel'],.012)
    box('Printed standee board',u,v,u+.42,v+.06,6,92,M['confetti cyan' if teal else 'confetti pink'],.008)
    # Original silhouette artwork, not a film poster or downloaded texture.
    face=v+.061
    mesh('Movie silhouette',[xyz(u+.07,face,15),xyz(u+.35,face,15),xyz(u+.31,face,64),xyz(u+.24,face,71),xyz(u+.14,face,64)],[(0,1,2,3,4)],M['ink'])
    cylinder('Standee silhouette head',xyz(u+.21,face+.006,76),.065,.003,M['ink'],(0,-1,0))
    line('Standee colored horizon',[xyz(u+.03,face,40),xyz(u+.39,face,44)],M['warm light'],.008)
    text('Standee original title','MIDNIGHT' if teal else 'VOYAGER',xyz(u+.21,face+.004,12),.075,M['soft menu'],rotation=FRONT_FACE)

def exterior_props():
    layer('bus_stop',[.4,9.3,2,9.55],96)
    META['bus_stop']['geometry_footprint']=[.35,9.25,2.05,9.6]
    for u in [.45,1.95]:
        cylinder('Bus shelter post',xyz(u,9.5,40),.022,80/ZPP,M['brushed nickel'])
        cylinder('Bus shelter foot',xyz(u,9.5,1),.06,2/ZPP,M['black enamel'])
    box('Bus shelter glass',.45,9.42,1.95,9.43,4,80,M['smoked glass'],.004)
    box('Bus shelter steel roof',.35,9.25,2.05,9.6,80,86,M['brushed nickel'],.025)
    box('Bus shelter underside light',.5,9.31,1.9,9.54,79,80,M['white light'],.006)
    center=xyz(1.2,9.6,91)
    panel('Bus route enamel',center,72,15,M['black enamel'],.04,.015)
    text('Bus route text','BUS 95',center+NORMAL*.03,.145,M['warm light'])
    point('Bus stop cool light',xyz(1.2,9.5,72),12,(.4,.65,1),.3)
    layer('street_lamp',[5,10.3,5.15,10.45],190)
    cylinder('Lamp base',xyz(5.07,10.37,6),.07,12/ZPP,M['black enamel'])
    cylinder('Street lamp fluted pole',xyz(5.07,10.37,92),.034,176/ZPP,M['brushed nickel'])
    cylinder('Lamp brass collar',xyz(5.07,10.37,175),.065,.04,M['warm brass'])
    ball('Lamp frosted globe',xyz(5.07,10.37,182),.075,M['warm light'],(1,1,1.3))
    point('Warm street lamp pool',xyz(5.07,10.37,180),65,(1,.64,.29),.20)
    layer('roxy_blade',[-.75,9.1,-.05,9.3],300)
    box('Roxy projecting sign',-.75,9.1,-.05,9.3,110,300,M['black enamel'],.03)
    for u in [-.72,-.08]:line('Roxy pink tube',[xyz(u,9.315,113),xyz(u,9.315,297)],M['pink neon'],.015)
    for z in [113,297]:line('Roxy end tube',[xyz(-.72,9.315,z),xyz(-.08,9.315,z)],M['pink neon'],.015)
    for i,ch in enumerate('ROXY'):
        text('Roxy neon letter '+ch,ch,xyz(-.4,9.33,276-i*44)+NORMAL*.28,.43,M['pink neon'],extrude=.004)
    point('Roxy neon spill',xyz(-.25,9.7,160),30,(1,.06,.31),.65)

def lighting():
    area('Large soft cinema key',xyz(7,5,350),350,(.72,.66,1),8,target=xyz(7,5,0))
    area('Warm lobby pool',xyz(7,7,240),180,(1,.61,.31),4.5,target=xyz(7,6,0))
    area('Concession warm ceiling bounce',xyz(10,4.9,250),130,(1,.74,.47),3,target=xyz(10,5.5,0))
    area('Corridor left blue fill',xyz(1.4,4,270),100,(.35,.57,1),4,target=xyz(1.4,4,0))
    area('Corridor right fill',xyz(8,1.3,265),125,(.45,.58,1),6,target=xyz(8,1.3,0))
    area('Cool street sky reflection',xyz(6,12,430),450,(.28,.42,1),9,target=xyz(6,11.5,0),size_y=3)
    for u in [4,8,12]:
        area('Neon storefront reflected glow',xyz(u,8.7,90),35,(1,.07,.3),2,target=xyz(u,11.6,0),size_y=.35)

def build(samples,scale):
    global FONT
    sc=setup(samples,scale)
    fontpath=Path('C:/Windows/Fonts/arialbd.ttf')
    if fontpath.exists():FONT=bpy.data.fonts.load(str(fontpath))
    for step in [palette,backdrop,ground,walls,storefront,box_office,concessions,furniture,exterior_props,lighting]:
        step()
        print('BUILD_STAGE',step.__name__,len(bpy.data.objects),flush=True)
    sc['projection']='P(u,v,z) = (900+60*(u-v),350+30*(u+v)-z); Blender=(u,-v,z/73.4846922835)'
    return sc

def set_visibility(selected=None):
    # Keep backdrop geometry as camera holdouts in sprite passes. Thus a sign in
    # front of a counter cuts a clean hole in the sprite, revealing that same sign
    # in bg.png. Indirect illumination and object shadows remain in every pass.
    for name,objects in GROUPS.items():
        visible=selected is None or name==selected or name=='background'
        holdout=selected not in [None,'background'] and name=='background'
        for obj in objects:
            obj.visible_camera=visible
            obj.is_holdout=holdout
    bpy.context.scene.render.film_transparent=selected not in [None,'background']

def timed_render(path):
    started=time.perf_counter();render(path)
    TIMES.append({'file':str(Path(path).relative_to(ROOT)), 'seconds':round(time.perf_counter()-started,3)})
    print('ROXY_RENDER',json.dumps(TIMES[-1]),flush=True)
    (ROOT/'qa').mkdir(exist_ok=True)
    (ROOT/'qa'/'render_times.json').write_text(json.dumps(TIMES,indent=2))

def bounds_for(name,pad=5):
    sc=bpy.context.scene
    bpy.context.view_layer.update()
    coords=[]
    for obj in GROUPS[name]:
        for co in obj.bound_box:
            p=world_to_camera_view(sc,sc.camera,obj.matrix_world@Vector(co))
            coords.append((p.x*1920,(1-p.y)*1080))
    return [max(0,math.floor(min(p[0] for p in coords))-pad),max(0,math.floor(min(p[1] for p in coords))-pad),
            min(1920,math.ceil(max(p[0] for p in coords))+pad),min(1080,math.ceil(max(p[1] for p in coords))+pad)]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['preview','final','layers'],default='preview')
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--scale',type=float,default=1)
    parser.add_argument('--tag',default='preview')
    parser.add_argument('--only',default='')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    started=time.perf_counter()
    sc=build(args.samples,args.scale)
    print('ROXY_BUILD_SECONDS',round(time.perf_counter()-started,3),'OBJECTS',len(bpy.data.objects),flush=True)
    if args.mode=='preview':
        timed_render(ROOT/'qa'/(args.tag+'.png'))
        return
    (ROOT/'out').mkdir(exist_ok=True)
    from depth_pass import configure, export_array
    position_dir=ROOT/'qa'/'positions'
    position_dir.mkdir(exist_ok=True)
    position_output=configure(sc,position_dir)
    position_output.mute=True
    sc.cycles.adaptive_threshold=.01 if args.mode=='final' else .025
    for name in META:
        b=bounds_for(name)
        META[name].update({'file':'occ_'+name+'.png','x':b[0],'y':b[1],'w':b[2]-b[0],'h':b[3]-b[1]})
    manifest={'size':[1920,1080],'scale2x':True,'bg':'bg.png','glow':None,
              'occluders':sorted(META.values(),key=lambda o:o['depth']),
              'baked_signs':['tickets','snackbar','gate','restroom','roxy','bus95','arcade_orbit','popcorn','standee_midnight','standee_voyager'],
              'projection':{'origin':[900,350],'tile_x':[60,30],'tile_y':[-60,30],'vertical_px_per_blender_unit':ZPP},
              'billboard_rect':[1296,40,576,324],
              'alpha':'PNG straight (unassociated); browser source-over, do not premultiply again',
              'render_device':sc['render_device'], 'seed':1997,
              'footprint_changes':[{'name':'offscreen_street_and_sidewalk_padding',
                                    'original':[-9,9.15,19,13.5],'footprint':[-12,9.15,23,13.5],
                                    'reason':'Additional paving lies wholly outside the 1920x1080 frame; all visible walkable areas and prop footprints are unchanged.'}],
              'height_changes':[{'name':'bench','from':18,'to':28},{'name':'podium','from':46,'to':49},{'name':'bus_stop','from':86,'to':96}],
              'notes':['Standees and bus shelter preserve original geometry extensions outside sorting footprint.',
                       'Long props require per-tile depth slicing as in original addProp(). See depth_slices metadata.',
                       'Restroom occupancy remains a dynamic DOM status; only RESTROOM is baked.',
                       'Movie marquees and poster apertures deliberately blank.'],
              'marquees':[{'screen':i,'bottom_center':project(0,a,124) if w=='u' else project(a,0,124),'inner_size':[176,92]} for i,(w,a) in enumerate([('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)],1)]}
    (ROOT/'out'/'manifest.json').write_text(json.dumps(manifest,indent=2))
    if args.mode=='final':
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy.blend'))
    scales=[1,2] if args.mode=='final' else [args.scale]
    selected=args.only.split(',') if args.only else None
    for scale in scales:
        suffix='@2x' if scale==2 else ''
        sc.render.resolution_x=int(1920*scale);sc.render.resolution_y=int(1080*scale)
        sc.render.use_border=False;sc.render.use_crop_to_border=False
        if not selected or 'full' in selected:
            set_visibility();timed_render(ROOT/'out'/('full'+suffix+'.png'))
            shutil.copyfile(ROOT/'out'/('full'+suffix+'.png'),ROOT/'qa'/('cycles_full'+suffix+'.png'))
        if not selected or 'bg' in selected:
            set_visibility('background');timed_render(ROOT/'out'/('bg'+suffix+'.png'))
        for name,meta in META.items():
            if selected and name not in selected:continue
            set_visibility(name)
            x,y,w,h=[meta[k] for k in ['x','y','w','h']]
            sc.render.use_border=True;sc.render.use_crop_to_border=True
            sc.render.border_min_x=x/1920;sc.render.border_max_x=(x+w)/1920
            sc.render.border_min_y=(1080-y-h)/1080;sc.render.border_max_y=(1080-y)/1080
            position_output.mute=False
            position_output.file_name=name+suffix+'_'
            timed_render(ROOT/'out'/('occ_'+name+suffix+'.png'))
            position_path=position_dir/(name+suffix+'_FloorUV.exr')
            export_array(position_path,position_dir/(name+suffix+'.npz'))
            position_path.unlink()
            position_output.mute=True
        sc.render.use_border=False;sc.render.use_crop_to_border=False
    set_visibility()

if __name__=='__main__':main()
