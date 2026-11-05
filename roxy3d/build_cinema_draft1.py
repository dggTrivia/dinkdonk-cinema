"""Brief 28: a NEW auditorium; exactly one still, never a lobby/bundle mutation.

Blender 5.2.3: --background --factory-startup --python <absolute script path>
Append -- --preflight for geometry/camera checks without saving or rendering.
An existing delivered PNG is an intentional stop gate; choose a new draft for revisions.
"""
import sys
sys.dont_write_bytecode = True
import os
import math
import json
import time
import random
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QA = ROOT / 'qa11'
SOURCE = ROOT / 'roxy_pass10_draft.blend'
TARGET = ROOT / 'roxy_cinema.blend'
IMAGE = QA / 'cinema_draft_01.png'
for key, folder in [('OPTIX_CACHE_PATH', 'optix'), ('CUDA_CACHE_PATH', 'cuda'),
                    ('TEMP', 'temp'), ('TMP', 'temp')]:
    directory = QA / 'runtime' / folder
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(directory)

import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

W, H = 1920, 1080
PPU = 60 * math.sqrt(2)
ZPP = 73.48469228349535
OX, OY = 800.0, 535.0
U1, V1 = 13.0, 7.8
SU0, SU1 = 2.5, 11.7
SZ0 = 100.0
SZ1 = SZ0 + (SU1 - SU0) * 9 / 16 * ZPP
RIGHT = Vector((2**-.5, 2**-.5, 0))
UP = Vector((-math.sqrt(.125), math.sqrt(.125), math.sqrt(.75)))
NORMAL = RIGHT.cross(UP)
SIDE_ROT = Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_quaternion()
RNG = random.Random(281997)
COLLECTION = None
M = {}
REUSED = []
ROWS = []
SEATS = [round(2.25 + j * .88, 4) for j in range(12)]
for i in range(6):
    ROWS.append({'row': chr(65+i), 'v': round(2.65+i*.90, 4),
                 'floor_zpx': i*22.0, 'seat_u': SEATS[:],
                 'cushion_zpx_above_floor': 22.0, 'back_top_zpx_above_floor': 61.0,
                 'seat_back_object': 'Row %s seat backs - future occluder' % chr(65+i)})


def xyz(u, v, z=0):
    return Vector((u, -v, z / ZPP))


def project(u, v, z=0):
    return [OX+(u-v)*60, OY+(u+v)*30-z]


def collection(name):
    global COLLECTION
    COLLECTION = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(COLLECTION)
    return COLLECTION


def register(ob):
    COLLECTION.objects.link(ob)
    return ob


def mesh(name, vertices, faces, material):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    ob = register(bpy.data.objects.new(name, data))
    if material:
        data.materials.append(material)
    return ob


def box(name, u0, v0, u1, v1, z0, z1, material, bevel=.012):
    ob = mesh(name, [xyz(u, v, z) for u,v,z in
        [(u0,v0,z0),(u0,v0,z1),(u0,v1,z0),(u0,v1,z1),
         (u1,v0,z0),(u1,v0,z1),(u1,v1,z0),(u1,v1,z1)]],
        [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)], material)
    # u,v handedness is reversed; explicitly recalculate outward normals.
    for polygon in ob.data.polygons:
        polygon.flip()
    if bevel:
        mod = ob.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        ob.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return ob


def line(name, points, material, radius=.012, cyclic=False):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, point in zip(spline.points, points):
        p.co = (*xyz(*point), 1)
    spline.use_cyclic_u = cyclic
    ob = register(bpy.data.objects.new(name, data))
    data.materials.append(material)
    return ob


