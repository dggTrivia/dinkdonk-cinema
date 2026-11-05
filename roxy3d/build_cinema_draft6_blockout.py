"""Brief 33: one quick Workbench blockout, new files only, no blend save."""
import sys
sys.dont_write_bytecode = True
import os, json, math, time, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUN = QA/'runtime06'
IMAGE = QA/'cinema_draft_06_blockout.png'
REPORT = QA/'CINEMA-DRAFT-06.md'
LAYOUT = QA/'cinema_layout_06.json'
for p in (IMAGE, REPORT, LAYOUT, RUN/'render_started'):
    assert not p.exists() or (os.environ.get('DRAFT06_FINISH')=='1' and p in (IMAGE,RUN/'render_started')), f'New-file guard: {p}'
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
ORTHO = 32
K = 22.627416998/ORTHO
OX,OY = 890,370
ZPP = 73.48469228349535
DEPTH = 14.9
WALL = 500
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
    result={}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUN in p.parents or p == Path(__file__).resolve(): continue
        if p.suffix.lower()=='.log': continue
        st=p.stat()
        result[str(p.relative_to(ROOT.parent))]=[st.st_size,st.st_mtime_ns]
    return result
baseline=RUN/'preservation_before.json'
before=json.loads(baseline.read_text(encoding='utf-8')) if baseline.exists() else snapshot()
if not baseline.exists(): baseline.write_text(json.dumps(before),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
sc.render.film_transparent=False; sc.render.filepath=str(IMAGE)
sc.display.shading.light='STUDIO'; sc.display.shading.studiolight_rotate_z=.4
sc.display.shading.color_type='OBJECT'; sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True; sc.display.shading.cavity_type='WORLD'
sc.display.shading.curvature_ridge_factor=1.25; sc.display.shading.curvature_valley_factor=1
sc.display.shading.show_specular_highlight=False
sc.display.shading.background_type='WORLD'
sc.world=bpy.data.worlds.new('Blockout ambient'); sc.world.color=(.018,.022,.03)
sc.view_settings.view_transform='Standard'; sc.display.render_aa='16'
def xyz(u,v,z=0): return Vector((u,-v,z/ZPP))
def project(u,v,z=0): return [OX+(u-v)*60*K, OY+((u+v)*30-z)*K]
def box(name,u0,v0,u1,v1,z0,z1,kind):
    assert u1>u0 and v1>v0 and z1>z0, name
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz((u0+u1)/2,(v0+v1)/2,(z0+z1)/2))
    ob=bpy.context.object; ob.name=name
    ob.dimensions=(u1-u0,v1-v0,(z1-z0)/ZPP)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.color=COLORS[kind]
    return ob
cam_data=bpy.data.cameras.new('Draft6 orthographic camera')
cam=bpy.data.objects.new('Camera',cam_data); sc.collection.objects.link(cam)
cam_data.type='ORTHO'; cam_data.ortho_scale=ORTHO
cam.rotation_euler=(math.radians(60),0,math.radians(45))
cam.location=RIGHT*((960-OX)/(60*math.sqrt(2)*K))+UP*((OY-540)/(60*math.sqrt(2)*K))+NORMAL*40
sc.camera=cam
LEFT=[.8,1.6,2.4]
MAIN=[round(4.5+j*.8,2) for j in range(13)]
EDGE=[16.1,16.9]
rows=[]
for i in range(8):
    bank=i>0
    blocks={'left':LEFT[:] if i==0 or i>=4 else [], 'main':MAIN[:], 'right':EDGE[:]}
    r={'row':chr(66+i),'v':2.9 if not bank else round(5.9+(i-1)*1.4,2),
       'floor_zpx_world':24 if not bank else 64+(i-1)*16,
       'section':'raised bank' if bank else 'flat front',
       'seat_u_by_block':blocks,'seat_u':[u for b in blocks.values() for u in b],
       'seat_count_per_block':{k:len(v) for k,v in blocks.items()}}
    rows.append(r)
# Continuous base slab: stair supports terminate on it, never below its underside.
box('Continuous floor slab',0,0,17.5,DEPTH,-8,24,'floor')
for i,r in enumerate(rows[1:]):
    lo=5.2 if i==0 else round(r['v']-.7,2)
    hi=DEPTH if i==6 else round(r['v']+.7,2)
    for a,b in [(0,2.95),(4.0,14.65),(15.65,17.5)]:
        box('Bank tier '+r['row'],a,lo,b,hi,24,r['floor_zpx_world'],'floor')
