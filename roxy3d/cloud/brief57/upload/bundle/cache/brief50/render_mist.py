"""Brief 50 isolated native-grid data captures and one physical mist phase."""
import sys, os, math, json, time, struct, zlib, random, hashlib, warnings
from pathlib import Path
sys.dont_write_bytecode=True
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT/'cache/brief50'; OUT=ROOT/'out10mist'
OUT.mkdir(exist_ok=True)
ZPP=60*math.sqrt(2)*math.cos(math.pi/6); PPU=60*math.sqrt(2)
RIGHT=np.array([2**-.5,2**-.5,0]); UP=np.array([-math.sqrt(.125),math.sqrt(.125),math.sqrt(.75)]); NORMAL=np.cross(RIGHT,UP)
TIMES={}
def savejson(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def png(p,a):
 a=np.asarray(a,np.uint8);h,w=a.shape[:2];c=1 if a.ndim==2 else a.shape[2]
 d=a.reshape(h,w,c).copy();d[:,1:]=(d[:,1:].astype(np.int16)-d[:,:-1]).astype(np.uint8)
 scan=np.concatenate([np.ones((h,1),np.uint8),d.reshape(h,w*c)],axis=1)
 def ch(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,{1:0,3:2,4:6}[c],0,0,0))+ch(b'IDAT',zlib.compress(scan.tobytes(),6))+ch(b'IEND',b''))
def pixels(p):
 im=bpy.data.images.load(str(p),check_existing=False);w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im);return a.reshape(h,w,4)[::-1].copy()
def area2(a):
 h,w=a.shape[:2];return a.reshape(h//2,2,w//2,2,*a.shape[2:]).mean(axis=(1,3),dtype=np.float32)
def log(s):print('BRIEF50',s,flush=True)
def gpu(sc):
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.refresh_devices()
 ds=[d for d in p.devices if d.type=='OPTIX'];assert ds,'Local OptiX GPU required; no CPU fallback'
 for d in p.devices:d.use=d in ds
 sc.cycles.device='GPU';log([d.name for d in ds])
 return [d.name for d in ds]
def config(sc,w=3840,h=2160,samples=16,denoise=False):
 sc.render.engine='CYCLES';gpu(sc);sc.render.resolution_x=w;sc.render.resolution_y=h;sc.render.resolution_percentage=100
 sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.use_sequencer=False;sc.render.use_compositing=False
 sc.render.use_persistent_data=True;sc.render.film_transparent=False;sc.render.fps=24
 sc.cycles.samples=samples;sc.cycles.use_adaptive_sampling=False;sc.cycles.use_denoising=denoise;sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True
 sc.cycles.seed=1701;sc.cycles.use_animated_seed=False;sc.cycles.pixel_filter_type='BLACKMAN_HARRIS';sc.cycles.filter_width=2.5 if w==3840 else 1.5
 sc.cycles.tile_size=2048
 sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='32';sc.render.image_settings.exr_codec='ZIP'
def movable(o):
 n=o.name.lower()
 return (any(s in n for s in ['water bead','dielectric bead','rain bead','surface beads','glass bead','edge drip','raindrop','rain streak','rain trail','micro impacts','stateless','thin steam','water crown','splash crown','rain particle']) or o.get('cloud_group')=='weather' or o.get('draft5_bus'))
def atmosphere(o):
 return any(s in o.name.lower() for s in ['atmospheric volume','cloud sky','atmosphere','hidden city','raycast target','light receiver mask'])
def eligible(o):
 n=o.name.lower()
 if movable(o) or atmosphere(o) or o.type=='FONT':return False
 if o.get('anim_id') or o.get('door_id') or any(s in n for s in ['cut core','cut interior','cut exterior','cut cap','section cap','restroom','corridor','lobby','ticket','concession','carpet','interior','cabbage','leaf','foliage','palm','neon','tube','marquee bulb','art ','window','glass left','glass right','glazing','perspex','catcher']):return False
 if any('glass' in m.name.lower() for m in o.data.materials if m) and not any(s in n for s in ['roof','skylight','canopy']):return False
 return True
def phase(sc):
 sc.frame_set(1)
 group=bpy.data.node_groups.get('D4 periodic ray-traced rain ripple normals')
 if group:group.nodes['Time seconds'].outputs[0].default_value=0
 for o in sc.objects:
  if o.get('d6_tube_state'):
   base=o['d6_on_material'] if o['d6_tube_state']=='A' else 'D6 unlit neon glass'
   ma=next((m for m in bpy.data.materials if m.name.startswith('D10 wet ') and m.name.endswith(' | '+base)),None) or bpy.data.materials.get(base)
   if ma:o.data.materials[0]=ma
  if o.name.startswith('D13 marquee bulb '):
   lev=.35+.65*(.5+.5*math.cos(math.tau*(-int(o['future_chase_group'])/4)))
   ma=o.data.materials[0].copy();o.data.materials[0]=ma
   for n in ma.node_tree.nodes:
    if n.type=='BSDF_PRINCIPLED':n.inputs['Emission Strength'].default_value=2.2*lev
   lamp=sc.objects.get('D13 incandescent local spill %02d'%int(o['marquee_index']))
   if lamp:lamp.data.energy=.06*lev
 bpy.context.view_layer.update()
def load(static=True):
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'cloud/bundle/scene.blend'));sc=bpy.context.scene
 bpy.context.preferences.filepaths.temporary_directory=str(WORK/'temp')
 for asset in list(bpy.data.images)+list(bpy.data.fonts):
  if asset.filepath.startswith('//'):asset.filepath=asset.filepath.replace('\\','/')
 phase(sc)
 rows=[]
 for i,o in enumerate(sorted([o for o in sc.objects if o.type in ['MESH','CURVE','FONT']],key=lambda o:o.name),1):
  o.pass_index=i
  if static and (movable(o) or atmosphere(o)):o.hide_render=True
  rows.append(dict(id=i,name=o.name,eligible=eligible(o),hidden=o.hide_render or not o.visible_camera,collections=[c.name for c in o.users_collection]))
 savejson(WORK/'object-ids.json',rows)
 return sc
