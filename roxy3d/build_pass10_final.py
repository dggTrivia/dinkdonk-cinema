"""Apply brief 13 to the approved draft source; render draft 2 before production."""
import sys,json,math,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector,Matrix
import build_scene as b
import build_pass10_draft as d
from common import xyz,ZPP,project,render,NORMAL
from pass8_common import gpu
from pass10_common import ROOT,QA,OUT,LIVE,status

META=json.loads((QA/'layout3_draft_coordinates.json').read_text())
META['draft_only']=False;META['source']='roxy_pass10_draft.blend';META['removed_final']=[]
BELLS={};NEON=[]
def remove(o):META['removed_final'].append(o.name);d.rm(o)
def group(o,g):
    for ls in b.GROUPS.values():
        if o in ls:ls.remove(o)
    o['layer']=g;b.GROUPS.setdefault(g,[]).append(o)
def tube(n,points,color,body,r=.018,animate=None):
    old=set(bpy.context.scene.objects);d.tube(n,points,color,body,r)
    new=set(bpy.context.scene.objects)-old
    if animate:
        for o in new:o['bell_id']=animate
    NEON.append({'name':n,'points_px':[project(*p) for p in points],'color':list(color.diffuse_color[:3]),'animated':animate})

def emote(name,u,v,z,w,h):
    green=bpy.data.materials['P10 frog mint tube core'];greenbody=bpy.data.materials['P10 frog glass body']
    yellow=bpy.data.materials['P10 warning yellow tube core'];yellowbody=bpy.data.materials['P10 amber glass body']
    white=bpy.data.materials['P10 warm white eye tube']
    lips=b.material('P10 '+name+' orange brown neon lips',(.86,.24,.035),.24,emit=4)
    lipbody=b.material('P10 '+name+' terracotta glass',(.25,.048,.012),.3,emit=.35)
    gold=b.material('P10 '+name+' bell gold neon',(.95,.61,.065),.24,emit=6)
    dark=bpy.data.materials['P10 aged graphite steel']
    def path(label,pts,color=green,body=greenbody,r=.017,ring=False):
        tube(name+' '+label,[(u+x/36*w,v,z+(30-y)/30*h) for x,y in pts],color,body,r,name if ring else None)
    # The actual 36x30 emote silhouette, traced in its pixel coordinates.
    path('pointed yellow hood',[(8,15),(11,10),(15,3),(17,5),(19,10),(22,13),(25,15),(8,15)],yellow,yellowbody,.023)
    path('yellow cape',[(1,29),(1,24),(4,23),(5,25),(13,25),(22,25),(23,29)],yellow,yellowbody,.022)
    path('frog face',[(4,23),(5,20),(7,17),(9,15),(14,15),(15,17),(18,18),(20,17),(22,18),(25,17),(26,20),(24,24),(22,25),(16,25),(10,25),(6,24)],green,greenbody,.021)
    path('left white eye',[(14.6,15.5),(18,15.7),(20,16.4),(19.5,18.1),(17.2,18.2),(15.5,17.4)],white,greenbody,.016)
    path('right white eye',[(20.5,15.7),(24.7,15.6),(25.2,17.3),(23.3,18.6),(21.2,18.0)],white,greenbody,.016)
    path('left pupil',[(18.2,17.3),(18.4,18.2)],dark,dark,.020)
    path('right pupil',[(23.3,17.6),(23.3,18.6)],dark,dark,.020)
    path('orange brown lips',[(14,21),(16.6,20.5),(19.8,20.6),(22,21.5),(19.4,22.2),(16.5,21.9),(14,21)],lips,lipbody,.019)
    path('lower face crease',[(12,23),(16,23.5),(21.5,23.1)],green,greenbody,.011)
    path('raised green arm',[(24.6,24.5),(26,26),(28,24),(28,19),(26.8,17.4)],green,greenbody,.021)
    path('gripping hand',[(25.8,18.2),(27,17),(28.2,17.3),(28.2,19),(26.8,19.6)],green,greenbody,.016)
    path('bell handle',[(27.7,18.0),(28.6,12.7)],gold,lipbody,.016,True)
    path('bell body',[(26.2,10),(27.6,8.6),(29.6,8.8),(30.6,10.3),(30.0,12.8),(31,13.3),(26.5,13.0),(27.0,12.4),(26.2,10)],gold,yellowbody,.022,True)
    path('bell clapper',[(28.5,13.1),(28.5,14.0)],gold,yellowbody,.016,True)
    pivot=xyz(u+27.7/36*w,v,z+(30-18)/30*h)
    BELLS[name]={'pivot':list(pivot),'angles_deg':[-12,18],'fps':4,'states':2,'plane_v':v,'label':name,'group':b.GROUP}
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o.get('bell_id')==name:
            o['bell_original_matrix']=[q for row in o.matrix_world for q in row]
    META.setdefault('emotes',[]).append({'name':name,'uvz':[u,v,z],'width_tiles':w,'height_px':h,'reference':'ref/dinkdonk-emote/DinkDonk-x12.png','features':['pointed yellow hood and cape','green frog','white eyes','orange-brown lips','raised arm and gold hand bell']})

