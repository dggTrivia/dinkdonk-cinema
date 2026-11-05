"""Brief 32: one quick Workbench layout still, new files only; no blend save."""
import sys
sys.dont_write_bytecode = True
import os, json, math, time, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUN = QA/'runtime05'
IMAGE = QA/'cinema_draft_05_blockout.png'
REPORT = QA/'CINEMA-DRAFT-05.md'
LAYOUT = QA/'cinema_layout_05.json'
for p in (IMAGE, REPORT, LAYOUT, RUN/'render_started'):
    assert not p.exists(), f'New-file guard: {p}'
RUN.mkdir(exist_ok=True)
for key in ('TEMP','TMP','CUDA_CACHE_PATH','OPTIX_CACHE_PATH','BLENDER_USER_CONFIG','BLENDER_USER_DATAFILES','BLENDER_USER_SCRIPTS'):
    folder = RUN/key.lower()
    folder.mkdir(exist_ok=True)
    os.environ[key] = str(folder)
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

T = time.perf_counter()
W,H = 1920,1080
K = 22.627416998/30
OX,OY = 800,548
ZPP = 73.48469228349535
RIGHT = Vector((2**-.5,2**-.5,0))
UP = Vector((-math.sqrt(.125),math.sqrt(.125),math.sqrt(.75)))
NORMAL = RIGHT.cross(UP)
COLORS = {'wall':(.095,.105,.12,1),'floor':(.33,.35,.38,1),
          'stairs':(.68,.71,.75,1),'seat':(.31,.075,.57,1),
          'screen':(.95,.95,.95,1),'stage':(.30,.14,.055,1),
          'divider':(.28,.025,.045,1),'black':(.009,.012,.016,1),
          'exit':(.03,.6,.16,1),'plaque':(.02,.65,.78,1),
          'light':(.68,.64,.43,1),'ink':(.82,.88,.94,1),'route':(1,.67,.07,1)}

def snapshot():
    # Read-only metadata baseline for every existing workspace file, except active runtime logs.
    result={}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUN in p.parents or p == Path(__file__).resolve(): continue
        if p.suffix.lower()=='.log': continue
        st=p.stat()
        result[str(p.relative_to(ROOT.parent))]=[st.st_size,st.st_mtime_ns]
    return result

before=snapshot()
(RUN/'preservation_before.json').write_text(json.dumps(before),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
sc.render.film_transparent=False
sc.render.filepath=str(IMAGE)
sc.display.shading.light='STUDIO'
sc.display.shading.studiolight_rotate_z=.4
sc.display.shading.color_type='OBJECT'
sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True
sc.display.shading.cavity_type='WORLD'
sc.display.shading.curvature_ridge_factor=1.25
sc.display.shading.curvature_valley_factor=1.0
sc.display.shading.show_specular_highlight=False
sc.display.shading.background_type='WORLD'
sc.world=bpy.data.worlds.new('Blockout ambient')
sc.world.color=(.018,.022,.03)
sc.view_settings.view_transform='Standard'
sc.display.render_aa='16'

def xyz(u,v,z=0): return Vector((u,-v,z/ZPP))
def project(u,v,z=0): return [OX+(u-v)*60*K, OY+((u+v)*30-z)*K]
def box(name,u0,v0,u1,v1,z0,z1,kind):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz((u0+u1)/2,(v0+v1)/2,(z0+z1)/2))
    ob=bpy.context.object; ob.name=name
    ob.dimensions=(u1-u0,v1-v0,(z1-z0)/ZPP)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.color=COLORS[kind]
    return ob

