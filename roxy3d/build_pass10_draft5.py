"""Brief 16: original art, surface-specific rain and physical micro-impacts.
Always starts from the preserved draft-4 source. Never invokes a pack builder.
"""
import sys,math,random,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import build_scene as b
import build_pass10_draft as d
import build_vehicles as veh
from common import xyz,ZPP,project
from pass8_common import gpu
from build_pass10_draft4 import quality
from draft5_common import *
R=random.Random(161005);META={'art':[],'water':[]};SPARKS=[]

def mat(n,c,r=.4,m=0):return b.material('D5 '+n,c,r,m)
def line(n,p,ma,r=.007):return b.line('D5 '+n,[xyz(*q) for q in p],ma,r)
def artmat(key,emit=0,paper=True):
    ma=mat('art '+key,(.5,.5,.5),.48);n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
    im=bpy.data.images.load(str(WORK/'art'/(key+'.png')),check_existing=True);im.pack();tex=n.new('ShaderNodeTexImage');tex.image=im;l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(tex.outputs['Alpha'],p.inputs['Alpha'])
    if emit:l.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emit
    p.inputs['Coat Weight'].default_value=.2 if paper else .35;p.inputs['Coat Roughness'].default_value=.27
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0012;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return ma
def art(key,a,c,v,z0,z1,axis='v',emit=0,peel=False,name=None):
    # UVs follow the physical wall, not the camera. Optional lifted paper corner.
    pts=[(a,v,z0),(c,v,z0),(c,v,z1),(a,v,z1)] if axis=='v' else [(v,c,z0),(v,a,z0),(v,a,z1),(v,c,z1)]
    if peel:pts[2]=(pts[2][0]+(.007 if axis=='u' else 0),pts[2][1]+(.007 if axis=='v' else 0),pts[2][2]-.9)
    ob=b.mesh('D5 art '+(name or key),[xyz(*p) for p in pts],[(0,1,2,3)],artmat(key,emit))
    uv=ob.data.uv_layers.new();coords=[(0,0),(1,0),(1,1),(0,1)]
    for i in range(4):uv.data[i].uv=coords[i]
    ob['approved_meme']=key;ob['original_art']='make_draft5_art.ps1';ob['rain_paper']=peel
    META['art'].append({'key':key,'object':ob.name,'axis':axis,'wall_extent':[a,c,v,z0,z1],'peeling_corner':peel})
    return ob

