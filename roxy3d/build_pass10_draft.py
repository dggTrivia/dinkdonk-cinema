"""Layout 3, draft only. One 1080p still; never invokes the pack pipeline."""
import sys,json,math,time,random,hashlib
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector,Matrix
import build_scene as b
from common import ROOT,xyz,ZPP,project,NORMAL,render
from pass8_common import gpu

QA=ROOT/'qa10';QA.mkdir(exist_ok=True)
META={'layout':3,'draft_only':True,'source':'roxy_pass9.blend','removed':[],
      'footprints':[],'walkable_spots':{},'ad_surfaces':[]}
RNG=random.Random(1010)
UFACE=Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
BACKFACE=Matrix(((-1,0,0),(0,0,1),(0,1,0))).transposed().to_quaternion()

def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:
        f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: '+s+'\n')
    print('DRAFT_STAGE',s,flush=True)

def rm(o):
    META['removed'].append(o.name)
    for group in b.GROUPS.values():
        if o in group:group.remove(o)
    bpy.data.objects.remove(o,do_unlink=True)

def bounds(o):
    if o.type not in ['MESH','CURVE','FONT']:
        return [o.location.x,-o.location.y,o.location.x,-o.location.y,o.location.z*ZPP,o.location.z*ZPP]
    p=[o.matrix_world@Vector(c) for c in o.bound_box]
    return [min(q.x for q in p),min(-q.y for q in p),max(q.x for q in p),max(-q.y for q in p),min(q.z for q in p)*ZPP,max(q.z for q in p)*ZPP]

def mat(n,c,r=.5,e=0,metal=0,texture=0):return b.material('P10 '+n,c,r,metal,e,texture)
def box(n,*args):return b.box('P10 '+n,*args)
def line(n,p,ma,r=.012):return b.line('P10 '+n,[xyz(*q) for q in p],ma,r)
def text(n,s,u,v,z,size,ma,wall='v'):
    return b.text('P10 '+n,s,xyz(u,v,z),size,ma,UFACE if wall=='u' else b.FRONT_FACE)
def footprint(n,rect,height,kind='solid'):
    META['footprints'].append({'name':n,'uv':rect,'height_px':height,'kind':kind})
def ellipse(n,u,v,z,rx,rz,ma,wall='v',radius=.009):
    pts=[(u+rx*math.cos(t),v,z+rz*math.sin(t)) if wall=='v' else (u,v+rx*math.cos(t),z+rz*math.sin(t)) for t in np.linspace(0,math.tau,33)]
    return line(n,pts,ma,radius)

def strip_old(sc):
    for o in list(sc.objects):
        a,v,c,w,z,h=bounds(o);n=o.name
        tower=(n.startswith(('P8 ','P9 ')) and a>=5.8 and c<=16.5 and v>=-5.2 and w<=-.35)
        rear_conflict=(n.startswith('P8B ') and a>=2.9 and c<4.7 and v<-.5 and w> -4.5 and h<220)
        left_old=(o.get('layer') in [None,'background'] and a>-.79 and c<.4 and v>=-.02 and w<=9.06 and h<180)
        old_sign=o.get('layer') in ['roxy_blade','ad_tower','front_low_wall'] or n.startswith(('P9 blue neon','P9 mint neon','P9 billboard warm','P8 billboard brick fill'))
        if tower or rear_conflict or left_old or old_sign:rm(o)
    for o in sc.objects:
        if o.get('door_id') in ['3','4','5']:o['door_id']=str(int(o['door_id'])-2)
        if o.type=='FONT':
            if o.name=='P9 entrance legend':o.data.body='DINK DONK  /  CINEMA';o.data.size=.067
            if o.name=='P9 window sticker':o.data.body='DD';o.data.size=.095
            if o.name=='P9 hanging wayfinding text':o.data.body='WC  <'
            if o.name=='P9 hanging wayfinding caption':o.data.body='RESTROOM'
            if o.name=='P9 hanging wayfinding text.001':o.data.body='>  1 - 3'
            if o.name=='P9 bus route lettering':o.data.body='95 / d.gg transit';o.data.size=.095
    # Remaining original thin left-side service building is no longer an auditorium.
    for o in sc.objects:
        if o.name.startswith('P8 Roxy auditorium'):o.name='P10 existing left service roof block'
        if o.name.startswith('P8 auditorium roof vent'):o.name=o.name.replace('auditorium','service')
    status('Source copied in memory; old left screen/loo fittings and commercial tower removed; right-wing screens renumbered 1-3')

def materials():
    global metal,black,ivory,teal,brass,red,tile,grout,porcelain,mirror,roof,brick,plaster,amber,green,yellow,blue,core,greenbody,yellowbody,bluebody,puddle
    metal=mat('aged graphite steel',(.045,.057,.065),.34,metal=.65,texture=42)
    black=mat('velvet darkness',(.003,.004,.006),1)
    ivory=mat('warm enamel lettering',(.78,.80,.70),.48,e=.28)
    teal=mat('restroom teal partitions',(.075,.24,.21),.44,texture=75)
    brass=mat('worn queue brass',(.40,.28,.13),.29,metal=.8,texture=65)
    red=mat('burgundy velvet rope',(.36,.014,.036),.88,texture=120)
    tile=mat('cream glazed tiles',(.43,.49,.45),.24,texture=85)
    grout=mat('dark aged grout',(.065,.085,.075),.96)
    porcelain=mat('off white porcelain',(.72,.77,.70),.17)
    mirror=mat('mirror silver',(.67,.77,.79),.08,metal=.98)
    roof=mat('wet mineral felt',(.055,.068,.082),.53,texture=75)
    brick=bpy.data.materials['P8 brownbrick']
    plaster=mat('auditorium faded concrete',(.18,.18,.17),.87,texture=38)
    amber=mat('amber display',(.9,.40,.065),.3,e=2)
    green=mat('frog mint tube core',(.13,1,.22),.2,e=7)
    yellow=mat('warning yellow tube core',(1,.68,.015),.2,e=8)
    blue=mat('cyan rooftop letter core',(.16,.76,1),.2,e=7)
    core=mat('warm white eye tube',(.85,1,.71),.2,e=6)
    greenbody=mat('frog glass body',(.025,.23,.04),.24,e=.5)
    yellowbody=mat('amber glass body',(.42,.20,.008),.24,e=.6)
    bluebody=mat('cyan glass body',(.025,.23,.32),.24,e=.5)
    puddle=mat('roof standing rainwater',(.018,.028,.038),.055,metal=.5)

