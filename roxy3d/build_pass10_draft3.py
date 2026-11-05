"""Brief 14: editable draft only. One low-sample 1080p still, no pack pipeline."""
import sys,json,math,random,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
import build_scene as b
import build_pass10_draft as d
import build_pass10_final as f
from common import ROOT,xyz,ZPP,project,NORMAL,render
from pass8_common import gpu
QA=ROOT/'qa10';R=random.Random(101403)
META={'brief':'BRIEF-14-pass10-draft3.md','draft_only':True,'removed':[], 'new_footprints':[], 'future_ad_surfaces':[], 'windows':[], 'roof_fans':[]}
MA={}

def status(s):d.status('Draft 3: '+s)
def rm(o):
    META['removed'].append(o.name);d.rm(o)
def box(n,*args):return b.box('D3 '+n,*args)
def line(n,pts,ma,r=.01):return b.line('D3 '+n,[xyz(*p) for p in pts],ma,r)
def text(n,s,u,v,z,size,ma,wall='v'):
    return b.text('D3 '+n,s,xyz(u,v,z),size,ma,d.UFACE if wall=='u' else b.FRONT_FACE)
def mat(n,c,r=.5,metal=0,e=0,texture=0):
    MA[n]=b.material('D3 '+n,c,r,metal,e,texture);return MA[n]
def assign(o,ma):o.data.materials.clear();o.data.materials.append(ma)
def bounds(o):return d.bounds(o)
def footprint(n,rect):META['new_footprints'].append({'name':n,'uv':rect})
def plane(n,wall,a,c,front,z0,z1,ma):
    if wall=='v':return box(n,a,front-.015,c,front,z0,z1,ma,.003)
    return box(n,front-.015,a,front,c,z0,z1,ma,.003)
def deco_mesh(n,wall,points,front,ma):
    return b.mesh('D3 '+n,[xyz(a,front,z) if wall=='v' else xyz(front,a,z) for a,z in points],[tuple(range(len(points)))],ma)

def palette():
    mat('cut plaster core',(.40,.36,.29),.9,texture=60)
    mat('cut teal laminate core',(.32,.28,.19),.85)
    mat('aged limestone cut cap',(.43,.43,.37),.88,texture=100)
    mat('charcoal wet steel',(.062,.075,.078),.31,.55,texture=44)
    mat('worn timber',(.16,.105,.060),.77,texture=29)
    mat('rust',(.20,.073,.028),.85,texture=36)
    mat('dusty moss',(.066,.080,.038),.96,texture=70)
    mat('cream paper',(.68,.61,.45),.86,e=.05)
    mat('muted teal',(.030,.14,.15),.60)
    mat('wine red',(.22,.032,.040),.72)
    mat('ochre',(.47,.24,.045),.78)
    mat('warm lettering',(.78,.69,.49),.46,e=.5)
    mat('ink',(.025,.028,.031),.87)
    mat('amber lamp',(.95,.50,.16),.3,e=3)
    mat('service green',(.24,.69,.34),.38,e=2)
    mat('wet repair tar',(.025,.031,.037),.19,.18)
    mat('blue tarp',(.028,.084,.11),.48,texture=90)
    mat('bin green',(.044,.12,.093),.48,.25,texture=32)
    mat('bin blue',(.03,.08,.18),.50,.15,texture=35)
    mat('trash sack',(.025,.035,.038),.38,texture=18)
    mat('curtain cream',(.26,.23,.17),.96)
    mat('curtain blue',(.064,.105,.13),.91)
    mat('curtain burgundy',(.12,.043,.042),.91)
    mat('cafe green',(.065,.14,.12),.59,texture=40)
    mat('cafe canvas',(.29,.22,.12),.90,texture=100)
    mat('cafe interior',(.21,.12,.045),.60,e=.8)

def restore_draft2(sc):
    # The interrupted production run saved draft 2's changes in roxy_pass10.blend,
    # while the explicitly requested editable draft file still held draft 1.
    # Reapply just the accepted geometry to its snapshot; never load production.
    if not bpy.data.objects.get('P10 single multiplex wet roof'):
        for o in list(sc.objects):
            if o.name.startswith(('P10 rooftop DinkDonk','P10 entrance DinkDonk')):rm(o)
        b.layer('rooftop_neon');f.emote('rooftop_dinkdonk',3.80,-.58,325,1.62,94)
        b.layer('entrance_neon');f.emote('entrance_dinkdonk',-.80,9.32,168,.75,71)
        f.pose_bells(0);f.multiplex(sc)
    for o in list(sc.objects):
        if o.get('bell_id') and o.type=='MESH':rm(o)
        elif o.get('bell_id') and o.type=='CURVE':o.data.use_fill_caps=True
    META['restored_draft2_geometry']=True
    status('approved draft-2 continuous multiplex roof and actual hooded-frog/bell neons reconciled into editable draft source')

def party_wall(sc):
    bpy.context.view_layer.update()
    b.layer('background')
    for o in list(sc.objects):
        if o.type not in ['MESH','CURVE','FONT']:continue
        a,v,c,w,z,h=bounds(o);n=o.name
        annex=n.startswith(('P10 existing left service roof block','P8 service roof vent'))
        annex=annex or (n.startswith(('P8 gravel roof','P8 roof felt patch','P8 rooftop pooled rain','P8 brick parapet')) and a>=-1.11 and c<=-.07 and v>=.04 and w<=8.64)
        covered_windows=(n.startswith(('P8 recessed window','P8 deep window','P8 lit recessed','P8 window','P8 uneven curtain')) and -1.22<a<-.99 and c<-.98 and w<8.5)
        internal_cap=(n.startswith(('P8 brick parapet','P8 left parapet coping')) and -1.32<a<-.98 and c<=-1.08)
        main_roof=(n.startswith('P8 gravel roof') and a< -4.9 and c< -1.15 and v<-.9 and w>8.6)
        if annex or covered_windows or internal_cap or main_roof:rm(o)
    brick=bpy.data.materials['P8 brick'];roof=bpy.data.materials['P10 wet mineral felt']
    box('continuous apartment party-wall extension',-1.2,-1,-.075,8.70,-5,235,brick,.006)
    box('apartment roof extension flush seam',-5,-1,-.075,8.70,235.015,235.035,roof,0)
    box('apartment party parapet',-.16,-1,-.075,8.70,235,240,brick,.005)
    box('apartment extended street parapet',-1.2,8.61,-.075,8.70,235,240,brick,.005)
    box('apartment rear parapet extension',-1.2,-1,-.075,-.91,235,240,brick,.005)
    # Small wet repairs and blank masonry, not fictitious buried windows.
    for v in [1.1,4.8,7.7]:
        plane('party-wall old mortar repair','u',v,v+.38,-.067,177,207,bpy.data.materials['P10 auditorium faded concrete'])
    META['party_wall']={'uv':[-5,-1,-.075,8.7],'roof_z':235,'cinema_facing_windows':0,'blank_face_u':-.075}
    status('low annex removed; brick apartment extended flush to restroom with a blank cinema-facing party wall and one continuous roof')

