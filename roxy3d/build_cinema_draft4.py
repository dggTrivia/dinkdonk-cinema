"""Brief 31: childhood multiplex auditorium; exactly one new draft-4 still.
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
TARGET = ROOT / 'roxy_cinema_draft4.blend'
IMAGE = QA / 'cinema_draft_04.png'
REPORT = QA / 'CINEMA-DRAFT-04.md'
LAYOUT = QA / 'cinema_layout_04.json'
RUNTIME = QA / 'runtime04'
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
ORTHO = 30.0
K = 22.627416998 / ORTHO
OX, OY = 800.0, 548.0
U1, V1 = 17.50, 10.58
WALL_Z = 650.0
SU0, SU1, SZ0 = 3.40, 15.40, 90.0
SZ1 = SZ0 + (SU1 - SU0) * 9 / 16 * ZPP
ROW_LO, ROW_PITCH, RISE = 2.58, .95, 48.0
RIGHT = Vector((2**-.5, 2**-.5, 0))
UP = Vector((-math.sqrt(.125), math.sqrt(.125), math.sqrt(.75)))
NORMAL = RIGHT.cross(UP)
SIDE_ROT = Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
RNG = random.Random(291997)
COLLECTION = None
M, REUSED, ROWS = {}, [], []
SEAT_PITCH = .84
CUSHION_HEIGHT = 36.0
LANE_U = .88
LANDING_Z = 34.0
SEATS = [round(2.60+j*SEAT_PITCH,4) for j in range(18)]
for i,(v,z,lo,hi) in enumerate([(3.08,14,2.58,3.58),(4.08,34,3.58,4.58),
        (5.33,64,4.83,5.805),(6.28,112,5.805,6.755),
        (7.23,160,6.755,7.705),(8.18,208,7.705,8.655),
        (9.13,256,8.655,9.605),(10.08,304,9.605,10.58)]):
    ROWS.append({'row':chr(65+i), 'v':v,
        'floor_zpx':z, 'tier_v_range':[lo,hi],
        'section':'gently raked low front' if i<2 else 'stadium bank',
        'seat_u':SEATS[:] if i<2 else [round(5.12+j*.784+(.14 if i==7 else 0),4) for j in range(0 if i<5 else 1,16)],
        'seat_pitch_u':.84 if i<2 else .784,
        'cushion_zpx_above_floor':CUSHION_HEIGHT, 'back_top_zpx_above_floor':62.0,
        'seat_back_object':'Row %s seat backs - future occluder' % chr(65+i)})
LIVED_IN = {'patched_seats':['H04'],
    'faded_seats':['G13','B06','E15','F08'],
    'half_folded_seat':'C02', 'popcorn_pieces':0, 'cups':0, 'boxes':0}


def xyz(u, v, z=0):
    return Vector((u, -v, z / ZPP))



def project(u, v, z=0):
    return [OX+(u-v)*60*K, OY+((u+v)*30-z)*K]



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






def configure():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.name='DINK DONK Screen 1 - Cinema draft 04 childhood hall'
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
    data.type='ORTHO'; data.ortho_scale=ORTHO
    data.clip_start=.01; data.clip_end=200
    cam=register(bpy.data.objects.new('Cinema exact page camera',data))
    cam.rotation_euler=(math.radians(60),0,math.radians(45))
    cam.location=RIGHT*((960-OX)/(PPU*K))+UP*((OY-540)/(PPU*K))+NORMAL*40
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
    sc['render_device']=device; sc['brief']='BRIEF-31-cinema-draft4.md'
    sc['source_palette']=str(SOURCE); sc['draft_only']=True
    sc['projection_origin_px']=[OX,OY]
    print('CINEMA_DEVICE',device,flush=True)
    return sc



def calibration(sc):
    bpy.context.view_layer.update()
    points=[(0,0,0),(U1,0,0),(0,V1,0),(U1,V1,ROWS[-1]['floor_zpx']),(0,0,WALL_Z)]
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
    global SCENE_BVH, SCENE_OWNERS, SCENE_VERTS
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
    SCENE_BVH, SCENE_OWNERS, SCENE_VERTS = tree, owners, verts
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
        u=(ix+.5-OX)/(60*K)
        top=project(u,0,SZ1)[1]; bottom=project(u,0,SZ0)[1]
        for iy in range(math.ceil(top-.5),math.floor(bottom-.5)+1):
            check(u,u*30+(OY-(iy+.5))/K)
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


def inherited_finishes():
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
    # Worn paths retain the actual carpet network and palette. Broken islands
    # of flattened pile replace draft 2's opaque yellow-green traffic bands.
    M['wear teal']=aged_copy('carpet midnight','D3 flattened midnight carpet pile',.84,1.18,18,.0007)
    M['wear plum']=aged_copy('carpet aubergine','D3 flattened aubergine carpet pile',.83,1.16,16,.0007)


def worn_patch(name,u0,v0,u1,v1,z,ma):
    # Separate, ragged footfalls with carpet-coloured noise, never a solid band.
    verts=[];faces=[]
    for j in range(max(3,int((u1-u0)*(v1-v0)*19))):
        u=RNG.uniform(u0,u1);v=RNG.uniform(v0,v1)
        ru=min((u1-u0)*.34,.15)*RNG.uniform(.65,1.25)
        rv=min((v1-v0)*.28,.16)*RNG.uniform(.65,1.25)
        start=len(verts)
        for i in range(13):
            a=i*math.tau/13;r=RNG.uniform(.72,1.18)
            verts.append(xyz(u+ru*math.cos(a)*r,v+rv*math.sin(a)*r,z))
        faces.append(tuple(range(start,len(verts))))
    return mesh(name,verts,faces,ma)




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




def back_label(body,u,v,z):
    data=bpy.data.curves.new('Seat identifier '+body,'FONT')
    data.body=body;data.align_x='CENTER';data.align_y='CENTER';data.size=.045
    data.extrude=.0003
    ob=register(bpy.data.objects.new('Engraved seat '+body,data))
    ob.location=xyz(u,v,z);ob.rotation_euler=(math.pi/2,0,0)
    data.materials.append(M['mask']);return ob


def tape_patch(name,u,v,z):
    verts=[xyz(u-.27,v,z-6),xyz(u+.27,v,z-2),xyz(u+.24,v,z+6),xyz(u-.28,v,z+2)]
    return mesh(name,verts,[(0,1,2,3)],M['gaffer'])




def point_lamp(name,point,power,color,radius):
    data=bpy.data.lights.new(name,'POINT');data.energy=power;data.color=color;data.shadow_soft_size=radius
    ob=register(bpy.data.objects.new(name,data));ob.location=xyz(*point)
    ob['switch_group']=COLLECTION.name;ob['lighting_state']='house_up'
    return ob




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
    collection('08 Five legible lived-in incidents')
    # One local spill beside the D01 entry, below the head silhouettes.
    row=ROWS[3];cu,cv,cz=row['seat_u'][0]-.60,row['v']-.31,row['floor_zpx']
    stain=[xyz(cu+.27*math.cos(i*math.tau/23)*RNG.uniform(.75,1.1),
               cv+.17*math.sin(i*math.tau/23)*RNG.uniform(.75,1.1),cz+.10) for i in range(23)]
    mesh('D01 aisle-side old soda spill',stain,[tuple(range(23))],M['coffee stain'])
    verts=[];faces=[]
    for i in range(34):
        u=cu+RNG.uniform(-.23,.23);v=cv+RNG.uniform(-.14,.14)
        c=xyz(u,v,cz+1);r=RNG.uniform(.025,.043);k=len(verts)
        verts.extend([c+Vector((r,0,0)),c+Vector((0,r,0)),c+Vector((-r,0,0)),
                      c+Vector((0,-r,0)),c+Vector((0,0,r))])
        faces.extend(tuple(k+j for j in f) for f in [(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
    mesh('D01 single clustered popcorn spill',verts,faces,M['popcorn'])
    LIVED_IN['popcorn_pieces']=34
    cup(cu+.1,cv-.14,cz+.4,True)
    # One conspicuous carton in the cross-aisle, well in front of row A.
    before=set(bpy.context.scene.objects)
    carton(7.1,1.75,.3)
    pivot=xyz(7.1,1.75,.3)
    transform=Matrix.Translation(pivot)@Matrix.Scale(1.8,4)@Matrix.Translation(-pivot)
    for ob in set(bpy.context.scene.objects)-before:
        ob.data.transform(transform)
    LIVED_IN['incidents']=[
        {'name':'broken entrance traffic track','uvzpx':[1.0,2.05,0],
         'detail':'ragged carpet-coloured footfalls, not an opaque band'},
        {'name':'D01 aisle-side soda and popcorn spill','uvzpx':[cu,cv,cz],
         'extent_world':[.54,.34,13],'size_1080p_px_about':[30,17]},
        {'name':'H04 broad frayed gaffer repair','seat':'H04','width_1080p_px':.55*60*K},
        {'name':'G13 faded upholstery patch','seat':'G13','width_1080p_px':.648*60*K},
        {'name':'discarded open popcorn carton','uvzpx':[7.1,1.75,.3],
         'size_1080p_px_about':[24,25]}]


def object_tree(objects):
    deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];owners=[]
    for ob in objects:
        if ob.type not in ['MESH','CURVE','FONT'] or ob.hide_render:continue
        evaluated=ob.evaluated_get(deps);me=evaluated.to_mesh();offset=len(verts)
        verts.extend(evaluated.matrix_world@v.co for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
        owners.extend([ob.name]*len(me.polygons));evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(verts,faces,all_triangles=False),owners


def top_exposure(tree,anchor,dx_worldpx=0,steps=400):
    # A DOM-facing billboard, bottom anchored on the cushion, with the brief's
    # 50*k height. Count the contiguous unobstructed portion down from its top.
    for i in range(steps):
        h=50*(1-(i+.5)/steps)
        p=anchor+RIGHT*(dx_worldpx/PPU)+UP*(h/PPU)
        hit=tree.ray_cast(p+NORMAL*45,-NORMAL,44.9995)
        if hit[2] is not None:return i/steps
    return 1.0




def audience_check():
    results=[];per_row={};face_rows=[]
    for row in ROWS:
        own=bpy.data.objects[row['seat_back_object']]
        own_tree,_=object_tree([own])
        nearer=[bpy.data.objects[r['seat_back_object']] for r in ROWS if r['v']>row['v']]
        nearer_tree,_=object_tree(nearer) if nearer else (None,None)
        own_fracs=[];all_fracs=[];core_fracs=[];nearer_fracs=[]
        for j,u in enumerate(row['seat_u']):
            tag='%s%02d'%(row['row'],j+1)
            head=project(u,row['v'],row['floor_zpx']+CUSHION_HEIGHT+50)
            right=head[0]+37*K
            edge=OY+.5*(right-OX)-SZ0*K
            clearance=head[1]-edge
            assert clearance>1
            anchor=xyz(u,row['v'],row['floor_zpx']+CUSHION_HEIGHT)
            own_frac=top_exposure(own_tree,anchor)
            all_frac=top_exposure(SCENE_BVH,anchor)
            core=min(top_exposure(SCENE_BVH,anchor,x) for x in [-11.1,0,11.1])
            near_frac=top_exposure(nearer_tree,anchor) if nearer_tree else 1.0
            available=tag!=LIVED_IN['half_folded_seat']
            if available:
                own_fracs.append(own_frac);all_fracs.append(all_frac)
                core_fracs.append(core);nearer_fracs.append(near_frac)
            results.append({'seat':tag,'u':u,'row':row['row'],'head_top_px':head,
                'screen_bottom_at_sprite_right_x_px':edge,'clearance_px':clearance,
                'available_for_chatter':available,'own_back_visible_fraction':own_frac,
                'all_geometry_visible_fraction':all_frac,'face_core_visible_fraction':core,
                'nearer_rows_only_visible_fraction':near_frac})
        info={'row':row['row'],'own_back_visible_fraction_min':min(own_fracs),
              'own_back_visible_fraction_max':max(own_fracs),
              'all_geometry_visible_fraction_min':min(all_fracs),
              'face_core_visible_fraction_min':min(core_fracs),
              'nearer_rows_only_visible_fraction_min':min(nearer_fracs),
              'visible_face_height_px_min':min(all_fracs)*50*K}
        face_rows.append(info)
        per_row[row['row']]=min(r['clearance_px'] for r in results if r['row']==row['row'])
    # Emote compositing is intentionally left to the page. This checks the
    # numeric envelope, not an extra image, sprite layer or actual face artwork.
    return {'emote_height_px':50*K,'emote_max_width_px':74*K,
        'unscaled_lobby_emote_height_px':50,'unscaled_lobby_emote_max_width_px':74,
        'anchor':'bottom centre on tier floor_zpx + 36 zpx_world cushion',
        'formula':'clearance=k*(60*v+90-floor_zpx-36-50-18.5)',
        'minimum_clearance_px':min(r['clearance_px'] for r in results),
        'row_minimum_clearance_px':per_row,'seats_checked':len(results),
        'visible_face_method':'400 vertical ray samples from the top of a camera-facing 50k envelope to its cushion plane; central vertical fraction above own back, all geometry, and nearer rows separately. Face core samples x offsets -11.1, 0, +11.1 lobby pixels. Excludes unavailable C02 from minima.',
        'visible_face_resolution_fraction':1/400,'per_row_visible_face_fraction':face_rows,
        'half_folded_seat_unavailable':'C02','seats':results}






def inherited_layout(sc,cal,visibility,audience,composition,preservation):
    corners=[project(SU0,0,SZ1),project(SU1,0,SZ1),project(SU1,0,SZ0),project(SU0,0,SZ0)]
    return {'brief':'BRIEF-31-cinema-draft4.md',
        'inherits':['BRIEF-28-cinema-draft1.md','BRIEF-29-cinema-draft2.md','reviews/review-cinema-d2.md (points 1-9; no emote test)'],
        'scene':'DINK DONK Screen 1 / cinema draft 3 / whole hall',
        'image':IMAGE.name,'resolution':[W,H],
        'coordinates':{'world':'(x,y,z)=(u,-v,zpx_world/73.48469228349535)',
            'projection':'P(u,v,zpx_world)=[Ox+(u-v)*60*k,Oy+(u+v)*30*k-zpx_world*k]',
            'Ox':OX,'Oy':OY,'k':K,'lobby_ortho_scale':22.627416998,
            'ZPP_world':ZPP,'px_per_u_tile':[60*K,30*K],
            'px_per_v_tile':[-60*K,30*K],'px_per_BU_height':ZPP*K,
            'pixel_origin':'top left; continuous corners; 4K doubles image coordinates'},
        'camera':{'type':'ORTHO','rotation_degrees':[60,0,45],'ortho_scale':ORTHO},
        'calibration':cal,'composition':composition,
        'screen':{'wall':'v=0','u_range':[SU0,SU1],'v':0,'zpx_world_range':[SZ0,SZ1],
            'corners_1920x1080':dict(zip(['TL','TR','BR','BL'],corners)),
            'corners_3840x2160':dict(zip(['TL','TR','BR','BL'],[[2*x,2*y] for x,y in corners])),
            'on_frame_bbox_width_px':(SU1-SU0)*60*K,'visibility_check':visibility,
            'matte':True,'emission':0,'on_frame':all(0<x<W and 0<y<H for x,y in corners)},
        'room':{'u_range':[0,U1],'v_range':[0,V1],'wall_top_zpx_world':WALL_Z,
            'kept_walls':['u=0','v=0'],'cut_edges':['u=17.50','v=10.58'],
            'ceiling':'Shallow strip v<=0.65; dark clouds zpx=638-645 and two open trusses zpx=630-646; stepped cornice top653.',
            'stage':{'u_range':[1.30,U1-.06],'v_range':[.12,.98],'top_zpx_world':28},
            'front_cross_aisle':{'v_range':[1.05,ROW_LO],'floor_zpx_world':0,
                'walk_path_uvzpx':[[.88,2.18,0],[1.7,2.05,0],[U1-.2,2.05,0]],
                'minimum_v_width_tiles':ROW_LO-1.05}},
        'seat_count':144,'usable_seat_count':143,'rows':ROWS,'seat_pitch_u':SEAT_PITCH,'row_pitch_v':ROW_PITCH,
        'entrance':{'wall':'u=0','u':0,'v_range':[1.48,2.88],'floor_zpx_world':0,
            'height_zpx_world':115,'height_bu':115/ZPP,'EXIT_center_uvz':[.179,2.18,137]},
        'side_aisle':{'u_range':[.03,1.59],'path_uvzpx':aisle_path(),
            'walking_lane_u':[.57,1.19],'centreline_u':.88,
            'maximum_step_rise_zpx_world':RISE/2,'handrail_u':.28,'handrail_height_above_tier_zpx_world':39,
            'step_lamps_u_range':[1.43,1.48],'step_lamp_height_above_tread_zpx_world':[2,5],
            'first_seat_left_edge_u':SEATS[0]-.348,
            'gap_from_aisle_edge_to_first_seat_tiles':SEATS[0]-.348-1.59,
            'row_entry_points_uvzpx':[[1.61,r['v'],r['floor_zpx']] for r in ROWS],
            'unavailable_seats':['C02']},
        'audience_clearance':audience,'lived_in_details':LIVED_IN,
        'source_materials':{'blend':SOURCE.name,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'appended_datablocks':REUSED,'adaptations':['Dry copied carpet networks, procedural cloth/brass grain, larger localized wear.']},
        'lighting':{'state':'house_up','switchable_collections':['04 HOUSE sconces - switchable',
            '05 HOUSE ceiling pools - switchable','06 AISLE safety lamps and handrail - switchable'],
            'seat_pool_energy_increase_vs_d2_stops_about':.7,
            'screen_emission':0,'glare':False,'fog':False,'projection_beam':False},
        'zoom_headroom':{'page_zoom_max':1.85,'future_resolution_target':[3840,2160],
            'detail_strategy':'Procedural world-space cloth/metal, real curved rims, seat piping, numbering, frayed tape, carton flaps and cornice flutes.',
            'limit':'Only the one 1080p still is rendered; 4K, zoom and DOM/emote composition remain untested.'},
        'preservation':{'method':'Pre-build SHA256 of existing blends, draft-1/2 source and deliverables, all page HTML/JS/CSS; size/mtime of cloud/bundle and out10; compared through preflight and render.',
            'sha256_files':len(preservation['sha256']),'bundle_and_out10_files':len(preservation['asset_tree']),
            'source_sha256':preservation['sha256'][str(SOURCE.relative_to(ROOT.parent))],'passed':None},
        'render':{'engine':'Cycles','max_samples':384,'adaptive_min_samples':64,'adaptive_threshold':.007,
            'denoise':True,'device':sc['render_device'],'exposure':.10,'view':'AgX / Medium High Contrast'},
        'scope':'Exactly one image; new draft-3 source/blend/runtime/report/layout only. No page, bundle, out10 or prior file changes.'}




# Draft 4 geometry and finishes. Common projection, BVH and modelling helpers
# above are retained verbatim from the draft-3 builder where applicable.
def hexrgb(value):
    values=[int(value.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in values)


def finishes():
    inherited_finishes()
    for key,h,rough,metal,emit in [
        ('mauve','#936783',.88,0,0),('rose','#B98387',.90,0,0),
        ('amber cloth','#B78149',.89,0,0),('rib teal','#315B58',.92,0,0),
        ('rib shadow','#254440',.96,0,0),('dado','#28232C',.88,0,0),
        ('pink trim','#B78689',.72,0,0),('coping','#C8B3A2',.76,0,0),
        ('fixture burgundy','#602F3E',.58,.12,0),('ivory core','#F4DDB0',.68,0,1.5),
        ('red dot','#D94B32',.65,0,2.1),('salida','#76CB55',.65,0,1.9),
        ('navy carpet','#272936',.98,0,0),('carpet wine','#704154',.98,0,0),
        ('carpet ochre','#A47C50',.98,0,0),('carpet teal','#416764',.98,0,0),
        ('carpet muted','#47414F',.98,0,0),('armrest','#25242A',.72,0,0),
        ('speaker cloth','#17191B',.98,0,0),('champagne','#827366',.46,.58,0),
        ('cyan accent','#38C4DA',.62,0,1.6),('ceiling tile','#191C22',.96,0,0),
        ('poster cream','#BCAE95',.95,0,0),('poster rust','#865246',.95,0,0)]:
        M[key]=material('D4 '+key+' '+h,hexrgb(h),rough,metal,emit)
    for key in ['mauve','rose','amber cloth','rib teal','dado','navy carpet','speaker cloth']:
        M[key]=aged_copy(key,'D4 woven '+key,.90,1.06,7,.0013)
    M['faded velvet']=M['rose']
    M['carpet midnight']=M['navy carpet']; M['carpet aubergine']=M['navy carpet']
    M['carpet inset']=M['navy carpet']
    M['wear teal']=aged_copy('navy carpet','D4 compressed faded carpet pile',1.10,1.42,18,.0005)
    M['wear plum']=M['carpet muted']
    # Upholstered rear faces use the same mauve cloth as the soft front pads.
    M['seat shell']=aged_copy('mauve','D4 subtly darkened upholstered rear shells',.72,.91,10,.001)
    M['screen']=material('D4 matte neutral projection fabric ZERO EMISSION',(.60,.60,.585),1)
    M['screen'].node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=0


def flecks(u0,v0,u1,v1,z,density=12):
    # Short broken, roughly aligned rectangles. A restrained woven pattern,
    # with gaps in every motif, replaces the bright random lobby confetti.
    verts=[];faces=[];indices=[]
    mats=[M['carpet wine'],M['carpet ochre'],M['carpet teal'],M['carpet muted']]
    for i in range(int((u1-u0)*(v1-v0)*density)):
        u=RNG.uniform(u0+.06,u1-.06);v=RNG.uniform(v0+.04,v1-.04)
        width=RNG.uniform(.025,.055);length=RNG.uniform(.065,.145)
        idx=RNG.choices(range(4),[4,1,3,4])[0]
        for start,stop in [(-length,-length*.12),(length*.17,length*.70)]:
            k=len(verts)
            verts.extend(xyz(a,b,z) for a,b in [(u+start,v-width/2),(u+stop,v-width/2),
                (u+stop,v+width/2),(u+start,v+width/2)])
            faces.append((k,k+1,k+2,k+3));indices.append(idx)
    ob=mesh('D4 broken rectangular woven carpet motifs',verts,faces,mats[0])
    for ma in mats[1:]:ob.data.materials.append(ma)
    for p,idx in zip(ob.data.polygons,indices):p.material_index=idx


def stair_treads():
    for i,row in enumerate(ROWS):
        lo,hi=row['tier_v_range'];z=row['floor_zpx']
        if i==0:
            yield lo,(lo+hi)/2,7,7
            yield (lo+hi)/2,hi,14,7
        elif i==1:
            yield lo,(lo+hi)/2,24,10
            yield (lo+hi)/2,hi,34,10
        elif i==2:
            for j in range(4):yield lo+(hi-lo)*j/4,lo+(hi-lo)*(j+1)/4,34+7.5*(j+1),7.5
        else:
            quarter=(hi-lo)/4
            yield lo,lo+quarter,z-32,16
            yield lo+quarter,lo+quarter*2,z-16,16
            yield lo+quarter*2,hi,z,16


def floor_and_steps():
    collection('01 Flat front, landing and six steeper stadium tiers')
    box('Flat cross aisle slab exposed dark cut',0,0,U1,ROW_LO,-17,-.1,M['concrete'])
    box('Flat front cross aisle charcoal carpet',0,0,U1,ROW_LO,-.1,0,M['navy carpet'],.002)
    flecks(.12,1.06,U1-.10,ROW_LO-.05,.045,12)
    for row in ROWS[:2]:
        lo,hi=row['tier_v_range'];z=row['floor_zpx']
        box('Low front row '+row['row']+' shallow platform',1.65,lo,U1,hi,z-17,z-.1,M['concrete'])
        box('Low front row '+row['row']+' patterned carpet',1.65,lo,U1,hi,z-.1,z,M['navy carpet'],.002)
        flecks(1.75,lo+.04,U1-.12,hi-.04,z+.045,12)
    box('Low front divider apron cut',1.65,4.58,U1,4.83,17,33.9,M['concrete'])
    box('Low front divider apron carpet',1.65,4.58,U1,4.83,33.9,34,M['navy carpet'],.002)
    box('Floor level passage landing',0,4.58,1.65,4.83,17,LANDING_Z,M['navy carpet'],.002)
    for i,row in enumerate(ROWS[2:],2):
        lo,hi=row['tier_v_range'];z=row['floor_zpx']
        box('Tier '+row['row']+' stepped structural cut',3.15,lo,U1,hi,z-17,z-.2,M['concrete'])
        box('Tier '+row['row']+' navy patterned carpet',3.15,lo,U1,hi,z-.2,z,M['navy carpet'],.002)
        flecks(3.24,lo+.035,U1-.12,hi-.035,z+.045,12)
        box('Tier '+row['row']+' dark shadow riser',3.15,lo,U1,lo+.028,ROWS[i-1]['floor_zpx'],z-.4,M['dado'],.002)
        line('Tier '+row['row']+' subdued pale nosing',[(3.20,lo+.035,z+.15),(U1-.05,lo+.035,z+.15)],M['champagne'],.007)
        if i==2:box('C row short lateral access step',1.60,row['v']-.10,3.16,row['v']+.10,z-7.5,z,M['navy carpet'],.004)
    for a,b,h,rise in stair_treads():
        end=3.15 if a>=4.83 else 1.65
        box('D4 side stair half step cut section',0,a,end,b,h-max(17,rise),h-.1,M['concrete'])
        box('D4 patterned stair carpet',.03,a,end-.06,b,h-.1,h+.02,M['navy carpet'],.002)
        if a>=4.83:flecks(1.75,a+.04,3.03,b-.03,h+.05,12)
        flecks(.10,a+.04,1.49,b-.03,h+.05,14)
        if rise:box('D4 dark stair riser',.03,a,1.59,a+.028,h-rise,h-.2,M['dado'],.002)
        line('D4 restrained tread nosing',[(.16,a+.035,h+.25),(1.44,a+.035,h+.25)],M['champagne'],.006)
        worn_patch('D4 broken stair carpet traffic',.58,a+.04,1.16,b-.035,h+.075,M['wear teal'])
        if a>=4.83:
            # Camera-facing cheek is deliberately only 11 world px high.
            box('Low cutaway dark stair cheek',1.51,a,1.65,b,h,h+4,M['dado'],.006)
            box('Low narrow pink cream stair coping',1.495,a,1.665,b,h+4,h+7,M['coping'],.006)
            box('Wall-side stair cheek',.06,a,.19,b,h,h+22,M['dado'],.006)
            box('Wall-side cream pink stair coping',.045,a,.205,b,h+22,h+25,M['coping'],.006)
    worn_patch('D4 passage landing traffic track',.48,4.10,1.24,4.78,LANDING_Z+.075,M['wear teal'])
    # Low divider separates flat seats from the stadium. Its pale cap is thin,
    # below the face envelopes; the rail has sparse uprights.
    for a,b,top in [(1.70,6.7,63),(6.7,12.4,68),(12.4,U1,73)]:
        box('Stepped low stadium divider wall',a,4.72,b,4.82,34,top,M['dado'],.009)
        box('Thin dusty pale divider coping',a-.008,4.712,b,4.828,top,top+3,M['coping'],.007)
        line('Divider champagne tubular rail',[(a+.04,4.785,top+22),(b-.04,4.785,top+22)],M['champagne'],.014)
        for u in [a+.12,b-.14]:line('Sparse divider rail post',[(u,4.785,top+3),(u,4.785,top+22)],M['champagne'],.011)
    box('D4 shallow stage dark apron',1.30,.12,U1-.06,.92,0,27,M['dado'],.025)
    box('D4 stage midnight top',1.30,.12,U1-.06,.92,27,28,M['navy carpet'],.006)
    box('D4 stage footlight lip',1.30,.90,U1-.06,.98,20,29,M['black enamel'],.009)
    line('D4 subdued stage brass lip',[(1.35,.98,28.4),(U1-.1,.98,28.4)],M['champagne'],.008)


def wall_floor(v):
    return next((r['floor_zpx'] for r in ROWS if r['tier_v_range'][0]<=v<r['tier_v_range'][1]),0)


def walls_screen_door():
    collection('02 Ribbed teal acoustic walls, matte screen and SALIDA passage')
    box('Screen wall structural shell',-.24,-.36,U1,-.12,-17,WALL_Z,M['dado'])
    for a,b in [(0,3.72),(4.82,V1)]:
        box('Side wall structural shell',-.24,a,-.04,b,-17,WALL_Z,M['dado'])
    box('Passage solid lintel wall',-.24,3.72,-.04,4.82,128+LANDING_Z,WALL_Z,M['dado'])
    box('Wall below passage threshold',-.24,3.72,-.04,4.82,-17,LANDING_Z,M['dado'])
    for i in range(151):
        a=i*V1/151;b=(i+1)*V1/151;v=(a+b)/2
        trim=113+wall_floor(v)
        bottom=max(trim+3,132+LANDING_Z if 3.72<v<4.82 else 0)
        box('Narrow vertical teal fabric acoustic rib',-.032,a+.005,.032,b-.005,bottom,620,M['rib teal'],.010)
        line('Pleat recessed dark seam',[(.017,a,bottom),(.017,a,620)],M['rib shadow'],.0035)
        if not 3.72<v<4.82:
            box('Plum charcoal lower dado',-.025,a,.039,b,0,trim,M['dado'],0)
    trim_points=[]
    for a,b,z in [(0,2.58,113),(2.58,3.58,127),(3.58,3.72,147),(4.82,4.83,113)]+[(r['tier_v_range'][0],r['tier_v_range'][1],113+r['floor_zpx']) for r in ROWS[2:]]:
        line('Dusty pink stepped dado top',[(.055,a,z),(.055,b,z)],M['pink trim'],.012)
        if a>4.82:line('Dusty pink vertical rake transition',[(.055,a,z-48),(.055,a,z)],M['pink trim'],.012)
    box('Dark dado below screen',0,-.115,U1,-.022,0,78,M['dado'],.005)
    for u0,u1 in [(.20,1.48),(16.98,17.48)]:
        for i in range(int((u1-u0)/.075)):
            a=u0+i*.075
            box('Screen flank teal vertical pleat',a,-.114,a+.060,-.062,80,620,M['rib teal'],.009)
    screen=mesh('SCREEN INNER clean 16 by 9 wall plane v=0',
        [xyz(SU0,0,SZ1),xyz(SU1,0,SZ1),xyz(SU1,0,SZ0),xyz(SU0,0,SZ0)],[(3,2,1,0)],M['screen'])
    screen['corner_order']='TL TR BR BL';screen['physical_aspect']=16/9
    for a,b in [(SU0-.11,SU0),(SU1,SU1+.11)]:box('Black screen vertical masking',a,-.06,b,0,SZ0-8,SZ1+8,M['mask'],0)
    for a,b in [(SZ0-8,SZ0),(SZ1,SZ1+8)]:box('Black screen horizontal masking',SU0,-.06,SU1,0,a,b,M['mask'],0)
    curtain(2.30,3.18);curtain(15.84,16.73)
    # A real, recessed floor-level passage instead of a flat door sticker.
    box('Passage carpet floor',-.95,3.72,.08,4.82,LANDING_Z-.1,LANDING_Z+.03,M['navy carpet'],.002)
    box('Passage dark roof',-.95,3.72,.045,4.82,128+LANDING_Z,134+LANDING_Z,M['dado'],.003)
    for v in [3.72,4.78]:box('Passage cheek wall',-.95,v,.025,v+.04,LANDING_Z,128+LANDING_Z,M['dado'],.004)
    box('Passage rear red padded fire door',-.94,3.78,-.90,4.76,LANDING_Z,123+LANDING_Z,M['curtain velvet'],.014)
    line('Passage rear door pushbar',[(-.88,3.91,52+LANDING_Z),(-.88,4.64,52+LANDING_Z)],M['champagne'],.012)
    for v in [3.73,4.81]:box('Dark burgundy passage jamb',-.025,v-.025,.08,v+.025,LANDING_Z,131+LANDING_Z,M['fixture burgundy'],.008)
    box('Passage burgundy head',-.025,3.705,.08,4.845,126+LANDING_Z,132+LANDING_Z,M['fixture burgundy'],.006)
    box('SALIDA dark plaque over mouth',.055,3.76,.16,4.79,139+LANDING_Z,160+LANDING_Z,M['black enamel'],.009)
    text('Luminous green SALIDA','SALIDA',.171,4.275,149.5+LANDING_Z,.175,M['salida'])
    box('DINK DONK separate wall plaque rim',.05,1.40,.115,3.24,271,317,M['champagne'],.010)
    box('DINK DONK plaque dark field',.115,1.43,.135,3.21,273,315,M['dado'],.006)
    text('DINK DONK warm plaque lettering','DINK DONK',.145,2.32,301,.215,M['poster cream'])
    text('Screen 1 warm plaque lettering','S C R E E N   1',.145,2.32,285,.106,M['poster cream'])
    line('Single small cyan foyer neon accent',[(.15,1.54,274.5),(.15,3.10,274.5)],M['cyan accent'],.009)
    # Three modest graphic picture frames, above the walking lane.
    for v,z,i in [(.64,259,0),(7.13,415,1),(7.83,415,2)]:
        box('Small framed side wall picture',.045,v-.22,.115,v+.22,z-19,z+19,M['black enamel'],.006)
        box('Small picture cream paper',.117,v-.185,.121,v+.185,z-15,z+15,M['poster cream'],.002)
        box('Picture abstract wine field',.123,v-.15,.126,v+.04,z-11,z+10,M['fixture burgundy'],0)
        line('Picture restrained teal diagonal',[(.129,v-.12,z-8),(.129,v+.12,z+8)],M['rib teal'],.016)
    return screen


def front_and_ceiling():
    collection('07 Multiplex cloth speakers and charcoal acoustic tile ceiling')
    for z,depth,height in [(623,.13,8),(640,.25,6),(648,.35,5)]:
        box('Quiet charcoal screen cornice',0,-.12,U1,depth,z,z+height,M['ceiling tile'],.007)
        box('Quiet charcoal side cornice',-.05,0,depth,V1,z,z+height,M['ceiling tile'],.007)
    for u0,u1 in [(1.00,1.57),(16.98,17.39)]:
        box('Subdued dark proscenium pillar',u0,.04,u1,.15,30,615,M['dado'],.023)
        for j in range(4):
            u=u0+.055+j*(u1-u0-.11)/3
            line('Quiet proscenium vertical flute',[(u,.16,42),(u,.16,602)],M['champagne'],.005)
    for u in [2.10,16.45]:
        box('Plain multiplex speaker enclosure',u,.17,u+.63,.64,28,246,M['armrest'],.030)
        box('Plain dark acoustic cloth grille NO WOOFER RINGS',u+.024,.646,u+.606,.660,35,239,M['speaker cloth'],.012)
        for z in [42,232]:
            for uu in [u+.05,u+.58]:cylinder('Small speaker fixing screw',uu,.666,z,.012,.006,M['champagne'],axis=(0,-1,0),count=8)
        box('Small speaker manufacturer tab',u+.24,.663,u+.39,.670,39,42,M['champagne'],.002)
    # An L-shaped shallow ceiling reveal; the rest is removed for the dollhouse.
    for j in range(22):
        a=.03+j*.79
        box('Charcoal acoustic ceiling tile',a,.05,min(a+.765,U1),.59,638,644,M['ceiling tile'],.004)
    for j in range(14):
        a=.03+j*.75
        box('Side acoustic ceiling tile',.025,a,.39,min(a+.724,V1),638,644,M['ceiling tile'],.004)
    for u in [3.8,8.3,12.7,16.8]:
        cylinder('Recessed circular downlight black bezel',u,.43,636.5,.090,.035,M['armrest'],count=24)
        cylinder('Recessed small ivory lens',u,.43,635,.062,.012,M['ivory core'],count=24)
    for u in [6.4,14.2]:
        box('Small square ceiling vent frame',u-.16,.16,u+.16,.50,634.5,638,M['armrest'],.003)
        for k in range(6):line('Ceiling square vent slot',[(u-.12,.20+k*.045,634),(u+.12,.20+k*.045,634)],M['champagne'],.003)


def pillow(name,u,v,z,width,height,depth,ma):
    # A rounded rectangular cushion with broad domed faces. Height is expressed
    # in world pixel units; shoulder radius is deliberately visible at overview.
    verts=[];faces=[];n=64
    centre=z+height/2
    for y,scale in [(-depth/2,.84),(-depth*.34,.99),(0,1),(depth*.34,.99),(depth/2,.84)]:
        for i in range(n):
            a=math.tau*i/n
            x=math.copysign(abs(math.cos(a))**.43,math.cos(a))*width/2*scale
            zz=math.copysign(abs(math.sin(a))**.43,math.sin(a))*height/2*scale
            verts.append(xyz(u+x,v+y,centre+zz))
    faces.extend([tuple(range(n-1,-1,-1)),tuple(range(4*n,5*n))])
    for j in range(4):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    ob=mesh(name,verts,faces,ma)
    # Winding is recalculated rather than relying on the u,-v coordinate sign.
    import bmesh
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data);bm.free()
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def seats():
    for row in ROWS:
        collection('03 Row '+row['row']+' rounded mauve seats')
        v=row['v'];z=row['floor_zpx'];backs=[];positions=row['seat_u'];pitch=row['seat_pitch_u']
        bank=row['section']=='stadium bank'
        for j,u in enumerate(positions):
            tag='%s%02d'%(row['row'],j+1);prefix='Seat '+tag
            cloth=M['rose' if tag in LIVED_IN['faded_seats'] else 'mauve']
            # A single small amber block, echoing photo 04 without a checkerboard.
            if row['row'] in ['D','E'] and 11<=j<=14:cloth=M['amber cloth']
            box(prefix+' low floor pedestal',u-.14,v-.12,u+.14,v+.18,z+.4,z+5,M['armrest'],.025)
            for du in [-.23,.23]:
                box(prefix+' dark pivot support',u+du-.025,v+.08,u+du+.025,v+.19,z+4,z+37,M['armrest'],.012)
                cylinder(prefix+' subdued flip hinge',u+du,v+.10,z+27,.050,.022,M['champagne'],axis=(1,0,0),count=16)
            cw=.29 if bank else .32
            cushion=[box(prefix+' thick soft flip cushion',u-cw,v-.39,u+cw,v+.12,z+26,z+CUSHION_HEIGHT,cloth,.055)]
            if tag=='C02':
                pivot=xyz(u,v+.10,z+31);rotation=Matrix.Rotation(math.radians(52),3,'X')
                for ob in cushion:
                    for vert in ob.data.vertices:vert.co=pivot+rotation@(vert.co-pivot)
                    ob['stuck_half_folded']=True
                row['seat_exceptions']=[{'seat':tag,'u':u,'state':'stuck half folded 52 degrees','available_for_chatter':False}]
            shell_cloth=cloth if tag in LIVED_IN['faded_seats'] or cloth==M['amber cloth'] else M['seat shell']
            backs.append(pillow(prefix+' rounded upholstered rear shell',u,v+.31,z+23,.665 if bank else .735,39,.265,shell_cloth))
            backs.append(pillow(prefix+' plump front backrest cushion',u,v+.185,z+28,.605 if bank else .668,32,.17,cloth))
            # Broad curved seam, not the hard bright brass rectangles of draft 3.
            seam=[]
            for k in range(33):
                a=math.pi*k/32
                seam.append((u+.300*math.cos(a),v+.439,z+37+18*math.sin(a)))
            backs.append(line(prefix+' soft rear shoulder seam',seam,M['dado'],.003))
            backs.append(box(prefix+' small rear seat number tab',u-.066,v+.447,u+.066,v+.453,z+36,z+40,M['champagne'],.003))
            backs.append(back_label(tag,u,v+.457,z+38))
            if tag in LIVED_IN['patched_seats']:
                backs.append(tape_patch(prefix+' broad frayed gaffer repair',u,v+.453,z+31))
                for k in range(5):backs.append(line(prefix+' frayed tape edge',[(u-.24+k*.12,v+.455,z+34),(u-.24+k*.12,v+.455,z+35)],M['gaffer'],.003))
        for j in range(len(positions)+1):
            u=positions[0]-pitch/2+j*pitch
            box('Shared dark armrest support',u-.028,v-.10,u+.028,v+.18,z+5,z+39,M['armrest'],.012)
            aw=.06 if bank else .068
            box('Soft rounded dark armrest',u-aw,v-.31,u+aw,v+.26,z+37,z+42,M['armrest'],.032)
            cylinder('Recessed black cupholder well',u,v-.17,z+42,.060,.015,M['mask'],count=24)
            line('Dark molded cupholder lip',[(u+.067*math.cos(k*math.tau/32),v-.17+.067*math.sin(k*math.tau/32),z+42.5) for k in range(32)],M['armrest'],.009,True)
        ob=join(backs,row['seat_back_object']);ob['row_id']=row['row'];ob['future_occluder']=True
        ob['facing']='toward v=0; rounded upholstered rear shells face positive-v'


STEP_DOTS=[]
def fixtures_and_lighting():
    collection('04 HOUSE sconces - switchable')
    for v,z in [(1.05,320),(3.30,344),(6.24,435),(9.30,540)]:
        box('Tall narrow burgundy deco fixture housing',.034,v-.115,.13,v+.115,z-47,z+47,M['fixture burgundy'],.024)
        box('Warm narrow ivory vertical diffuser',.132,v-.053,.19,v+.053,z-40,z+40,M['ivory core'],.020)
        for zz in [z-45,z+42]:box('Burgundy sconce narrow end cap',.12,v-.105,.205,v+.105,zz,zz+3,M['fixture burgundy'],.006)
        point_lamp('Warm deco light soft fabric pool',(.29,v,z+15),22,(1,.74,.49),.25)
        light('Sconce soft upward pleat wash',(.40,v,z+29),(.02,v,z+105),13,(1,.79,.58),.45,.17)
    for v,z in [(2.20,472),(4.98,501),(7.80,565),(10.12,583)]:
        before=set(bpy.context.scene.objects)
        box('Compact high wall surround angled enclosure',.03,v-.19,.29,v+.19,z-17,z+17,M['armrest'],.014)
        box('Compact surround dark fabric front',.294,v-.162,.303,v+.162,z-14,z+14,M['speaker cloth'],.005)
        pivot=xyz(.12,v,z)
        rot=Matrix.Rotation(math.radians(13),4,'Y')@Matrix.Rotation(math.radians(-8),4,'Z')
        transform=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot)
        for ob in set(bpy.context.scene.objects)-before:ob.data.transform(transform)
    collection('05 HOUSE ceiling pools - switchable')
    for u,v,power in [(4,3.3,460),(10,3.3,500),(16.4,3.3,460),
        (4.4,6.7,420),(10.8,7,430),(16.4,7.1,390),(6,10,330),(14.6,10,350)]:
        light('HOUSE soft neutral warm seat pool',(u,v,610),(u,v,wall_floor(v)+20),power,(1,.84,.71),2.05,1.65)
    light('HOUSE readable passage landing',(1.15,4.15,240),(.65,4.50,0),70,(1,.79,.59),1.2,.9)
    for v,z,power in [(6.1,405,110),(9.1,575,95)]:
        light('HOUSE readable stair landing pool',(.85,v,z),(.75,v,z-235),power,(1,.84,.70),1.8,2.2)
    light('HOUSE soft cool-neutral seat bounce',(15,9,500),(10,7,190),130,(.57,.72,.81),4,3)
    # No small cornice bounce directed at the top edge of the screen.
    collection('06 AISLE safety lamps and handrail - switchable')
    rail=[]
    for a,b,h,rise in stair_treads():
        if a<4.83:continue
        rail.append((.12,a+.05,h+37));rail.append((.12,b-.03,h+37))
        if rise:
            line('Sparse champagne handrail upright',[(.12,a+.15,h+25),(.12,a+.15,h+37)],M['champagne'],.013)
        u,v,z=1.668,a+.08,h-rise*.5
        cylinder('Small discrete red orange riser end dot',u,v,z,.022,.018,M['red dot'],axis=(1,0,0),count=16)
        STEP_DOTS.append([u,v,z])
        light('Tiny red safety riser pool',(u+.04,v,z),(u+.35,v,h),.45,(1,.12,.035),.09,.06)
    line('Simple continuous tubular champagne side rail',rail,M['champagne'],.021)
    box('Low passage base continuing onto landing',.08,4.79,1.50,4.83,LANDING_Z,LANDING_Z+4,M['dado'],.005)
    for u in [.98,1.15,1.32,1.49]:
        box('Discrete passage landing base red safety dot',u-.023,4.79,u+.023,4.83,LANDING_Z+1.5,LANDING_Z+3.5,M['red dot'],.008)
        STEP_DOTS.append([u,4.81,LANDING_Z+2.5])
    light('Dim warm passage interior',(-.45,4.15,95),(-.2,4.35,0),10,(1,.65,.37),.4,.5)


def link_screen_lighting(sc,screen):
    # Receiver linking keeps every local sconce/downlight off the projection
    # surface. A very large diffuse house-fill source makes a smooth matte quad.
    room=bpy.data.collections.new('Lighting receivers - room excluding screen')
    screen_receivers=bpy.data.collections.new('Lighting receiver - matte screen only')
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:
            (screen_receivers if ob==screen else room).objects.link(ob)
    for ob in sc.objects:
        if ob.type=='LIGHT':ob.light_linking.receiver_collection=room
    collection('05b HOUSE broad diffuse screen fill - switchable')
    fill=light('Broad indirect-style house fill on matte screen',(9.4,6,395),(9.4,0,335),920,(.94,.95,1),14,10)
    fill.light_linking.receiver_collection=screen_receivers


def aisle_path():
    path=[[.48,4.275,LANDING_Z],[LANE_U,4.275,LANDING_Z],[LANE_U,4.73,LANDING_Z]]
    for a,b,h,rise in stair_treads():
        if a>=4.83:path.append([LANE_U,a+.12,h])
    path.append([LANE_U,V1-.12,ROWS[-1]['floor_zpx']])
    return path


def composition_and_route(sc):
    pixels=[project(p.x,-p.y,p.z*ZPP) for p in SCENE_VERTS]
    bounds=[min(p[0] for p in pixels),min(p[1] for p in pixels),max(p[0] for p in pixels),max(p[1] for p in pixels)]
    margins=dict(zip(['left','top','right','bottom'],[bounds[0],bounds[1],W-bounds[2],H-bounds[3]]))
    assert min(margins.values())>=39,('Silhouette too close to frame',margins)
    path=aisle_path();points=[]
    for a,b in zip(path,path[1:]):
        for i in range(6):points.append([a[j]+(b[j]-a[j])*i/6 for j in range(3)])
    points.append(path[-1]);route=[]
    for point in points:
        anchor=xyz(*point)
        fracs=[top_exposure(SCENE_BVH,anchor,x) for x in [-11.1,0,11.1]]
        route.append({'uvzpx':point,'pixel_floor':project(*point),'unobstructed_top_fraction':min(fracs)})
        if min(fracs)<.55:
            hits=[]
            for dx,frac in zip([-11.1,0,11.1],fracs):
                p=anchor+RIGHT*(dx/PPU)+UP*((50*(1-frac)-.08)/PPU)
                hit=SCENE_BVH.ray_cast(p+NORMAL*45,-NORMAL,44.9995)
                if hit[2] is not None:hits.append(SCENE_OWNERS[hit[2]])
            print('ROUTE_LOW_FRACTION',point,min(fracs),hits,flush=True)
    lamp_pixels=[project(*p) for p in STEP_DOTS];conflicts=[]
    for r in route:
        x,y=r['pixel_floor']
        for lamp in lamp_pixels:
            if abs(lamp[0]-x)<37*K and y-50*K<lamp[1]<y-22.5*K:conflicts.append({'walker':r['uvzpx'],'lamp_pixel':lamp})
    return {'evaluated_geometry_bounds_1080p':bounds,'dark_margins_px':margins,'minimum_margin_px':min(margins.values()),
        'note':'Same camera, origin, screen quad and footprint as draft 3; steeper bank lifts the lower silhouette within the existing dark margins.',
        'route_check':{'method':'400-ray vertical samples across three face-core columns at six subdivisions of every passage/landing/stair link; no audience image.',
            'samples':route,'minimum_visible_top_fraction':min(r['unobstructed_top_fraction'] for r in route),
            'bright_step_lamp_centres_in_upper_55pct_head_envelopes':conflicts}}


def preservation_snapshot():
    strong=set(ROOT.glob('*.blend'))|set(ROOT.glob('*.blend1'))|set(ROOT.glob('*.py'))
    for n in [1,2,3]:
        for name in ['CINEMA-DRAFT-%02d.md'%n,'cinema_layout_%02d.json'%n,'cinema_draft_%02d.png'%n]:strong.add(QA/name)
    for ext in ['*.html','*.js','*.css']:
        strong.update(p for p in ROOT.parent.rglob(ext) if not any(s in p.relative_to(ROOT.parent).parts for s in ['tools','node_modules']))
    strong.discard(TARGET);strong.discard(Path(__file__).resolve())
    hashes={str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(strong) if p.is_file()}
    tree={}
    for directory in [ROOT/'cloud'/'bundle',ROOT/'out10']:
        for p in directory.rglob('*'):
            if p.is_file():
                st=p.stat();tree[str(p.relative_to(ROOT.parent))]=[st.st_size,st.st_mtime_ns]
    return {'sha256':hashes,'asset_tree':tree}


def layout(sc,cal,visibility,audience,composition,preservation):
    d=inherited_layout(sc,cal,visibility,audience,composition,preservation)
    d.update(brief='BRIEF-31-cinema-draft4.md',inherits=['BRIEF-28-cinema-draft1.md','BRIEF-29-cinema-draft2.md','BRIEF-30-cinema-draft3.md','reviews/review-cinema-d3-refs.md'],
        scene='DINK DONK Screen 1 / cinema draft 4 / childhood multiplex',scope='Exactly one 1080p image; new draft-4 builder/blend/runtime/report/layout only. Only writes inside roxy3d.')
    d['seat_count']=sum(len(r['seat_u']) for r in ROWS);d['usable_seat_count']=d['seat_count']-1
    d['seat_pitch_u']='Per-row: .84 for low front, .784 for stadium; see rows[].seat_pitch_u'
    d['row_pitch_v_per_pair']=[{'from':a['row'],'to':b['row'],'delta_v':round(b['v']-a['v'],4)} for a,b in zip(ROWS,ROWS[1:])]
    d['room']['ceiling']='Charcoal acoustic tile L-shaped shallow reveal; screen-wall v<=0.59 and side-wall u<=0.39; small round downlights and two square vents; cornice top653.'
    d['room']['low_front_rows']=['A','B'];d['room']['low_front_rake_zpx_world']=[14,34];d['room']['stadium_rows']=['C','D','E','F','G','H']
    d['room']['stadium_rise_zpx_world']=48;d['room']['front_cross_aisle']['walk_path_uvzpx']=[[.88,2.32,0],[U1-.2,2.32,0]]
    d['room']['stadium_full_height_floor_start_u']=3.15
    d['room']['stair_access_terraces_u_range']=[1.65,3.15]
    d['room']['divider']={'v_range':[4.712,4.828],'u_range':[1.70,U1],'wall_top_zpx_world':[63,68,73],
        'coping_thickness_zpx_world':3,'rail_height_above_wall_zpx_world':22}
    d['room']['landing']={'u_range':[.20,1.50],'v_range':[4.20,4.83],'floor_zpx_world':LANDING_Z}
    d['entrance']={'wall':'u=0','type':'recessed floor-level passage with rear fire door','u_range':[-.95,.08],
        'v_range':[3.72,4.82],'floor_zpx_world':LANDING_Z,'height_zpx_world':128,
        'SALIDA_center_uvz':[.171,4.275,149.5+LANDING_Z],'rear_door_u':-.90,'spawn_uvzpx':[.48,4.275,LANDING_Z]}
    d['side_aisle'].update(u_range=[.03,1.59],path_uvzpx=aisle_path(),walking_lane_u=[.57,1.19],centreline_u=LANE_U,
        maximum_step_rise_zpx_world=16,handrail_u=.12,handrail_height_above_tier_zpx_world=37,
        step_lamps_u_range=[1.659,1.677],step_lamp_height_above_tread_zpx_world=[-8,-3.75],
        first_seat_left_edge_u=SEATS[0]-.3675,gap_from_aisle_edge_to_first_seat_tiles=SEATS[0]-.3675-1.59,
        row_entry_points_uvzpx=[[1.72,r['v'],r['floor_zpx']] for r in ROWS],
        front_rows_branch_uvzpx=[[LANE_U,4.275,34],[LANE_U,4.08,34],[LANE_U,3.70,24],[LANE_U,3.40,14],[LANE_U,3.08,14]],
        low_front_row_entry_paths_uvzpx={'A':[[.88,3.08,14],[1.72,3.08,14],[2.15,3.08,14]],
            'B':[[.88,4.08,34],[1.72,4.08,34],[2.22,4.08,34]]},
        half_steps=[{'v_range':[a,b],'floor_zpx_world':h,'rise_zpx_world':r} for a,b,h,r in stair_treads()],
        safety_lamp_centres_uvzpx=STEP_DOTS)
    d['side_aisle']['first_seat_left_edge_u_by_row']={r['row']:r['seat_u'][0]-(.3675 if i<2 else .3325) for i,r in enumerate(ROWS)}
    d['side_aisle']['extended_stair_tread_u_range']=[.03,3.09]
    d['side_aisle']['camera_facing_cheek']={'u_range':[1.495,1.665],'dark_height_zpx_world':4,'coping_thickness_zpx_world':3}
    d['lived_in_details']['incidents'][0]['uvzpx']=[1.0,4.275,LANDING_Z]
    d['source_materials']['adaptations']=['Dry lobby palette and curtain wear retained; sRGB childhood-photo palette converted to scene linear; mauve upholstered rear shells, teal pleats, patterned navy carpet and subdued champagne rail.']
    d['reference_features']={'02':'Teal vertical pleats, stepped dusty pink trim over dark dado, tall burgundy/ivory sconces, small wall speakers and framed pictures; low front section.',
        '03':'Dark entrance passage, SALIDA plaque, visible landing and side stair route; narrow cream pink stair coping and red dots.',
        '04':'Dusty mauve soft seats with four rose replacements and one eight-seat amber block.',
        '05':'Rounded high backs, dark arms/cupholders, patterned stair carpet and discrete red riser lights.',
        '01 and 06':'One small cyan plaque underline; ceiling tiles and navy/wine/ochre/teal carpet motifs.',
        '07':'Restrained connection to mall multiplex atmosphere; no literal mall elements copied.'}
    d['lighting']={'state':'house_up','switchable_collections':['04 HOUSE sconces - switchable','05 HOUSE ceiling pools - switchable',
        '05b HOUSE broad diffuse screen fill - switchable','06 AISLE safety lamps and handrail - switchable'],
        'screen_emission':0,'screen_local_light_linking':'All local lights exclude the screen; a single very broad diffuse house fill illuminates only its matte fabric, removing the draft-3 top-edge hot spot.',
        'glare':False,'fog':False,'projection_beam':False}
    d['preservation']['method']='SHA256 of every original blend, root Python builder, prior cinema deliverable and page HTML/JS/CSS; size/mtime inventory of cloud/bundle and out10; before/after comparison. External cloud runner logs are excluded.'
    d['zoom_headroom']['detail_strategy']='Rounded pillow meshes, cloth weave, modeled pleats, molded cupholders, seat identifiers, frayed tape, small screws and carpet motifs.'
    return d


def report(data):
    c=data['coordinates'];cal=data['calibration'];a=data['audience_clearance'];r=data['render'];s=data['screen'];co=data['composition']
    lines=['# Cinema draft 04 - childhood multiplex','',
        'One 1920x1080 house-lights-up still for Brief 31. Same whole-hall orthographic framing and screen quad as draft 3; '
        f"two gently raked low front rows of 18 seats, three main rows of 16 and three rear rows of 15: {data['seat_count']} total / {data['usable_seat_count']} usable (C02 stuck half folded). "
        'The main bank is set back from the stair lane, with one extra seat-width notch in the last three rows, to keep the arrival route clear in projection.','',
        f"Camera `(60,0,45)` degrees, `ortho_scale=30`, `Ox={OX:g}, Oy={OY:g}`, `k={K:.12f}`. "
        f"World `(x,y,z)=(u,-v,zpx_world/{ZPP})`. "
        '`P=[Ox+(u-v)*60k, Oy+(u+v)*30k-zpx_world*k]`.','',
        f"One u tile: `({60*K:.9f},{30*K:.9f})px`; v tile: `({-60*K:.9f},{30*K:.9f})px`; "
        f"one BU height: `{ZPP*K:.9f}px`. Emote envelope `{50*K:.6f} x {74*K:.6f}px`. All JSON heights use lobby zpx_world units.",'',
        '## Calibration and composition','',
        f"Five non-rendering marker empties, independent Blender camera matrix vs analytic formula. Maximum axis error `{cal['max_axis_error_px']:.9f}px`; PASS +/-1 px. No calibration image.",'',
        '| Marker (u,v,zpx_world) | x error px | y error px |','|---|---:|---:|']
    for p in cal['points']:lines.append(f"| {tuple(p['uvz'])} | {p['error_px'][0]:.9f} | {p['error_px'][1]:.9f} |")
    lines.extend(['',f"Evaluated geometry bounds L/T/R/B: `{', '.join(f'{x:.3f}' for x in co['evaluated_geometry_bounds_1080p'])}`. "
        f"Dark margins: `{json.dumps({k:round(v,2) for k,v in co['dark_margins_px'].items()})}`. Full hall and both row ends retained.",'',
        '## Screen and layout','',
        f"Screen on v=0: `u=[{SU0},{SU1}]`, `zpx_world=[{SZ0},{SZ1:.9f}]`; physical 16:9, width `{s['on_frame_bbox_width_px']:.3f}px`. "
        'Matte fabric, zero emission and specular, no artwork. All local light sources exclude this surface; one broad diffuse house fill supplies smooth neutral illumination. '
        'No cornice-directed small lamp, glare, fog or beam.','',
        '| Corner | 1920x1080 (x,y) | 3840x2160 (x,y) |','|---|---|---|'])
    for key,p in s['corners_1920x1080'].items():lines.append(f"| {key} | ({p[0]:.6f}, {p[1]:.6f}) | ({2*p[0]:.6f}, {2*p[1]:.6f}) |")
    lines.extend(['',f"Screen visibility: `{s['visibility_check']['rays']:,}` evaluated-geometry rays, every inner image-pixel centre plus inset perimeter; zero blockers. "
        'The 4K coordinates are computed, not a rendered 4K image.','',
        f"Room `u=[0,{U1}], v=[0,{V1}]`; walls u=0/v=0, top650; shallow ceiling/cornice top653. "
        'Low front rows A/B stand at 14/34 zpx_world (20-unit rake); C-H stand at 64/112/160/208/256/304. The passage landing is at 34, matching row B. Four 7.5-unit starter steps reach C, then three 16-unit side steps per subsequent tier. Full-height bank floors start at u=3.15; lower stair-access terraces extend from u=1.65 to 3.15. The divider stands on the 34-unit apron with wall tops 63/68/73, a three-unit cream-pink cap and a sparse champagne rail 22 above it.','',
        '| Row | Section | Seat-line v | Floor zpx_world | Seat u positions |','|---|---|---:|---:|---|'])
    for row in ROWS:lines.append(f"| {row['row']} | {row['section']} | {row['v']:.3f} | {row['floor_zpx']} | "+', '.join(f'{u:.2f}' for u in row['seat_u'])+' |')
    lines.extend(['','Full tier extents, seat centres, passage/landing/stair points, low-front-row branch and entry points are in `cinema_layout_04.json`.','',
        '## Faces, passage and stairs','',
        'Each row has one joined backrest mesh, including its rounded upholstered rear shells, front pads, seams, number tabs and repairs. '
        'Cushion anchor = tier+36; high rounded rear shells top = tier+62. Dark arms have recessed cupholders. '
        'The numeric face check uses 400 vertical ray samples from each 50k-pixel camera-facing envelope; face-core columns are -11.1,0,+11.1 lobby pixels. '
        'C02 is excluded from usable-seat minima.','',
        '| Row | Own back visible % min-max | All geometry visible % min | Face core visible % min | Nearer rows visible % min | Exposed height px min | Screen clearance px |',
        '|---|---:|---:|---:|---:|---:|---:|'])
    for f in a['per_row_visible_face_fraction']:
        lines.append(f"| {f['row']} | {100*f['own_back_visible_fraction_min']:.2f}-{100*f['own_back_visible_fraction_max']:.2f} | "
            f"{100*f['all_geometry_visible_fraction_min']:.2f} | {100*f['face_core_visible_fraction_min']:.2f} | "
            f"{100*f['nearer_rows_only_visible_fraction_min']:.2f} | {f['visible_face_height_px_min']:.3f} | {a['row_minimum_clearance_px'][f['row']]:.3f} |")
    lines.extend(['',f"All {data['seat_count']} full envelopes pass screen clearance: `k*(60*v+90-floor_zpx_world-36-50-18.5)`, minimum `{a['minimum_clearance_px']:.6f}px`. "
        'This checks the maximum74k width against the sloping lower screen edge.','',
        'Recessed entrance passage: `u=[-0.95,0.08], v=[3.72,4.82], floor=34, clear height=128`; rear burgundy fire door at u=-0.90. '
        '`SALIDA` green plaque centre `(0.171,4.275,183.5)`. Spawn `(0.48,4.275,34)` -> lit landing `(0.88,4.275,34)` -> '
        'stair foot `(0.88,4.73,34)` -> each half-step -> back-row landing. The front rows branch down the shallow side steps. '
        'Walk lane u=0.57-1.19; front seat left edge=2.2325, main bank left edge=4.7875 (rear notch=5.5715, H=5.7115). Far-wall tubular rail u=0.12 at tier+37; camera-facing cheek is only four high with a three-unit narrow cap. Red dots sit midway down exposed riser ends, away from passing heads.','',
        f"Route face-core minimum `{100*co['route_check']['minimum_visible_top_fraction']:.2f}%` across "
        f"{len(co['route_check']['samples'])} sampled positions; "
        f"`{len(co['route_check']['bright_step_lamp_centres_in_upper_55pct_head_envelopes'])}` safety-dot centres inside upper55% face envelopes. "
        'The route remains a numeric envelope check; no emote image or page behaviour was tested.','',
        '## Photo translation and lived-in detail',''])
    for key,value in data['reference_features'].items():lines.append(f'- Photo {key}: {value}')
    lines.extend(['','Five wear groups retained: entrance carpet traffic, D01 popcorn/soda spill and tipped cup, broad H04 gaffer repair, '
        'conspicuous G13 faded rear upholstery (plus three quieter rose replacements), and discarded open carton in the front cross-aisle. '
        'The JSON cross-aisle route uses v2.32 to pass behind the carton. C02 remains half folded52 degrees. '
        'Carpet is charcoal navy with subdued broken wine/ochre/teal rectangles; no full-strength foyer neon. '
        'Switchable light collections separate sconces, house pools, broad screen fill and safety dots.','',
        '## Render and preservation','',
        f"Blender {r['blender_version']}; Cycles adaptive64-384, threshold0.007, denoise, {r['device']}. "
        f"Single render `{r['seconds']:.2f}s`; build/checks `{r['build_and_checks_seconds']:.2f}s`; total `{r['total_seconds']:.2f}s`. Exactly one beauty PNG.",'',
        f"Preservation PASS: `{data['preservation']['sha256_files']}` original blend, Python, previous cinema and page files match SHA256; "
        f"`{data['preservation']['bundle_and_out10_files']}` cloud/out10 files match size/mtime. "
        f"Source palette SHA256 `{data['preservation']['source_sha256']}`. All writes confined to new draft4 paths inside roxy3d; runtime and GPU caches under qa11/runtime04.",'',
        'Reproduce with `build_cinema_draft4.py` in headless Blender5.2.3. `-- --preflight` only builds and checks geometry, never renders or saves a blend. '
        'Existing image/blend/report/layout or render-started marker blocks another beauty render.','',
        'No alternate stills, 4K rendering, audience artwork, live page/zoom validation, dim state, layers, sprites or loops. Stop for owner review.',''])
    with REPORT.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))


def main():
    started=time.perf_counter()
    assert bpy.app.version[:3]==(5,2,3),bpy.app.version_string
    preflight='--preflight' in sys.argv
    if not preflight:
        for p in [IMAGE,TARGET,REPORT,LAYOUT,RUNTIME/'render_started']:
            assert not p.exists(),'Strict new-file/single-render stop: '+str(p)
    before=preservation_snapshot()
    baseline=RUNTIME/'preservation_before.json'
    if baseline.exists():
        saved=json.loads(baseline.read_text())
        # The first preflight included active external cloud runner logs; retain
        # that original evidence, compare only the explicitly protected bundle.
        saved['asset_tree']={k:v for k,v in saved['asset_tree'].items()
            if ('cloud'+os.sep+'bundle'+os.sep) in k or ('out10'+os.sep) in k}
        assert saved==before,'Protected file changed since first preflight'
    else:
        with baseline.open('x',encoding='utf-8') as f:json.dump(before,f,indent=2)
    sc=configure();palette();finishes();floor_and_steps();screen=walls_screen_door()
    front_and_ceiling();seats();fixtures_and_lighting();litter();link_screen_lighting(sc,screen)
    collection('00 Exact page camera and calibration markers')
    cal=calibration(sc);visibility=screen_check(sc,screen);audience=audience_check()
    print('FACE_CHECK',json.dumps(audience['per_row_visible_face_fraction']),flush=True)
    composition=composition_and_route(sc)
    assert preservation_snapshot()==before,'Protected original changed during build'
    data=layout(sc,cal,visibility,audience,composition,before)
    occluders=[o for o in sc.objects if o.get('future_occluder')]
    assert len(occluders)==8 and all(o.type=='MESH' for o in occluders)
    print('CINEMA_PREFLIGHT',json.dumps({'origin':[OX,OY],'ortho_scale':ORTHO,'k':K,
        'calibration_max_error':cal['max_axis_error_px'],'screen_width':data['screen']['on_frame_bbox_width_px'],
        'screen_rays':visibility['rays'],'screen_blocked':visibility['blocked'],
        'composition':composition,'visible_face_rows':audience['per_row_visible_face_fraction'],
        'audience_minimum_clearance':audience['minimum_clearance_px'],'object_count':len(sc.objects),
        'row_occluders':len(occluders)}),flush=True)
    assert all(.55<=f['own_back_visible_fraction_min']<=.70 for f in audience['per_row_visible_face_fraction'])
    assert all(f['all_geometry_visible_fraction_min']>=.55 for f in audience['per_row_visible_face_fraction'])
    assert all(f['face_core_visible_fraction_min']>=.55 for f in audience['per_row_visible_face_fraction'])
    assert all(f['nearer_rows_only_visible_fraction_min']>=f['own_back_visible_fraction_min'] for f in audience['per_row_visible_face_fraction'])
    assert composition['route_check']['minimum_visible_top_fraction']>=.55
    assert not composition['route_check']['bright_step_lamp_centres_in_upper_55pct_head_envelopes']
    if preflight:
        p=RUNTIME/('preflight_%02d.json'%(1+len(list(RUNTIME.glob('preflight_*.json')))))
        with p.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
        print('PREFLIGHT PASSED. NO IMAGE RENDERED. NO BLEND SAVED.',flush=True);return
    sc.render.filepath=str(IMAGE)
    sc['screen_quad_1920']=json.dumps(data['screen']['corners_1920x1080'])
    sc['layout_contract']=json.dumps(data)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    with (RUNTIME/'render_started').open('x',encoding='utf-8') as f:f.write('One render authorized by Brief 31. No second render.\n')
    built=time.perf_counter();print('CINEMA_SINGLE_RENDER_START',flush=True)
    bpy.ops.render.render(write_still=True)
    ended=time.perf_counter()
    assert IMAGE.exists() and preservation_snapshot()==before,'Image missing or original changed'
    data['preservation']['passed']=True
    data['render'].update(seconds=ended-built,build_and_checks_seconds=built-started,
        total_seconds=ended-started,blender_version=bpy.app.version_string)
    with LAYOUT.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')
    report(data)
    print('CINEMA_DRAFT_04_RENDER_COMPLETE',flush=True)


if __name__=='__main__':main()

