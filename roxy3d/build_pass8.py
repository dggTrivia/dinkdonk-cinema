"""Connected, genuinely three-dimensional surroundings; exact inherited camera.

Stage one renders a lit preview and an independent action-volume holdout test.
No animation frames are produced by this script.
"""
import sys,json,math,random,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector,Matrix
import build_scene as b
from common import ROOT,xyz,project,ZPP,PPU,RIGHT,UP,NORMAL,render
from pass8_common import status,gpu
QA=ROOT/'qa8';M={};NEW=[];REGIONS=[];RNG=random.Random(8802)

def box(n,u0,v0,u1,v1,z0,z1,m,bevel=.012):
    ob=b.box('P8 '+n,u0,v0,u1,v1,z0,z1,M[m],bevel);NEW.append(ob);return ob

def line(n,pts,r,m):
    ob=b.line('P8 '+n,[xyz(*p) for p in pts],M[m],r);NEW.append(ob);return ob

def cyl(n,u,v,z,r,h,m):
    ob=b.cylinder('P8 '+n,xyz(u,v,z+h/2),r,h/ZPP,M[m],vertices=20);NEW.append(ob);return ob

def mat(n,col,rough=.75,metal=0,emit=0,texture=0):
    M[n]=b.material('P8 '+n,col,rough,metal,emit,texture);return M[n]