def mathnode(t,op,*args):
 q=t.nodes.new('ShaderNodeMath');q.operation=op
 for i,v in enumerate(args):
  if isinstance(v,(int,float)):q.inputs[i].default_value=v
  else:t.links.new(v,q.inputs[i])
 return q.outputs[0]
def allowed(t,geo):
 sep=t.nodes.new('ShaderNodeSeparateXYZ');t.links.new(geo.outputs['Position'],sep.inputs[0]);x,y,z=sep.outputs
 def inside(v,lo,hi):return mathnode(t,'MULTIPLY',mathnode(t,'GREATER_THAN',v,lo),mathnode(t,'LESS_THAN',v,hi))
 interior=mathnode(t,'MULTIPLY',mathnode(t,'MULTIPLY',inside(x,.01,12.99),inside(y,-8.92,-.03)),mathnode(t,'LESS_THAN',z,175/ZPP))
 annex=mathnode(t,'MULTIPLY',mathnode(t,'MULTIPLY',inside(x,15,17.5),inside(y,-6.5,-.5)),mathnode(t,'LESS_THAN',z,58/ZPP))
 return mathnode(t,'SUBTRACT',1,mathnode(t,'MAXIMUM',interior,annex))
def material(base,ok,mode):
 ma=bpy.data.materials.new('B50 '+mode+' '+('outdoor ' if ok else 'excluded ')+(base.name if base else 'none'));ma.use_nodes=True;t=ma.node_tree;t.nodes.clear()
 out=t.nodes.new('ShaderNodeOutputMaterial');geo=t.nodes.new('ShaderNodeNewGeometry')
 allow=allowed(t,geo) if ok else 0
 white=t.nodes.new('ShaderNodeBsdfDiffuse');white.inputs['Roughness'].default_value=0
 if mode=='catch':
  if ok:t.links.new(allow,white.inputs['Color'])
  else:white.inputs['Color'].default_value=(0,0,0,1)
 else:white.inputs['Color'].default_value=(1,1,1,1)
 t.links.new(white.outputs[0],out.inputs['Surface'])
 for name,socket in [('B50Position',geo.outputs['Position']),('B50Normal',geo.outputs['Normal'])]:
  a=t.nodes.new('ShaderNodeOutputAOV');a.aov_name=name;t.links.new(socket,a.inputs['Color'])
 info=t.nodes.new('ShaderNodeObjectInfo');a=t.nodes.new('ShaderNodeOutputAOV');a.aov_name='B50Index';t.links.new(info.outputs['Object Index'],a.inputs['Value'])
 return ma
