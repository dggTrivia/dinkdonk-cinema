"""Pass 3: original procedural 1990s traffic, exact Roxy camera, no downloads.

Only writes qa3/ and roxy_vehicles.blend. Packaging is separate and targets out3.
Vehicle local +X is forward; z values are page pixels, u/v values are tiles.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import argparse
import json
import math
import time
import bpy
from mathutils import Matrix, Vector
import build_scene as b
from common import ROOT, ZPP, xyz, project, setup, render

QA = ROOT/'qa3'
ORIGIN = (6, 11)
SPECS = {
    'bus': {'length':2.6, 'width':.78, 'height':64, 'paint':(.045,.29,.27)},
    'taxi': {'length':1.72, 'width':.70, 'height':36, 'paint':(.9,.51,.025)},
    'sedan_a': {'length':1.64, 'width':.68, 'height':32, 'paint':(.26,.025,.075)},
    'sedan_b': {'length':1.68, 'width':.69, 'height':30, 'paint':(.035,.14,.32)},
}
M = {}

def mat(name, color, rough=.4, metal=0, emit=0, texture=0):
    m = b.material(name,color,rough,metal,emit,texture)
    M[name] = m
    return m

def palette(kind):
    mat('paint',SPECS[kind]['paint'],.2,.48,texture=85)
    p=M['paint'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Coat Weight'].default_value=.85
    p.inputs['Coat Roughness'].default_value=.09
    # Fine raindrops interrupt the long reflected neon streaks.
    p.inputs['Specular IOR Level'].default_value=.55
    mat('cream',(.59,.57,.43),.3,.3,texture=65)
    mat('rubber',(.008,.011,.019),.64,texture=120)
    mat('black',(.009,.014,.022),.29,.35)
    mat('chrome',(.4,.48,.53),.17,.85)
    mat('grille',(.02,.025,.033),.4,.68)
    mat('seat',(.09,.12,.12),.65,texture=70)
    mat('floor',(.12,.10,.07),.7,texture=50)
    mat('headlamp',(1,.83,.49),.18,.05,emit=5)
    mat('tail',(1,.007,.015),.22,.1,emit=3)
    mat('amber',(1,.20,.012),.25,.08,emit=1.7)
    mat('interior',(1,.65,.3),.5,emit=1.5)
    mat('sign',(1,.68,.21),.5,emit=1.8)
    mat('ink',(.004,.008,.011),.9)
    mat('plate',(.45,.49,.41),.4,.25)
    M['glass']=b.glass('Rain streaked smoked glazing',(.10,.24,.28),.36)
    p=M['glass'].node_tree.nodes.get('Principled BSDF')
    p.inputs['Coat Weight'].default_value=1
    p.inputs['Coat Roughness'].default_value=.06
    n=M['glass'].node_tree.nodes
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=95
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08
    bump.inputs['Distance'].default_value=.003
    M['glass'].node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
    M['glass'].node_tree.links.new(bump.outputs[0],p.inputs['Normal'])

def box(name, u0,v0,u1,v1,z0,z1, material, bevel=.012):
    return b.box(name,u0,v0,u1,v1,z0,z1,M.get(material,material),bevel)

def poly(name, points, material, bevel=0):
    ob=b.mesh(name,[xyz(*p) for p in points],[tuple(range(len(points)))],M[material])
    if bevel:
        mod=ob.modifiers.new('Window surround depth','SOLIDIFY');mod.thickness=bevel
    return ob

def line(name, points, material='black', r=.008):
    return b.line(name,[xyz(*p) for p in points],M[material],r)

def label(name, value, pos, size, face, material='sign'):
    right={'front':(0,1,0),'rear':(0,-1,0),'right':(1,0,0),'left':(-1,0,0)}[face]
    up=Vector((0,0,1));right=Vector(right)
    rot=Matrix((right,up,right.cross(up))).transposed().to_quaternion()
    return b.text(name,value,xyz(*pos),size,M[material],rot,.0005)

def wheels(length, width, bus=False):
    radius=.115 if bus else .091
    z=radius*ZPP
    axles=[-.83,.82] if bus else [-length*.32,length*.32]
    for x in axles:
        for side in [-1,1]:
            v=side*(width/2-.025)
            b.cylinder('Radial tire',xyz(x,v,z),radius,.10,M['rubber'],(0,1,0),32)
            v=side*(width/2+.027)
            b.cylinder('Recessed steel wheel',xyz(x,v,z),radius*.61,.012,M['chrome'],(0,1,0),24)
            b.cylinder('Dark wheel hub',xyz(x,v+side*.009,z),radius*.26,.015,M['black'],(0,1,0),16)
            for a in range(5):
                ang=a*math.tau/5
                b.ball('Lug nut',xyz(x+math.sin(ang)*radius*.36,v+side*.015,z+math.cos(ang)*radius*.36*ZPP),.008,M['chrome'])
    return axles,radius

def wheel_arch_panels(length,width,z0,z1,axles,radius,paint='paint'):
    """A concave lower-body face follows each wheel arch instead of hiding tires."""
    for side in [-1,1]:
        v=side*width/2
        pts=[(-length/2,v,z1),(length/2,v,z1),(length/2,v,z0)]
        for x in sorted(axles,reverse=True):
            rr=radius+.018
            pts.append((x+rr,v,z0))
            for j in range(13):
                a=j*math.pi/12
                pts.append((x+rr*math.cos(a),v,radius*ZPP+rr*ZPP*math.sin(a)))
            pts.append((x-rr,v,z0))
        pts.append((-length/2,v,z0))
        poly('Pressed steel wheel arch sill',pts,paint,.025)
        for x in axles:
            line('Rubber wheel arch moulding',[(x+(radius+.02)*math.cos(j*math.pi/16),v+side*.009,radius*ZPP+(radius+.02)*ZPP*math.sin(j*math.pi/16)) for j in range(17)],'black',.009)

def add_lamp(x,v,z,tail=False,bus=False):
    # Rectangular sealed-beam units, characteristic of the period.
    face=1 if not tail else -1
    box('Lamp rubber gasket',x-.012,v-.082,x+.012,v+.082,z-2.7,z+2.7,'black',.006)
    box('Tail lens' if tail else 'Sealed beam headlight',x+face*.013-.007,v-.066,x+face*.013+.007,v+.066,z-1.9,z+1.9,'tail' if tail else 'headlamp',.004)
    for vv in [-.035,0,.035]:
        line('Ribbed lamp lens',[(x+face*.023,v+vv,z-1.6),(x+face*.023,v+vv,z+1.6)],'tail' if tail else 'headlamp',.0015)
    if tail:
        ob=b.point('Red tail reflection',xyz(x-.03,v,z),3.0 if bus else 2.2,(1,.012,.018),.055)
    else:
        data=bpy.data.lights.new('Warm sealed beam cone','SPOT')
        data.energy=85 if bus else 65;data.color=(1,.76,.40)
        data.spot_size=math.radians(54);data.spot_blend=.65;data.shadow_soft_size=.032
        ob=bpy.data.objects.new('Headlight road beam',data);bpy.context.collection.objects.link(ob)
        ob.location=xyz(x+.025,v,z)
        ob.rotation_euler=(xyz(x+1.8,v*.88,0)-ob.location).to_track_quat('-Z','Y').to_euler()
    ob['vehicle_lamp']=True

def bus(door_open=False):
    L=2.6;w=.78
    axles,r=wheels(L,w,True)
    box('Bus chassis',-1.25,-.32,1.25,.32,11,23,'black')
    box('Teal lower body',-1.29,-w/2,1.29,w/2,19,33,'paint',.022)
    wheel_arch_panels(L,w,10,24,axles,r)
    box('Ivory belt line',-1.3,-w/2-.005,1.3,w/2+.005,29,33,'cream',.007)
    box('Passenger floor',-1.24,-.36,1.24,.36,29,30.5,'floor')
    box('Cream bus roof',-1.31,-.40,1.31,.40,59,64,'cream',.035)
    box('Front engine panel',1.23,-.39,1.3,.39,27,38,'paint')
    box('Rear engine panel',-1.30,-.39,-1.23,.39,28,42,'cream')
    box('Rear upper fascia',-1.3,-.39,-1.25,.39,54,60,'cream')
    # Slim window pillars with a real lit cabin behind the glass.
    for side in [-1,1]:
        for j in range(7):
            x=-1.25+j*.415
            box('Window vertical mullion',x-.016,side*.39-.015,x+.016,side*.39+.015,32,60,'cream',.004)
        for j in range(6):
            x=-1.21+j*.415
            # Front entrance is curbside (-v); door animation replaces this bay.
            if side==-1 and j==5: continue
            for za,zb in [(34,36),(56.5,58)]:
                box('Dark window sill',x-.01,side*.391-.009,x+.37,side*.391+.009,za,zb,'black',.004)
            box('Warm translucent passenger window',x+.014,side*.397-.007,x+.346,side*.397+.007,36,56.5,'glass',.002)
            line('Sliding window chrome divider',[(x+.016,side*.408,50),(x+.342,side*.408,50)],'chrome',.003)
        box('Long rain gutter',-1.30,side*.41-.009,1.30,side*.41+.009,59,60.5,'black',.003)
        for x in [-.96,-.54,-.12,.30]:
            box('Passenger seat cushion',x-.13,side*.22-.10,x+.12,side*.22+.10,34,37,'seat')
            box('Passenger seat back',x-.13,side*.22-.1,x-.085,side*.22+.10,36,46,'seat')
            line('Chrome seat rail',[(x-.1,side*.22-.105,39),(x-.1,side*.22-.105,47),(x-.1,side*.22+.105,47),(x-.1,side*.22+.105,39)],'chrome',.006)
        label('Side route number','95',(-.84,side*.411,25),.11,'right' if side==1 else 'left','cream')
        label('Municipal transit lettering','ROXY TRANSIT',(-.05,side*.409,25),.066,'right' if side==1 else 'left','cream')
        for x in [-1.16,1.16]:
            box('Orange side marker',x-.035,side*.405-.005,x+.035,side*.405+.005,31,33,'amber',.003)
    # Front and rear windows, actual destination lettering on both ends.
    for v in [-.365,.365]:
        box('Front windshield frame',1.26,v-.01,1.305,v+.01,38,55,'black')
    box('Front windshield',1.309,-.35,1.319,.35,39,54,'glass',.003)
    box('Windshield centre divider',1.32,-.011,1.329,.011,39,54,'black',.003)
    box('Destination sign housing',1.29,-.375,1.322,.375,55,62,'black',.005)
    label('Front destination 95 ROXY','95 ROXY',(1.328,0,58.4),.112,'front')
    box('Rear glazing',-1.316,-.33,-1.306,.33,43,54,'glass',.003)
    box('Rear route housing',-1.32,-.24,-1.308,.24,54.5,61,'black',.004)
    label('Rear destination 95 ROXY','95 ROXY',(-1.327,0,57.7),.083,'rear')
    for v in [-.18,.18]:
        line('Windshield wiper',[(1.334,v-.08,40),(1.337,v+.07,48)],'black',.007)
        add_lamp(1.315,v*1.5,28,False,True)
        add_lamp(-1.319,v*1.5,30,True,True)
    for x in [-1.32,1.32]:
        box('Heavy rubber bumper',x-.033,-.41,x+.033,.41,17,22,'black')
        box('Bumper chrome stripe',x-.037,-.36,x+.037,.36,20,21,'chrome',.004)
    for z in range(22,39,3):
        line('Rear engine louvre',[(-1.335,-.18,z),(-1.335,.18,z)],'grille',.009)
    box('Roof ventilation pod',-.65,-.23,.0,.23,64,67,'cream',.025)
    for x in [-.55,-.45,-.35,-.25,-.15]:
        box('Ventilation grille',x,-.17,x+.025,.17,67,67.4,'grille',.002)
    for side in [-1,1]:
        line('Bus mirror arm',[(1.13,side*.39,49),(1.40,side*.49,49)],'chrome',.012)
        box('Bus side mirror',1.34,side*.49-.045,1.44,side*.49+.045,46,54,'black',.008)
    # Two-leaf folding entry, opening inward along the curb side.
    box('Entrance dark recess',.87,-.394,1.22,-.370,29,58,'black',.005)
    for j in range(3):
        box('Entry step',.88,-.40+j*.055,1.20,-.34+j*.055,21+j*3,23+j*3,'chrome',.003)
    for j in range(2):
        x=.88+j*.165
        members=[]
        before=set(bpy.context.scene.objects)
        box('Folding door lower panel',x,-.413,x+.165,-.394,29,34,'cream',.006)
        for xx in [x,x+.155]:
            box('Folding door cream frame',xx,-.413,xx+.01,-.394,34,59,'cream',.003)
        box('Door glass inset',x+.018,-.419,x+.147,-.417,34,56,'glass',.003)
        line('Door rubber edge',[(x,-.425,29),(x,-.425,59)],'black',.006)
        if door_open:
            bpy.context.view_layer.update()
            hinge=xyz(x,-.398,0)
            rotation=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(74 if j==0 else -74),4,'Z')@Matrix.Translation(-hinge)
            for ob in set(bpy.context.scene.objects)-before: ob.matrix_world=rotation@ob.matrix_world
    for x in [-.7,.15,.8]:
        box('Warm ceiling strip',x-.22,-.08,x+.22,.08,59,59.3,'interior')
        ob=b.area('Passenger cabin lamp',xyz(x,0,57),3.8,(1,.65,.32),.55,xyz(x,0,30),.22);ob['vehicle_lamp']=True
    box('Driver dashboard',.93,-.04,1.22,.33,36,40,'black')
    b.cylinder('Steering wheel',xyz(.99,.15,42),.065,.015,M['black'],(1,0,1),20)

def sedan(kind,door_open=False):
    spec=SPECS[kind];L=spec['length'];w=spec['width'];taxi=kind=='taxi';popup=kind=='sedan_b'
    h=29 if popup else 31
    axles,r=wheels(L,w)
    box('Car chassis',-L/2+.05,-w/2+.03,L/2-.05,w/2-.03,7,14,'black')
    box('Square lower body',-L/2,-w/2,L/2,w/2,14,18,'paint',.025)
    wheel_arch_panels(L,w,7,16,axles,r)
    box('Long flat hood',.42,-w/2,L/2-.015,w/2,17,20,'paint',.019)
    box('Short trunk lid',-L/2+.01,-w/2,-.44,w/2,17,20,'paint',.019)
    box('Cabin floor',-.45,-.30,.47,.30,17,18,'black')
    # Sloped windscreen/rear glass, straight roof and upright 1990s pillars.
    poly('Front windshield',[(.48,-.30,20),(.48,.30,20),(.24,.25,h),(.24,-.25,h)],'glass',.006)
    poly('Rear windshield',[(-.46,.30,20),(-.46,-.30,20),(-.28,-.25,h),(-.28,.25,h)],'glass',.006)
    box('Pressed steel roof',-.29,-.263,.25,.263,h,h+1.8,'paint',.016)
    for side in [-1,1]:
        v=side*.306;vt=side*.255
        # Separate doors on both sides; rear curb door can swing open.
        for rear in [False,True]:
            before=set(bpy.context.scene.objects)
            xa,xb=(-.43,-.03) if rear else (-.025,.46)
            ta,tb=(-.275,-.035) if rear else (-.02,.235)
            box('Door panel',xa,v-side*.009,xb,v+side*.009,11,20,'paint',.009) if side==1 else box('Door panel',xa,v-.009,xb,v+.009,11,20,'paint',.009)
            poly('Door window',[(xa,v,20.4),(xb,v,20.4),(tb,vt,h-.4),(ta,vt,h-.4)],'glass',.004)
            line('Door chrome window frame',[(xa,v,20),(xb,v,20),(tb,vt,h),(ta,vt,h),(xa,v,20)],'chrome',.005)
            line('Door vertical pillar',[(xb,v,20),(tb,vt,h)],'black',.012)
            line('Door bottom seam',[(xa,v+side*.013,11),(xb,v+side*.013,11),(xb,v+side*.013,20)],'black',.003)
            line('Door handle',[(xa+.065,v+side*.023,18),(xa+.14,v+side*.023,18)],'chrome',.009)
            if taxi:
                for k in range(4):
                    x=xa+.025+k*.08
                    box('Taxi checker livery',x,v+side*.018-.002,x+.04,v+side*.018+.002,13 if k%2 else 15,15 if k%2 else 17,'black',.001)
            if door_open and rear and side==-1:
                bpy.context.view_layer.update()
                hinge=xyz(xb,v,0)
                rotation=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(-56),4,'Z')@Matrix.Translation(-hinge)
                for ob in set(bpy.context.scene.objects)-before: ob.matrix_world=rotation@ob.matrix_world
        line('Body side rubbing strip',[(-L/2+.03,side*(w/2+.013),12),(L/2-.03,side*(w/2+.013),12)],'black',.011)
        line('Side mirror arm',[(.36,side*.30,23),(.38,side*.39,23)],'black',.012)
        box('Side mirror',.32,side*.38-.04,.42,side*.38+.04,22,25,'paint',.013)
        for x in [-.22,.17]:
            box('Upholstered seat',x-.12,side*.14-.09,x+.10,side*.14+.09,19,22,'seat')
            box('Seat back',x-.13,side*.14-.085,x-.08,side*.14+.085,21,27,'seat')
            box('Headrest',x-.12,side*.14-.055,x-.07,side*.14+.055,26,28,'seat')
    line('Windscreen wiper',[(.48,-.23,20.4),(.39,-.02,24.2)],'black',.006)
    line('Second wiper',[(.48,.02,20.4),(.39,.22,24.2)],'black',.006)
    box('Dashboard',.32,-.26,.45,.26,21,23,'black')
    b.cylinder('Steering rim',xyz(.29,.16,25),.043,.008,M['black'],(1,0,1),16)
    for x in [-L/2,L/2]:
        box('Rubber bumper',x-.025,-w/2-.008,x+.025,w/2+.008,8,11,'black')
        box('Chrome bumper edge',x-.028,-w/2,x+.028,w/2,10,11.1,'chrome',.004)
    for v in [-w*.30,w*.30]:
        headx=L/2+.005
        z=15
        if popup:
            headx=L/2-.11;z=22.5
            verts=[xyz(x,v+vv,zz) for x,zz in [(headx-.17,19),(headx+.005,19),(headx+.005,25)] for vv in [-.082,.082]]
            ob=b.mesh('Raised wedge pop up headlamp pod',verts,[(0,2,4),(1,5,3),(0,1,3,2),(2,3,5,4),(4,5,1,0)],M['paint'])
            mod=ob.modifiers.new('Headlamp pod edge bevel','BEVEL');mod.width=.006;mod.segments=2
        add_lamp(headx,v,z)
        add_lamp(-L/2-.008,v,15,True)
        box('Front amber indicator',L/2+.024,v-.053,L/2+.034,v+.053,11.3,12.9,'amber',.003)
    box('Radiator grille',L/2+.016,-.11,L/2+.03,.11,12,18,'grille',.004)
    for z in [13,15,17]: line('Grille chrome bar',[(L/2+.035,-.10,z),(L/2+.035,.10,z)],'chrome',.003)
    box('Rear number plate',-L/2-.031,-.075,-L/2-.028,.075,11.5,14,'plate',.002)
    label('Rear plate','RXY 95',(-L/2-.033,0,12.7),.026,'rear','black')
    box('Interior dome light',-.07,-.04,.02,.04,h-.2,h,'interior',.003)
    ob=b.point('Car warm interior',xyz(-.02,0,h-1.6),.28,(1,.56,.25),.08);ob['vehicle_lamp']=True
    if taxi:
        # Draft 16: compact roof light, .12 x .32 tiles x 5 scene pixels.
        # The luminous box starts 1.4 pixels above the steel roof (h+1.8).
        box('Roof lamp black base',-.085,-.175,.065,.175,h+1.8,h+3.0,'black',.006)
        box('Illuminated TAXI roof box',-.07,-.16,.05,.16,h+3.2,h+8.2,'sign',.006)
        label('TAXI front roof lettering','TAXI',(.057,0,h+5.7),.075,'front','ink')
        label('TAXI rear roof lettering','TAXI',(-.077,0,h+5.7),.075,'rear','ink')
    else:
        line('Radio antenna',[(-.64,-.28,20),(-.70,-.28,31)],'chrome',.003)

def receiver():
    # A black, rough wet-road receiver. Only vehicle lamps illuminate this pass.
    m=mat('Wet asphalt light receiver',(.075,.085,.10),.20,.16,texture=115)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.55
    p.inputs['Coat Roughness'].default_value=.085
    tex=m.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=7
    mapping=m.node_tree.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY'
    mapping.inputs[1].default_value=(.5,14,1)
    coords=m.node_tree.nodes.new('ShaderNodeTexCoord')
    ramp=m.node_tree.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.025,.025,.025,1)
    ramp.color_ramp.elements[1].color=(.30,.30,.30,1)
    links=m.node_tree.links
    links.new(coords.outputs['Generated'],mapping.inputs[0]);links.new(mapping.outputs[0],tex.inputs[0])
    links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],p.inputs['Roughness'])
    return box('Receiver only for additive road pass',-5,-4,5,4,-.12,-.02,m,0)

def lighting():
    # Draft 15: vehicle studio only. Never change the shared lobby setup.
    bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.015
    return [
        b.area('Cool overcast fill',xyz(5,10,310),0,(.38,.51,1),5,xyz(6,11,20)),
        b.area('Current warm script reflection',xyz(3,8,150),8,(1,.27,.39),3.2,xyz(6,11,25),.55),
        b.area('Cinema cyan reflection',xyz(8,8,145),11.2,(.10,1,.92),3,xyz(6,11,25),.4),
        b.area('Warm street fill',xyz(9,13,150),6.8,(1,.73,.45),3,xyz(6,11,22)),
    ]

def make(kind,direction,door_open,samples,scale,preview=False):
    sc=setup(samples,scale,True)
    b.GROUPS.clear();b.META.clear();b.GROUP='vehicle'
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    palette(kind)
    before=set(sc.objects)
    bus(door_open) if kind=='bus' else sedan(kind,door_open)
    model=set(sc.objects)-before
    bpy.context.view_layer.update()
    corners=[ob.matrix_world@Vector(p) for ob in model if ob.type in ['MESH','CURVE','FONT'] for p in ob.bound_box]
    footprint=[min(p.x for p in corners),-max(p.y for p in corners),max(p.x for p in corners),-min(p.y for p in corners)]
    measured_height=max(p.z for p in corners)*ZPP
    rotate=Matrix.Translation(xyz(*ORIGIN))@Matrix.Rotation(math.pi if direction=='minus' else 0,4,'Z')
    for ob in model: ob.matrix_world=rotate@ob.matrix_world
    rig=lighting()
    # Common roomy working border, packaging computes the exact shared crop.
    x,y,w,h=300,630,610,400
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=(x+w+.1)/1920
    sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=(1080-y+.1)/1080
    name=kind+'_'+direction+('_open' if door_open else '')
    suffix='@2x' if scale==2 else ''
    raw_dir='raw_preview' if preview else 'raw'
    render(QA/raw_dir/(name+suffix+'.png'))
    # Light receiver uses the same camera, with only the moving vehicle's lamps.
    for ob in rig:ob.hide_render=True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    sc.render.film_transparent=False
    for ob in model:
        if ob.type!='LIGHT':ob.visible_camera=False
    floor=receiver();floor.location+=xyz(*ORIGIN)
    render(QA/raw_dir/(name+'_light'+suffix+'.png'))
    if kind=='bus' and direction=='plus' and not door_open and scale==2:
        floor.hide_render=True
        for ob in rig:ob.hide_render=False
        for ob in model:
            if ob.type!='LIGHT':ob.visible_camera=True
        sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.015
        sc.render.film_transparent=True
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_vehicles.blend'))
    return {'name':name,'kind':kind,'direction':'+u' if direction=='plus' else '-u',
            'door_open':door_open,'scale':scale,'raw_dir':raw_dir,'border':[x,y,w,h],
            'anchor_global':project(*ORIGIN),'length_tiles':SPECS[kind]['length'],
            'width_tiles':SPECS[kind]['width'],'height_px':round(measured_height,3),
            'geometry_local_footprint':[round(v,5) for v in footprint]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=96)
    ap.add_argument('--preview',action='store_true');ap.add_argument('--kind',choices=list(SPECS))
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    QA.mkdir(exist_ok=True);rows=[];t=time.time()
    for kind in ([args.kind] if args.kind else SPECS):
        for direction in ['plus','minus']:
            for opened in ([False] if args.preview or kind not in ['bus','taxi'] else [False,True]):
                for scale in ([1] if args.preview else [1,2]):
                    started=time.time()
                    row=make(kind,direction,opened,args.samples,scale,args.preview)
                    row['seconds']=round(time.time()-started,2);rows.append(row)
                    print('VEHICLE_DONE',json.dumps(row),flush=True)
    target=QA/('render_preview.json' if args.preview else 'render_vehicles.json')
    # A --kind rebuild updates only that model's entries.
    if args.kind and target.exists():
        rows=[r for r in json.loads(target.read_text())['renders'] if r['kind']!=args.kind]+rows
    target.write_text(json.dumps({'elapsed_seconds':round(time.time()-t,2),'renders':rows},indent=2))

if __name__=='__main__':main()