def artworks(sc):
    b.layer('draft5_art')
    for o in list(sc.objects):
        if o.name.startswith(('D3 board heading','D3 board listings','D3 board foot','P8 noodle','P8 sign TAKE AWAY')) and o.type=='FONT':d.rm(o)
    art('whiplash',1.02,2.82,.105,64,130)
    # Cover the old fictional corridor one-sheet inside its existing frame.
    art('glorp',3.05,3.81,.118,67,127)
    art('wcat',10.03,12.67,-3.532,285,355)
    art('travel',.553,1.107,9.477,10.5,70.5,emit=.33)
    metal=mat('scuffed call box',(.15,.20,.19),.38,.55)
    b.box('D5 red blue utility call box',1.40,9.445,1.72,9.52,25,61,metal,.012)
    art('buttons',1.405,1.715,9.523,25.5,60.5)
    for u,col in [(1.482,(.45,.018,.012)),(1.625,(.015,.07,.36))]:
        ma=mat('button '+str(u),col,.21,.15);b.cylinder('D5 physical utility push button',xyz(u,9.533,41.3),.034,.017,ma,(0,-1,0),24)
    # Both alley walls retain emergency-door / delivery routes.
    art('cinema',13.25,16.45,-.223,136,170,emit=0)
    art('turf',15.08,16.64,-.048,37,91)
    art('lookalike',.18,.76,9.072,98,148,peel=True)
    for j in range(3):
        ob=art('conductor',.90+j*.64,1.40+j*.64,9.073,98,148,peel=True,name='conductor '+str(j))
        if j==2:
            # Real torn shape, not a rectangular black crop.
            vs=ob.data.vertices;vs[0].co.z=124/ZPP;vs[1].co.z=118/ZPP
            uv=ob.data.uv_layers.active;uv.data[0].uv.y=(124-98)/50;uv.data[1].uv.y=(118-98)/50
            ob['half_torn']=True
    art('cabge',-2.54,-1.41,8.825,44.5,64.5)
    canvas=mat('soaked CABGE canvas',(.075,.16,.09),.72)
    b.mesh('D5 CABGE soaked awning',[xyz(*p) for p in [(-2.57,8.84,43),(-1.38,8.84,43),(-1.38,9.12,36),(-2.57,9.12,36)]],[(0,1,2,3)],canvas)
    timber=mat('wet crate timber',(.14,.085,.035),.56);green=mat('green cabbage',(.15,.27,.075),.46);red=mat('single red cabbage',(.24,.035,.10),.42)
    for j,u in enumerate([-2.34,-1.76]):
        for z in [5,10,15]:
            b.box('D5 cabbage crate slat',u-.23,8.94,u+.23,8.97,z,z+2,timber,.004)
            b.box('D5 cabbage crate slat',u-.23,9.25,u+.23,9.28,z,z+2,timber,.004)
        for k in range(6):
            cu=u-.15+(k%3)*.15;cv=9.02+(k//3)*.15;ma=red if j==1 and k==4 else green
            ob=b.ball('D5 RED cabbage' if ma==red else 'D5 green cabbage',xyz(cu,cv,16.5),.087,ma,scale=(1,1,.85))
            for n in range(3):line('cabbage leaf vein',[(cu-.055,cv+n*.018-.018,19),(cu,cv+n*.02-.02,22),(cu+.06,cv+n*.018-.018,18.5)],green if ma!=red else red,.002)
    before=set(sc.objects);b.layer('draft5_parked_bus');veh.palette('bus');veh.bus(False)
    bus_objects=set(sc.objects)-before;offset=xyz(-.5,11.24,0)
    for o in bus_objects:
        o.location+=offset
        if o.type=='LIGHT' and 'reflection' in o.name.lower():bpy.data.objects.remove(o,do_unlink=True)
        elif o.type=='LIGHT':o.data.energy*=.35
        else:o['draft5_bus']=True
    p=veh.M['paint'].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.15,.085,.035,1)
    b.layer('draft5_art')
    art('boxing',-1.67,-.55,11.655,20,34.5,emit=0)
    art('courier',-.51,.62,11.655,20,34.5,emit=0)
    META['bus']={'origin':[-.5,11.24],'parked':True,'objects':len(bus_objects),'production_sprite_pack':False}
    assert len(set(a['key'] for a in META['art']))==12
    assert len([o for o in sc.objects if o.name=='D5 RED cabbage'])==1
    status('all twelve approved memes placed as original packed artwork on physical walls, paper, sign boxes and a parked bus; CABGE has exactly one red cabbage')