# Screen wall and entrance-side wall, both lowered to 500.
box('Screen wall',-.12,-.12,17.5,-.025,-8,WALL,'wall')
box('Side wall before passage',-.12,0,0,3.7,-8,WALL,'wall')
box('Side wall after passage',-.12,4.6,0,DEPTH,-8,WALL,'wall')
box('Passage lintel',-.12,3.7,0,4.6,152,WALL,'wall')
box('Black passage recess',-.9,3.7,-.85,4.6,24,152,'black')
box('Passage floor',-.9,3.7,.12,4.6,20,24,'black')
box('Green EXIT sign',.015,3.67,.13,4.63,163,182,'exit')
# Largest 16:9 screen with existing 90-unit bottom and 40-unit top border.
SZ0,SZ1=90,460
SW=(SZ1-SZ0)/ZPP*16/9
SU0,SU1=9.4-SW/2,9.4+SW/2
me=bpy.data.meshes.new('Clean screen quad')
me.from_pydata([xyz(SU0,0,SZ1),xyz(SU1,0,SZ1),xyz(SU1,0,SZ0),xyz(SU0,0,SZ0)],[],[(3,2,1,0)])
screen=bpy.data.objects.new('White 16 by 9 screen v=0',me); sc.collection.objects.link(screen)
screen.color=COLORS['screen']
box('Stage',2.8,.10,16.1,.57,24,43,'stage')
for a,b in [(.3,2.95),(4,14.65),(15.65,17.2)]:
    box('Cross-aisle divider',a,4.9,b,5.0,24,53,'divider')
for u in (3.5,15.3): box('Speaker stack',u-.3,.11,u+.3,.6,43,194,'black')
box('DINK DONK plaque',.04,1.1,.18,2.4,305,337,'plaque')
for v in (1.1,7.0,12.0):
    box('Wall speaker',.01,v,.23,v+.35,350,390,'black')
    box('Wall light',.01,v+.5,.17,v+.72,265,306,'light')
stairs=[]
for j in range(4): stairs.append([round(4.5+j*.35,2),round(4.5+(j+1)*.35,2),24+10*(j+1)])
for j in range(12): stairs.append([round(5.9+j*.7,2),round(5.9+(j+1)*.7,2),64+8*(j+1)])
for a,b in [(2.95,4.0),(14.65,15.65)]:
    for j,(lo,hi,z) in enumerate(stairs): box('Supported aisle stair %s %02d'%(a,j),a,lo,b,hi,24,z,'stairs')
    box('Back aisle landing',a,14.3,b,DEPTH,24,160,'stairs')
for r in rows:
    for j,u in enumerate(r['seat_u']):
        v=r['v']; z=r['floor_zpx_world']
        box(r['row']+' seat '+str(j+1),u-.29,v-.25,u+.29,v+.23,z+26,z+36,'seat')
        box(r['row']+' back '+str(j+1),u-.29,v+.18,u+.29,v+.29,z+26,z+62,'seat')
bpy.context.view_layer.update()
errors=[]
for p in [(0,0,0),(17.5,0,0),(0,DEPTH,160),(17.5,DEPTH,160),(0,0,WALL)]:
    q=world_to_camera_view(sc,cam,xyz(*p)); expected=project(*p)
    errors.extend([q.x*W-expected[0],(1-q.y)*H-expected[1]])
assert max(map(abs,errors))<1
bounds=[world_to_camera_view(sc,cam,ob.matrix_world@Vector(c)) for ob in sc.objects if ob.type=='MESH' for c in ob.bound_box]
bbox=[min(p.x*W for p in bounds),min((1-p.y)*H for p in bounds),max(p.x*W for p in bounds),max((1-p.y)*H for p in bounds)]
assert bbox[0]>10 and bbox[1]>10 and bbox[2]<W-10 and bbox[3]<H-10,bbox
# Foreground annotations only: no scene text that can leave a stray fragment.
scale=ORTHO/W
rot=Matrix((RIGHT,UP,NORMAL)).transposed().to_quaternion()
def overlay_point(x,y): return cam.location-NORMAL*10+RIGHT*((x-W/2)*scale)+UP*((H/2-y)*scale)
def label(text,x,y,size=19,kind='ink'):
    curve=bpy.data.curves.new(text,'FONT'); curve.body=text; curve.size=size*scale
    ob=bpy.data.objects.new('Label '+text,curve); sc.collection.objects.link(ob)
    ob.location=overlay_point(x,y); ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rot
    ob.color=COLORS[kind]
    ob.display.show_shadows=False