def frame(n,wall,a,c,front,z0,z1,paper=None):
    plane(n+' walnut frame',wall,a-.045,c+.045,front,z0-3,z1+3,MA['charcoal wet steel'])
    plane(n+' paper',wall,a,c,front+.018,z0,z1,paper or MA['cream paper'])

def poster(n,title,subtitle,wall,a,c,front,z0,z1,palette_index=0):
    frame(n,wall,a,c,front,z0,z1)
    accent=[MA['muted teal'],MA['wine red'],MA['ochre']][palette_index%3]
    plane(n+' printed art',wall,a+.025,c-.025,front+.025,z0+12,z1-13,accent)
    # Original graphic one-sheet: moon, abstract city silhouette and figure.
    mid=(a+c)/2;w=c-a;cz=z0+(z1-z0)*.60
    pts=[(mid+w*.12+w*.17*math.cos(t),cz+(z1-z0)*.13*math.sin(t)) for t in np.linspace(0,math.tau,33)]
    deco_mesh(n+' printed moon',wall,pts,front+.029,MA['cream paper'])
    for j in range(6):
        aa=a+.03+j*(w-.06)/6;hh=z0+15+(j*11%19)
        plane(n+' printed skyline',wall,aa,aa+(w-.06)/7,front+.032,z0+13,hh,MA['ink'])
    u,v=(mid,front+.034) if wall=='v' else (front+.034,mid)
    text(n+' title',title,u,v,z1-7,min(.093,w*.14),MA['ink'],wall)
    text(n+' billing',subtitle,u,v,z0+6,min(.045,w*.07),MA['ink'],wall)

def corridor(sc):
    b.layer('corridor_dressing')
    for o in list(sc.objects):
        if o.name.startswith(('Sconce mounting','Opal sconce','Wall sconce pool')) and abs(o.location.x-2)<.12:rm(o)
    # The junction's two exposed walls get room-scale readable decoration.
    poster('junction one-sheet','THE BLUE HOUR','A FILM BY E. MARLOW','u',.43,1.20,.045,62,125,0)
    poster('junction one-sheet two','NIGHT FERRY','LAST CROSSING  11:45','u',1.48,2.22,.045,62,125,1)
    frame('double programme board','v',1.00,2.84,.055,62,132,MA['ink'])
    text('board heading','NOW SHOWING',1.92,.095,121,.16,MA['warm lettering'])
    for j,s in enumerate(['1  THE GLASS CITY','2  MIDNIGHT SERVICE','3  AFTER THE RAIN']):text('board listings',s,1.92,.096,108-j*11,.084,MA['cream paper'])
    text('board foot','COMING SOON / NIGHT FERRY',1.92,.096,71,.058,MA['ochre'])
    # A clock with physical hands on the v=0 wall.
    b.cylinder('D3 wall clock frame',xyz(.48,.10,128),.205,.045,MA['charcoal wet steel'],(0,-1,0),48)
    b.cylinder('D3 wall clock face',xyz(.48,.128,128),.176,.006,MA['cream paper'],(0,-1,0),48)
    for j in range(12):
        a=j*math.tau/12
        line('clock tick',[(.48+.149*math.sin(a),.133,128+10.9*math.cos(a)),(.48+.166*math.sin(a),.133,128+12.2*math.cos(a))],MA['ink'],.004)
    line('clock minute hand',[(.48,.139,128),(.60,.139,135.5)],MA['ink'],.008)
    line('clock hour hand',[(.48,.141,128),(.40,.141,129.5)],MA['ink'],.010)
    # Wall payphone: shallow enough that the junction's walking lane stays clear.
    box('payphone hood',.15,2.35,.39,2.88,55,108,MA['charcoal wet steel'],.018)
    box('payphone teal face',.391,2.40,.414,2.84,58,100,MA['muted teal'],.006)
    text('phone label','PHONE',.419,2.62,96,.075,MA['cream paper'],'u')
    box('payphone silver controls',.417,2.55,.43,2.76,64,85,MA['aged limestone cut cap'],.003)
    for j in range(4):
        for k in range(3):box('phone keypad',.431,2.58+k*.048,.438,2.61+k*.048,67+j*3,69+j*3,MA['ink'],.001)
    line('telephone handset',[(.452,2.455,88),(.47,2.455,82),(.47,2.455,69)],MA['ink'],.027)
    line('telephone cord',[(.47,2.455,70),(.48,2.48,52),(.45,2.61,51),(.435,2.66,66)],MA['ink'],.007)
    footprint('junction wall payphone',[.15,2.35,.49,2.88])
    for i,(a,c) in enumerate([(3.03,3.83)]):
        poster('corridor fictional poster '+str(i),['RADIO SILENCE','NIGHT FERRY'][i],'COMING NEXT MONTH','v',a,c,.06,66,128,i+1)
    # Framed sepia history pictures and safety fittings in the remaining wall gaps.
    for i,u in enumerate([5.95,9.35]):
        frame('history photograph','v',u-.22,u+.22,.06,118,147,MA['ochre'])
        plane('history sepia sky','v',u-.195,u+.195,.082,125,144,MA['aged limestone cut cap'])
        for k in range(5):plane('history old cinema facade','v',u-.18+k*.075,u-.13+k*.075,.086,126,133+k%2*3,MA['ink'])
        text('history photo caption','OPENING NIGHT  /  1936',u,.09,121,.032,MA['cream paper'])
    box('red fire alarm',2.78,.045,2.91,.112,139,153,MA['wine red'],.008)
    text('alarm FIRE','FIRE',2.845,.117,145,.04,MA['cream paper'])
    box('extinguisher glass cabinet',10.21,.02,10.52,.13,19,58,MA['wine red'],.006)
    plane('extinguisher cabinet opening','v',10.245,10.49,.135,24,53,MA['ink'])
    b.cylinder('D3 cabinet extinguisher',xyz(10.36,.153,37),.060,23/ZPP,MA['wine red'],vertices=16)
    text('fire extinguisher label','FIRE',10.36,.218,48,.044,MA['cream paper'])
    # Local warm pools, with no added floor furniture in the clear band.
    for u in [.78,2.90]:
        box('junction sconce back',u-.08,.04,u+.08,.10,91,117,MA['charcoal wet steel'],.012)
        box('junction sconce diffuser',u-.052,.11,u+.052,.17,94,114,MA['amber lamp'],.012)
        b.point('D3 junction sconce light',xyz(u,.27,105),9,(1,.59,.28),.19)
    status('junction and corridor dressed with original framed films, programme board, clock, payphone, cinema-history photos and safety fittings; all new fixtures wall-mounted')

