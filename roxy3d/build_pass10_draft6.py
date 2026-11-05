"""Brief 17: still-only draft, built from the preserved Draft 5 scene."""
import sys,math,random,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
import build_scene as b
import build_pass10_draft as d
from common import xyz,ZPP,project
from build_pass10_draft4 import quality
from draft6_common import *
R=random.Random(171006);META={'brief':'BRIEF-17-draft6.md','draft_only':True,'removed':[],'art':[],'seats':[]};NEW=[]

def rm(o):META['removed'].append(o.name);d.rm(o)
def mat(n,c,rough=.5,metal=0,emit=0,texture=0):return b.material('D6 '+n,c,rough,metal,emit,texture)
def box(n,*a):return b.box('D6 '+n,*a)
def line(n,pts,ma,r=.006):return b.line('D6 '+n,[xyz(*p) for p in pts],ma,r)
def text(n,s,u,v,z,size,ma,axis='v'):
    return b.text('D6 '+n,s,xyz(u,v,z),size,ma,d.UFACE if axis=='u' else b.FRONT_FACE)
def wet(ma,coat=.35):
    p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.23
    return ma
def image_mat(key,emit=0):
    ma=wet(mat('printed '+key,(.5,.5,.5),.60),.22);n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    im=bpy.data.images.load(str(WORK/'art'/(key+'.png')),check_existing=True);im.pack();q=n.new('ShaderNodeTexImage');q.image=im;l.new(q.outputs['Color'],p.inputs['Base Color'])
    if emit:l.new(q.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emit
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=110
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.0009;bump.inputs['Strength'].default_value=.18;l.new(noise.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return ma
def quad(n,pts,ma):
    ob=b.mesh('D6 '+n,[xyz(*p) for p in pts],[(0,1,2,3)],ma);uv=ob.data.uv_layers.new()
    for k,co in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[k].uv=co
    return ob
def art(key,u0,u1,v,z0,z1,emit=0):
    ob=quad('art '+key,[(u0,v,z0),(u1,v,z0),(u1,v,z1),(u0,v,z1)],image_mat(key,emit));ob['wall_mounted']=True
    META['art'].append({'name':key,'object':ob.name,'bounds_uvz':[u0,u1,v,z0,z1]});return ob

def clean_inherited_water(sc):
    # Preserve batch objects and light-link identity; remove only droplets tied
    # to surfaces which this draft moves/rebuilds. The still uses saved phase 0.
    def affected(p):
        u,v,z=p.x,-p.y,p.z*ZPP
        return (-.15<u<2.9 and 9.12<v<10.17 and z>3) or (-2.62<u<-1.28 and 8.78<v<9.4 and z<70) or (-.95<u<.12 and 9.10<v<9.5 and z>130) or (3.7<u<5.6 and -.9<v<-.35 and z>310) or (13.5<u<14.4 and 7.5<v<8.4 and z>2)
    rows=[]
    for name in ['D5 physical surface beads','D5 periodic wet micro impacts']:
        o=sc.objects.get(name)
        if not o:continue
        verts=[v.co.copy() for v in o.data.vertices];faces=[tuple(p.vertices) for p in o.data.polygons if not affected(o.matrix_world@p.center)]
        old=len(o.data.polygons);o.data.clear_geometry();o.data.from_pydata(verts,[],faces);o.data.update();rows.append([name,old-len(faces)])
    for name in ['D5 metal and cap splash crowns','D5 hem edge drips and glass runnels']:
        o=sc.objects.get(name)
        if not o:continue
        count=0
        for sp in list(o.data.splines):
            pts=[Vector(p.co[:3]) for p in sp.points]
            if pts and affected(o.matrix_world@(sum(pts,Vector())/len(pts))):o.data.splines.remove(sp);count+=1
        rows.append([name,count])
    for o in list(sc.objects):
        if o.name.startswith(('D5 shelter wind-facing','D5 shelter glass gravity')):rm(o)
    META['retired_water_elements']=rows

# Monoline capitals, individually jittered and tilted; these are small marker
# strokes on the actual surfaces, with no rectangular decal backing.
GLYPHS={
'A':[[(0,0),(.48,1),(1,0)],[(.22,.40),(.78,.42)]],
'E':[[(1,1),(0,1),(.03,0),(1,.03)],[(.02,.51),(.80,.53)]],
'I':[[(.5,0),(.48,1)]],
'L':[[(.1,1),(.02,0),(.95,.03)]],
'N':[[(0,0),(.01,1),(.96,0),(1,1)]],
'O':[[(.16,0),(0,.24),(.04,.80),(.25,1),(.80,.96),(1,.70),(.96,.20),(.74,.02),(.16,0)]],
'P':[[(0,0),(.03,1),(.76,.96),(1,.77),(.87,.54),(.02,.50)]],
'S':[[(.92,.91),(.55,1),(.08,.84),(.03,.61),(.87,.37),(.97,.14),(.60,0),(0,.09)]],
'V':[[(0,1),(.48,0),(1,1)]],
'W':[[(0,1),(.22,0),(.53,.66),(.77,0),(1,1)]],
'Y':[[(0,1),(.48,.52),(1,1)],[(.48,.52),(.46,0)]],
'D':[[(0,0),(0,1),(.52,.98),(1,.76),(1,.27),(.57,.02),(0,0)]],
'R':[[(0,0),(0,1),(.76,.98),(1,.76),(.78,.53),(0,.51)],[(.48,.51),(1,0)]],
'F':[[(0,0),(0,1),(1,1)],[(.03,.51),(.83,.51)]],
'0':[[(.18,0),(0,.25),(0,.77),(.24,1),(.77,1),(1,.73),(1,.23),(.74,0),(.18,0)]],
'5':[[(1,1),(0,1),(0,.56),(.76,.56),(1,.30),(.85,.04),(.23,0),(0,.12)]]}
def scribble(label,body,u,v,z,width,height,ma,axis='u',radius=.0017):
    unit=width/max(1,len(body)*1.25-.25)
    for j,ch in enumerate(body):
        if ch==' ':continue
        wob=R.uniform(-.035,.035)
        for stroke in GLYPHS.get(ch,[]):
            pts=[]
            for x,y in stroke:
                xx=(j*1.25+x+.09*y+R.uniform(-.02,.02))*unit;zz=z+(y+wob)*height
                pts.append((u,v-xx,zz) if axis=='u' else (u+xx,v,zz))
            ob=line(label,pts,ma,radius);ob['surface_vandalism']=True
def dino(n,u,v,z,s,ma,axis='u'):
    shape=[(0,0),(.28,.17),(.26,.5),(.45,.57),(.47,.92),(.83,.94),(1,.76),(.74,.68),(.62,.69),(.62,.34),(.8,.19),(.64,.05),(.58,.20),(.38,.15),(.35,0)]
    pts=[(u,v-x*s,z+y*s*ZPP) if axis=='u' else (u+x*s,v,z+y*s*ZPP) for x,y in shape];line(n,pts,ma,.0015)
def restroom(sc):
    b.layer('draft6_restroom')
    for o in list(sc.objects):
        if o.name.startswith(('D5 art turf','D3 alley future paste-up panel')):rm(o)
    ink=mat('faded blue black marker',(.014,.022,.027),.92);red=mat('red marker overtag',(.18,.023,.025),.88);scratch=mat('cut laminate scratch',(.32,.40,.34),.76);etched=mat('mirror etched frosted grooves',(.42,.49,.45),.38)
    # Closed second stall: the argument, overwritten by a second hand.
    scribble('stall marker YEE NEVA LOSE','YEE NEVA LOSE',1.108,5.78,55,.72,4.9,ink)
    line('crossed out YEE one',[(1.111,5.79,55.4),(1.111,5.03,59.7)],red,.0021)
    line('crossed out YEE two',[(1.111,5.77,60.0),(1.111,5.04,54.9)],red,.0018)
    scribble('PEPE WINS overwrite','PEPE WINS',1.113,5.70,46,.58,6.3,red,radius=.0023)
    dino('tiny dino retaliation',1.114,5.22,64,.12,ink)
    # A less prominent scratched repeat on a different door and a divider.
    scribble('scratched YEE stall three','YEE',1.108,6.73,38,.19,4.5,scratch,radius=.0008)
    scribble('partition small marker','PEPE',.34,6.916,60,.24,5.5,ink,'v',.0015)
    dino('tile little dino',.0205,7.8,114,.14,ink)
    scribble('tile reply','NEVA LOSE',.0205,7.7,105,.48,4.2,ink,radius=.0013)
    scribble('mirror scratched YEE','YEE',1.978,3.1135,69,.18,3.9,etched,'v',.00065)
    for j in range(9):
        u=2.57+R.uniform(-.12,.12);z=R.uniform(67,85);line('mirror key scratch',[(u,3.114,z),(u+R.uniform(.025,.08),3.114,z+R.uniform(1,3))],etched,.0005)
    META['restroom']={'turf_removed_from_alley':True,'primary_tag_surface':'P10 stall 2 door','primary_tag_plane_u':1.108,'tags':['YEE NEVA LOSE crossed out','PEPE WINS','tiny dino re-tag','scratched YEE','tile marker','mirror etching'],'no_floating_backboards':True}
    status('35: YEE/PEPE moved into small irregular marker strokes and scratched marks on restroom door, partition, tiles and mirrors; alley turf poster and empty framed board removed')

def neon_state(sc,state):
    for o in sc.objects:
        if o.get('d6_tube_state'):
            on=o['d6_tube_state']==state
            o.data.materials[0]=bpy.data.materials[o['d6_on_material'] if on else 'D6 unlit neon glass']
            o['d6_is_lit']=on
    sc['d6_neon_state']=state

def neon(sc):
    b.layer('rooftop_neon')
    for o in list(sc.objects):
        if o.name.startswith('P10 rooftop_dinkdonk') and any(k in o.name for k in ['raised green arm','gripping hand','bell handle','bell body','bell clapper']):rm(o)
        elif o.name.startswith('P10 entrance_dinkdonk') or o.name=='P10 entrance DD caption':rm(o)
    off=wet(mat('unlit neon glass',(.025,.038,.032),.24,.12),.4)
    green=mat('state arm lit green',(.20,1,.40),.25,emit=12);gold=mat('state bell lit amber',(1,.60,.09),.25,emit=12);steel=bpy.data.materials['P10 aged graphite steel']
    u,v,z,w,h=3.8,-.58,325,1.62,94
    def tube(state,label,pts,ma,r=.011):
        world=[(u+x/36*w,v+.026,z+(30-y)/30*h) for x,y in pts]
        ob=line('roof neon '+state+' '+label,world,ma,r);ob.data.use_fill_caps=True;ob['d6_tube_state']=state;ob['d6_on_material']=ma.name;ob['d6_is_lit']=True
        for x,y,zz in world[::max(1,len(world)//3)]:line('roof '+state+' insulated standoff',[(x,v-.055,zz),(x,v+.010,zz)],steel,.004)
    A=[('arm down',[(24.6,24.5),(27,28.4),(30,28.9),(32.3,26.2)],green),('hand down',[(31.5,25),(33,24.4),(34,25.3),(33.4,27),(32.1,27.1)],green),('bell handle down',[(32.8,26),(32.3,29.2)],gold),('bell down',[(30.6,29.4),(31.4,28.8),(33,29),(33.7,29.8),(34,31.9),(34.7,32.3),(30,32.1),(30.7,31.4),(30.6,29.4)],gold),('clapper down',[(32.5,32.2),(32.5,33.2)],gold)]
    B=[('arm raised',[(24.6,24.5),(26,26),(28,24),(28,19),(26.8,17.4)],green),('hand up',[(25.8,18.2),(27,17),(28.2,17.3),(28.2,19),(26.8,19.6)],green),('bell handle up',[(27.7,18),(28.6,12.7)],gold),('bell up',[(26.2,10),(27.6,8.6),(29.6,8.8),(30.6,10.3),(30,12.8),(31,13.3),(26.5,13),(27,12.4),(26.2,10)],gold),('clapper up',[(28.5,13.1),(28.5,14)],gold),('ring left',[(24.2,7),(23.1,5)],gold),('ring right',[(32.1,8),(33.8,6.5)],gold)]
    for state,paths in [('A',A),('B',B)]:
        for label,pts,ma in paths:tube(state,label,pts,ma,.010 if 'bell' in label else .012)
    # Tubes remain present in both states; only circuit emission/material changes.
    neon_state(sc,'A');META['neon']={'states':{'A':'arm and bell down; up set dark glass','B':'arm and bell up, two ringing ticks; down set dark glass'},'default':'A','switch':'build_pass10_draft6.neon_state(scene, state)','animation_rendered':False,'physical_tube_sets':[len(A),len(B)]}
    b.layer('entrance_neon')
    back=bpy.data.objects.get('P10 small entrance neon backer')
    if back:rm(back)
    box('Anything else script blade',-.91,9.12,.02,9.28,142,234,steel,.026)
    pink=mat('Anything else warm script neon',(1,.27,.39),.23,emit=10)
    # Hand-designed connected script paths rather than filled text lettering.
    cursive={
    'A':[[(-.12,0),(.45,1.1),(.68,.08),(.95,.15)],[(.13,.45),(.67,.49)]],
    'n':[[(0,.07),(.12,.55),(.15,.12),(.37,.60),(.59,.56),(.61,.12),(.9,.14)]],
    'y':[[(0,.55),(.1,.1),(.35,.1),(.5,.55),(.4,-.32),(.15,-.42),(.08,-.24),(.82,.14)]],
    't':[[(0,.1),(.34,.95),(.16,.18),(.39,.03),(.78,.14)],[(.02,.57),(.65,.62)]],
    'h':[[(0,.08),(.36,1),(.20,1.12),(.06,.30),(.12,.11),(.39,.57),(.6,.54),(.62,.13),(.85,.14)]],
    'i':[[(0,.1),(.2,.54),(.12,.16),(.45,.13)],[(.22,.83),(.235,.85)]],
    'g':[[(.55,.49),(.36,.63),(.12,.51),(.03,.21),(.21,.09),(.51,.50),(.44,-.33),(.19,-.43),(.04,-.24),(.83,.14)]],
    'e':[[(0,.12),(.49,.45),(.30,.61),(.08,.46),(.05,.19),(.30,.05),(.72,.14)]],
    'l':[[(0,.13),(.35,.91),(.29,1.10),(.14,.93),(.08,.29),(.18,.08),(.62,.14)]],
    's':[[(0,.13),(.39,.60),(.48,.49),(.17,.31),(.50,.17),(.35,.03),(.1,.06),(.76,.14)]],
    '?':[[(.03,.81),(.26,1),(.59,.89),(.60,.68),(.31,.49),(.25,.27)],[(.24,.04),(.25,.06)]]}
    def script(word,start,z0,cell,height):
        for k,ch in enumerate(word):
            for path in cursive[ch]:
                pts=[xyz(start+(k+x)*cell,9.324,z0+y*height) for x,y in path]
                cu=bpy.data.curves.new('D6 script glass','CURVE');cu.dimensions='3D';cu.bevel_depth=.0045;cu.bevel_resolution=3;cu.resolution_u=14;cu.use_fill_caps=True
                sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
                for q,p in zip(sp.bezier_points,pts):q.co=p;q.handle_left_type='AUTO';q.handle_right_type='AUTO'
                ob=bpy.data.objects.new('D6 Anything else script tube',cu);sc.collection.objects.link(ob);b.register(ob,ob.name,pink)
    # Readable script letterforms, converted to actual hollow contour tubing.
    # The custom trial strokes were too ambiguous at the owner's draft scale.
    original_font=b.FONT;b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/segoesc.ttf')
    for word,z0,size in [('Anything',201,.21),('else?',174,.28)]:
        ob=text('Anything else script '+word,word,-.445,9.324,z0,size,pink)
        bpy.context.view_layer.update();factor=min(1,.79/max(ob.dimensions.x,1e-6));ob.scale*=factor
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='CURVE')
        ob=bpy.context.view_layer.objects.active;ob.data.dimensions='3D';ob.data.fill_mode='FULL';ob.data.extrude=0;ob.data.bevel_depth=.0022;ob.data.bevel_resolution=3;ob.data.resolution_u=16;ob.data.use_fill_caps=True
        # Conversion keeps glyph contours; all spline paths are real glass tubes.
    b.FONT=original_font
    line('script underline',[(-.69,9.324,158),(-.48,9.324,155),(-.16,9.324,157)],pink,.004)
    for u1,z1 in [(-.72,190),(-.19,195),(-.62,170),(-.18,174)]:line('script ceramic mount',[(u1,9.285,z1),(u1,9.315,z1)],off,.008)
    status('36 and 38: separate DOWN/UP arm-and-bell neon circuits built with visible dark off-glass; saved state A; entrance frog/DD replaced by small two-line Anything else? script tubes')

def walls_ads(sc):
    b.layer('draft6_ads')
    # Refit the existing pasted posters to the solid exterior restroom wall.
    placements=[('D5 art lookalike',.12,.51),('D5 art conductor 0',.57,.96),('D5 art conductor 1',1.02,1.41),('D5 art conductor 2',1.47,1.86)]
    for name,a,c in placements:
        o=sc.objects[name];bb=d.bounds(o)
        for q in o.data.vertices:
            q.co.x=a+(q.co.x-bb[0])/(bb[2]-bb[0])*(c-a);q.co.y=-9.054;q.co.z=(105+(q.co.z*ZPP-98)/50*43)/ZPP
        o['wall_mounted']=True;o['support']='P10 solid restroom street wall';o.data.update()
    frame=wet(mat('poster frame charcoal',(.045,.053,.055),.39,.5),.4)
    # Match the 1000x1400 poster aspect in world units, preserving the emote.
    poster_width=(153-104)/ZPP*(1000/1400);centre=2.435
    box('EatFresh wall frame',centre-poster_width/2-.035,9.051,centre+poster_width/2+.035,9.068,102,155,frame,.008)
    ob=art('eatfresh',centre-poster_width/2,centre+poster_width/2,9.071,104,153)
    META['eatfresh']={'source':'ref/eatfresh-emote/EatFresh.png','slogan':'EAT OUR FRESH NOTHING BURGERS','surface':'real restroom exterior wall above the Route 05 shelter','palette':'cream, muted coral and ink violet; no sandwich-chain branding'}
    for o in sc.objects:
        if o.name.startswith(('D3 paint tag','D3 faded paint mark')):
            # Legacy tags were detached from brick. Put the curves/text onto it.
            if o.type=='FONT':o.location.y=.226
            elif o.type=='CURVE':
                for sp in o.data.splines:
                    for p in sp.points:p.co.y=.226
            o['wall_mounted']=True
    status('37 and poster fix: EatFresh reference emote composed into original 90s parody poster on a real wall; LOOKALIKE/RE-ELECT pasted directly to masonry; alley ABSOLUTE CINEMA retained and stray tags grounded on brick')

def frontage(sc):
    b.layer('draft6_frontage');offset=xyz(0,.08,14)
    move=[]
    for o in sc.objects:
        if o.name.startswith(('D5 art cabge','D5 CABGE','D5 cabbage','D5 green cabbage','D5 RED cabbage')):
            o.location+=offset;move.append(o.name)
    # Crates stay on the pavement; only the fascia/awning shifts up with its bay.
    for name in move:
        if name.startswith(('D5 cabbage','D5 green cabbage','D5 RED cabbage')):sc.objects[name].location.z-=14/ZPP
    wood=wet(mat('CABGE bay green timber',(.056,.13,.082),.58,texture=65),.28);glass=wet(mat('CABGE dark shop glass',(.026,.071,.045),.24,.40),.55);ivory=mat('shop faded cream',(.71,.66,.48),.55)
    box('CABGE own storefront timber bay',-2.60,8.815,-1.33,8.885,0,82,wood,.012)
    box('CABGE own dark display window',-2.53,8.886,-1.80,8.897,8,55,glass,.007)
    box('CABGE recessed door',-1.74,8.886,-1.40,8.897,2,55,glass,.004)
    for u in [-2.57,-1.78,-1.37]:box('CABGE shop jamb',u,8.895,u+.026,8.912,0,57,wood,.005)
    box('CABGE exclusive sign fascia',-2.58,8.815,-1.35,8.902,57,81,wood,.009)
    for u in [-2.44,-1.49]:line('CABGE awning arm',[(u,8.90,52),(u,9.20,43)],wood,.012)
    line('CABGE door pull',[(-1.49,8.92,23),(-1.49,8.92,35)],ivory,.009)
    text('CABGE opening hours','OPEN 8 - LATE',-1.56,8.901,45,.026,ivory)
    # The takeaway is rebuilt in the separate blank bay to the right. Both
    # shops remain in the approved fixed camera, with a brick pier between.
    brown=wet(mat('NOODLES bay burgundy timber',(.16,.053,.035),.57,texture=50),.25)
    box('NOODLES independent storefront',-1.22,8.75,-.10,8.85,0,81,brown,.012)
    box('NOODLES separate window',-1.15,8.852,-.55,8.865,8,54,glass,.006)
    box('NOODLES separate doorway',-.49,8.852,-.17,8.866,2,54,glass,.004)
    box('NOODLES exclusive fascia',-1.21,8.85,-.11,8.875,57,80,brown,.008)
    text('NOODLES separate takeaway','NOODLES',-.66,8.882,68,.16,ivory)
    line('NOODLES door pull',[(-.24,8.88,24),(-.24,8.88,35)],ivory,.007)
    # One red cabbage survives the relocation, no duplication.
    assert len([o for o in sc.objects if o.name=='D5 RED cabbage'])==1
    META['frontage']={'cabge_bay_uv':[-2.60,8.815,-1.33,9.36],'cafe_bay_u':[-7.45,-5.20],'separate_noodles_bay_u':[-1.22,-.10],'red_cabbages':1,'moved_objects':len(move),'review_revision':'keep CABGE inside the fixed camera, separate it from NOODLES with two complete shop bays'}
    status('frontage fix: CABGE and NOODLES now have separate complete framed shop bays and fascias, divided by brick; CABGE remains inside the fixed camera with its own window, door, awning and one red cabbage')

def shelter(sc):
    b.layer('draft6_shelter')
    for o in list(sc.objects):
        if o.name.startswith(('Bus shelter','P9 bus route')):rm(o)
    steel=wet(mat('shelter weathered steel',(.075,.11,.12),.36,.7,texture=90),.5);rubber=mat('shelter rubber seals',(.012,.018,.019),.75)
    glass=b.glass('D6 scratched shelter perspex',(.24,.32,.33),.12);scratch=mat('perspex scratches',(.30,.34,.31),.49);cream=mat('route enamel cream',(.71,.71,.56),.44,emit=.5);blue=mat('route header blue',(.024,.062,.082),.50)
    lamp=mat('shelter fluorescent diffuser',(.66,.80,.71),.3,emit=3);water=bpy.data.materials['D5 dielectric water beads']
    # Real depth, two side panels and a glazed back, open on the street side.
    for u in [-.08,2.80]:
        for v in [9.18,10.10]:
            box('shelter steel corner post',u-.026,v-.026,u+.026,v+.026,0,98,steel,.006)
            box('shelter bolted foot',u-.07,v-.07,u+.07,v+.07,.2,2.2,steel,.007)
    for u in [.96,1.92]:box('shelter back mullion',u-.016,9.164,u+.016,9.197,4,94,steel,.003)
    box('shelter wet back glazing',-.045,9.166,2.765,9.176,8,93,glass,.003)
    for u in [-.076,2.796]:
        box('shelter side perspex',u-.004,9.21,u+.004,10.055,8,93,glass,.002)
        for z in [8,93]:line('shelter side rubber seal',[(u,9.21,z),(u,10.055,z)],rubber,.009)
    box('shelter deep steel roof',-.17,9.08,2.90,10.21,97,101,steel,.018)
    for v in [9.11,10.18]:line('shelter folded roof lip',[(-.15,v,102),(2.88,v,102)],steel,.012)
    box('shelter lit header housing',-.12,10.18,2.84,10.23,88,97,blue,.008)
    text('shelter route 05 header','05  /  d.gg transit',1.36,10.236,92.3,.16,cream)
    for u in [.25,1.55]:box('shelter underside lamp',u,9.42,u+.60,9.57,95.4,96.4,lamp,.006)
    # Existing travel lightbox relocated to the left rear; keep PICK ONE separate.
    for o in sc.objects:
        if o.name.startswith(('P9 ad blank shelter','P9 ad frame shelter','P9 ad glass shelter','P9 ad glass glint shelter','D5 art travel')):o.location+=xyz(-.47,-.215,0)
        elif o.name.startswith(('D5 red blue utility call box','D5 art buttons','D5 physical utility push button')):o.location+=xyz(-.77,-.305,8)
    box('timetable steel glazed case',1.08,9.184,1.60,9.235,42,87,steel,.008)
    art('timetable',1.105,1.575,9.239,44,85,emit=.10)
    # Two slatted seat places, independently documented for later riders.
    for v in [9.29,9.37,9.45,9.53]:box('shelter bench seat slat',1.72,v,2.57,v+.055,23,25.5,steel,.009)
    for z in [35,41,47]:box('shelter bench back slat',1.72,9.245,2.57,9.29,z,z+4,steel,.008)
    for u in [1.80,2.47]:
        for v in [9.30,9.50]:box('bench fixed leg',u-.019,v-.019,u+.019,v+.019,0,23,steel,.004)
    for u in [1.72,2.57]:line('bench curved arm',[(u,9.28,23),(u,9.28,35),(u,9.53,35),(u,9.55,25)],steel,.012)
    META['seats']=[{'id':'shelter_05_left','uvz':[1.94,9.43,25.5],'faces':'toward street (+v)'},{'id':'shelter_05_right','uvz':[2.35,9.43,25.5],'faces':'toward street (+v)'}]
    # Stop pole sits to the right of the door-to-sidewalk corridor.
    b.cylinder('D6 stop pole',xyz(3.04,10.21,57),.022,114/ZPP,steel,vertices=20)
    box('stop sign enamel plate',2.86,10.20,3.22,10.24,98,126,cream,.015)
    text('stop sign 05','05',3.04,10.246,114,.21,blue);text('stop sign bus','BUS',3.04,10.247,102,.061,blue)
    text('pole operator','d.gg',3.04,10.247,122,.057,blue)
    b.cylinder('D6 shelter litter bin',xyz(3.08,9.53,18),.145,35/ZPP,steel,vertices=24)
    b.cylinder('D6 bin dark opening',xyz(3.08,9.53,35.7),.123,.012,rubber,vertices=24)
    line('bin rim',[(3.08+.145*math.cos(t),9.53+.145*math.sin(t),36.3) for t in np.linspace(0,math.tau,33)],steel,.011)
    for k in range(11):
        v=R.uniform(9.30,9.98);z=R.uniform(24,71);line('shelter scratched glass',[(2.804,v,z),(2.804,v+.045,z+R.uniform(2,7))],scratch,.0009)
    scribble('shelter key etched YEE','YEE',2.806,9.89,57,.23,5,scratch,radius=.0008)
    sticker=mat('old paper stickers',(.53,.48,.31),.83);gum=mat('old chewing gum',(.17,.15,.12),.95)
    for u,v,z in [(-.05,10.13,57),(2.80,10.13,38),(2.80,10.13,67)]:box('peeling pole sticker',u-.020,v,u+.020,v+.002,z,z+6,sticker,.001)
    for u,v in [(2.63,9.88),(2.58,10.0),(1.74,9.76)]:b.ball('D6 stuck pavement gum',xyz(u,v,.15),.018,gum,(1,1,.1))
    for i in range(70):
        u=R.uniform(-.12,2.85);v=R.uniform(9.13,10.17)
        b.ball('D6 shelter roof water bead',xyz(u,v,101.2),R.uniform(.003,.012),water,(1.2,1,.5))
    for k in range(18):
        u=R.uniform(-.10,2.82);line('shelter roof edge drip',[(u,10.20,100),(u,10.20,98),(u+.003,10.20,96-R.random()*2)],water,.0020)
    for k in range(24):
        v=R.uniform(9.25,10.02);z=R.uniform(14,89)
        b.ball('D6 side glass bead',xyz(2.803,v,z),R.uniform(.003,.007),water,(.6,1,1.5))
        if k%3==0:line('shelter side runnel',[(2.804,v,z),(2.804,v+.008,z-3),(2.804,v+.003,z-7)],water,.0013)
    # Route 05 on all existing bus lettering and both licence plates.
    for o in sc.objects:
        if o.type!='FONT':continue
        if o.name.startswith('Side route number'):o.data.body='05'
        if o.name.startswith('Municipal transit lettering'):o.data.body='d.gg transit'
        if 'destination 95 ROXY' in o.name:
            o.data.body='05  DINK DONK';o.data.size=.082 if o.name.startswith('Front') else .055;o.name=o.name.replace('95 ROXY','05 DINK DONK')
    for u,axis in [( .857,'front'),(-1.860,'rear')]:
        ob=box('bus DGG 05 number plate',u-.003,11.15,u+.003,11.33,22.3,27.0,cream,.002)
        # These belong to the parked inspection bus, not the shelter. They
        # must leave with that bus when production switches to moving sprites.
        from parked_bus_fix import tag_parked_bus_plate
        tag_parked_bus_plate(ob)
        rot=d.UFACE if axis=='front' else d.UFACE.copy()
        label=b.text('D6 bus plate DGG 05','DGG 05',xyz(u+(.004 if axis=='front' else -.004),11.24,24.5),.034,blue,rot,.0002)
        tag_parked_bus_plate(label)
        if axis=='rear':label.rotation_quaternion=Vector((-1,0,0)).to_track_quat('Z','Y')
    META['shelter']={'footprint_uv':[-.17,9.08,2.90,10.23],'height_px':102,'route':'05','destination':'05  DINK DONK','operator':'d.gg transit','timetable':'Route 05 - every 5 min (sticker over old 15)','boarding_corridor_uv':[.25,9.68,1.10,10.90],'bus_door_uv':[.38,10.82,.72,10.87],'furniture':['steel frame','back and side perspex','lit roof header','two seat slatted bench','travel ad','PICK ONE call box','glazed route map/timetable','stop pole and 05 sign','litter bin','stickers etching gum'],'new_roof_beads':70,'new_drips':18,'new_glass_beads':24}
    status('40: deep steel/perspex shelter built with lit Route 05 header, bench and two seat coordinates, timetable, stop pole, bin and wear; travel/PICK ONE retained; destination and plates changed to 05 / DINK DONK / DGG 05')

HOLES=[(13.89,1.96,.24,.37),(14.40,4.85,.27,.43),(13.86,7.84,.28,.39),(14.45,8.52,.23,.29)]
def ground_z(u,v):
    z=.22+.20*math.sin(u*17+v*5)*math.cos(v*9)
    if u<13.55:return z
    z+=.70*math.sin(u*11+v*3)**2
    for x,y,rx,ry in HOLES:
        r=((u-x)/rx)**2+((v-y)/ry)**2
        z-=3.4*math.exp(-r*1.5)
    return z
def patch(n,u,v,rx,ry,ma,dz=.1,N=11):
    coords=[]
    for t in np.linspace(0,math.tau,N,endpoint=False):
        q=R.uniform(.80,1.12);x=u+rx*q*math.cos(t);y=v+ry*q*math.sin(t);coords.append((x,y,ground_z(x,y)+dz))
    verts=[xyz(u,v,ground_z(u,v)+dz)]+[xyz(*p) for p in coords];ob=b.mesh('D6 '+n,verts,[(0,(j+1)%N+1,j+1) for j in range(N)],ma);return ob
def alley(sc):
    b.layer('draft6_alley')
    for o in list(sc.objects):
        if o.name.startswith(('D3 tied trash sack','D3 trash tie','D3 alley asphalt repair','D3 pothole','D3 alley settled seam','D3 alley neon reflecting puddle')):rm(o)
    old=sc.objects['P8 right service alley']
    for v in old.data.vertices:
        if (old.matrix_world@v.co).z>-.7/ZPP:v.co.z=-4/ZPP-old.location.z
    # Independent opaque aggregate surface: the inherited layered material on
    # a reversed-winding box is unsuitable for this new upward-facing mesh.
    asphalt=mat('fractured wet alley asphalt',(.023,.029,.032),.75,texture=85)
    n=asphalt.node_tree.nodes;l=asphalt.node_tree.links;p=n.get('Principled BSDF');p.inputs['Alpha'].default_value=1
    bump=next(q for q in n if q.type=='BUMP');bump.inputs['Distance'].default_value=.0018;bump.inputs['Strength'].default_value=.26
    ripple=n.new('ShaderNodeGroup');ripple.node_tree=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];ripple.inputs['Strength'].default_value=.16;l.new(bump.outputs[0],ripple.inputs['Normal In']);l.new(ripple.outputs['Normal'],p.inputs['Normal']);l.new(ripple.outputs['Normal'],p.inputs['Coat Normal'])
    geo=n.new('ShaderNodeNewGeometry');film=n.new('ShaderNodeTexNoise');film.inputs['Scale'].default_value=2.4;l.new(geo.outputs['Position'],film.inputs['Vector']);amount=n.new('ShaderNodeMapRange');amount.inputs['To Min'].default_value=.06;amount.inputs['To Max'].default_value=.28;l.new(film.outputs['Fac'],amount.inputs['Value']);l.new(amount.outputs[0],p.inputs['Coat Weight']);p.inputs['Coat Roughness'].default_value=.28
    tar=wet(mat('dark patched tar',(.014,.019,.023),.56,texture=78),.23);concrete=wet(mat('broken concrete aggregate',(.11,.115,.105),.72,texture=95),.25);chip=wet(mat('crumbling stone edge',(.085,.092,.088),.74,texture=65),.24);black=mat('deep pavement cracks',(.006,.009,.008),.83)
    water=bpy.data.materials['D5 dielectric water beads'].copy();water.name='D6 shallow pothole water';wn=water.node_tree.nodes;wl=water.node_tree.links;wp=wn.get('Principled BSDF');wp.inputs['Roughness'].default_value=.20
    wr=wn.new('ShaderNodeGroup');wr.node_tree=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];wr.inputs['Strength'].default_value=.42;wl.new(wr.outputs['Normal'],wp.inputs['Normal']);wl.new(wr.outputs['Normal'],wp.inputs['Coat Normal'])
    nu,nv=34,144;verts=[];faces=[]
    for j in range(nv+1):
        for i in range(nu+1):
            u=13.065+i*(14.99-13.065)/nu;v=.02+j*9.10/nv
            if i not in [0,nu] and j not in [0,nv]:u+=R.uniform(-.014,.014);v+=R.uniform(-.014,.014)
            verts.append(xyz(u,v,ground_z(u,v)))
    for j in range(nv):
        for i in range(nu):a=j*(nu+1)+i;faces.extend([(a,a+nu+2,a+1),(a,a+nu+1,a+nu+2)])
    ob=b.mesh('D6 broken heaved alley ground',verts,faces,asphalt);ob['real_displacement']=True
    for i,(u,v,rx,ry) in enumerate(HOLES):
        # Water is level inside a depressed, jagged surface, not a dark circle.
        pts=[xyz(u+rx*.68*math.cos(t),v+ry*.68*math.sin(t),-1.30) for t in np.linspace(0,math.tau,25,endpoint=False)]
        b.mesh('D6 water filled pothole',pts,[tuple(reversed(range(25)))],water)
        for k in range(14):
            t=k*math.tau/14;x=u+rx*math.cos(t);y=v+ry*math.sin(t);q=b.ball('D6 pothole broken aggregate',xyz(x,y,ground_z(x,y)+.25),R.uniform(.009,.025),chip,(1,1,.32));q.rotation_euler.z=R.random()*6
    for u,v,rx,ry in [(13.72,.62,.20,.28),(14.20,2.9,.40,.44),(13.84,4.1,.18,.59),(14.57,5.42,.19,.31),(13.87,8.82,.30,.22),(14.48,.39,.30,.25)]:
        patch('uneven cold asphalt repair',u,v,rx,ry,tar,.18)
    for u,v in [(14.47,2.1),(14.6,7.85),(13.73,5.23)]:
        patch('heaved concrete fragment',u,v,.25,.38,concrete,.85)
    for i in range(38):
        u=R.uniform(13.60,14.85);v=R.uniform(.15,8.6);pts=[]
        for j in range(5):x=u+R.uniform(-.04,.04);y=min(9.05,v+j*.07);pts.append((x,y,ground_z(x,y)+.04))
        line('broken asphalt fissure',pts,black,R.uniform(.003,.009))
        if i%4==0:
            p=pts[2];line('forked crack',[p,(p[0]+.11,p[1]+.06,ground_z(p[0]+.11,p[1]+.06)+.06)],black,.004)
    oil=wet(mat('old oily grime',(.018,.019,.014),.42,texture=40),.28)
    for u,v in [(13.79,3.10),(14.30,5.2),(13.81,6.9),(14.65,.4)]:patch('irregular oil stain',u,v,.26,.42,oil,.07)
    moss=mat('damp weeds',(.055,.11,.037),.75);dirt=mat('wall foot accumulated grime',(.033,.038,.025),.90,texture=40)
    for side in [13.09,14.92]:
        for j in range(23):patch('crumbled dirty wall edge',side,j*.39+.1,R.uniform(.025,.07),R.uniform(.12,.22),dirt,.25)
    for k in range(29):
        u=13.10+R.uniform(-.018,.035) if k%2 else 14.89+R.uniform(-.02,.02);v=R.uniform(.15,8.9);z=ground_z(u,v)
        for j in range(4):line('weed in crack',[(u,v,z),(u+R.uniform(-.03,.03),v+R.uniform(-.025,.025),z+R.uniform(2,5))],moss,.0018)
    paper=wet(mat('soaked paper grey',(.39,.37,.29),.85,texture=70),.12);card=wet(mat('soggy cardboard',(.17,.115,.055),.89,texture=50),.14)
    newspaper=image_mat('newspaper');flyer=image_mat('flyer');count=0
    def sheet(name,u,v,w,h,ma,angle):
        co=[]
        for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]:
            xx=u+x*math.cos(angle)-y*math.sin(angle);yy=v+x*math.sin(angle)+y*math.cos(angle);co.append((xx,yy,ground_z(xx,yy)+.22+R.uniform(0,.08)))
        ob=quad(name,co,ma);ob.data.flip_normals();return ob
    litter=[(13.77,2.7,.35,.48),(14.20,7.70,.40,.32),(14.27,.73,.34,.40)]
    for u,v,w,h in litter:
        sheet('flattened soggy cardboard',u,v,w,h,card,R.random()*2);line('cardboard fold',[(u-w*.3,v,ground_z(u-w*.3,v)+.37),(u+w*.3,v,ground_z(u+w*.3,v)+.37)],dirt,.002)
    sheet('wet newspaper spread',13.91,4.07,.46,.34,newspaper,-.3)
    for i in range(12):
        u=R.uniform(13.64,14.60);v=R.uniform(.3,8.85);sheet('scattered wet flyer' if i%3==0 else 'stuck wet paper',u,v,R.uniform(.10,.20),R.uniform(.13,.26),flyer if i%3==0 else paper,R.uniform(-2,2))
    can=wet(mat('crushed drink can silver',(.24,.28,.29),.33,.8),.3);cup=wet(mat('soaked cup red band',(.19,.047,.029),.75),.2)
    for i,(u,v) in enumerate([(14.33,8.0),(13.65,1.0),(14.05,5.5),(14.65,2.5),(13.78,8.6),(14.35,4.1)]):
        z=ground_z(u,v)+1.2
        ob=b.ball('D6 crushed can' if i%2==0 else 'D6 collapsed paper cup',xyz(u,v,z),.055,can if i%2==0 else paper,(1.30,.72,.30));ob.rotation_euler.z=i*.7
        if i%2:line('crushed cup rim',[(u-.055,v-.025,z),(u+.05,v-.025,z),(u+.055,v+.02,z),(u-.05,v+.02,z),(u-.055,v-.025,z)],cup,.0025)
    # Low open takeaway carton: four deformed sides, no bag substitute.
    u,v=14.18,8.47;z=ground_z(u,v)+.3
    box('flattened takeaway box bottom',u-.075,v-.06,u+.075,v+.06,z,z+.8,paper,.002)
    for p in [[(u-.075,v-.06,z),(u+.075,v-.06,z),(u+.09,v-.085,z+4),(u-.09,v-.085,z+3)],[(u-.075,v+.06,z),(u+.075,v+.06,z),(u+.095,v+.09,z+2),(u-.10,v+.1,z+3)]]:quad('takeaway carton soggy flap',p,paper)
    filt=mat('cigarette filters',(.29,.16,.055),.87)
    for i in range(23):
        u=R.uniform(13.62,14.80);v=R.uniform(.20,8.9);z=ground_z(u,v)+.28;a=R.uniform(0,math.tau);line('cigarette butt',[(u,v,z),(u+.025*math.cos(a),v+.025*math.sin(a),z)],filt,.0035)
    META['alley']={'displaced_vertices':len(verts),'water_potholes':len(HOLES),'repair_patches':6,'heaved_concrete_fragments':3,'fissures':38,'weed_clumps':29,'flat_cardboard':3,'newspaper':1,'papers_flyers':12,'cups_cans':6,'cigarette_butts':23,'takeaway_box':1,'clear_walkway_uv':[13.12,.35,13.55,8.8],'trash_bags_removed':True}
    status('39: alley rebuilt as displaced broken asphalt with water-filled potholes, heaved concrete, irregular repairs, cracks, oil and wall grime, weeds and wet ground litter; trash bags removed; central walking strip retained')

