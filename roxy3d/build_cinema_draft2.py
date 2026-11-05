"""Brief 29: one larger, lived-in auditorium still; all draft-1 files preserved.
Run Blender 5.2.3 --background --factory-startup --python this_file.
Append -- --preflight for geometry/camera checks only. Existing outputs block rendering.
All explicit writes, runtime and GPU caches are isolated below roxy3d/.
"""
import sys
sys.dont_write_bytecode = True
import os, math, json, time, random, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT / 'qa11'
SOURCE = ROOT / 'roxy_pass10_draft.blend'
TARGET = ROOT / 'roxy_cinema_draft2.blend'
IMAGE = QA / 'cinema_draft_02.png'
REPORT = QA / 'CINEMA-DRAFT-02.md'
LAYOUT = QA / 'cinema_layout_02.json'
RUNTIME = QA / 'runtime02'
for key, folder in [('OPTIX_CACHE_PATH','optix'),('CUDA_CACHE_PATH','cuda'),
                    ('TEMP','temp'),('TMP','temp')]:
    directory = RUNTIME / folder
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(directory)
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
W, H = 1920, 1080
PPU = 60 * math.sqrt(2)
ZPP = 73.48469228349535
OX, OY = 700.0, 635.0
U1, V1 = 20.10, 13.38
WALL_Z = 945.0
SU0, SU1, SZ0 = 3.50, 17.10, 145.0
SZ1 = SZ0 + (SU1 - SU0) * 9 / 16 * ZPP
ROW_LO, ROW_PITCH, RISE = 2.58, 1.08, 22.0
RIGHT = Vector((2**-.5, 2**-.5, 0))
UP = Vector((-math.sqrt(.125), math.sqrt(.125), math.sqrt(.75)))
NORMAL = RIGHT.cross(UP)
SIDE_ROT = Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
RNG = random.Random(291997)
COLLECTION = None
M, REUSED, ROWS = {}, [], []
SEATS = [round(2.25+j*.88,4) for j in range(20)]
for i in range(10):
    ROWS.append({'row':chr(65+i), 'v':round(3.12+i*ROW_PITCH,4),
        'floor_zpx':i*RISE, 'seat_u':SEATS[:],
        'cushion_zpx_above_floor':22.0, 'back_top_zpx_above_floor':61.0,
        'seat_back_object':'Row %s seat backs - future occluder' % chr(65+i)})
LIVED_IN = {'patched_seats':['B03','D08','F05','H12'],
    'faded_seats':['A09','C04','E10','G06','I13'],
    'half_folded_seat':'C02', 'popcorn_pieces':0, 'cups':0, 'boxes':0}


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



def configure():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.name='DINK DONK Screen 1 - Cinema draft 02'
    sc.render.engine='CYCLES'
    sc.cycles.samples=384; sc.cycles.use_adaptive_sampling=True
    sc.cycles.adaptive_min_samples=64; sc.cycles.adaptive_threshold=.007
    sc.cycles.use_denoising=True; sc.cycles.seed=291997
    sc.cycles.max_bounces=10; sc.cycles.diffuse_bounces=5; sc.cycles.glossy_bounces=4
    sc.cycles.transmission_bounces=4
    sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
    sc.render.image_settings.color_depth='8'; sc.render.image_settings.compression=25
    sc.render.film_transparent=False; sc.render.use_compositing=False
    sc.render.use_sequencer=False; sc.render.use_persistent_data=True
    sc.render.use_file_extension=True
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
    sc.view_settings.exposure=.10
    world=bpy.data.worlds.new('Cinema quiet plum ambient')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.033,.025,.049,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.17
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
    sc['render_device']=device; sc['brief']='BRIEF-29-cinema-draft2.md'
    sc['source_palette']=str(SOURCE); sc['draft_only']=True
    sc['projection_origin_px']=[OX,OY]
    print('CINEMA_DEVICE',device,flush=True)
    return sc



def calibration(sc):
    bpy.context.view_layer.update()
    points=[(0,0,0),(U1,0,0),(0,V1,0),(U1,V1,198),(0,0,WALL_Z)]
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



def walls_screen_door():
    collection('02 Two retained acoustic walls and screen')
    box('Screen wall structural shell',-.24,-.36,U1,-.12,-17,WALL_Z,M['wall plum'])
    # Real opening in u=0, front entrance at floor level; two solid wall sections.
    for a,b in [(0,1.48),(2.88,V1)]:
        box('Side wall structural shell',-.24,a,-.04,b,-17,WALL_Z,M['wall plum'])
    box('Solid lintel above entrance',-.24,1.48,-.04,2.88,115,WALL_Z,M['wall plum'])
    box('Screen wall pale cut cap',-.24,-.36,U1,-.12,WALL_Z,WALL_Z+3,M['D3 cut plaster core'],.003)
    box('Side wall pale cut cap',-.24,0,-.04,V1,WALL_Z,WALL_Z+3,M['D3 cut plaster core'],.003)
    for v in [.35]+[3.28+j*.88 for j in range(12)]:
        for z0,z1 in [(125,259),(266,412),(419,565),(572,718),(725,871),(878,930)]:
            box('Side wall padded acoustic panel',-.036,v-.31,.035,v+.31,z0,z1,M['velvet teal' if z0==266 else 'dark plum'],.028)
            for z in range(z0+14,z1,28):
                line('Side acoustic panel diagonal quilting',[(.046,v-.28,z),(.046,v,z+12),(.046,v+.28,z)],M['wall plum'],.003)
    for u in [.65,1.38,18.83,19.65]:
        box('Screen wall acoustic fabric strip',u-.29,-.114,u+.29,-.065,43,WALL_Z-20,M['dark plum'],.02)
    # Low teal wainscot with brass ribs visually connects to the lobby.
    for a,b in [(0,1.48),(2.88,V1)]:
        box('Side wall teal lower wainscot',-.025,a,.04,b,0,109,M['velvet teal'],.006)
        line('Side wall brass wainscot rail',[(.055,a,109),(.055,b,109)],M['aged brass'],.009)
    for v in [3.15+j*.28 for j in range(36)]:
        line('Wainscot slender brass flute',[(.057,v,9),(.057,v,103)],M['aged brass'],.004)
    screen=mesh('SCREEN INNER clean 16 by 9 wall plane v=0',
                [xyz(SU0,0,SZ1),xyz(SU1,0,SZ1),xyz(SU1,0,SZ0),xyz(SU0,0,SZ0)],
                [(3,2,1,0)],M['screen'])
    screen['corner_order']='TL TR BR BL'; screen['physical_aspect']=16/9
    for a,b in [(SU0-.11,SU0),(SU1,SU1+.11)]:
        box('Vertical black screen masking',a,-.06,b,0,SZ0-8,SZ1+8,M['mask'],0)
    for a,b in [(SZ0-8,SZ0),(SZ1,SZ1+8)]:
        box('Horizontal black screen masking',SU0,-.06,SU1,0,a,b,M['mask'],0)
    curtain(2.30,3.28); curtain(17.54,18.43)
    # Padded double doors use the lobby's actual red velvet and brass.
    box('Entrance double door dark reveal',-.02,1.48,.035,2.88,0,115,M['mask'],.004)
    for a,b in [(1.53,2.165),(2.195,2.83)]:
        box('Entrance padded red velvet door leaf',.036,a,.088,b,1,110,M['velvet burgundy'],.022)
        for z in range(15,101,14):
            line('Entrance door diamond seam',[(.093,a+.04,z),(.093,(a+b)/2,z+9),(.093,b-.04,z),(.093,(a+b)/2,z-9),(.093,a+.04,z)],M['dark plum'],.004)
        box('Entrance brass kickplate',.092,a+.035,.104,b-.035,3,17,M['aged brass'],.005)
    for v in [2.115,2.245]:
        line('Entrance polished door pull',[(.15,v,42),(.15,v,60)],M['aged brass'],.015)
    for v in [1.49,2.87]:
        box('Entrance brass jamb',.04,v-.018,.125,v+.018,0,114,M['aged brass'],.005)
    box('Entrance brass head',.04,1.48,.125,2.88,112,115,M['aged brass'],.004)
    box('EXIT black fixture',.06,1.78,.17,2.58,128,147,M['black enamel'],.012)
    text('Lit entrance EXIT','EXIT',.179,2.18,137,.20,M['exit'])
    # Small side-wall plaque, completely away from the projection rectangle.
    box('DINK DONK side wall brass plaque rim',.052,3.48,.115,5.62,278,325,M['aged brass'],.012)
    box('DINK DONK side wall plaque dark center',.115,3.51,.135,5.59,280,323,M['dark plum'],.008)
    text('DINK DONK plaque lettering','DINK DONK',.145,4.55,308,.235,M['cyan neon'])
    text('Side wall Screen 1 lettering','S C R E E N   1',.146,4.55,291,.115,M['warm light'])
    return screen