def mnode(n,l,op,*args):
    q=n.new('ShaderNodeMath');q.operation=op
    for i,v in enumerate(args):
        if isinstance(v,(int,float)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs[0]
def vnode(n,l,op,a,c):
    q=n.new('ShaderNodeVectorMath');q.operation=op
    for i,v in enumerate([a,c]):
        if isinstance(v,(tuple,list)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs.get('Value') if op=='DOT_PRODUCT' else q.outputs[0]
def range_node(n,l,inp,lo,hi):
    q=n.new('ShaderNodeMapRange');l.new(inp,q.inputs['Value']);q.inputs['To Min'].default_value=lo;q.inputs['To Max'].default_value=hi;return q.outputs[0]
def wetmaterial(original,kind,cache):
    key=(original.name,kind)
    if key in cache:return cache[key]
    ma=original.copy();ma.name='D5 wet '+kind+' | '+original.name;cache[key]=ma
    if not ma.use_nodes:return ma
    n=ma.node_tree.nodes;l=ma.node_tree.links;p=next((q for q in n if q.type=='BSDF_PRINCIPLED'),None)
    if p is None:return ma
    def put(name,v):
        if name not in p.inputs:return
        for link in list(p.inputs[name].links):l.remove(link)
        if isinstance(v,(int,float,tuple,list)):p.inputs[name].default_value=v
        else:l.new(v,p.inputs[name])
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=28;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    broad=n.new('ShaderNodeTexNoise');broad.inputs['Scale'].default_value=1.25;broad.inputs['Detail'].default_value=4;l.new(geo.outputs['Position'],broad.inputs['Vector'])
    put('Coat Weight',range_node(n,l,broad.outputs['Fac'],.18,.70));put('Coat Roughness',range_node(n,l,noise.outputs['Fac'],.18,.39))
    ranges={'asphalt':(.39,.68),'felt':(.55,.82),'paving':(.38,.64),'water':(.16,.29),'metal':(.24,.46),'glass':(.10,.23),'fabric':(.65,.88),'masonry':(.47,.78),'wood':(.46,.74),'vegetation':(.38,.60),'paint':(.35,.64)}
    lo,hi=ranges[kind];put('Roughness',range_node(n,l,noise.outputs['Fac'],lo,hi))
    if kind in ['asphalt','felt','paving','water']:
        put('Metallic',0);put('IOR',1.333 if kind=='water' else 1.48);put('Anisotropic IOR Level',.76 if kind in ['asphalt','water'] else .42);put('Tangent',(-.707106,.707106,0))
        if kind=='water':put('Coat Weight',.55);put('Coat Roughness',.23)
        if kind=='asphalt':
            graincolor=n.new('ShaderNodeMixRGB');graincolor.blend_type='MULTIPLY';graincolor.inputs[0].default_value=1;graincolor.inputs[1].default_value=(.031,.039,.047,1);l.new(range_node(n,l,noise.outputs['Fac'],.55,1.35),graincolor.inputs[2]);put('Base Color',graincolor.outputs[0]);put('Specular IOR Level',.50);put('Coat Weight',range_node(n,l,broad.outputs['Fac'],.32,.92));put('Coat Roughness',range_node(n,l,noise.outputs['Fac'],.10,.24))
        tangent=n.new('ShaderNodeCombineXYZ');tangent.inputs[0].default_value=-.707106;tangent.inputs[1].default_value=.707106;put('Tangent',tangent.outputs[0])
    if kind=='fabric':
        col=p.inputs['Base Color'].default_value;put('Base Color',(col[0]*.56,col[1]*.56,col[2]*.56,1));put('Coat Weight',.06)
    if kind in ['masonry','metal','paint','wood']:
        runoff=n.new('ShaderNodeTexNoise');runoff.inputs['Scale'].default_value=1;runoff.inputs['Detail'].default_value=2;l.new(vnode(n,l,'MULTIPLY',geo.outputs['Position'],(16,16,.18)),runoff.inputs['Vector'])
        wash=n.new('ShaderNodeMixRGB');wash.blend_type='MULTIPLY';wash.inputs[0].default_value=.4
        if p.inputs['Base Color'].is_linked:l.new(p.inputs['Base Color'].links[0].from_socket,wash.inputs[1])
        else:wash.inputs[1].default_value=p.inputs['Base Color'].default_value
        l.new(range_node(n,l,runoff.outputs['Fac'],.48,1),wash.inputs[2]);put('Base Color',wash.outputs[0])
    # Grain + directional micro-rain normals. Wet film is variable, no new mirror plane.
    prev=p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].is_linked else None
    # Remove existing ripple from the path and reinsert exactly once beneath new grain.
    for q in n:
        if q.type=='GROUP' and q.node_tree and q.node_tree.name=='D4 periodic ray-traced rain ripple normals':
            prev=q.outputs['Normal'];q.inputs['Strength'].default_value=.85 if kind=='water' else (.42 if kind=='asphalt' else .24)
    if kind in ['asphalt','felt','paving','water'] and not any(q.type=='GROUP' and q.node_tree and q.node_tree.name=='D4 periodic ray-traced rain ripple normals' for q in n):
        q=n.new('ShaderNodeGroup');q.node_tree=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];q.inputs['Strength'].default_value=.22 if kind!='water' else .85
        if prev:l.new(prev,q.inputs['Normal In'])
        prev=q.outputs['Normal']
    grain=n.new('ShaderNodeBump');grain.inputs['Strength'].default_value=.24 if kind=='asphalt' else .16;grain.inputs['Distance'].default_value=.006 if kind=='asphalt' else .003
    l.new(noise.outputs['Fac'],grain.inputs['Height'])
    if prev:l.new(prev,grain.inputs['Normal'])
    # Two camera-ground basis vectors: horizontal texture continuity, narrow ridges
    # transverse to the view produce broken depth-wise specular streaks.
    cross=vnode(n,l,'DOT_PRODUCT',geo.outputs['Position'],(.707106,.707106,0));depth=vnode(n,l,'DOT_PRODUCT',geo.outputs['Position'],(-.707106,.707106,0))
    combine=n.new('ShaderNodeCombineXYZ');l.new(mnode(n,l,'MULTIPLY',cross,6),combine.inputs[0]);l.new(mnode(n,l,'MULTIPLY',depth,65),combine.inputs[1]);l.new(mnode(n,l,'MULTIPLY',geo.outputs['Position'],0),combine.inputs[2]) if False else None
    micro=n.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=1;micro.inputs['Detail'].default_value=2;l.new(combine.outputs[0],micro.inputs['Vector'])
    fine=n.new('ShaderNodeBump');fine.inputs['Strength'].default_value=.4 if kind in ['asphalt','water'] else .2;fine.inputs['Distance'].default_value=.0045 if kind in ['asphalt','water'] else .0015;l.new(micro.outputs['Fac'],fine.inputs['Height']);l.new(grain.outputs[0],fine.inputs['Normal']);put('Normal',fine.outputs[0]);put('Coat Normal',fine.outputs[0])
    if kind=='asphalt':
        # Dielectric, anisotropic water-film lobe above rough aggregate. Its
        # Fresnel weight is modulated by the large-scale wetting/thickness field.
        # Unlike Principled's isotropic coat, this can make long broken highlights.
        put('Roughness',range_node(n,l,noise.outputs['Fac'],.60,.84));put('Coat Weight',0)
        film=n.new('ShaderNodeBsdfAnisotropic');film.name='D5 directional water film';film.inputs['Color'].default_value=(.9,.95,1,1);film.inputs['Anisotropy'].default_value=.95;l.new(tangent.outputs[0],film.inputs['Tangent']);l.new(range_node(n,l,noise.outputs['Fac'],.16,.28),film.inputs['Roughness']);l.new(fine.outputs[0],film.inputs['Normal'])
        # Two-sided thin-film Schlick Fresnel (water F0 = .02037). Legacy
        # reversed box winding must not be interpreted as water-to-air TIR.
        cosine=mnode(n,l,'ABSOLUTE',vnode(n,l,'DOT_PRODUCT',fine.outputs[0],geo.outputs['Incoming']))
        fres=mnode(n,l,'ADD',.02037,mnode(n,l,'MULTIPLY',.97963,mnode(n,l,'POWER',mnode(n,l,'SUBTRACT',1,cosine),5)))
        # Calibrated wet-lobe coverage for this dimetric scene. This is a rough
        # layered-material approximation, not a measured thin-film solver.
        weight=mnode(n,l,'MAXIMUM',fres,range_node(n,l,broad.outputs['Fac'],.14,.34))
        mix=n.new('ShaderNodeMixShader');l.new(weight,mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(film.outputs[0],mix.inputs[2]);out=next(q for q in n if q.type=='OUTPUT_MATERIAL');l.new(mix.outputs[0],out.inputs['Surface'])
    ma['rain_response']=kind;ma['variable_water_film']=True;return ma

def classify(o,ma):
    s=(o.name+' '+ma.name).lower()
    if ('skylight' in o.name.lower() and any(k in o.name.lower() for k in ['bar','frame','kerb'])) or 'fire escape' in o.name.lower():return 'metal'
    if any(k in s for k in ['skylight wired glass','warm wired skylight','shelter glass','glass','glazing']):return 'glass'
    if any(k in s for k in ['puddle','reflective water','shallow water']):return 'water'
    if any(k in s for k in ['felt','tarp','roof repair']):return 'felt'
    if any(k in s for k in ['asphalt','wet street','road']):return 'asphalt'
    if any(k in s for k in ['awning','canvas','parasol']):return 'fabric'
    if any(k in s for k in ['cabbage','leaf','plant','foliage']):return 'vegetation'
    if any(k in s for k in ['wood','timber','crate']):return 'wood'
    if any(k in s for k in ['paving','curb','concrete','limestone',' cap','coping','sill','ledge','brick','masonry','render']):return 'masonry' if 'paving' not in s else 'paving'
    if any(k in s for k in ['metal','steel','iron','nickel','brass','chrome','ac ','hvac','duct','fan','vent','shelter roof','bin','dumpster','sign','billboard','rail','escape','bus','hatch','canopy']):return 'metal'
    return 'paint'

def outdoor(p,o):
    # An open cinema leaf can cross the coordinate cutoff; identity is stable.
    if str(o.get('door_id','')) in {'1','2','3'} or o.get('anim_id') in {'screen_1','screen_2','screen_3'}:return False
    u,v,z=p.x,-p.y,p.z*ZPP
    # Cutaway auditorium/restrooms/lobby are indoors despite being camera-open.
    if 0.01<u<12.99 and .03<v<8.92 and z<175:return False
    if o.get('approved_meme') in ['whiplash','glorp']:return False
    if any(t in o.name.lower() for t in ['cut core','cut interior','cut exterior','cut cap','section cap']):return False
    return True

def atmosphere(o):return any(s in o.name.lower() for s in ['cloud sky','atmospheric volume','atmosphere','sky dome','light receiver mask'])

def water_audit(sc):
    b.layer('draft5_rain_response');cache={};deps=bpy.context.evaluated_depsgraph_get();surfaces=[];excluded=[];data=[];pending=[]
    # Immutable ray BVH avoids dependency-graph refresh and costly scene queries
    # for every drop. Includes the same evaluated bevel/curve geometry as render.
    bv=[];bf=[]
    for o in list(sc.objects):
        if o.type not in ['MESH','CURVE'] or o.hide_render or atmosphere(o):continue
        eo=o.evaluated_get(deps);me=eo.to_mesh();base=len(bv);bv.extend(eo.matrix_world@v.co for v in me.vertices);bf.extend(tuple(base+i for i in p.vertices) for p in me.polygons);eo.to_mesh_clear()
    print('D5 building sky BVH',len(bv),'vertices',len(bf),'faces',flush=True)
    sky=BVHTree.FromPolygons(bv,bf);del bv,bf
    def covered(pt):return sky.ray_cast(pt,Vector((0,0,1)),80)[0] is not None
    for oi,o in enumerate(list(sc.objects)):
        if oi%500==0:print('D5 exposure scan',oi,'/',len(sc.objects),flush=True)
        if o.type not in ['MESH','CURVE'] or o.hide_render or not o.data.materials:continue
        if atmosphere(o):excluded.append(o.name);continue
        if o.name.startswith(('Fine asphalt aggregate','D5 art')):continue
        mesh=o.to_mesh();world=o.matrix_world;normal=world.to_3x3().inverted().transposed();candidates=[]
        for face in mesh.polygons:
            nn=(normal@face.normal).normalized()
            # Legacy box meshes use inward winding; test both sides geometrically.
            # The sky ray rejects undersides, unlike trusting a signed mesh normal.
            if abs(nn.z)<.03:continue
            if nn.z<0:nn=-nn
            center=world@face.center
            if not outdoor(center,o):continue
            # Sample each top-facing polygon; a real sky ray rejects sheltered parts.
            verts=[world@mesh.vertices[i].co for i in face.vertices]
            probes=[center]+[center.lerp(v,.65) for v in verts[:4]]
            if all(covered(pt+Vector((0,0,.003))) for pt in probes):continue
            area=sum((verts[k]-verts[0]).cross(verts[k+1]-verts[0]).length*.5 for k in range(1,len(verts)-1));mi=min(face.material_index,len(o.data.materials)-1);candidates.append((center,nn,verts,area,mi))
        o.to_mesh_clear()
        if not candidates:excluded.append(o.name);continue
        kinds=[]
        for mi in sorted(set(q[4] for q in candidates)):
            original=o.data.materials[mi]
            if original is None:continue
            kind=classify(o,original);kinds.append(kind);pending.append((o,mi,original,kind))
        for center,nn,verts,area,mi in candidates:
            kind=classify(o,o.data.materials[mi]);surfaces.append({'object':o.name,'point':center,'normal':nn,'verts':verts,'area':area,'kind':kind})
        data.append({'name':o.name,'kinds':sorted(set(kinds)),'sky_exposed_upward_polygons':len(candidates),'world_area':sum(q[3] for q in candidates),'bounds':list(d.bounds(o))})
    for o,mi,original,kind in pending:
        o.data.materials[mi]=wetmaterial(original,kind,cache);o['rain_audited']=True;o['rain_response']=kind
    META['water']=data;META['water_excluded']=excluded
    required=['Bus shelter steel roof','D4 north mechanical AC case','D4 south mechanical AC case','D4 southwest skylight wired glass','D4 northeast skylight wired glass','D3 cafe striped awning','D3 folded rain parasol','D3 dumpster ribbed hinged lid','D3 alley fire escape landing']
    found={q['name'] for q in data};assert all(k in found for k in required),[k for k in required if k not in found]
    META['required_water_targets']={k:True for k in required}
    print('D5 exposure scan complete',len(data),'objects;',len(surfaces),'polygons',flush=True)
    # Make weather on tops directly visible: droplets, crowns and runoff are actual
    # scene geometry with dielectric BSDFs, never emissive white screen noise.
    water=mat('dielectric water beads',(.84,.92,.98),.09)
    p=water.node_tree.nodes.get('Principled BSDF');p.inputs['IOR'].default_value=1.333;p.inputs['Transmission Weight'].default_value=.92;p.inputs['Coat Weight'].default_value=.22
    steelwater=water
    verts=[];faces=[];crowns=[];drips=[];sites=[];counts={}
    def bead(c,r,flatten=.50):
        off=len(verts);verts.append(tuple(c+Vector((0,0,r*flatten))))
        for k in range(8):verts.append(tuple(c+Vector((math.cos(k*math.tau/8)*r,math.sin(k*math.tau/8)*r,r*flatten*.18))))
        verts.append(tuple(c-Vector((0,0,r*.12))))
        for k in range(8):faces.extend([(off,off+1+k,off+1+(k+1)%8),(off+9,off+1+(k+1)%8,off+1+k)])
    for s in surfaces:
        area=s['area'];kind=s['kind'];poly=s['verts']
        if area<.00008:continue
        # Importance density is higher on metal/glass, with a bounded count for roofs.
        qty=min(48,max(0,int(area*(55 if kind in ['metal','glass'] else 3)+R.random())))
        if kind in ['metal','glass'] and area>.008:qty=max(qty,3)
        center=s['point'];tris=[(poly[0],poly[k],poly[k+1]) for k in range(1,len(poly)-1)]
        if not tris:continue
        for k in range(qty):
            a,c,e=R.choice(tris);r1=math.sqrt(R.random());r2=R.random();pt=a*(1-r1)+c*(r1*(1-r2))+e*(r1*r2);pt+=Vector((0,0,.002))
            if not outdoor(pt,bpy.data.objects[s['object']]) or covered(pt+Vector((0,0,.003))):continue
            r=R.uniform(.006,.018) if kind in ['metal','glass'] else R.uniform(.005,.012)
            bead(pt,r,.48);counts[kind]=counts.get(kind,0)+1
            if kind in ['metal','glass','masonry','fabric'] and k%13==0:
                # Crown is a connected irregular water rim plus three satellite drops.
                pts=[pt+Vector((math.cos(j*math.tau/12)*r*2.1,math.sin(j*math.tau/12)*r*2.1,r*(1.8 if j%2==0 else .45))) for j in range(13)]
                crowns.append(pts)
            if kind=='glass' and k%5==0:drips.append([pt,pt+Vector((.025,-.008,-.004)),pt+Vector((.062,-.018,-.009))])
        # Edge drops/runoff on each exposed sizeable cap or equipment face.
        if kind in ['metal','glass','masonry','fabric','wood','paint'] and area>.015:
            edges=list(zip(poly,poly[1:]+poly[:1]));edges.sort(key=lambda e:(e[1]-e[0]).length,reverse=True)
            for a,c in edges[:2]:
                for f in [.21,.58,.86]:
                    pt=a.lerp(c,f)+Vector((0,-.002,.001));length=R.uniform(.025,.075)
                    if not outdoor(pt,bpy.data.objects[s['object']]):continue
                    drips.append([pt,pt+Vector((.002,-.002,-length*.6)),pt+Vector((.003,-.003,-length))]);bead(pt+Vector((.003,-.003,-length)),.006,.85)
        # Micro-impact population on real WET sky-visible upward surfaces only.
        ns=min(1800,int(area*(22 if kind in ['water','asphalt','paving','felt'] else 5)+R.random()))
        for k in range(ns):
            a,c,e=R.choice(tris);r1=math.sqrt(R.random());r2=R.random();pt=a*(1-r1)+c*r1*(1-r2)+e*r1*r2+Vector((0,0,.004))
            if not outdoor(pt,bpy.data.objects[s['object']]) or covered(pt+Vector((0,0,.003))):continue
            sites.append({'point':list(pt),'phase':R.random(),'radius':R.choice([.006,.009,.014,.020]),'duration':R.choice([.075,.10,.125]),'object':s['object'],'kind':kind})
    if verts:
        ob=b.mesh('D5 physical surface beads',verts,faces,steelwater)
        for f in ob.data.polygons:f.use_smooth=True
    def batch_curves(name,paths,r):
        cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1
        for path in paths:
            sp=cu.splines.new('POLY');sp.points.add(len(path)-1)
            for q,pt in zip(sp.points,path):q.co=(*pt,1)
        ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob);cu.materials.append(water);return ob
    batch_curves('D5 metal and cap splash crowns',crowns,.0022);batch_curves('D5 hem edge drips and glass runnels',drips,.0024)
    # Wind-facing shelter glazing sits under the steel overhang. Give it beads
    # and downward runnels explicitly; it is not a falling-impact landing face.
    pane=bpy.data.objects['Bus shelter glass'];pane.data.materials[0]=wetmaterial(pane.data.materials[0],'glass',cache);pane['rain_response']='wind-driven glass beads and runnels';pane['rain_audited']=True
    wallruns=[]
    for k in range(32):
        u=R.uniform(1.18,1.91);v=9.438;z=R.uniform(12,73);radius=R.uniform(.004,.011)
        b.ball('D5 shelter wind-facing glass bead',xyz(u,v,z),radius,water,scale=(1,.55,1.45))
        if k%3==0:wallruns.append([xyz(u,v,z),xyz(u+.008,v+.001,z-2),xyz(u+.003,v+.001,z-R.uniform(3,7))])
    batch_curves('D5 shelter glass gravity runnels',wallruns,.002)
    META['shelter_wind_glass']={'beads':32,'runnels':len(wallruns),'rationale':'wind-driven rain on vertical glass beneath overhang; not upward-facing impact sites'}
    # Dynamic impacts are a single efficient faceted mesh. Their normals create
    # specular glints from existing lights; no emission, no added light sources.
    SV=[];SF=[]
    for s in sites:
        i=len(SV);SV.extend([s['point']]*6);SF.extend([(i,i+1,i+2),(i,i+2,i+3),(i,i+3,i+4),(i,i+4,i+1),(i+5,i+2,i+1),(i+5,i+3,i+2),(i+5,i+4,i+3),(i+5,i+1,i+4)])
    ob=b.mesh('D5 periodic wet micro impacts',SV,SF,water);ob['wet_only']=True;ob['period_seconds']=2.;ob['seed']=161005;ob['emission_strength']=0.
    report('impact_sites.json',sites);META['water_summary']={'audited_objects':len(data),'exposed_upward_polygons':len(surfaces),'wet_material_variants':len(cache),'static_beads_by_material':counts,'splash_crowns':len(crowns),'edge_drips_and_runnels':len(drips),'micro_impact_sites':len(sites),'unhandled_exposed_objects':0,'exclusions':'indoors, cutaway section edges, sky-occluded faces, vertical-only faces; transparent art uses its own wet-paper shader'}
    status('surface audit complete: %d exposed objects treated, %d bead sites, %d crowns and %d edge drips/runnels; %d periodic wet-surface micro-impact sites'%(len(data),sum(counts.values()),len(crowns),len(drips),len(sites)))