def cylinder(name, u, v, z, radius, depth, material, axis=(0,0,1), count=20):
    q = Vector((0,0,1)).rotation_difference(Vector(axis))
    center = xyz(u,v,z)
    vertices = [center + q @ Vector((radius*math.cos(i*math.tau/count),
                radius*math.sin(i*math.tau/count), zz))
                for zz in [-depth/2,depth/2] for i in range(count)]
    faces = [tuple(range(count-1,-1,-1)), tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    ob = mesh(name,vertices,faces,material)
    mod = ob.modifiers.new('Small edge bevel','BEVEL'); mod.width=.006; mod.segments=2
    for p in ob.data.polygons:
        p.use_smooth = len(p.vertices)==4
    return ob


def text(name, body, u, v, z, size, material):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.align_x = 'CENTER'; data.align_y = 'CENTER'
    data.size = size; data.extrude = .001
    ob = register(bpy.data.objects.new(name,data))
    ob.location = xyz(u,v,z)
    ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = SIDE_ROT
    data.materials.append(material)
    return ob


def material(name, rgb, rough=.7, metal=0, emission=0):
    ma = bpy.data.materials.new(name)
    ma.diffuse_color = (*rgb,1)
    ma.use_nodes = True
    p = ma.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb,1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emission:
        p.inputs['Emission Color'].default_value = (*rgb,1)
        p.inputs['Emission Strength'].default_value = emission
    return ma


def light(name, point, target, energy, color, size, size_y=None):
    data = bpy.data.lights.new(name,'AREA')
    data.energy = energy; data.color=color
    data.shape = 'RECTANGLE' if size_y else 'DISK'
    data.size = size
    if size_y: data.size_y = size_y
    ob = register(bpy.data.objects.new(name,data))
    ob.location = xyz(*point)
    ob.rotation_euler = (xyz(*target)-ob.location).to_track_quat('-Z','Y').to_euler()
    ob['lighting_state'] = 'house_up'; ob['switch_group'] = COLLECTION.name
    return ob


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    return ob


def palette():
    names = ['wall plum','dark plum','velvet teal','velvet burgundy','warm brass',
             'black enamel','warm light','ink','cyan neon','pink neon','carpet inset',
             'D10 wet paint | carpet aubergine','D10 wet paint | carpet midnight',
             'Pass4 muted weave confetti pink','Pass4 muted weave confetti lilac',
             'Pass4 muted weave confetti gold','Pass4 muted weave confetti cyan',
             'D3 cut plaster core']
    with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
        assert all(n in src.materials for n in names)
        dst.materials = names
    for ma in dst.materials:
        M[ma.name] = ma
        REUSED.append(ma.name)
    # The approved file retains carpet as a wet-layer wrapper. Copy the saved
    # dry Principled network and reconnect its output; leave the library untouched.
    for key, source in [('carpet aubergine','D10 wet paint | carpet aubergine'),
                        ('carpet midnight','D10 wet paint | carpet midnight')]:
        ma = M[source].copy(); ma.name = 'Cinema dry reuse - '+key
        nodes=ma.node_tree.nodes; p=nodes.get('Principled BSDF')
        ma.node_tree.links.new(p.outputs['BSDF'],nodes.get('Material Output').inputs['Surface'])
        for n in list(nodes):
            if n.type == 'GROUP' and 'WetLayer' in n.name: nodes.remove(n)
        M[key]=ma
    M['screen'] = material('Cinema plain matte projection fabric - NO emission',(.66,.65,.62),1)
    p=M['screen'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Specular IOR Level'].default_value=.08
    M['mask'] = material('Cinema black light-absorbing masking',(.004,.003,.006),1)
    M['concrete'] = material('Cinema dark structural slab core',(.075,.072,.088),.9)
    M['amber'] = material('Cinema small amber aisle lamps',(1,.35,.055),.55,emission=2.0)
    M['exit'] = material('Cinema green EXIT lettering',(.15,.8,.35),.5,emission=2.2)


def flecks(u0,v0,u1,v1,z,density=19):
    vertices=[]; faces=[]; indices=[]
    for i in range(int((u1-u0)*(v1-v0)*density)):
        u=RNG.uniform(u0+.035,u1-.035); v=RNG.uniform(v0+.035,v1-.035)
        a=RNG.uniform(0,math.tau); length=RNG.uniform(.025,.06); width=.009
        du,dv=math.cos(a)*length,math.sin(a)*length
        k=len(vertices)
        vertices += [xyz(u-du,v-dv,z),xyz(u+du,v+dv,z),
                     xyz(u+du-width,v+dv+width,z),xyz(u-du-width,v-dv+width,z)]
        faces.append((k,k+1,k+2,k+3)); indices.append(RNG.randrange(4))
    mats=[M['Pass4 muted weave confetti '+c] for c in ['pink','cyan','gold','lilac']]
    ob=mesh('Muted woven 1990s cinema carpet flecks',vertices,faces,mats[0])
    for ma in mats[1:]: ob.data.materials.append(ma)
    for p,idx in zip(ob.data.polygons,indices): p.material_index=idx


def floor_and_steps():
    collection('01 Cutaway floor and stadium structure')
    box('Front structural slab exposed at cut',0,0,U1,3.10,-17,-.1,M['concrete'])
    box('Front cross aisle midnight carpet',0,0,U1,3.10,-.1,0,M['carpet midnight'],.002)
    flecks(.15,1.35,12.85,2.22,.05,15)
    for i,row in enumerate(ROWS):
        lo=2.20+i*.9; hi=lo+.9 if i<5 else V1; z=row['floor_zpx']
        # Thin stepped slab: the exposed underside follows the tier profile.
        box('Tier %s exposed structural cut' % row['row'],1.60,lo,U1,hi,z-17,z-.15,M['concrete'])
        box('Tier %s purple carpet' % row['row'],1.60,lo,U1,hi,z-.15,z,M['carpet aubergine'],.002)
        flecks(1.72,lo+.035,12.84,hi-.035,z+.045,20)
        if i:
            box('Tier %s vertical riser' % row['row'],1.60,lo,U1,lo+.035,z-22,z-.3,M['dark plum'],.003)
            line('Tier %s brass nosing' % row['row'],[(1.65,lo+.045,z+.2),(12.96,lo+.045,z+.2)],M['warm brass'],.006)
        # Two eleven-pixel half-steps per tier in a 1.6-tile side aisle.
        steps=[(lo,hi,z)] if i==0 else [(lo,lo+.45,z-11),(lo+.45,hi,z)]
        for a,b,h in steps:
            box('Side aisle step solid',0,a,1.60,b,h-18,h-.1,M['concrete'])
            box('Teal side aisle carpet tread',.03,a,1.59,b,h-.1,h+.03,M['carpet inset'],.003)
            if i:
                box('Side aisle eleven pixel riser',.02,a,1.60,a+.035,h-11,h,M['dark plum'],.002)
            line('Side aisle brass tread edge',[(.10,a+.045,h+.2),(1.52,a+.045,h+.2)],M['warm brass'],.007)
    # Stage stays well below the screen's lower edge, including its projection.
    box('Low stage dark apron',1.30,.12,12.95,1.27,0,27,M['dark plum'],.025)
    box('Low stage midnight carpet top',1.30,.12,12.95,1.27,27,28,M['carpet midnight'],.008)
    line('Stage apron brass lip',[(1.35,1.26,26),(12.92,1.26,26)],M['warm brass'],.009)
    for u in [1.45,12.62]:
        box('Stage corner amber marker',u,1.273,u+.16,1.295,9,13,M['amber'],.006)


def curtain(u0,u1):
    vertices=[]; faces=[]; segments=100
    for i in range(segments+1):
        u=u0+(u1-u0)*i/segments
        v=.19+.095*math.cos(i/segments*math.tau*7)
        for z in [31,SZ1+15]: vertices.append(xyz(u,v,z))
    for i in range(segments): faces.append((2*i,2*i+1,2*i+3,2*i+2))
    ob=mesh('Drawn open pleated red velvet curtain',vertices,faces,M['velvet burgundy'])
    for p in ob.data.polygons: p.use_smooth=True
    mod=ob.modifiers.new('Velvet thickness','SOLIDIFY');mod.thickness=.018
    line('Curtain lower velvet hem',[(u0+(u1-u0)*i/100,.19+.095*math.cos(i/100*math.tau*7),32) for i in range(101)],M['velvet burgundy'],.016)


def walls_screen_door():
    collection('02 Two retained acoustic walls and screen')
    box('Screen wall structural shell',-.24,-.36,13.0,-.12,-17,500,M['wall plum'])
    # Real opening in u=0, front entrance at floor level; two solid wall sections.
    for a,b in [(0,1.48),(2.88,V1)]:
        box('Side wall structural shell',-.24,a,-.04,b,-17,500,M['wall plum'])
    box('Solid lintel above entrance',-.24,1.48,-.04,2.88,115,500,M['wall plum'])
    box('Screen wall pale cut cap',-.24,-.36,13.0,-.12,500,503,M['D3 cut plaster core'],.003)
    box('Side wall pale cut cap',-.24,0,-.04,V1,500,503,M['D3 cut plaster core'],.003)
    for v in [.35,3.28,4.08,4.88,5.68,6.48,7.28]:
        for z0,z1 in [(125,259),(266,412),(419,487)]:
            box('Side wall padded acoustic panel',-.036,v-.31,.035,v+.31,z0,z1,M['velvet teal' if z0==266 else 'dark plum'],.028)
            for z in range(z0+14,z1,28):
                line('Side acoustic panel diagonal quilting',[(.046,v-.28,z),(.046,v,z+12),(.046,v+.28,z)],M['wall plum'],.003)
    for u in [.65,1.38,12.46]:
        box('Screen wall acoustic fabric strip',u-.29,-.114,u+.29,-.065,43,487,M['dark plum'],.02)
    # Low teal wainscot with brass ribs visually connects to the lobby.
    for a,b in [(0,1.48),(2.88,V1)]:
        box('Side wall teal lower wainscot',-.025,a,.04,b,0,109,M['velvet teal'],.006)
        line('Side wall brass wainscot rail',[(.055,a,109),(.055,b,109)],M['warm brass'],.009)
    for v in [3.15+j*.28 for j in range(17)]:
        line('Wainscot slender brass flute',[(.057,v,9),(.057,v,103)],M['warm brass'],.004)
    screen=mesh('SCREEN INNER clean 16 by 9 wall plane v=0',
                [xyz(SU0,0,SZ1),xyz(SU1,0,SZ1),xyz(SU1,0,SZ0),xyz(SU0,0,SZ0)],
                [(3,2,1,0)],M['screen'])
    screen['corner_order']='TL TR BR BL'; screen['physical_aspect']=16/9
    for a,b in [(SU0-.11,SU0),(SU1,SU1+.11)]:
        box('Vertical black screen masking',a,-.06,b,0,SZ0-8,SZ1+8,M['mask'],0)
    for a,b in [(SZ0-8,SZ0),(SZ1,SZ1+8)]:
        box('Horizontal black screen masking',SU0,-.06,SU1,0,a,b,M['mask'],0)
    curtain(1.30,2.31); curtain(12.12,12.91)
    # Padded double doors use the lobby's actual red velvet and brass.
    box('Entrance double door dark reveal',-.02,1.48,.035,2.88,0,115,M['mask'],.004)
    for a,b in [(1.53,2.165),(2.195,2.83)]:
        box('Entrance padded red velvet door leaf',.036,a,.088,b,1,110,M['velvet burgundy'],.022)
        for z in range(15,101,14):
            line('Entrance door diamond seam',[(.093,a+.04,z),(.093,(a+b)/2,z+9),(.093,b-.04,z),(.093,(a+b)/2,z-9),(.093,a+.04,z)],M['dark plum'],.004)
        box('Entrance brass kickplate',.092,a+.035,.104,b-.035,3,17,M['warm brass'],.005)
    for v in [2.115,2.245]:
        line('Entrance polished door pull',[(.15,v,42),(.15,v,60)],M['warm brass'],.015)
    for v in [1.49,2.87]:
        box('Entrance brass jamb',.04,v-.018,.125,v+.018,0,114,M['warm brass'],.005)
    box('Entrance brass head',.04,1.48,.125,2.88,112,115,M['warm brass'],.004)
    box('EXIT black fixture',.06,1.78,.17,2.58,128,147,M['black enamel'],.012)
    text('Lit entrance EXIT','EXIT',.179,2.18,137,.20,M['exit'])
    # Small side-wall plaque, completely away from the projection rectangle.
    box('DINK DONK side wall brass plaque rim',.052,3.48,.115,5.62,278,325,M['warm brass'],.012)
    box('DINK DONK side wall plaque dark center',.115,3.51,.135,5.59,280,323,M['dark plum'],.008)
    text('DINK DONK plaque lettering','DINK DONK',.145,4.55,308,.235,M['cyan neon'])
    text('Side wall Screen 1 lettering','S C R E E N   1',.146,4.55,291,.115,M['warm light'])
    return screen


def seats():
    for row in ROWS:
        collection('03 Row '+row['row']+' seats')
        v=row['v']; z=row['floor_zpx']; backs=[]
        for j,u in enumerate(SEATS):
            prefix='Seat %s%02d' % (row['row'],j+1)
            box(prefix+' floor pedestal',u-.14,v-.13,u+.14,v+.18,z+.4,z+4,M['black enamel'],.02)
            for du in [-.22,.22]:
                box(prefix+' steel support',u+du-.03,v+.06,u+du+.03,v+.18,z+3,z+31,M['black enamel'],.01)
                cylinder(prefix+' brass flip hinge',u+du,v+.10,z+22,.055,.025,M['warm brass'],axis=(1,0,0),count=16)
            box(prefix+' flip seat shell',u-.325,v-.36,u+.325,v+.13,z+14,z+18,M['black enamel'],.035)
            box(prefix+' upholstered seat cushion',u-.305,v-.35,u+.305,v+.12,z+17,z+22,M['velvet burgundy'],.030)
            backs.append(box(prefix+' back shell',u-.348,v+.18,u+.348,v+.34,z+17,z+62,M['black enamel'],.055))
            backs.append(box(prefix+' red velvet back upholstery',u-.324,v+.157,u+.324,v+.355,z+24,z+61,M['velvet burgundy'],.060))
            # Rear upholstery seams also belong to the future row occluder.
            for du in [-.258,.258]:
                backs.append(line(prefix+' rear tailored piping',[(u+du,v+.361,z+28),(u+du,v+.361,z+53),(u+du*.83,v+.361,z+57)],M['dark plum'],.004))
            backs.append(box(prefix+' rear brass number plate',u-.073,v+.36,u+.073,v+.37,z+43,z+48,M['warm brass'],.003))
        for j in range(13):
            u=SEATS[0]-.44+j*.88
            box('Row %s shared armrest stem'%row['row'],u-.027,v-.07,u+.027,v+.15,z+5,z+34,M['black enamel'],.008)
            box('Row %s padded armrest'%row['row'],u-.065,v-.30,u+.065,v+.26,z+32,z+36,M['black enamel'],.025)
            # Open cupholder: brass annulus around a visibly black recess.
            cylinder('Cupholder black inner well',u,v-.18,z+36.0,.057,.012,M['mask'],count=20)
            pts=[(u+.063*math.cos(k*math.tau/24),v-.18+.063*math.sin(k*math.tau/24),z+36.5) for k in range(24)]
            line('Cupholder brass rim',pts,M['warm brass'],.007,True)
        ob=join(backs,row['seat_back_object'])
        ob['row_id']=row['row']; ob['future_occluder']=True
        ob['facing']='toward v=0; backs on positive-v side'


def fixtures_and_lighting():
    collection('04 HOUSE sconces - switchable')
    for v in [1.00,3.15,5.83,7.32]:
        z=212 if v<2 else 245
        box('Brass sconce backplate',.035,v-.11,.10,v+.11,z-16,z+17,M['warm brass'],.015)
        box('Warm opal sconce diffuser',.10,v-.075,.19,v+.075,z-12,z+13,M['warm light'],.022)
        for zz in [z-13,z+14]: box('Sconce brass end cap',.095,v-.09,.20,v+.09,zz,zz+2,M['warm brass'],.006)
        light('HOUSE warm side sconce',(.24,v,z),(2.6,v,z-50),32,(1,.64,.36),.35,.22)
    collection('05 HOUSE ceiling softboxes - switchable')
    for u,v,power in [(3.2,3.3,370),(7.1,3.3,430),(11.1,3.3,390),
                      (3.2,6.6,370),(7.1,6.6,430),(11.1,6.6,390)]:
        light('HOUSE warm overhead',(u,v,480),(u,v,40),power,(1,.77,.54),3.0,2.2)
    light('HOUSE soft stage wash',(7.3,2.0,465),(7.3,0,260),130,(1,.83,.68),5.5,2.0)
    collection('06 AISLE safety lamps and handrail - switchable')
    rail=[]
    for i,row in enumerate(ROWS):
        v=row['v']-.25; z=row['floor_zpx']
        rail.append((.28,v,z+61))
        line('Side aisle brass rail post',[(.28,v,z),(.28,v,z+61)],M['warm brass'],.015)
        cylinder('Side aisle rail foot',.28,v,z+1,.065,.028,M['warm brass'])
        box('Small amber step-edge lamp',.045,v-.11,.082,v+.11,z+8,z+12,M['amber'],.008)
        light('AISLE amber step pool',(.10,v,z+12),(1.4,v+.2,z),2.3,(1,.40,.10),.19,.08)
    line('Continuous brass side aisle handrail',rail,M['warm brass'],.024)


def configure():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.name='DINK DONK Screen 1 - Cinema draft 01'
    sc.render.engine='CYCLES'
    sc.cycles.samples=256; sc.cycles.use_adaptive_sampling=True
    sc.cycles.adaptive_min_samples=48; sc.cycles.adaptive_threshold=.008
    sc.cycles.use_denoising=True; sc.cycles.seed=281997
    sc.cycles.max_bounces=10; sc.cycles.diffuse_bounces=5; sc.cycles.glossy_bounces=4
    sc.cycles.transmission_bounces=4
    sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
    sc.render.image_settings.color_depth='8'; sc.render.image_settings.compression=25
    sc.render.film_transparent=False; sc.render.use_compositing=False
    sc.render.use_sequencer=False; sc.render.use_persistent_data=True
    sc.render.use_file_extension=True
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
    sc.view_settings.exposure=.25
    world=bpy.data.worlds.new('Cinema quiet plum ambient')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.033,.025,.049,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.24
    sc.world=world
    collection('00 Exact page camera and calibration markers')
    data=bpy.data.cameras.new('Lobby-matched orthographic 60 0 45')
    data.type='ORTHO'; data.ortho_scale=22.627416998
    data.clip_start=.01; data.clip_end=200
    cam=register(bpy.data.objects.new('Cinema exact page camera',data))
    cam.rotation_euler=(math.radians(60),0,math.radians(45))
    cam.location=RIGHT*((960-OX)/PPU)+UP*((OY-540)/PPU)+NORMAL*40
    sc.camera=cam
    device='CPU'; prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ['OPTIX','CUDA']:
        try:
            prefs.compute_device_type=backend; prefs.get_devices()
            found=[d for d in prefs.devices if d.type==backend]
            if found:
                for d in prefs.devices: d.use=d.type==backend
                sc.cycles.device='GPU'; device=backend+': '+', '.join(d.name for d in found)
                sc.cycles.denoiser='OPTIX' if backend=='OPTIX' else 'OPENIMAGEDENOISE'
                break
        except Exception: pass
    sc['render_device']=device; sc['brief']='BRIEF-28-cinema-draft1.md'
    sc['source_palette']=str(SOURCE); sc['draft_only']=True
    sc['projection_origin_px']=[OX,OY]
    print('CINEMA_DEVICE',device,flush=True)
    return sc


def calibration(sc):
    bpy.context.view_layer.update()
    points=[(0,0,0),(13,0,0),(0,7.8,0),(13,7.8,110),(0,0,170)]
    results=[]
    for i,point in enumerate(points):
        ob=register(bpy.data.objects.new('Calibration marker %d' % (i+1),None))
        ob.location=xyz(*point); ob.empty_display_type='SPHERE'; ob.empty_display_size=.075
        expected=project(*point)
        p=world_to_camera_view(sc,sc.camera,ob.location)
        actual=[p.x*W,(1-p.y)*H]
        errors=[actual[j]-expected[j] for j in [0,1]]
        pixel=[math.floor(c)+.5 for c in actual]
        results.append({'uvz':point,'expected_px':expected,'camera_projected_px':actual,
                        'error_px':errors,'nearest_pixel_center_error_px':[pixel[j]-expected[j] for j in [0,1]]})
    assert max(abs(e) for r in results for e in r['error_px'])<=1
    return {'method':'Five non-rendering 3D marker empties; independent Blender world_to_camera_view vs brief formula. No separate calibration image or raster-centroid render.',
            'max_axis_error_px':max(abs(e) for r in results for e in r['error_px']),
            'max_pixel_center_error_px':max(abs(e) for r in results for e in r['nearest_pixel_center_error_px']),
            'passed_1px':True,'points':results}


def screen_check(sc,screen):
    # One half-pixel perimeter sweep plus a two-pixel interior grid. BVH is
    # evaluated geometry, including bevels, curtain thickness and row joins.
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    verts=[]; faces=[]; owners=[]
    for original in list(sc.objects):
        if original.type not in ['MESH','CURVE','FONT'] or original.hide_render: continue
        evaluated=original.evaluated_get(deps)
        me=evaluated.to_mesh()
        offset=len(verts)
        verts.extend(evaluated.matrix_world @ v.co for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
        owners.extend([original.name]*len(me.polygons))
        evaluated.to_mesh_clear()
    tree=BVHTree.FromPolygons(verts,faces,all_triangles=False)
    tests=0; failures=[]
    def check(u,z):
        nonlocal tests
        point=xyz(u,0,z)
        hit=tree.ray_cast(point+NORMAL*45,-NORMAL,46)
        tests+=1
        if hit[2] is None or owners[hit[2]]!=screen.name:
            failures.append({'u':u,'zpx':z,'hit':None if hit[2] is None else owners[hit[2]]})
    # Sample all final image pixel centres inside the quad, including the
    # quarter-pixel-inset boundary. This verifies exact chroma-quad visibility.
    xmin=math.ceil(project(SU0,0,0)[0]-.5); xmax=math.floor(project(SU1,0,0)[0]-.5)
    for ix in range(xmin,xmax+1):
        u=(ix+.5-OX)/60
        top=project(u,0,SZ1)[1]; bottom=project(u,0,SZ0)[1]
        for iy in range(math.ceil(top-.5),math.floor(bottom-.5)+1):
            check(u,OY+u*30-(iy+.5))
    for k in range(1105):
        f=(k+.5)/1105
        for u,z in [(SU0+(SU1-SU0)*f,SZ0+.05),(SU0+(SU1-SU0)*f,SZ1-.05),
                    (SU0+.0005,SZ0+(SZ1-SZ0)*f),(SU1-.0005,SZ0+(SZ1-SZ0)*f)]:
            check(u,z)
    if failures:
        from collections import Counter
        print('SCREEN_BLOCKERS',dict(Counter(f['hit'] for f in failures)),flush=True)
    assert not failures, ('Screen occlusion!',len(failures),failures[:12])
    return {'method':'Orthographic ray cast against evaluated geometry at every inner-quad image pixel centre plus subpixel-inset perimeter',
            'rays':tests,'blocked':0,'passed':True,'emission_strength':0,
            'compositor_glare':False,'physical_width_bu':SU1-SU0,
            'physical_height_bu':(SZ1-SZ0)/ZPP,'aspect':16/9}


def audience_check():
    result=[]
    # A 60px DOM image is bottom-anchored on the cushion. Its complete width
    # (conservatively 60px), foot extent and one-pixel allowance are included.
    for row in ROWS:
        for u in SEATS:
            head=project(u,row['v'],row['floor_zpx']+22+60)
            # Screen bottom slopes +0.5px / +1px in x; its rightmost value
            # under the 60px sprite is the closest possible lower edge.
            edge=OY+.5*(head[0]+30-OX)-SZ0
            clearance=head[1]-edge
            assert clearance>1
            result.append({'row':row['row'],'u':u,'head_top_px':head,
                           'screen_bottom_at_sprite_right_x_px':edge,'clearance_px':clearance})
    return {'emote_height_px':60,'emote_width_px_assumed':60,
            'anchor':'bottom center on floor_zpx + 22px cushion',
            'formula':'clearance = 60*v + screen_bottom_zpx - floor_zpx - 22 - 60 - 15',
            'minimum_clearance_px':min(r['clearance_px'] for r in result),
            'row_minimum_clearance_px':{row['row']:min(r['clearance_px'] for r in result if r['row']==row['row']) for row in ROWS},
            'backrest_coverage':'Back top +61px at v+0.355; projected back top lies 31.65px below the sprite head top at its centre. Lower body is behind the row back; future DOM occlusion not rendered.',
            'passed_all_72_seats':True,'seats':result}


def layout(sc,cal,visibility,audience):
    corners=[project(SU0,0,SZ1),project(SU1,0,SZ1),project(SU1,0,SZ0),project(SU0,0,SZ0)]
    path=[[.80,2.18,0],[.80,2.30,0]]
    for i,row in enumerate(ROWS):
        lo=2.20+i*.9; z=row['floor_zpx']
        if i: path.extend([[.80,lo+.10,z-11],[.80,lo+.55,z]])
        path.append([.80,row['v'],z])
    path.append([.80,7.70,110])
    return {'brief':'BRIEF-28-cinema-draft1.md','scene':'DINK DONK Screen 1 / auditorium / new scene 2',
        'image':'cinema_draft_01.png','resolution':[W,H],
        'coordinates':{'world':'(x,y,z)=(u,-v,zpx/73.48469228349535)',
                       'projection':'[Ox+60*(u-v), Oy+30*(u+v)-zpx]',
                       'Ox':OX,'Oy':OY,'ZPP':ZPP,'pixel_origin':'top left; corners are continuous pixel coordinates'},
        'camera':{'type':'ORTHO','rotation_degrees':[60,0,45],'ortho_scale':22.627416998},
        'calibration':cal,
        'screen':{'wall':'v=0','u_range':[SU0,SU1],'v':0,'zpx_range':[SZ0,SZ1],
                  'corners_1920x1080':dict(zip(['TL','TR','BR','BL'],corners)),
                  'corners_3840x2160':dict(zip(['TL','TR','BR','BL'],[[x*2,y*2] for x,y in corners])),
                  'on_frame_bbox_width_px':(SU1-SU0)*60,'visibility_check':visibility},
        'room':{'u_range':[0,U1],'v_range':[0,V1],'wall_top_zpx':500,
                'kept_walls':['u=0','v=0'],'cut_edges':['u=13','v=7.8'],
                'stage':{'u_range':[1.30,12.95],'v_range':[.12,1.27],'top_zpx':28},
                'front_cross_aisle':{'u_range':[.15,12.95],'v_range':[1.35,2.20],'floor_zpx':0}},
        'seat_count':72,'rows':ROWS,
        'entrance':{'wall':'u=0','u':0,'v_range':[1.48,2.88],'floor_zpx':0,
                    'height_zpx':115,'leaf_height_zpx':110,'height_bu':115/ZPP,
                    'EXIT_center_uvz':[.179,2.18,137]},
        'side_aisle':{'u_range':[.03,1.59],'path_uvzpx':path,'maximum_step_rise_zpx':11,
                      'handrail_u':.28,'handrail_height_above_tier_zpx':61,
                      'row_entry_points_uvzpx':[[1.61,r['v'],r['floor_zpx']] for r in ROWS]},
        'audience_clearance':audience,
        'source_materials':{'blend':SOURCE.name,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                            'appended_datablocks':REUSED,
                            'adaptations':['Copied carpet networks reconnected to their original dry Principled outputs; wet wrapper removed only on copies.']},
        'lighting':{'state':'house_up','switchable_collections':['04 HOUSE sconces - switchable',
                    '05 HOUSE ceiling softboxes - switchable','06 AISLE safety lamps and handrail - switchable'],
                    'screen_emission':0,'glare':False},
        'render':{'engine':'Cycles','max_samples':256,'adaptive_min_samples':48,'adaptive_threshold':.008,
                   'denoise':True,'device':sc['render_device'],'exposure':.25,'view':'AgX / Medium High Contrast'},
        'scope':'One image only; no loops, sprites, occluder exports, weather, page changes or bundle updates.'}


def report(data):
    c=data['screen']['corners_1920x1080']; c4=data['screen']['corners_3840x2160']
    cal=data['calibration']; timing=data['render']
    lines=['# Cinema draft 01 — DINK DONK Screen 1','',
        'New scene 2, built from scratch. One 1920×1080 house-lights-up still, 72 empty flip seats in six stadium rows. '
        'Red velvet, acoustic plum/teal fabric, muted 1990s carpet flecks, brass, padded double entrance, EXIT, '
        'side-wall DINK DONK plaque, lit half-steps and handrail. Slab and rising cross-section are exposed at the two cut edges.','',
        f'Projection: `Ox={OX:g}, Oy={OY:g}`; `P=[800+60(u-v), 535+30(u+v)-zpx]`. '
        'Orthographic camera rotation `(60,0,45)°`, scale `22.627416998`, `ZPP=73.48469228349535`.','',
        'Five marker calibration (Blender camera projection against the independent page formula; no second calibration image):','',
        '| Marker (u,v,zpx) | Error x px | Error y px |','|---|---:|---:|']
    for r in cal['points']:
        lines.append(f"| {tuple(r['uvz'])} | {r['error_px'][0]:.7f} | {r['error_px'][1]:.7f} |")
    lines += ['',f"Maximum axis error {cal['max_axis_error_px']:.7f}px; nearest pixel-centre error ≤{cal['max_pixel_center_error_px']:.3f}px. PASS ±1px. "
        'This is a camera-matrix check with five marker empties, not the separately rendered alpha-centroid test in calibrate.py.','',
        f'Screen: exact flat 16:9 inner surface on `v=0`, `u=[{SU0},{SU1}]`, '
        f'`zpx=[{SZ0:.6f},{SZ1:.6f}]`; projected width {(SU1-SU0)*60:.0f}px. Black border and both open curtains stay outside its four-corner quad.','',
        '| Corner | 1920×1080 (x,y) | 3840×2160 (x,y) |','|---|---|---|']
    for key in ['TL','TR','BR','BL']:
        lines.append(f'| {key} | ({c[key][0]:.6f}, {c[key][1]:.6f}) | ({c4[key][0]:.6f}, {c4[key][1]:.6f}) |')
    lines += ['',f"Screen visibility: {data['screen']['visibility_check']['rays']:,} evaluated-geometry orthographic rays "
        '(every image pixel centre inside the quad and a subpixel-inset perimeter); zero blocked. '
        'Matte light grey, zero emission, no screen artwork, glare, haze or compositor.','',
        f'Room: `u=[0,{U1:g}], v=[0,{V1:g}]`. Stage top `28zpx`; front cross-aisle `v=1.35–2.20`. '
        'Rows face decreasing v; the rear of every seat is toward the camera.','',
        '| Row | Seat-line v | Tier floor zpx | Seat centre u positions |','|---|---:|---:|---|']
    for r in ROWS:
        lines.append(f"| {r['row']} | {r['v']:.2f} | {r['floor_zpx']:.0f} | "+', '.join(f'{u:.2f}' for u in r['seat_u'])+' |')
    lines += ['', 'Entrance: real double-door opening in `u=0`, `v=[1.48,2.88]`, floor `0zpx`, '
        f'height `115zpx` ({115/ZPP:.4f} BU), padded leaves `110zpx`, EXIT centre `(0.179,2.18,137)`. '
        'Side aisle `u=0.03–1.59`, centreline `u=0.80`; all path points and row entries are in '
        '`cinema_layout_01.json`. Two 11px half-steps per 22px tier rise.','',
        'Audience numeric check: a 60px tall × 60px wide image is bottom-anchored at the cushion '
        '`floor_zpx+22`. Against the screen bottom at the sprite’s right edge, '
        '`clearance=60v+100-floor_zpx-22-60-15`. All 72 seats pass. '
        f"Minimum {data['audience_clearance']['minimum_clearance_px']:.2f}px; per-row minima: "+
        ', '.join(f"{k}={v:.2f}px" for k,v in data['audience_clearance']['row_minimum_clearance_px'].items())+'. '
        'Each row’s evaluated back shells, upholstery, seams and number plates are joined into its own '
        '`Row [A–F] seat backs - future occluder` mesh. Backrest top is 31.65px below the centred sprite’s head top, '
        'covering the lower body while leaving head/shoulders; actual DOM audience integration remains for the later page work.','',
        'Saved lobby material datablocks were appended from `roxy_pass10_draft.blend` (approved draft 13). '
        'Carpet copies retain the saved weave/base palette with only their wet wrapper bypassed for a dry indoor floor. '
        'House sconces, overhead lighting and aisle lamps are in separate switchable collections.','',
        f"Render: Blender {bpy.app.version_string}, Cycles adaptive 48–256 / 0.008, denoised, {timing['device']}; "
        f"{timing['seconds']:.2f}s rendering; {timing['build_and_checks_seconds']:.2f}s build/checks; "
        f"{timing['total_seconds']:.2f}s total. One beauty render and one PNG. ",
        '', 'Draft limits: single house-up state; no audience sprites/DOM test, dimmed state, loops, weather or layer exports. '
        'Camera calibration uses projected marker positions to preserve the one-render rule. '
        'Only new files under roxy3d were written; source blends, cloud bundle, out10 and all pages were left alone.','',
        'Re-run on a fresh output location with `build_cinema_draft1.py`; an existing draft PNG intentionally blocks another render. '
        '`-- --preflight` performs geometry/camera checks without rendering or saving a blend.']
    (QA/'CINEMA-DRAFT-01.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    started=time.perf_counter()
    assert bpy.app.version[:3]==(5,2,3),bpy.app.version_string
    preflight='--preflight' in sys.argv
    if not preflight:
        assert not IMAGE.exists(),'Strict draft stop: PNG already exists; no second render.'
        assert not TARGET.exists(),'Refuse to overwrite an existing cinema blend.'
        assert not (QA/'CINEMA-DRAFT-01.md').exists()
        assert not (QA/'cinema_layout_01.json').exists()
    sc=configure(); palette(); floor_and_steps(); screen=walls_screen_door()
    seats(); fixtures_and_lighting()
    collection('00 Exact page camera and calibration markers')
    cal=calibration(sc); visibility=screen_check(sc,screen); audience=audience_check()
    data=layout(sc,cal,visibility,audience)
    print('CINEMA_PREFLIGHT',json.dumps({'origin':[OX,OY],'calibration':cal,
          'screen':data['screen'],'audience_minimum_clearance':audience['minimum_clearance_px'],
          'object_count':len(sc.objects)}),flush=True)
    if preflight:
        print('PREFLIGHT PASSED. NO IMAGE RENDERED. NO BLEND SAVED.',flush=True)
        return
    sc.render.filepath=str(IMAGE)
    sc['screen_quad_1920']=json.dumps(data['screen']['corners_1920x1080'])
    sc['layout_contract']=json.dumps(data)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    built=time.perf_counter()
    print('CINEMA_SINGLE_RENDER_START',flush=True)
    bpy.ops.render.render(write_still=True)
    ended=time.perf_counter()
    data['render'].update(seconds=ended-built,build_and_checks_seconds=built-started,total_seconds=ended-started,
                          blender_version=bpy.app.version_string)
    assert IMAGE.exists()
    (QA/'cinema_layout_01.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    report(data)
    print('CINEMA_DRAFT_01_RENDER_COMPLETE',flush=True)


if __name__=='__main__':
    main()