def aovs(sc):
 vl=sc.view_layers[0]
 for a in list(vl.aovs):vl.aovs.remove(a)
 for name,typ in [('B50Position','COLOR'),('B50Normal','COLOR'),('B50Index','VALUE')]:a=vl.aovs.add();a.name=name;a.type=typ
 tree=bpy.data.node_groups.new('Brief50 data only','CompositorNodeTree');tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
 layer=tree.nodes.new('CompositorNodeRLayers');layer.scene=sc;out=tree.nodes.new('NodeGroupOutput');tree.links.new(layer.outputs['Image'],out.inputs['Image'])
 for name in ['B50Position','B50Normal','B50Index']:
  f=tree.nodes.new('CompositorNodeOutputFile');f.directory=str(WORK/'aov');f.file_name=name
  f.format.media_type='IMAGE';f.format.file_format='OPEN_EXR';f.format.color_mode='RGBA';f.format.color_depth='32';f.format.exr_codec='ZIP';f.file_output_items.new('RGBA',name);tree.links.new(layer.outputs[name],f.inputs[name])
 sc.compositing_node_group=tree;sc.render.use_compositing=True
def capture(sc,name):
 t=time.perf_counter();sc.render.filepath=str(WORK/(name+'.exr'))
 bpy.ops.render.render(write_still=True,scene=sc.name)
 TIMES[name]=time.perf_counter()-t;savejson(WORK/('timings-'+MODE+'.json'),TIMES);log((name,TIMES[name]))
 return pixels(WORK/(name+'.exr'))
def display(sc,a,p,glare=False):
 # Production route: scene-linear buffer (already area-reduced for 1x), then retained AgX/glare.
 tree=sc.compositing_node_group.copy() if glare else bpy.data.node_groups.new('B50 display','CompositorNodeTree')
 if not glare:tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');tree.nodes.new('NodeGroupOutput')
 comp=bpy.data.scenes.new('B50 display scene');comp.collection.objects.link(sc.camera);comp.camera=sc.camera;comp.render.engine='BLENDER_WORKBENCH'
 comp.render.resolution_x=a.shape[1];comp.render.resolution_y=a.shape[0];comp.render.resolution_percentage=100;comp.render.use_compositing=True;comp.render.use_sequencer=False
 for k in ['view_transform','look','exposure','gamma']:setattr(comp.view_settings,k,getattr(sc.view_settings,k))
 comp.compositing_node_group=tree
 im=bpy.data.images.new('B50 linear buffer',width=a.shape[1],height=a.shape[0],alpha=True,float_buffer=True);im.alpha_mode='PREMUL';im.pixels.foreach_set(a[::-1].copy().ravel());im.update()
 node=tree.nodes.new('CompositorNodeImage');node.image=im
 for old in list(tree.nodes):
  if old.type=='R_LAYERS':
   for link in list(tree.links):
    if link.from_node==old and link.from_socket.name=='Image':tree.links.new(node.outputs['Image'],link.to_socket)
   tree.nodes.remove(old)
 if not glare:tree.links.new(node.outputs['Image'],next(n for n in tree.nodes if n.type=='GROUP_OUTPUT').inputs['Image'])
 comp.render.image_settings.media_type='IMAGE';comp.render.image_settings.file_format='PNG';comp.render.image_settings.color_mode='RGBA';comp.render.image_settings.color_depth='8';comp.render.filepath=str(p)
 bpy.ops.render.render(write_still=True,scene=comp.name)
 bpy.data.scenes.remove(comp);bpy.data.images.remove(im);bpy.data.node_groups.remove(tree)
def catch_pass():
 sc=load(True);config(sc,samples=16)
 metadata=dict(source='cloud/bundle/scene.blend',source_sha256=hashlib.sha256((ROOT/'cloud/bundle/scene.blend').read_bytes()).hexdigest(),camera_matrix=[v for r in sc.camera.matrix_world for v in r],ortho=sc.camera.data.ortho_scale,resolution=[3840,2160],phase=0,gpu=gpu(sc))
 savejson(WORK/'capture-metadata.json',metadata)
 for o in sc.objects:
  if o.type=='LIGHT':o.hide_render=True
 sc.world=bpy.data.worlds.new('B50 black sky');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
 cache={}
 for o in sc.objects:
  if o.type not in ['MESH','CURVE','FONT'] or o.hide_render:continue
  ok=eligible(o)
  if o.data.users>1:o.data=o.data.copy()
  old=list(o.data.materials);o.data.materials.clear()
  key=ok
  if key not in cache:cache[key]=material(None,ok,'catch')
  for _ in old or [None]:o.data.materials.append(cache[key])
 data=bpy.data.lights.new('B50 straight overhead exposure','SUN');data.energy=math.pi;data.angle=0
 sun=bpy.data.objects.new('B50 straight overhead exposure',data);sc.collection.objects.link(sun)
 sc.cycles.max_bounces=0;sc.cycles.diffuse_bounces=0;sc.cycles.glossy_bounces=0;sc.cycles.transmission_bounces=0
 aovs(sc);capture(sc,'catch-linear')
 log('Native exposure + position/normal/index complete')