cam_data=bpy.data.cameras.new('Exact draft4 orthographic camera')
cam=bpy.data.objects.new('Camera',cam_data); sc.collection.objects.link(cam)
cam_data.type='ORTHO'; cam_data.ortho_scale=30
cam.rotation_euler=(math.radians(60),0,math.radians(45))
cam.location=RIGHT*((960-OX)/(60*math.sqrt(2)*K))+UP*((OY-540)/(60*math.sqrt(2)*K))+NORMAL*40
sc.camera=cam
rows=[]
for i,(v,z) in enumerate([(1.5,24),(2.9,24),(4.3,64),(5.7,80),(7.1,96),(8.5,112)]):
    small=[.8,1.6,2.4] if i>=2 else [.8+j*.8 for j in range(21)]
    main=[4.4+j*.8 for j in range(16)] if i>=2 else []
    row={'row':chr(65+i),'v':v,'floor_zpx_world':z,
         'section':'flat front' if i<2 else 'raised bank',
         'seat_u':small+main,'seat_u_by_block':{'small_wall_side' if i>=2 else 'front':small,'main':main},
         'seat_count_per_block':{'small_wall_side' if i>=2 else 'front':len(small),'main':len(main)}}
    rows.append(row)

# Shortened hall retains the fixed camera and generous seat widths without clipping.
box('Flat floor',0,0,17.5,3.9,-8,24,'floor')
for i,r in enumerate(rows[2:]):
    lo=3.9 if i==0 else r['v']-.7
    hi=9.1 if i==3 else r['v']+.7
    box('Tier '+r['row'],0,lo,17.5,hi,0,r['floor_zpx_world'],'floor')
    # A genuine opening through each platform for the middle stair flight.
    # Replace the solid platform with two sides and separate stair treads.
    ob=bpy.context.object
    bpy.data.objects.remove(ob,do_unlink=True)
    for a,b in [(0,2.95),(3.95,17.5)]:
        z=r['floor_zpx_world']
        box('Tier '+r['row'],a,lo,b,hi,z-4,z,'floor')
        box('Tier riser '+r['row'],a,lo,b,lo+.035,24 if i==0 else z-16,z,'floor')

# Back wall and side wall, with actual recessed entrance opening at ground level.
box('Screen wall',-.12,-.12,17.5,0,-8,650,'wall')
box('Side wall before passage',-.12,0,0,3.42,-8,650,'wall')
box('Side wall after passage',-.12,4.05,0,9.1,-8,650,'wall')
box('Passage lintel',-.12,3.42,0,4.05,152,650,'wall')
box('Black passage recess',-.9,3.42,-.85,4.05,24,152,'black')
box('Passage floor',-.9,3.42,.12,4.05,20,24,'black')
box('Green EXIT sign',.015,3.38,.13,4.1,163,182,'exit')
screen_z1=90+12*9/16*ZPP
screen=box('White screen',3.4,.015,15.4,.035,90,screen_z1,'screen')
box('Stage',2.8,.10,16.1,.57,24,43,'stage')
box('Low divider',.3,3.36,2.95,3.45,24,53,'divider')
box('Low divider main',3.95,3.36,17.2,3.45,24,53,'divider')
for u in (2.4,16.2):
    box('Speaker stack',u-.3,.11,u+.3,.6,43,194,'black')
box('DINK DONK plaque',.04,1.1,.18,2.4,305,337,'plaque')
for v in (1.1,5.2,7.8):
    box('Wall speaker',.01,v,.23,v+.35,350,390,'black')
    box('Wall light',.01,v+.5,.17,v+.72,265,306,'light')

# Stair centre u=3.45, seats on both sides. Four starter steps then two per tier.
stairs=[]
for j in range(4):
    stairs.append((3.48+j*.205,3.48+(j+1)*.205,24+10*(j+1)))
for j in range(6):
    stairs.append((4.3+j*.7,4.3+(j+1)*.7,64+8*(j+1)))
for j,(lo,hi,z) in enumerate(stairs):
    box('Stair tread %02d'%j,2.95,lo,3.95,hi,0,z,'stairs')
box('Back stair landing',2.95,8.5,3.95,9.1,0,112,'stairs')
for r in rows:
    for j,u in enumerate(r['seat_u']):
        v=r['v']; z=r['floor_zpx_world']
        box(r['row']+' seat '+str(j+1),u-.29,v-.25,u+.29,v+.23,z+26,z+36,'seat')
        box(r['row']+' back '+str(j+1),u-.29,v+.18,u+.29,v+.29,z+26,z+62,'seat')