def aged_copy(source, name, low=.68, high=1.08, scale=4, bump=.002):
    """Keep the saved palette/weave and add world-space mottling and fine grain."""
    ma=M[source].copy(); ma.name=name
    t=ma.node_tree; n=t.nodes; links=t.links
    p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale
    tex.inputs['Detail'].default_value=4; tex.inputs['Roughness'].default_value=.72
    geo=n.new('ShaderNodeNewGeometry'); links.new(geo.outputs['Position'],tex.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.23; ramp.color_ramp.elements[0].color=(low,low,low,1)
    ramp.color_ramp.elements[1].position=.78; ramp.color_ramp.elements[1].color=(high,high,high,1)
    links.new(tex.outputs['Fac'],ramp.inputs[0])
    mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1
    incoming=list(p.inputs['Base Color'].links)
    if incoming: links.new(incoming[0].from_socket,mix.inputs[1])
    else: mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    links.new(ramp.outputs[0],mix.inputs[2]); links.new(mix.outputs[0],p.inputs['Base Color'])
    fine=n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value=160
    fine.inputs['Detail'].default_value=2
    links.new(geo.outputs['Position'],fine.inputs['Vector'])
    b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.24
    b.inputs['Distance'].default_value=bump
    if p.inputs['Normal'].is_linked: links.new(p.inputs['Normal'].links[0].from_socket,b.inputs['Normal'])
    links.new(fine.outputs['Fac'],b.inputs['Height']); links.new(b.outputs[0],p.inputs['Normal'])
    rough=n.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value=.33 if 'brass' in name.lower() else .72
    rough.inputs['To Max'].default_value=.72 if 'brass' in name.lower() else .98
    links.new(tex.outputs['Fac'],rough.inputs['Value']); links.new(rough.outputs[0],p.inputs['Roughness'])
    return ma


def finishes():
    M['aged brass']=aged_copy('warm brass','D2 scuffed, oxidized warm brass',.48,1.04,9,.0014)
    M['scratched brass']=material('D2 bright rubbed brass scratches',(.48,.30,.12),.42,.72)
    M['velvet burgundy']=aged_copy('velvet burgundy','D2 aged burgundy velvet nap',.66,1.12,5,.0025)
    M['faded velvet']=aged_copy('velvet burgundy','D2 sun-faded seat cloth',1.12,1.65,6,.003)
    M['curtain velvet']=aged_copy('velvet burgundy','D2 dusty sun-faded curtain velvet',.82,1.44,2.8,.003)
    M['velvet teal']=aged_copy('velvet teal','D2 lightly stained teal acoustic fabric',.56,1.02,3.5,.002)
    M['dark plum']=aged_copy('dark plum','D2 lightly stained plum acoustic fabric',.64,1.05,4,.002)
    M['wear teal']=material('D2 flattened, dirty teal carpet traffic path',(.043,.072,.069),.97)
    M['wear plum']=material('D2 exposed tired aubergine carpet pile',(.064,.035,.067),.98)
    M['gaffer']=material('D2 frayed grey gaffer tape',(.17,.16,.14),.94)
    M['ceiling']=material('D2 charcoal acoustic ceiling clouds',(.018,.022,.026),.95)
    M['ceiling edge']=material('D2 painted ceiling truss and cornice recess',(.047,.042,.047),.74,.15)
    M['popcorn']=material('D2 buttered popcorn irregular kernels',(.64,.48,.24),.91)
    M['popcorn pale']=material('D2 popcorn pale broken edges',(.82,.73,.47),.96)
    M['cup cream']=material('D2 used wax paper cups cream',(.49,.42,.31),.8)
    M['cup red']=material('D2 faded burgundy concession cup stripe',(.28,.027,.035),.84)
    M['box card']=material('D2 crumpled popcorn carton inner card',(.37,.28,.17),.96)
    M['coffee stain']=material('D2 old dark sticky carpet mark',(.024,.018,.017),.68)
    # Copy all further wear materials so the source palette stays untouched.
    for key in ['wear teal','wear plum','gaffer','ceiling','cup cream','cup red','box card']:
        M[key]=aged_copy(key,'D2 grain - '+key,.77,1.15,12,.002)


def worn_patch(name,u0,v0,u1,v1,z,ma):
    # Irregular real geometry, a few mm above the existing carpet weave.
    count=16; verts=[]
    for i in range(count+1):
        v=v0+(v1-v0)*i/count
        verts.append(xyz(u0+RNG.uniform(-.035,.035),v,z))
    for i in range(count,-1,-1):
        v=v0+(v1-v0)*i/count
        verts.append(xyz(u1+RNG.uniform(-.035,.035),v,z))
    return mesh(name,verts,[tuple(range(len(verts)))],ma)


def floor_and_steps():
    collection('01 Cutaway floor and ten stadium tiers')
    box('Front slab exposed at cut',0,0,U1,ROW_LO,-17,-.1,M['concrete'])
    box('Front cross aisle midnight carpet',0,0,U1,ROW_LO,-.1,0,M['carpet midnight'],.002)
    flecks(.12,1.06,U1-.10,ROW_LO-.05,.045,24)
    worn_patch('Worn side aisle entrance track',.52,1.5,1.27,ROW_LO,.07,M['wear teal'])
    worn_patch('Cross aisle flattened main traffic band',1.63,1.40,U1-.1,1.97,.075,M['wear teal'])
    # Faint narrow dragged/scuffed areas break up the main wear band.
    for j in range(28):
        u=RNG.uniform(2,U1-.2); v=RNG.uniform(1.42,1.96)
        line('Cross aisle irregular shoe scuff',[(u,v,.095),(u+.08,v+.10,.095)],M['wear plum'],.008)
    for i,row in enumerate(ROWS):
        lo=ROW_LO+i*ROW_PITCH; hi=lo+ROW_PITCH; z=row['floor_zpx']
        box('Tier '+row['row']+' exposed structural cut',1.60,lo,U1,hi,z-17,z-.15,M['concrete'])
        box('Tier '+row['row']+' purple carpet',1.60,lo,U1,hi,z-.15,z,M['carpet aubergine'],.002)
        flecks(1.72,lo+.035,U1-.12,hi-.035,z+.045,23)
        worn_patch('Tier '+row['row']+' flattened row-entry carpet',1.70,lo+.08,3.02,lo+.32,z+.07,M['wear plum'])
        if i:
            box('Tier '+row['row']+' vertical riser',1.60,lo,U1,lo+.035,z-RISE,z-.3,M['dark plum'],.003)
            line('Tier brass nosing',[(1.65,lo+.045,z+.2),(U1-.04,lo+.045,z+.2)],M['aged brass'],.006)
        steps=[(lo,hi,z)] if i==0 else [(lo,lo+ROW_PITCH/2,z-RISE/2),(lo+ROW_PITCH/2,hi,z)]
        for a,b,h in steps:
            box('Side aisle structural half-step',0,a,1.60,b,h-18,h-.1,M['concrete'])
            box('Teal side aisle carpet tread',.03,a,1.59,b,h-.1,h+.03,M['carpet inset'],.003)
            if i: box('Eleven pixel aisle riser',.02,a,1.60,a+.035,h-11,h,M['dark plum'],.002)
            worn_patch('Flattened side aisle carpet footfall',.55,a+.055,1.21,b-.02,h+.075,M['wear teal'])
            line('Scuffed brass tread edge',[(.10,a+.045,h+.2),(1.52,a+.045,h+.2)],M['aged brass'],.007)
    # Shallow apron; cross aisle starts beyond v=1.05 and remains clear.
    box('Narrow stage dark apron',1.30,.12,U1-.06,.92,0,27,M['dark plum'],.025)
    box('Narrow stage midnight top',1.30,.12,U1-.06,.92,27,28,M['carpet midnight'],.008)
    box('Stage worn footlight lip',1.30,.90,U1-.06,.98,20,29,M['black enamel'],.009)
    line('Stage apron rubbed brass lip',[(1.35,.98,28.4),(U1-.1,.98,28.4)],M['aged brass'],.010)
    for u in [1.54+j*1.18 for j in range(16)]:
        box('Recessed amber footlight in stage lip',u,.982,u+.13,.992,23.1,25.8,M['amber'],.003)


def curtain(u0,u1):
    verts=[]; faces=[]; count=128
    for i in range(count+1):
        f=i/count; u=u0+(u1-u0)*f; v=.19+.095*math.cos(f*math.tau*7)
        for z in [31+math.sin(f*17)*.8,SZ1+15]: verts.append(xyz(u,v,z))
    for i in range(count): faces.append((2*i,2*i+1,2*i+3,2*i+2))
    ob=mesh('Dusty open red velvet pleats',verts,faces,M['curtain velvet'])
    for p in ob.data.polygons:p.use_smooth=True
    mod=ob.modifiers.new('Real velvet thickness','SOLIDIFY');mod.thickness=.018
    line('Dusty curtain lower hem',[(u0+(u1-u0)*i/count,.19+.095*math.cos(i/count*math.tau*7),32+math.sin(i/count*17)*.8) for i in range(count+1)],M['curtain velvet'],.016)
    # Local lighter vertical bands read as sun fade, outside the screen quad.
    for f in [.18,.55,.83]:
        u=u0+(u1-u0)*f; v=.19+.095*math.cos(f*math.tau*7)
        line('Curtain raised dusty fold',[(u,v+.012,48),(u+.007,v+.015,SZ1+5)],M['faded velvet'],.009)


def front_and_ceiling():
    collection('07 Picture palace proscenium and cutaway ceiling')
    # A high ceiling ribbon is cut away beyond v=3.1; all its geometry projects
    # ABOVE the screen. Two retained walls have a tiered, brass-trimmed cornice.
    for z,depth,height,ma in [(915,.14,7,'dark plum'),(928,.23,5,'velvet teal'),(937,.31,4,'aged brass'),(943,.38,5,'ceiling edge')]:
        box('Screen-wall stepped picture-palace cornice',0,-.12,U1,depth,z,z+height,M[ma],.008)
        box('Side-wall stepped picture-palace cornice',-.05,0,depth,V1,z,z+height,M[ma],.008)
    for u0,u1 in [(1.00,1.57),(18.79,19.40)]:
        box('Fluted proscenium pillar',u0,.04,u1,.15,30,910,M['dark plum'],.024)
        for k in range(5):
            u=u0+.065+k*(u1-u0-.13)/4
            line('Proscenium rubbed brass flute',[(u,.165,42),(u,.165,897)],M['aged brass'],.011)
        box('Proscenium pillar plinth',u0-.08,.04,u1+.08,.28,28,49,M['black enamel'],.015)
        box('Proscenium pillar capital',u0-.10,.04,u1+.10,.30,899,915,M['aged brass'],.012)
    # Speakers and their real circular cones stay outside the quad's x extent.
    for u in [2.10,18.10]:
        box('Proscenium speaker stack enamel shell',u,.17,u+.63,.64,28,246,M['black enamel'],.035)
        box('Speaker stack cloth grille',u+.025,.648,u+.605,.660,35,238,M['mask'],.012)
        for z in [69,128,193]:
            cylinder('Speaker circular driver',u+.315,.667,z,.205,.016,M['ceiling edge'],axis=(0,-1,0),count=32)
            cylinder('Speaker driver dust cap',u+.315,.680,z,.075,.016,M['mask'],axis=(0,-1,0),count=24)
        for z in [41,230]:box('Speaker brass corner protector',u+.025,.669,u+.11,.683,z,z+4,M['aged brass'],.002)
    # Cloud panels and exposed truss stay in the upper cutaway band; no beam.
    for u in [1.15+j*1.35 for j in range(14)]:
        box('Dark suspended acoustic ceiling cloud',u,.43,u+1.12,2.95,933,940,M['ceiling'],.025)
        for v in [.50,2.85]:
            line('Cloud suspension cable',[(u+.14,v,940),(u+.14,v,945)],M['black enamel'],.006)
    for v in [.18,3.09]:
        for z in [914,930]:
            line('Exposed dark ceiling truss chord',[(.35,v,z),(U1-.10,v,z)],M['ceiling edge'],.022)
        for j in range(25):
            u=.35+j*.78
            line('Ceiling truss diagonal brace',[(u,v,914),(u+.76,v,930)],M['ceiling edge'],.010)
    # Small overhead service lamps provide visible ceiling scale, softly lit.
    for u in [4.0,8.3,12.6,16.9]:
        cylinder('Ceiling warm downlight black bezel',u,1.65,931,.13,.045,M['black enamel'],count=24)
        cylinder('Ceiling small opal lens',u,1.65,929,.10,.015,M['warm light'],count=24)


def back_label(body,u,v,z):
    data=bpy.data.curves.new('Seat identifier '+body,'FONT')
    data.body=body;data.align_x='CENTER';data.align_y='CENTER';data.size=.045
    data.extrude=.0003
    ob=register(bpy.data.objects.new('Engraved seat '+body,data))
    ob.location=xyz(u,v,z);ob.rotation_euler=(math.pi/2,0,0)
    data.materials.append(M['mask']);return ob


def tape_patch(name,u,v,z):
    verts=[xyz(u-.16,v,z-5),xyz(u+.17,v,z-2),xyz(u+.15,v,z+4),xyz(u-.17,v,z+1)]
    return mesh(name,verts,[(0,1,2,3)],M['gaffer'])


def seats():
    for row in ROWS:
        collection('03 Row '+row['row']+' seats')
        v=row['v'];z=row['floor_zpx'];backs=[]
        for j,u in enumerate(SEATS):
            tag='%s%02d'%(row['row'],j+1);prefix='Seat '+tag
            cloth=M['faded velvet' if tag in LIVED_IN['faded_seats'] else 'velvet burgundy']
            box(prefix+' floor pedestal',u-.14,v-.13,u+.14,v+.18,z+.4,z+4,M['black enamel'],.02)
            for du in [-.22,.22]:
                box(prefix+' steel support',u+du-.03,v+.06,u+du+.03,v+.18,z+3,z+31,M['black enamel'],.01)
                cylinder(prefix+' worn brass flip hinge',u+du,v+.10,z+22,.055,.025,M['aged brass'],axis=(1,0,0),count=16)
            cushion=[box(prefix+' flip seat shell',u-.325,v-.36,u+.325,v+.13,z+14,z+18,M['black enamel'],.035),
                box(prefix+' upholstered cushion',u-.305,v-.35,u+.305,v+.12,z+17,z+22,cloth,.030)]
            if tag==LIVED_IN['half_folded_seat']:
                pivot=xyz(u,v+.1,z+18)
                rotation=Matrix.Rotation(math.radians(52),3,'X')
                for ob in cushion:
                    for vertex in ob.data.vertices:vertex.co=pivot+rotation@(vertex.co-pivot)
                    ob['stuck_half_folded']=True
                row['seat_exceptions']=[{'seat':tag,'u':u,'state':'stuck half folded, 52 degrees','available_for_chatter':False}]
            backs.append(box(prefix+' back shell',u-.348,v+.18,u+.348,v+.34,z+17,z+62,M['black enamel'],.055))
            backs.append(box(prefix+' red velvet back',u-.324,v+.157,u+.324,v+.355,z+24,z+61,cloth,.060))
            for du in [-.258,.258]:
                backs.append(line(prefix+' rear tailored piping',[(u+du,v+.361,z+28),(u+du,v+.361,z+53),(u+du*.83,v+.361,z+57)],M['dark plum'],.004))
            backs.append(box(prefix+' rubbed brass number plate',u-.088,v+.36,u+.088,v+.37,z+43,z+48,M['aged brass'],.003))
            backs.append(back_label(tag,u,v+.374,z+45.4))
            if tag in LIVED_IN['patched_seats']:
                backs.append(tape_patch(prefix+' gaffer tape repair',u,v+.374,z+34))
                for k in range(5):
                    backs.append(line(prefix+' tape frayed edge',[(u-.15+k*.065,v+.376,z+35.2),(u-.15+k*.065,v+.376,z+36.2)],M['gaffer'],.002))
        for j in range(len(SEATS)+1):
            u=SEATS[0]-.44+j*.88
            box('Row '+row['row']+' shared armrest stem',u-.027,v-.07,u+.027,v+.15,z+5,z+34,M['black enamel'],.008)
            box('Row '+row['row']+' padded armrest',u-.065,v-.30,u+.065,v+.26,z+32,z+36,M['black enamel'],.025)
            cylinder('Cupholder dark inner well',u,v-.18,z+36,.057,.012,M['mask'],count=24)
            line('Cupholder rubbed brass rim',[(u+.063*math.cos(k*math.tau/32),v-.18+.063*math.sin(k*math.tau/32),z+36.5) for k in range(32)],M['aged brass'],.007,True)
        ob=join(backs,row['seat_back_object'])
        ob['row_id']=row['row'];ob['future_occluder']=True
        ob['facing']='toward v=0; backs on positive-v side'


def point_lamp(name,point,power,color,radius):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    ob=register(bpy.data.objects.new(name,data));ob.location=xyz(*point)
    ob['switch_group']=COLLECTION.name;ob['lighting_state']='house_up'
    return ob


def fixtures_and_lighting():
    collection('04 HOUSE sconces - switchable')
    for v in [1.00,3.15,5.83,8.15,10.55,12.85]:
        # Raise the fixtures with the stadium, preserving readable light pools.
        i=max(0,min(9,round((v-3.12)/ROW_PITCH)))
        z=215+i*RISE
        box('Scuffed sconce brass backplate',.035,v-.11,.10,v+.11,z-16,z+17,M['aged brass'],.015)
        box('Warm opal sconce diffuser',.10,v-.075,.19,v+.075,z-12,z+13,M['warm light'],.022)
        for zz in [z-13,z+14]:box('Sconce aged brass cap',.095,v-.09,.20,v+.09,zz,zz+2,M['aged brass'],.006)
        point_lamp('HOUSE warm sconce local pool',(.29,v,z),30,(1,.48,.20),.14)
    collection('05 HOUSE ceiling pools - switchable')
    for u,v,power in [(4,3.4,310),(11,3.3,345),(18,3.3,300),
                       (4.4,7.7,265),(11.5,8,290),(18.2,8.2,250),
                       (6,12,220),(15.1,12,245)]:
        # Smaller sources and wider spacing give a moodier, less even house-up state.
        light('HOUSE warm overhead pool',(u,v,625),(u,v,70),power,(1,.67,.40),1.55,1.30)
    light('HOUSE low stage wash',(10,1.4,635),(10,0,335),110,(1,.80,.60),7,1.1)
    light('HOUSE high ceiling cornice bounce',(9,1.2,875),(11,1,945),190,(1,.66,.40),5,1.8)
    collection('06 AISLE safety lamps and handrail - switchable')
    rail=[]
    for i,row in enumerate(ROWS):
        v=row['v']-.25;z=row['floor_zpx'];rail.append((.28,v,z+61))
        line('Side aisle aged brass rail post',[(.28,v,z),(.28,v,z+61)],M['aged brass'],.015)
        cylinder('Side aisle rail foot',.28,v,z+1,.065,.028,M['aged brass'])
        lo=ROW_LO+i*ROW_PITCH
        steps=[(lo,z)] if not i else [(lo,z-11),(lo+ROW_PITCH/2,z)]
        for a,h in steps:
            box('Amber half-step edge lamp',.045,a+.13,.082,a+.35,h+8,h+12,M['amber'],.008)
            light('AISLE amber half-step pool',(.10,a+.24,h+12),(1.32,a+.35,h),2.0,(1,.32,.065),.19,.08)
        # Individual tiny rubs remain sharp when the world is magnified.
        for k in range(6):
            vv=v+RNG.uniform(-.14,.14)
            line('Handrail exposed rubbed brass scratch',[(.298,vv,z+61.4),(.302,vv+.045,z+61.65)],M['scratched brass'],.0022)
    line('Continuous scuffed brass side handrail',rail,M['aged brass'],.024)


def cup(u,v,z,tilt=False):
    # Open tapered paper shell, thick rim and two faded red bands.
    count=32;verts=[]
    for zz,r in [(0,.071),(13,.108),(13,.098),(1,.064)]:
        verts.extend(xyz(u+r*math.cos(k*math.tau/count),v+r*math.sin(k*math.tau/count),z+zz) for k in range(count))
    faces=[]
    for ring in range(3):
        for k in range(count):faces.append((ring*count+k,ring*count+(k+1)%count,(ring+1)*count+(k+1)%count,(ring+1)*count+k))
    faces.append(tuple(range(3*count,4*count)))
    ob=mesh('Discarded open wax-paper soda cup',verts,faces,M['cup cream'])
    stripes=[]
    for zz,r in [(3,.080),(8,.095)]:
        stripes.append(line('Faded red cup stripe',[(u+r*math.cos(k*math.tau/40),v+r*math.sin(k*math.tau/40),z+zz) for k in range(40)],M['cup red'],.010,True))
    stripes.append(line('Rolled paper cup lip',[(u+.109*math.cos(k*math.tau/40),v+.109*math.sin(k*math.tau/40),z+13) for k in range(40)],M['cup cream'],.009,True))
    if tilt:
        pivot=xyz(u,v,z);rot=Matrix.Rotation(math.radians(76),3,'X')
        ob.data.transform(Matrix.Translation(pivot)@rot.to_4x4()@Matrix.Translation(-pivot))
        for curve in stripes:
            for spline in curve.data.splines:
                for p in spline.points:p.co=(*(pivot+rot@(Vector(p.co[:3])-pivot)),1)
        # Lift the tipped rim just clear of the floor.
        for item in [ob]+stripes:item.location.z+=.065
    LIVED_IN['cups']+=1


def carton(u,v,z):
    # Open, slightly crushed carton with an off-centre flap.
    verts=[xyz(u+du,v+dv,z+h) for du,dv,h in
        [(-.10,-.10,0),(.10,-.10,0),(.10,.10,0),(-.10,.10,0),
         (-.15,-.14,12),(.13,-.14,12),(.14,.14,11),(-.14,.15,10)]]
    mesh('Crushed open popcorn carton',verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],M['cup red'])
    mesh('Carton folded cream inner flap',[verts[4],verts[5],xyz(u+.10,v-.05,z+8),xyz(u-.10,v-.05,z+8)],[(0,1,2,3)],M['box card'])
    for d in [-.075,0,.075]:line('Popcorn carton cream stripe',[(u+d,v+.146,z+3),(u+d,v+.15,z+9)],M['cup cream'],.010)
    LIVED_IN['boxes']+=1