def process():
 raw=pixels(WORK/'catch-linear.exr')[:,:,:3].mean(axis=2)
 files=list((WORK/'aov').glob('*.exr'));log([p.name for p in files])
 pos=pixels(next(p for p in files if p.name.startswith('B50Position')))[:,:,:3]
 normal=pixels(next(p for p in files if p.name.startswith('B50Normal')))[:,:,:3]
 ids=pixels(next(p for p in files if p.name.startswith('B50Index')))[:,:,0]
 catch=np.clip(raw,0,1);catch[catch<1/1024]=0
 # A rim must neighbour a physical lower surface, rather than a mere shadow boundary.
 z=pos[:,:,2];rim=np.zeros(z.shape,bool);valid=catch>.02
 for dy,dx in [(0,6),(0,-6),(6,0),(-6,0),(4,4),(4,-4),(-4,4),(-4,-4)]:
  edge=valid.copy()
  for factor in [1,5/3,7/3]:
   oy,ox=round(dy*factor),round(dx*factor);zz=np.roll(z,(oy,ox),(0,1))
   offset=RIGHT*(-ox)/(PPU*2)+UP*oy/(PPU*2)
   denominator=np.sum(normal*NORMAL,axis=2)
   tangent_z=offset[2]-NORMAL[2]*np.divide(np.sum(normal*offset,axis=2),denominator,out=np.zeros_like(z),where=np.abs(denominator)>.1)
   edge &= (z+tangent_z-zz)>.018
  # A drop must persist beyond the boundary: narrow joints between paving slabs are not outer rims.
  rim |= edge
 rim[:7]=False;rim[-7:]=False;rim[:,:7]=False;rim[:,-7:]=False
 # These individual paving slabs form one sidewalk. Their internal joints are not drop edges.
 sidewalk=(np.abs(z)<.012)&(-pos[:,:,1]>=9.15)&(-pos[:,:,1]<=10.50)
 rim[sidewalk & (-pos[:,:,1]<10.40)]=False
 rim=catch*rim
 rows=json.loads((WORK/'scene-inventory.json').read_text());roofs=[r for r in rows if not r['hide'] and ('roof' in r['name'].lower()) and 'bead' not in r['name'].lower() and r['bounds'][5]<900]
 top=max(r['bounds'][5] for r in roofs)/ZPP
 street=next(r['bounds'][5] for r in rows if r['name']=='Wet street')/ZPP
 height=np.clip((z-street)/(top-street),0,1)*(catch>.5/255)
 np.savez_compressed(WORK/'surface-data.npz',catch=catch,rim=rim,height=height,position=pos,normal=normal,ids=ids)
 stats={}
 for name,a in [('catch',catch),('rim',rim),('height',height)]:
  for suffix,q in [('@2x',a),('',area2(a))]:
   u=np.rint(np.clip(q,0,1)*255).astype(np.uint8)
   if name=='height':u[(catch if suffix else area2(catch))<=.5/255]=0
   png(OUT/(name+suffix+'.png'),u)
   stats[name+suffix]=dict(min=int(u.min()),max=int(u.max()),nonzero=int(np.count_nonzero(u)),size=[u.shape[1],u.shape[0]])
 savejson(WORK/'pass-stats.json',dict(maps=stats,street_world_z=street,street_screen_z=street*ZPP,top_roof_world_z=top,top_roof_screen_z=top*ZPP,top_roof_screen_height=(top-street)*ZPP,raw_catch_max=float(raw.max()),raw_catch_p99=float(np.percentile(raw,99))))
 log(('MAPS',stats,'top',top*ZPP))
