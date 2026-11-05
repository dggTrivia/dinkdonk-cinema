"""Layout 2: wall counters, aged materials, fixed calibrated camera.

Reuses pass-1 geometry helpers, never its output runner. All products go to
out2/ and qa2/. Units are floor tiles and projected vertical pixels.
"""
import sys, math, json, time, argparse, shutil, random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix, Vector
import build_scene as b
from common import ROOT, ZPP, xyz, project, render

OUT=ROOT/'out2'; QA=ROOT/'qa2'
UFACE=Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
ORIGINAL={n:getattr(b,n) for n in ['palette','ground','walls','low_wall','furniture','exterior_props']}
TIMES=[]

def weather_material(mat, strength=.45, stretch=(1,1,1), traffic=False):
    """World-space low frequency wear over the original fine surface texture."""
    n=mat.node_tree.nodes; links=mat.node_tree.links; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeNewGeometry'); vec=n.new('ShaderNodeVectorMath');vec.operation='MULTIPLY'
    vec.inputs[1].default_value=stretch;links.new(tex.outputs['Position'],vec.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.7
    noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.8
    links.new(vec.outputs['Vector'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22
    ramp.color_ramp.elements[0].color=(1-strength,)*3+(1,)
    ramp.color_ramp.elements[1].position=.76;ramp.color_ramp.elements[1].color=(1.12,1.04,.95,1)
    links.new(noise.outputs['Fac'],ramp.inputs[0])
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    previous=p.inputs['Base Color'].links
    if previous: links.new(previous[0].from_socket,mix.inputs[1])
    else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
    links.new(ramp.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
    if traffic:
        sep=n.new('ShaderNodeSeparateXYZ');links.new(tex.outputs['Position'],sep.inputs[0])
        # Broad polished routes: entrance to the gate and cross-lobby service route.
        dist=n.new('ShaderNodeMath');dist.operation='SUBTRACT';dist.inputs[1].default_value=8.4
        links.new(sep.outputs['X'],dist.inputs[0])
        ab=n.new('ShaderNodeMath');ab.operation='ABSOLUTE';links.new(dist.outputs[0],ab.inputs[0])
        mask=n.new('ShaderNodeMapRange');links.new(ab.outputs[0],mask.inputs['Value'])
        mask.inputs['From Min'].default_value=.25;mask.inputs['From Max'].default_value=1.6
        mask.inputs['To Min'].default_value=.50;mask.inputs['To Max'].default_value=0
        wear=n.new('ShaderNodeMixRGB');links.new(mask.outputs['Result'],wear.inputs[0])
        links.new(mix.outputs[0],wear.inputs[1]);wear.inputs[2].default_value=(.105,.079,.107,1)
        links.new(wear.outputs[0],p.inputs['Base Color'])
    p.inputs['Roughness'].default_value=max(.42,p.inputs['Roughness'].default_value)

def palette():
    ORIGINAL['palette']()
    for name in ['wall plum','dark plum','concrete','asphalt','counter stone','velvet teal','velvet burgundy','black enamel','red enamel']:
        weather_material(b.M[name],.65 if name in ['wall plum','asphalt','concrete'] else .38,
                         (3,3,.28) if name=='wall plum' else (1,1,1))
    for name in ['carpet aubergine','carpet midnight','carpet inset']:
        weather_material(b.M[name],.58,traffic=name=='carpet aubergine')
    # Tone down the original bright confetti and make paint/metal less pristine.
    for name in ['confetti pink','confetti cyan','confetti gold','confetti lilac']:
        p=b.M[name].node_tree.nodes.get('Principled BSDF')
        c=p.inputs['Base Color'].default_value;p.inputs['Base Color'].default_value=(*(x*.65 for x in c[:3]),1)
    b.material('old plaster',(.16,.115,.12),.88,texture=34)
    weather_material(b.M['old plaster'],.64,(2,2,.18))
    b.material('scuffed paint',(.21,.16,.13),.95,texture=90)
    b.material('water streak',(.045,.027,.041),.92)
    b.material('gum',(.34,.31,.26),.97,texture=25)
    b.material('tar crack',(.008,.008,.012),.96)
    b.material('palm leaf',(.045,.125,.065),.72,texture=18)
    b.material('palm leaf light',(.095,.19,.055),.8,texture=24)
    b.material('terracotta',(.24,.075,.039),.85,texture=26)
    b.material('pot soil',(.019,.014,.012),1,texture=90)
    b.material('faded paper',(.33,.25,.14),.95,texture=80)
    # Dirt in glass varies continuously instead of making panes opaque.
    for name in ['glass','smoked glass']:
        mat=b.M[name];n=mat.node_tree.nodes;mix=next(x for x in n if x.bl_idname=='ShaderNodeMixShader')
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=24;tex.inputs['Detail'].default_value=3
        ramp=n.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=.06;ramp.inputs['To Max'].default_value=.28
        mat.node_tree.links.new(tex.outputs['Fac'],ramp.inputs['Value']);mat.node_tree.links.new(ramp.outputs[0],mix.inputs[0])

def ground():
    ORIGINAL['ground']();b.layer('background')
    # Faded angular weave motifs; sparse enough for 50px walkers to read.
    for u in [4.8,6.3,7.8,9.3,10.8,12.3]:
        for v in [5.3,6.6,7.9]:
            b.line('Worn carpet diamond',[xyz(u-.22,v,.09),xyz(u,v-.22,.09),xyz(u+.22,v,.09),xyz(u,v+.22,.09)],b.M['confetti lilac'],.006,True)
    for r in [1.02,1.08]:
        b.line('Faded lobby medallion',[xyz(8.4+math.cos(t)*r,6.5+math.sin(t)*r,.10) for t in [i*math.tau/96 for i in range(96)]],b.M['confetti gold'],.007,True)
    # Worn flecks and dirt scars are meshes, not independent tiny objects.
    rng=random.Random(2011)
    for kind,count,mat in [('Gum on sidewalk',150,'gum'),('Fine asphalt aggregate',650,'scuffed paint')]:
        verts=[];faces=[]
        for i in range(count):
            u=rng.uniform(-10,22);v=rng.uniform(9.2,10.45) if 'Gum' in kind else rng.uniform(10.65,13.45)
            r=rng.uniform(.008,.027) if 'Gum' in kind else rng.uniform(.003,.012)
            j=len(verts);verts.extend([xyz(u+math.cos(k*math.tau/7)*r,v+math.sin(k*math.tau/7)*r*.65,.13) for k in range(7)])
            faces.append(tuple(range(j,j+7)))
        b.mesh(kind,verts,faces,b.M[mat])
    for i in range(48):
        u=rng.uniform(-9,22);v=rng.uniform(10.65,13.3)
        pts=[]
        for j in range(rng.randint(3,8)):
            pts.append(xyz(u,v,.12));u+=rng.uniform(.04,.14);v+=rng.uniform(-.11,.11)
        b.line('Branching asphalt crack',pts,b.M['tar crack'],rng.uniform(.003,.008))
    oil=b.material('Iridescent old oil',(.065,.045,.087),.21,.45,texture=13)
    for i in range(12):
        u=rng.uniform(-6,18);v=rng.uniform(10.8,13.3)
        pts=[xyz(u+math.cos(k*math.tau/28)*.22,v+math.sin(k*math.tau/28)*.075,.115) for k in range(28)]
        b.line('Oil tide edge',pts,oil,.004,True)

def scars(wall,start,end,front,top,count=70):
    rng=random.Random(int(start*100+end*17+top))
    for i in range(count):
        t=rng.uniform(start+.02,end-.02);z=rng.uniform(2,14)
        b.wall_line('Boot scuff',wall,[(t,z),(min(end,t+rng.uniform(.015,.09)),z+rng.uniform(-1,1))],b.M['scuffed paint'],.003,front)
    for i in range(count//5):
        t=rng.uniform(start+.02,end-.02);z=rng.uniform(top*.64,top*.96)
        b.wall_line('Fine water drip',wall,[(t,z),(t+.005,z-rng.uniform(5,19))],b.M['water streak'],.004,front)

def walls():
    ORIGINAL['walls']()
    # Keep all title/poster apertures untouched; wear the metal border edges only.
    for wall,at in [('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)]:
        a=at-1.55 if wall=='u' else at+.75
        b.wall_line('Sun faded poster edging',wall,[(a-.024,27),(a-.024,124)],b.M['faded paper'],.006,.015)
    scars('u',.1,3.3,.05,155,55);scars('v',.1,4.1,.05,155,55)

def low_wall(name,fp):
    if name=='front_low_wall':
        ORIGINAL['low_wall'](name,fp);scars('v',fp[0],fp[2],9.053,30,55);return
    b.layer(name,fp,90);a,c,d,e=fp
    wall='u' if d-a<e-c else 'v';start=c if wall=='u' else a;end=e if wall=='u' else d
    b.box(name+' plaster',a,c,d,e,0,88,b.M['old plaster'],.01)
    front=3.105
    b.wallbox('Lobby walnut wainscot',wall,start,end,0,39,b.M['dark plum'],front,.035)
    b.wallbox('Lobby brass dado',wall,start,end,38,41,b.M['warm brass'],front+.008,.045)
    b.wallbox('Partition worn coping',wall,start,end,87,90,b.M['counter stone'],3.1,.2)
    b.wall_line('Lobby neon strip',wall,[(start,44),(end,44)],b.M['cyan neon' if wall=='u' else 'pink neon'],.009,front+.012)
    for i in range(int((end-start)/.32)):
        t=start+(i+.5)*.32;b.wall_line('Wainscot panels',wall,[(t,6),(t,34)],b.M['warm brass'],.004,front+.01)
    scars(wall,start,end,front+.023,86,90)

def wall_text(name,body,wall,t,z,size,mat,front=3.155):
    return b.text(name,body,b.wp(wall,t,z,front),size,b.M[mat],rotation=UFACE if wall=='u' else b.FRONT_FACE)

def box_office():
    b.layer('boxoffice',[3.8,5,4.4,8.4],84)
    b.box('Ticket desk plinth',3.8,5,4.4,8.4,0,5,b.M['black enamel'])
    b.box('Ticket desk teal cabinet',3.82,5.02,4.38,8.38,5,40,b.M['velvet teal'])
    b.box('Ticket desk worn stone top',3.8,5,4.4,8.4,40,44,b.M['counter stone'])
    for i in range(28):
        v=5.05+i*.12;b.box('Ticket counter ribs',4.38,v,4.395,v+.025,6,36,b.M['warm brass'],.003)
    b.line('Ticket desk cyan edging',[xyz(4.405,5,36),xyz(4.405,8.4,36),xyz(3.8,8.4,36)],b.M['cyan neon'],.009)
    # Two actual speaking holes in the glass, with open tray slots underneath.
    for a,c in [(5.02,5.68),(6.32,7.08),(7.72,8.38)]:
        b.box('Cashier fixed glazing',4.10,a,4.115,c,44,84,b.M['glass'],.002)
    for v in [6,7.4]:
        b.box('Window lower glass',4.10,v-.32,4.115,v+.32,50,61,b.M['glass'],.002)
        b.box('Window upper glass',4.10,v-.32,4.115,v+.32,73,84,b.M['glass'],.002)
        # Annular rectangle triangulated around an elliptical speaking opening.
        verts=[];faces=[]
        for j in range(48):
            t=j*math.tau/48;co=math.cos(t);si=math.sin(t)
            factor=min(.32/max(abs(co),1e-7),6/ZPP/max(abs(si),1e-7))
            verts.extend([xyz(4.116,v+co*.064,67+si*4.7),xyz(4.116,v+co*factor,67+si*factor*ZPP)])
        for j in range(48):faces.append((j*2,j*2+1,((j+1)%48)*2+1,((j+1)%48)*2))
        b.mesh('Glass around speaking hole',verts,faces,b.M['glass'])
        b.line('Speaking hole brass rim',[xyz(4.123,v+math.cos(j*math.tau/48)*.064,67+math.sin(j*math.tau/48)*4.7) for j in range(48)],b.M['brushed nickel'],.005,True)
        b.box('Ticket pass tray',3.92,v-.23,4.36,v+.23,44,45,b.M['brushed nickel'],.008)
        b.box('Ticket slot dark bottom',4.12,v-.18,4.34,v+.18,45,45.2,b.M['ink'],.001)
        for k in range(3):b.box('Printed tickets',4.27,v-.12,4.36,v+.06,45.3+k*.25,45.5+k*.25,b.M['paper'],.001)
    for v in [5.02,6.7,8.38]:b.box('Cashier screen upright',4.08,v-.014,4.14,v+.014,44,84,b.M['brushed nickel'],.004)
    b.box('Cashier screen top rail',4.08,5.02,4.14,8.38,82.5,84,b.M['brushed nickel'],.004)
    # Wall sign is part of the occluding partition, so it cannot bleed through it.
    b.layer('partition_left')
    b.wallbox('Tickets lightboard housing','u',5.05,8.3,58,87,b.M['black enamel'],3.14,.04)
    b.wallbox('Tickets amber lightboard','u',5.1,8.25,60,85,b.M['soft menu'],3.151,.01)
    wall_text('Tickets heading','T I C K E T S','u',6.67,78,.19,'ink')
    wall_text('Ticket showtime list','MATINEE  4.50  /  EVENING  6.00','u',6.67,65,.095,'ink')
    b.layer('background')
    for v in [6,7.4]:
        # Wall shelf leaves the cashier's floor point unoccupied.
        b.box('Cashier rear shelf',3.12,v-.38,3.34,v+.38,31,34,b.M['counter stone'])
        b.box('Ticket printer',3.14,v-.28,3.32,v-.07,34,43,b.M['black enamel'],.012)
        b.box('Ticket printer paper',3.31,v-.26,3.34,v-.09,36,39,b.M['paper'],.001)
        b.box('Cash register',3.14,v+.06,3.33,v+.30,34,44,b.M['brushed nickel'],.013)
        b.box('Register green display',3.331,v+.08,3.34,v+.28,40,43,b.M['cyan neon'],.001)

def concessions():
    b.layer('snack',[5.6,4,11.6,4.6],44)
    b.box('Snack counter plinth',5.6,4,11.6,4.6,0,5,b.M['black enamel'])
    b.box('Snack cabinet rear',5.62,4.02,11.58,4.32,5,40,b.M['dark plum'])
    b.box('Snack granite top',5.6,4,11.6,4.6,40,44,b.M['counter stone'])
    # Continuous recessed front display, glass flush with the front face.
    b.box('Candy display black recess',5.65,4.32,11.55,4.37,9,36,b.M['black enamel'],.007)
    for z in [11,24]:
        b.box('Candy shelf',5.68,4.36,11.52,4.59,z,z+1,b.M['warm brass'],.002)
        for i in range(35):
            u=5.72+i*.165
            b.box('Candy packets',u,4.44,u+.115,4.57,z+1,z+7,b.M[['confetti pink','confetti cyan','confetti gold','confetti lilac'][i%4]],.007)
    b.box('Candy display glass',5.68,4.594,11.52,4.599,10,36,b.M['glass'],.001)
    for u in [5.6,7.1,8.6,10.1,11.58]:b.box('Candy cabinet mullion',u,4.58,u+.02,4.6,5,40,b.M['warm brass'],.003)
    b.line('Snack counter pink edging',[xyz(5.6,4.605,37),xyz(11.6,4.605,37)],b.M['pink neon'],.009)
    # All upper equipment is behind staff but taller than a 50px emote, so it
    # shares partition_right's depth-sliced sprite. The low back cabinet is bg.
    b.layer('background')
    b.box('Back bar low cabinet',5.55,3.1,11.65,3.45,0,31,b.M['dark plum'])
    b.box('Back bar worktop',5.55,3.1,11.65,3.45,31,34,b.M['counter stone'])
    b.layer('partition_right')
    for u in [6.0,7.06]:
        b.box('Popper red base',u,3.12,u+.65,3.44,34,40,b.M['red enamel'])
        for va in [3.13,3.43]:b.box('Popper glass panel',u+.02,va,u+.63,va+.008,40,65,b.M['glass'],.001)
        for x in [u+.015,u+.635]:
            for v in [3.13,3.43]:b.box('Popper corner',x,v,x+.014,v+.014,40,68,b.M['warm brass'],.003)
        b.box('Popper red crown',u,3.12,u+.65,3.45,65,70,b.M['red enamel'])
        b.box('Popper warming lamp',u+.04,3.16,u+.61,3.4,63,64,b.M['warm light'],.002)
        b.cylinder('Popper kettle',xyz(u+.33,3.28,57),.10,.09,b.M['brushed nickel'])
        for j in range(80):b.ball('Fresh popcorn',xyz(u+b.RNG.uniform(.05,.60),b.RNG.uniform(3.17,3.40),b.RNG.uniform(41,47)),.024,b.M['popcorn'],(1,.85,1.2))
        wall_text('Popper label','POPCORN','v',u+.325,67,.08,'soft menu',3.455)
        b.point('Static popcorn amber lamp',xyz(u+.33,3.28,57),3,(1,.54,.15),.13)
    b.box('Soda fountain',8.0,3.12,8.78,3.43,34,65,b.M['brushed nickel'])
    b.box('Soda fountain dark face',8.03,3.431,8.75,3.445,42,61,b.M['black enamel'])
    for i in range(4):
        u=8.12+i*.17
        b.box('Soda selection button',u-.05,3.45,u+.05,3.46,53,60,b.M[['red enamel','cyan neon','warm light','confetti lilac'][i]],.003)
        b.line('Soda nozzle',[xyz(u,3.46,51),xyz(u,3.48,46)],b.M['black enamel'],.015)
    b.box('Soda drip tray',8.0,3.38,8.78,3.45,34,36,b.M['black enamel'])
    b.box('Hotdog grill base',9.1,3.13,9.82,3.44,34,39,b.M['brushed nickel'])
    for i in range(7):
        b.cylinder('Hotdog steel roller',xyz(9.46,3.17+i*.037,41),.017,.61,b.M['brushed nickel'],(1,0,0),12)
    for i in range(4):b.cylinder('Hotdog on roller',xyz(9.46,3.19+i*.065,44),.026,.29,b.M['terracotta'],(1,0,0),12)
    b.box('Nacho warmer base',10.02,3.12,10.65,3.44,34,39,b.M['warm brass'])
    b.box('Nacho warmer glass',10.04,3.43,10.63,3.44,39,55,b.M['glass'],.002)
    b.box('Nacho warmer lid',10.02,3.12,10.65,3.44,55,58,b.M['red enamel'])
    for i in range(35):
        u=b.RNG.uniform(10.08,10.59);v=b.RNG.uniform(3.16,3.39);z=b.RNG.uniform(40,46)
        b.mesh('Tortilla chips',[xyz(u-.03,v,z),xyz(u+.04,v,z),xyz(u,v+.04,z+2)],[(0,1,2)],b.M['popcorn'])
    for u in [10.94,11.13,11.32]:
        for i in range(6):b.cylinder('Stacked striped cups',xyz(u,3.29,37+i*1.8),.052,.065,b.M['paper'],vertices=16)
        b.line('Cup red stripe',[xyz(u-.05,3.342,40),xyz(u+.05,3.342,40)],b.M['red enamel'],.007)
    # Wall-plane menus, below the 90px top. No floating panels over corridor.
    for a,c,title,price in [(5.6,7.65,'POPCORN','$4.50'),(7.8,9.6,'SODA','$2.75'),(9.75,11.6,'NACHOS','$3.25')]:
        b.wallbox('Menu housing','v',a,c,72,88,b.M['black enamel'],3.134,.03)
        b.wallbox('Menu glowing paper','v',a+.04,c-.04,73.5,86.5,b.M['soft menu'],3.15,.01)
        wall_text('Snack menu title',title+'  '+price,'v',(a+c)/2,80,.125,'ink')
    wall_text('Snack bar label','SNACK BAR','v',5.05,76,.105,'soft menu')
    b.META['partition_right']['geometry_footprint']=[4.4,2.9,13,3.48]
    b.META['partition_right']['contents']='90px wall, menus, and tall back-bar equipment, all behind clerks'

def move_group(name,old,new):
    bpy.context.view_layer.update()
    sx=(new[2]-new[0])/(old[2]-old[0]);sv=(new[3]-new[1])/(old[3]-old[1])
    matrix=Matrix.Translation((new[0],-new[1],0))@Matrix.Diagonal((sx,sv,1,1))@Matrix.Translation((-old[0],old[1],0))
    for obj in b.GROUPS[name]:obj.matrix_world=matrix@obj.matrix_world
    b.layer(name,new,b.META[name]['height_px'])

def furniture():
    ORIGINAL['furniture']()
    move_group('podium',[4.6,3.5,5.1,4],[4.55,3.55,5,4])
    bpy.data.objects['Usher lamp glow'].location=xyz(4.82,3.73,46)
    move_group('bench',[6.4,3.25,7.9,3.75],[11.2,6,12.6,6.4])
    move_group('standee_2',[6,6.3,6.42,6.36],[7.2,8.5,7.62,8.56])
    b.META['standee_2']['geometry_footprint']=[7.15,8.42,7.67,8.64]
    b.layer('palm',[12.3,3.4,12.8,3.9],112)
    b.cylinder('Palm pot',xyz(12.55,3.65,12),.235,24/ZPP,b.M['terracotta'],vertices=28)
    b.cylinder('Palm pot lip',xyz(12.55,3.65,23),.25,4/ZPP,b.M['terracotta'],vertices=28)
    b.cylinder('Palm soil',xyz(12.55,3.65,25),.21,.008,b.M['pot soil'],vertices=24)
    for j in range(3):
        u=12.55+(j-1)*.07;v=3.65+(j-1)*.04;top=82+j*9
        b.line('Palm cane',[xyz(u,v,24),xyz(u-.04,v,top)],b.M['warm brass'],.018)
        for k in range(7):
            t=k*math.tau/7+j;length=.36+(k%3)*.07
            spine=[xyz(u+math.cos(t)*length*s,v+math.sin(t)*length*s,top+17*math.sin(s*math.pi)-12*s) for s in [i/8 for i in range(9)]]
            b.line('Palm frond spine',spine,b.M['palm leaf'],.006)
            for q in range(1,8):
                s=q/8;pt=spine[q];wide=.10*math.sin(math.pi*s)
                for side in [-1,1]:
                    end=pt+Vector((math.cos(t+side*1.25)*wide, -math.sin(t+side*1.25)*wide,-.035))
                    tip=spine[min(q+1,8)]
                    b.mesh('Palm tapered leaflet',[pt,end,tip],[(0,1,2)],b.M['palm leaf light' if k%3==0 else 'palm leaf'])
    b.META['palm']['geometry_footprint']=[11.97,3.1,13.08,4.2]

def exterior_props():
    ORIGINAL['exterior_props']()
    # Grimy shelter and storefront: fine streaks attached to their own sprites.
    for name in ['bus_stop','glass_left','glass_right']:
        b.layer(name);fp=b.META[name]['footprint'];rng=random.Random(len(name)*33)
        for i in range(16):
            u=rng.uniform(fp[0]+.02,fp[2]-.02);v=9.435 if name=='bus_stop' else 9.012
            top=rng.uniform(18,70) if name=='bus_stop' else rng.uniform(12,27)
            b.line('Glass rain residue',[xyz(u,v,top),xyz(u+.002,v,top-rng.uniform(4,10))],b.M['water streak'],.002)

def build(samples,scale):
    for name in ORIGINAL:setattr(b,name,globals()[name])
    b.box_office=box_office;b.concessions=concessions
    return b.build(samples,scale)

def timed(path):
    start=time.perf_counter();render(path)
    TIMES.append({'file':str(path.relative_to(ROOT)),'seconds':round(time.perf_counter()-start,3)})
    (QA/'render_times.json').write_text(json.dumps(TIMES,indent=2))
    print('PASS2_RENDER',json.dumps(TIMES[-1]),flush=True)

def geometry_bounds():
    bpy.context.view_layer.update();result={}
    for name,objects in b.GROUPS.items():
        if name=='background':continue
        coords=[obj.matrix_world@Vector(c) for obj in objects for c in obj.bound_box]
        result[name]={'geometry_footprint':[round(min(c.x for c in coords),5),round(min(-c.y for c in coords),5),round(max(c.x for c in coords),5),round(max(-c.y for c in coords),5)],
            'geometry_z_px':[round(min(c.z for c in coords)*ZPP,3),round(max(c.z for c in coords)*ZPP,3)]}
    return result

def manifest(sc):
    return {'layout':2,'status':'stills_ready','size':[1920,1080],'scale2x':True,'bg':'bg.png','glow':None,'full':'full.png',
        'occluders':sorted(b.META.values(),key=lambda o:o['depth']),
        'baked_signs':['tickets','showtime_prices','snackbar','gate','restroom','roxy','bus95','arcade_orbit','popcorn','standee_midnight','standee_voyager'],
        'projection':{'origin':[900,350],'tile_x':[60,30],'tile_y':[-60,30],'vertical_px_per_blender_unit':ZPP},
        'billboard_rect':[1296,40,576,324],
        'alpha':'PNG straight (unassociated); browser source-over; do not premultiply again',
        'render_device':sc['render_device'],'seed':1997,
        'staff_positions':{'cashiers':[[3.45,7.4],[3.45,6]],'snack_clerks':[[6.6,3.75],[8.2,3.75],[9.8,3.75]],'usher':[5.3,3.8]},
        'customer_positions':{'tickets':[[4.85,7.4],[4.85,6]],'ticket_queue_direction':[1,0],'snack':[[6.6,5.05],[8.2,5.05],[9.8,5.05]]},
        'coordinate_deviations':[
            {'name':'standee_1_foot','geometry_footprint':[12.15,4.92,12.67,5.14],'reason':'Preserved stabilizing foot; sorting footprint remains exact.'},
            {'name':'standee_2_foot','geometry_footprint':[7.15,8.42,7.67,8.64],'reason':'Same stabilizing foot at new position; sorting footprint remains exact.'},
            {'name':'bus_shelter_roof','geometry_footprint':[.35,9.25,2.05,9.6],'reason':'Preserved pass-1 roof overhang.'},
            {'name':'palm_fronds','geometry_footprint':[11.97,3.1,13.08,4.2],'height_px':112,'reason':'Pot within requested footprint; crown naturally overhangs.'},
            {'name':'soda_nozzles','geometry_footprint':[8.0,3.12,8.78,3.48],'reason':'Spouts project 0.03 tile past 3.45 worktop, above floor.'},
            {'name':'street_padding','geometry_footprint':[-12,9.15,23,13.5],'reason':'Preserved offscreen padding from pass 1.'}],
        'footprint_changes':[],
        'notes':['All requested layout-2 sorting footprints are exact. Coordinate deviations above are geometry overhangs only.',
            '90px partitions include their wall-mounted signage. Upper back-bar appliances share partition_right sprites because they are taller than the clerks.',
            'Back bar low cabinet, ticket printer and register are background, behind staff.',
            'Movie marquees and poster apertures deliberately blank; restroom occupancy remains dynamic.',
            'Live out/ is untouched. Loop will be added after the still manifest is ready.'],
        'marquees':[{'screen':i,'bottom_center':project(0,a,124) if w=='u' else project(a,0,124),'inner_size':[176,92]} for i,(w,a) in enumerate([('u',6.4),('u',4),('v',4.8),('v',8.2),('v',11.2)],1)]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preview','final'],default='preview');p.add_argument('--samples',type=int,default=32);p.add_argument('--tag',default='layout2_preview');p.add_argument('--only',default='')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
    if args.only and (QA/'render_times.json').exists():TIMES.extend(json.loads((QA/'render_times.json').read_text()))
    sc=build(args.samples,1)
    if args.mode=='preview':timed(QA/(args.tag+'.png'));return
    sc.cycles.adaptive_threshold=.01
    from depth_pass import configure,export_array
    pos=QA/'positions';pos.mkdir(exist_ok=True);aov=configure(sc,pos);aov.mute=True
    for name in b.META:
        x,y,x1,y1=b.bounds_for(name);b.META[name].update(file='occ_'+name+'.png',x=x,y=y,w=x1-x,h=y1-y)
    (QA/'manifest_staging.json').write_text(json.dumps(manifest(sc),indent=2))
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass2.blend'))
    selected=args.only.split(',') if args.only else None
    for scale,suffix in [(1,''),(2,'@2x')]:
        sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
        sc.render.use_border=False;sc.render.use_crop_to_border=False
        if not selected or 'full' in selected:
            b.set_visibility();timed(QA/('cycles_full'+suffix+'.png'))
        if not selected or 'bg' in selected:
            b.set_visibility('background');timed(QA/('raw_bg'+suffix+'.png'))
        for name,e in b.META.items():
            if selected and name not in selected:continue
            b.set_visibility(name);x,y,w,h=[e[k] for k in ['x','y','w','h']]
            sc.render.use_border=True;sc.render.use_crop_to_border=True
            # Blender stores normalized borders as float32 then truncates pixels.
            # A tenth-pixel interior bias avoids 970.99998 becoming 970 at x=971.
            sc.render.border_min_x=(x+.1)/1920;sc.render.border_max_x=min(1,(x+w+.1)/1920)
            sc.render.border_min_y=(1080-y-h+.1)/1080;sc.render.border_max_y=min(1,(1080-y+.1)/1080)
            aov.mute=False;aov.file_name=name+suffix+'_'
            timed(OUT/(e['file'][:-4]+suffix+'.png'))
            path=pos/(name+suffix+'_FloorUV.exr');export_array(path,pos/(name+suffix+'.npz'));path.unlink();aov.mute=True
    b.set_visibility()

if __name__=='__main__':main()
