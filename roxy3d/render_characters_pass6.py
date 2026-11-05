"""Original 3D janitor and folding umbrellas, rendered with the Roxy camera."""
import sys,json,math,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector,Matrix
import build_scene as b
import render_cat_pass5 as mesh_helpers
from common import ROOT,xyz,ZPP,project,render
QA=ROOT/'qa6';ORIGIN=(10.75,7.75);M={};PARTS=[]
ANIMS={'walk_plus_u':(12,12),'walk_minus_u':(12,12),'walk_plus_v':(12,12),'walk_minus_v':(12,12),'sweep':(48,16),'idle':(48,16)}
COLORS={'red':(.43,.025,.035),'blue':(.025,.13,.43),'yellow':(.62,.38,.035),'black':(.027,.032,.039)}

def ball(n,p,s,m):
    ob=b.ball('Pass6 '+n,Vector(p),1,M[m],s);PARTS.append(ob);return ob
def tube(n,pts,r,m):
    mesh_helpers.M=M;mesh_helpers.PARTS=PARTS
    return mesh_helpers.tube(n,pts,r,m)
def limb(n,a,c,r,m):return tube(n,[a,c],[r,r*.83],m)
def clear():
    for ob in PARTS:
        data=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if data.users==0:
            if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
            elif isinstance(data,bpy.types.Curve):bpy.data.curves.remove(data)
    PARTS.clear()
def place(angle=0):
    bpy.context.view_layer.update();tr=Matrix.Translation(xyz(*ORIGIN))@Matrix.Rotation(angle,4,'Z')
    for ob in PARTS:ob.matrix_world=tr@ob.matrix_world

def broom(top,bottom):
    limb('wood broom shaft',bottom,top,.010,'wood')
    x,y,z=bottom
    ball('broom binding',(x,y,z+.032),(.035,.095,.023),'metal')
    for j in range(13):
        yy=y+(j-6)*.014
        tube('straw broom bristles',[(x,yy,z+.028),(x+.013,yy*0+ y+(j-6)*.016,z-.038)],[.006,.004],'straw')

def bucket(pos):
    x,y,z=pos
    # Open tapered pail with a separate dark water surface and curved wire handle.
    verts=[];faces=[]
    for radius,zz in [(.055,z),(.075,z+.12),(.067,z+.12),(.048,z+.015)]:
        for j in range(20):verts.append((x+radius*math.cos(j*math.tau/20),y+radius*math.sin(j*math.tau/20),zz))
    for ring in range(3):
        for j in range(20):faces.append((ring*20+j,ring*20+(j+1)%20,(ring+1)*20+(j+1)%20,(ring+1)*20+j))
    ob=b.mesh('Pass6 galvanized bucket',verts,faces,M['metal']);PARTS.append(ob)
    ball('bucket water',(x,y,z+.065),(.05,.05,.004),'water')
    pts=[(x,y+.073*math.cos(a),z+.12+.115*math.sin(a)) for a in [j*math.pi/16 for j in range(17)]]
    tube('bucket wire handle',pts,[.004]*len(pts),'dark')