def light_pass():
 sc=load(True);config(sc,samples=32,denoise=True);cache={}
 # Keep all night lights and emissive materials. Only rain-receiving opaque objects become white matte.
 for o in sc.objects:
  if o.type not in ['MESH','CURVE','FONT'] or o.hide_render or not eligible(o):continue
  if o.data.users>1:o.data=o.data.copy()
  for i,ma in enumerate(list(o.data.materials)):
   if not ma:continue
   emitting=ma.node_tree and any((n.type=='EMISSION' and n.inputs['Strength'].default_value>0) or (n.type=='BSDF_PRINCIPLED' and (n.inputs['Emission Strength'].is_linked or n.inputs['Emission Strength'].default_value>0)) for n in ma.node_tree.nodes)
   if emitting:continue
   if ma.name not in cache:cache[ma.name]=material(ma,True,'light')
   o.data.materials[i]=cache[ma.name]
 a=pixels(WORK/'light-linear.exr') if MODE=='exportlight' else capture(sc,'light-linear');s=np.load(WORK/'surface-data.npz');c=s['catch'];a[:,:,:3]*=c[:,:,None];a[:,:,3]=1
 np.save(WORK/'light-masked-linear.npy',a)
 for suffix,q in [('@2x',a),('',area2(a))]:
  p=WORK/('light-display'+suffix+'.png');display(sc,q,p,False)
  im=bpy.data.images.load(str(p),check_existing=False);im.colorspace_settings.name='Non-Color';w,h=im.size;b=np.empty(w*h*4,np.float32);im.pixels.foreach_get(b);bpy.data.images.remove(im)
  b=np.rint(b.reshape(h,w,4)[::-1]*255).clip(0,255).astype(np.uint8)[:,:,:3]
  support=c if suffix else area2(c);b[support<=.5/255]=0;png(OUT/('light'+suffix+'.png'),b)
 log('Night irradiance captures exported')
def mesh_obj(name,verts,faces,mat,sc,collections=()):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);me.materials.append(mat)
 for cn in collections:
  col=bpy.data.collections.get(cn)
  if col and o.name not in col.objects:col.objects.link(o)
 return o
def volume_material():
 ma=bpy.data.materials.new('B50 physical non-emissive white-grey spray volume');ma.use_nodes=True;t=ma.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');vol=t.nodes.new('ShaderNodeVolumeScatter');vol.inputs['Color'].default_value=(.88,.91,.94,1);vol.inputs['Anisotropy'].default_value=.15
 tex=t.nodes.new('ShaderNodeTexNoise');tex.noise_dimensions='3D';tex.inputs['Scale'].default_value=32;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.7
 geo=t.nodes.new('ShaderNodeNewGeometry');t.links.new(geo.outputs['Position'],tex.inputs['Vector'])
 den=mathnode(t,'MULTIPLY',mathnode(t,'MAXIMUM',mathnode(t,'SUBTRACT',tex.outputs['Fac'],.28),0),4.0)
 t.links.new(den,vol.inputs['Density']);t.links.new(vol.outputs[0],out.inputs['Volume']);return ma
def water_material():
 ma=bpy.data.materials.new('B50 physical crown and broken water droplets');ma.use_nodes=True;p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.85,.92,1,1);p.inputs['Roughness'].default_value=.12;p.inputs['IOR'].default_value=1.333;p.inputs['Transmission Weight'].default_value=.72;p.inputs['Coat Weight'].default_value=.3;return ma