def auditoriums():
    b.layer('auditorium_block')
    edges=[3,19/3,29/3,13];heights=[238,246,240]
    for i,(a,c,h) in enumerate(zip(edges[:-1],edges[1:],heights),1):
        # Hollow shell: real doorway vestibules remain empty inside.
        box('hall %d concrete floor'%i,a,-4.4,c,-.23,-5,0,plaster)
        box('hall %d rear masonry'%i,a,-4.4,c,-4.23,0,h,brick)
        for u in [a,c-.12]:box('hall %d side wall'%i,u,-4.4,u+.12,-.23,0,h,brick)
        box('hall %d front upper wall'%i,a,-.40,c,-.23,170,h,brick)
        box('hall %d roof slab'%i,a,-4.4,c,-.23,h-4,h,roof,.008)
        for vv in [-4.4,-.30]:box('hall parapet',a,vv,c,vv+.07,h,h+6,plaster,.008)
        for uu in [a,c-.055]:box('hall roof dividing coping',uu,-4.4,uu+.055,-.23,h,h+5,plaster,.004)
        # Projection booth, service hatch, HVAC unit and bent ductwork.
        mid=(a+c)/2
        box('projection booth %d'%i,mid-.55,-1.55,mid+.55,-.58,h,h+29,plaster)
        box('projection booth felt cap',mid-.59,-1.59,mid+.59,-.54,h+29,h+32,roof,.008)
        box('projection booth louvres',mid-.32,-.575,mid+.32,-.56,h+9,h+19,metal,.004)
        for k in range(5):box('booth vent slat',mid-.30,-.555,mid+.30,-.547,h+9+k*2,h+9.6+k*2,black,0)
        box('roof hatch rim',a+.3,-2.42,a+.91,-1.89,h,h+4,metal,.006)
        box('roof hatch lid',a+.34,-2.38,a+.87,-1.93,h+4,h+5.5,plaster,.005)
        line('roof hatch grab',[(a+.47,-2.04,h+5.5),(a+.47,-2.04,h+8),(a+.70,-2.04,h+8),(a+.70,-2.04,h+5.5)],metal,.012)
        box('HVAC feet',mid-.5,-3.6,mid+.5,-2.75,h,h+5,metal)
        box('HVAC cabinet',mid-.47,-3.57,mid+.47,-2.78,h+5,h+28,metal)
        for du in [-.23,.23]:
            b.cylinder('P10 HVAC fan',xyz(mid+du,-3.17,h+28.5),.18,.012,black,vertices=24)
            for k in range(6):
                ang=k*math.pi/6
                line('HVAC grille',[(mid+du-.16*math.cos(ang),-3.17-.16*math.sin(ang),h+29),(mid+du+.16*math.cos(ang),-3.17+.16*math.sin(ang),h+29)],brass,.005)
        box('air duct horizontal',mid+.30,-2.80,mid+.70,-1.64,h+9,h+22,metal)
        box('air duct elbow',mid+.30,-1.79,mid+.70,-1.42,h+4,h+22,metal)
        for vv in np.arange(-2.72,-1.65,.18):box('duct seam',mid+.29,vv,mid+.71,vv+.012,h+8.5,h+22.4,brass,0)
        for j in range(4):
            u=a+.30+RNG.random()*(c-a-.6);v=-4.05+RNG.random()*3.3
            b.ball('P10 roof puddle',xyz(u,v,h+.07),1,puddle,(.23+RNG.random()*.15,.12+RNG.random()*.13,.001))
        footprint('Auditorium '+str(i),[a,-4.4,c,-.23],h+32)
    b.area('P10 broad roof moon fill',xyz(8,-1,650),700,(.43,.54,.77),9,target=xyz(8,-2,230))
    b.area('P10 auditorium facade fill',xyz(8,3,420),200,(.55,.46,.34),7,target=xyz(8,-.24,210))
    META['screens']=[{'screen':i,'door_uv':[u,0],'approach_uv':[u-.5,0,u+.5,1.4],'hall_uv':[edges[i-1],-4.4,edges[i],-.23],'roof_z':heights[i-1]} for i,u in enumerate([4.8,8.2,11.2],1)]
    status('Three hollow auditorium shells, projection booths, HVAC/ducts, hatches and wet roofs modelled behind the surviving doors')

