"""Original procedural ginger lobby cat, lit in the actual pass-4 scene.

Native 2x RGBA renders; packaging derives clean premultiplied-filtered 1x sheets.
"""
import sys,json,math,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector,Matrix
import build_scene as b
from common import ROOT,xyz,ZPP,render,project

QA=ROOT/'qa5';ORIGIN=(10.75,7.75);M={};PARTS=[]
ANIMS={'sleep':(48,16),'sit':(48,16),'walk_plus_u':(10,12),'walk_minus_u':(10,12),
       'walk_plus_v':(10,12),'walk_minus_v':(10,12),'stretch':(32,16)}

def ball(name,pos,size,mat):
    ob=b.ball('Cat '+name,Vector(pos),1,M[mat],size);PARTS.append(ob);return ob

def tube(name,points,radii,mat):
    verts=[];faces=[]
    for i,p in enumerate(points):
        p=Vector(p);t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        t.normalize();u=t.cross(Vector((0,0,1)))
        if u.length<.01:u=t.cross(Vector((0,1,0)))
        u.normalize();v=t.cross(u)
        for j in range(8):verts.append(p+radii[i]*(u*math.cos(j*math.tau/8)+v*math.sin(j*math.tau/8)))
    for i in range(len(points)-1):
        for j in range(8):faces.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
    faces += [tuple(range(7,-1,-1)),tuple((len(points)-1)*8+j for j in range(8))]
    ob=b.mesh('Cat '+name,verts,faces,M[mat]);PARTS.append(ob)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def limb(a,c,r=.023,mat='fur'):
    return tube('leg',[a,c],[r,r*.65],mat)

def head(pos,closed=False,tilt=0,ear=0,lick=0):
    start=len(PARTS);x,y,z=pos
    ball('round head',pos,(.064,.058,.056),'fur')
    for side in [-1,1]:
        # Thick triangular pinnae, with a recessed warm pink inner triangle.
        verts=[(x-.025,y+side*.022,z+.034),(x+.020,y+side*.059,z+.029),
               (x-.011+ear*.008,y+side*(.063+ear*.01),z+.103),
               (x-.040,y+side*.039,z+.035)]
        ob=b.mesh('Cat pointed ear',verts,[(0,1,2),(0,2,3),(1,3,2),(0,3,1)],M['fur']);PARTS.append(ob)
        inner=[(x-.011,y+side*.032,z+.046),(x+.009,y+side*.051,z+.042),(x-.008+ear*.006,y+side*.057,z+.083)]
        ob=b.mesh('Cat inner ear',inner,[(0,1,2)],M['pink']);PARTS.append(ob)
        ball('cream whisker pad',(x+.052,y+side*.021,z-.016),(.022,.027,.019),'cream')
        if closed:
            tube('closed eye',[(x+.054,y+side*.028,z+.010),(x+.056,y+side*.042,z+.006)], [.0025,.0025],'dark')
        else:
            eye=ball('amber eye',(x+.052,y+side*.036,z+.012),(.010,.014,.011),'eye')
            ball('vertical pupil',(x+.060,y+side*.038,z+.012),(.003,.005,.009),'dark')
            ball('eye catchlight',(x+.061,y+side*.038,z+.017),(.0025,.0025,.0025),'cream')
        for j in range(2):
            tube('whisker',[(x+.065,y+side*.029,z-.011-j*.007),(x+.071,y+side*(.075+j*.006),z-.006-j*.009)], [.0009,.0003],'cream')
    ball('nose',(x+.074,y,z-.008),(.010,.013,.008),'pink')
    tube('mouth',[(x+.071,y,z-.015),(x+.066,y,z-.027)],[.0018,.0013],'dark')
    if lick>0:ball('tongue',(x+.081,y,z-.022),(.018*lick,.008,.005),'pink')
    # Tabby brow marks follow the head and stay legible in the enlarged reference.
    for j in [-1,0,1]:tube('brow stripe',[(x+.019,y+j*.018,z+.048),(x+.045,y+j*.018,z+.032)],[.003,.002],'stripe')
    if tilt:
        bpy.context.view_layer.update()
        tr=Matrix.Translation(Vector(pos))@Matrix.Rotation(tilt,4,'Y')@Matrix.Translation(-Vector(pos))
        for ob in PARTS[start:]:ob.matrix_world=tr@ob.matrix_world