def build_mist(sc):
 t=time.perf_counter();d=np.load(WORK/'surface-data.npz');c=d['catch'];pos=d['position'];normal=d['normal'];ids=np.rint(d['ids']).astype(int);rim=d['rim']
 records={r['id']:r for r in json.loads((WORK/'object-ids.json').read_text())};rng=np.random.default_rng(505017)
 linked={col.name for o in sc.objects if o.type=='LIGHT' for col in [o.light_linking.receiver_collection] if col}
 groups={};drops={};count=0;rejected=0;crowns=0
 # Adaptive camera-grid tessellation lies on the actual world-space surface planes.
 def cell(y,x,size):
  nonlocal count,rejected,crowns
  cy=y+size//2;cx=x+size//2
  if cy>=2160 or cx>=3840:return
  if c[cy,cx]<.35:return
  rec=records.get(int(ids[cy,cx]));n=normal[cy,cx].astype(float);n/=max(np.linalg.norm(n),1e-6)
  if not rec or not rec['eligible'] or n[2]<.35:return
  p=pos[cy,cx].astype(float);y1=min(y+size-1,2159);x1=min(x+size-1,3839)
  coords=[(y,x),(y,x1),(y1,x1),(y1,x)];good=all(c[yy,xx]>.30 and abs(float(pos[yy,xx,2]-p[2]))<.045 for yy,xx in coords)
  if not good:
   if size>2:
    half=size//2
    for yy in [y,y+half]:
     for xx in [x,x+half]:cell(yy,xx,half)
   else:rejected+=1
   return
  cols=tuple(sorted(set(rec['collections'])&linked));vs,fs=groups.setdefault(cols,([],[]));dv,df=drops.setdefault(cols,([],[]))
  height=float(rng.uniform(.035,.105));height*=1.15 if rim[cy,cx]>.1 else 1
  corners=[]
  for dx,dy in [(-size/2,-size/2),(size/2,-size/2),(size/2,size/2),(-size/2,size/2)]:
   off=RIGHT*dx/(PPU*2)-UP*dy/(PPU*2);off-=NORMAL*np.dot(n,off)/max(np.dot(n,NORMAL),.1);corners.append(p+off+np.array([0,0,.002]))
  base=len(vs);vs.extend(tuple(q) for q in corners);vs.extend(tuple(q+np.array([0,0,height])) for q in corners)
  # Screen-clockwise corners are clockwise in XY: reverse the standard box faces for outward normals.
  fs.extend(tuple(base+k for k in reversed(f)) for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
  count+=1
  # Deterministic single exposure: irregular crown rims and sub-centimetre broken droplets.
  if rng.random()<(.45 if rim[cy,cx]>.1 else .14):
   radius=float(rng.uniform(.010,.026));h=float(rng.uniform(.015,.065));b=len(dv)
   for j in range(10):
    ang=j*math.tau/10;r=radius*(1+.22*rng.random());zz=.005+h*(1 if j%2==0 else .25)
    dv.extend([tuple(p+np.array([r*math.cos(ang),r*math.sin(ang),zz])),tuple(p+np.array([r*.84*math.cos(ang),r*.84*math.sin(ang),zz-.004]))])
   df.extend((b+2*j,b+2*((j+1)%10),b+2*((j+1)%10)+1,b+2*j+1) for j in range(10));crowns+=1
   for j in range(3):
    q=p+np.array([rng.uniform(-.035,.035),rng.uniform(-.035,.035),rng.uniform(.025,.15)]);r=float(rng.uniform(.0012,.0035));b=len(dv)
    dv.extend(tuple(q+np.array(off)*r) for off in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1.5),(0,0,-1.5)])
    df.extend(tuple(b+i for i in f) for f in [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)])
 for y in range(0,2160,8):
  for x in range(0,3840,8):cell(y,x,8)
 vm=volume_material();wm=water_material();objects=[]
 for i,(cols,(v,f)) in enumerate(groups.items()):
  objects.append(mesh_obj('B50 surface spray volume '+str(i),v,f,vm,sc,cols))
  dv,df=drops[cols]
  if dv:objects.append(mesh_obj('B50 crowns and droplets '+str(i),dv,df,wm,sc,cols))
 report=dict(volume_cells=count,boundary_rejections=rejected,crowns=crowns,broken_droplets=crowns*3,objects=len(objects),receiver_signatures=len(groups),height_world_units=[.035,.12075],droplet_max_height=.15,build_seconds=time.perf_counter()-t,emission=0)
 savejson(WORK/'physical-mist.json',report);log(report);return objects
def baked():
 sc=load(False);config(sc,1920,1080,48,True);tree=sc.compositing_node_group
 sc.cycles.volume_bounces=2;sc.cycles.volume_step_rate=.5
 # Both exposures use the exact same phase, lights, materials, camera and seed.
 before=capture(sc,'before-linear');sc.compositing_node_group=tree;display(sc,before,WORK/'before.png',True)
 objects=build_mist(sc);bpy.context.view_layer.update()
 sc.cycles.volume_bounces=2;sc.cycles.volume_step_rate=.5
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'mist-sample.blend'),compress=True)
 after=capture(sc,'mist-baked-linear');sc.compositing_node_group=tree;display(sc,after,OUT/'mist-baked.png',True)
 log('One baked mist phase complete')
def refine():
 import bmesh
 bpy.ops.wm.open_mainfile(filepath=str(WORK/'mist-sample.blend'));sc=bpy.context.scene;config(sc,1920,1080,48,True);tree=sc.compositing_node_group
 for o in sc.objects:
  if o.name.startswith('B50 surface spray volume'):
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'mist-sample-final.blend'),compress=True)
 a=capture(sc,'mist-baked-final-linear');sc.compositing_node_group=tree;display(sc,a,OUT/'mist-baked.png',True)
 log('Final bake: corrected outward volume normals, same phase and seed')
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'catch'
if MODE=='catch':catch_pass();process()
elif MODE=='process':process()
elif MODE in ['light','exportlight']:light_pass()
elif MODE=='baked':baked()
elif MODE=='refine':refine()
