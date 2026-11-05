"""One-process rendering, resumable buffers and periodic scene state."""
import os,json,time,math,hashlib,random
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
import build_scene as b
from common import ROOT,xyz,ZPP,project,quality,gpu

WORK=ROOT/'work';WORK.mkdir(exist_ok=True)
def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.partial');tmp.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(tmp,path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def log(stage,**data):
    row={'time':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'stage':stage,**data}
    line=json.dumps(row);print('LOCAL56_PROGRESS '+line,flush=True)
    with (ROOT/'progress.log').open('a',encoding='utf-8') as f:f.write(line+'\n')
def pixels(path):
    im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im);return a.reshape(h,w,4)[::-1].copy()
def rgba8(path):
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im);return np.rint(np.clip(a.reshape(h,w,4)[::-1],0,1)*255).astype(np.uint8)
def png(path,a):
    # Portable stdlib PNG encoder; no external Python packages.
    import struct,zlib
    a=np.asarray(a,np.uint8);h,w,c=a.shape;d=a.copy();d[:,1:]=(a[:,1:].astype(np.int16)-a[:,:-1]).astype(np.uint8)
    scan=np.concatenate([np.ones((h,1),np.uint8),d.reshape(h,w*c)],axis=1)
    def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6 if c==4 else 2,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(scan.tobytes(),6))+chunk(b'IEND',b'')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.partial');tmp.write_bytes(data);os.replace(tmp,path)
def diff(a,c):
    d=np.abs(a[:,:,:3].astype(np.float64)-c[:,:,:3]);return dict(mean=float(d.mean()),p99=float(np.percentile(d,99)),max=float(d.max()))
def within(x,base):return x['mean']<=base['mean']+1e-7 and x['p99']<=base['p99']+1e-7

