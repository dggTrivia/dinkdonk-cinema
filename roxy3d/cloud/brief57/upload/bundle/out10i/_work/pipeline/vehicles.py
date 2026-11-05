"""Re-render changed route-05 bus bodies; preserve compatible light contracts."""
import math,json,copy,os,time
import bpy,numpy as np
from mathutils import Matrix,Vector
import build_scene as b
import build_vehicles as v
from common import ROOT,xyz,ZPP,setup,quality
from runtime import WORK,Renderer,rgba8,png,sha,atomic_json,log
from package_vehicles import shadow_body
from fast_pipeline import area2,position2
from fast_pipeline import NativeRenderer as Renderer
import package_vehicle_pass5 as slices

def build_model(opened):
    v.bus(opened)
    v.M['paint'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.15,.085,.035,1)
    for o in bpy.context.scene.objects:
        if o.name.startswith('Municipal transit lettering'):o.location.z=31/ZPP;o.data.size=.040
    for side in [-1,1]:
        v.box('Bus side advertisement frame',-.65,side*.414-.005,.65,side*.414+.005,19.5,29.2,'black',.008)
        v.box('Bus blank advertisement face',-.61,side*.421-.002,.61,side*.421+.002,20.5,28.2,'cream',.002)
        # The two approved Draft 5 bus artworks fit side by side inside the
        # existing replacement-ad quad. Preserve UV handedness on both sides.
        for key,lo,hi in [('boxing',-.61,-.015),('courier',.015,.61)]:
            ma=b.material('Bus approved '+key+' wet paper',(.5,.5,.5),.48)
            nodes=ma.node_tree.nodes;links=ma.node_tree.links;p=nodes.get('Principled BSDF')
            path=next((ROOT/'assets/textures').glob('*_'+key+'.png.png'))
            im=bpy.data.images.load(str(path),check_existing=True);tex=nodes.new('ShaderNodeTexImage');tex.image=im
            links.new(tex.outputs['Color'],p.inputs['Base Color']);links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
            p.inputs['Coat Weight'].default_value=.35;p.inputs['Coat Roughness'].default_value=.09
            noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
            bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0012
            links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
            a,c=(lo,hi) if side==1 else (-lo,-hi)
            ob=b.mesh('Bus approved '+key+' art '+str(side),[xyz(u,side*.424,z) for u,z in [(a,20.5),(c,20.5),(c,28.2),(a,28.2)]],[(0,1,2,3)],ma)
            uv=ob.data.uv_layers.new()
            for i,co in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=co
            ob['approved_meme']=key
    v.box('Bus rear plate',-1.342,-.13,-1.338,.13,23,27,'plate',.002)
    v.label('Bus fleet plate','DGG 05',(-1.346,0,25),.041,'rear','black')

def rebuild_bus(manifest,out,qa):
    # Geometry and lamp positions are unchanged. Add the pass-9 ad frame and
    # move the operator above it, retaining the existing ad-panel coordinates.
    reports=[];positions=qa/'positions';positions.mkdir(exist_ok=True)
    for direction in ['+u','-u']:
        entry=manifest['vehicles']['bus'][direction];label='plus' if direction=='+u' else 'minus'
        for opened in [False,True]:
            name='bus_'+label+('_open' if opened else '');variant=entry['door_open'] if opened else entry
            variant['default_ad_art']=['FROGS vs DINOS - THE REMATCH','CLIPPED & SHIPPED'];variant['default_ad_art_baked']=True
            for scale,key in [(2,'file_2x')]:
                sc=setup(256,scale,True);b.GROUPS.clear();b.META.clear();b.layer('vehicle');b.FONT=bpy.data.fonts.load(str(ROOT/'assets/fonts/arialbd.ttf'));v.palette('bus');before=set(sc.objects);build_model(opened);objects=set(sc.objects)-before;bpy.context.view_layer.update()
                pts=[o.matrix_world@Vector(c) for o in objects if o.type in ['MESH','CURVE','FONT'] for c in o.bound_box];fp=[min(p.x for p in pts),min(-p.y for p in pts),max(p.x for p in pts),max(-p.y for p in pts)];variant['geometry_local_footprint']=fp
                transform=Matrix.Translation(xyz(6,11))@Matrix.Rotation(math.pi if direction=='-u' else 0,4,'Z')
                for o in objects:o.matrix_world=transform@o.matrix_world
                v.lighting();quality(sc,1920*scale,1080*scale);sc.render.film_transparent=True
                # Shared render helper uses the identical AOV/EXR/display path as
                # smoke, without opening a second Blender process or source scene.
                r=Renderer.__new__(Renderer);r.sc=sc;r.width=1920*scale;r.height=1080*scale;r.signature=sha(ROOT/'scene.blend')+name;r.original={o.name:list(o.data.materials) for o in sc.objects if o.type in ['MESH','CURVE','FONT']};r.masks={};r.wet=set();r.rain=[];r.phase=lambda frame:None
                r.code_signature=sha(ROOT/'runtime.py');r.visible={o.name:(o.visible_camera,o.hide_render,o.is_holdout) for o in sc.objects if o.name in r.original}
                for o in sc.objects:
                    if o.type in ['MESH','CURVE','FONT']:o['cloud_group']='vehicle'
                a,_=r.capture(name+('_2x' if scale==2 else '_1x'),part='vehicle',rect=[300,630,610,400],aov=True,state={'route':'05','operator':'d.gg TRANSIT','opened':opened},adaptive=True,threshold=.01)
                uv=np.load(WORK/'positions'/(name+'_2x.npz'))['uv']
                for output_scale,key,buffer in [(2,'file_2x',a),(1,'file',area2(a))]:
                    display=WORK/(name+f'_{output_scale}.png');r.display(buffer,display,glare=False);body=shadow_body(rgba8(display),dict(scale=output_scale,border=[300,630,610,400],anchor_global=[600,860],length_tiles=2.6,width_tiles=.78))
                    x=300-entry['anchor'][0];y=230-entry['anchor'][1];w=entry['w'];h=entry['h'];cropped=body[y*output_scale:(y+h)*output_scale,x*output_scale:(x+w)*output_scale]
                    assert cropped.shape==(h*output_scale,w*output_scale,4);assert not np.any(cropped[[0,-1],:,3]) and not np.any(cropped[:,[0,-1],3]),('Bus sprite edge clipping',name,output_scale)
                    png(out/variant[key],cropped)
                    np.savez_compressed(positions/(name+('@2x' if output_scale==2 else '')+'.npz'),uv=uv if output_scale==2 else position2(uv,a[:,:,3]))
            slices.OUT=out;slices.QA=qa;reports.extend(slices.slice_vehicle(entry,variant,name,direction));log('bus_body_complete',direction=direction,opened=opened)
    atomic_json(qa/'bus_validation.json',reports);atomic_json(out/'manifest.json',manifest)