def tube(n,pts,color,body,r=.019):
    line(n+' bent glass',pts,body,r)
    line(n+' luminous core',[(u,v+r*.95,z) for u,v,z in pts],color,r*.37)
    for p in [pts[0],pts[-1]]:b.ball('P10 '+n+' rounded tube end',xyz(p[0],p[1]+r*.95,p[2]),r*.4,color)
    for p in pts[::max(1,len(pts)//3)]:line(n+' standoff',[(p[0],p[1]-.065,p[2]),p],metal,.008)

def frog(u,v,z,w,h,n):
    # Hand-drawn tube paths from ref/dinkdonk-emote/DinkDonk.png: warning
    # triangle, asymmetric low frog head, drooping eyes, flat mouth and chin.
    def path(label,p,c=green,body=greenbody,r=.017):tube(n+' '+label,[(u+x*w,v,z+y*h) for x,y in p],c,body,r)
    path('warning triangle',[(.05,.07),(.50,.98),(.96,.07),(.05,.07)],yellow,yellowbody,.023)
    path('frog silhouette',[(.12,.20),(.10,.31),(.20,.43),(.33,.47),(.34,.56),(.44,.61),(.55,.58),(.62,.62),(.76,.60),(.82,.52),(.92,.46),(.86,.31),(.73,.20),(.56,.16),(.36,.17),(.12,.20)])
    path('left eyelid',[(.31,.47),(.42,.50),(.53,.48)],core,greenbody,.013)
    path('right eyelid',[(.60,.50),(.71,.52),(.81,.49)],core,greenbody,.013)
    path('left pupil',[(.43,.49),(.43,.44)],yellow,yellowbody,.014)
    path('right pupil',[(.72,.51),(.72,.46)],yellow,yellowbody,.014)
    path('muzzle',[(.17,.34),(.34,.36),(.51,.33),(.70,.34),(.82,.39)],green,greenbody,.015)
    path('mouth',[(.20,.28),(.38,.27),(.58,.28),(.72,.31)],core,greenbody,.011)

GLYPHS={
'D':[[(0,0),(0,1),(.57,1),(.85,.82),(.85,.20),(.57,0),(0,0)]],
'I':[[(.12,1),(.76,1)],[(.44,1),(.44,0)],[(.12,0),(.76,0)]],
'N':[[(0,0),(0,1),(.85,0),(.85,1)]],
'K':[[(0,0),(0,1)],[(.85,1),(0,.46),(.85,0)]],
'O':[[(.2,0),(0,.20),(0,.8),(.2,1),(.65,1),(.85,.8),(.85,.20),(.65,0),(.2,0)]]}

def branding():
    b.layer('rooftop_neon')
    v=-.61
    for z in [322,421]:line('rooftop sign horizontal truss',[(3.7,v-.08,z),(12.55,v-.08,z)],metal,.036)
    for u in [3.8,5.6,7.4,9.2,11,12.5]:
        line('rooftop sign vertical truss',[(u,v-.08,244),(u,v-.08,425)],metal,.035)
        line('rooftop sign diagonal brace',[(u,-2.3,250),(u,v-.11,407)],metal,.023)
        box('roof sign foot',u-.11,-2.41,u+.11,-2.19,245,250,metal)
    for a in [3.8,5.6,7.4,9.2,11]:
        line('rooftop truss cross brace',[(a,v-.09,322),(min(a+1.8,12.5),v-.09,421)],metal,.012)
    frog(3.84,v,325,1.55,94,'rooftop DinkDonk')
    x=5.76
    for ch in 'DINK DONK':
        if ch==' ':x+=.30;continue
        for path in GLYPHS[ch]:tube('rooftop letter '+ch,[(x+px*.72,v+.03,343+py*64) for px,py in path],blue,bluebody,.023)
        x+=.79
    # A few deliberately visible ceramic transformers and insulated leads.
    for u in [5.3,8.7,11.8]:
        box('neon transformer',u-.10,v-.15,u+.10,v-.06,312,319,metal)
        line('neon supply lead',[(u,v-.08,316),(u+.05,v-.08,337)],black,.009)
    b.area('P10 rooftop neon cyan cast',xyz(8,-.40,360),85,(.10,.65,1),5,target=xyz(8,-1.7,241))
    b.point('P10 rooftop frog warm cast',xyz(4.55,-.3,375),30,(.9,.65,.08),.55)
    # Separate small projecting entrance emblem, on the existing facade location.
    b.layer('entrance_neon')
    box('small entrance neon backer',-.83,9.12,-.03,9.28,132,247,metal,.026)
    for z in [145,234]:line('entrance sign bracket',[(-.07,8.75,z),(-.07,9.24,z)],metal,.024)
    frog(-.79,9.32,168,.72,71,'entrance DinkDonk')
    text('entrance DD caption','DD',-.43,9.34,151,.28,blue)
    b.point('P10 entrance frog green spill',xyz(-.3,9.6,194),38,(.14,1,.23),.42)
    b.point('P10 entrance triangle yellow spill',xyz(-.3,9.6,231),24,(1,.62,.03),.40)
    # Wet street receives the neon colors from physical lights; no painted pixels.
    b.area('P10 sign street green reflection',xyz(.1,9.7,110),18,(.12,.8,.22),1.2,target=xyz(.1,11,0))
    META['brand']={'name':'DINK DONK','rooftop_sign':{'uv_plane_v':v,'along_u':[3.7,12.55],'z_px':[312,425]},'entrance_emblem':{'uv':[-.83,9.12,-.03,9.35],'z_px':[132,247]},'reference':'ref/dinkdonk-emote/DinkDonk.png'}
    # Transfer the tower ad to a smaller legible roof billboard clear of the wordmark.
    b.layer('ad_rooftop');a,c,v,z0,z1=10.0,12.7,-3.55,283,357
    box('roof billboard blank',a,v-.06,c,v,z0,z1,b.M['P9 backlit blank panel'],.006)
    for u in [a,c]:box('roof billboard upright',u-.035,v-.1,u+.035,v+.02,z0-2,z1+2,metal,.006)
    for z in [z0-2,z1]:box('roof billboard edge',a,v-.1,c,v+.02,z,z+2,metal,.006)
    for u in [a+.25,c-.25]:
        line('roof billboard leg',[(u,v-.04,244),(u,v-.04,z1)],metal,.025)
        line('roof billboard rear brace',[(u,-4.15,246),(u,v-.08,z1-5)],metal,.018)
    b.area('P10 roof billboard lamp',xyz(11.35,-3.1,368),18,(.8,.75,.56),1.5,target=xyz(11.35,v,320))
    ad={'name':'tower','new_name':'auditorium_rooftop','wall':'v','offset':v,'along':[a,c],'z_px':[z0,z1],
        'quad_px':[project(u,v,z) for u,z in [(a,z1),(c,z1),(c,z0),(a,z0)]],'aspect':(c-a)*ZPP/(z1-z0),'lit':True}
    META['ad_surfaces'].append(ad)
    old=json.loads((ROOT/'out9/manifest.json').read_text())
    META['ad_surfaces'] += [e for e in old['ad_surfaces'] if e['name']!='tower']
    status('DINK DONK roof truss/neon and two frog emblems modelled; former tower ad moved onto the auditorium roof; d.gg retained only on transit signage')

def bathroom():
    b.layer('restroom')
    # Rebuilt junction wall, then a tiled back wall for the cut-away restroom.
    box('junction plum wall',-.22,0,0,3,0,170,b.M['wall plum'])
    box('junction walnut dado',-.02,0,.02,3,0,44,b.M['dark plum'])
    line('junction neon',[ (.06,0,150),(.06,3,150)],b.M['pink neon'],.014)
    box('restroom left structural wall',-.22,3,0,9.02,0,155,plaster)
    box('restroom tiled floor',.025,3.04,2.86,8.40,.16,.8,grout,0)
    for u in np.arange(.04,2.86,.23):
        for v in np.arange(3.05,8.39,.23):box('restroom floor tile',float(u),float(v),min(float(u)+.216,2.86),min(float(v)+.216,8.39),.8,1.02,tile,0)
    # Wall tiles are one readable mesh per row, avoiding a costly subdivision.
    for v in np.arange(3.04,8.4,.32):
        for z in np.arange(2,153,18):box('restroom wall tile',.004,float(v),.018,min(float(v)+.308,8.4),float(z),min(float(z)+17,154),tile,.002)
    box('restroom teal wall belt',.018,3.02,.028,8.4,89,98,teal,.002)
    # New doorway at the corridor junction. Upper section/face is retained,
    # while the right wall stays cut down so the owner can see the fixtures.
    for a,c in [(0,.95),(1.85,2.9)]:box('restroom junction partition',a,2.94,c,3.08,0,125,plaster)
    box('restroom door lintel',.95,2.94,1.85,3.08,105,125,plaster)
    for u in [.95,1.81]:box('restroom door jamb',u,2.92,u+.04,3.1,0,106,metal,.006)
    box('restroom open door leaf',1.80,3.08,1.84,3.90,1,103,teal,.012)
    line('restroom open door pull',[(1.78,3.74,44),(1.78,3.74,58)],brass,.014)
    # Plaque is double sided, both faces belonging to the v=3 wall.
    box('restroom plaque',.96,2.89,1.84,3.115,109,122,metal,.005)
    text('restroom room-side plaque','RESTROOM',1.4,3.12,115.5,.10,ivory)
    b.text('P10 restroom corridor-side plaque','RESTROOM',xyz(1.4,2.885,115.5),.10,ivory,BACKFACE)
    box('occupancy housing',1.91,2.90,2.20,3.12,94,104,metal,.004)
    text('green vacant light','VACANT',2.055,3.127,99,.058,green)
    b.text('P10 corridor green vacant light','VACANT',xyz(2.055,2.893,99),.058,green,BACKFACE)
    b.point('P10 restroom plaque glow',xyz(2.05,3.2,99),1.5,(.15,1,.30),.08)
    # Four stalls run along u=0; doors face the common aisle.
    centers=[4.40,5.40,6.40,7.40]
    for j,v in enumerate(centers,1):
        lo=v-.48;hi=v+.48
        for vv in [lo,hi]:box('stall %d divider'%j,.04,vv,1.10,vv+.035,8,84,teal,.007)
        box('stall %d pilaster'%j,1.075,lo,1.115,lo+.11,2,85,metal,.004)
        # One door left ajar makes the ceramic toilet and stall purpose visible.
        if j==1:
            leaf=box('stall 1 ajar door',.54,lo+.08,1.07,lo+.12,9,78,teal,.007)
        else:
            box('stall %d door'%j,1.065,lo+.13,1.105,hi-.06,9,78,teal,.007)
            b.ball('P10 stall lock',xyz(1.128,hi-.16,41),.026,brass)
        for zz in [22,64]:box('stall hinge',1.104,lo+.13,1.119,lo+.18,zz,zz+5,brass,.002)
        b.ball('P10 toilet bowl',xyz(.53,v,23),1,porcelain,(.19,.26,.105))
        b.ball('P10 toilet seat opening',xyz(.54,v,29),1,black,(.11,.18,.012))
        b.cylinder('P10 toilet pedestal',xyz(.48,v,12),.10,20/ZPP,porcelain,vertices=20)
        box('toilet cistern',.13,v-.21,.32,v+.21,18,49,porcelain,.03)
        box('toilet cistern lid',.11,v-.23,.34,v+.23,49,51,porcelain,.02)
        line('toilet flush lever',[(.34,v+.10,45),(.38,v+.10,45)],brass,.012)
        b.cylinder('P10 toilet paper roll',xyz(.75,lo+.08,36),.055,.14,ivory,(1,0,0),16)
        footprint('Stall '+str(j),[.04,lo,1.12,hi+.035],85)
    # Two sinks/mirrors face into the room from the new inner wall.
    for j,u in enumerate([2.12,2.63],1):
        box('sink wall bracket',u-.16,3.10,u+.16,3.34,26,33,metal)
        b.ball('P10 sink %d ceramic basin'%j,xyz(u,3.39,39),1,porcelain,(.205,.25,.085))
        b.ball('P10 sink %d basin recess'%j,xyz(u,3.40,43),1,teal,(.125,.16,.012))
        line('sink chrome faucet',[(u,3.17,42),(u,3.17,53),(u,3.33,53),(u,3.33,49)],brass,.014)
        box('sink mirror frame',u-.215,3.084,u+.215,3.105,59,96,metal,.008)
        box('sink mirror',u-.195,3.106,u+.195,3.111,61,94,mirror,.004)
        box('mirror light',u-.19,3.13,u+.19,3.16,99,102,ivory,.004)
        line('sink drain pipe',[(u,3.37,35),(u,3.37,18),(u,3.12,18)],metal,.018)
        footprint('Sink '+str(j),[u-.21,3.08,u+.21,3.65],53)
    box('hand dryer enamel body',.32,3.09,.72,3.32,48,70,porcelain,.028)
    box('hand dryer nozzle',.38,3.24,.65,3.34,44,49,metal,.008)
    text('dryer label','DRY',.52,3.335,61,.07,teal)
    footprint('Hand dryer',[.32,3.08,.72,3.34],70)
    # Mop/service fixtures stay out of the central circulation aisle.
    box('mop sink tray',2.14,7.56,2.78,8.12,1,12,porcelain,.03)
    box('mop sink recessed pan',2.20,7.62,2.72,8.06,12,12.2,teal,.01)
    line('mop sink tap',[(2.81,7.85,16),(2.81,7.85,40),(2.60,7.85,40),(2.60,7.85,35)],brass,.016)
    line('mop handle',[(2.55,8.17,5),(2.75,8.25,87)],brass,.013)
    for j in range(7):line('mop strands',[(2.53+(j-3)*.035,8.15,8),(2.47+(j-3)*.045,8.18,1.2)],ivory,.014)
    b.cylinder('P10 restroom trash can',xyz(2.58,6.88,18),.19,34/ZPP,metal,vertices=24)
    b.cylinder('P10 restroom trash dark opening',xyz(2.58,6.88,35),.16,.015,black,vertices=24)
    box('restroom cutaway right nib',2.86,3.08,2.94,4.4,0,30,plaster)
    # Existing ticket wall is preserved; its room-side wainscot remains low.
    box('closet divider cutaway',.02,8.35,2.88,8.44,0,35,teal)
    box('closet dead corner floor',.02,8.44,2.88,8.9,.3,.7,black)
    b.layer('front_solid_wall')
    box('solid street wall',0,8.90,3,9.05,0,155,brick,.016)
    box('solid street wall coping',-.015,8.88,3.015,9.07,155,159,plaster,.012)
    box('street wall cream inset',.10,9.051,2.90,9.059,34,112,plaster,.005)
    for u in [.25,2.60]:box('high glass block inset',u,9.060,u+.25,9.07,126,146,b.M['P9 lightly tinted display glass'],.003)
    b.layer('restroom')
    b.area('P10 restroom soft ceiling',xyz(1.5,5.5,270),100,(.66,.86,.78),3.5,target=xyz(1.5,5.5,0))
    META['restroom']={'room_uv':[0,3,2.9,8.4],'cutaway_right_wall_height_px':30,'entry':{'wall':'v','at_u':1.4,'at_v':3.0,'opening_u':[.95,1.85],'height_px':105,'draft_pose':'open inward'},'occupancy_light':{'u':2.055,'v':3.12,'z_px':99,'states':['green VACANT','red OCCUPIED'],'draft_state':'green VACANT'},'dead_corner_uv':[0,8.4,2.9,8.9],'front_solid_wall_uv':[0,8.9,3,9.05],'front_solid_wall_height_px':159}
    META['walkable_spots']['stalls']=[[1.50,v] for v in centers]
    META['walkable_spots']['sinks']=[[2.12,4.10],[2.63,4.10]]
    META['walkable_spots']['dryer']=[[.55,3.55]]
    META['walkable_spots']['restroom_aisle']=[1.2,3.95,2.28,7.50]
    META['routes']={'gate_to_junction':[[3.7,3.7],[1.4,1.4]],'junction_to_restroom':[[1.4,1.4],[1.4,2.6],[1.4,3.45],[1.60,3.8],[1.6,7.40]],'junction_to_screens':[[1.4,1.4],[4.8,1.4],[8.2,1.4],[11.2,1.4]],'dryer_branch':[[1.4,3.45],[.55,3.55]],'sink_branch':[[1.6,4.1],[2.12,4.1],[2.63,4.1]]}
    footprint('Restroom',[0,3,2.9,8.4],155,'room')
    footprint('New street wall',[0,8.9,3,9.05],159)
    status('Cut-away restroom with four stalls, two mirrored sinks, dryer, bin/mop sink, new junction door/occupancy plaque and full-height street wall modelled')

def ticket_queue():
    b.layer('ticket_ropes')
    runs=[([5.2,6.55,7.9,9.2],7.8),([5.9,7.0,8.1,9.2],7.0)]
    for us,v in runs:
        for u in us:
            b.cylinder('P10 queue weighted base',xyz(u,v,1.6),.105,3/ZPP,metal,vertices=24)
            b.cylinder('P10 queue brass post',xyz(u,v,22),.019,41/ZPP,brass,vertices=16)
            b.ball('P10 queue post finial',xyz(u,v,44),.045,brass)
        for a,c in zip(us[:-1],us[1:]):
            pts=[(a+(c-a)*t,v,42-7*math.sin(math.pi*t)) for t in np.linspace(0,1,20)]
            line('red velvet rope',pts,red,.026)
        footprint('Front queue rope' if v==7.8 else 'Back queue rope',[us[0]-.105,v-.105,us[-1]+.105,v+.105],48)
    META['ticket_queue']={'window_points':[[4.85,7.4],[4.85,6.0]],'queue_slots':[[round(4.85+.62*i,2),7.4] for i in range(7)],'front_rope_v':7.8,'front_posts_u':runs[0][0],'back_rope_v':7.0,'back_posts_u':runs[1][0],'open_end_uv':[9.3,7.4],'window_2_gap_u':[4.4,5.79],'lane_uv':[4.85,7.10,9.30,7.70]}
    status('Brass stanchions and red velvet queue ropes added at v7.0/7.8 with seven slots and open window-2/far-end approaches')

def snacks():
    b.layer('snack')
    for i,u in enumerate([6.6,8.2,9.8],1):
        box('register %d cash drawer'%i,u-.21,4.13,u+.21,4.47,44,50,metal)
        box('register %d keypad case'%i,u-.19,4.20,u+.19,4.44,50,55,ivory,.009)
        for a in range(5):
            for c in range(4):box('register key',u-.15+a*.06,4.23+c*.042,u-.107+a*.06,4.26+c*.042,55,56,black,.002)
        box('register display neck',u-.10,4.16,u+.10,4.22,52,63,metal,.008)
        box('register amber customer display',u-.15,4.224,u+.15,4.24,61,66,black,.005)
        text('register digits','0.00',u,4.245,63.5,.064,amber)
    # Stock and tools sit on the existing 44px worktop, never on customer floor.
    for u in [7.18,7.38]:
        for j in range(6):b.cylinder('P10 nested drinks cups',xyz(u,4.22,47+j*2),.058,.075,ivory,vertices=16)
        for j in range(2):line('cup stripe',[(u-.055,4.279,49+j*5),(u+.055,4.279,49+j*5)],red,.009)
    for j in range(5):
        b.cylinder('P10 popcorn tub stack',xyz(10.35,4.23,47+j*3),.11,.10,ivory,vertices=20)
        b.cylinder('P10 popcorn tub red band',xyz(10.35,4.23,49+j*3),.111,.018,red,vertices=20)
    box('chrome napkin dispenser',5.79,4.19,6.02,4.40,44,58,metal,.02)
    box('white folded napkins',5.81,4.401,5.99,4.414,50,56,ivory,.002)
    b.cylinder('P10 straw holder',xyz(6.15,4.25,49),.067,10/ZPP,metal)
    for j in range(11):
        u=6.15+RNG.uniform(-.04,.04);v=4.25+RNG.uniform(-.04,.04)
        line('paper straw',[(u,v,47),(u,v,63+RNG.random()*3)],ivory if j%2 else red,.006)
    # A glass tip jar, with coins visible through the body.
    tipglass=b.glass('P10 tip jar glass',(.25,.55,.52),.24)
    b.cylinder('P10 tip jar',xyz(8.65,4.35,50),.08,12/ZPP,tipglass,vertices=24)
    for j in range(8):b.cylinder('P10 tip coin',xyz(8.65+RNG.uniform(-.045,.045),4.35+RNG.uniform(-.04,.04),44.5+j*.45),.022,.004,brass,vertices=12)
    text('tip jar label','TIPS',8.65,4.432,50,.045,ivory)
    # Small countertop candy cabinet in addition to the existing front display.
    box('candy counter case base',10.84,4.08,11.45,4.51,44,46,metal)
    box('candy counter case glass',10.86,4.49,11.43,4.50,46,67,b.M['glass'],.002)
    box('candy case lid',10.84,4.08,11.45,4.51,66,68,metal,.007)
    for z in [47,56]:
        box('counter candy shelf',10.87,4.1,11.42,4.47,z,z+.7,brass,.002)
        for j in range(6):box('counter candy packet',10.88+j*.087,4.31,10.95+j*.087,4.45,z+1,z+6,b.M[['confetti pink','confetti gold','confetti cyan'][j%3]],.006)
    b.layer('partition_right')
    box('nacho cheese pump reservoir',7.76,3.18,7.96,3.41,34,58,brass,.02)
    box('nacho cheese pump lid',7.75,3.17,7.97,3.42,58,60,metal,.007)
    line('cheese pump spout',[(7.85,3.28,60),(7.85,3.28,70),(7.85,3.49,70),(7.85,3.49,65)],metal,.013)
    text('cheese label','CHEESE',7.86,3.425,48,.035,black)
    META['snack_additions']={'registers_uv':[[6.6,4.3],[8.2,4.3],[9.8,4.3]],'customer_spots':[[6.6,5.05],[8.2,5.05],[9.8,5.05]],'counter_footprint':[5.6,4,11.6,4.6],'back_bar_pump_uv':[7.86,3.3],'all_new_equipment_v_max':4.51}
    status('Three lit registers, cups/tubs, napkins/straws, glass candy case, tip jar and cheese pump added on the existing counters')

def standee(n,u,v,title,sub,accent):
    b.layer('corridor_dressing')
    box(n+' weighted foot',u-.24,v-.07,u+.24,v+.09,0,3,metal)
    # Original die-cut robot/helmet silhouette; every face follows the v plane.
    p=[(-.19,3),(-.19,42),(-.12,44),(-.17,65),(-.10,82),(.11,86),(.19,73),(.16,56),(.10,45),(.21,39),(.21,3)]
    b.mesh('P10 '+n+' cardboard',[xyz(u+x,v,z) for x,z in p],[tuple(range(len(p)))],accent)
    box(n+' helmet visor',u-.115,v+.002,u+.125,v+.01,63,72,black,.01)
    line(n+' bright collar',[(u-.14,v+.015,48),(u+.13,v+.015,48)],ivory,.012)
    text(n+' title',title,u,v+.018,20,.064,ivory)
    text(n+' subtitle',sub,u,v+.018,12,.035,ivory)
    footprint(n,[u-.24,v-.07,u+.24,v+.09],86,'corridor_prop')

def corridor():
    b.layer('corridor_dressing')
    runner=mat('faded burgundy corridor runner',(.15,.028,.055),.99,texture=135)
    box('corridor carpet runner',3,.87,12.94,2.03,.14,.19,runner,0)
    for v in [.93,1.97]:line('runner brass weave',[(3.05,v,.22),(12.90,v,.22)],brass,.005)
    standee('Crescent Nine standee',3.60,.29,'CRESCENT 9','A LUNAR MYSTERY',teal)
    standee('The Last Train standee',7.18,.28,'LAST TRAIN','NO STOPS AFTER MIDNIGHT',red)
    b.layer('corridor_dressing')
    box('coming soon housing',6.45,.02,7.50,.10,117,146,metal)
    box('coming soon lightbox',6.48,.101,7.47,.112,120,143,ivory,.004)
    text('coming soon heading','COMING SOON',6.975,.116,135,.108,black)
    text('coming soon subline','CRESCENT 9  /  LAST TRAIN',6.975,.116,125,.052,black)
    for u in [8.9,10.1]:
        for v in [2.51,2.75]:box('corridor bench foot',u-.025,v-.025,u+.025,v+.025,0,22,metal,.007)
    box('corridor bench velvet seat',8.80,2.43,10.22,2.83,20,28,teal,.045)
    box('corridor bench backrest',8.80,2.78,10.22,2.87,27,48,teal,.025)
    footprint('Corridor bench',[8.8,2.43,10.22,2.87],48,'corridor_prop')
    box('drinking fountain wall body',6.91,2.61,7.36,2.86,12,43,metal,.02)
    box('drinking fountain basin',6.91,2.48,7.36,2.86,40,45,porcelain,.025)
    line('fountain bubbler',[(7.28,2.70,45),(7.28,2.70,49),(7.20,2.70,49)],brass,.012)
    footprint('Drinking fountain',[6.91,2.48,7.36,2.86],49,'corridor_prop')
    b.cylinder('P10 corridor trash can',xyz(12.68,2.65,18),.17,35/ZPP,metal,vertices=24)
    b.cylinder('P10 corridor trash opening',xyz(12.68,2.65,35.8),.143,.012,black,vertices=24)
    footprint('Corridor trash',[12.51,2.48,12.85,2.82],36,'corridor_prop')
    b.cylinder('P10 fire extinguisher',xyz(10.33,.17,35),.065,27/ZPP,red,vertices=20)
    line('extinguisher hose',[(10.32,.17,50),(10.44,.19,47),(10.45,.2,26)],black,.010)
    box('extinguisher handle',10.27,.12,10.39,.2,49,52,metal,.005)
    box('extinguisher label',10.27,.238,10.39,.25,30,39,ivory,.001)
    footprint('Fire extinguisher',[10.26,.10,10.47,.26],52,'corridor_prop')
    box('exit sign case',12.36,.02,12.93,.10,122,139,metal,.006)
    text('exit sign text','EXIT >',12.64,.115,130,.125,green)
    for i,u in enumerate([4.8,8.2,11.2],1):
        text('screen number '+str(i),str(i),u,.13,112,.11,ivory)
    # Actual black folded curtains inside the hollow halls, beyond the leaves.
    b.layer('background')
    for i,u in enumerate([4.8,8.2,11.2],1):
        for o in list(bpy.context.scene.objects):
            if o.name.startswith('Pass6 interior'):
                a,v,c,w,z,h=bounds(o)
                if a>=u-.6 and c<=u+.6 and w<0:
                    if 'aisle light' in o.name:rm(o)
                    elif o.type=='MESH':o.data.materials.clear();o.data.materials.append(black)
        for j in range(19):
            uu=u-.47+j*.052;vv=-.60+.028*math.cos(j*math.pi)
            box('screen %d black velvet curtain fold'%i,uu,vv-.035,uu+.055,vv,1,108,black,.012)
        for side in [-1,1]:line('screen low amber aisle cue',[(u+side*.42,-.58,5),(u+side*.42,-.58,13)],amber,.005)
    # Single demonstration pose in this still, not an animation or sprite export.
    for o in bpy.context.scene.objects:
        if o.get('door_id')=='2':
            side=o['door_side'];pivot=xyz(8.2+side*.465,.028,0)
            o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(-72*side),4,'Z')@Matrix.Translation(-pivot)@o.matrix_world
    META['corridor']={'walk_band_uv':[3,.9,13,2.0],'prop_strips_v':[[0,.5],[2.4,3]],'door_approaches':[s['approach_uv'] for s in META['screens']],'draft_open_screen':2,'vestibules':'real hollow shell with black velvet folds; no brick behind openings'}
    status('Corridor furnished outside the walking band; three real dark curtain vestibules modelled and screen 2 posed open for review')

def storefront():
    ma=bpy.data.materials['P9 lightly tinted display glass'].copy();ma.name='P10 visible reflective storefront'
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.10,.27,.29,1);p.inputs['Metallic'].default_value=.58;p.inputs['Roughness'].default_value=.15
    p.inputs['Coat Weight'].default_value=.35;p.inputs['Coat Roughness'].default_value=.11
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4;noise.inputs['Detail'].default_value=3
    tex=n.new('ShaderNodeTexCoord');l.new(tex.outputs['Generated'],noise.inputs['Vector'])
    alpha=n.new('ShaderNodeMapRange');alpha.inputs['From Min'].default_value=.2;alpha.inputs['From Max'].default_value=.8
    alpha.inputs['To Min'].default_value=.20;alpha.inputs['To Max'].default_value=.34;l.new(noise.outputs['Fac'],alpha.inputs['Value'])
    mix=next(q for q in n if q.type=='MIX_SHADER');l.new(alpha.outputs[0],mix.inputs[0])
    for o in bpy.context.scene.objects:
        if o.name.startswith('P9 clear tinted storefront'):o.data.materials.clear();o.data.materials.append(ma)
    grime=b.glass('P10 pane residue',(.11,.19,.18),.12)
    glint=b.glass('P10 reflected lamp edge',(.47,.66,.62),.24)
    for group,a,c in [('glass_left',3,8.4),('glass_right',10.6,13)]:
        b.layer(group)
        count=math.ceil((c-a)/1.05)
        for j in range(count):
            lo=a+(c-a)*j/count;hi=a+(c-a)*(j+1)/count
            # Film buildup at edges and thin, irregular rain runs on the actual pane.
            box('window edge residue',lo+.018,9.012,lo+.045,9.016,8,117,grime,0)
            box('window lower grime band',lo+.02,9.012,hi-.02,9.016,7,11,grime,0)
            line('glass edge light',[(hi-.038,9.018,12),(hi-.038,9.018,114)],glint,.007)
            for k in range(4):
                u=RNG.uniform(lo+.08,hi-.08);z=RNG.uniform(55,115)
                line('glass water trace',[(u,9.018,z),(u+.012,9.018,z-8),(u+.008,9.018,z-24)],glint,.003)
    META['storefront']={'plane_v':9,'glass_left_u':[3,8.4],'glass_right_u':[10.6,13],'height_px':[5,145],'material_mix_range':[.20,.34],'changes':['reflective tinted film','edge glints','irregular grime','rain traces'],'entrance_open_u':[8.4,10.6]}
    status('Full-height panes given visible reflective tint, edge light, grime and static rain traces while preserving interior visibility')