class Renderer:
    def __init__(self,width=1280,height=720):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'));self.sc=bpy.context.scene;self.width=width;self.height=height
        from screen_door_fix import repair_screen_doors
        repair_screen_doors(self.sc)
        # Blender canonicalizes relative separators to the loading host. Always
        # normalize before resolving fallback paths; packed data is authoritative.
        for asset in list(bpy.data.images)+list(bpy.data.fonts):
            if asset.filepath.startswith('//'):asset.filepath=asset.filepath.replace('\\','/')
        quality(self.sc,width,height);self.devices=gpu(self.sc);self.sc.render.use_compositing=False
        self.original={o.name:list(o.data.materials) for o in self.sc.objects if o.type in ['MESH','CURVE','FONT']}
        self.visible={o.name:(o.visible_camera,o.hide_render,o.is_holdout) for o in self.sc.objects if o.type in ['MESH','CURVE','FONT']}
        self.masks={};self.sites=json.loads((ROOT/'assets/impact_sites.json').read_text(encoding='utf-8'));self.rain=[]
        self.meta=json.loads((ROOT/'production.json').read_text(encoding='utf-8'))
        self.signature=sha(ROOT/'scene.blend');self.code_signature=sha(Path(__file__));self.wet=set()
        self.chase=[]
        for o in self.sc.objects:
            if o.name.startswith('D13 marquee bulb '):
                ma=o.data.materials[0].copy();ma.name='Cloud amber chase '+str(o['marquee_index'])
                o.data.materials[0]=ma;self.original[o.name]=[ma]
                self.chase.append((o,ma,int(o['future_chase_group'])))
            if o.name in ['D10 stateless edge drips and impact crowns','D10 stateless gutter and AC pours']:
                o.cycles.use_motion_blur=False
        for o in self.sc.objects:
            if o.type not in ['MESH','CURVE','FONT']:continue
            mats=list(o.data.materials)
            # Glass, glossy receivers and changing emitters stay in the dynamic
            # layer. The dry plate is deliberately conservative.
            moving=bool(o.get('d6_tube_state'))
            for ma in mats:
                if not ma or not ma.node_tree:continue
                moving|=ma.get('variable_water_film',False) or any(k in ma.name.lower() for k in ['water','wet','glass','neon','tube','mirror'])
                for n in ma.node_tree.nodes:
                    if n.type=='BSDF_PRINCIPLED':moving|=n.inputs['Metallic'].is_linked or n.inputs['Metallic'].default_value>.1 or n.inputs['Transmission Weight'].default_value>0 or n.inputs['Roughness'].default_value<.4
            if moving:self.wet.add(o.name)
        self.circuits=[o for o in self.sc.objects if o.get('d6_tube_state')]
        self.circuit_materials={base:next((m for m in bpy.data.materials if m.name.startswith('D10 wet ') and m.name.endswith(' | '+base)),None) or bpy.data.materials.get(base) for base in {o['d6_on_material'] for o in self.circuits}|{'D6 unlit neon glass'}}
        self._phase=None;self._visibility=None;self._excluded=set()
        self.add_rain();self.phase(0)
        log('scene_loaded',devices=self.devices,wet_objects=len(self.wet),total_geometry=len(self.original))
    def add_rain(self):
        rng=random.Random(161005);b.layer('cloud_rain')
        ma=b.glass('Cloud airborne rain',(.45,.54,.64),.24);p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.15;p.inputs['Coat Weight'].default_value=.6;p.inputs['Emission Color'].default_value=(.12,.16,.22,1);p.inputs['Emission Strength'].default_value=.15
        regions=[(-12,9.18,23,13.5,.12,640),(-5,-1,-.075,8.7,235.2,120),(-4,-13,25,-.23,240.2,500),(13.08,.05,15,9,.08,80),(15,.6,17.5,6.4,58.1,35),(15,6.5,17.5,9.1,61.1,30),(-9.4,3.4,-5.1,7.35,95.1,30)]
        for a,v,c,w,z,count in regions:
            for j in range(count):
                u=rng.uniform(a,c);vv=rng.uniform(v,w);zz=z+rng.uniform(3,190);length=rng.uniform(5,18)
                o=b.line('Cloud periodic rain',[xyz(u,vv,zz),xyz(u+.018,vv-.006,zz-length)],ma,rng.uniform(.0015,.0037));o.visible_shadow=False;o['cloud_group']='weather';o.hide_render=True
                self.rain.append((o,o.location.copy(),z,zz))
                for cname in ['P8 surroundings light receivers','P10 multiplex roof light receivers']:
                    col=bpy.data.collections.get(cname)
                    if col:col.objects.link(o)
        self.rain_names={o.name for o,_,_,_ in self.rain}
    def phase(self,frame):
        if getattr(self,'_phase',None)==frame%48:return
        # Geometry Nodes Scene Time and curb-flow drivers must advance too.
        self.sc.frame_set(frame%48+1)
        t=(frame%48)/24
        group=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];group.nodes['Time seconds'].outputs[0].default_value=t
        ob=self.sc.objects['D5 periodic wet micro impacts'];arr=[]
        for s in self.sites:
            age=(t/2-s['phase'])%1;f=math.sin(math.pi*age/s['duration'])**2 if age<s['duration'] else 0;r=s['radius']*f;p=Vector(s['point']);h=r*(1.5-age/max(s['duration'],1e-6))
            arr.extend([p+Vector((0,0,h)),p+Vector((r,0,0)),p+Vector((0,r,0)),p+Vector((-r,0,0)),p+Vector((0,-r,0)),p-Vector((0,0,r*.1))])
        ob.data.vertices.foreach_set('co',np.asarray(arr,np.float32).ravel());ob.data.update()
        state='A' if (frame%48)//12%2==0 else 'B'
        for o in self.circuits:
            if o.get('d6_tube_state'):
                base=o['d6_on_material'] if o['d6_tube_state']==state else 'D6 unlit neon glass'
                ma=self.circuit_materials[base]
                assert ma,('Missing neon circuit material',base)
                if self.original[o.name][0]!=ma:
                    self.original[o.name]=[ma];self._visibility=None
        # Four staggered, softly dimmed groups: one complete chase per 2 s.
        for o,ma,group in self.chase:
            level=.35+.65*(.5+.5*math.cos(math.tau*(frame%48/48-group/4)))
            for node in ma.node_tree.nodes:
                if node.type=='BSDF_PRINCIPLED':node.inputs['Emission Strength'].default_value=2.2*level
            lamp=self.sc.objects.get('D13 incandescent local spill %02d'%int(o['marquee_index']))
            if lamp:lamp.data.energy=.06*level
        for o,loc,z,zz in self.rain:
            # Integer wrap count gives a true 2-second period, including rain.
            height=190;dz=((zz-z-3-t*height)%height)-(zz-z-3);o.location=loc+Vector((0,0,dz/ZPP))
        bpy.context.view_layer.update()
        self._phase=frame%48
    def masked(self,ma):
        if ma.name in self.masks:return self.masks[ma.name]
        original_output=next(q for q in ma.node_tree.nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output)
        if not original_output.inputs['Surface'].links:return ma
        cp=ma.copy();cp.name='Cloud camera holdout '+ma.name;n=cp.node_tree.nodes;l=cp.node_tree.links;out=next(q for q in n if q.type=='OUTPUT_MATERIAL' and q.is_active_output)
        if not out.inputs['Surface'].links:return ma
        source=out.inputs['Surface'].links[0].from_socket;hold=n.new('ShaderNodeHoldout');ray=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader')
        l.new(ray.outputs['Is Camera Ray'],mix.inputs[0]);l.new(source,mix.inputs[1]);l.new(hold.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);self.masks[ma.name]=cp;return cp
    def visibility(self,part='all',split='full',rain=False):
        state=(part,split,rain)
        if getattr(self,'_visibility',None)==state:return
        for name,mats in self.original.items():
            o=self.sc.objects.get(name)
            if not o:continue
            group=o.get('cloud_group','background')
            selected=part=='all' or group==part or (part=='foreground' and group not in ['background','weather'])
            # Backgrounds exclude foreground camera rays, but keep indirect
            # lighting and shadows. Foreground passes keep the background as
            # a holdout and omit independently depth-sorted foreground peers.
            camera,hidden,original_holdout=self.visible[name]
            if o.hide_render!=hidden:o.hide_render=hidden
            if o.is_holdout!=original_holdout:o.is_holdout=original_holdout
            visible=camera and (selected or part=='weather' or (part not in ['all','background'] and group=='background'))
            if o.visible_camera!=visible:o.visible_camera=visible
            hold=(not selected) or (split=='dry' and name in self.wet) or (split=='wet' and name not in self.wet)
            # Geometry Nodes assigns its own materials to rain instances; an
            # object holdout is necessary when there are no object slots.
            if not mats and not hidden:o.is_holdout=original_holdout or hold
            for i,ma in enumerate(mats):
                desired=self.masked(ma) if hold and ma else ma
                if o.data.materials[i]!=desired:o.data.materials[i]=desired
            # Volume-only meshes have no opaque surface to hold out. Their
            # camera contribution is already in the background and must not
            # be accumulated again by foreground or precipitation overlays.
            if part not in ['all','background'] and not selected:
                outputs=[n for ma in mats if ma and ma.node_tree for n in ma.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output]
                if outputs and all(not n.inputs['Surface'].links for n in outputs):o.visible_camera=False
        for o,_,_,_ in self.rain:o.hide_render=not rain;o.is_holdout=False;o.visible_camera=True
        self.sc.render.film_transparent=part!='all' or split!='full' or rain
        self._visibility=state
    def capture(self,tag,part='all',split='full',frame=0,seed=1701,adaptive=False,threshold=.001,rain=False,rect=None,force=False,persistent=True,aov=False,state=None,exclude=None,mattes=False):
        started=time.perf_counter();timing={}
        key={'scene':self.signature,'runtime':self.code_signature,'size':[self.width,self.height],'part':part,'split':split,'frame':frame%48,'seed':seed,'adaptive':adaptive,'threshold':threshold,'rain':rain,'rect':rect,'persistent':persistent}
        if part=='weather':key['all_geometry_holdout']=3
        if part not in ['all','background']:key['nonselected_volume_camera']=False
        if state is not None:key['state']=state
        if exclude:key['excluded_objects']=sorted(exclude)
        if aov:key['position_aov']=1
        if mattes:key['cryptomatte_groups']=sha(ROOT/'production.json')
        folder=WORK/'buffers';folder.mkdir(exist_ok=True);path=folder/(tag+'.exr');receipt=folder/(tag+'.json')
        uvpath=WORK/'positions'/(tag+'.npz');uvpath.parent.mkdir(exist_ok=True)
        if not force and path.exists() and receipt.exists():
            r=json.loads(receipt.read_text());
            maskpath=WORK/'positions'/(tag+'_masks.npz')
            if r['key']==key and r['sha256']==sha(path) and (not aov or (uvpath.exists() and r.get('uv_sha256')==sha(uvpath))) and (not mattes or (maskpath.exists() and r.get('masks_sha256')==sha(maskpath))):
                log('render_cache_hit',tag=tag,original_seconds=r['seconds']);return pixels(path),r['seconds']
        t=time.perf_counter();self.phase(frame);timing['phase']=time.perf_counter()-t
        # Restore explicit exclusions even when the pass itself is unchanged.
        for name in getattr(self,'_excluded',set()):self.sc.objects[name].hide_render=self.visible[name][1]
        self._excluded=set(exclude or [])
        t=time.perf_counter();self.visibility(part,split,rain);timing['visibility']=time.perf_counter()-t
        sc=self.sc;t=time.perf_counter();quality(sc,self.width,self.height,adaptive,threshold);sc.cycles.seed=seed;sc.render.use_persistent_data=persistent
        for name in exclude or []:self.sc.objects[name].hide_render=True
        sc.render.film_transparent=part not in ['all','background'] or split!='full' or rain
        if rect:
            x,y,w,h=rect;sc.render.use_border=True;sc.render.use_crop_to_border=True
            sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x+w+.1)/1920;sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
        sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='32';sc.render.image_settings.exr_codec='ZIP'
        approved_tree=sc.compositing_node_group
        sc.view_layers[0].use_pass_cryptomatte_object=bool(mattes)
        if aov:
            self.position_output(tag);sc.render.use_compositing=True
        if mattes:self.matte_output(tag)
        timing['configuration']=time.perf_counter()-t
        tmp=path.with_name(path.stem+'.partial.exr');sc.render.filepath=str(tmp);start=time.perf_counter()
        try:
            bpy.ops.render.render(write_still=False,scene=sc.name)
            timing['render_sync_trace_compositor']=time.perf_counter()-start
            t=time.perf_counter();bpy.data.images['Render Result'].save_render(str(tmp),scene=sc);timing['exr_write']=time.perf_counter()-t
        finally:sc.compositing_node_group=approved_tree;sc.render.use_compositing=False
        seconds=time.perf_counter()-start;os.replace(tmp,path)
        t=time.perf_counter();record=dict(key=key,seconds=seconds,sha256=sha(path));timing['hash']=time.perf_counter()-t
        if aov:
            import depth_pass
            candidates=list((WORK/'position_raw'/tag).glob('*.exr'));assert len(candidates)==1,(tag,candidates)
            depth_pass.export_array(candidates[0],uvpath);record['uv_sha256']=sha(uvpath)
        if mattes:
            t=time.perf_counter();masks={}
            for spec in self.meta['groups']:
                raw=list((WORK/'matte_raw'/tag/spec['name']).glob('*.exr'));assert len(raw)==1,(spec['name'],raw)
                masks[spec['name']]=pixels(raw[0])[:,:,0]
            maskpath=WORK/'positions'/(tag+'_masks.npz');np.savez_compressed(maskpath,**masks);record['masks_sha256']=sha(maskpath);timing['mask_export']=time.perf_counter()-t
        t=time.perf_counter();result=pixels(path);timing['exr_read']=time.perf_counter()-t
        timing['total']=time.perf_counter()-started;record['timing']=timing
        atomic_json(receipt,record);log('render_done',tag=tag,seconds=seconds,timing=timing)
        return result,seconds
    def matte_output(self,tag):
        sc=self.sc;sc.view_layers[0].use_pass_cryptomatte_object=True;sc.view_layers[0].pass_cryptomatte_depth=6
        tree=sc.compositing_node_group
        for spec in self.meta['groups']:
            node=tree.nodes.new('CompositorNodeCryptomatteV2');node.source='RENDER';node.scene=sc;node.layer_name=sc.view_layers[0].name+'.CryptoObject';node.matte_id=','.join(spec['objects'])
            f=tree.nodes.new('CompositorNodeOutputFile');f.format.media_type='IMAGE';f.format.file_format='OPEN_EXR';f.format.color_mode='RGBA';f.format.color_depth='16';f.format.exr_codec='ZIP'
            folder=WORK/'matte_raw'/tag/spec['name'];folder.mkdir(parents=True,exist_ok=True);f.directory=str(folder);f.file_name='mask';f.file_output_items.new('RGBA','mask');tree.links.new(node.outputs['Matte'],f.inputs['mask'])
    def position_output(self,tag):
        sc=self.sc
        if 'FloorUV' not in sc.view_layers[0].aovs:
            aov=sc.view_layers[0].aovs.add();aov.name='FloorUV';aov.type='COLOR'
        for ma in bpy.data.materials:
            if not ma.node_tree or any(n.type=='OUTPUT_AOV' and n.aov_name=='FloorUV' for n in ma.node_tree.nodes):continue
            n=ma.node_tree.nodes;l=ma.node_tree.links;geo=n.new('ShaderNodeNewGeometry');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(1,-1,1);o=n.new('ShaderNodeOutputAOV');o.aov_name='FloorUV';l.new(geo.outputs['Position'],v.inputs[0]);l.new(v.outputs['Vector'],o.inputs['Color'])
        tree=bpy.data.node_groups.get('Cloud position output') or bpy.data.node_groups.new('Cloud position output','CompositorNodeTree');tree.nodes.clear()
        if not tree.interface.items_tree:tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
        out=tree.nodes.new('NodeGroupOutput');layer=tree.nodes.new('CompositorNodeRLayers');layer.scene=sc;tree.links.new(layer.outputs['Image'],out.inputs['Image'])
        f=tree.nodes.new('CompositorNodeOutputFile');f.format.media_type='IMAGE';f.format.file_format='OPEN_EXR';f.format.color_mode='RGBA';f.format.color_depth='32';f.format.exr_codec='ZIP'
        folder=WORK/'position_raw'/tag;folder.mkdir(parents=True,exist_ok=True);f.directory=str(folder);f.file_name='position';f.file_output_items.new('RGBA','FloorUV');tree.links.new(layer.outputs['FloorUV'],f.inputs['FloorUV']);sc.compositing_node_group=tree
    def display(self,a,path,glare=True):
        sc=self.sc
        name='Cloud compositor only';comp=bpy.data.scenes.get(name) or bpy.data.scenes.new(name)
        if sc.camera.name not in comp.collection.objects:comp.collection.objects.link(sc.camera)
        comp.camera=sc.camera;comp.render.engine='BLENDER_WORKBENCH';comp.render.resolution_x=a.shape[1];comp.render.resolution_y=a.shape[0];comp.render.resolution_percentage=100;comp.render.film_transparent=True;comp.render.use_sequencer=False
        comp.view_settings.view_transform=sc.view_settings.view_transform;comp.view_settings.look=sc.view_settings.look;comp.view_settings.exposure=sc.view_settings.exposure;comp.view_settings.gamma=sc.view_settings.gamma
        tree=sc.compositing_node_group.copy() if glare else bpy.data.node_groups.new('Cloud no glare','CompositorNodeTree')
        if not glare:tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');tree.nodes.new('NodeGroupOutput')
        comp.compositing_node_group=tree;comp.render.use_compositing=True
        im=bpy.data.images.new('Cloud linear combined buffer',width=a.shape[1],height=a.shape[0],alpha=True,float_buffer=True);im.alpha_mode='PREMUL';im.pixels.foreach_set(a[::-1].copy().ravel());im.update()
        node=tree.nodes.new('CompositorNodeImage');node.image=im
        for old in list(tree.nodes):
            if old.type=='R_LAYERS':
                links=[(l.from_socket.name,l.to_socket) for l in list(tree.links) if l.from_node==old]
                for output,target in links:
                    if output=='Image':tree.links.new(node.outputs['Image'],target)
                tree.nodes.remove(old)
        if not glare:tree.links.new(node.outputs['Image'],next(n for n in tree.nodes if n.type=='GROUP_OUTPUT').inputs['Image'])
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);comp.render.image_settings.media_type='IMAGE';comp.render.image_settings.file_format='PNG';comp.render.image_settings.color_mode='RGBA';comp.render.image_settings.color_depth='8';comp.render.filepath=str(path)
        bpy.ops.render.render(write_still=True,scene=comp.name)
        tree.nodes.remove(node);bpy.data.images.remove(im);comp.compositing_node_group=None;bpy.data.node_groups.remove(tree)
    def rect(self,objects,pad=6):
        bpy.context.view_layer.update();points=[project(p.x,-p.y,p.z*ZPP) for o in objects for corner in o.bound_box for p in [o.matrix_world@Vector(corner)]]
        x=max(0,math.floor(min(p[0] for p in points))-pad);y=max(0,math.floor(min(p[1] for p in points))-pad);r=min(1920,math.ceil(max(p[0] for p in points))+pad);d=min(1080,math.ceil(max(p[1] for p in points))+pad)
        return [x,y,r-x,d-y]
