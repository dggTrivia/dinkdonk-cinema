"""Six original miniature props, using the saved layout-2 camera and lighting.

No image assets are used in the models. Final renders are 4x supersampled;
package_pass7.py filters straight RGBA correctly to the delivered 2x and 1x.
"""
import sys, json, math, random, time, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import build_scene as b
from common import ROOT, RIGHT, UP, NORMAL, PPU, xyz, project, render
from render_loop_basis import crop

QA = ROOT/'qa7'
ORIGIN = (8, 7, 50)
FRONT = Vector((2**-.5, -2**-.5, 0))
PARTS = []
M = {}
SPECS = {
    'popcorn': (16, 20, [8, 18], 'bottom centre of tub'),
    'soda': (12, 18, [6, 16], 'bottom centre of cup'),
    'stub': (12, 8, [6, 4], 'centre of ticket stub'),
    'ticket': (18, 11, [9, 5.5], 'centre of whole ticket'),
    'cap_cashier': (28, 12, [14, 10], 'bottom centre of cap'),
    'cap_usher': (28, 12, [14, 10], 'bottom centre of cap'),
}

def q(x,y,z):
    return RIGHT*x + FRONT*y + Vector((0,0,z))

def mesh(name, verts, faces, material):
    ob=b.mesh('Pass7 '+name, verts, faces, M[material]); PARTS.append(ob)
    return ob

def line(name, points, radius, material, cyclic=False):
    ob=b.line('Pass7 '+name, points, M[material], radius, cyclic); PARTS.append(ob)
    return ob

def ball(name, p, scale, material):
    ob=b.ball('Pass7 '+name, q(*p), 1, M[material], scale); PARTS.append(ob)
    # Ellipsoid axes follow the miniature's camera-relative horizontal axes.
    ob.rotation_euler.z=math.pi/4
    return ob