def janitor(anim,i,n):
    clear();t=(i%n)/n;a=t*math.tau;walk=anim.startswith('walk')
    angle={'walk_plus_u':0,'walk_minus_u':math.pi,'walk_plus_v':-math.pi/2,'walk_minus_v':math.pi/2}.get(anim,-math.pi/2)
    bob=.008*math.cos(a*2) if walk else .003*math.sin(a)
    lean=.025*math.sin(a) if anim=='sweep' else .012
    ball('shirt torso',(lean,0,.452+bob),(.10,.125,.145),'shirt')
    ball('denim waist',(0,0,.333+bob),(.102,.123,.08),'denim')
    ball('overall bib',(.089+lean,0,.465+bob),(.022,.088,.094),'denim')
    for side in [-1,1]:
        tube('overall shoulder strap',[(.09+lean,side*.071,.46+bob),(.043+lean,side*.078,.584+bob),(-.07+lean,side*.074,.50+bob)],[.014,.014,.014],'denim')
        ball('brass overall button',(.109+lean,side*.068,.50+bob),(.005,.008,.008),'brass')
    tube('bib pocket stitching',[(.113+lean,-.043,.46+bob),(.115+lean,-.038,.422+bob),(.115+lean,.038,.422+bob),(.113+lean,.043,.46+bob)],[.002]*4,'stitch')
    ball('neck',(lean,0,.595+bob),(.040,.047,.04),'skin')
    ball('face',(lean+.012,0,.659+bob),(.067,.061,.077),'skin')
    ball('nose',(lean+.076,0,.655+bob),(.024,.017,.019),'skin')
    ball('grey moustache',(lean+.072,0,.630+bob),(.010,.029,.009),'hair')
    for side in [-1,1]:
        ball('ear',(lean+.005,side*.061,.653+bob),(.015,.013,.023),'skin')
        ball('eye',(lean+.068,side*.028,.675+bob),(.005,.007,.005),'dark')
        limb('brow',(lean+.066,side*.017,.688+bob),(lean+.062,side*.042,.686+bob),.003,'hair')
    ball('cap crown',(lean-.006,0,.718+bob),(.073,.067,.032),'denim')
    ball('cap brim',(lean+.059,0,.710+bob),(.075,.068,.008),'denim')
    ball('cap badge',(lean+.063,0,.726+bob),(.004,.018,.011),'stitch')
    for side in [-1,1]:
        phase=(t+(.5 if side<0 else 0))%1
        dx=(.12-.48*phase if phase<.5 else -.12+.48*(phase-.5)) if walk else (.025 if side<0 else -.025)
        lift=.045*math.sin((phase-.5)*math.tau) if walk and phase>=.5 else 0
        hip=(0,side*.075,.337+bob);knee=(dx*.35+.022,side*.075,.19+lift*.5);ankle=(dx,side*.075,.055+lift)
        limb('trouser thigh',hip,knee,.053,'denim');limb('trouser cuff',knee,ankle,.042,'denim')
        ball('work boot',(dx+.026,side*.075,.030+lift),(.069,.047,.030),'dark')
        ball('boot sole',(dx+.027,side*.075,.013+lift),(.070,.048,.012),'rubber')
    sway=.10*math.sin(a) if anim=='sweep' else .018*math.sin(a)
    bottom=(.29+sway,-.16,.05);top=(.11+lean,-.11,.61+bob)
    broom(top,bottom)
    # Right arm grips shaft; left hand either carries pail or checks a watch.
    right=(.16+lean,-.12,.43+bob)
    check=(.5-.5*math.cos(a))**4 if anim=='idle' else 0
    left=(.08+.10*check,.17-.14*check,.32+.18*check+bob)
    for side,hand in [(-1,right),(1,left)]:
        shoulder=(lean,side*.116,.535+bob);elbow=(.06+lean,side*.17,.424+bob)
        limb('shirt sleeve',shoulder,elbow,.040,'shirt');limb('forearm',elbow,hand,.027,'skin');ball('working hand',hand,(.029,.024,.025),'skin')
    ball('wristwatch band',(left[0]-.015,left[1]+.003,left[2]+.005),(.014,.027,.027),'dark')
    ball('watch dial',(left[0]-.012,left[1],left[2]+.029),(.015,.016,.003),'stitch')
    if walk:bucket((left[0],left[1],left[2]-.235))
    else:bucket((-.14,.23,.015))
    place(angle)