def brick(n,col):
    m=mat(n,col,.84);nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(tex.outputs['Object'],sep.inputs[0])
    # Use world XY/Z coordinates on both vertical faces, not object-scaled boxes.
    geom=nodes.new('ShaderNodeNewGeometry');links.new(geom.outputs['Position'],sep.inputs[0])
    vec=nodes.new('ShaderNodeCombineXYZ');add=nodes.new('ShaderNodeMath');add.operation='ADD'
    links.new(sep.outputs['X'],add.inputs[0]);links.new(sep.outputs['Y'],add.inputs[1]);links.new(add.outputs[0],vec.inputs['X']);links.new(sep.outputs['Z'],vec.inputs['Y'])
    br=nodes.new('ShaderNodeTexBrick');links.new(vec.outputs[0],br.inputs['Vector'])
    br.inputs['Scale'].default_value=3.2;br.inputs['Brick Width'].default_value=.52;br.inputs['Row Height'].default_value=.25
    br.inputs['Mortar Size'].default_value=.018;br.inputs['Color1'].default_value=(*col,1)
    br.inputs['Color2'].default_value=(*(c*.63 for c in col),1);br.inputs['Mortar'].default_value=(.055,.052,.045,1)
    links.new(br.outputs['Color'],p.inputs['Base Color']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.014
    links.new(br.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal']);return m

def materials():
    brick('brick',(.18,.105,.071));brick('brownbrick',(.105,.078,.063));brick('distantbrick',(.055,.062,.078))
    for args in [('stone',(.22,.215,.19),.88,0,0,36),('cream',(.38,.34,.25),.88,0,0,38),('tar',(.023,.028,.033),.40,0,0,55),
                 ('gravel',(.065,.064,.059),.78,0,0,110),('metal',(.09,.10,.105),.42,.65,0,35),('rust',(.15,.073,.031),.9,.35,0,55),
                 ('darkglass',(.014,.026,.032),.22,.2,0,0),('amber',(.62,.32,.105),.4,0,1.4,0),('dimwindow',(.15,.16,.13),.5,0,.28,0),
                 ('tv',(.09,.21,.27),.4,0,.9,0),('greenpaint',(.075,.12,.095),.78,0,0,35),('bluepaint',(.065,.11,.15),.82,0,0,35),
                 ('wet',(.012,.022,.031),.075,.3,0,5),('concrete',(.105,.12,.13),.45,0,0,40),('asphalt',(.021,.027,.031),.2,.12,0,90),
                 ('ink',(.014,.012,.011),.95,0,0,0),('signlight',(.49,.34,.16),.5,0,1.3,0),('signolive',(.12,.27,.19),.5,0,1.8,0)]:mat(*args)

def roof(u0,v0,u1,v1,z,kit=True):
    box('gravel roof',u0,v0,u1,v1,z-2,z,'gravel')
    for a,c in [(u0,u0+.09),(u1-.09,u1)]:box('brick parapet',a,v0,c,v1,z,z+5,'brick')
    for a,c in [(v0,v0+.09),(v1-.09,v1)]:box('brick parapet',u0,a,u1,c,z,z+5,'brick')
    for i in range(6):
        u=RNG.uniform(u0+.2,u1-.6);v=RNG.uniform(v0+.2,v1-.5)
        box('roof felt patch',u,v,min(u+.65,u1-.1),min(v+.4,v1-.1),z+.02,z+.06,'tar',0)
        if i%2==0:
            ob=b.ball('P8 rooftop pooled rain',xyz(u+.2,v+.12,z+.09),1,M['wet'],(.26,.12,.001));NEW.append(ob)
    if kit:
        u=(u0+u1)/2;v=(v0+v1)/2
        box('AC unit feet',u-.38,v-.25,u+.38,v+.25,z,z+3,'rust')
        box('rooftop AC case',u-.34,v-.23,u+.34,v+.23,z+3,z+19,'metal')
        cyl('AC fan grille',u,v,z+19,.18,.7,'ink')
        for i in range(6):box('AC slotted intake',u+.341,v-.18+i*.06,u+.35,v-.15+i*.06,z+5,z+15,'ink',0)
        cyl('vent stack',u+.75,v+.6,z,.095,25,'metal');cyl('vent cap',u+.75,v+.6,z+24,.14,2,'metal')
        box('skylight frame',u-.95,v+.55,u-.27,v+1.05,z+.1,z+6,'metal')
        box('warm wired skylight',u-.91,v+.59,u-.31,v+1.01,z+6,z+6.6,'amber',.004)
        for i in range(4):box('skylight glazing bars',u-.90+i*.19,v+.58,u-.885+i*.19,v+1.02,z+6.7,z+7,'metal',0)

def window(wall,at,front,z,w=.45,h=28,lit=True):
    color=RNG.choice(['amber','dimwindow','tv']) if lit else 'darkglass'
    def panel(n,a,c,bottom,top,material,depth):
        if wall=='v':return box(n,a,front,c,front+depth,bottom,top,material,.005)
        return box(n,front,a,front+depth,c,bottom,top,material,.005)
    panel('recessed window stone lintel',at-w/2-.06,at+w/2+.06,z-3,z+h+4,'stone',.035)
    panel('deep window reveal',at-w/2-.025,at+w/2+.025,z-1,z+h+1,'ink',.05)
    ob=panel('lit recessed window',at-w/2,at+w/2,z,z+h,color,.055)
    if color=='tv':ob['pass8_tv']=True
    panel('window centre mullion',at-.012,at+.012,z,z+h,'metal',.06)
    panel('window sill',at-w/2-.06,at+w/2+.06,z-4,z-2,'stone',.12)
    if lit and RNG.random()<.6:panel('uneven curtain',at-w*.48,at-w*.22,z+2,z+h,'cream',.06)

def lettering(body,u,v,z,size,wall='v',m='cream'):
    rot=b.FRONT_FACE if wall=='v' else Matrix(((0,-1,0),(0,0,1),(1,0,0))).transposed().to_quaternion()
    ob=b.text('P8 sign '+body,body,xyz(u,v,z),size,M[m],rot,.0007);NEW.append(ob);return ob

def fireescape(u,v,z0,z1,width=.85):
    for z in np.arange(z0,z1+1,61):
        box('fire escape landing',u,v,u+width,v+.40,z,z+2,'metal')
        for j in range(7):line('iron escape bars',[(u+j*width/6,v+.40,z+2),(u+j*width/6,v+.40,z+20)],.008,'metal')
        line('escape handrail',[(u,v+.40,z+20),(u+width,v+.40,z+20)],.012,'metal')
        if z+61<=z1:
            for j in range(11):box('escape stair tread',u+width*.1+j*.058,v+.05,u+width*.1+j*.058+.11,v+.33,z+j*5.5,z+j*5.5+1.2,'metal',.002)

def tank(u,v,z,r=.43,h=48):
    for du,dv in [(-r*.6,-r*.6),(-r*.6,r*.6),(r*.6,-r*.6),(r*.6,r*.6)]:line('water tank legs',[(u+du,v+dv,z),(u+du,v+dv,z+12)],.025,'metal')
    cyl('rooftop water tank',u,v,z+12,r,h-14,'rust');cyl('tank lid',u,v,z+h-2,r*1.03,2,'metal')
    for zz in [z+19,z+h-10]:
        pts=[(u+r*1.005*math.cos(a),v+r*1.005*math.sin(a),zz) for a in np.linspace(0,math.tau,41)]
        line('tank steel band',pts,.012,'metal')

def build_city():
    # Ground under the whole city; no image planes or floating slab edges.
    # The connected foreground terrain terminates behind the city horizon.
    # Extending an opaque plane to infinity would hide the sky in this camera.
    ob=b.mesh('P8 connected city terrain',[xyz(u,v,-5) for u,v in [(-51,45),(60,45),(60,-50),(44,-50)]],[(3,2,1,0)],M['asphalt']);NEW.append(ob)
    box('opposite curb',-30,13.5,30,13.65,-4,0,'stone')
    box('opposite paved sidewalk',-30,13.65,30,16.35,-4,.05,'concrete',0)
    for u in np.arange(-20,24,.75):line('opposite paving joint',[(u,13.7,.08),(u,16.3,.08)],.005,'ink')
    for v in [14.4,15.15,15.9]:line('opposite longitudinal joint',[(-25,v,.08),(28,v,.08)],.005,'ink')
    box('left connected forecourt',-12,0,-.12,9.15,-9,-.5,'concrete',0)
    box('right service alley',13.06,-1,23,9.15,-9,-.35,'concrete',0)
    # Low opposite roofs obey H <= 60(v-13.5)-48, including every piece of kit.
    for i,(u0,u1,z) in enumerate([(-2,3.2,96),(3.2,8.1,105),(8.1,14,112)]):
        v0,v1=16.5,21
        box('opposite workshop masonry',u0,v0,u1,v1,-5,z-5,'brownbrick');roof(u0,v0,u1,v1,z-5)
        REGIONS.append({'name':'opposite_workshop_'+str(i),'uv':[u0,v0,u1,v1],'roof_px':z,'envelope':'H <= 60*(v-13.5)-48'})
        # Street-facing fascia is on the far side; camera sees its braced back.
        box('roof sign weathered back',u0+.4,16.95,u1-.4,17.03,z+8,z+28,'metal')
        for u in [u0+.65,u1-.65]:line('roof sign triangulated strut',[(u,17,z+10),(u,17.7,z),(u,17,z+27)],.018,'rust')
        box('street-facing sign light',u0+.45,16.938,u1-.45,16.95,z+11,z+25,'signolive' if i==0 else 'signlight',.004)
        b.area('P8 opposite sign street spill '+str(i),xyz((u0+u1)/2,16.8,z+17),35,(.57,.63,.32) if i==0 else (1,.53,.21),2.5,target=xyz((u0+u1)/2,13.6,0))
        if i==1:tank(6.8,19,z-5,.35,37)
        for u in [u0+.15,u1-.15]:line('workshop downspout',[(u,16.48,z-2),(u,16.48,5)],.025,'metal')
    # Short street furniture stays behind the same action envelope.
    for u in [-2,3,9,14]:
        box('far sidewalk low bollard',u,15.3,u+.10,15.4,0,30,'metal')
    box('opposite timber bench',1,15.6,2.1,15.86,4,13,'greenpaint')
    # Roxy's own auditorium mass behind the left corridor.
    box('Roxy auditorium 1-2 block',-1.1,.05,-.08,8.62,-5,205,'brownbrick');roof(-1.1,.05,-.08,8.62,205,False)
    for v in [1.1,3.2,5.3,7.4]:box('auditorium roof vent',-.80,v,-.36,v+.36,206,217,'metal')
    REGIONS.append({'name':'Roxy auditorium block','uv':[-1.1,.05,-.08,8.62],'max_height_px':217})
    # Left apartments above the video-rental shop and shuttered takeaway.
    box('left brick apartment building',-5,-1,-1.2,8.7,-5,235,'brick');roof(-5,-1,-1.2,8.7,235)
    for z in [75,130,185]:
        for u in [-4.55,-3.7,-2.85,-2]:window('v',u,8.705,z,.51,32,RNG.random()<.72)
        for v in [0,1.3,2.6,3.9,5.2,6.5,7.7]:window('u',v,-1.195,z,.5,32,RNG.random()<.5)
    for a,c in [(-4.8,-2.65),(-2.55,-1.4)]:
        box('shop fascia',a,8.72,c,8.82,44,65,'greenpaint')
        box('shop front recess',a,8.71,c,8.74,1,43,'ink')
    box('video shop lit display',-4.69,8.75,-2.8,8.77,8,39,'dimwindow')
    for j in range(12):box('video rental VHS case',-4.62+j*.15,8.79,-4.54+j*.15,8.81,12,29,'cream' if j%3 else 'bluepaint',.002)
    for z in range(5,43,3):box('takeaway roller shutter rib',-2.49,8.77,-1.48,8.84,z,z+1.2,'metal',.002)
    lettering('VIDEO  RENTAL',-3.75,8.831,54,.19);lettering('TAKE AWAY',-1.97,8.831,54,.11)
    # Fabric awning and gutter remain v<9.15, safely behind the sidewalk.
    ob=b.mesh('P8 striped shop awning',[xyz(-4.82,8.78,43),xyz(-2.62,8.78,43),xyz(-2.62,9.09,36),xyz(-4.82,9.09,36)],[(0,1,2,3)],M['greenpaint']);NEW.append(ob)
    line('awning drip edge',[(-4.82,9.09,36),(-2.62,9.09,36)],.025,'metal')
    fireescape(-4.7,8.69,72,194,.8)
    for u in [-4.7,-1.35]:line('apartment rain pipe',[(u,8.76,235),(u,8.76,3)],.024,'metal')
    for u in [-4.5,-3.2]:cyl('chimney pot',u,2,240,.12,23,'rust')
    line('rooftop aerial mast',[(-2.3,4,240),(-2.3,4,278)],.012,'metal')
    for z in [261,271]:line('TV aerial crossbar',[(-2.7,4,z),(-1.9,4,z)],.008,'metal')
    REGIONS.append({'name':'left apartments and video rental','uv':[-5,-1,-1.2,8.7],'max_height_px':278})
    # Right service alley and low annex: kit is included in the 72px maximum.
    box('record and repair annex',15,.5,17.5,6.5,-5,58,'brownbrick');roof(15,.5,17.5,6.5,58,False)
    for v in np.arange(.9,6,.38):window('u',v,17.505,37,.25,13,True)
    box('annex faded cream fascia',15.2,6.505,17.3,6.54,39,54,'cream')
    lettering('RECORDS / REPAIRS',16.25,6.56,46,.12,m='ink')
    box('annex service door',15.3,6.51,15.8,6.55,0,34,'greenpaint')
    box('annex door lamp',15.85,6.55,15.95,6.65,26,32,'amber')
    b.point('P8 annex amber pool',xyz(15.9,6.75,29),4,(1,.53,.23),.12)
    REGIONS.append({'name':'right low annex','uv':[15,.5,17.5,6.5],'max_height_px':63,'envelope':'H <= 60*(u-13)-48'})
    box('right apartment block',18,-1,22,6.5,-5,192,'brownbrick');roof(18,-1,22,6.5,192)
    for z in [55,109,159]:
        for u in [18.5,19.35,20.2,21.05]:window('v',u,6.505,z,.48,27,RNG.random()<.7)
        for v in [0,1.2,2.4,3.6,4.8,5.9]:window('u',v,22.005,z,.45,27,RNG.random()<.6)
    tank(20.8,1.4,192,.45,47);fireescape(19.3,6.58,54,176,.9)
    REGIONS.append({'name':'right apartments','uv':[18,-1,22,6.5],'max_height_px':239,'envelope':'H <= 60*(u-13)-48'})
    # The actual billboard building, with masonry return walls and stair tower.
    box('billboard brick commercial tower',6,-5,16,-1,-8,465,'brownbrick');roof(6,-5,16,-1,465,False)
    box('concrete stairwell',14.5,-4.8,15.8,-.94,0,477,'stone')
    for z in range(55,431,54):
        for u in np.arange(6.55,14.4,.93):window('v',float(u),-.995,z,.5,31,RNG.random()<.44)
        for v in [-4.35,-3.4,-2.45,-1.5]:window('u',v,16.005,z,.43,31,RNG.random()<.46)
    fireescape(6.45,-.83,58,424,.85);tank(9,-3.4,465,.45,35)
    for u in [6.2,13.8]:line('tower downpipe',[(u,-.94,465),(u,-.94,8)],.028,'metal')
    REGIONS.append({'name':'billboard commercial tower','uv':[6,-5,16,-1],'max_height_px':500})
    # Move the inherited camera-facing billboard along its own view rays only.
    # It keeps every pixel but now occupies a real supported position in space.
    target=xyz(12.4,1,550);old=bpy.data.objects.get('Billboard black aperture')
    delta=target-old.location
    for ob in bpy.data.objects:
        if ob.name.startswith(('Billboard black aperture','Billboard heavy bezel','Billboard cyan inner rail','Billboard pink outer rail','Billboard fixing')):ob.location+=delta
    for du in [-2.5,2.5]:
        top=target+RIGHT*du-UP*1.65;u,v,z=top.x,-top.y,top.z*ZPP
        low=top-NORMAL*.45;high=target+RIGHT*du+UP*1.65-NORMAL*.45
        cv=lambda p:(p.x,-p.y,p.z*ZPP)
        line('billboard steel support',[(u,-1.05,460),cv(low),cv(high)],.065,'metal')
        line('billboard angled roof brace',[(u,-3.8,465),cv(high)],.035,'metal')
    # True dimetric distant blocks, kept behind the cinema rather than painted.
    for i in range(20):
        u=-20+i*2.1;v=-11-RNG.random()*8;w=RNG.uniform(1.3,2.5);d=RNG.uniform(2,4);h=RNG.uniform(200,520)
        box('distant solid city block',u,v,u+w,v+d,-20,h,'distantbrick',.02)
        for z in np.arange(30,h-15,44):
            for uu in np.arange(u+.3,u+w-.2,.55):
                if RNG.random()<.25:box('distant inset window',uu,v+d,uu+.13,v+d+.009,z,z+13,'dimwindow',0)
    for i in range(8):
        u=-9-RNG.random()*6;v=-3+i*1.55;h=RNG.uniform(155,290)
        box('left receding city block',u,v,u+1.9,v+1.3,-15,h,'distantbrick',.02)
    # A subtle real atmospheric volume, confined behind the action planes.
    fog=bpy.data.materials.new('P8 distant rain haze');n=fog.node_tree.nodes;n.clear();vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=.004
    vol.inputs['Color'].default_value=(.19,.23,.30,1);out=n.new('ShaderNodeOutputMaterial');fog.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume'])
    ob=b.box('P8 distant atmospheric volume',-35,-80,35,-6,-16000,3000,fog,0);ob['pass8_fog']=True

def setup():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass6.blend'));sc=bpy.context.scene
    b.GROUPS.clear();b.GROUP='background'
    old_prefix=('Clouded night sky','City masonry','Roof parapet','Distant lit window','Roof antenna','Aviation beacon','Billboard tower','Tower vertical ribs','Tower windows')
    for ob in list(bpy.data.objects):
        if ob.name.startswith(old_prefix):bpy.data.objects.remove(ob,do_unlink=True)
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(ob.get('layer','background'),[]).append(ob)
    # Restore stable illumination from the minimum saved scene; no global pulse.
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT'] and ob.data.materials:
            if ob.name.startswith(('Pink perimeter neon','Cyan low wall tube','Marquee pink tube','Billboard cyan inner rail','Billboard pink outer rail')):
                p=ob.data.materials[0].node_tree.nodes.get('Principled BSDF')
                if p:p.inputs['Emission Strength'].default_value*=8
        if ob.type=='LIGHT' and ob.name.startswith('Neon storefront reflected glow'):ob.data.energy*=10
    sc.render.use_compositing=False;sc.render.use_border=False;sc.render.use_crop_to_border=False
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.cycles.samples=32;sc.cycles.adaptive_threshold=.025;sc.render.film_transparent=False
    materials();build_city()
    for ob in NEW:ob['pass8_surrounding']=True
    return sc

def holdout(scale=1):
    # Isolated emission renders test actual visible geometry against the union
    # of protected action prisms. Occlusion is depth-tested by Cycles itself.
    sc=bpy.context.scene
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    suffix='@2x' if scale==2 else ''
    for ob in sc.objects:ob.hide_render=True
    sc.camera.hide_render=False;sc.render.film_transparent=True;sc.cycles.samples=8;sc.cycles.use_denoising=False
    sc.cycles.device='CPU';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
    white=b.material('P8 QA white',(1,1,1),emit=1);p=white.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(0,0,0,1)
    hold=bpy.data.materials.new('P8 QA holdout');n=hold.node_tree.nodes;n.clear();h=n.new('ShaderNodeHoldout');o=n.new('ShaderNodeOutputMaterial');hold.node_tree.links.new(h.outputs[0],o.inputs[0])
    prisms=[]
    for name,u0,v0,u1,v1,h in [('cinema',0,0,13,9,120),('sidewalk',-12,9.15,23,10.5,90),('road',-12,10.6,23,13.5,90)]:
        ob=b.box('P8 protected '+name,u0,v0,u1,v1,0,h,white,0);prisms.append(ob)
    render(QA/('action_volume_mask'+suffix+'.png'))
    for ob in NEW:
        ob.hide_render=False;ob.visible_camera=True
        if ob.type in ['MESH','CURVE','FONT']:ob.data.materials.clear();ob.data.materials.append(white)
    for ob in prisms:ob.data.materials.clear();ob.data.materials.append(hold)
    render(QA/('surroundings_action_holdout'+suffix+'.png'))
    def alpha(path):
        im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a);return a.reshape(h,w,4)[::-1,:,3]
    mask=alpha(QA/('action_volume_mask'+suffix+'.png'));a=alpha(QA/('surroundings_action_holdout'+suffix+'.png'))
    covered=(mask>.999)&(a>1/255);count=int(covered.sum())
    report={'passed':count==0,'protected_action_pixels':int((mask>.999).sum()),'covered_action_pixels':count,
            'method':'Independent Cycles holdout render of protected cinema 0..120px and street/sidewalk 0..90px volumes against all new solid surroundings.',
            'size':[1920*scale,1080*scale],'regions':REGIONS,'spawn_u':[-6,16.5],'protected_street_u':[-12,23],
            'threshold':'Action coverage > .999; new solid alpha > 1/255. Partial boundary pixels excluded from the hard coverage count.'}
    (QA/('surroundings_occlusion'+suffix+'.json')).write_text(json.dumps(report,indent=2))
    assert count==0,('New surroundings cover protected action pixels',count)
    status('Surroundings holdout validated: '+str(count)+' covered action pixels / '+str(report['protected_action_pixels'])+' protected pixels')

def main():
    start=time.perf_counter();QA.mkdir(exist_ok=True)
    resume='--resume' in sys.argv;relight='--lighting' in sys.argv
    scene_path=ROOT/('roxy_pass8_surroundings_lit.blend' if relight else 'roxy_pass8_surroundings.blend')
    if resume:
        bpy.ops.wm.open_mainfile(filepath=str(scene_path));sc=bpy.context.scene
        NEW.extend(ob for ob in sc.objects if ob.get('pass8_surrounding'))
        REGIONS.extend(json.loads((QA/'surroundings_regions.json').read_text()))
    else:
        sc=setup()
        if relight:
            import lighting_pass8
            lighting_pass8.apply(sc,sys.modules[__name__])
        bpy.context.view_layer.update()
        (QA/'surroundings_regions.json').write_text(json.dumps(REGIONS,indent=2))
        bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
        status('Modelled connected surroundings: opposite workshops, left apartments/video rental, auditorium block, right alley/annex/apartments, billboard tower, 3D distant city')
    gpu(sc)
    preview='preview_surroundings_2.png' if relight else 'preview_surroundings.png'
    render(QA/preview);status('Lit surroundings still rendered: qa8/'+preview)
    if relight:
        from pngio import predecode,read,write
        predecode([QA/preview]);a=read(QA/preview)[:,:,:3].astype(np.float32)
        gray=np.rint((a@np.array([.2126,.7152,.0722])).reshape(540,2,960,2).mean((1,3))).astype(np.uint8)
        write(QA/'preview_surroundings_2_gray.png',np.repeat(gray[:,:,None],3,axis=2))
        status('Downscaled grayscale surroundings preview saved for lighting readability check')
    holdout()
    (QA/'surroundings_timing.json').write_text(json.dumps({'seconds':round(time.perf_counter()-start,3)},indent=2))

if __name__=='__main__':main()
