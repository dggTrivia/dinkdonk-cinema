"""Render actual 3D tumbling popcorn and occluded sign/screen masks.

The scene is black except for the selected light contribution. Glass attenuates
the moving kernels and the unchanged kettle/cabinet geometry occludes them.
"""
import sys,json,math,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import build_scene as b
from common import ROOT,xyz,project,ZPP,render

QA=ROOT/'qa4';N=72;TIMES=[]

def emission(name,color):
    mat=bpy.data.materials.new(name);n=mat.node_tree.nodes;n.clear()
    em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(*color,1)
    out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(em.outputs[0],out.inputs[0])
    return mat

def crop(sc,rect,scale=2):
    x,y,w,h=rect;sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=min(1,(x+w+.1)/1920)
    sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=min(1,(1080-y+.1)/1080)

def rect_for(objects,pad=3):
    bpy.context.view_layer.update()
    points=[project(q.x,-q.y,q.z*ZPP) for ob in objects for p in ob.bound_box for q in [ob.matrix_world@Vector(p)]]
    x=math.floor(min(p[0] for p in points))-pad;y=math.floor(min(p[1] for p in points))-pad
    w=math.ceil(max(p[0] for p in points))+pad-x;h=math.ceil(max(p[1] for p in points))+pad-y
    return [x,y,w+(w%2),h+(h%2)]