def pose_bells(state):
    for name,e in BELLS.items():
        pivot=Vector(e['pivot']);angle=math.radians(e['angles_deg'][state])
        for o in bpy.context.scene.objects:
            if o.get('bell_id')==name:
                a=list(o['bell_original_matrix']);orig=Matrix([a[j:j+4] for j in range(0,16,4)])
                o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Y')@Matrix.Translation(-pivot)@orig

def multiplex(sc):
    b.layer('background');roof=bpy.data.materials['P10 wet mineral felt'];brick=bpy.data.materials['P8 brownbrick'];metal=bpy.data.materials['P10 aged graphite steel'];concrete=bpy.data.materials['P10 auditorium faded concrete'];water=bpy.data.materials['P10 roof standing rainwater']
    for o in list(sc.objects):
        n=o.name;a,v,c,w,z,h=d.bounds(o)
        shell=n.startswith(('P10 hall ','P10 hall parapet','P10 hall roof dividing'))
        far=n.startswith(('P8 distant solid city','P8 distant inset window','P8B irregular distant','P8B distant','P8B roof stair','P10 distant building','P10 low rear'))
        if shell or (far and c>-4):remove(o)
    # One connected footprint with a west service return behind the neighbouring
    # shop. A single unbroken roof occupies the top/right camera crop.
    polygon=[(-4,-30),(32,-30),(32,-.23),(0,-.23),(0,-1.08),(-4,-1.08)]
    top=240
    b.mesh('P10 single multiplex wet roof',[xyz(u,v,top) for u,v in polygon],[tuple(range(len(polygon)))],roof)
    for i,((u,v),(a,c)) in enumerate(zip(polygon,polygon[1:]+polygon[:1])):
        if i==2:
            # Front band above the retained corridor wall; no solid infill behind doors.
            b.box('P10 multiplex continuous front masonry',0,-.40,32,-.23,170,240,brick,.01)
        else:
            b.mesh('P10 multiplex external wall',[xyz(u,v,-8),xyz(a,c,-8),xyz(a,c,240),xyz(u,v,240)],[(0,1,2,3)],brick)
        d.line('multiplex coping',[(u,v,242),(a,c,242)],concrete,.045)
    for u in [19/3,29/3]:b.box('P10 internal hall party wall',u-.06,-4.4,u+.06,-.41,0,236,brick,.006)
    # Move retained roof equipment onto the common 240px roof.
    prefixes=('P10 projection booth','P10 roof hatch','P10 HVAC','P10 air duct','P10 duct seam','P10 roof puddle')
    for o in sc.objects:
        if o.name.startswith(prefixes):
            a,v,c,w,z,h=d.bounds(o);u=(a+c)/2;old=238 if u<19/3 else 246 if u<29/3 else 240
            o.location.z+=(240-old)/ZPP
    # Believable additional service kit on the newly visible connected roof.
    rng=np.random.default_rng(1310)
    for i,(u,v) in enumerate([(1.0,-3.5),(3.1,-6.6),(6.1,-7.6),(9.2,-6.8),(12.8,-7.9)]):
        b.box('P10 additional roof HVAC feet',u-.5,v-.40,u+.5,v+.40,240,245,metal)
        b.box('P10 additional HVAC unit',u-.47,v-.37,u+.47,v+.37,245,269,metal)
        for du in [-.22,.22]:b.cylinder('P10 additional HVAC fan',xyz(u+du,v,269.4),.17,.012,bpy.data.materials['P10 velvet darkness'],vertices=24)
        b.box('P10 additional HVAC duct',u+.25,v+.37,u+.65,v+1.28,246,260,metal)
    b.box('P10 roof access hut',.35,-2.15,1.7,-1.12,240,304,concrete)
    b.box('P10 roof access hut cap',.30,-2.20,1.75,-1.07,304,308,roof)
    b.box('P10 roof service door',.68,-1.105,1.30,-1.08,240,293,metal,.008)
    d.line('roof service handle',[(1.20,-1.06,260),(1.20,-1.06,270)],concrete,.012)
    for u in [.18,1.90]:d.line('roof access ladder side',[(u,-.44,176),(u,-.44,253)],metal,.014)
    for zz in range(180,253,8):d.line('roof access ladder rung',[(.18,-.44,zz),(1.90,-.44,zz)],metal,.009)
    for u in [2.8,6.6,10.4,12.95]:
        d.line('multiplex drainpipe',[(u,-.21,240),(u,-.19,180),(u,-.42,173)],metal,.022)
        b.box('multiplex rain hopper',u-.07,-.30,u+.07,-.16,230,242,metal,.009)
    for i in range(42):
        u=float(rng.uniform(-1,18));v=float(rng.uniform(-12,-.55))
        b.ball('P10 multiplex roof pooled rain',xyz(u,v,240.09),1,water,(float(rng.uniform(.12,.55)),float(rng.uniform(.08,.30)),.001))
    # Linked fill gives the broad wet roof readable 90s service-building texture.
    receivers=bpy.data.collections.new('P10 multiplex roof light receivers');sc.collection.children.link(receivers)
    for o in sc.objects:
        if o.name.startswith(('P10 single multiplex','P10 multiplex','P10 additional','P10 roof access','P10 roof service')):receivers.objects.link(o)
    lamp=b.area('P10 broad multiplex roof fill',xyz(6,-4,730),1100,(.40,.48,.63),14,target=xyz(6,-4,240));lamp.light_linking.receiver_collection=receivers
    META['multiplex']={'footprint_polygon_uv':polygon,'roof_z_px':240,'front_wall_v':-.23,'single_continuous_roof':True,'fills_top_right':True,'hall_divisions_u':[3,19/3,29/3,13]}
    for s in META['screens']:s['roof_z']=240
    status('Auditoriums combined into one continuous multiplex building extending off the top/right frame; service hut, HVAC, ducts, ladders, drains and wet roof added')

