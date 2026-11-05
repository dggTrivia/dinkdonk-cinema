"""Pass 9: real wall signs, storefront, bent-tube branding and street context."""
import sys,json,math,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Matrix,Vector
import build_scene as b
import build_pass8 as city
from common import xyz,project,ZPP,render,NORMAL
from pass8_common import gpu
from pass9_common import ROOT,QA,OUT,LIVE,status
UFACE=Matrix(((0,1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
CHANGED=['glass_left','glass_right','entrance_post_1','entrance_post_2','bus_stop','roxy_blade','arcade','paste_wall']
META={'led_signs':[],'poster_frames':[],'poster_bulbs':[],'ad_surfaces':[],'changed_groups':CHANGED,'removed':[]}
def text(n,s,wall,t,z,size,ma,front=.08):return b.text(n,s,b.wp(wall,t,z,front),size,ma,UFACE if wall=='u' else b.FRONT_FACE)
def mat(n,c,r=.5,e=0):return b.material('P9 '+n,c,r,emit=e)
def rm(o):
    META['removed'].append(o.name)
    for a in b.GROUPS.values():
        if o in a:a.remove(o)
    bpy.data.objects.remove(o,do_unlink=True)
def quad(wall,a,c,z0,z1,front):
    ts=[c,a] if wall=='u' else [a,c]
    return [project(*((front,t,z) if wall=='u' else (t,front,z))) for t,z in [(ts[0],z1),(ts[1],z1),(ts[1],z0),(ts[0],z0)]]
def frame(n,wall,a,c,z0,z1,front,ma,width=.035):
    for aa,cc in [(a-width,a),(c,c+width)]:b.wallbox(n,wall,aa,cc,z0-2,z1+2,ma,front,.05,.006)
    for zz in [z0-2,z1]:b.wallbox(n,wall,a,c,zz,zz+2,ma,front,.05,.006)
def ad(n,wall,a,c,z0,z1,front,lit,zidx,group=None):
    b.layer(group or 'background')
    b.wallbox('P9 ad blank '+n,wall,a,c,z0,z1,paperlit if lit else paper,front,.035,.004)
    b.layer('ad_'+n)
    frame('P9 ad frame '+n,wall,a,c,z0,z1,front+.026,metal,.05)
    # Fine rails/glass glints are a separate transparent overlay above page art.
    b.wall_line('P9 ad glass glint '+n,wall,[(a+.025,z1-1),(c-.025,z1-1)],glint,.006,front+.035)
    b.wallbox('P9 ad glass '+n,wall,a,c,z0,z1,adglass,front+.030,.002,0)
    META['ad_surfaces'].append({'name':n,'quad_px':quad(wall,a,c,z0,z1,front),'z_index':zidx,'lit':lit,'aspect':(c-a)*ZPP/(z1-z0),'layer':'ad_'+n,'wall':wall+'0','along':[a,c],'z_px':[z0,z1],'offset':front})
    b.layer(group or 'background')
def dots(wall,at):
    verts=[];faces=[];cols=108;pitch=1.0;span=cols*pitch/ZPP;a=at-span/2;c=at+span/2
    for top in [143,132]:
        for row in range(7):
            for col in range(cols):
                t=a+(col+.5)*pitch/ZPP;z=top-(row+.5)*pitch
                k=len(verts)
                for j in range(8):
                    th=j*math.tau/8;verts.append(b.wp(wall,t+math.cos(th)*.24/ZPP,z+math.sin(th)*.24,.078))
                faces.append(tuple(range(k,k+8)))
    b.mesh('P9 unlit LED dot field',verts,faces,darkdot)
    return a,c
def storefront():
    for group,a,c in [('glass_left',3,8.4),('glass_right',10.6,13)]:
        b.layer(group,[a,8.95,c,9.05],151)
        b.box('P9 storefront wet sill',a,8.95,c,9.05,0,5,metal,.006)
        b.box('P9 clear tinted storefront',a,8.995,c,9.005,5,145,glass,.001)
        b.box('P9 storefront header',a,8.95,c,9.05,141,151,metal,.006)
        b.box('P9 storefront transom',a,8.98,c,9.02,118,121,metal,.004)
        count=math.ceil((c-a)/1.05)
        for j in range(count+1):
            u=a+(c-a)*j/count
            b.box('P9 full height mullion',max(a,u-.016),8.97,min(c,u+.016),9.03,4,144,metal,.003)
        for j in range(count):
            u=a+(c-a)*(j+.5)/count
            b.wall_line('P9 glass safety etch','v',[(u-.06,53),(u+.06,53)],etched,.006,9.018)
        if group=='glass_left':
            b.wallbox('P9 small window one-sheet','v',3.15,3.49,67,104,paper,9.022,.002,0)
            text('P9 window print title','MIDNIGHT','v',3.32,97,.043,ink,9.026)
            b.wallbox('P9 window print image','v',3.18,3.46,75,92,blue,9.026,.001,0)
            text('P9 opening hours','OPEN 12 - LATE','v',6.8,91,.055,etched,9.024)
            text('P9 no smoking','NO SMOKING','v',6.8,82,.051,etched,9.024)
        else:text('P9 window sticker','d.gg','v',12.72,104,.11,mint,9.024)
    for i,u in enumerate([8.4,10.6],1):
        b.layer('entrance_post_'+str(i),[u-.07,8.93,u+.07,9.07],151)
        b.box('P9 entrance jamb',u-.045,8.95,u+.045,9.05,0,151,metal,.009)
        b.box('P9 entrance jamb lamp',u-.025,9.052,u+.025,9.062,12,138,cyan,.003)
    # Open doorway: overhead member has its own depth-sliced parent, no leaf across the route.
    b.layer('entrance_header',[8.4,8.95,10.6,9.05],151)
    b.box('P9 open entrance overhead',8.4,8.95,10.6,9.05,141,151,metal,.006)
    text('P9 entrance legend','d.gg  /  CINEMA','v',9.5,146,.075,etched,9.058)

def signs():
    b.layer('background')
    for i,(wall,at,a) in enumerate([('u',6.4,4.85),('u',4,2.35),('v',4.8,5.55),('v',8.2,8.95),('v',11.2,11.95)],1):
        lo,hi=at-.79,at+.79
        b.wallbox('P9 LED cast housing '+str(i),wall,lo,hi,119,149,metal,.055,.12,.014)
        b.wallbox('P9 LED recessed face '+str(i),wall,lo+.035,hi-.035,121,147,ink,.072,.008,.004)
        aa,cc=dots(wall,at)
        META['led_signs'].append({'door':i,'wall':wall+'0','along':[aa,cc],'z_px':[122,145],'offset':.078,'cols':108,'rows_px':[[143,136],[132,125]],'dot_pitch_px':1,'glyph_rows':7,'characters_at_6_columns':18,'quad_px':quad(wall,aa,cc,122,145,.078),'z_index':901})
        width=.81;z0=20;z1=z0+width*40/27*ZPP;c=a+width
        b.wallbox('P9 one-sheet aperture '+str(i),wall,a,c,z0,z1,paper,.072,.004,0)
        frame('P9 one-sheet frame '+str(i),wall,a,c,z0,z1,.11,metal,.055)
        pts=[]
        for t in np.linspace(a-.033,c+.033,13):pts.append((float(t),z1+3))
        for z in np.linspace(z1+3,z0-3,17)[1:]:pts.append((c+.033,float(z)))
        for t in np.linspace(c+.033,a-.033,13)[1:]:pts.append((float(t),z0-3))
        for z in np.linspace(z0-3,z1+3,17)[1:-1]:pts.append((a-.033,float(z)))
        for t,z in pts:b.ball('P9 poster bulb socket',b.wp(wall,t,z,.128),.010,bulbdim)
        META['poster_frames'].append({'screen':i,'wall':wall+'0','along':[a,c],'z_px':[z0,z1],'offset':.072,'aspect':27/40,'quad_px':quad(wall,a,c,z0,z1,.072)})
        META['poster_bulbs'].append({'door':i,'points_px':[project(*((.14,t,z) if wall=='u' else (t,.14,z))) for t,z in pts],'z_index':902})
    # Remove two old sconces now occupied by correctly proportioned poster frames.
    for o in list(bpy.context.scene.objects):
        if o.name.startswith(('Sconce mounting','Opal sconce','Wall sconce pool')):
            p=o.location;t=-p.y if p.x<.4 else p.x
            if (p.x<.4 and abs(t-2.4)<.15) or (abs(p.y)<.4 and abs(t-12.7)<.15):rm(o)
    b.wallbox('P9 restroom enamel plaque','u',7.93,8.67,113,130,metal,.055,.07,.008)
    text('P9 restroom wall lettering','RESTROOM','u',8.3,121,.10,etched,.092)
    b.wallbox('P9 occupancy indicator housing','u',7.45,7.80,64,78,metal,.07,.06,.006)
    META['wc_indicator_plane']={'wall':'u','along':[7.47,7.78],'z_px':[66,76],'front':.108,'z_index':901}
    # Suspended double-faced directions follow the two actual wall axes.
    for wall,t,f,label in [('u',2.68,3.17,'1 - 2  <'),('v',3.87,3.17,'>  3 - 5')]:
        b.wallbox('P9 hanging wayfinding housing',wall,t-.53,t+.53,169,190,metal,f,.09,.012)
        text('P9 hanging wayfinding text',label,wall,t,179,.16,etched,f+.025)
        text('P9 hanging wayfinding caption','SCREENS',wall,t,186,.055,cyan,f+.025)
        for q in [t-.4,t+.4]:b.wall_line('P9 suspension rod',wall,[(q,190),(q,215)],metal,.007,f-.04)
    b.layer('bus_stop')
    b.wallbox('P9 bus route blade','v',.58,1.82,86,102,metal,9.57,.055,.008)
    text('P9 bus route lettering','95  /  d.gg','v',1.20,94,.15,paperlit,9.605)
    # Shelter panel behind the front posts, with an independent overlay crop.
    ad('shelter','v',.54,1.12,9,72,9.445,True,2024,'bus_stop')
    b.layer('arcade')
    text('P9 arcade cabinet header','ORBIT','v',12.4,77,.12,etched,8.31)

def neon():
    b.layer('roxy_blade')
    b.box('P9 d.gg blade backer',-.75,9.10,-.05,9.30,110,300,metal,.025)
    for z in [125,280]:b.line('P9 blade mounting bracket',[xyz(-.09,8.72,z),xyz(-.09,9.18,z)],metal,.027)
    outline=[(-.71,114),(-.71,296),(-.09,296),(-.09,114),(-.71,114)]
    b.line('P9 blade outline glass',[xyz(u,9.33,z) for u,z in outline],bluebody,.018)
    b.line('P9 blade outline core',[xyz(u,9.345,z) for u,z in outline],blue,.006)
    allpaths=[]
    def tube(label,pts,color,body):
        b.line('P9 neon glass '+label,[xyz(u,9.34,z) for u,z in pts],body,.023)
        b.line('P9 neon core '+label,[xyz(u,9.356,z) for u,z in pts],color,.009)
        for u,z in [pts[0],pts[-1]]:b.ball('P9 rounded tube end',xyz(u,9.356,z),.009,color)
        for u,z in pts[::max(1,len(pts)//3)]:b.cylinder('P9 neon stand-off',xyz(u,9.323,z),.012,.035,metal,(0,-1,0),12)
        allpaths.append({'name':label,'points_px':[project(u,9.356,z) for u,z in pts]})
    circle=lambda z:[(-.42+.18*math.cos(t),z+14*math.sin(t)) for t in np.linspace(0,math.tau,41)]
    tube('lowercase d bowl',circle(267),blue,bluebody);tube('lowercase d ascender',[(-.24,253),(-.24,291)],blue,bluebody)
    tube('decimal dot',[(-.43+.025*math.cos(t),238+2*math.sin(t)) for t in np.linspace(0,math.tau,21)],pink,pinkbody)
    for z in [212,161]:
        tube('lowercase g bowl',circle(z),mint,mintbody)
        tube('lowercase g descender',[(-.24,z+13),(-.24,z-17),(-.27,z-23),(-.35,z-26),(-.49,z-26),(-.57,z-22)],mint,mintbody)
    b.point('P9 blue neon wall spill',xyz(-.25,9.55,264),24,(.12,.50,1),.45)
    b.point('P9 mint neon sidewalk spill',xyz(-.25,9.60,165),24,(.05,1,.56),.45)
    META['neon_paths']=allpaths

def surroundings():
    b.layer('background');before=set(bpy.context.scene.objects)
    brick=bpy.data.materials['P8 brick'];roofma=bpy.data.materials.get('P8 dark weathered annex felt') or metal
    b.box('P9 west infill block',-9.5,.0,-6.1,6.68,-5,187,brick,.02)
    b.box('P9 west infill roof',-9.55,-.05,-6.05,6.72,187,191,metal,.01)
    b.box('P9 west shop fascia',-9.35,6.70,-6.25,6.79,46,63,metal,.01)
    text('P9 west shop sign','DIAL-UP  /  REPAIR','v',-7.8,55,.16,etched,6.81)
    for u in [-8.9,-7.9,-6.9]:
        b.wallbox('P9 west shop window','v',u-.34,u+.34,6,42,window,6.70,.05,.004)
        for z in [87,137]:
            b.wallbox('P9 west upstairs window frame','v',u-.30,u+.30,z-2,z+32,metal,6.72,.07,.01)
            b.wallbox('P9 west upstairs window','v',u-.25,u+.25,z,z+28,window,6.76,.01,.005)
    b.box('P9 alley inset utility door',-5.98,6.7,-5.32,6.77,0,65,metal,.01)
    b.line('P9 alley overhead cable',[xyz(-6.1,8.5,130),xyz(-5.6,8.4,122),xyz(-5.0,8.5,130)],metal,.008)
    b.point('P9 west shop warm pool',xyz(-7.6,6.9,48),12,(1,.64,.32),.38)
    receivers=bpy.data.collections.new('P9 west fill receivers');bpy.context.scene.collection.children.link(receivers)
    for o in bpy.context.scene.objects:
        if o.name.startswith('P9 west') or (o.name.startswith(('P8 gravel roof','P8 roof felt patch')) and o.location.x<0):receivers.objects.link(o)
    fill=b.area('P9 west facade and roof fill',xyz(-5,10,400),650,(.43,.50,.69),9,target=xyz(-5,4,170));fill.light_linking.receiver_collection=receivers
    # Continue the records shop to the street line; the alley remains the gap at u13..15.
    b.box('P9 records frontage extension',15,6.45,17.5,9.10,-4,58,brick,.015)
    b.box('P9 records continuous roof',15,6.45,17.5,9.10,58,61,metal,.008)
    b.wallbox('P9 records shop fascia','v',15.15,17.35,42,57,metal,9.13,.05,.006)
    text('P9 records shop lettering','RECORDS & REPAIR','v',16.25,49,.12,etched,9.17)
    for u in [15.65,16.65]:
        b.wallbox('P9 records display frame','v',u-.36,u+.36,6,39,metal,9.13,.06,.006)
        b.wallbox('P9 records display glass','v',u-.31,u+.31,9,36,window,9.17,.01,.002)
        for j in range(5):b.wallbox('P9 record sleeves','v',u-.27+j*.11,u-.18+j*.11,13,24,paper,9.19,.004,0)
    b.point('P9 records frontage light',xyz(16.25,9.20,40),7,(1,.65,.32),.35)
    # Low gutter and curb cut connect the same sidewalk level across the alley mouth.
    b.box('P9 alley curb cut',13.15,9.10,15,9.19,-.34,.10,metal,0)
    for u in np.arange(13.2,15,.13):b.box('P9 alley drainage slot',u,9.13,u+.045,9.18,.11,.14,ink,0)
    b.box('P9 alley dumpster',14.35,6.5,14.95,7.20,0,29,metal,.02)
    b.box('P9 dumpster sloping lid',14.36,6.46,14.99,7.24,29,32,green,.015)
    for u in [14.4,14.85]:b.cylinder('P9 dumpster caster',xyz(u,6.85,3),.035,.20,ink,(1,0,0))
    b.box('P9 concrete planter',14.63,8.40,14.95,8.75,0,15,metal,.015)
    for j in range(7):b.line('P9 planter leaves',[xyz(14.79,8.57,13),xyz(14.66+j*.035,8.48+(j%3)*.07,27+(j%3)*4)],green,.018)
    # Blank paste-up surface in the west alley; page owns future poster content.
    b.layer('paste_wall',[-2.50,8.84,-1.54,8.96],40)
    ad('paste_wall','v',-2.42,-1.62,5,37,8.89,False,100,'paste_wall')
    b.layer('background')
    # Real facade billboard: its content follows the commercial tower's wall.
    ad('tower','v',6.65,15.0,310,495,-.86,True,100)
    for u in [7.1,14.5]:
        b.line('P9 tower billboard brace',[xyz(u,-1.04,310),xyz(u,-.78,310),xyz(u,-.78,495),xyz(u,-1.04,495)],metal,.035)
    b.area('P9 billboard warm flood',xyz(10.8,.3,510),100,(.74,.78,1),4,target=xyz(10.8,-.86,390))
    for o in set(bpy.context.scene.objects)-before:
        if o.type in ['MESH','CURVE','FONT'] and o.get('layer') in ['background','paste_wall','ad_paste_wall','ad_tower']:o['pass9_surrounding']=True

def build():
    global metal,ink,paper,paperlit,etched,glint,glass,adglass,blue,mint,pink,bluebody,mintbody,pinkbody,cyan,bulbdim,darkdot,green,window
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass8b.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.META.clear();b.M.clear()
    for ma in bpy.data.materials:b.M[ma.name]=ma
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    for o in list(sc.objects):
        if o.get('layer') in ['glass_left','glass_right','entrance_post_1','entrance_post_2','roxy_blade'] or o.name.startswith(('Billboard ','Blank marquee','Marquee ','Poster ','Blank poster','Sun faded poster','Restroom sign','Restroom text','Usher gate hanging','Gate cyan','Gate lettering','Gate directional','Bus route enamel','Bus route text','Arcade header','Roxy neon spill','P8 billboard steel','P8 billboard angled')):rm(o)
    metal=mat('graphite enamel',(.025,.034,.045),.32);ink=mat('recess black',(.004,.006,.009),.66)
    paper=mat('blank poster stock',(.45,.43,.38),.82);paperlit=mat('backlit blank panel',(.35,.39,.40),.65,.18)
    etched=mat('ivory lettering',(.68,.78,.79),.5,.35);glint=mat('glass glint',(.17,.32,.40),.25,.2)
    glass=b.glass('P9 lightly tinted display glass',(.14,.29,.32),.07);adglass=b.glass('P9 advertising glass',(.12,.18,.22),.035)
    blue=mat('blue neon core',(.20,.62,1),.22,7);mint=mat('mint neon core',(.12,1,.60),.22,6);pink=mat('dot neon core',(1,.22,.50),.2,6)
    bluebody=mat('blue bent glass',(.025,.12,.32),.2,.5);mintbody=mat('mint bent glass',(.02,.27,.17),.2,.5);pinkbody=mat('pink bent glass',(.35,.02,.08),.2,.5)
    cyan=mat('transom running light',(.16,.56,.74),.3,2);bulbdim=mat('unlit bulb glass',(.38,.28,.12),.3,.18);darkdot=mat('unlit amber LED',(.065,.035,.012),.5,.1)
    green=mat('weathered green',(.025,.065,.05),.6);window=mat('warm shop window',(.21,.13,.055),.3,.65)
    storefront();signs();neon();surroundings()
    sc['pass9_posters_forward']=True
    # Rename invisible source labels too; retain the legacy roxy_blade layer key for compatibility.
    for o in sc.objects:
        if o.type=='FONT':assert 'ROXY' not in o.data.body.upper(),o.name
    bpy.context.view_layer.update()
    facing=[o.name for o in sc.objects if o.type=='FONT' and abs((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(NORMAL))>.999]
    assert not facing,facing
    META['no_camera_facing_text']=True
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.use_border=False;sc.render.use_compositing=False;sc.cycles.samples=64
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass9.blend'))
    (QA/'scene_metadata.json').write_text(json.dumps(META,indent=2))
    status('World model built: full-height storefront, wall LED/poster housings, physical wayfinding, d.gg glass neon, connected shopfronts and three ad surfaces')
    render(QA/'preview_1.png');status('Lit 1920x1080 preview_1.png rendered before expensive loops; no screen-facing text remains in the scene')
if __name__=='__main__':build()