def ticket_letter_object(source,white):
    # Isolate the fifth glyph (E) from the evaluated original heading mesh.
    # Connected face x-intervals yield the seven ink glyphs including extrusion.
    deps=bpy.context.evaluated_depsgraph_get();ev=source.evaluated_get(deps);mesh=ev.to_mesh()
    intervals=sorted((min(mesh.vertices[i].co.x for i in p.vertices),max(mesh.vertices[i].co.x for i in p.vertices)) for p in mesh.polygons)
    merged=[]
    for a,c in intervals:
        if merged and a<=merged[-1][1]+.0001:merged[-1][1]=max(merged[-1][1],c)
        else:merged.append([a,c])
    assert len(merged)==7,merged
    a,c=merged[4]
    selected=[p for p in mesh.polygons if a-.0001<=sum(mesh.vertices[i].co.x for i in p.vertices)/len(p.vertices)<=c+.0001]
    vertices=[];faces=[]
    for poly in selected:
        start=len(vertices);vertices.extend([mesh.vertices[i].co.copy() for i in poly.vertices]);faces.append(tuple(range(start,len(vertices))))
    ob=b.mesh('Pass4 isolated E phosphor',vertices,faces,white);ob.matrix_world=source.matrix_world.copy()
    ev.to_mesh_clear();return ob

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=32)
    ap.add_argument('--masks-only',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    started=time.perf_counter();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass4.blend'))
    sc=bpy.context.scene;sc.cycles.samples=args.samples;sc.cycles.adaptive_threshold=.015
    # These tiny emission/occlusion crops render quickly on CPU; no GPU setup
    # dependency is inherited from the saved beauty scene.
    sc.cycles.device='CPU'
    sc.cycles.use_denoising=False;sc.cycles.max_bounces=4;sc.cycles.transparent_max_bounces=12
    sc.render.film_transparent=False;sc.render.use_compositing=False
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    black=emission('Pass4 black occlusion',(0,0,0));white=emission('Pass4 surface mask',(1,1,1))
    original={}
    for ob in sc.objects:
        if ob.type=='LIGHT':ob.hide_render=True
        if ob.type in ['MESH','FONT','CURVE']:
            ob.visible_camera=True;ob.is_holdout=False
            original[ob.name]=list(ob.data.materials)
            for i in range(len(ob.data.materials)):ob.data.materials[i]=black
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    source=bpy.data.objects['Tickets heading'];glyph=ticket_letter_object(source,white)
    glyph.visible_camera=False
    logo=b.text('Pass4 Soda logo','SODA',xyz(8.39,3.449,63),.075,white,rotation=b.FRONT_FACE)
    logo.visible_camera=False
    specs=[]
    # Rects for animated popcorn include their glass and four black border pixels.
    poprects=[[1048,553,68,66],[1112,585,68,66]]
    for i,rect in enumerate(poprects):specs.append({'name':'popcorn_'+str(i+1),'rect':rect,'parent':'partition_right','kind':'popcorn','machine_u':6.0+i*1.06})
    groups=[]
    for i,ob in enumerate(sorted([o for o in sc.objects if o.name.startswith('Menu glowing paper')],key=lambda o:o.name)):
        groups.append(('menu_'+['popcorn','soda','nachos'][i],[ob],'partition_right','menu'))
    groups += [('arcade_attract',[bpy.data.objects['Arcade CRT dark glass']],'arcade','arcade'),
               ('soda_logo',[logo]+[o for o in sc.objects if o.name.startswith('Soda selection button')],'partition_right','soda'),
               ('tickets_letter_e',[glyph],'partition_left','ticket')]
    for name,objects,parent,kind in groups:
        for ob in objects:
            ob.visible_camera=True
            for i in range(len(ob.data.materials)):ob.data.materials[i]=white
        if kind=='arcade':
            for ob in sc.objects:
                if ob.name.startswith('CRT game pixels'):ob.visible_camera=False
        if kind=='ticket':source.visible_camera=False
        rect=rect_for(objects,4);crop(sc,rect)
        render(QA/'prop_masks'/(name+'@2x.png'))
        specs.append({'name':name,'rect':rect,'parent':parent,'kind':kind})
        for ob in objects:
            for i in range(len(ob.data.materials)):ob.data.materials[i]=black
        glyph.visible_camera=False;logo.visible_camera=False;source.visible_camera=True
        for ob in sc.objects:
            if ob.name.startswith('CRT game pixels'):ob.visible_camera=True
    (QA/'prop_specs.json').write_text(json.dumps({'fps':24,'frames':N,'seconds':3,'specs':specs},indent=2))
    if args.masks_only:return
    # Restore only glass transmission, with all non-particle surfaces absorbing.
    glass=bpy.data.materials.new('Pass4 kernel through glass');n=glass.node_tree.nodes;n.clear()
    tr=n.new('ShaderNodeBsdfTransparent');tr.inputs[0].default_value=(.68,.74,.76,1)
    out=n.new('ShaderNodeOutputMaterial');glass.node_tree.links.new(tr.outputs[0],out.inputs[0])
    for ob in sc.objects:
        if ob.name.startswith('Popper glass panel'):ob.data.materials[0]=glass
    mat=emission('Pass4 lobed kernel',(.8,.59,.28));n=mat.node_tree.nodes;links=mat.node_tree.links
    em=n.get('Emission');geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    dot.inputs[1].default_value=(.35,-.45,.82);links.new(geo.outputs['Normal'],dot.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.10,.045,.009,1)
    ramp.color_ramp.elements[1].color=(.62,.39,.11,1);links.new(dot.outputs['Value'],ramp.inputs[0]);links.new(ramp.outputs[0],em.inputs[0])
    kernels=[]
    for machine,u in enumerate([6.0,7.06]):
        for i in range(9):
            root=bpy.data.objects.new('Popping kernel '+str(machine)+' '+str(i),None);sc.collection.objects.link(root)
            for j,(x,y,z,r) in enumerate([(0,0,0,.018),(.017,0,.007,.014),(-.012,.008,.007,.013),(.004,-.015,.012,.014),(.002,.006,-.014,.012)]):
                ob=b.ball('Kernel lobe',(x,y,z),r,mat,(1,.85,1.1));ob.parent=root
            kernels.append((root,machine,i,u))
    rect=[1048,553,132,98];crop(sc,rect)
    for frame in range(N+1):
        t=(frame%N)/N
        for root,machine,i,u in kernels:
            freq=1+(i%3);phase=(t*freq+i*.127+machine*.19)%1;life=phase/.62
            active=life<1
            p=min(life,1);fade=min(1,p*15,(1-p)*15) if active else 0
            root.scale=(max(0,fade),)*3
            root.location=xyz(u+.10+(i%4)*.13+.045*math.sin(p*math.tau+i),3.20+(i%3)*.068,43+16*math.sin(p*math.pi))
            root.rotation_euler=(p*math.tau*2+i,p*math.tau*3+machine,p*math.tau*2.0+i*.3)
        render(QA/'popcorn_raw'/('f'+str(frame).zfill(3)+'@2x.png'))
        if frame%12==0:print('POPCORN_FRAME',frame,'/',N,flush=True)
    (QA/'prop_render_times.json').write_text(json.dumps({'seconds':round(time.perf_counter()-started,3),'popcorn_frames':N,'endpoint_frame':N,'samples':args.samples,'combined_rect':rect},indent=2))

if __name__=='__main__':main()