def litter():
    collection('08 Lived-in cinema crumbs and concession litter')
    # Batch low-poly irregular kernels so their silhouette survives 4K/zoom.
    verts=[];faces=[];mats=[]
    clusters=[(3.05,2.69,0),(6.9,3.40,0),(3.1,4.40,22),(8.2,5.43,44),
              (4.1,6.54,66),(10.7,7.63,88),(3.0,8.68,110),(7.2,9.77,132),
              (12.5,10.84,154),(4.5,11.95,176),(15.1,12.99,198)]
    for cu,cv,cz in clusters:
        for _ in range(RNG.randrange(10,19)):
            u=cu+RNG.uniform(-.30,.30);v=cv+RNG.uniform(-.14,.14)
            # All debris is under seats or at their front edge, outside aisle centre.
            z=cz+RNG.uniform(.45,1.1);r=RNG.uniform(.018,.031)
            c=xyz(u,v,z);k=len(verts)
            verts.extend([c+Vector((r,0,0)),c+Vector((0,r*.85,0)),c+Vector((-r*.9,0,0)),
                          c+Vector((0,-r,0)),c+Vector((.004,0,r*1.15)),c+Vector((0,0,-r*.35))])
            for f in [(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]:
                faces.append(tuple(k+i for i in f));mats.append(RNG.randrange(2))
            LIVED_IN['popcorn_pieces']+=1
    ob=mesh('Scattered irregular buttered popcorn kernels',verts,faces,M['popcorn'])
    ob.data.materials.append(M['popcorn pale'])
    for p,m in zip(ob.data.polygons,mats):p.material_index=m
    for u,v,z,tipped in [(3.0,2.75,.5,True),(5.4,4.35,22.5,False),(9.7,6.83,66.5,True),
                          (2.95,9.13,132.5,False),(14.3,11.28,176.5,True)]:cup(u,v,z,tipped)
    for u,v,z in [(4.0,3.40,.5),(7.5,6.64,66.5),(3.3,11.34,176.5)]:carton(u,v,z)
    for u,v,z in [(3.1,2.75,.09),(5.4,4.35,22.09),(9.7,6.83,66.09)]:
        mesh('Old small spilled drink carpet stain',[xyz(u+.19*math.cos(k*math.tau/15),v+.11*math.sin(k*math.tau/15),z) for k in range(15)],[tuple(range(15))],M['coffee stain'])


def audience_check():
    results=[]
    # roxy.html:198 EH=50 and :844 MAXW=74, fit both maximums.
    # A 50x74 envelope is conservative for every actual emote aspect ratio.
    for row in ROWS:
        for u in SEATS:
            head=project(u,row['v'],row['floor_zpx']+22+50)
            right=head[0]+37
            edge=OY+.5*(right-OX)-SZ0
            clearance=head[1]-edge
            assert clearance>1
            tag='%s%02d'%(row['row'],SEATS.index(u)+1)
            x0=max(head[0]-37,project(SU0,0,0)[0])
            x1=min(head[0]+37,project(SU1,0,0)[0])
            results.append({'seat':tag,'row':row['row'],'u':u,'head_top_px':head,
                'screen_bottom_at_sprite_right_x_px':edge,'clearance_px':clearance,
                'overlaps_screen_x_range':x0<x1,
                'available_for_chatter':tag!=LIVED_IN['half_folded_seat']})
    # Same-room backrest top is lower on the image than the head by 21.65px.
    # At sprite centre the back's front edge adds 4.71px perspective offset;
    # cushion+50=72 vs rear back top+61 => 11+10.65=21.65.
    return {'emote_height_px':50,'emote_max_width_px':74,
        'page_source':{'file':'roxy.html','height_line':198,'width_line':844,
            'fit':'height=min(50,74*naturalHeight/naturalWidth); bottom anchored'},
        'anchor':'bottom centre on tier floor_zpx+22px cushion',
        'formula':'clearance=60*v+145-floor_zpx-22-50-18.5',
        'minimum_clearance_px':min(r['clearance_px'] for r in results),
        'row_minimum_clearance_px':{row['row']:min(r['clearance_px'] for r in results if r['row']==row['row']) for row in ROWS},
        'head_visible_above_rear_backrest_px':21.65,
        'backrest_coverage':'Back top at v+0.355, tier+61; centre of the 50px head envelope is 21.65px above that rear edge. Separate row back meshes cover the lower body in future DOM composition.',
        'passed_all_200_seats':True,'seats_checked':200,
        'half_folded_seat_unavailable':'C02 is excluded from seating paths; conservative standard-cushion envelope also checked there.',
        'seats':results}


def preservation_snapshot():
    """Read-only inventory. No baseline file or originals are written."""
    # Hash original blends, draft-1 deliverables/source, and all HTML pages.
    strong=set(ROOT.glob('*.blend'))|set(ROOT.glob('*.blend1'))
    strong.update([ROOT/'build_cinema_draft1.py',QA/'CINEMA-DRAFT-01.md',
                   QA/'cinema_layout_01.json',QA/'cinema_draft_01.png'])
    strong.update(p for p in ROOT.parent.rglob('*.html') if 'tools' not in p.relative_to(ROOT.parent).parts)
    strong.discard(TARGET)
    hashes={str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(strong) if p.is_file()}
    # Tree size and timestamp inventory covers bundled assets and out10 without
    # touching them or spending time decoding the many animation files.
    tree={}
    for directory in [ROOT/'cloud'/'bundle',ROOT/'out10']:
        for p in directory.rglob('*'):
            if p.is_file():
                s=p.stat();tree[str(p.relative_to(ROOT.parent))]=[s.st_size,s.st_mtime_ns]
    return {'sha256':hashes,'asset_tree':tree}


def layout(sc,cal,visibility,audience,preservation):
    corners=[project(SU0,0,SZ1),project(SU1,0,SZ1),project(SU1,0,SZ0),project(SU0,0,SZ0)]
    path=[[.12,2.18,0],[.80,2.18,0],[.80,ROW_LO+.10,0]]
    for i,row in enumerate(ROWS):
        lo=ROW_LO+i*ROW_PITCH;z=row['floor_zpx']
        if i:path.append([.80,lo+.10,z-11])
        path.append([.80,row['v'],z])
    path.append([.80,V1-.10,198])
    counts={'sha256_files':len(preservation['sha256']),'bundle_and_out10_files':len(preservation['asset_tree'])}
    return {'brief':'BRIEF-29-cinema-draft2.md','inherits':'BRIEF-28-cinema-draft1.md',
        'scene':'DINK DONK Screen 1 / auditorium / cinema draft 2',
        'image':IMAGE.name,'resolution':[W,H],
        'coordinates':{'world':'(x,y,z)=(u,-v,zpx/73.48469228349535)',
            'projection':'[Ox+60*(u-v),Oy+30*(u+v)-zpx]','Ox':OX,'Oy':OY,'ZPP':ZPP,
            'pixel_origin':'top left; continuous corner coordinates; 4K scales all image coordinates by 2'},
        'camera':{'type':'ORTHO','rotation_degrees':[60,0,45],'ortho_scale':22.627416998},
        'calibration':cal,
        'screen':{'wall':'v=0','u_range':[SU0,SU1],'v':0,'zpx_range':[SZ0,SZ1],
            'corners_1920x1080':dict(zip(['TL','TR','BR','BL'],corners)),
            'corners_3840x2160':dict(zip(['TL','TR','BR','BL'],[[2*x,2*y] for x,y in corners])),
            'on_frame_bbox_width_px':(SU1-SU0)*60,'visibility_check':visibility,
            'matte':True,'emission':0,'on_frame':all(0<x<W and 0<y<H for x,y in corners)},
        'room':{'u_range':[0,U1],'v_range':[0,V1],'wall_top_zpx':WALL_Z,
            'kept_walls':['u=0','v=0'],'cut_edges':['u=20.1','v=13.38'],
            'ceiling':'Stepped plum/teal/brass cornice, dark clouds at zpx=933-940, two open trusses; ceiling cut away beyond v=3.1.',
            'stage':{'u_range':[1.30,U1-.06],'v_range':[.12,.98],'top_zpx':28,'footlight_lip_top_zpx':29},
            'front_cross_aisle':{'u_range':[.15,U1-.06],'v_range':[1.05,ROW_LO],'floor_zpx':0,
                'walk_path_uvzpx':[[.8,2.18,0],[1.65,2.05,0],[U1-.20,2.05,0]],
                'minimum_v_width_tiles':ROW_LO-1.05}},
        'seat_count':200,'usable_seat_count':199,'rows':ROWS,'seat_pitch_u':.88,'row_pitch_v':ROW_PITCH,
        'entrance':{'wall':'u=0','u':0,'v_range':[1.48,2.88],'floor_zpx':0,
            'height_zpx':115,'height_bu':115/ZPP,'leaf_height_zpx':110,'EXIT_center_uvz':[.179,2.18,137]},
        'side_aisle':{'u_range':[.03,1.59],'path_uvzpx':path,'maximum_step_rise_zpx':11,
            'handrail_u':.28,'handrail_height_above_tier_zpx':61,
            'row_entry_points_uvzpx':[[1.61,r['v'],r['floor_zpx']] for r in ROWS],
            'unavailable_seats':['C02']},
        'audience_clearance':audience,'lived_in_details':LIVED_IN,
        'source_materials':{'blend':SOURCE.name,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'appended_datablocks':REUSED,'adaptations':['Saved dry carpet networks restored on copies.',
                'Copied fabric/brass networks gain world-space mottling, grain, dust, stains and variable roughness.']},
        'lighting':{'state':'house_up','switchable_collections':['04 HOUSE sconces - switchable',
            '05 HOUSE ceiling pools - switchable','06 AISLE safety lamps and handrail - switchable'],
            'screen_emission':0,'glare':False,'fog':False,'projection_beam':False},
        'zoom_headroom':{'page_zoom_max':1.85,'final_resolution_target':[3840,2160],
            'draft_only_resolution':[1920,1080],
            'detail_strategy':'Real seams, cupholder wells, seat numbers, tape, paper rims, grain and scuffs; procedural world-space microtextures and curved silhouettes. No pixel textures or baked 1080p artwork.',
            'limit':'Only this 1080p still is rendered. 4K and live 1.85x page zoom are not rendered or integrated in this draft.'},
        'preservation':{'method':'SHA-256 of original blends, draft-1 source/deliverables and HTML pages; size/mtime inventory of cloud/bundle and out10. Compared before/after the build.',
            **counts,'source_sha256':preservation['sha256'][str(SOURCE.relative_to(ROOT.parent))],
            'passed':None},
        'render':{'engine':'Cycles','max_samples':384,'adaptive_min_samples':64,'adaptive_threshold':.007,
            'denoise':True,'device':sc['render_device'],'exposure':.10,'view':'AgX / Medium High Contrast'},
        'scope':'One image; all outputs and runtime isolated to new paths in roxy3d; no page, bundle, out10 or prior blend updates.'}


def report(data):
    cal=data['calibration'];r=data['render'];screen=data['screen'];aud=data['audience_clearance']
    lines=['# Cinema draft 02 - DINK DONK Screen 1','',
        'One 1920x1080 house-lights-up still. Ten stadium rows of twenty red velvet flip seats (200 total; '
        'C02 is stuck half-folded, leaving 199 usable). Larger picture-palace room, tall retained walls, '
        'stepped brass/plum/teal cornice, dark acoustic ceiling clouds and exposed truss. '
        'The room fills the frame by cropping seating and slab at the left, right and bottom; the entire screen stays on frame.','',
        f'Projection: `Ox={OX:g}, Oy={OY:g}`; `P=[700+60(u-v),635+30(u+v)-zpx]`. '
        'Camera rotation `(60,0,45)` degrees, orthographic scale `22.627416998`, '
        f'`ZPP={ZPP}`; unchanged from draft 1 except the permitted origin move.','',
        'Five-marker camera-matrix calibration, against the independent page formula (no extra calibration image):','',
        '| Marker (u,v,zpx) | x error px | y error px |','|---|---:|---:|']
    for p in cal['points']:lines.append(f"| {tuple(p['uvz'])} | {p['error_px'][0]:.7f} | {p['error_px'][1]:.7f} |")
    lines.extend(['',f"Maximum axis error {cal['max_axis_error_px']:.7f}px; nearest pixel-centre error "
        f"{cal['max_pixel_center_error_px']:.4f}px. PASS +/-1px. Same analytic marker check as cinema draft 1; "
        'not a second raster-centroid render.','',
        f'Screen: physical 16:9 on `v=0`, `u=[{SU0:g},{SU1:g}]`, '
        f'`zpx=[{SZ0:.6f},{SZ1:.6f}]`; {screen["on_frame_bbox_width_px"]:.0f}px projected width '
        '(draft 1: 552px). Matte grey fabric, zero emission, no artwork; all curtains, speakers, '
        'pillars, ceiling, rails and sconces remain outside its four-corner quad.','',
        '| Corner | 1920x1080 (x,y) | 3840x2160 (x,y) |','|---|---|---|'])
    for key in ['TL','TR','BR','BL']:
        c=screen['corners_1920x1080'][key];d=screen['corners_3840x2160'][key]
        lines.append(f'| {key} | ({c[0]:.6f}, {c[1]:.6f}) | ({d[0]:.6f}, {d[1]:.6f}) |')
    lines.extend(['',f"Screen visibility: {screen['visibility_check']['rays']:,} orthographic rays against evaluated "
        'geometry, covering every inner image pixel centre and a subpixel-inset perimeter. Zero blocked. '
        'No haze, fog, beam, glare or compositing crosses the screen.','',
        f'Room footprint: `u=[0,{U1:g}], v=[0,{V1:g}]`; retained walls `u=0, v=0`, top `{WALL_Z:g}zpx`. '
        'Stage is shallow (`v=0.12-0.98`, top 28zpx) with a recessed footlight lip; '
        f'front cross-aisle `v=1.05-{ROW_LO:g}` is {ROW_LO-1.05:.2f} tiles deep and remains walkable. '
        'Speaker stacks and fluted proscenium pillars flank the screen outside the quad.','',
        '| Row | Seat-line v | Tier floor zpx | Seat centre u positions |','|---|---:|---:|---|'])
    for row in ROWS:lines.append(f"| {row['row']} | {row['v']:.2f} | {row['floor_zpx']:.0f} | "+', '.join(f'{u:.2f}' for u in SEATS)+' |')
    lines.extend(['',
        'Entrance: padded double door in a real opening on `u=0`, `v=[1.48,2.88]`, floor 0zpx, '
        f'height 115zpx ({115/ZPP:.4f} BU), leaves 110zpx, EXIT centre `(0.179,2.18,137)`. '
        'Side aisle is `u=0.03-1.59`, centreline `u=0.80`, handrail at `u=0.28` and tier+61zpx. '
        'Each 22zpx tier rise has two lit 11zpx half-steps. Door, cross-aisle, side-aisle and every row entry '
        'have world-coordinate paths in `cinema_layout_02.json`; C02 is marked unavailable.','',
        'Audience clearance uses the real page limits: `roxy.html:198` has `EH=50`; '
        '`roxy.html:844` has `MAXW=74`, and the following lines fit both limits. '
        'A conservative 50px tall x 74px wide rectangle is bottom-anchored at `tier+22zpx`. '
        'For its rightmost x (where the screen bottom is lowest), '
        '`clearance=60*v+145-floor_zpx-22-50-18.5`. '
        f"All 200 standard seat envelopes pass; minimum {aud['minimum_clearance_px']:.2f}px. "
        'Per-row minima: '+', '.join(f'{k}={v:.2f}px' for k,v in aud['row_minimum_clearance_px'].items())+'. '
        'The image head top is 21.65px above the rear backrest top at the centre. '
        'Every row has its own joined seat-back mesh, including upholstery, seams, number plates and tape, '
        'for future occlusion. No DOM audience or page integration is produced in this draft.','',
        f"Wear and litter: {LIVED_IN['popcorn_pieces']} irregular popcorn kernels, {LIVED_IN['cups']} discarded open/tipped "
        f"paper cups, {LIVED_IN['boxes']} open crushed cartons and a few old drink stains under seats. "
        'Flattened irregular carpet tracks run along the entrance, both half-steps and cross-aisle. '
        'B03/D08/F05/H12 have frayed gaffer repairs; A09/C04/E10/G06/I13 are faded; C02 is raised 52 degrees. '
        'Dusty sun-faded curtain folds, lightly mottled acoustic fabric and scratched/oxidized brass share the '
        'approved lobby palette. Sconces cast warmer local pools with darker gaps; ceiling light spacing is less even. '
        'House sconces, overhead pools and aisle lamps are in separate switchable collections.','',
        'Zoom headroom: procedural world-space cloth/metal grain, real piping, tape, engraved seat IDs, '
        'cupholder wells, curved cup rims, paper flaps and scuffs avoid 1080p texture limits. '
        'The draft is rendered only at 1080p; final 4K and live 1.85x zoom remain future owner-reviewed work.','',
        f"Render: Blender {r['blender_version']}; Cycles adaptive 64-384 / 0.007, denoised, {r['device']}; "
        f"{r['seconds']:.2f}s render, {r['build_and_checks_seconds']:.2f}s build/checks, "
        f"{r['total_seconds']:.2f}s total. Exactly one beauty render and one draft-2 PNG. ",
        '',f"Preservation PASS: {data['preservation']['sha256_files']} original blend/draft-1/page files match their "
        f"pre-build SHA-256 hashes; {data['preservation']['bundle_and_out10_files']} existing cloud-bundle/out10 files "
        'match pre-build size/mtime inventory. '
        f"Approved source blend SHA-256: `{data['preservation']['source_sha256']}`. "
        'All explicit writes use new draft-2 paths inside roxy3d. Existing blends, draft-1 outputs, '
        'cloud bundle, out10 and all pages were left untouched.','',
        'Reproduction: `build_cinema_draft2.py` rebuilds deterministically from the read-only draft-13 source palette. '
        'Existing blend/image/report/layout or a started-render marker block another render. '
        '`-- --preflight` checks camera, evaluated geometry, audience clearance and preservation without saving a blend '
        'or rendering. Runtime/GPU caches use new `qa11/runtime02/` paths.','',
        'Draft limits: one house-up image only; no film, audience, dim state, 4K frame, alternate stills, '
        'layers, loops or exports. Stop for owner review.'])
    with REPORT.open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')


def main():
    started=time.perf_counter()
    assert bpy.app.version[:3]==(5,2,3),bpy.app.version_string
    preflight='--preflight' in sys.argv
    if not preflight:
        for p in [IMAGE,TARGET,REPORT,LAYOUT,RUNTIME/'render_started']:
            assert not p.exists(),'Strict draft/new-file stop: existing '+str(p)
    before=preservation_snapshot()
    sc=configure();palette();finishes();floor_and_steps();screen=walls_screen_door()
    front_and_ceiling();seats();fixtures_and_lighting();litter()
    collection('00 Exact page camera and calibration markers')
    cal=calibration(sc);visibility=screen_check(sc,screen);audience=audience_check()
    assert preservation_snapshot()==before,'Protected original changed during build.'
    data=layout(sc,cal,visibility,audience,before)
    assert data['screen']['on_frame']
    occluders=[o for o in sc.objects if o.get('future_occluder')]
    assert len(occluders)==10 and all(o.type=='MESH' for o in occluders)
    print('CINEMA_PREFLIGHT',json.dumps({'origin':[OX,OY],'calibration':cal,
        'screen':data['screen'],'audience_minimum_clearance':audience['minimum_clearance_px'],
        'object_count':len(sc.objects),'row_occluders':len(occluders),'lived_in':LIVED_IN}),flush=True)
    if preflight:
        print('PREFLIGHT PASSED. NO IMAGE RENDERED. NO BLEND SAVED.',flush=True);return
    sc.render.filepath=str(IMAGE)
    sc['screen_quad_1920']=json.dumps(data['screen']['corners_1920x1080'])
    sc['layout_contract']=json.dumps(data)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    with (RUNTIME/'render_started').open('x',encoding='utf-8') as f:f.write('One render authorized by Brief 29. No second render.\n')
    built=time.perf_counter();print('CINEMA_SINGLE_RENDER_START',flush=True)
    bpy.ops.render.render(write_still=True)
    ended=time.perf_counter()
    assert IMAGE.exists()
    assert preservation_snapshot()==before,'Protected original changed during render.'
    data['preservation']['passed']=True
    data['render'].update(seconds=ended-built,build_and_checks_seconds=built-started,
        total_seconds=ended-started,blender_version=bpy.app.version_string)
    with LAYOUT.open('x',encoding='utf-8') as f:f.write(json.dumps(data,indent=2)+'\n')
    report(data)
    print('CINEMA_DRAFT_02_RENDER_COMPLETE',flush=True)


if __name__=='__main__':main()