def rings(name, sections, material, stripes=False, count=48):
    """Tapered/crowned elliptical solids, with optional alternating printed panels."""
    verts=[q(rx*math.cos(i*math.tau/count), ry*math.sin(i*math.tau/count), z)
           for rx,ry,z in sections for i in range(count)]
    faces=[tuple(range(count-1,-1,-1))]
    faces += [(j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i)
              for j in range(len(sections)-1) for i in range(count)]
    faces.append(tuple((len(sections)-1)*count+i for i in range(count)))
    ob=mesh(name,verts,[tuple(reversed(f)) for f in faces],material)
    if stripes:
        ob.data.materials.append(M['red'])
        for p in ob.data.polygons[1:-1]:p.material_index=((p.index-1)%count//3)%2
    for p in ob.data.polygons[1:-1]:p.use_smooth=True
    return ob

def rim(name, rx,ry,z,r,mat):
    return line(name,[q(rx*math.cos(i*math.tau/64),ry*math.sin(i*math.tau/64),z) for i in range(64)],r,mat,True)

def popcorn():
    rng=random.Random(9707)
    rings('striped paper popcorn tub',[(.054,.048,0),(.075,.065,.143)],'paper',True)
    rim('rolled cream tub rim',.075,.065,.143,.0036,'paper')
    rim('worn lower paper seam',.054,.048,.003,.0014,'worn')
    # Separate lumpy kernels, rather than a single white dome.
    for level,n,rr in [(0,17,.059),(1,10,.043),(2,4,.022)]:
        for i in range(n):
            a=i*math.tau/n + level*.7
            r=rr*rng.uniform(.83,1.06)
            x,y=r*math.cos(a),r*math.sin(a)
            z=.146+level*.018+rng.uniform(-.003,.004)
            mat='kernel' if i%4 else 'butter'
            ball('popped corn heart',(x,y,z),(.011,.010,.010),mat)
            for j in range(3):
                a2=j*math.tau/3+.2*i
                ball('popped corn petal',(x+.010*math.cos(a2),y+.009*math.sin(a2),z+.006),(.009,.008,.009),mat)
            if i%3==0:ball('toasted kernel dimple',(x,y+.007,z+.011),(.003,.003,.002),'toast')
    for x in [-.033,.026]:
        line('faded tub crease',[q(x,.052,.025),q(x+.003,.059,.090)],.0008,'worn')

def soda():
    rings('waxed soda cup',[(.038,.033,0),(.054,.047,.119)],'paper')
    rings('faded teal paper print',[(.043,.037,.039),(.050,.043,.088)],'teal')
    rings('red printed cup stripe',[(.045,.039,.052),(.047,.041,.065)],'red')
    rings('plastic lid shoulder',[(.055,.049,.117),(.059,.051,.122),(.052,.046,.130)],'lid')
    rim('raised lid lip',.057,.050,.123,.0022,'paper')
    rim('lid central emboss',.033,.029,.131,.0012,'lid')
    ball('straw lid recess',(.010,-.005,.132),(.008,.007,.0014),'worn')
    pts=[q(.01,-.005,.127),q(.013,-.005,.187),q(.034,-.005,.208)]
    line('paper straw',pts,.0042,'paper')
    for z in [.143,.161,.178]:line('red straw bands',[q(.010+(z-.127)*.05,-.005,z),q(.010+(z-.127)*.05,-.005,z+.006)],.0043,'red')
    line('straw open tip',[q(.030,-.005,.204),q(.034,-.005,.208)],.0021,'dark')
    line('cup paper overlap',[q(-.018,.034,.008),q(-.023,.047,.112)],.0008,'worn')

def cap(usher=False):
    mat='maroon' if usher else 'red_cloth'
    if usher:
        rings('pillbox velvet crown',[(.148,.068,0),(.153,.072,.060),(.142,.067,.067)],mat)
        rings('pillbox gold band',[(.149,.069,.008),(.151,.071,.023)],'gold')
        rim('pillbox top piping',.148,.069,.062,.0023,'seam')
        ball('gold pillbox front button',(.074,.065,.040),(.010,.005,.010),'gold')
        line('pillbox panel seam',[q(-.05,-.062,.064),q(-.044,.062,.064)],.0012,'seam')
    else:
        # A shallow peaked staff cap with a visibly curved dark-red visor.
        ball('curved red visor',(.002,.060,.006),(.145,.073,.010),'visor')
        rings('cap headband',[(.127,.061,.010),(.130,.064,.041)],'red_cloth')
        rings('staff cap gold band',[(.129,.063,.014),(.131,.065,.029)],'gold')
        rings('soft red cap crown',[(.133,.067,.032),(.149,.073,.062),(.137,.065,.081),(.020,.015,.088)],mat)
        rim('cap crown seam',.148,.073,.060,.0018,'seam')
        ball('small brass cap badge',(0,.072,.054),(.012,.005,.010),'gold')
        for x in [-.10,.10]:ball('visor brass fastening',(x,.045,.020),(.005,.005,.004),'gold')
        line('crown stitch seam',[q(-.018,-.059,.078),q(0,0,.089),q(.018,.055,.076)],.0009,'seam')
    # These are shallow staff hats. Narrow the physical fore-aft profile and
    # lower the crown so the visible brim fills the requested 28px canvas.
    bpy.context.view_layer.update()
    basis=Matrix((RIGHT,FRONT,Vector((0,0,1)))).transposed().to_4x4()
    f=.84 if usher else .66
    reshape=basis@Matrix.Diagonal(Vector((1,f,f,1)))@basis.inverted()
    for ob in PARTS:ob.matrix_world=reshape@ob.matrix_world

def ticket(stub=False):
    # The card is a curved 3D paper slab, tilted in space, with a dark fibre edge.
    angle=math.radians(12 if stub else -9)
    rx=RIGHT*math.cos(angle)+UP*math.sin(angle)
    ry=(-RIGHT*math.sin(angle)+UP*math.cos(angle))*math.cos(.46)-NORMAL*math.sin(.46)
    normal=rx.cross(ry).normalized()
    w,h=(.115,.060) if stub else (.185,.090)
    def p(x,y,depth=0):return rx*x+ry*y+normal*(depth+.055*x*x/w)
    if stub:
        edge=[(-w/2,-h/2),(w/2-.006,-h/2),(w/2-.001,-.020),(w/2-.008,-.013),(w/2+.001,-.005),(w/2-.005,.003),(w/2,.012),(w/2-.007,.019),(w/2,h/2),(-w/2,h/2)]
    else:
        edge=[(-w/2,-h/2),(w/2,-h/2),(w/2,-.012),(w/2-.007,-.008),(w/2-.010,0),(w/2-.007,.008),(w/2,.012),(w/2,h/2),(-w/2,h/2),(-w/2,.012),(-w/2+.007,.008),(-w/2+.010,0),(-w/2+.007,-.008),(-w/2,-.012)]
    n=len(edge);verts=[p(x,y,d) for d in [-.002,0] for x,y in edge]
    ob=mesh('torn ticket' if stub else 'whole cinema ticket',verts,[tuple(range(n,2*n)),tuple(range(n-1,-1,-1))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],'ticket')
    ob.data.materials.append(M['ticket_edge'])
    for poly in ob.data.polygons[1:]:poly.material_index=1
    for y in [-h*.34,h*.34]:line('red printed ticket rule',[p(-w*.40,y,.0007),p(w*.37,y,.0007)],.0015,'ink')
    # Printed box/serial bars stay graphic and crisp at the intended tiny size.
    for i in range(5):line('ticket serial bar',[p(-w*.29+i*w*.105,-h*.18,.001),p(-w*.29+i*w*.105,-h*.05,.001)],.0011 if i%2 else .0018,'ink')
    line('ticket admission ink',[p(-w*.24,h*.12,.001),p(w*.21,h*.12,.001)],.003,'ink')
    if not stub:
        for j in range(6):line('ticket perforation',[p(w*.29,-h*.35+j*h*.12,.0005),p(w*.29,-h*.30+j*h*.12,.0005)],.001,'ticket_edge')
    else:
        for i in [2,4,6]:line('exposed torn paper fibre',[p(*edge[i],.0002),p(edge[i][0]+.002,edge[i][1]+.001,.0002)],.0006,'paper')

def setup(samples):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass6.blend'))
    sc=bpy.context.scene
    sc.render.use_compositing=False;sc.render.film_transparent=True
    sc.cycles.device='CPU';sc.cycles.samples=samples;sc.cycles.adaptive_threshold=.01;sc.cycles.max_bounces=5
    sc.cycles.use_denoising=True
    for ob in sc.objects:
        if ob.type in ['MESH','FONT','CURVE']:ob.visible_camera=False
    b.GROUP='pass7_items';b.GROUPS.clear()
    palette=[('paper',(.74,.66,.47),.62,0),('red',(.48,.026,.035),.66,0),('worn',(.34,.27,.16),.85,0),
             ('kernel',(.86,.76,.48),.8,0),('butter',(.64,.44,.18),.8,0),('toast',(.22,.09,.024),.9,0),
             ('teal',(.035,.24,.22),.62,0),('lid',(.69,.67,.56),.4,0),('dark',(.03,.018,.015),.75,0),
             ('red_cloth',(.40,.018,.027),.84,0),('maroon',(.19,.012,.029),.86,0),('gold',(.80,.48,.12),.48,.25),
             ('visor',(.095,.012,.018),.47,0),('seam',(.24,.022,.028),.85,0),('ticket',(.73,.48,.23),.86,0),
             ('ticket_edge',(.29,.17,.065),.95,0),('ink',(.29,.025,.026),.9,0)]
    for name,col,rough,metal in palette:
        mat=b.material('Pass7 '+name,col,rough,metal,texture=90 if name in ['paper','red_cloth','maroon','ticket'] else 0)
        for node in mat.node_tree.nodes:
            if node.type=='BUMP':node.inputs['Distance'].default_value=.0007;node.inputs['Strength'].default_value=.12
        M[name]=mat
    return sc

def fit(sc,name):
    """Uniform physical scaling and translation only; no screen-space distortion."""
    bpy.context.view_layer.update()
    verts=[];deps=bpy.context.evaluated_depsgraph_get()
    for ob in PARTS:
        evaluated=ob.evaluated_get(deps);data=evaluated.to_mesh()
        verts += [evaluated.matrix_world@v.co for v in data.vertices]
        evaluated.to_mesh_clear()
    xx=[v.dot(RIGHT)*PPU for v in verts];yy=[-v.dot(UP)*PPU for v in verts]
    w,h,anchor,_=SPECS[name]
    vertical_padding=3 if name in ['stub','ticket'] else 4
    factor=min((w-3)/(max(xx)-min(xx)),(h-vertical_padding)/(max(yy)-min(yy)))
    # The visible bottom centre is the attachment reference for cups/caps.
    ax=(min(xx)+max(xx))/2;ay=(min(yy)+max(yy))/2 if name in ['stub','ticket'] else max(yy)
    correction=-RIGHT*(ax/PPU)+UP*(ay/PPU)
    tr=Matrix.Translation(xyz(*ORIGIN)+correction*factor)@Matrix.Scale(factor,4)
    for ob in PARTS:ob.matrix_world=tr@ob.matrix_world
    bpy.context.view_layer.update()
    x,y=project(*ORIGIN);rect=[x-anchor[0],y-anchor[1],w,h]
    # Half-pixel centre for the odd-height whole ticket: shift its actual root
    # half a pixel down, keeping the render crop at integer pixel boundaries.
    dy=rect[1]-math.floor(rect[1]);rect[1]=math.floor(rect[1])
    if dy:
        for ob in PARTS:ob.location+=UP*(dy/PPU)
    crop(sc,dict(zip(['x','y','w','h'],rect)))
    return {'w':w,'h':h,'anchor':anchor,'attach_point':SPECS[name][3],
            'render_rect':rect,'uniform_model_scale':factor,'origin_uvz':ORIGIN}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--samples',type=int,default=96)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    QA.mkdir(exist_ok=True);sc=setup(24 if args.preview else args.samples)
    sc.render.resolution_x=7680;sc.render.resolution_y=4320;sc.render.resolution_percentage=100
    meta={'render_scale':4,'samples':sc.cycles.samples,'device':'CPU','items':{}};start=time.perf_counter()
    for name in SPECS:
        for ob in PARTS:bpy.data.objects.remove(ob,do_unlink=True)
        PARTS.clear()
        if name=='popcorn':popcorn()
        elif name=='soda':soda()
        elif name in ['stub','ticket']:ticket(name=='stub')
        else:cap(name=='cap_usher')
        info=fit(sc,name);t=time.perf_counter()
        path=QA/('items_preview' if args.preview else 'items_raw')/(name+'@4x.png')
        render(path);info['render_seconds']=round(time.perf_counter()-t,3);meta['items'][name]=info
        print('PASS7_ITEM',name,info['render_seconds'],flush=True)
    meta['seconds']=round(time.perf_counter()-start,3)
    (QA/('items_preview_metadata.json' if args.preview else 'items_metadata.json')).write_text(json.dumps(meta,indent=2))

if __name__=='__main__':main()