def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.M.clear()
    for ma in bpy.data.materials:b.M[ma.name]=ma
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o);o.visible_camera=True;o.is_holdout=False
    d.metal=bpy.data.materials['P10 aged graphite steel'];b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    for o in list(sc.objects):
        if o.name.startswith(('P10 rooftop DinkDonk','P10 entrance DinkDonk')):remove(o)
    b.layer('rooftop_neon');emote('rooftop_dinkdonk',3.80,-.58,325,1.62,94)
    b.layer('entrance_neon');emote('entrance_dinkdonk',-.80,9.32,168,.75,71)
    pose_bells(0);multiplex(sc)
    # Keep all broad roof/sign geometry in the background; the foreground blade
    # will be exported as a proper slice-owned occluder, with its bell separate.
    for o in list(sc.objects):
        if o.get('layer') in ['auditorium_block','rooftop_neon','ad_rooftop']:
            group(o,'background')
        if o.get('bell_id'):group(o,'bell_'+o['bell_id'])
    META['bells']=BELLS;META['neon_paths']=NEON
    sc['pass10_final_brief']='BRIEF-13-pass10-final.md';sc['draft_only']=False
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100;sc.cycles.samples=24;sc.cycles.adaptive_threshold=.05
    bpy.context.view_layer.update();sc.render.use_border=False;sc.render.use_crop_to_border=False
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10.blend'))
    (QA/'scene_metadata_final.json').write_text(json.dumps(META,indent=2))
    status('Both DinkDonk emblems rebuilt from the enlarged actual emote: pointed hood/cape, frog eyes, orange-brown lips and gold bell; two physical bell poses prepared')
    t=time.perf_counter();render(QA/'draft_2.png')
    status('Quick lit draft_2.png rendered in %.1f seconds; continuing directly into complete out10 production'%(time.perf_counter()-t))
if __name__=='__main__':main()