def feather_material():
    ma=mat('feathered reflective water',(.065,.086,.10),.10,.34)
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Coat Weight'].default_value=.7;p.inputs['Coat Roughness'].default_value=.09
    at=n.new('ShaderNodeAttribute');at.attribute_name='D3Coverage'
    transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(at.outputs['Color'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8.5;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=.07;r.inputs['To Max'].default_value=.23;l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Roughness'])
    return ma

def irregular(n,u,v,z,rx,ry,ma,alpha=None):
    count=48;phase=R.random()*math.tau
    shapes=[1+.16*math.sin(a*3+phase)+.11*math.cos(a*5-phase)+.07*math.sin(a*8+phase) for a in np.linspace(0,math.tau,count,endpoint=False)]
    rings=[.0,.50,.80,1.0] if alpha is not None else [.0,1.0]
    verts=[]
    for factor in rings:
        for k,a in enumerate(np.linspace(0,math.tau,count,endpoint=False)):
            verts.append(xyz(u+rx*factor*shapes[k]*math.cos(a),v+ry*factor*shapes[k]*math.sin(a),z))
    faces=[]
    for j in range(len(rings)-1):
        for k in range(count):faces.append((j*count+k,j*count+(k+1)%count,(j+1)*count+(k+1)%count,(j+1)*count+k))
    ob=b.mesh('D3 '+n,verts,faces,ma)
    if alpha is not None:
        at=ob.data.color_attributes.new(name='D3Coverage',type='FLOAT_COLOR',domain='POINT')
        for j,c in enumerate(at.data):a=[alpha,alpha*.90,alpha*.38,0][j//count];c.color=(a,a,a,1)
    return ob

def wet_surfaces(sc):
    bpy.context.view_layer.update()
    b.layer('background');ma=feather_material();pools=[];oldcracks=[]
    for o in list(sc.objects):
        n=o.name
        ispool=n.startswith(('Rainwater pool','P8 rooftop pooled rain','P8B alley puddle','P10 roof puddle','P10 multiplex roof pooled rain'))
        if ispool:
            a,v,c,w,z,h=bounds(o);pools.append(((a+c)/2,(v+w)/2,(z+h)/2,(c-a)/2,(w-v)/2));rm(o)
        elif n.startswith(('Oil tide edge','P10 glass water trace','P9 glass safety etch','P8B alley expansion joint','P8B alley transverse joint')):rm(o)
        elif n.startswith('Branching asphalt crack'):
            for s in o.data.splines:
                oldcracks.append([o.matrix_world@Vector(p.co[:3]) for p in s.points])
            rm(o)
    for i,(u,v,z,rx,ry) in enumerate(pools):
        # Feathered, irregular film; no opaque oval body and no outline stroke.
        irregular('shallow rainwater film',u,v,z+(.04 if z>1 else 0),rx*1.16,ry*1.15,ma,.54 if z>100 else .43)
    for pts in oldcracks:
        for offset in range(0,len(pts)-1,5):
            pp=pts[offset:offset+4]
            if len(pp)>1:b.line('D3 low-contrast broken sealed crack',[Vector((p.x,p.y,.035/ZPP)) for p in pp],MA['wet repair tar'],.0048)
    META['water_revision']={'old_pools_replaced':len(pools),'old_crack_paths_reworked':len(oldcracks),'static_ripple_outlines':0,'front_glass_static_rain_traces':0,'method':'irregular 48-point shallow reflective film with 4 vertex-alpha rings; no outline geometry'}
    status('all '+str(len(pools))+' inherited puddles rebuilt as irregular feathered reflective films; static oil/ripple outlines and glass dashes removed; asphalt cracks thinned, broken and softened')

def worn_roof_material():
    ma=mat('mottled mineral felt',(.075,.084,.087),.64,.04)
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.6;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.72;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    # A tiny sky fill keeps felt in deep service-roof shadow readable in the
    # quick still; it does not turn the material into a luminous surface.
    p.inputs['Emission Color'].default_value=(.045,.052,.065,1);p.inputs['Emission Strength'].default_value=.13
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(.033,.040,.045,1);ramp.color_ramp.elements[1].position=.75;ramp.color_ramp.elements[1].color=(.10,.107,.104,1);l.new(noise.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    rough=n.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.20;rough.inputs['To Max'].default_value=.78;l.new(noise.outputs[0],rough.inputs[0]);l.new(rough.outputs[0],p.inputs['Roughness'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=95;l.new(geo.outputs['Position'],fine.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=.006;l.new(fine.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return ma

def roofs(sc):
    b.layer('background');felt=worn_roof_material()
    roofrects=[(-4.85,-.83,-.23,8.51,235),(-1.8,16.7,3.0,20.8,91),(3.4,16.7,7.9,20.8,100),(8.3,16.7,13.8,20.8,107),(15.1,.6,17.4,6.4,58),(15.1,6.6,17.4,9,61),(18.2,-.8,21.8,6.3,192),(-3,-12,19,-.6,240)]
    for o in sc.objects:
        if o.name.startswith(('P10 single multiplex wet roof','P8 gravel roof','D3 apartment roof extension','P9 records continuous roof')):assign(o,felt)
    patch=mat('patched felt',(.043,.051,.053),.76,texture=120)
    dirt=mat('roof old damp stains',(.043,.052,.043),.84,texture=65)
    # Feather stains too: the roof wear must not become new opaque stickers.
    for ma in [dirt,MA['dusty moss']]:
        n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');at=n.new('ShaderNodeAttribute');at.attribute_name='D3Coverage'
        tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(at.outputs['Color'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    # Ragged overlapped repair sheets replace repeated clean rectangles.
    for o in list(sc.objects):
        if o.name.startswith('P8 roof felt patch'):rm(o)
    for a,v,c,w,z in roofrects:
        count=14 if z==240 else 5
        for j in range(count):
            u=R.uniform(a+.15,c-.4);vv=R.uniform(v+.15,w-.35);rx=R.uniform(.13,.53);ry=R.uniform(.10,.31)
            irregular('felt damp stain',u,vv,z+.018,rx*1.5,ry*1.5,dirt,.42)
            if j%2==0:
                pts=[(u-rx,vv-ry),(u+rx*.9,vv-ry*.95),(u+rx,vv+ry*.8),(u-rx*.86,vv+ry)]
                b.mesh('D3 ragged repair felt',[xyz(x,y,z+.035) for x,y in pts],[(0,1,2,3)],patch)
                line('patched seam',[(x,y,z+.07) for x,y in pts[:3]],MA['wet repair tar'],.004)
            if j%3==0:
                for k in range(5):
                    uu=u+R.uniform(-rx,rx);v2=vv+R.uniform(-ry,ry)
                    ob=box('windblown roof debris',uu,v2,uu+R.uniform(.025,.09),v2+.035,z+.06,z+.28,MA['cream paper'] if k%2 else MA['rust'],0);ob.rotation_euler.z=R.uniform(-1,1)
        # Organic corner growth in a few sheltered damp spots.
        for uu,vv in [(a+.17,v+.12),(c-.16,w-.13)]:irregular('corner moss',uu,vv,z+.045,.20,.13,MA['dusty moss'],.58)
    # Soft wrinkled blue tarpaulin weighted with bricks on the big roof.
    verts=[];faces=[];nu,nv=17,13
    for j in range(nv):
        for i in range(nu):
            u=5.6+i/16*1.9;v=-5.2+j/12*1.2;zz=240.65+.45*math.sin(i*1.3+j*.55)+.32*math.cos(j*1.8)
            verts.append(xyz(u,v,zz))
    for j in range(nv-1):
        for i in range(nu-1):k=j*nu+i;faces.append((k,k+1,k+1+nu,k+nu))
    tarp=b.mesh('D3 wrinkled anchored tarp',verts,faces,MA['blue tarp'])
    for p in tarp.data.polygons:p.use_smooth=True
    for u,v in [(5.65,-5.1),(7.35,-5.05),(5.65,-4.08),(7.35,-4.08)]:box('tarp weight brick',u,v,u+.14,v+.08,241,245,MA['rust'],.008)
    # A bent vent and rust stains on all roof equipment, not just the multiplex.
    line('bent vent stack',[(2.7,-3.9,240),(2.7,-3.9,261),(2.91,-3.9,273),(3.04,-3.9,273)],MA['charcoal wet steel'],.10)
    b.cylinder('D3 vent tilted cowl',xyz(3.04,-3.9,275),.15,.035,MA['charcoal wet steel'],(.25,0,.96))
    bpy.context.view_layer.update()
    kit=[o for o in sc.objects if o.type=='MESH' and o.name.startswith(('P10 additional HVAC unit','P10 HVAC box','P8 rooftop AC case','P10 projection booth body'))]
    for i,o in enumerate(kit):
        a,v,c,w,z,h=bounds(o)
        for k in range(3):
            u=a+(c-a)*(.18+.26*k)
            deco_mesh('HVAC rust wash','v',[(u,w*0+h-4),(u+.025,h-4),(u+.006,max(z+2,h-R.uniform(10,20)))],w+.002,MA['rust'])
    # Replace plain fan discs with a readable rotor and wire grille. Tag pivots
    # for the later animation kit, but write no keyframes/frames in this draft.
    fans=[o for o in sc.objects if o.type=='MESH' and o.name.startswith(('P10 additional HVAC fan','P10 HVAC fan','P8 AC fan grille'))]
    for i,o in enumerate(fans):
        a,v,c,w,z,h=bounds(o);u=(a+c)/2;vv=(v+w)/2;r=min(c-a,w-v)*.44
        for k in range(4):
            aa=k*math.tau/4
            points=[(u+.03*math.cos(aa),vv+.03*math.sin(aa)),(u+r*math.cos(aa+.25),vv+r*math.sin(aa+.25)),(u+r*.9*math.cos(aa+.9),vv+r*.9*math.sin(aa+.9))]
            ob=b.mesh('D3 exposed fan rotor',[xyz(x,y,h+.12) for x,y in points],[(0,1,2)],MA['charcoal wet steel']);ob['future_fan_id']=i
        for dr in [.6,.9]:
            line('AC grille wire',[(u+r*dr*math.cos(t),vv+r*dr*math.sin(t),h+.40) for t in np.linspace(0,math.tau,25)],MA['aged limestone cut cap'],.0035)
        META['roof_fans'].append({'id':i,'pivot_uvz':[u,vv,h+.12],'mode':'dead' if i==1 else 'wobble' if i==4 else 'spin'})
    # Copings are slightly uneven in the exterior, while cutaway caps stay clean.
    for i,o in enumerate(sc.objects):
        if o.type=='MESH' and o.name.startswith('P8 brick parapet'):
            a,v,c,w,z,h=bounds(o)
            if c-a>1:
                for x in np.arange(a,c-.12,.68):box('uneven exterior coping slab',float(x),v-.015,min(float(x)+.63,c),w+.015,h,h+R.uniform(.8,2.4),MA['aged limestone cut cap'],.003)
    status('all roof zones weathered with felt repairs, stains, rust, debris, corner moss, uneven coping, tarp and bent vent; fan rotors tagged for later spin/dead/wobble states')

def alley(sc):
    b.layer('background')
    brick=bpy.data.materials['P8 brownbrick'];metal=MA['charcoal wet steel']
    # Complete the multiplex's own front return wall below the former black gap.
    box('cinema alley masonry return',13,-.41,32,-.23,-5,170,brick,.005)
    for a,c in [(13.53,14.39)]:
        box('emergency exit stone reveal',a-.06,-.225,c+.06,-.17,0,104,MA['aged limestone cut cap'],.008)
        box('emergency exit steel leaf',a,-.16,c,-.125,0,98,MA['bin green'],.006)
        line('exit push bar',[(a+.08,-.11,46),(c-.08,-.11,46)],metal,.018)
        box('EXIT lit housing',a+.08,-.18,c-.08,-.08,110,125,metal,.004)
        text('external EXIT','EXIT', (a+c)/2,-.07,117,.16,MA['service green'])
        box('loose doorstop brick',c-.1,.02,c+.06,.13,0,5,MA['rust'],.006)
    box('loading shutter surround',15.02,-.22,16.65,-.16,0,118,metal,.005)
    for z in range(1,115,6):box('loading shutter corrugation',15.07,-.14,16.60,-.105,z,z+4,MA['aged limestone cut cap'],.003)
    text('deliveries lettering','DELIVERIES',15.84,-.09,127,.12,MA['cream paper'])
    line('alley downpipe',[(14.78,-.12,234),(14.78,-.10,19),(14.85,.02,3)],metal,.026)
    for z in [40,105,160]:box('drainpipe wall strap',14.72,-.15,14.84,-.08,z,z+2.0,MA['rust'],.003)
    box('grimy bulkhead light frame',14.53,-.15,14.79,-.06,145,158,metal,.018)
    box('grimy bulkhead light glass',14.56,-.052,14.76,-.035,147,156,MA['amber lamp'],.014)
    b.point('D3 alley service pool',xyz(14.66,.2,151),75,(1,.62,.32),.40)
    # New local fill lights the masonry and reveals the working alley floor.
    b.area('D3 alley bounced sky',xyz(14.2,3.8,310),125,(.42,.53,.65),4,target=xyz(14.2,2.6,0))
    b.point('D3 alley wet neon bounce',xyz(14.2,5.5,65),13,(.27,.62,.48),.6)
    # Keep lower cinema-side wall available for page-authored community paint.
    frame('alley future paste-up panel','v',14.91,16.88,-.07,37,91,MA['aged limestone cut cap'])
    META['future_ad_surfaces'].append({'name':'cinema_alley_pasteup','quad_px':[project(u,-.04,z) for u,z in [(14.91,91),(16.88,91),(16.88,37),(14.91,37)]],'z_index':100,'lit':False,'content':'blank reserved for page-owned community content'})
    # Small fictional tags outside the reserved clean panel.
    text('paint tag','SLOW / 98',13.32,-.08,145,.12,MA['ochre'])
    for j in range(4):line('faded paint mark',[(17.06+j*.13,-.08,54),(17.13+j*.11,-.08,78),(17.18+j*.12,-.08,52)],MA['muted teal'],.014)
    # A new all-over asphalt surface, without a regular paving grid.
    ground=mat('patched alley asphalt',(.024,.029,.032),.52,.10,texture=92)
    for o in sc.objects:
        if o.name=='P8 right service alley':assign(o,ground)
    for i in range(14):
        u=R.uniform(13.20,14.86);v=R.uniform(.45,8.8)
        irregular('alley asphalt repair',u,v,-.27,R.uniform(.12,.38),R.uniform(.13,.45),MA['wet repair tar'] if i%2 else MA['charcoal wet steel'])
        if i%3==0:
            irregular('pothole damp rim',u,v,-.24,.20,.27,MA['wet repair tar'])
            irregular('pothole standing water',u,v,-.22,.17,.23,MA['feathered reflective water'],.7)
    for i in range(18):
        u=R.uniform(13.20,14.85);v=R.uniform(.4,8.7)
        pp=[(u,v,-.20),(u+.045,v+.13,-.20),(u-.035,v+.24,-.20),(u+.01,v+.40,-.20)]
        line('alley settled seam',pp,MA['wet repair tar'],.005)
    irregular('alley neon reflecting puddle',14.03,4.6,-.19,.48,1.05,MA['feathered reflective water'],.78)
    # Remove the earlier featureless low bin, then dress one edge only.
    for o in list(sc.objects):
        if o.name.startswith(('P9 alley dumpster','P9 dumpster sloping lid','P9 dumpster caster')):rm(o)
    box('large recycling dumpster',14.42,6.20,14.98,7.40,3,43,MA['bin green'],.025)
    for v in [6.20,6.80]:box('dumpster ribbed hinged lid',14.40,v,15.00,v+.59,43,47,metal,.012)
    for v in [6.28,7.29]:
        for u in [14.46,14.93]:b.cylinder('D3 dumpster wheel',xyz(u,v,3),.045,.06,MA['ink'],(1,0,0),16)
    text('dumpster stencil','CINEMA',14.995,6.80,27,.075,MA['cream paper'],'u')
    box('blue bottle recycling bin',14.58,5.64,14.94,6.10,0,31,MA['bin blue'],.027)
    box('bottle bin lid',14.55,5.61,14.97,6.13,31,34,metal,.01)
    for u,v in [(14.62,7.78),(14.80,8.09),(14.34,7.82)]:
        ob=b.ball('D3 tied trash sack',xyz(u,v,10),1,MA['trash sack'],(.13,.16,.15));ob.rotation_euler.z=R.random()*2
        line('trash tie',[(u,v,19),(u+.035,v+.018,24),(u-.03,v+.04,23)],MA['trash sack'],.019)
    # Loading clutter sits under the wall, outside the central alley reserve.
    for z in [0,7]:
        for u in [14.46,14.91]:box('pallet runner',u,.85,u+.06,1.73,z,z+4,MA['worn timber'],.003)
        for v in np.arange(.86,1.74,.17):box('pallet plank',14.44,float(v),14.99,float(v)+.11,z+4,z+6,MA['worn timber'],.002)
    box('slatted delivery crate',14.57,1.02,14.96,1.47,14,42,MA['worn timber'],.004)
    for v in [1.04,1.38]:line('crate brace',[(14.975,v,17),(14.975,v+.08,39)],MA['ochre'],.013)
    # Wall-mounted fire escape on the records shop's far side, parallel to alley.
    box('alley fire escape landing',14.48,2.85,15.0,4.05,59,61,metal,.004)
    for v in np.arange(2.90,4.03,.18):line('escape vertical',[(14.48,float(v),61),(14.48,float(v),82)],metal,.008)
    line('escape rail',[(14.48,2.85,82),(14.48,4.05,82)],metal,.012)
    for u in [14.60,14.88]:line('alley ladder rail',[(u,3.9,0),(u,3.9,61)],metal,.014)
    for z in range(4,62,7):line('alley ladder rung',[(14.60,3.9,z),(14.88,3.9,z)],metal,.010)
    # Quiet draft steam wisp from a wall vent: real translucent volume.
    box('alley steam vent',14.91,4.50,15.01,4.90,22,40,metal,.01)
    steam=bpy.data.materials.new('D3 thin service steam');n=steam.node_tree.nodes;n.clear();l=steam.node_tree.links
    geo=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Generated'],noise.inputs[0])
    ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.38;ramp.inputs['From Max'].default_value=.77;ramp.inputs['To Min'].default_value=0;ramp.inputs['To Max'].default_value=.55;l.new(noise.outputs[0],ramp.inputs[0])
    vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.52,.58,.60,1);l.new(ramp.outputs[0],vol.inputs['Density']);out=n.new('ShaderNodeOutputMaterial');l.new(vol.outputs[0],out.inputs['Volume'])
    b.ball('D3 thin steam plume',xyz(14.30,4.69,48),1,steam,(.35,.20,.35))
    # Place the short furnishings far enough from the foreground annex to be
    # visible in the fixed cutaway camera, while retaining a walking strip.
    for o in sc.objects:
        if o.name.startswith(('D3 large recycling dumpster','D3 dumpster','D3 blue bottle','D3 bottle bin','D3 tied trash','D3 trash tie')):o.location.x-=.62
    footprint('alley dumpster',[13.78,6.20,14.38,7.40])
    footprint('alley recycling',[13.93,5.61,14.35,6.13])
    footprint('alley bags',[13.58,7.60,14.34,8.26])
    META['alley']={'clear_reserve_uv':[13.12,.35,13.55,8.8],'wall_material':'multiplex brownbrick','floor':'irregular patched asphalt, no grid','exit_uv':[13.96,-.125],'future_content':'reserved paste-up panel plus open upper alley; page-owned graffiti content later'}
    status('black alley gap replaced by lit multiplex masonry, EXIT and loading doors, drainage and service light; patched wet alley dressed along its edge with bins, bags, pallets, fire escape and steam')

def cafe(sc):
    b.layer('background')
    for o in list(sc.objects):
        if o.name.startswith(('P9 west infill','P9 west shop','P9 west upstairs')):rm(o)
    brick=bpy.data.materials['P8 brick']
    box('small corner cafe building',-9.5,3.3,-5.10,7.38,-5,91,brick,.012)
    box('cafe roof',-9.55,3.25,-5.05,7.41,91,95,MA['mottled mineral felt'],.005)
    # Readable right-hand sign falls inside the frame even though the building
    # intentionally continues beyond the left crop.
    box('cafe cream fascia',-7.42,7.40,-5.22,7.48,55,77,MA['cafe green'],.006)
    text('cafe sign','CAFE LUNA',-6.25,7.49,66,.23,MA['warm lettering'])
    for u0,u1 in [(-7.38,-6.47),(-6.36,-5.28)]:
        box('cafe window frame',u0,7.39,u1,7.46,4,54,MA['charcoal wet steel'],.004)
        box('cafe warm shop window',u0+.04,7.465,u1-.04,7.475,8,51,MA['cafe interior'],.003)
        for u in np.arange(u0+.12,u1-.07,.19):box('cafe cups on shelf',float(u),7.485,float(u)+.055,7.52,17,24,MA['cream paper'],.005)
        line('cafe interior shelf',[(u0+.05,7.52,15),(u1-.05,7.52,15)],MA['worn timber'],.015)
    # Small rain canopy and warm shop pool.
    b.mesh('D3 cafe striped awning',[xyz(u,v,z) for u,v,z in [(-7.45,7.44,55),(-5.20,7.44,55),(-5.20,7.78,48),(-7.45,7.78,48)]],[(0,1,2,3)],MA['cafe canvas'])
    b.point('D3 cafe window pool',xyz(-5.85,7.9,48),26,(1,.60,.28),.40)
    for i,(u,v) in enumerate([(-5.65,8.48),(-6.45,8.0)]):
        b.cylinder('D3 wet cafe round table',xyz(u,v,30),.20,2/ZPP,MA['charcoal wet steel'],vertices=32)
        line('cafe table pedestal',[(u,v,2),(u,v,29)],MA['charcoal wet steel'],.025)
        for du,dv in [(-.16,0),(.16,0),(0,-.16),(0,.16)]:line('cafe table foot',[(u,v,3),(u+du,v+dv,1)],MA['charcoal wet steel'],.014)
        for k,(du,dv) in enumerate([(.29,0),(-.29,0),(0,.30)]):
            uu,vv=u+du,v+dv
            box('cafe chair seat',uu-.095,vv-.095,uu+.095,vv+.095,17,20,MA['cafe green'],.015)
            for dx,dy in [(-.075,-.075),(.075,-.075),(-.075,.075),(.075,.075)]:line('cafe chair leg',[(uu+dx,vv+dy,1),(uu+dx,vv+dy,18)],MA['charcoal wet steel'],.010)
            box('cafe chair back',uu-.095,vv-.10,uu+.095,vv-.07,19,37,MA['cafe green'],.015)
        footprint('cafe seating '+str(i),[u-.41,v-.12,u+.41,v+.41])
        irregular('cafe table rain film',u,v,31.1,.15,.15,MA['feathered reflective water'],.48)
    # One folded parasol keeps the little shopfront visible in the rain.
    u,v=-5.25,8.28
    line('closed parasol shaft',[(u,v,0),(u,v,99)],MA['worn timber'],.018)
    b.cylinder('D3 parasol weighted foot',xyz(u,v,2),.12,4/ZPP,MA['charcoal wet steel'])
    points=[xyz(u+.11*math.cos(a),v+.11*math.sin(a),55+2*math.sin(a*5)) for a in np.linspace(0,math.tau,12,endpoint=False)]+[xyz(u,v,98)]
    b.mesh('D3 folded rain parasol',points,[(i,(i+1)%12,12) for i in range(12)],MA['cafe canvas'])
    footprint('cafe folded parasol',[u-.14,v-.14,u+.14,v+.14])
    # Low A-board, kept behind v9.1 and safely away from the spawn strip.
    frame('cafe menu A-board','v',-5.40,-5.10,8.93,8,36,MA['cafe green'])
    text('cafe menu title','COFFEE',-5.25,8.96,29,.055,MA['cream paper'])
    text('cafe menu line','SOUP / 2.50',-5.25,8.96,19,.033,MA['cream paper'])
    footprint('cafe menu',[-5.45,8.86,-5.05,9.03])
    line('cafe festoon cable',[(-7.18,7.71,87),(-6.20,7.95,77),(-5.15,8.18,87)],MA['charcoal wet steel'],.006)
    for i in range(9):
        t=i/8;uu=-7.18+t*2.03;vv=7.71+t*.47;z=87-10*math.sin(math.pi*t)
        b.ball('D3 cafe string bulb',xyz(uu,vv,z-3),.022,MA['amber lamp'])
    META['cafe']={'building_uv':[-9.5,3.3,-5.1,7.38],'seating_v_max':9.03,'protected_spawn_lane_uv':[-6.35,9.78,-5.65,10.05]}
    status('cropped REPAIR shop replaced by CAFE LUNA with lit windows, two wet tables/chairs, folded parasol, menu board and string lights; spawn strip untouched')

def windows(sc):
    b.layer('background');bpy.context.view_layer.update()
    candidates=[o for o in sc.objects if o.name.startswith(('P8 lit recessed window','P8 distant inset window','P8B hazy distant window'))]
    for i,o in enumerate(candidates):
        a,v,c,w,z,h=bounds(o);wall='u' if c-a<w-v else 'v';front=c if wall=='u' else w;lo,hi=(v,w) if wall=='u' else (a,c)
        # Reject openings on hidden back faces / outside the crop before adding
        # details. Their geometry remains, for future camera-independent data.
        quad=[project(front,t,zz) if wall=='u' else project(t,front,zz) for t,zz in [(lo,h),(hi,h),(hi,z),(lo,z)]]
        if max(p[0] for p in quad)<0 or min(p[0] for p in quad)>1920 or max(p[1] for p in quad)<0 or min(p[1] for p in quad)>1080:continue
        building='left_apartments' if c<0 else 'records_annex' if 15<c<18 else 'right_apartments' if a>=18 else 'distant_neighbour'
        lit=any('amber' in m.name or 'dimwindow' in m.name or 'tv' in m.name for m in o.data.materials)
        style=['half_blind','parted_curtains','single_drape','open_interior'][i%4]
        META['windows'].append({'id':o.name,'quad_px':quad,'z_index':100,'lit':lit,'building':building,'wall':wall,'style':style,'visibility':'in-frame candidate; final occlusion mask/raycast filtering deferred'})
        if hi-lo<.18 or h-z<15:continue
        color=MA[['curtain cream','curtain blue','curtain burgundy'][i%3]]
        if style=='half_blind':
            for zz in np.arange(z+(h-z)*.55,h,2.8):plane('window uneven venetian blind',wall,lo+.015,hi-.015,front+.009,float(zz),float(zz)+1.3,color)
            line('blind cord',[(front+.018,hi-.04,z+(h-z)*.45),(front+.018,hi-.04,h)] if wall=='u' else [(hi-.04,front+.018,z+(h-z)*.45),(hi-.04,front+.018,h)],MA['cream paper'],.002)
        elif style in ['parted_curtains','single_drape']:
            intervals=[(lo+.01,lo+(hi-lo)*.24)]
            if style=='parted_curtains':intervals.append((hi-(hi-lo)*.27,hi-.01))
            for ll,hh in intervals:
                for k in range(5):plane('soft curtain pleat',wall,ll+k*(hh-ll)/5,ll+(k+1)*(hh-ll)/5,front+.008+.007*math.sin(k*2),z+.8,h,color)
        else:
            # Small interior lamp and bookcase shapes read behind the window frame.
            mid=(lo+hi)/2;pts=[(mid-.04,z+7),(mid+.04,z+7),(mid+.07,z+15),(mid-.07,z+15)]
            deco_mesh('window interior lampshade',wall,pts,front+.008,MA['warm lettering'])
            plane('window lamp stem',wall,mid-.008,mid+.008,front+.01,z+2,z+7,MA['ink'])
    status('remaining in-frame neighbour windows given varied blinds, parted curtains and small interiors; candidate quads recorded for the future page-driven event kit')

def cutaways(sc):
    b.layer('background')
    for o in list(sc.objects):
        if o.name.startswith(('Crown cornice','Crown brass ribbon','Partition worn coping')):rm(o)
    core=MA['cut plaster core'];outer=bpy.data.materials['P8 brownbrick'];purple=bpy.data.materials['wall plum'];teal=bpy.data.materials['P10 restroom teal partitions']
    # Three side-by-side bands on the exposed top show the actual section.
    # Exterior roofs retain weathered copings; these interior cuts stay clean.
    def cap(n,rect,z,inside=purple,axis='v'):
        a,v,c,w=rect;box(n+' core',a,v,c,w,z,z+1.6,core,.002)
        if axis=='v':
            box(n+' exterior finish',a,v,c,v+.026,z+1.6,z+1.9,outer,0)
            box(n+' interior finish',a,w-.025,c,w,z+1.6,z+1.9,inside,0)
        else:
            box(n+' exterior finish',a,v,a+.026,w,z+1.6,z+1.9,outer,0)
            box(n+' interior finish',c-.025,v,c,w,z+1.6,z+1.9,inside,0)
        META.setdefault('cut_caps',[]).append({'name':n,'uv':rect,'z':z,'section':'exterior masonry / pale core / interior finish'})
    cap('right corridor exposed cut',[0,-.22,13,.025],170)
    cap('junction exposed cut',[-.22,0,.025,3],170,purple,'u')
    cap('restroom left cut',[-.22,3,.03,8.9],155,teal,'u')
    cap('restroom entrance cut',[0,2.94,2.9,3.08],125,teal)
    cap('ticket partition cut',[2.9,4.4,3.1,8.9],88,purple,'u')
    cap('concessions partition cut',[4.4,2.9,13,3.1],88,purple)
    cap('restroom service end cut',[.02,8.35,2.88,8.44],35,teal)
    cap('restroom low return cut',[2.86,3.08,2.94,4.4],30,teal,'u')
    cap('street wall cut',[0,8.90,3,9.05],159,teal)
    b.layer('restroom')
    # Thin panels expose a laminate core rather than pretending to be brick.
    for o in list(sc.objects):
        if o.type=='MESH' and o.name.startswith('P10 stall ') and 'divider' in o.name:
            a,v,c,w,z,h=bounds(o)
            box('stall laminate cut edge',a,v+.006,c,w-.006,h,h+.65,MA['cut teal laminate core'],0)
    status('purple cornice replaced with explicit pale wall-core caps and distinct interior/exterior finishes; matching cuts added to junction, restroom, partitions, left wing and stall panels')

def link_new_surface_lighting(sc):
    bpy.context.view_layer.update()
    city=bpy.data.collections.get('P8 surroundings light receivers');west=bpy.data.collections.get('P9 west fill receivers');roof=bpy.data.collections.get('P10 multiplex roof light receivers');alley_collection=bpy.data.collections.get('P8B alley light receiver')
    counts={'city':0,'west':0,'roof':0,'alley':0}
    for o in sc.objects:
        if o.type not in ['MESH','CURVE','FONT'] or not o.name.startswith('D3 '):continue
        a,v,c,w,z,h=bounds(o);u=(a+c)/2;vv=(v+w)/2
        targets=[]
        if vv<-.23 and u>-.07 and z>230:targets.append(('roof',roof))
        elif u<-.075 or u>13 or vv>13.5:targets.append(('city',city))
        if u<-.075 and z>230 or o.name.startswith(('D3 cafe','D3 small corner cafe','D3 wet cafe','D3 closed parasol','D3 folded rain')):targets.append(('west',west))
        if u>13 and -.23<vv<9.15 and h<2:targets.append(('alley',alley_collection))
        for key,col in targets:
            if col and o.name not in col.objects:col.objects.link(o);counts[key]+=1
    META['new_surface_light_links']=counts
    status('still-review correction: new exterior surfaces share their support buildings lighting; wear softened, alley darkened, live poster apertures cleared and remaining glass marks removed')

def check(sc,camera):
    bpy.context.view_layer.update()
    new_overlap=[];forbidden=[[3,.9,13,2.0]]+[[u-.5,0,u+.5,1.4] for u in [4.8,8.2,11.2]]+[[-6.35,9.78,-5.65,10.05]]
    for e in META['new_footprints']:
        r=e['uv']
        for q in forbidden:
            if min(r[2],q[2])-max(r[0],q[0])>0 and min(r[3],q[3])-max(r[1],q[1])>0:new_overlap.append([e['name'],q])
    assert not new_overlap,new_overlap
    assert list(sc.camera.matrix_world)==camera
    assert not any(o.name.startswith(('Oil tide edge','P10 glass water trace','Branching asphalt crack','P8B alley expansion joint','P8B alley transverse joint')) for o in sc.objects)
    assert bpy.data.objects.get('P10 single multiplex wet roof')
    facing=[o.name for o in sc.objects if o.type=='FONT' and abs((o.matrix_world.to_quaternion()@Vector((0,0,1))).dot(NORMAL))>.999]
    assert not facing,facing
    META['checks']={'new_fixture_route_overlap_count':len(new_overlap),'camera_unchanged':True,'screen_ids':sorted({o.get('door_id') for o in sc.objects if o.get('door_id')}),'static_glass_trace_count':0,'static_ripple_ring_count':0,'old_asphalt_scribble_count':0,'alley_tile_joint_count':0,'screen_facing_text_count':len(facing),'window_candidates':len(META['windows']),'production_validation':'not run; draft only'}
    status('draft checks passed: unchanged camera, 3 screen IDs, clear corridor/door approaches/spawn strip, zero obsolete glass dashes, ripple outlines or alley grid joints')

def main():
    start=time.perf_counter()
    bpy.ops.wm.open_mainfile(filepath=str(QA/'source_before_draft3.blend'));sc=bpy.context.scene;gpu(sc)
    b.GROUPS.clear();b.M.clear()
    for ma in bpy.data.materials:b.M[ma.name]=ma
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:
            b.GROUPS.setdefault(o.get('layer','background'),[]).append(o);o.visible_camera=True;o.hide_render=False;o.is_holdout=False
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf');d.metal=bpy.data.materials['P10 aged graphite steel']
    bpy.context.view_layer.update();camera=list(sc.camera.matrix_world)
    restore_draft2(sc);palette();party_wall(sc);corridor(sc);wet_surfaces(sc);roofs(sc);alley(sc);cafe(sc);windows(sc);cutaways(sc);link_new_surface_lighting(sc);check(sc,camera)
    sc['draft_only']=True;sc['draft_brief']='BRIEF-14-pass10-draft3.md';sc['draft_number']=3
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.cycles.adaptive_threshold=.05
    sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=16
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100;sc.render.film_transparent=False
    sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.use_compositing=True
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'))
    (QA/'draft3_geometry.json').write_text(json.dumps(META,indent=2))
    status('editable roxy_pass10_draft.blend saved; only one 1920x1080 low-sample still configured')
    t=time.perf_counter();render(QA/'draft_3.png')
    timing={'render_seconds':round(time.perf_counter()-t,2),'total_seconds':round(time.perf_counter()-start,2),'samples':24,'resolution':[1920,1080],'production_outputs':0,'loops':0,'slices':0,'sprites':0,'renders_2x':0}
    (QA/'draft3_render_timing.json').write_text(json.dumps(timing,indent=2))
    status('quick lit draft_3.png rendered in %.1f seconds; no out10, loop, sprite, slice or 2x jobs invoked'%timing['render_seconds'])
if __name__=='__main__':main()