def line2d(points,kind='route',width=1.7):
    curve=bpy.data.curves.new('annotation','CURVE'); curve.dimensions='3D'; curve.bevel_depth=width*scale/2; curve.bevel_resolution=0
    spl=curve.splines.new('POLY'); spl.points.add(len(points)-1)
    for p,(x,y) in zip(spl.points,points): p.co=(*overlay_point(x,y),1)
    ob=bpy.data.objects.new('Annotation line',curve); sc.collection.objects.link(ob); ob.color=COLORS[kind]
    ob.display.show_shadows=False
def callout(text,x,y,target,size=19):
    label(text,x,y,size); line2d([(x,y+6),target],'ink',1)
route=[[-.45,4.15,24],[.45,4.15,24],[3.475,4.15,24],[3.475,4.5,24]]
route += [[3.475,(lo+hi)/2,z] for lo,hi,z in stairs]
route += [[3.475,14.65,160]]
projected=[project(u,v,z+8) for u,v,z in route]
for a,b in zip(projected,projected[1:]):
    dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
    for t in range(0,max(1,int(length)),10):
        end=min(t+3,length)
        line2d([(a[0]+dx*t/length,a[1]+dy*t/length),(a[0]+dx*end/length,a[1]+dy*end/length)])
# Clean fixed outside-room column, with leaders terminating at each row's left edge.
for r in rows:
    x,y=project(0,r['v'],r['floor_zpx_world']+42)
    label(r['row'],195,y,21)
    line2d([(218,y-5),(x-12,y-5)],'ink',.7)
label('CINEMA / DRAFT 06 / LAYOUT BLOCKOUT',65,48,26)
label('1 FRONT + 7 BANK ROWS  |  1.4 TILE BANK PITCH  |  16 UNIT RISE',65,78,17)
label('YELLOW ROUTE = EXIT PASSAGE > CROSS-AISLE > LEFT STAIRS > BACK',65,1045,16,'route')
callout('SCREEN / 16:9',1530,190,project(13,0,400),20)
callout('STAGE',1650,820,project(14,.4,44),18)
callout('CLEAR FRONT GAP',1540,915,project(13,1.5,24),17)
callout('2 TILE CROSS-AISLE + DIVIDER',1160,990,project(12,4.2,24),17)
callout('ENTRANCE / EXIT',65,330,project(.05,4.15,90),18)
label('EXIT',*project(.1,4.15,172),13)
callout('LEFT STAIRS / OPEN ARRIVAL',65,820,project(3.475,7.3,80),17)
callout('RIGHT AISLE',1580,965,project(15.15,11.5,128),17)
callout('DINK DONK',65,160,project(.12,1.8,320),16)
pairs=[]
for a,b in zip(rows,rows[1:]):
    dv=b['v']-a['v']; dz=b['floor_zpx_world']-a['floor_zpx_world']
    sep=K*abs(2*dz-120*dv)/math.sqrt(5)
    pairs.append({'from':a['row'],'to':b['row'],'delta_v':round(dv,4),'delta_zpx_world':dz,'perpendicular_px':sep,'passes_25px':sep>=25})
assert all(p['passes_25px'] for p in pairs)
for r in rows:
    r['screen_clearance_px']=K*(60*r['v']+SZ0-r['floor_zpx_world']-36-50-18.5)
    assert r['screen_clearance_px']>0
corners={name:project(u,0,z) for name,u,z in [('TL',SU0,SZ1),('TR',SU1,SZ1),('BR',SU1,SZ0),('BL',SU0,SZ0)]}
aisles={'left_u':[2.95,4.0],'right_u':[14.65,15.65],'cross_v':[3.2,5.2],
        'cross_clear_depth_tiles':2.0,'divider_v':[4.9,5.0],
        'blank_left_arrival':{'u':[0,2.95],'v':[5.2,9.4],'rows':['C','D','E']},
        'stage_to_first_seat_clear_v':[.57,2.65]}