def draft_refinements(sc):
    # Open, recessed ceramic basins instead of solid oval placeholders.
    for o in list(sc.objects):
        if o.name.startswith(('P10 sink 1 ceramic','P10 sink 2 ceramic','P10 sink 1 basin','P10 sink 2 basin','P10 toilet bowl','P10 toilet seat opening')):rm(o)
    def basin(n,u,v,z,rx,ry,depth):
        verts=[];faces=[];count=40
        for sx,zz in [(.65,z-depth),(.99,z-1),(1,z),(.72,z+.1),(.46,z-depth*.65)]:
            verts += [xyz(u+rx*sx*math.cos(t),v+ry*sx*math.sin(t),zz) for t in np.linspace(0,math.tau,count,endpoint=False)]
        for ring in range(4):
            for k in range(count):faces.append((ring*count+k,ring*count+(k+1)%count,(ring+1)*count+(k+1)%count,(ring+1)*count+k))
        faces.append(tuple(range(4*count,5*count)))
        o=b.mesh('P10 '+n,verts,faces,porcelain)
        for p in o.data.polygons:p.use_smooth=True
        b.ball('P10 '+n+' drain',xyz(u,v,z-depth*.65+.25),1,metal,(rx*.15,ry*.15,.002))
    b.layer('restroom')
    for u in [2.12,2.63]:basin('recessed sink',u,3.39,45,.205,.25,8)
    for v in [4.4,5.4,6.4,7.4]:basin('open toilet bowl',.53,v,31,.19,.26,12)
    # The retired tall tower had hidden the feet of the far skyline. Extend
    # those existing masses down and add a low service block behind the halls.
    b.layer('background')
    for o in list(sc.objects):
        if o.name.startswith('P8 distant solid city block'):
            a,v,c,w,z,h=bounds(o)
            if a>=-1.2:box('distant building foundation',a,v,c,w,-280,-19.98,o.data.materials[0],0)
    distant=bpy.data.materials['P8B distant rain brick']
    for a,c,h in [(3.15,6.3,104),(6.3,9.6,132),(9.6,13,111)]:
        box('low rear service block',a,-8.0,c,-4.55,-230,h,distant,.012)
        box('low rear service roof',a,-8.0,c,-4.55,h,h+3,roof,.006)
    # Keep bathroom alternate state editable without generating any sheets.
    light=bpy.data.objects['P10 green vacant light'];light['alternate_text']='OCCUPIED';light['alternate_color']=[1,.035,.025]
    # Subtle optical bloom from exposed physical tube cores, in the still only.
    tree=bpy.data.node_groups.new('P10 draft optical neon bloom','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    source=tree.nodes.new('CompositorNodeRLayers');source.scene=sc
    glow=tree.nodes.new('CompositorNodeGlare')
    glow.inputs['Type'].default_value='Fog Glow';glow.inputs['Quality'].default_value='High'
    glow.inputs['Threshold'].default_value=1.5;glow.inputs['Strength'].default_value=.20;glow.inputs['Size'].default_value=.20
    dest=tree.nodes.new('NodeGroupOutput');tree.links.new(source.outputs['Image'],glow.inputs['Image']);tree.links.new(glow.outputs['Image'],dest.inputs['Image'])
    sc.compositing_node_group=tree
    status('First-still review refinements: recessed porcelain basins, exposed luminous tube cores with subtle bloom, and grounded distant skyline')

def check(sc,camera):
    bpy.context.view_layer.update()
    bad=[]
    def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-5 and min(a[3],b[3])-max(a[1],b[1])>1e-5
    zones=[META['corridor']['walk_band_uv']]+META['corridor']['door_approaches']
    for e in META['footprints']:
        if e['kind']=='corridor_prop':
            for z in zones:
                if overlap(e['uv'],z):bad.append([e['name'],z])
    assert not bad,bad
    # Test all restroom branches against the modeled fixtures and inward leaf.
    obstacles=[e['uv'] for e in META['footprints'] if e['name'].startswith(('Stall ','Sink ','Hand dryer'))]
    obstacles += [[0,2.94,.95,3.08],[1.85,2.94,2.9,3.08],[1.80,3.08,1.84,3.90],[2.86,3.08,2.94,4.4]]
    route_hits=[];radius=.12
    routes=[META['routes'][k] for k in ['junction_to_restroom','dryer_branch','sink_branch']]
    routes += [[[1.6,v],[u,v]] for u,v in META['walkable_spots']['stalls']]
    for path in routes:
        for a,c in zip(path[:-1],path[1:]):
            for t in np.linspace(0,1,101):
                u=a[0]*(1-t)+c[0]*t;v=a[1]*(1-t)+c[1]*t
                for r in obstacles:
                    if r[0]-radius<u<r[2]+radius and r[1]-radius<v<r[3]+radius:route_hits.append([u,v,r])
    assert not route_hits,route_hits[:3]
    ids=sorted({o.get('door_id') for o in sc.objects if o.get('door_id')})
    assert ids==['1','2','3'],ids
    facing=[o.name for o in sc.objects if o.type=='FONT' and abs((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(NORMAL))>.999]
    assert not facing,facing
    assert list(sc.camera.matrix_world)==camera
    META['draft_checks']={'camera_unchanged':True,'screen_ids':ids,'corridor_prop_overlap_count':len(bad),'restroom_route_hits_at_0_12_tile_radius':len(route_hits),'screen_facing_text_count':len(facing),'production_occlusion_and_animation_validation':'deferred to approved final pass; no pack or loops produced'}
    (QA/'layout3_draft_coordinates.json').write_text(json.dumps(META,indent=2))
    status('Draft geometry checks passed: unchanged camera, exactly three screen IDs, clear corridor/door approach footprints, no screen-facing text')

def main():
    start=time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass9.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.M.clear();b.META.clear()
    for m in bpy.data.materials:b.M[m.name]=m
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:
            b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
            o.visible_camera=True;o.hide_render=False;o.is_holdout=False
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    bpy.context.view_layer.update();camera=list(sc.camera.matrix_world)
    strip_old(sc);materials();auditoriums();branding();bathroom();ticket_queue();snacks();corridor();storefront();draft_refinements(sc);check(sc,camera)
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.cycles.adaptive_threshold=.05
    sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=16
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.film_transparent=False
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    sc.render.use_compositing=True
    sc['draft_only']=True;sc['layout']=3;sc['draft_brief']='BRIEF-12-pass10-draft.md'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
    status('Editable draft scene saved as roxy_pass10_draft.blend; 24-sample denoised Cycles still configured at 1920x1080')
    t=time.perf_counter();render(QA/'draft_1.png')
    timing={'render_seconds':round(time.perf_counter()-t,3),'total_build_and_render_seconds':round(time.perf_counter()-start,3),'resolution':[1920,1080],'samples':24,'loops_rendered':0,'sprites_rendered':0,'slices_rendered':0,'renders_2x':0}
    (QA/'draft_render_timing.json').write_text(json.dumps(timing,indent=2))
    status('Quick full-frame lit draft_1.png rendered in %.1f seconds; no production renders started'%timing['render_seconds'])

if __name__=='__main__':main()