bpy.context.view_layer.update()
markers=[(0,0,0),(17.5,0,0),(0,9.1,112),(17.5,9.1,112),(0,0,650)]
errors=[]
for p in markers:
    q=world_to_camera_view(sc,cam,xyz(*p)); expected=project(*p)
    errors.extend([q.x*W-expected[0],(1-q.y)*H-expected[1]])
assert max(map(abs,errors))<1
bounds=[world_to_camera_view(sc,cam,ob.matrix_world@Vector(c)) for ob in sc.objects if ob.type=='MESH' for c in ob.bound_box]
bbox=[min(p.x*W for p in bounds),min((1-p.y)*H for p in bounds),max(p.x*W for p in bounds),max((1-p.y)*H for p in bounds)]
assert bbox[0]>0 and bbox[1]>0 and bbox[2]<W and bbox[3]<H,bbox

# Camera-facing foreground annotation: no second image or postprocessing output.
scale=30/W
rot=Matrix((RIGHT,UP,NORMAL)).transposed().to_quaternion()
def overlay_point(x,y):
    return cam.location-NORMAL*10+RIGHT*((x-W/2)*scale)+UP*((H/2-y)*scale)
def label(text,x,y,size=19,kind='ink'):
    curve=bpy.data.curves.new(text,'FONT'); curve.body=text; curve.size=size*scale
    ob=bpy.data.objects.new('Label '+text,curve); sc.collection.objects.link(ob)
    ob.location=overlay_point(x,y); ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rot
    ob.color=COLORS[kind]
def line2d(points,kind='route',width=1.7):
    curve=bpy.data.curves.new('annotation','CURVE'); curve.dimensions='3D'; curve.bevel_depth=width*scale/2; curve.bevel_resolution=0
    spl=curve.splines.new('POLY'); spl.points.add(len(points)-1)
    for p,(x,y) in zip(spl.points,points): p.co=(*overlay_point(x,y),1)
    ob=bpy.data.objects.new('Annotation line',curve); sc.collection.objects.link(ob); ob.color=COLORS[kind]
def callout(text,x,y,target,size=19):
    label(text,x,y,size)
    line2d([(x,y+6),target],'ink',1)

route=[[-.45,3.73,0],[.45,3.73,0],[3.45,3.73,32]]
# Landing goes around the foot, then climbs the stair centre.
route=[[-.45,3.73,24],[.45,3.73,24],[2.6,3.59,24],[3.45,3.43,24]]
route += [[3.45,(lo+hi)/2,z] for lo,hi,z in stairs]
route += [[3.45,8.65,112]]
projected=[project(u,v,z+8) for u,v,z in route]
for a,b in zip(projected,projected[1:]):
    dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
    for t in range(0,max(1,int(length)),10):
        end=min(t+3,length)
        line2d([(a[0]+dx*t/length,a[1]+dy*t/length),(a[0]+dx*end/length,a[1]+dy*end/length)])
for r in rows:
    x,y=project(.35,r['v'],r['floor_zpx_world']+45)
    label(r['row'],x-26,y,23)
label('CINEMA / DRAFT 05 / LAYOUT BLOCKOUT',75,60,27)
label('6 ROWS  |  1.4 TILE PITCH  |  16 UNIT BANK RISE',75,91,18)
label('YELLOW DOTTED LINE = ENTRANCE > STAIRS > BACK ROW',75,1039,17,'route')
callout('SCREEN',1445,220,project(13,0,450),22)
callout('STAGE',1570,855,project(14,.4,44))
callout('FRONT AISLE',1390,975,project(13,.88,25))
callout('DIVIDER',1390,1020,project(15,3.4,53))
callout('ENTRANCE / EXIT',100,485,project(.05,3.73,90),20)
label('EXIT',*project(.1,3.7,172),15,'ink')
callout('STAIRS',95,750,project(3.45,6.3,80),22)
callout('SMALL BLOCK',95,815,project(1.6,7.1,130),17)
callout('MAIN BLOCK',1190,1055,project(12,8.5,153),17)
callout('DINK DONK',85,265,project(.12,1.8,320),17)

