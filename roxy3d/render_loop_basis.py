"""Render one stable minimum-light scene and four positive light bases.

No per-frame denoising: animation interpolates these fixed Cycles results and
adds deterministic emission rain/splashes. Prop lights are deliberately static.
"""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_pass2 as layout
import build_scene as b
from common import ROOT,render

QA=ROOT/'qa2';OUT=ROOT/'out2';BASIS=QA/'loop_basis';SPRITES=QA/'minimum_sprites'
GROUPS=['neon','billboard','projector','reflections']
VARIABLES={k:[] for k in GROUPS}
MINIMUM={'neon':.10,'billboard':.10,'projector':.12,'reflections':.08}
TIMES=[]

def animated_materials():
    for obj in b.GROUPS['background']:
        group=None
        if obj.name.startswith(('Pink perimeter neon','Cyan low wall tube','Marquee pink tube')):group='neon'
        elif obj.name.startswith(('Billboard cyan inner rail','Billboard pink outer rail')):group='billboard'
        elif obj.name.startswith(('Porthole amber glass','Light under auditorium door')):group='projector'
        if not group or not obj.data.materials:continue
        original=obj.data.materials[0];mat=original.copy();mat.name='Loop '+group+' '+obj.name
        obj.data.materials[0]=mat
        p=mat.node_tree.nodes.get('Principled BSDF')
        value=p.inputs['Emission Strength'].default_value
        VARIABLES[group].append((p.inputs['Emission Strength'],'default_value',value))
    for obj in bpy.data.objects:
        if obj.type!='LIGHT':continue
        group='projector' if obj.name.startswith('Warm light leaking under screen') else ('reflections' if obj.name.startswith('Neon storefront reflected glow') else None)
        if group:VARIABLES[group].append((obj.data,'energy',obj.data.energy))

def lighting(active=None):
    for group,items in VARIABLES.items():
        for obj,attr,maximum in items:setattr(obj,attr,maximum*(1 if group==active else MINIMUM[group]))

def timed(path):
    start=time.perf_counter();render(path)
    TIMES.append({'file':str(path.relative_to(ROOT)),'seconds':round(time.perf_counter()-start,3)})
    (QA/'loop_render_times.json').write_text(json.dumps(TIMES,indent=2))
    print('LOOP_BASIS_RENDER',json.dumps(TIMES[-1]),flush=True)

def crop(sc,e):
    x,y,w,h=[e[k] for k in ['x','y','w','h']]
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=min(1,(x+w+.1)/1920)
    sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=min(1,(1080-y+.1)/1080)

def main():
    assert (QA/'manifest_stills_ready.json').exists(),'Publish still manifest first'
    BASIS.mkdir(exist_ok=True);SPRITES.mkdir(exist_ok=True)
    m=json.loads((QA/'manifest_stills_ready.json').read_text())
    sc=layout.build(96,1);sc.cycles.adaptive_threshold=.01
    (QA/'geometry_bounds.json').write_text(json.dumps(layout.geometry_bounds(),indent=2))
    animated_materials();lighting()
    sc['loop_minimum_factors']=json.dumps(MINIMUM)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass2_minimum.blend'))
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        sc.render.use_border=False;sc.render.use_crop_to_border=False
        b.set_visibility('background');timed(BASIS/('minimum'+suffix+'.png'))
        for e in m['occluders']:
            b.set_visibility(e['name']);crop(sc,e);timed(SPRITES/(e['file'][:-4]+suffix+'.png'))
    sc.render.resolution_x=1920;sc.render.resolution_y=1080
    sc.render.use_border=False;sc.render.use_crop_to_border=False;b.set_visibility('background')
    for group in GROUPS:
        lighting(group);timed(BASIS/(group+'.png'))
    lighting();b.set_visibility()
    (QA/'loop_basis.json').write_text(json.dumps({'groups':GROUPS,'minimum_factors':MINIMUM,
        'animated_inputs':{k:len(v) for k,v in VARIABLES.items()},'seed':1701,'samples':96,
        'method':'Fixed denoised light bases; no per-frame denoising.',
        'static_prop_lights':['partitions','tickets','snack','podium','arcade','street_lamp','roxy_blade','bus_stop','entrance_posts']},indent=2))

if __name__=='__main__':main()