def final_checks(sc,initial):
    b.layer('draft6_finish')
    group=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];group.nodes['Ray traced ripple normal'].inputs['Distance'].default_value=.0045
    group.nodes['Time seconds'].outputs[0].default_value=0
    META['ripples']={'algorithm':'approved D4 periodic ray-traced normal group retained','distance_before':.012,'distance_after':.0045,'reason':'soften hard ring contrast in stills; no new ripple experiment'}
    for o in sc.objects:
        if o.name.startswith('D6 ') and o.type in ['MESH','CURVE','FONT'] and o.get('layer')!='draft6_restroom':
            receivers=['P8 surroundings light receivers','P8B alley light receiver'] if o.get('layer')=='draft6_alley' else ['P8 surroundings light receivers','P9 west fill receivers','P10 multiplex roof light receivers']
            for cname in receivers:
                col=bpy.data.collections.get(cname)
                if col and o.name not in col.objects:col.objects.link(o)
    bpy.context.view_layer.update()
    # Evaluate solid furniture against the full door-to-sidewalk reserve.
    corridor=META['shelter']['boarding_corridor_uv'];hits=[]
    for o in sc.objects:
        if not o.name.startswith('D6 '):continue
        if not any(k in o.name for k in ['corner post','bolted foot','bench','call box','litter bin','stop pole']):continue
        a,v,c,w,z,h=d.bounds(o)
        if h>3 and z<75 and a<corridor[2] and c>corridor[0] and v<corridor[3] and w>corridor[1]:hits.append(o.name)
    stale=[{'object':o.name,'body':o.data.body} for o in sc.objects if o.type=='FONT' and ('95' in o.data.body or 'ROXY' in o.data.body.upper()) and (o.get('draft5_bus') or any(k in o.name.lower() for k in ['route','transit','destination','bus','plate']))]
    META['checks']={'boarding_path_solid_hits':hits,'stale_transit_labels':stale,'main_camera_unchanged':list(v for row in sc.camera.matrix_world for v in row)==initial['camera_matrix'],'red_cabbage_count':sum(o.name=='D5 RED cabbage' for o in sc.objects),'no_entrance_emote_objects':not any(o.name.startswith('P10 entrance_dinkdonk') for o in sc.objects),'no_alley_turf_board':not any(o.name.startswith(('D5 art turf','D3 alley future paste')) for o in sc.objects)}
    assert not hits,hits
    assert not stale,stale
    assert META['checks']['main_camera_unchanged']
    quality(sc);sc.cycles.use_denoising=True;sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.use_compositing=False
    sc['draft6_only']=True;sc['draft6_no_clips']=True;sc['d6_neon_state']='A';sc['draft6_seats_json']=json.dumps(META['seats']);sc['draft6_boarding_corridor']=corridor
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
    META['source_sha256']=hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest();META['object_count']=len(sc.objects);report('scene.json',META)
    status('model saved from Draft 5 at final 720p/256-sample settings; approved ripples softened; boarding reserve has zero solid hits and all transit labels use leading-zero 05')

def main():
    bpy.ops.wm.open_mainfile(filepath=str(QA/'source_before_draft6.blend'));sc=bpy.context.scene;b.GROUPS.clear();b.M.clear();b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
    initial=json.loads((WORK/'source.json').read_text(encoding='utf-8'));clean_inherited_water(sc);restroom(sc);neon(sc);walls_ads(sc);frontage(sc);shelter(sc);alley(sc);final_checks(sc,initial)
if __name__=='__main__':main()