pairs=[]
for a,b in zip(rows,rows[1:]):
    dv=b['v']-a['v']; dz=b['floor_zpx_world']-a['floor_zpx_world']
    sep=K*abs(2*dz-120*dv)/math.sqrt(5)
    pairs.append({'from':a['row'],'to':b['row'],'delta_v':round(dv,4),'delta_zpx_world':dz,'perpendicular_px':sep,'passes_25px':sep>=25})
assert all(p['passes_25px'] for p in pairs)
for r in rows:
    r['screen_clearance_px']=K*(60*r['v']+90-r['floor_zpx_world']-36-50-18.5)
    assert r['screen_clearance_px']>0
data={'brief':'BRIEF-32-cinema-draft5-blockout.md','image':[W,H],
      'camera':{'rotation_degrees':[60,0,45],'ortho_scale':30,'k':K,'Ox':OX,'Oy':OY,'calibration_max_axis_error_px':max(map(abs,errors))},
      'room':{'u':[0,17.5],'v':[0,9.1],'wall_top_zpx_world':650,'geometry_bounds_px':bbox},
      'layout_decision':'Six rows instead of draft4 eight: two flat front, four bank; shortened depth fits 1.4 pitch and 16 rise within unchanged camera. Owner can review capacity in this blockout.',
      'rows':rows,'row_pairs':pairs,'total_seats':sum(len(r['seat_u']) for r in rows),
      'stairs':{'u_range':[2.95,3.95],'small_block_seats_per_bank_row':3,'main_block_seats_per_bank_row':16,'treads_v0_v1_zpx_world':stairs},
      'screen':{'u':[3.4,15.4],'v':0,'zpx_world':[90,screen_z1],
                'corners_px':{name:project(u,0,z) for name,u,z in [('TL',3.4,screen_z1),('TR',15.4,screen_z1),('BR',15.4,90),('BL',3.4,90)]}},
      'emote_clearance':{'width_px':74*K,'height_px':50*K,'seat_anchor_zpx_world':36,'minimum_px':min(r['screen_clearance_px'] for r in rows),
                         'method':'k*(60*v+90-floor_z-36-50-18.5), conservative right-corner clearance to extended lower screen edge. Geometric envelope only; no emote artwork or occlusion render.'},
      'walk_route':{'units':'u,v,zpx_world','passage_to_back_row':route,'row_branches':[{'row':r['row'],'points':[[3.45,r['v'],r['floor_zpx_world']],[2.8,r['v'],r['floor_zpx_world']]],'main_points':[[3.45,r['v'],r['floor_zpx_world']],[4.0,r['v'],r['floor_zpx_world']]]} for r in rows[2:]],'front_branch':[[.45,3.73,24],[.45,2.9,24],[.45,1.5,24]]},
      'render':{'engine':'Workbench studio / object colors','count':1,'materials':0,'blend_saved':False},
      'limitations':['Six-row capacity is a blockout choice for fixed framing.','No styled materials, wear, lighting design, physical access/code validation, emote visibility or page tests.']}