def umbrella(color,i=0):
    clear();fold=i/5;radius=.43*(1-fold)+.040*fold;rim_z=.44-.15*fold;peak=.64
    M['canopy']=M['canopy_'+color];M['panel']=M['panel_'+color]
    for k in range(8):
        verts=[];faces=[]
        for ring in range(5):
            r=radius*ring/4
            for j in range(5):
                theta=(k+j/4)*math.tau/8
                # Each fabric gore sags slightly between structural ribs.
                z=peak-(peak-rim_z)*(r/radius)**1.45-.026*math.sin(j*math.pi/4)*(r/radius)**2*(1-fold)
                verts.append((r*math.cos(theta),r*math.sin(theta),z))
        for ring in range(4):
            for j in range(4):faces.append((ring*5+j,ring*5+j+1,(ring+1)*5+j+1,(ring+1)*5+j))
        ob=b.mesh('Pass6 umbrella fabric gore',verts,faces,M['canopy' if k%2 else 'panel']);PARTS.append(ob)
        mod=ob.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=.002
        theta=k*math.tau/8
        pts=[(radius*s*math.cos(theta),radius*s*math.sin(theta),peak-(peak-rim_z)*s**1.45+.001) for s in [j/8 for j in range(9)]]
        tube('umbrella rib seam',pts,[.0025]*9,'rib')
        ball('umbrella tip',pts[-1],(.006,.006,.006),'metal')
    tube('umbrella shaft',[(0,0,-.035),(0,0,.66)],[.007,.004],'metal')
    pts=[(.026-.026*math.cos(a),0,-.015-.026*math.sin(a)) for a in [j*math.pi/12 for j in range(13)]]
    tube('curved handle grip',pts,[.008]*len(pts),'dark');ball('umbrella finial',(0,0,.669),(.009,.009,.020),'metal')
    place()

def setup():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass6.blend'));sc=bpy.context.scene
    sc.render.use_compositing=False;sc.render.film_transparent=True;sc.cycles.device='CPU';sc.cycles.samples=48
    sc.cycles.adaptive_threshold=.02;sc.cycles.max_bounces=5
    for ob in sc.objects:
        if ob.type in ['MESH','FONT','CURVE']:ob.visible_camera=False
    b.GROUP='pass6_character';b.GROUPS.clear()
    for name,col,rough,metal in [('denim',(.035,.11,.14),.88,0),('shirt',(.28,.27,.19),.95,0),('skin',(.44,.25,.14),.80,0),('hair',(.13,.12,.10),1,0),('stitch',(.50,.46,.30),.95,0),('dark',(.023,.018,.014),.8,0),('rubber',(.015,.019,.022),.9,0),('metal',(.24,.29,.31),.4,.7),('brass',(.4,.27,.08),.45,.65),('wood',(.23,.10,.035),.85,0),('straw',(.48,.33,.13),.90,0),('water',(.025,.045,.05),.15,.3),('rib',(.14,.15,.17),.55,.3)]:
        M[name]=b.material('Pass6 character '+name,col,rough,metal)
    for color,col in COLORS.items():
        M['canopy_'+color]=b.material('Umbrella '+color,col,.57)
        M['panel_'+color]=b.material('Umbrella alternate '+color,tuple(c*.78 for c in col),.62)
    return sc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--only',choices=['janitor','umbrella']);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    sc=setup();scale=4 if args.preview else 2;sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    start=time.perf_counter();meta={};x,y=project(*ORIGIN)
    from render_loop_basis import crop
    for kind in ([args.only] if args.only else ['janitor','umbrella']):
        w,h,anchor=(96,96,[48,78]) if kind=='janitor' else (88,80,[44,68]);rect=[int(x)-anchor[0],int(y)-anchor[1],w,h]
        crop(sc,dict(zip(['x','y','w','h'],rect)))
        jobs=ANIMS if kind=='janitor' else {c:(6,12) for c in COLORS}
        for name,(n,fps) in jobs.items():
            frames=[0,n//3] if args.preview else range(n+1 if kind=='janitor' else n)
            for i in frames:
                janitor(name,i,n) if kind=='janitor' else umbrella(name,i)
                render(QA/(kind+'_preview' if args.preview else kind+'_raw')/name/('f'+str(i).zfill(3)+'.png'))
            print('PASS6_CHARACTER',kind,name,round(time.perf_counter()-start,2),flush=True)
        meta[kind]={'rect':rect,'frame_width':w,'frame_height':h,'anchor':anchor,'scale':scale,'origin':ORIGIN}
    meta['seconds']=round(time.perf_counter()-start,3)
    (QA/('characters_preview_metadata.json' if args.preview else 'characters_metadata'+('_'+args.only if args.only else '')+'.json')).write_text(json.dumps(meta,indent=2))

if __name__=='__main__':main()