def set_phase(sc,t):
    t=t%2.;bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'].nodes['Time seconds'].outputs[0].default_value=t
    ob=bpy.data.objects.get('D5 periodic wet micro impacts')
    if not ob:return
    sites=json.loads((WORK/'impact_sites.json').read_text());arr=[]
    for s in sites:
        age=(t/2-s['phase'])%1;f=math.sin(math.pi*age/s['duration'])**2 if age<s['duration'] else 0
        if sc.get('d5_control_off',False):f=0
        r=s['radius']*f;p=Vector(s['point']);h=r*(1.5-age/max(s['duration'],1e-6))
        arr.extend([p+Vector((0,0,h)),p+Vector((r,0,0)),p+Vector((0,r,0)),p+Vector((-r,0,0)),p+Vector((0,-r,0)),p-Vector((0,0,r*.1))])
    ob.data.vertices.foreach_set('co',np.asarray(arr,dtype=np.float32).ravel());ob.data.update()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(QA/'source_before_draft5.blend'));sc=bpy.context.scene;gpu(sc);b.GROUPS.clear();b.M.clear();b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    for o in sc.objects:
        if o.type in ['MESH','CURVE','FONT']:b.GROUPS.setdefault(o.get('layer','background'),[]).append(o)
    artworks(sc);bpy.context.view_layer.update();water_audit(sc);set_phase(sc,0);quality(sc);sc.cycles.use_denoising=True
    # Existing architectural light linking applies also to new wet details and art.
    for o in sc.objects:
        if o.name.startswith('D5 ') and o.type in ['MESH','CURVE','FONT']:
            for cname in ['P8 surroundings light receivers','P9 west fill receivers','P10 multiplex roof light receivers']:
                col=bpy.data.collections.get(cname)
                if col and o.name not in col.objects:col.objects.link(o)
    sc['draft_number']=5;sc['draft_brief']='BRIEF-16-draft5.md';sc['draft_only']=True
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));report('scene.json',META)
    status('draft 5 source saved from draft 4 with packed original art, revised wet materials, retained ray-traced ripple group and analytic 2-second micro-impacts; no pack build')
if __name__=='__main__':main()