data={'brief':'BRIEF-33-cinema-draft6-blockout.md','image':[W,H],
      'camera':{'rotation_degrees':[60,0,45],'ortho_scale':ORTHO,'k':K,'Ox':OX,'Oy':OY,'calibration_max_axis_error_px':max(map(abs,errors))},
      'room':{'u':[0,17.5],'v':[0,DEPTH],'wall_top_zpx_world':WALL,'geometry_bounds_px':bbox},
      'layout_decision':'A removed; B retained as the only front row, split 3/13/2. Seven bank rows C-I, first three without left seats; later left blocks return. Two longitudinal stair aisles and a two-tile cross-aisle. Last row retains aisles.',
      'rows':rows,'row_pairs':pairs,'total_seats':sum(len(r['seat_u']) for r in rows),'aisles':aisles,
      'stairs':{'u_ranges':[[2.95,4.0],[14.65,15.65]],'treads_v0_v1_zpx_world':stairs,'support_bottom_zpx_world':24,'floor_slab_zpx_world':[-8,24]},
      'screen':{'u':[SU0,SU1],'v':0,'zpx_world':[SZ0,SZ1],'physical_aspect':16/9,'top_wall_border_zpx_world':40,
                'corners_wall':{name:[u,0,z] for name,u,z in [('TL',SU0,SZ1),('TR',SU1,SZ1),('BR',SU1,SZ0),('BL',SU0,SZ0)]},
                'corners_1920x1080':corners,'corners_3840x2160':{n:[2*x for x in p] for n,p in corners.items()}},
      'emote_clearance':{'width_px':74*K,'height_px':50*K,'seat_anchor_zpx_world':36,'minimum_px':min(r['screen_clearance_px'] for r in rows),
                         'method':'k*(60*v+90-floor_z-36-50-18.5), conservative right-corner clearance to extended lower screen edge. Numeric envelope only.'},
      'walk_route':{'units':'u,v,zpx_world','passage_to_back_row':route,
                    'row_branches':[{'row':r['row'],'points':[[3.475,r['v'],r['floor_zpx_world']],[4.15,r['v'],r['floor_zpx_world']]],'left_points':[[3.475,r['v'],r['floor_zpx_world']],[2.8,r['v'],r['floor_zpx_world']]] if r['seat_u_by_block']['left'] else [],'right_points':[[15.15,r['v'],r['floor_zpx_world']],[15.8,r['v'],r['floor_zpx_world']]]} for r in rows[1:]],
                    'front_branch':[[.45,4.15,24],[3.475,4.15,24],[3.475,2.9,24]],
                    'right_aisle_connection':[[3.475,4.15,24],[15.15,4.15,24],[15.15,4.5,24]]},
      'render':{'engine':'Workbench studio / object colors','count':2 if os.environ.get('DRAFT06_FINISH')=='1' else 1,'final_images':1,'materials':0,'blend_saved':False},
      'limitations':['Quick boxes only; no styled surfaces, wear or lighting design.','Numeric emote envelope only; no audience artwork or visibility test.','No physical accessibility/code validation or page tests.']}
