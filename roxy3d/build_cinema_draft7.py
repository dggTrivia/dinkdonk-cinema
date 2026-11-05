"""Brief 34. Style the immutable draft-6 v2 layout; one beauty image then stop.

Blender --background --factory-startup --python-exit-code 1 --python this.py
Use -- --preflight for geometry only. All writes and caches live under roxy3d.
Draft 4 supplies selected pure geometry/material helpers, never its main/module
side effects. No old blend is opened, modified, or saved.
"""
import sys
sys.dont_write_bytecode = True
import os, ast, math, json, time, random, hashlib, copy, struct, zlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUNTIME = QA/'runtime07'
IMAGE = QA/'cinema_draft_07.png'
REPORT = QA/'CINEMA-DRAFT-07.md'
LAYOUT = QA/'cinema_layout_07.json'
TARGET = ROOT/'roxy_cinema_draft7.blend'
for key, folder in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),
                    ('OPTIX_CACHE_PATH','optix'),('BLENDER_USER_CONFIG','config'),
                    ('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts'),
                    ('BLENDER_USER_EXTENSIONS','extensions'),('XDG_CACHE_HOME','xdg')]:
    directory=RUNTIME/folder
    directory.mkdir(parents=True,exist_ok=True)
    os.environ[key]=str(directory)
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
W,H=1920,1080
ZPP=73.48469228349535
PPU=60*math.sqrt(2)
APPROVED=json.loads((QA/'cinema_layout_06.json').read_text(encoding='utf-8'))
ORTHO=APPROVED['camera']['ortho_scale']
K=APPROVED['camera']['k']
OX,OY=APPROVED['camera']['Ox'],APPROVED['camera']['Oy']
U1,V1=APPROVED['room']['u'][1],APPROVED['room']['v'][1]
WALL_Z=APPROVED['room']['wall_top_zpx_world']
SU0,SU1=APPROVED['screen']['u']
SZ0,SZ1=APPROVED['screen']['zpx_world']
RIGHT=Vector((2**-.5,2**-.5,0))
UP=Vector((-math.sqrt(.125),math.sqrt(.125),math.sqrt(.75)))
NORMAL=RIGHT.cross(UP)
SIDE_ROT=Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
RNG=random.Random(341997)
M={}
COLLECTION=None
ROWS=copy.deepcopy(APPROVED['rows'])
for row in ROWS:
    row['floor_zpx']=row['floor_zpx_world']
    row['seat_back_object']='Row '+row['row']+' purple backs - future occluder'
STAIRS=APPROVED['stairs']['treads_v0_v1_zpx_world']
LIVED_IN={'cups':0,'boxes':0}
STEP_DOTS=[]
HELPERS=['xyz','project','collection','register','mesh','box','line','cylinder','text',
         'material','light','join','aged_copy','worn_patch','back_label','tape_patch',
         'point_lamp','cup','carton','pillow','object_tree','top_exposure','screen_check','calibration','hexrgb']
tree=ast.parse((ROOT/'build_cinema_draft4.py').read_text(encoding='utf-8'))
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in HELPERS]
assert len(selected)==len(HELPERS)
exec(compile(ast.Module(body=selected,type_ignores=[]),'draft4_pure_helpers','exec'),globals())


def preservation_snapshot():
    records={}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUNTIME in p.parents:continue
        # Concurrent external log writers are not builder output.
        if p.suffix.lower()=='.log':continue
        st=p.stat()
        records[str(p.relative_to(ROOT.parent))]=[st.st_size,st.st_mtime_ns]
    return records


def configure():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.name='DINK DONK Screen 1 - draft 07 - 30 percent house lights'
    sc.render.engine='CYCLES'
    sc.cycles.samples=384;sc.cycles.use_adaptive_sampling=True
    sc.cycles.adaptive_min_samples=64;sc.cycles.adaptive_threshold=.007
    sc.cycles.use_denoising=True;sc.cycles.seed=341997
    sc.cycles.max_bounces=10;sc.cycles.diffuse_bounces=5;sc.cycles.glossy_bounces=4
    sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
    sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    sc.render.film_transparent=False;sc.render.use_compositing=False;sc.render.use_sequencer=False
    sc.render.use_persistent_data=True;sc.render.filepath=str(IMAGE)
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    sc.view_settings.exposure=0
    world=bpy.data.worlds.new('D7 very low neutral ambient')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.11,.125,.15,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.10
    sc.world=world
    collection('00 Immutable draft6 camera and calibration')
    data=bpy.data.cameras.new('Approved camera 60 0 45 scale32')
    data.type='ORTHO';data.ortho_scale=ORTHO;data.clip_start=.01;data.clip_end=200
    cam=register(bpy.data.objects.new('Camera',data))
    cam.rotation_euler=(math.radians(60),0,math.radians(45))
    cam.location=RIGHT*((960-OX)/(PPU*K))+UP*((OY-540)/(PPU*K))+NORMAL*40
    sc.camera=cam
    prefs=bpy.context.preferences.addons['cycles'].preferences
    device='CPU'
    for backend in ['OPTIX','CUDA']:
        try:
            prefs.compute_device_type=backend;prefs.get_devices()
            found=[d for d in prefs.devices if d.type==backend]
            if found:
                for d in prefs.devices:d.use=d.type==backend
                sc.cycles.device='GPU';device=backend+': '+', '.join(d.name for d in found)
                sc.cycles.denoiser='OPTIX' if backend=='OPTIX' else 'OPENIMAGEDENOISE'
                break
        except Exception:pass
    sc['render_device']=device;sc['brief']='BRIEF-34-cinema-draft7-styled.md'
    sc['house_light_state']='30 percent pre-show, low warm pools'
    print('DEVICE',device,flush=True)
    return sc


