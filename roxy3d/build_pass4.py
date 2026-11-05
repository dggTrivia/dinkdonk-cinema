"""Pass 4 lighting/material polish, preserving every layout-2 object transform.

Read-only reuse of the layout builder. Writes only qa4 and roxy_pass4.blend.
"""
import sys,json,time,argparse,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import build_scene as b
import build_pass2 as layout
import render_loop_basis as ambient
from common import ROOT,ZPP,xyz,project,render

QA=ROOT/'qa4';SOURCE=ROOT/'out3';TIMES=[]
ACTION=[('ticket_6',4.85,6),('ticket_7_4',4.85,7.4),
        ('snack_6_6',6.6,5.05),('snack_8_2',8.2,5.05),('snack_9_8',9.8,5.05),('gate',3.7,3.7)]

def multiply_color(mat,factor):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF')
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    previous=p.inputs['Base Color'].links
    if previous:links.new(previous[0].from_socket,mix.inputs[1])
    else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    mix.inputs[2].default_value=(*(factor if hasattr(factor,'__len__') else [factor]*3),1)
    links.new(mix.outputs[0],p.inputs['Base Color'])

def polish():
    # Copies are assigned only to floor motifs; candy and standee colours survive.
    colors=[(.104,.068,.110),(.071,.091,.100),(.112,.092,.079),(.079,.070,.109)]
    floor_mats={}
    for old,col in zip(['confetti pink','confetti cyan','confetti gold','confetti lilac'],colors):
        mat=b.M[old].copy();mat.name='Pass4 muted weave '+old
        p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1)
        p.inputs['Roughness'].default_value=1;floor_mats[old]=mat
    prefixes=('Woven Memphis carpet flecks','Worn carpet diamond','Faded lobby medallion','Lobby carpet piping','Runner brass thread')
    for ob in bpy.data.objects:
        if ob.name.startswith(prefixes):
            for i,mat in enumerate(ob.data.materials):
                if mat.name in floor_mats:ob.data.materials[i]=floor_mats[mat.name]
    # The existing worn entrance route becomes darker rather than chalky pale.
    carpet=b.M['carpet aubergine'];multiply_color(carpet,.88)
    for n in carpet.node_tree.nodes:
        if n.bl_idname=='ShaderNodeMixRGB' and tuple(round(x,3) for x in n.inputs[2].default_value[:3])==(.105,.079,.107):
            n.inputs[2].default_value=(.034,.027,.049,1)
    multiply_color(b.M['counter stone'],.64)
    b.M['counter stone'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.55
    # Tone down local counter/partition trim, retaining exterior neon and apertures.
    softened={}
    for ob in bpy.data.objects:
        if ob.name.startswith(('Ticket desk cyan edging','Snack counter pink edging','Lobby neon strip')):
            old=ob.data.materials[0]
            if old.name not in softened:
                mat=old.copy();mat.name='Pass4 restrained '+old.name
                mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value*=.30
                softened[old.name]=mat
            ob.data.materials[0]=softened[old.name]
    paper=b.M['soft menu'].copy();paper.name='Pass4 warm modest backlight'
    paper.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value*=.58
    multiply_color(paper,.85)
    for ob in bpy.data.objects:
        if ob.name.startswith(('Menu glowing paper','Tickets amber lightboard')):ob.data.materials[0]=paper
    # Old game pixels stay in the geometry, at a dark idle level under attract mode.
    idle=b.material('Pass4 idle CRT phosphor',(.004,.013,.018),.4,emit=.08)
    for ob in bpy.data.objects:
        if ob.name.startswith('CRT game pixels'):ob.data.materials[0]=idle
    for name,factor in [('Large soft cinema key',.76),('Warm lobby pool',.55),('Concession warm ceiling bounce',.60)]:
        bpy.data.objects[name].data.energy*=factor
    # Broad feathered spots centre precisely on customer positions, not counters.
    for name,u,v in ACTION:
        data=bpy.data.lights.new('Pass4 action pool '+name,'SPOT')
        data.energy=78 if name=='gate' else 90
        data.color=(1,.62,.28);data.spot_size=math.radians(65);data.spot_blend=1
        data.shadow_soft_size=.24
        ob=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(ob)
        ob.location=xyz(u,v,108);ob.rotation_euler=(xyz(u,v,0)-ob.location).to_track_quat('-Z','Y').to_euler()
    for number,(wall,t) in enumerate([('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)],1):
        u,v=(.30,t) if wall=='u' else (t,.30)
        b.area('Pass4 steady screen spill '+str(number),xyz(u,v,14),4.8,(1,.58,.24),.58,
               xyz(u+(.32 if wall=='u' else 0),v+(.32 if wall=='v' else 0),0),.16)

def build(samples=96):
    b.GROUPS.clear();b.META.clear();b.M.clear();b.RNG.seed(1997)
    sc=layout.build(samples,1);polish()
    return sc

def timed(path):
    start=time.perf_counter();render(path)
    TIMES.append({'file':str(path.relative_to(ROOT)),'seconds':round(time.perf_counter()-start,3)})
    (QA/'render_times.json').write_text(json.dumps(TIMES,indent=2))
    print('PASS4_RENDER',json.dumps(TIMES[-1]),flush=True)

def export_surfaces():
    # Exact object matrices are useful for attaching additive overlays to signs.
    wanted=['Tickets heading','Tickets amber lightboard','Menu glowing paper','Arcade CRT dark glass','Soda fountain dark face']
    result={}
    bpy.context.view_layer.update()
    for ob in bpy.data.objects:
        if any(ob.name.startswith(s) for s in wanted):
            coords=[ob.matrix_world@Vector(c) for c in ob.bound_box]
            result[ob.name]={'matrix_world':[list(row) for row in ob.matrix_world],
                'local_bounds':[list(c) for c in ob.bound_box],
                'screen_bounds':[project(c.x,-c.y,c.z*ZPP) for c in coords]}
    (QA/'prop_surfaces.json').write_text(json.dumps(result,indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['preview','final'],default='preview')
    ap.add_argument('--samples',type=int,default=96);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    QA.mkdir(exist_ok=True);sc=build(args.samples);export_surfaces()
    measured=layout.geometry_bounds();source=json.loads((SOURCE/'manifest.json').read_text())
    for e in source['occluders']:
        assert measured[e['name']]['geometry_footprint']==e['geometry_footprint'],e['name']
        assert measured[e['name']]['geometry_z_px']==e['geometry_z_px'],e['name']
    (QA/'geometry_bounds.json').write_text(json.dumps(measured,indent=2))
    if args.mode=='preview':timed(QA/'polish_preview.png');return
    sc.cycles.adaptive_threshold=.01
    for items in ambient.VARIABLES.values():items.clear()
    ambient.animated_materials();ambient.lighting()
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass4.blend'))
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        sc.render.use_border=False;sc.render.use_crop_to_border=False
        b.set_visibility();timed(QA/('cycles_minimum_full'+suffix+'.png'))
        b.set_visibility('background');timed(QA/'loop_basis'/('minimum'+suffix+'.png'))
        for e in source['occluders']:
            b.set_visibility(e['name']);ambient.crop(sc,e)
            timed(QA/'minimum_sprites'/(e['file'][:-4]+suffix+'.png'))
    sc.render.resolution_x=1920;sc.render.resolution_y=1080
    sc.render.use_border=False;sc.render.use_crop_to_border=False;b.set_visibility('background')
    for group in ambient.GROUPS:
        ambient.lighting(group);timed(QA/'loop_basis'/(group+'.png'))
    ambient.lighting();b.set_visibility()
    (QA/'loop_basis.json').write_text(json.dumps({'groups':ambient.GROUPS,'minimum_factors':ambient.MINIMUM,
        'animated_inputs':{k:len(v) for k,v in ambient.VARIABLES.items()},'seed':1701,'samples':args.samples,
        'static_prop_lights':source['loop_static_prop_lights'],
        'method':'Fixed Cycles light bases with pass4 material and action-pool changes.'},indent=2))

if __name__=='__main__':main()