def body_stripes(x0,x1,rz,cy=0,cz=.13,ry=.065):
    for i in range(5):
        x=x0+(x1-x0)*(i+.5)/5
        pts=[(x,cy+ry*math.sin(a),cz+rz*math.cos(a)) for a in [j*math.pi/10-math.pi/2 for j in range(11)]]
        tube('tabby flank stripe',pts,[.004]*len(pts),'stripe')

def pose(anim,index,n):
    global PARTS
    for ob in PARTS:
        data=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if data.users==0:
            if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
            elif isinstance(data,bpy.types.Curve):bpy.data.curves.remove(data)
    PARTS=[];t=(index%n)/n if anim!='stretch' else index/(n-1);a=math.tau*t
    angle={'walk_plus_u':0,'walk_minus_u':math.pi,'walk_plus_v':-math.pi/2,'walk_minus_v':math.pi/2}.get(anim,0)
    if anim=='sleep':
        breath=1+.022*math.sin(a)
        ball('curled body',(-.020,.005,.069),(.155,.115,.068*breath),'fur')
        body_stripes(-.12,.03,.058*breath,cz=.069,ry=.104)
        ball('tucked thigh',(-.09,-.055,.045),(.078,.058,.041),'fur')
        for y in [-.051,.006]:ball('tucked cream paw',(.105,y,.026),(.044,.027,.019),'cream')
        head((.103,-.034,.065),True,tilt=.18,ear=.20*math.exp(-(((t-.65+.5)%1-.5)/.04)**2))
        pts=[(-.02+.163*math.cos(q),.012+.125*math.sin(q),.036+.009*math.sin(q)) for q in [math.pi*.75+j*math.pi*1.52/24 for j in range(25)]]
        tube('wrapped tail',pts,[.024*(1-i/30) for i in range(25)],'fur')
        tube('dark tail tip',pts[-5:],[.008,.007,.006,.004,.002],'stripe')
    elif anim=='sit':
        bob=.003*math.sin(a);lick=math.exp(-(((t-.64+.5)%1-.5)/.075)**2)
        ball('haunches',(-.055,0,.080),(.092,.080,.078),'fur')
        ball('upright chest',(.011,0,.170+bob),(.068,.060,.112),'fur')
        ball('cream bib',(.064,-.001,.174+bob),(.015,.047,.070),'cream')
        for side in [-1,1]:
            limb((.040,side*.044,.175),(.066,side*.044,.031),.021)
            ball('front cream paw',(.079,side*.044,.019),(.033,.023,.017),'cream')
            ball('hind foot',(-.082,side*.067,.021),(.047,.033,.021),'fur')
        blink=math.exp(-(((t-.34+.5)%1-.5)/.025)**2)>.45
        head((.037+.009*lick,-.004,.282+bob-.025*lick),blink or lick>.4,tilt=.35*lick,lick=lick if lick>.3 else 0)
        pts=[(-.10-.16*s,-.025-.09*math.sin(s*2.1+.35*math.sin(a)),.027+.010*math.sin(s*math.pi)) for s in [i/18 for i in range(19)]]
        tube('swishing tail',pts,[.021*(1-i/23) for i in range(19)],'fur')
        tube('tail tip',pts[-4:],[.007,.006,.004,.002],'stripe')
    else:
        walk=anim.startswith('walk');extension=math.sin(math.pi*t)**2 if not walk else 0
        bob=.004*math.cos(2*a) if walk else -.025*extension
        ball('long torso',(-.016,0,.151+bob),(.133+.025*extension,.061,.068),'fur')
        body_stripes(-.115,.075,.061,cz=.151+bob,ry=.057)
        for front in [False,True]:
            x=.087 if front else -.106
            for side in [-1,1]:
                phase=(t+(0 if front else .5)+(.5 if side<0 else 0))%1
                # Half-cycle stance travels backward by 0.16 tiles: 0.32 per cycle.
                if walk:
                    dx=.08-.32*phase if phase<.5 else -.08+.32*(phase-.5)
                    lift=.037*math.sin((phase-.5)*math.tau) if phase>=.5 else 0
                else:dx=(.065 if front else -.035)*extension;lift=0
                shoulder=(x,side*.043,.145+bob)
                foot=(x+dx,side*.046,.018+lift)
                knee=((shoulder[0]+foot[0])*.5-.015,side*.047,.080+lift*.45)
                limb(shoulder,knee,.022);limb(knee,foot,.017)
                ball('cream paw',foot,(.028,.022,.017),'cream')
        head((.133+.030*extension,0,.192+bob-.043*extension),False,tilt=.18*extension)
        pts=[(-.13-.16*s,.02*math.sin(a+s*2) if walk else .02*math.sin(s*2),.16+.06*math.sin(s*2.5)+.06*extension*s) for s in [i/18 for i in range(19)]]
        tube('walking tail',pts,[.019*(1-i/23) for i in range(19)],'fur')
        tube('tail tip',pts[-4:],[.007,.006,.004,.002],'stripe')
    bpy.context.view_layer.update()
    transform=Matrix.Translation(xyz(*ORIGIN))@Matrix.Rotation(angle,4,'Z')
    for ob in PARTS:ob.matrix_world=transform@ob.matrix_world

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--anim',choices=list(ANIMS))
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass4.blend'));sc=bpy.context.scene
    sc.render.use_compositing=False;sc.render.film_transparent=True
    sc.cycles.device='CPU';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.cycles.adaptive_threshold=.02
    sc.cycles.max_bounces=5;sc.render.use_persistent_data=True
    for ob in sc.objects:
        if ob.type in ['MESH','FONT','CURVE']:ob.visible_camera=False
    b.GROUP='cat';b.GROUPS.clear()
    for name,color in [('fur',(.40,.16,.045)),('stripe',(.12,.039,.012)),('cream',(.65,.48,.28)),('pink',(.42,.15,.12)),('dark',(.008,.006,.004)),('eye',(.42,.50,.12))]:
        M[name]=b.material('Cat '+name,color,.8)
    x,y=project(*ORIGIN);rect=[int(x)-32,int(y)-44,64,64]
    scale=4 if args.preview else 2
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=(rect[0]+.1)/1920;sc.render.border_max_x=(rect[0]+64+.1)/1920
    sc.render.border_min_y=(1080-rect[1]-64+.1)/1080;sc.render.border_max_y=(1080-rect[1]+.1)/1080
    records=[];start=time.perf_counter()
    for anim in ([args.anim] if args.anim else ANIMS):
        n,fps=ANIMS[anim];frames=[0,n//3] if args.preview else range(n+(0 if anim=='stretch' else 1))
        for i in frames:
            pose(anim,i,n);folder=QA/('cat_preview' if args.preview else 'cat_raw')/anim
            render(folder/('f'+str(i).zfill(3)+'.png'))
        records.append({'name':anim,'frames':n,'fps':fps,'loop':anim!='stretch','stride_tiles':.32 if anim.startswith('walk') else None})
        print('PASS5_CAT',anim,round(time.perf_counter()-start,2),flush=True)
        if anim=='sit' and not args.preview:bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_cat.blend'))
    (QA/('cat_preview_metadata.json' if args.preview else 'cat_metadata.json')).write_text(json.dumps({'origin':ORIGIN,'rect':rect,
        'frame_size':[64,64],'anchor':[32,44],'render_scale':scale,'approximate_length_tiles':.45,
        'seconds':round(time.perf_counter()-start,3),'animations':records},indent=2))

if __name__=='__main__':main()