def palette():
    entries=[
      ('purple','#4B2A63',.9,0,0),('purple edge','#6A3F8A',.9,0,0),
      ('faded purple','#604474',.95,0,0),('rib teal','#1E3231',.95,0,0),
      ('rib shadow','#152221',.98,0,0),('dado','#1A161D',.94,0,0),
      ('pink trim','#7A5A5E',.84,0,0),('coping','#51434C',.87,0,0),
      ('fixture burgundy','#45212D',.7,.08,0),('ivory core','#F4DDB0',.8,0,.8),
      ('red dot','#D94B32',.7,0,3.8),('exit','#76CB55',.7,0,1.7),
      ('navy carpet','#1E2030',.98,0,0),('carpet wine','#41303E',.98,0,0),
      ('carpet ochre','#524731',.98,0,0),('carpet teal','#2A4141',.98,0,0),
      ('carpet muted','#30303E',.98,0,0),('armrest','#151419',.78,0,0),
      ('speaker cloth','#111315',1,0,0),('champagne','#655D5C',.56,.52,0),
      ('cyan accent','#38C4DA',.8,0,1.1),('ceiling tile','#191C22',.97,0,0),
      ('poster cream','#928571',.98,0,0),('poster rust','#62423F',.98,0,0),
      ('structure','#101219',.94,.08,0),('cut core','#292632',.94,0,0),
      ('mask','#060609',1,0,0),('curtain','#30182B',.97,0,0),
      ('gaffer','#69616D',.95,0,0),('cup cream','#A99D88',.95,0,0),
      ('cup red','#66303C',.98,0,0),('box card','#79604E',.98,0,0),
      ('popcorn','#AA9874',.98,0,0),('coffee stain','#100E15',.85,0,0)]
    for key,h,r,met,em in entries:M[key]=material('D7 '+key+' '+h,hexrgb(h),r,met,em)
    for key in ['purple','faded purple','rib teal','dado','navy carpet','speaker cloth','curtain']:
        M[key]=aged_copy(key,'D7 woven '+key,.90,1.06,7,.0012)
    # Fresnel cloth sheen supplies purple edges, never pale rose replacements.
    for key in ['purple','faded purple']:
        p=M[key].node_tree.nodes.get('Principled BSDF')
        p.inputs['Sheen Weight'].default_value=.32
        p.inputs['Sheen Tint'].default_value=(*hexrgb('#6A3F8A'),1)
        p.inputs['Sheen Roughness'].default_value=.8
    M['seat shell']=aged_copy('purple','D7 deep purple upholstered rear shells',.87,.99,10,.001)
    M['wear']=aged_copy('navy carpet','D7 flattened entrance carpet nap',1.13,1.46,18,.0005)
    M['screen']=material('D7 matte unlit neutral screen ZERO emission',(.33,.335,.33),1)
    p=M['screen'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Specular IOR Level'].default_value=0


def flecks(u0,v0,u1,v1,z,density=13):
    vertices=[];faces=[];indices=[]
    mats=[M['carpet wine'],M['carpet ochre'],M['carpet teal'],M['carpet muted']]
    for i in range(int((u1-u0)*(v1-v0)*density)):
        u=RNG.uniform(u0+.035,u1-.035);v=RNG.uniform(v0+.025,v1-.025)
        width=RNG.uniform(.012,.025);length=RNG.uniform(.035,.085)
        idx=RNG.choices(range(4),[5,1,3,5])[0]
        for aa,bb in [(-length,-length*.15),(length*.17,length*.65)]:
            k=len(vertices)
            vertices.extend(xyz(a,b,z) for a,b in [(u+aa,v-width/2),(u+bb,v-width/2),(u+bb,v+width/2),(u+aa,v+width/2)])
            faces.append((k,k+1,k+2,k+3));indices.append(idx)
    ob=mesh('Quiet low contrast broken woven carpet texture',vertices,faces,mats[0])
    for ma in mats[1:]:ob.data.materials.append(ma)
    for p,idx in zip(ob.data.polygons,indices):p.material_index=idx


def floors():
    collection('01 Exact tier tops - open dark cut structure')
    box('Continuous approved floor slab',0,0,U1,V1,-8,23.8,M['cut core'],.008)
    box('Front and cross aisle carpet',0,0,U1,5.2,23.8,24,M['navy carpet'],.002)
    flecks(.12,.7,U1-.12,5.13,24.035)
    for i,r in enumerate(ROWS[1:]):
        lo=5.2 if i==0 else round(r['v']-.7,2)
        hi=V1 if i==6 else round(r['v']+.7,2)
        z=r['floor_zpx']
        prev=24 if i==0 else ROWS[i]['floor_zpx']
        for a,b in [(0,2.95),(4.0,14.65),(15.65,17.5)]:
            box('Tier '+r['row']+' thin exposed deck',a,lo,b,hi,z-7,z-.15,M['cut core'],.006)
            box('Tier '+r['row']+' carpet top exact elevation',a,lo,b,hi,z-.15,z,M['navy carpet'],.002)
            box('Tier '+r['row']+' dark visible riser',a,lo,b,lo+.055,prev,z-1,M['dado'],.003)
            flecks(a+.08,lo+.06,b-.08,hi-.04,z+.035)
            # Open underside with occasional dark supports, no monolithic block.
            for u in [a+.15,b-.15]:
                box('Dark bank support pier',u-.045,hi-.17,u+.045,hi-.07,24,z-7,M['structure'],.002)
            box('Dark joist below tier',a,hi-.18,b,hi-.08,z-13,z-7,M['structure'],.002)
    for a,b in APPROVED['stairs']['u_ranges']:
        previous=24
        for j,(lo,hi,z) in enumerate(STAIRS):
            box('Exact supported aisle tread '+str(j),a,lo,b,hi,24,z-.12,M['structure'],.002)
            box('Patterned stair carpet',a,lo,b,hi,z-.12,z,M['navy carpet'],.001)
            flecks(a+.09,lo+.025,b-.09,hi-.025,z+.03,12)
            line('Dark dusty tread nosing',[(a+.08,lo+.013,z+.1),(b-.08,lo+.013,z+.1)],M['coping'],.007)
            box('Far stair cheek outside walking lane',a-.06,lo,a,hi,z,z+15,M['dado'],.003)
            box('Far cheek muted coping outside lane',a-.064,lo,a,hi,z+15,z+17,M['coping'],.003)
            box('Low camera side stair cheek outside lane',b,lo,b+.055,hi,z,z+3,M['dado'],.003)
            box('Low dark dusty coping outside lane',b,lo,b+.06,hi,z+3,z+5,M['coping'],.003)
            previous=z
        box('Back aisle landing exact top',a,14.3,b,V1,24,159.85,M['structure'],.003)
        box('Back aisle landing carpet',a,14.3,b,V1,159.85,160,M['navy carpet'],.002)
    for a,b in [(.3,2.95),(4,14.65),(15.65,17.2)]:
        box('Approved cross aisle divider',a,4.9,b,5.0,24,51.8,M['dado'],.004)
        box('Divider subdued dusty coping within same bounds',a,4.9,b,5.0,51.8,53,M['coping'],.003)
    box('Stage within approved footprint',2.8,.10,16.1,.57,24,42.7,M['dado'],.012)
    box('Stage carpet top',2.8,.10,16.1,.57,42.7,43,M['navy carpet'],.002)
    box('Stage recessed footlight lip',2.82,.51,16.08,.565,36,42.5,M['mask'],.005)
    for u in [4.2,7.1,10,12.9,15.2]:
        line('Very low warm stage footlight',[(u-.055,.568,38),(u+.055,.568,38)],M['ivory core'],.009)


def wall_floor(v):
    if v<5.2:return 24
    return next((r['floor_zpx'] for r in ROWS[1:] if r['v']-.7<=v<r['v']+.7),160)


def curtain(u0,u1):
    verts=[];faces=[];count=96
    for i in range(count+1):
        f=i/count;u=u0+(u1-u0)*f;v=.14+.055*math.cos(f*math.tau*8)
        for z in [44+math.sin(f*17)*.7,473]:verts.append(xyz(u,v,z))
    for i in range(count):faces.append((2*i,2*i+1,2*i+3,2*i+2))
    ob=mesh('Open deep plum pleated stage curtain',verts,faces,M['curtain'])
    for p in ob.data.polygons:p.use_smooth=True
    mod=ob.modifiers.new('Velvet thickness','SOLIDIFY');mod.thickness=.012


def walls_screen_passage():
    collection('02 Deep desaturated teal pleats and plum charcoal dado')
    box('Screen wall exact shell',-.12,-.12,U1,-.025,-8,500,M['dado'],0)
    box('Side wall before passage',-.12,0,0,3.7,-8,500,M['dado'],0)
    box('Side wall after passage',-.12,4.6,0,V1,-8,500,M['dado'],0)
    box('Passage lintel exact height',-.12,3.7,0,4.6,152,500,M['dado'],0)
    count=210
    for i in range(count):
        a=i*V1/count;b=(i+1)*V1/count;v=(a+b)/2
        top=112+wall_floor(v)
        bottom=max(top+2,152 if 3.7<v<4.6 else 0)
        box('Vertical acoustic fabric pleat',-.019,a+.004,.032,b-.004,bottom,493,M['rib teal'],.008)
        line('Vertical recessed fabric seam',[(.005,a,bottom),(.005,a,493)],M['rib shadow'],.0025)
    segments=[(0,3.7,136),(4.6,5.2,136)]
    for i,r in enumerate(ROWS[1:]):
        lo=5.2 if i==0 else round(r['v']-.7,2)
        hi=V1 if i==6 else round(r['v']+.7,2)
        segments.append((lo,hi,112+r['floor_zpx']))
    last=None
    for a,b,z in segments:
        line('Stepped muted dusty pink rake trim',[(.046,a,z),(.046,b,z)],M['pink trim'],.012)
        if last and abs(last[1]-a)<.001:
            line('Dusty pink vertical trim riser',[(.046,a,last[2]),(.046,a,z)],M['pink trim'],.012)
        last=(a,b,z)
    for u0,u1 in [(0,2.75),(16.2,U1)]:
        for i in range(int((u1-u0)/.075)):
            a=u0+i*.075
            box('Screen flank fabric pleat',a,-.03,a+.063,-.006,92,493,M['rib teal'],.008)
    screen=mesh('SCREEN clean unchanged 16 by 9 quad',
      [xyz(SU0,0,SZ1),xyz(SU1,0,SZ1),xyz(SU1,0,SZ0),xyz(SU0,0,SZ0)],[(3,2,1,0)],M['screen'])
    for a,b in [(SU0-.10,SU0),(SU1,SU1+.10)]:box('Black vertical screen mask',a,-.018,b,0,83,467,M['mask'],0)
    for a,b in [(83,90),(460,467)]:box('Black horizontal screen mask',SU0,-.018,SU1,0,a,b,M['mask'],0)
    curtain(2.94,4.55);curtain(14.25,15.98)
    box('Recessed EXIT passage floor',-.9,3.7,.12,4.6,20,24,M['navy carpet'],.002)
    box('Recessed rear burgundy fire door',-.9,3.73,-.85,4.57,24,150,M['fixture burgundy'],.005)
    for v in [3.7,4.57]:box('Passage inner dark reveal',-.89,v,.015,v+.03,24,152,M['dado'],.002)
    box('Passage inner roof',-.9,3.7,.015,4.6,152,155,M['dado'],.002)
    line('Exit door push bar',[(-.84,3.86,81),(-.84,4.44,81)],M['champagne'],.012)
    box('English EXIT dark sign exact extents',.015,3.67,.13,4.63,163,182,M['armrest'],.005)
    text('Green EXIT in English','E X I T',.14,4.15,172.5,.18,M['exit'])
    box('DINK DONK plaque approved footprint',.04,1.1,.18,2.4,305,337,M['armrest'],.007)
    text('DINK DONK Screen1 plaque','DINK DONK',.188,1.75,326.5,.147,M['poster cream'])
    text('Screen1 plaque small line','S C R E E N  1',.188,1.75,314.5,.082,M['poster cream'])
    line('One small cyan neon underline',[(.19,1.28,307),(.19,2.22,307)],M['cyan accent'],.009)
    for v,z in [(2.8,265),(7.7,330),(8.35,330)]:
        box('Small high framed poster',.035,v-.20,.09,v+.20,z-18,z+18,M['armrest'],.004)
        box('Muted poster paper',.091,v-.167,.095,v+.167,z-15,z+15,M['poster cream'],.001)
        box('Poster burgundy abstract field',.096,v-.135,.098,v+.04,z-12,z+10,M['fixture burgundy'],0)
        line('Poster teal diagonal',[(.10,v-.12,z-9),(.10,v+.12,z+8)],M['rib teal'],.012)
    return screen


def front_ceiling():
    collection('03 Plain cloth front speaker stacks and ceiling tile strip')
    for u in (3.5,15.3):
        box('Speaker stack exact approved envelope',u-.3,.11,u+.3,.6,43,194,M['armrest'],.018)
        box('Plain cloth speaker grille',u-.276,.598,u+.276,.604,48,189,M['speaker cloth'],.005)
        box('Small subdued speaker maker tab',u-.055,.605,u+.055,.607,49,51,M['champagne'],.001)
    # All ceiling details fit below the retained 500-unit wall tops.
    for u in [i*.72 for i in range(25) if i*.72<U1]:
        box('Charcoal ceiling strip tile',u,.015,min(u+.70,U1),.25,491,497,M['ceiling tile'],.003)
    for v in [i*.72 for i in range(21) if i*.72<V1]:
        box('Side ceiling strip tile',.015,v,.25,min(v+.70,V1),491,497,M['ceiling tile'],.003)
    line('Screen cornice recessed edge',[(0,.255,493),(U1,.255,493)],M['structure'],.012)
    line('Side cornice recessed edge',[(.255,0,493),(.255,V1,493)],M['structure'],.012)
    for u in [2.1,7.7,12.2,16.8]:
        cylinder('Small round recessed downlight bezel',u,.145,489.8,.065,.024,M['armrest'],count=20)
        cylinder('Dim round ceiling lens',u,.145,488.8,.041,.009,M['ivory core'],count=20)
    for v in [5.4,10.7,14.3]:
        cylinder('Small side ceiling downlight',.14,v,489,.05,.009,M['ivory core'],count=20)


def seats():
    for row in ROWS:
        collection('04 Row '+row['row']+' deep velvet purple')
        v=row['v'];z=row['floor_zpx'];backs=[]
        for j,u in enumerate(row['seat_u']):
            tag='%s%02d'%(row['row'],j+1);prefix='Seat '+tag
            cloth=M['faded purple'] if tag=='G11' else M['purple']
            box(prefix+' low dark pedestal',u-.12,v-.10,u+.12,v+.14,z+1,z+7,M['armrest'],.018)
            for du in [-.23,.23]:
                box(prefix+' pivot support',u+du-.023,v+.04,u+du+.023,v+.16,z+6,z+37,M['armrest'],.008)
                cylinder(prefix+' subdued hinge',u+du,v+.08,z+27,.035,.014,M['champagne'],axis=(1,0,0),count=12)
            box(prefix+' thick rounded velvet cushion',u-.245,v-.25,u+.245,v+.17,z+26,z+36,cloth,.045)
            shell=M['faded purple'] if tag=='G11' else M['seat shell']
            backs.append(pillow(prefix+' high rounded upholstered back',u,v+.23,z+26,.58,36,.12,shell))
            backs.append(pillow(prefix+' soft front pad',u,v+.165,z+29,.51,31,.07,cloth))
            seam=[(u+.25*math.cos(math.pi*k/32),v+.291,z+38+18*math.sin(math.pi*k/32)) for k in range(33)]
            backs.append(line(prefix+' quiet shoulder seam',seam,M['dado'],.002))
            backs.append(box(prefix+' rear small number tab',u-.052,v+.292,u+.052,v+.295,z+35,z+38,M['champagne'],.001))
            backs.append(back_label(tag,u,v+.296,z+36.5))
            if tag=='H06':
                backs.append(tape_patch(prefix+' broad frayed gaffer repair',u,v+.293,z+34))
            for du in [-.263,.263]:
                box(prefix+' padded dark armrest',u+du-.026,v-.22,u+du+.026,v+.19,z+37,z+42,M['armrest'],.021)
                cylinder(prefix+' recessed cupholder',u+du,v-.13,z+42,.022,.008,M['mask'],count=16)
                line(prefix+' cupholder molded lip',[(u+du+.024*math.cos(k*math.tau/20),v-.13+.024*math.sin(k*math.tau/20),z+42.2) for k in range(20)],M['armrest'],.004,True)
        ob=join(backs,row['seat_back_object']);ob['future_occluder']=True;ob['row_id']=row['row']


def route_samples():
    points=[]
    route=APPROVED['walk_route']['passage_to_back_row']
    for a,b in zip(route,route[1:]):
        for i in range(8):points.append([a[j]+(b[j]-a[j])*i/8 for j in range(3)])
    return points+[route[-1]]


def dot_conflicts(point):
    x,y=project(*point)
    return [p for p in all_walking_samples() if abs(x-project(*p)[0])<37*K and project(*p)[1]-50*K<y<project(*p)[1]-22.5*K]


def all_walking_samples():
    paths=[APPROVED['walk_route']['passage_to_back_row'],APPROVED['walk_route']['front_branch'],APPROVED['walk_route']['right_aisle_connection']]
    paths.append([[15.15,p[1],p[2]] for p in APPROVED['walk_route']['passage_to_back_row'] if p[0]==3.475 and p[1]>=4.5])
    for row in APPROVED['walk_route']['row_branches']:
        for key in ['points','left_points','right_points']:
            if row[key]:paths.append(row[key])
    samples=[]
    for path in paths:
        for a,b in zip(path,path[1:]):
            for i in range(8):samples.append([a[j]+(b[j]-a[j])*i/8 for j in range(3)])
        samples.append(path[-1])
    return samples


def fixtures_lighting():
    collection('05 Dim burgundy sconces, compact surrounds and warm pools')
    for v,z in [(1.2,390),(5.65,397),(10.1,426),(13.7,440)]:
        box('Tall narrow burgundy sconce',.035,v-.09,.125,v+.09,z-39,z+39,M['fixture burgundy'],.016)
        box('Dim soft ivory sconce core',.127,v-.035,.17,v+.035,z-33,z+33,M['ivory core'],.013)
        point_lamp('Warm isolated sconce pool',(.29,v,z+8),12,(1,.72,.46),.22)
        light('Soft narrow pleat wash',(.35,v,z+25),(.025,v,z+67),7,(1,.79,.59),.36,.18)
    for v,z in [(3.0,405),(7.25,423),(11.9,447)]:
        box('Compact black wall surround',.02,v-.17,.24,v+.17,z-15,z+15,M['armrest'],.012)
        box('Compact surround cloth front',.241,v-.143,.247,v+.143,z-12,z+12,M['speaker cloth'],.004)
    collection('06 Thirty percent pre show house pools')
    for u,v,power in [(5.7,3.2,100),(12.2,3.1,105),(16.7,3.4,65),
                      (5.5,7,105),(11.8,7.2,108),(16.7,8,65),
                      (1.4,11.4,75),(6.8,12.4,100),(13.1,12.3,95),(17,13.4,55)]:
        light('Low warm seating pool',(u,v,478),(u,v,wall_floor(v)+25),power,(1,.87,.78),2.3,1.7)
    light('Subtle cool velvet edge bounce',(16,12,410),(9,9,110),65,(.65,.69,.89),5,4)
    light('Dim readable open arrival landing',(1.6,6.8,305),(1.6,6.4,64),28,(1,.79,.61),2.1,1.7)
    light('Dim warm passage mouth',(1.1,4.15,245),(.5,4.15,24),19,(1,.73,.49),1,.75)
    light('Dim warm recessed passage',(-.3,4.15,145),(-.2,4.15,24),4,(1,.64,.37),.35,.35)
    collection('07 Tubular rails and rhythmic red orange safety dots')
    for a,b in APPROVED['stairs']['u_ranges']:
        rail=[]
        for i,(lo,hi,z) in enumerate(STAIRS):
            rail.extend([(a-.03,lo+.025,z+30),(a-.03,hi-.025,z+30)])
            if i%3==0:line('Sparse dark metal rail upright',[(a-.03,lo+.10,z+17),(a-.03,lo+.10,z+30)],M['champagne'],.010)
        line('Simple tubular handrail',rail,M['champagne'],.015)
        previous=24
        for i,(lo,hi,z) in enumerate(STAIRS):
            rise=z-previous;previous=z
            # Two small riser-end lights. Only candidates outside every sampled
            # route face envelope survive; removed positions are documented.
            for u in [a+.085,b-.085]:
                point=[u,lo-.012,z-rise*.52]
                if dot_conflicts(point):continue
                cylinder('Distinct red orange stair riser dot',*point,.025,.012,M['red dot'],axis=(0,-1,0),count=16)
                STEP_DOTS.append(point)
        # A parallel low cheek-end rhythm is outside the head-passing corridor.
    for v in [3.78,4.03,4.28,4.53]:
        point=[.07,v,27]
        if not dot_conflicts(point):
            cylinder('Passage low red marker',*point,.022,.012,M['red dot'],axis=(1,0,0),count=16)
            STEP_DOTS.append(point)


def wear():
    collection('08 Five subdued lived in clusters')
    worn_patch('Entrance ragged flattened carpet traffic',.08,3.82,1.65,4.48,24.06,M['wear'])
    worn_patch('Arrival carpet traffic continuation',1.0,5.35,2.1,6.6,64.06,M['wear'])
    # The spill is beside D01, on its tier, clear of the actual stair lane.
    u,v,z=4.15,7.02,80
    stain=[xyz(u+.20*math.cos(i*math.tau/23)*RNG.uniform(.75,1.1),v+.13*math.sin(i*math.tau/23)*RNG.uniform(.75,1.1),z+.10) for i in range(23)]
    mesh('D01 small dark soda spill',stain,[tuple(range(23))],M['coffee stain'])
    verts=[];faces=[]
    for i in range(22):
        c=xyz(u+RNG.uniform(-.16,.16),v+RNG.uniform(-.10,.10),z+1)
        r=RNG.uniform(.018,.032);k=len(verts)
        verts.extend([c+Vector((r,0,0)),c+Vector((0,r,0)),c+Vector((-r,0,0)),c+Vector((0,-r,0)),c+Vector((0,0,r))])
        faces.extend(tuple(k+j for j in f) for f in [(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
    mesh('D01 clustered popcorn spill',verts,faces,M['popcorn'])
    cup(4.17,6.89,80.2,True)
    carton(10.9,3.52,24.2)


def screen_lighting(sc,screen):
    room=bpy.data.collections.new('Receivers - room excluding matte screen')
    screen_only=bpy.data.collections.new('Receiver - screen only')
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:(screen_only if ob==screen else room).objects.link(ob)
    for ob in sc.objects:
        if ob.type=='LIGHT':ob.light_linking.receiver_collection=room
    # Smooth diffuse ambient spill, no projection, emission, or focused light.
    collection('09 Smooth neutral ambient spill onto matte screen')
    fill=light('Broad dim indirect screen ambient',(9.4,7,350),(9.4,0,290),175,(.94,.96,1),15,12)
    fill.light_linking.receiver_collection=screen_only


def audience_checks():
    results=[];face_rows=[]
    for row in ROWS:
        own,_=object_tree([bpy.data.objects[row['seat_back_object']]])
        nearer=[bpy.data.objects[r['seat_back_object']] for r in ROWS if r['v']>row['v']]
        near,_=object_tree(nearer) if nearer else (None,None)
        group=[]
        for j,u in enumerate(row['seat_u']):
            anchor=xyz(u,row['v'],row['floor_zpx']+36)
            item={'seat':'%s%02d'%(row['row'],j+1),'row':row['row'],'u':u,'v':row['v'],
                  'floor_zpx_world':row['floor_zpx'],'anchor_zpx_world':row['floor_zpx']+36,
                  'own_back_visible_fraction':top_exposure(own,anchor),
                  'all_geometry_visible_fraction':top_exposure(SCENE_BVH,anchor),
                  'face_core_visible_fraction':min(top_exposure(SCENE_BVH,anchor,x) for x in [-11.1,0,11.1]),
                  'nearer_rows_only_visible_fraction':top_exposure(near,anchor) if near else 1.0,
                  'screen_clearance_px':K*(60*row['v']+90-row['floor_zpx']-36-50-18.5)}
            group.append(item);results.append(item)
        info={'row':row['row']}
        for key in ['own_back_visible_fraction','all_geometry_visible_fraction','face_core_visible_fraction','nearer_rows_only_visible_fraction']:
            info[key+'_min']=min(p[key] for p in group)
        info['own_back_visible_fraction_max']=max(p['own_back_visible_fraction'] for p in group)
        info['exposed_height_px_min']=min(p['all_geometry_visible_fraction'] for p in group)*50*K
        info['screen_clearance_px_min']=min(p['screen_clearance_px'] for p in group)
        face_rows.append(info)
    return {'emote_height_px':50*K,'emote_max_width_px':74*K,'anchor':'floor +36 zpx_world',
            'method':'400 vertical orthographic rays from envelope top at centre and face-core x=-11.1,0,+11.1 lobby px; all evaluated styled geometry; own backs and all nearer row backs separately. Numeric emote envelope, no page artwork.',
            'per_row_visible_face_fraction':face_rows,'seats':results,'seats_checked':len(results),
            'minimum_screen_clearance_px':min(p['screen_clearance_px'] for p in results)}


def composition_route():
    pixels=[project(p.x,-p.y,p.z*ZPP) for p in SCENE_VERTS]
    bounds=[min(p[0] for p in pixels),min(p[1] for p in pixels),max(p[0] for p in pixels),max(p[1] for p in pixels)]
    # Approved blockout backs as analytic boxes, without mutating the scene.
    bv=[];bf=[]
    for row in ROWS:
        for u in row['seat_u']:
            v=row['v'];z=row['floor_zpx'];k=len(bv)
            bv.extend(xyz(a,b,c) for a,b,c in [(u-.29,v+.18,z+26),(u-.29,v+.18,z+62),(u-.29,v+.29,z+26),(u-.29,v+.29,z+62),(u+.29,v+.18,z+26),(u+.29,v+.18,z+62),(u+.29,v+.29,z+26),(u+.29,v+.29,z+62)])
            bf.extend(tuple(k+i for i in face) for face in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)])
    blockout_backs=BVHTree.FromPolygons(bv,bf,all_triangles=False)
    samples=[]
    for p in route_samples():
        anchor=xyz(*p)
        frac=min(top_exposure(SCENE_BVH,anchor,x) for x in [-11.1,0,11.1])
        blockers=[]
        if frac<.55:
            for dx in [-11.1,0,11.1]:
                f=top_exposure(SCENE_BVH,anchor,dx)
                if f<.55:
                    q=anchor+RIGHT*(dx/PPU)+UP*((50*(1-f)-.08)/PPU)
                    hit=SCENE_BVH.ray_cast(q+NORMAL*45,-NORMAL,44.9995)
                    if hit[2] is not None:blockers.append(SCENE_OWNERS[hit[2]])
        base=min(top_exposure(blockout_backs,anchor,x) for x in [-11.1,0,11.1])
        samples.append({'uvzpx':p,'pixel_floor':project(*p),'visible_top_fraction':frac,'blockers_below55pct':blockers,'approved_blockout_backs_only_visible_fraction':base})
    conflicts=[{'dot':dot,'walker':p} for dot in STEP_DOTS for p in dot_conflicts(dot)]
    return {'geometry_bounds_px':bounds,'margins_px':[bounds[0],bounds[1],W-bounds[2],H-bounds[3]],
            'route_samples':samples,'minimum_route_face_core_visible_fraction':min(p['visible_top_fraction'] for p in samples),
            'minimum_in_hall_route_face_core_visible_fraction':min(p['visible_top_fraction'] for p in samples if p['uvzpx'][0]>=0),
            'minimum_approved_blockout_backs_only_fraction_on_in_hall_route':min(p['approved_blockout_backs_only_visible_fraction'] for p in samples if p['uvzpx'][0]>=0),
            'route_limit':'Recessed spawn is hidden by retained wall/reveal; some starter-stair face cores overlap the fixed row-C backs. Both are reported; no approved seat or route moved.',
            'safety_dot_walk_sample_count':len(all_walking_samples()),
            'bright_step_dot_conflicts_with_main_route_upper55pct':conflicts,'step_dots':STEP_DOTS}


def make_data(sc,cal,visibility,audience,composition):
    data=copy.deepcopy(APPROVED)
    data['brief']='BRIEF-34-cinema-draft7-styled.md'
    data['approved_layout_source']='qa11/cinema_layout_06.json'
    data['layout_lock']={'passed':True,'seat_count':135,'seat_centres_changed':0,'tier_tops_changed':0,
        'screen_corners_changed':0,'camera_changed':False,'aisle_or_route_points_changed':0,
        'seat_footprint_note':'Backs and cushions stay within approved u +/-0.29 and v [-0.25,+0.29]. Seams, labels and repair are at v+0.291 to +0.296 (maximum 0.006 tile detail overhang); armrests fit original footprint. No walking lane changes.',
        'other_detail_footprint_changes':'Acoustic pleats project 0.032 tile into hall; ceiling strip projects 0.25 tile at z491-497; curtain folds v0.085-0.195 outside screen; speaker cloth grille +0.007 tile at v0.607. Stair cheeks/coping project at most0.064 tile outside the aisle, into existing seat-side gaps; full approved aisle widths retained. No seats, aisles, screen or route moved.',
        'cut_section':'Original walking surfaces and slab retained; solid bank infill replaced by 7-unit decks, riser fascias, dark joists and support piers.'}
    data['calibration']=cal;data['screen_visibility']=visibility
    data['audience_check']=audience;data['composition_and_route']=composition
    data['style']={'house_lights':'30 percent before show; low warm pools, dark between fixtures',
        'palette_srgb':{'walls':'#1E3231','dado':'#1A161D','trim':'#7A5A5E','seat_base':'#4B2A63','seat_sheen':'#6A3F8A','carpet':'#1E2030','step_dots':'#D94B32'},
        'photos_used':{'02':'Vertical teal fabric pleats, stepped dusty trim, burgundy ivory sconces, compact black surrounds and small frames.',
                       '03':'Recessed exit passage, dark stair cheeks, simple rail and low red markers. Owner overrides Spanish sign and pale coping.',
                       '04 and 05':'Soft high purple velvet backs, dark arms/cupholders, patterned carpet and discrete riser lights. Owner excludes orange/pink seats.',
                       '01 and 06':'Only one small cyan neon underline on DINK DONK Screen 1 plaque.',
                       '05 and 07':'Shallow charcoal ceiling tile strip with small round downlights; multiplex context.'},
        'wear_clusters':[{'name':'entrance and arrival traffic','location':'u0.08-2.1, passage and blank arrival carpet'},
                         {'name':'soda and popcorn spill plus tipped cup','location':'beside D01, u4.15 v7.02 z80'},
                         {'name':'taped upholstery','seat':'H06'}, {'name':'faded purple upholstery','seat':'G11'},
                         {'name':'discarded open popcorn carton','uvzpx':[10.9,3.52,24.2]}]}
    data['render']={'engine':'Cycles','samples_max':384,'adaptive_min':64,'adaptive_threshold':.007,'denoising':True,
        'device':sc['render_device'],'count':0,'resolution':[W,H],'blender_version':bpy.app.version_string,
        'image':'qa11/cinema_draft_07.png','blend':'roxy_cinema_draft7.blend'}
    data['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'build_cinema_draft4.py',ROOT/'build_cinema_draft6_blockout.py',QA/'cinema_layout_06.json',ROOT/'BRIEF-34-cinema-draft7-styled.md']}
    data['limitations']=['Numeric 50k by74k emote envelope; no emote artwork or live page test.',
        'Single pre-show still; no separate dark state, layers, loop or 4K render. 4K screen corners are computed.',
        'Route check reports occlusion of the approved route, including the physically recessed passage; not accessibility or building-code validation.']
    return data


def delivered_png_rgb(path):
    """Decode saved RGB8 PNG bytes without Blender image color interpretation."""
    raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    pos=8;parts=[]
    while pos<len(raw):
        size=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8]
        payload=raw[pos+8:pos+8+size]
        if kind==b'IHDR':
            w,h,depth,color,_,_,interlace=struct.unpack('>IIBBBBB',payload)
            assert (w,h,depth,color,interlace)==(W,H,8,2,0)
        if kind==b'IDAT':parts.append(payload)
        pos+=size+12
    stream=zlib.decompress(b''.join(parts));stride=W*3
    pixels=bytearray(W*H*3)
    for y in range(H):
        filt=stream[y*(stride+1)];scan=stream[y*(stride+1)+1:(y+1)*(stride+1)]
        base=y*stride
        for x,value in enumerate(scan):
            a=pixels[base+x-3] if x>=3 else 0
            b=pixels[base+x-stride] if y else 0
            c=pixels[base+x-stride-3] if y and x>=3 else 0
            p=a+b-c;aa=abs(p-a);bb=abs(p-b);cc=abs(p-c)
            paeth=a if aa<=bb and aa<=cc else b if bb<=cc else c
            pred=0 if filt==0 else a if filt==1 else b if filt==2 else (a+b)//2 if filt==3 else paeth
            pixels[base+x]=(value+pred)&255
    return pixels


def seat_back_luminance(sc):
    pix=delivered_png_rgb(IMAGE);values=[];per_row={r['row']:[] for r in ROWS}
    for y in range(0,H,2):
        for x in range(0,W,2):
            origin=sc.camera.location-NORMAL*2+RIGHT*((x+.5-W/2)*ORTHO/W)+UP*((H/2-y-.5)*ORTHO/W)
            hit=SCENE_BVH.ray_cast(origin,-NORMAL,100)
            if hit[2] is None:continue
            name=SCENE_OWNERS[hit[2]]
            row=next((r['row'] for r in ROWS if r['seat_back_object']==name),None)
            if row is None:continue
            i=(y*W+x)*3
            rgb=pix[i:i+3]
            lum=sum(c*w for c,w in zip(rgb,[.2126,.7152,.0722]))
            values.append(lum);per_row[row].append(lum)
    assert values
    values.sort()
    result={'method':'Direct delivered PNG RGB8 bytes without color re-encoding; Rec709 weighted display sRGB. Every second pixel in x/y whose first evaluated camera ray hits a row back mesh; excludes carpet and screen. Includes back seams, number tabs and H06 tape.',
        'samples':len(values),'mean_display_luminance_0_255':sum(values)/len(values),
        'median_display_luminance_0_255':values[len(values)//2],
        'p10_p90_display_luminance_0_255':[values[len(values)//10],values[int(len(values)*.9)]],
        'per_row_mean_display_luminance_0_255':{r:sum(v)/len(v) for r,v in per_row.items() if v}}
    return result


def write_report(data):
    a=data['audience_check'];c=data['composition_and_route'];r=data['render']
    table='\n'.join('| {row} | {own_back_visible_fraction_min:.2%} | {all_geometry_visible_fraction_min:.2%} | {face_core_visible_fraction_min:.2%} | {nearer_rows_only_visible_fraction_min:.2%} | {exposed_height_px_min:.3f} | {screen_clearance_px_min:.3f} |'.format(**p) for p in a['per_row_visible_face_fraction'])
    corners='\n'.join('| '+n+' | '+str(data['screen']['corners_1920x1080'][n])+' | '+str(data['screen']['corners_3840x2160'][n])+' |' for n in ['TL','TR','BR','BL'])
    routes='\n'.join('- `'+str(p)+'`' for p in data['walk_route']['passage_to_back_row'])
    textout=f'''# Cinema draft 07 — styled approved blockout v2

One 1920×1080 Cycles image. **135 purple seats**, exactly the approved B–I positions: front B 3/13/2, bank C–E 0/13/2, F–I 3/13/2. Camera `(60,0,45)`, ortho scale **32**, origin **(890,370)**, k `{K:.12f}`. Hall u 0–17.5 / v 0–14.9; both retained walls top 500. Bank pitch 1.4 / rise 16, floors 64–160. All seat centres, floor tops, aisle boundaries, screen corners and route points are copied from `cinema_layout_06.json` and checked unchanged.

## Styling and photo interpretation

Low pre-show house light, approximately 30% intent: warm pools at burgundy/ivory wall sconces, dark fabric between them, deep desaturated teal `#1E3231`, plum charcoal dado `#1A161D`, muted stepped pink trim `#7A5A5E`. Purple velvet base `#4B2A63` with `#6A3F8A` sheen, rounded high backs, dark armrests and cupholders; G11 is faded purple. No orange or rose seating. Dark navy patterned carpet uses small, quiet wine/ochre/teal broken flecks. Coping is dark dusty plum, with sparse tubular rails and distinct red-orange riser dots.

Photo02 supplies acoustic pleats, stepped dado, sconces, compact surrounds and small framed posters. Photo03 supplies the recessed exit, dark stair cheeks and safety-light rhythm; the owner's **English EXIT** and dark coping override its SALIDA and cream rail. Photos04/05 supply purple upholstery, soft silhouettes, dark arms/cupholders and stair carpet. Photos01/06 contribute only the small cyan underline to the DINK DONK / Screen1 plaque. Photos05/07 inform the shallow charcoal acoustic ceiling strip and small round downlights. Deep plum curtains, stage footlight lip and plain cloth-front stacks stay outside the screen quad.

Cut bank: original floor tops remain fixed; thin stepped decks, riser fascias, dark joists and piers replace the tall flat grey mass. Five wear clusters: broken entrance/arrival carpet traffic; small D01 soda/popcorn spill with tipped cup; H06 taped back; G11 faded purple back; open carton at `(10.9,3.52,24.2)`. These remain below the emote face area.

## Calibration and screen

Five non-rendering markers: maximum axis error **{data['calibration']['max_axis_error_px']:.9f}px**, PASS ±1px. Evaluated geometry bounds L/T/R/B `{[round(x,3) for x in c['geometry_bounds_px']]}`. All camera values match draft6. Projection `P=[890+(u-v)60k,370+((u+v)30-zpx_world)k]`; world `(u,-v,zpx_world/{ZPP})`.

Unchanged physical16:9 quad: u `{SU0:.12f}–{SU1:.12f}`, v0, z90–460. Matte, zero emission and zero specular; local lamps exclude it. A broad dim neutral ambient source gives a smooth unprojected surface, no image or hotspot. Visibility: **{data['screen_visibility']['rays']:,} evaluated-geometry rays, zero blockers**, every interior image pixel plus inset perimeter.

| Corner | 1920×1080 | 3840×2160 calculated |
|---|---|---|
{corners}

## Face clearance and row separation

Envelope 35.355 px high (`50k`) by 52.326 px wide (`74k`), bottom anchor floor+36. There are 400 samples from the top per vertical ray column; centre and three face-core columns, own rounded back, all scene geometry and nearer-row backs separately. No unavailable seat exceptions.

| Row | Own back min | All geometry min | Face core min | Nearer rows min | Exposed height px | Screen clearance px |
|---|---:|---:|---:|---:|---:|---:|
{table}

Minimum extended lower-screen clearance **{a['minimum_screen_clearance_px']:.6f}px**, formula `k*(60v+90-floor-36-50-18.5)`. Row-line separation remains **88.544px B–C**, **43.007px C–I**, all above25px; same `k*abs(2dz-120dv)/sqrt(5)` check as draft6.

## Approved route and footprints

Cross-aisle v3.2–5.2, divider v4.9–5.0, open arrival u0–2.95/v5.2–9.4. Left stairs u2.95–4.0; right stairs u14.65–15.65. Four10-unit starter treads, then twelve8-unit treads; last landing z160. Front gap v0.57–2.65 stays2.08 tiles. All branch and right-aisle connection points remain in JSON.

Approved passage-to-back points (u,v,zpx_world):
{routes}

Route visibility: **{len(c['route_samples'])} positions**, three face-core columns /400 samples. Whole-route minimum **{c['minimum_route_face_core_visible_fraction']:.2%}** at the recessed spawn, occluded by the retained side wall/reveal. In-hall minimum **{c['minimum_in_hall_route_face_core_visible_fraction']:.2%}** on the starter stairs, where the fixed row-C backs cross the walker face core in projection. The original blockout backs alone have a minimum **{c['minimum_approved_blockout_backs_only_fraction_on_in_hall_route']:.2%}** on this same route. This is a known visibility limit of the locked layout, not a full55% route pass; no seats or route moved to conceal it. JSON records every sample and blocker.

Bright step-dot centres inside upper55% walking envelopes: **{len(c['bright_step_dot_conflicts_with_main_route_upper55pct'])}**, across **{c['safety_dot_walk_sample_count']}** positions covering both stairs, cross-aisle, front branch and row-entry branches. Total red markers: **{len(c['step_dots'])}**; conflicting candidates were omitted. This is a geometric check, not page/emote-art or physical accessibility acceptance.

Seat silhouettes/cushions remain inside approved width±0.29 and depth[-0.25,+0.29]; seams, labels and tape project at most**0.006 tile** beyond the rear footprint. Acoustic pleats add0.032 tile wall depth; ceiling strip projects0.25 tile at z491–497; curtain folds v0.085–0.195, outside the screen; speaker cloth adds0.007 tile. Dark cheeks/coping project at most0.064 tile outside aisle boundaries, within existing seat-side gaps; rail is on the far cheek. The full1.05/1.00-tile aisle widths stay clear. No seat, screen, aisle or route was moved.

## Darkness, render and preservation

Seat-back image luminance (display sRGB, Rec709 weights): mean **{data['seat_back_luminance']['mean_display_luminance_0_255']:.2f}/255**, median **{data['seat_back_luminance']['median_display_luminance_0_255']:.2f}/255**, p10/p90 **{[round(v,2) for v in data['seat_back_luminance']['p10_p90_display_luminance_0_255']]}**, from {data['seat_back_luminance']['samples']:,} first-hit back pixels at 2 px sampling. Per-row values and method in JSON; this is a delivered-image metric for tuning, not the material hex value.

Blender {r['blender_version']}, Cycles 64–384 / adaptive 0.007, denoise, **{r['device']}**. Build/checks {r['build_checks_seconds']:.2f}s; one render **{r['seconds']:.2f}s**. PNG SHA256 `{r['image_sha256']}`. Single image, one render start/completion. New blend saved once without backups.

Preservation: **{data['preservation']['existing_roxy3d_files_checked']} existing roxy3d files** unchanged by size/nanosecond mtime; pages checked separately. Original baseline retained in runtime07. Existing blends, earlier drafts, cloud bundle and out10 untouched. All explicit output/cache paths inside new draft7 paths under roxy3d. Draft4 reuse is limited to selected pure helper functions read via AST; its module/main are never executed and no old blend is opened. No pages or cloud state were written.

No extra beauty still, audience artwork, live page/zoom test, alternate dim state, layers, sprites, loops or4K rendering. STOP.
'''
    with REPORT.open('x',encoding='utf-8') as f:f.write(textout)


def main():
    started=time.perf_counter()
    preflight='--preflight' in sys.argv
    for p in [IMAGE,REPORT,LAYOUT,TARGET,RUNTIME/'render_started']:
        assert not p.exists(),'New-file / one-image guard: '+str(p)
    before=preservation_snapshot()
    baseline=RUNTIME/'preservation_before.json'
    if baseline.exists():
        old=json.loads(baseline.read_text(encoding='utf-8'))
        changed=[p for p,st in old.items() if before.get(p)!=st and p not in ['roxy3d\\build_cinema_draft7.py','roxy3d/build_cinema_draft7.py']]
        assert not changed,changed
    else:
        with baseline.open('x',encoding='utf-8') as f:json.dump(before,f)
    sc=configure();palette();floors();screen=walls_screen_passage();front_ceiling();seats();fixtures_lighting();wear();screen_lighting(sc,screen)
    collection('00 Calibration marker empties')
    cal=calibration(sc);visibility=screen_check(sc,screen);audience=audience_checks();composition=composition_route()
    data=make_data(sc,cal,visibility,audience,composition)
    # Exact layout verification, independent of visual/material treatment.
    for key in ['camera','rows','row_pairs','aisles','stairs','screen','walk_route','total_seats']:
        assert data[key]==APPROVED[key],key
    assert min(composition['margins_px'])>=8,composition['margins_px']
    assert all(r['all_geometry_visible_fraction_min']>=.55 and r['face_core_visible_fraction_min']>=.55 for r in audience['per_row_visible_face_fraction']),audience['per_row_visible_face_fraction']
    assert not composition['bright_step_dot_conflicts_with_main_route_upper55pct'],composition['bright_step_dot_conflicts_with_main_route_upper55pct'][:5]
    print('PREFLIGHT',json.dumps({'calibration':cal['max_axis_error_px'],'screen_rays':visibility['rays'],
       'face_rows':audience['per_row_visible_face_fraction'],'route_min':composition['minimum_route_face_core_visible_fraction'],
       'bounds':composition['geometry_bounds_px'],'dot_count':len(STEP_DOTS),'object_count':len(sc.objects)}),flush=True)
    print('ROUTE_LOW',json.dumps([p for p in composition['route_samples'] if p['visible_top_fraction']<.55]),flush=True)
    if preflight:
        p=RUNTIME/('preflight_%02d.json'%(1+len(list(RUNTIME.glob('preflight_*.json')))))
        with p.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
        print('PREFLIGHT COMPLETE - no image and no blend saved',flush=True);return
    bpy.context.preferences.filepaths.save_version=0
    sc['layout_contract']=json.dumps(data);sc['draft_only']=True
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    with (RUNTIME/'render_started').open('x',encoding='utf-8') as f:f.write('One image authorized by Brief34. Do not render another.\n')
    built=time.perf_counter();print('DRAFT07_SINGLE_RENDER_START',flush=True)
    bpy.ops.render.render(write_still=True)
    ended=time.perf_counter()
    data['render'].update(count=1,seconds=ended-built,build_checks_seconds=built-started,total_seconds=ended-started,
        image_sha256=hashlib.sha256(IMAGE.read_bytes()).hexdigest())
    data['seat_back_luminance']=seat_back_luminance(sc)
    after=preservation_snapshot()
    changed=[p for p,st in before.items() if after.get(p)!=st]
    inside=[p for p in changed if p.startswith(('roxy3d\\','roxy3d/'))]
    assert not inside,inside
    pages=[p for p in changed if p.endswith(('.html','.htm'))]
    assert not pages,pages
    data['preservation']={'passed':True,'existing_roxy3d_files_checked':sum(p.startswith(('roxy3d\\','roxy3d/')) for p in before),
        'existing_pages_checked':sum(p.endswith(('.html','.htm')) for p in before),
        'unrelated_workspace_changes':changed,'method':'Before/after file sizes and nanosecond mtimes; active logs excluded. runtime07 baseline retained. All builder writes restricted to new roxy3d draft7 files.'}
    with LAYOUT.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')
    write_report(data)
    print('DRAFT07_SINGLE_RENDER_COMPLETE',flush=True)
    print('STATUS: DRAFT 07 COMPLETE | one 1920x1080 image | report + JSON | STOP',flush=True)


if __name__=='__main__':main()