(RUN/'render_started').write_text('one Workbench render',encoding='utf-8')
rt=time.perf_counter()
bpy.ops.render.render(write_still=True)
data['render']['seconds']=time.perf_counter()-rt
data['render']['total_seconds']=time.perf_counter()-T
data['render']['blender_version']=bpy.app.version_string
data['render']['image_sha256']=hashlib.sha256(IMAGE.read_bytes()).hexdigest()
after=snapshot()
changed=[p for p,st in before.items() if after.get(p)!=st]
assert not changed,changed
data['preservation']={'passed':True,'existing_files_checked':len(before),'method':'Before/after size and nanosecond mtime, every pre-existing workspace file except .log files; no original file writes. No blend loaded or saved.'}
with LAYOUT.open('x',encoding='utf-8') as f: json.dump(data,f,indent=2)
table='\n'.join('| '+r['row']+' | '+str(r['v'])+' | '+str(r['floor_zpx_world'])+' | '+', '.join(map(str,r['seat_u']))+' | '+str(r['seat_count_per_block'])+' |' for r in rows)
seps='\n'.join(f"| {p['from']}-{p['to']} | {p['delta_v']} | {p['delta_zpx_world']} | {p['perpendicular_px']:.3f} | PASS |" for p in pairs)
report=f'''# Cinema draft 05 - quick layout blockout

One 1920x1080 Workbench still with basic boxes and object colors. Two flat front rows, a low red divider, four shallow raised rows, and a light grey staircase between a three-seat wall-side block and a sixteen-seat main block. Purple seats use just seat and back boxes. English EXIT, black passage, white screen, brown stage, black speaker stacks, wall fixture boxes and cyan DINK DONK plaque retained. Labels and dotted route are camera-facing annotations in this same render.

**Capacity choice for review:** draft 4 had eight rows. This blockout has six (118 seats) and a shorter hall depth of 9.1 tiles so the fixed camera retains the entire hall while using 1.4-tile row pitch and 16-unit bank rise (66.7% flatter than 48). Rows A/B both stand on the flat floor at 24. The raised bank begins at 64, matching draft 4's first bank elevation; its last row is 112. Four starter steps rise 10 each, then two steps of 8 per bank-row interval. Layout capacity can be revised after owner feedback.

Camera `(60,0,45)`, ortho scale `30`, `Ox={OX}`, `Oy={OY}`, `k={K:.12f}`. Independent camera/formula calibration maximum error `{max(map(abs,errors)):.6f}px`. Geometry bounds L/T/R/B `{[round(x,2) for x in bbox]}`; whole hall inside frame with dark margins. Screen unchanged: v=0, u=3.4-15.4, z=90-{screen_z1:.9f}. JSON contains unchanged screen corners.

| Row | v | Floor zpx_world | Seat u positions | Counts per block |
|---|---:|---:|---|---|
{table}

| Pair | dv | dz | Perpendicular separation px | >=25px |
|---|---:|---:|---:|---|
{seps}

Formula `k*abs(2*dz-120*dv)/sqrt(5)`. Minimum `{min(p['perpendicular_px'] for p in pairs):.3f}px`; all pairs pass, including the front-to-bank transition. Same-bank pairs are `{pairs[-1]['perpendicular_px']:.3f}px` apart.

Seated camera-facing emote envelope: height `50k={50*K:.3f}px`, width `74k={74*K:.3f}px`, anchor at floor+36. Clearance to the screen's extended sloping lower edge uses `k*(60*v+90-floor_z-36-50-18.5)`; minimum `{data['emote_clearance']['minimum_px']:.3f}px`. Per-row values are in JSON. This checks the numeric envelope only, without audience artwork or face-occlusion testing.

Route: recessed passage on u=0 wall at v=3.73 -> landing/front cross-aisle in front of raised bank -> u=3.45 stair foot -> starter steps -> shallow central flight -> back-row landing; each bank row branches to seats on both sides. Rows A/B branch along the flat wall-side aisle. All route points, stair treads and row branches are in JSON; thin yellow dotted overlay shows the passage-to-back route. The separately labelled FRONT AISLE is the open flat strip beside the stage.

Render `{data['render']['seconds']:.2f}s`; build/check/render `{data['render']['total_seconds']:.2f}s`, Blender {bpy.app.version_string}. Exactly one render, no blend save, no materials, no wear or styled lighting. Studio Workbench illumination supplies simple ambient/key shading. Future styling notes retained: much darker muted walls, less overall light, purple seats, English EXIT.

Preservation PASS: {len(before)} pre-existing workspace files matched size/mtime; active .log files excluded. Existing .blend files, earlier drafts, cloud bundle, out10 and pages were never opened for writing. All new outputs and runtime files are inside roxy3d/. No extra image, 4K render, page changes or live tests. Stop for owner layout review.
'''
with REPORT.open('x',encoding='utf-8') as f: f.write(report)
print('STATUS: DRAFT 05 BLOCKOUT COMPLETE | one 1920x1080 image | report + JSON | STOP',flush=True)

