"""Pass 6 scene: separated title stacks, surface wear, hinged screen doors.

Only qa6/out6 and the new scene are written. Previous builders are read-only.
"""
import sys,json,math,random,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
import build_scene as b
import build_pass4 as prior
import build_pass2 as layout
import render_loop_basis as ambient
from common import ROOT,xyz,project,ZPP,UP,NORMAL,PPU,render

QA=ROOT/'qa6';SOURCE=ROOT/'out5';TIMES=[]
DOORS=[('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)]
# Wall coordinate of title centre, projected bottom y, poster inner interval.
STACKS=[(6.8333333333,396,[5.2,5.7],[20,90]),(3.5666666667,315,[2.8,3.3],[20,105]),
        (4.8,350,[5.5,6.1],[20,105]),(8.12,450,[8.9,9.5],[20,105]),(11.38,540,[11.9,12.5],[20,105])]
HEIGHTS=[92,92,92,80,92]
ORIGINAL_DOOR=b.door

def remove(ob):
    for objects in b.GROUPS.values():
        if ob in objects:objects.remove(ob)
    bpy.data.objects.remove(ob,do_unlink=True)

def tag(ob,number,side):ob['door_id']=str(number);ob['door_side']=side

def frame(wall,at,width,height,number):
    for a,c in [(at-width/2,at-width/2+.055),(at+width/2-.055,at+width/2)]:
        b.wallbox('Pass6 jamb '+str(number),wall,a,c,0,height,b.M['brushed nickel'],.007,.11)
    b.wallbox('Pass6 lintel '+str(number),wall,at-width/2,at+width/2,height-5,height,b.M['brushed nickel'],.007,.11)
    b.wallbox('Pass6 interior back '+str(number),wall,at-width/2,at+width/2,0,height,b.M['dark plum'],-.68,.06)
    # A shallow warm vestibule behind the actual wall opening, never over the floor.
    for t in [at-width*.39,at+width*.39]:
        b.wallbox('Pass6 interior wall return',wall,t-.025,t+.025,0,height,b.M['dark plum'],-.12,.58)
        b.wall_line('Pass6 interior aisle light',wall,[(t,8),(t,70)],b.M['warm light'],.008,-.63)
    if wall=='u':b.box('Pass6 vestibule floor',-.7,at-width/2,.005,at+width/2,-.1,.05,b.M['black enamel'],0)
    else:b.box('Pass6 vestibule floor',at-width/2,-.7,at+width/2,.005,-.1,.05,b.M['black enamel'],0)

def door(wall,at,number):
    before=set(bpy.data.objects);ORIGINAL_DOOR(wall,at,number);created=set(bpy.data.objects)-before
    bpy.context.view_layer.update()
    leaf_prefix=('Upholstered cinema door','Door diamond stitching','Porthole chrome','Porthole amber','Polished door pull','Door brass kickplate')
    for ob in list(created):
        if ob.name.startswith(('Blank marquee','Marquee ','Poster ','Blank poster','Door brushed frame','Door dark reveal')):remove(ob)
        elif ob.name.startswith(leaf_prefix):
            coords=[ob.matrix_world@Vector(c) for c in ob.bound_box]
            t=sum((-p.y if wall=='u' else p.x) for p in coords)/len(coords);tag(ob,number,-1 if t<at else 1)
    frame(wall,at,1.1,114,number)
    t,bottom,along,z=STACKS[number-1];base_y=350+30*t;anchor=b.wp(wall,t,base_y-bottom)
    height=HEIGHTS[number-1];center=anchor+UP*(height/2/PPU)+NORMAL*1.9
    b.panel('Blank marquee interior '+str(number),center,176,height,b.M['display recess'],.10,.045)
    b.screen_frame('Marquee silver rim '+str(number),center+NORMAL*.06,176,height,b.M['brushed nickel'],thick=3)
    b.screen_frame('Marquee pink tube '+str(number),center+NORMAL*.09,180,height+4,b.M['pink neon'],thick=1.5)
    b.line('Marquee bracket',[b.wp(wall,at,116),anchor+UP*.15-NORMAL*.15],b.M['black enamel'],.025)
    a,c=along;z0,z1=z
    b.wallbox('Poster outer metal frame '+str(number),wall,a-.035,c+.035,z0-3,z1+3,b.M['brushed nickel'],.001,.045)
    b.wallbox('Blank poster aperture '+str(number),wall,a,c,z0,z1,b.M['dark plum'],.002,.001,0)
    for edge in [a-.020,c+.020]:b.wall_line('Poster perimeter glow '+str(number),wall,[(edge,z0-1),(edge,z1+1)],b.M['white light'],.004,.012)
    b.wall_line('Poster top light '+str(number),wall,[(a,z1+2),(c,z1+2)],b.M['warm light'],.007,.025)

def wear():
    rng=random.Random(7601)
    chip=b.material('Pass6 exposed stone chips',(.24,.205,.17),.96,texture=65)
    scratch=b.material('Pass6 rubbed metal',(.23,.19,.125),.68,.5,texture=90)
    dirt=b.material('Pass6 settled grime',(.019,.012,.018),1,texture=28)
    # Extra wear only on furniture materials: the pass-4 carpet is untouched.
    for prefix in ['Ticket desk teal cabinet','Snack cabinet rear','Ticket desk worn stone top','Snack granite top','Door brass kickplate','Restroom teal door']:
        mats={}
        for ob in list(bpy.data.objects):
            if not ob.name.startswith(prefix):continue
            old=ob.data.materials[0]
            if old.name not in mats:
                mat=old.copy();mat.name='Pass6 wear '+prefix
                layout.weather_material(mat,.66,(3,3,.45));mats[old.name]=mat
            ob.data.materials[0]=mats[old.name]
    for ob in bpy.data.objects:
        if ob.name.startswith(('Ticket desk cyan edging','Snack counter pink edging','Lobby neon strip')):
            mat=ob.data.materials[0].copy();mat.name='Pass6 subdued furniture trim';ob.data.materials[0]=mat
            mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value*=.30
    for name in ['glass','smoked glass']:
        for node in b.M[name].node_tree.nodes:
            if node.bl_idname=='ShaderNodeMapRange':node.inputs['To Min'].default_value=.10;node.inputs['To Max'].default_value=.35
    # Scars sit within original opaque silhouettes, retaining every crop and footprint.
    for group,wall,a,c,front in [('boxoffice','u',5.05,8.34,4.401),('snack','v',5.65,11.55,4.601)]:
        b.layer(group)
        for i in range(50):
            t=rng.uniform(a,c-.045);z=rng.uniform(39.8,43.8) if i<32 else rng.uniform(5,10)
            b.wall_line('Pass6 chipped counter edge',wall,[(t,z),(t+rng.uniform(.012,.042),z+rng.uniform(-.4,.4))],chip,.0035,front)
        for i in range(24):
            t=rng.uniform(a,c-.09);p=(4.35,t) if wall=='u' else (t,4.53)
            b.line('Pass6 countertop scratches',[xyz(*p,44.025),xyz(p[0]+.015,p[1]+.06,44.025)],scratch,.002)
    b.layer('background')
    for number,(wall,at) in enumerate(DOORS+[('u',8.3)],1):
        number=number if number<6 else 'wc';width=.8 if number=='wc' else 1.1
        for i in range(26):
            t=at+rng.uniform(-width*.39,width*.39);z=rng.uniform(3,13)
            ob=b.wall_line('Pass6 kickplate scuff',wall,[(t,z),(t+.018,z+.25)],scratch,.0028,.057)
            tag(ob,number,-1 if number=='wc' or t<at else 1)
        # Worn threshold is contained in the existing wall opening.
        b.wallbox('Pass6 worn threshold',wall,at-width*.44,at+width*.44,.25,1.0,scratch,.07,.13,.002)
    for wall,a,c,front in [('u',.1,3.2,.052),('v',.1,4.0,.052),('u',8.72,8.95,.052)]:
        for i in range(45):
            t=rng.uniform(a,c);h=rng.uniform(.5,7)
            b.wall_line('Pass6 corner grime',wall,[(t,.5),(t+.01,h)],dirt,.004,front)
    for i in range(18):
        u=rng.uniform(2.4,11.6);v=rng.uniform(9.3,10.4);r=rng.uniform(.018,.036)
        b.ball('Pass6 pavement cigarette burn',xyz(u,v,.16),1,dirt,(r,r*.7,.0008))
        if i%3==0:b.ball('Pass6 old pale gum',xyz(u+.06,v,.18),1,b.M['gum'],(.024,.018,.0014))

def coordinates():
    result={'marquees':[],'poster_frames':[],'changes':[]}
    for i,((wall,at),(t,bottom,along,z)) in enumerate(zip(DOORS,STACKS),1):
        p=[round(900+(-t if wall=='u' else t)*60,3),bottom]
        result['marquees'].append({'screen':i,'bottom_center':p,'inner_size':[176,HEIGHTS[i-1]]})
        result['poster_frames'].append({'screen':i,'wall':wall+'0','along':along,'z_px':z})
        old=project(0,at,124) if wall=='u' else project(at,0,124)
        oldalong=[at-1.55,at-.75] if wall=='u' else [at+.75,at+1.55]
        result['changes'].append({'screen':i,'marquee_bottom_center':{'old':old,'new':p},'marquee_inner_size':{'old':[176,92],'new':[176,HEIGHTS[i-1]]},
            'poster_along':{'old':oldalong,'new':along},'poster_z_px':{'old':[23,128],'new':z},'door_uv_unchanged':[0,at] if wall=='u' else [at,0]})
    return result

def build(samples):
    b.door=door;sc=prior.build(samples)
    for ob in list(bpy.data.objects):
        if ob.name.startswith('Sun faded poster edging'):remove(ob)
        elif ob.name.startswith('Restroom chrome frame'):remove(ob)
        elif ob.name.startswith(('Restroom teal door','Restroom inset panel','Restroom brass knob')):tag(ob,'wc',-1)
    b.layer('background');frame('u',8.3,.8,104,'wc');wear()
    return sc

def timed(path):
    started=time.perf_counter();render(path);TIMES.append({'file':str(path.relative_to(ROOT)),'seconds':round(time.perf_counter()-started,3)})
    (QA/'scene_render_times.json').write_text(json.dumps(TIMES,indent=2));print('PASS6_SCENE',TIMES[-1],flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--samples',type=int,default=96)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);QA.mkdir(exist_ok=True)
    sc=build(args.samples);(QA/'coordinates.json').write_text(json.dumps(coordinates(),indent=2))
    if args.preview:timed(QA/'scene_preview.png');return
    sc.cycles.adaptive_threshold=.01
    for items in ambient.VARIABLES.values():items.clear()
    ambient.animated_materials();ambient.lighting()
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass6.blend'))
    source=json.loads((SOURCE/'manifest.json').read_text())
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        sc.render.use_border=False;sc.render.use_crop_to_border=False
        b.set_visibility();timed(QA/('cycles_minimum_full'+suffix+'.png'))
        b.set_visibility('background');timed(QA/'loop_basis'/('minimum'+suffix+'.png'))
        for e in source['occluders']:
            b.set_visibility(e['name']);ambient.crop(sc,e);timed(QA/'minimum_sprites'/(e['file'][:-4]+suffix+'.png'))
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.use_border=False;sc.render.use_crop_to_border=False
    b.set_visibility('background')
    for group in ambient.GROUPS:ambient.lighting(group);timed(QA/'loop_basis'/(group+'.png'))
    ambient.lighting();b.set_visibility()
    (QA/'geometry_bounds.json').write_text(json.dumps(layout.geometry_bounds(),indent=2))

if __name__=='__main__':main()