(RUN/'render_started').write_text('one Workbench render',encoding='utf-8')
rt=time.perf_counter(); bpy.ops.render.render(write_still=True)
data['render']['seconds']=time.perf_counter()-rt
data['render']['total_seconds']=time.perf_counter()-T
data['render']['blender_version']=bpy.app.version_string
data['render']['image_sha256']=hashlib.sha256(IMAGE.read_bytes()).hexdigest()
after=snapshot()
changed=[p for p,st in before.items() if after.get(p)!=st]
project_changed=[p for p in changed if p.startswith('roxy3d\\') or p.startswith('roxy3d/')]
assert not project_changed,project_changed
project_count=sum(p.startswith('roxy3d\\') or p.startswith('roxy3d/') for p in before)
data['preservation']={'passed':True,'existing_roxy3d_files_checked':project_count,'unrelated_concurrent_workspace_changes':changed,'method':'Before/after size and nanosecond mtime, original baseline retained. Every pre-existing roxy3d file unchanged; active .log files excluded. Concurrent changes outside roxy3d listed separately. All builder writes confined to roxy3d; no blend loaded or saved.'}
with LAYOUT.open('x',encoding='utf-8') as f: json.dump(data,f,indent=2)
table='\n'.join('| '+r['row']+' | '+str(r['v'])+' | '+str(r['floor_zpx_world'])+' | '+' / '.join(', '.join(map(str,b)) or '(blank)' for b in r['seat_u_by_block'].values())+' |' for r in rows)
seps='\n'.join(f"| {p['from']}-{p['to']} | {p['delta_v']} | {p['delta_zpx_world']} | {p['perpendicular_px']:.3f} | PASS |" for p in pairs)
screen_table='\n'.join(f'| {n} | {data["screen"]["corners_wall"][n]} | {[round(x,3) for x in p]} | {[round(2*x,3) for x in p]} |' for n,p in corners.items())
report=f'''# Cinema draft 06 - quick layout blockout

One 1920x1080 Workbench still, flat object colors and seat/back boxes. Row A removed. Former B is the only front row, split into left/main/right blocks of 3/13/2. Stage rear v=0.57 to first seat front v=2.65 leaves 2.08 tiles clear. The front seats remain at v=2.9, away from the screen.

Seven bank rows C-I add three rows to draft 5's four-row bank. Pitch 1.4 tiles, rise 16 zpx_world, floors 64-160. First three bank rows C/D/E leave the left block blank for the arrival area; three-seat left blocks return in F-I. Long main blocks have 13 seats; right edge blocks have two. Total **{data['total_seats']} seats**. Last row keeps both aisles. Seat map used indicatively, not copied exactly.

Cross-aisle v=3.2-5.2 (2 tiles) separates B from C; divider at v=4.9-5.0 with aisle openings. Longitudinal aisles u=2.95-4.0 and 14.65-15.65. Blank left arrival u=0-2.95, v=5.2-9.4. Both stair lanes have four 10-unit starter steps, then two 8-unit steps per bank interval. Their solid supports start at floor z=24, above the continuous slab underside z=-8; no hanging block. Row letters occupy one clean column outside the room, with leaders; all labels are foreground annotations.

Camera `(60,0,45)`, ortho_scale **{ORTHO}**, `k={K:.12f}`, `Ox={OX}`, `Oy={OY}`. Walls lowered from 650 to **{WALL}** on both retained sides. Hall u=0-17.5, v=0-{DEPTH}. Geometry bounds L/T/R/B `{[round(x,2) for x in bbox]}`; whole hall passes 10px dark-margin check. Calibration maximum axis error `{max(map(abs,errors)):.6f}px`.

Screen: clean 16:9 quad on v=0, u={SU0:.9f}-{SU1:.9f}, z=90-{SZ1}, largest within the retained 90-unit bottom / 40-unit top borders. White, no artwork or projected light; plain Workbench shading. Speaker stacks remain outside its horizontal extent.

| Corner | Wall [u,v,zpx_world] | 1080p [x,y] | 4K [x,y] (calculated) |
|---|---|---|---|
{screen_table}

| Row | v | Floor zpx_world | Seat u: left / main / right |
|---|---:|---:|---|
{table}

| Pair | dv | dz | Perpendicular separation px | >=25px |
|---|---:|---:|---:|---|
{seps}

Formula `k*abs(2*dz-120*dv)/sqrt(5)`. Minimum `{min(p['perpendicular_px'] for p in pairs):.3f}px`; all row pairs pass. Seated emote envelope `50k={50*K:.3f}px` high by `74k={74*K:.3f}px` wide, anchor floor+36. Conservative clearance to extended screen lower edge `k*(60*v+90-floor_z-36-50-18.5)`, minimum `{data['emote_clearance']['minimum_px']:.3f}px`. Per-row values in JSON; geometric envelope only, no artwork/face occlusion test.

Route: recessed English EXIT passage on u=0 at v=3.7-4.6 -> cross-aisle at v=4.15 -> left aisle centre u=3.475 -> stair foot v=4.5 -> up -> back row. Yellow dotted line follows these points. JSON records all treads, route points, per-row branches, front branch and connection to the right stair aisle.

Final render `{data['render']['seconds']:.2f}s`; final build/check/render `{data['render']['total_seconds']:.2f}s`, Blender {bpy.app.version_string}. Exactly one final image; an initial render was replaced to remove annotation shadows. No blend save, materials, wear or styled lighting. Future styling notes: darker muted walls, less light overall, purple seats, English EXIT.

Preservation PASS for all {project_count} pre-existing roxy3d files: size/mtime match (active .log files excluded). Earlier drafts, existing roxy3d .blend files, cloud bundle, out10 and pages untouched by this builder. The broader workspace baseline detected concurrent changes outside roxy3d: {changed}; these are recorded separately and were not written by this builder. New builder and runtime06 files only, all writes inside roxy3d/. 4K corner coordinates are calculated; no 4K render. STOP for owner layout review.
'''
with REPORT.open('x',encoding='utf-8') as f: f.write(report)
print('STATUS: DRAFT 06 BLOCKOUT COMPLETE | one 1920x1080 image | report + JSON | STOP',flush=True)
