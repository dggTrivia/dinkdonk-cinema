"""Corrected Brief 22: build from immutable D9, one weather-composited draft.

No animation rendering, alternate views, audits, production or cloud work.
"""
import sys, math, random, time, shutil, hashlib
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import build_scene as b
from common import ROOT, xyz, ZPP, RIGHT
from build_pass10_draft4 import quality
from build_pass10_draft7 import rain_layer, link_exterior
from build_pass10_draft5 import classify, outdoor, atmosphere
from pass8_common import gpu
from pngio import read, write

QA=ROOT/'qa10'; TMP=ROOT/'cache'/'draft10'
SOURCE=ROOT/'roxy_pass10_draft.blend'
D9_SHA='de035e87bc1ce1f12312224a895bfeb76c84f942b83281fce6d184c7493990ac'
R=random.Random(221010)


class Nodes:
    def __init__(self, tree): self.t=tree; self.n=tree.nodes; self.l=tree.links
    def node(self, typ, name=None):
        q=self.n.new(typ)
        if name: q.name=name; q.label=name
        return q
    def put(self, socket, value):
        if isinstance(value, (int,float,tuple,list,Vector)): socket.default_value=value
        else: self.l.new(value,socket)
    def math(self, op, *values):
        q=self.node('ShaderNodeMath'); q.operation=op
        for s,v in zip(q.inputs,values): self.put(s,v)
        return q.outputs[0]
    def vec(self, op, a, c=None):
        q=self.node('ShaderNodeVectorMath'); q.operation=op; self.put(q.inputs[0],a)
        if c is not None: self.put(q.inputs['Scale'] if op=='SCALE' else q.inputs[1],c)
        return q.outputs['Value'] if op in ['LENGTH','DOT_PRODUCT','DISTANCE'] else q.outputs[0]
    def xyz(self, x=0,y=0,z=0):
        q=self.node('ShaderNodeCombineXYZ')
        for s,v in zip(q.inputs,[x,y,z]): self.put(s,v)
        return q.outputs[0]
    def split(self, v):
        q=self.node('ShaderNodeSeparateXYZ');self.put(q.inputs[0],v);return q.outputs
    def ramp(self, v, a,b,c=0,d=1):
        q=self.node('ShaderNodeMapRange');q.clamp=True;q.interpolation_type='SMOOTHSTEP'
        for s,x in zip(q.inputs,[v,a,b,c,d]):self.put(s,x)
        return q.outputs[0]
    def mix(self, a,b,f):
        q=self.node('ShaderNodeMixRGB');self.put(q.inputs[0],f);self.put(q.inputs[1],a);self.put(q.inputs[2],b)
        return q.outputs[0]
    def noise(self, pos, scale=1, detail=2):
        q=self.node('ShaderNodeTexNoise');self.put(q.inputs['Vector'],pos);q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=detail
        return q.outputs['Fac']
    def attr(self, name):
        q=self.node('ShaderNodeAttribute');q.attribute_name=name;return q.outputs['Fac']


def interface(tree, name, typ, direction='INPUT', default=None):
    s=tree.interface.new_socket(name=name,in_out=direction,socket_type=typ)
    if default is not None:s.default_value=default
    return s


def bounds(o):
    ps=[o.matrix_world@Vector(p) for p in o.bound_box]
    return tuple(min(p[i] for p in ps) for i in range(3)),tuple(max(p[i] for p in ps) for i in range(3))


def collision_geometry(sc):
    """Author a hidden static ray target from the actual model, without particles."""
    verts=[];faces=[]
    for o in list(sc.objects):
        if o.type!='MESH' or o.hide_render or atmosphere(o):continue
        if any(s in o.name.lower() for s in ['bead','micro','splash','sparkle','rain streak','confetti','aggregate']):continue
        if len(o.data.vertices)>50000:continue
        start=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices)
        faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
    tree=BVHTree.FromPolygons(verts,faces)
    target=b.mesh('D10 static model raycast target',verts,faces,None)
    target.hide_render=True;target.hide_set(True);target['draft10_helper']=True
    print('D10 static collision geometry authored',len(verts),len(faces),flush=True)
    return target,tree


def wet_group():
    g=bpy.data.node_groups.new('D10 WetLayer - exposure porosity depth states','ShaderNodeTree');h=Nodes(g)
    for name,typ,val in [('Base Color','NodeSocketColor',(.1,.1,.1,1)),('Roughness','NodeSocketFloat',.5),('Metallic','NodeSocketFloat',0),('Porosity','NodeSocketFloat',.35),('Exposure','NodeSocketFloat',1),('Normal','NodeSocketVector',(0,0,1)),('Ripple Normal','NodeSocketVector',(0,0,1))]:interface(g,name,typ,default=val)
    for name,typ in [('Color','NodeSocketColor'),('Roughness','NodeSocketFloat'),('Coat','NodeSocketFloat'),('Coat Roughness','NodeSocketFloat'),('Coat Normal','NodeSocketVector'),('Wet','NodeSocketFloat'),('Pool','NodeSocketFloat')]:interface(g,name,typ,'OUTPUT')
    gi=h.node('NodeGroupInput');go=h.node('NodeGroupOutput');geo=h.node('ShaderNodeNewGeometry')
    p=h.split(geo.outputs['Position']);normal=geo.outputs['Normal'];nz=h.math('ABSOLUTE',h.split(geo.outputs['True Normal'])['Z'])
    # The model is a camera-open cutaway; this volume is still dry interior.
    tests=[h.math('GREATER_THAN',p['X'],.01),h.math('LESS_THAN',p['X'],12.99),h.math('LESS_THAN',p['Y'],-.03),h.math('GREATER_THAN',p['Y'],-8.92),h.math('LESS_THAN',p['Z'],175/ZPP)]
    inside=tests[0]
    for t in tests[1:]:inside=h.math('MULTIPLY',inside,t)
    outside=h.math('SUBTRACT',1,inside)
    broad=h.noise(geo.outputs['Position'],1.7,3)
    runoff=h.noise(h.vec('MULTIPLY',geo.outputs['Position'],(12,12,.28)),1,2)
    slope=h.ramp(nz,.08,.92,.50,1)
    cavity=h.ramp(broad,.18,.80,.65,1)
    wet=h.math('MULTIPLY',outside,h.math('MULTIPLY',gi.outputs['Exposure'],h.math('MULTIPLY',slope,cavity)))
    wet=h.math('MINIMUM',1,h.math('MULTIPLY',wet,h.ramp(runoff,0,1,.9,1.25)))
    poolable=h.attr('d10_poolable');level=h.attr('d10_water_level')
    height=h.math('ADD',p['Z'],h.math('MULTIPLY',h.math('SUBTRACT',broad,.38),.085))
    depth=h.math('SUBTRACT',level,height)
    pool=h.math('MULTIPLY',outside,h.math('MULTIPLY',poolable,h.math('MULTIPLY',h.ramp(nz,.90,.99),h.ramp(depth,-.002,.009))))
    drenched=h.math('MAXIMUM',h.ramp(wet,.25,.72),pool)
    # Lagarde albedo loss depends on porosity, never metallic colour.
    factor=h.math('SUBTRACT',1,h.math('MULTIPLY',.8,h.math('MULTIPLY',gi.outputs['Porosity'],h.math('SUBTRACT',1,gi.outputs['Metallic']))))
    albedo_factor=h.math('SUBTRACT',1,h.math('MULTIPLY',wet,h.math('SUBTRACT',1,factor)))
    color=h.vec('SCALE',gi.outputs['Base Color'],albedo_factor)
    rough=h.math('MULTIPLY',gi.outputs['Roughness'],h.math('SUBTRACT',1,h.math('MULTIPLY',.5,h.math('MULTIPLY',wet,h.math('SUBTRACT',1,factor)))))
    coat=h.math('MULTIPLY',outside,drenched)
    coatrough=h.math('ADD',.008,h.math('MULTIPLY',h.math('SUBTRACT',1,pool),.027))
    smooth=h.math('MULTIPLY',drenched,.65)
    # Vector math avoids colour clamping of signed normals.
    softened=h.vec('NORMALIZE',h.vec('ADD',h.vec('SCALE',gi.outputs['Normal'],h.math('SUBTRACT',1,smooth)),h.vec('SCALE',normal,smooth)))
    cn=h.vec('NORMALIZE',h.vec('ADD',h.vec('SCALE',softened,h.math('SUBTRACT',1,pool)),h.vec('SCALE',gi.outputs['Ripple Normal'],pool)))
    for name,value in [('Color',color),('Roughness',rough),('Coat',coat),('Coat Roughness',coatrough),('Coat Normal',cn),('Wet',wet),('Pool',pool)]:h.put(go.inputs[name],value)
    return g


def apply_wet(sc, sky):
    group=wet_group();cache={};count=0
    porosity={'asphalt':.30,'felt':.34,'paving':.38,'masonry':.38,'fabric':.43,'wood':.40,'paint':.14,'vegetation':.08,'metal':0,'glass':0,'water':0}
    original_objects=list(sc.objects)
    for o in original_objects:
        if o.type not in ['MESH','CURVE','FONT'] or o.hide_render or atmosphere(o) or not o.data.materials:continue
        if any(s in o.name.lower() for s in ['physical surface bead','micro impact','splash crown']):continue
        lo,hi=bounds(o);center=Vector(tuple((a+c)/2 for a,c in zip(lo,hi)))
        probes=[center]+[o.matrix_world@Vector(p) for p in o.bound_box]
        if not any(outdoor(p,o) for p in probes):continue
        if o.get('approved_meme') in ['whiplash','glorp']:continue
        top=Vector((center.x,center.y,hi[2]+.008))
        visible=sum(sky.ray_cast(top+Vector((dx,dy,0)),Vector((0,0,1)),60)[0] is None for dx,dy in [(0,0),(.06,0),(-.06,0),(0,.06),(0,-.06)])
        exposure=1.0 if visible>=3 else (.7 if visible else .42)
        # Substantial sheltered faces are damp from wind; explicitly indoor
        # geometry is gated to zero by position, regardless of material sharing.
        if o.data.users>1:o.data=o.data.copy()
        if o.type=='MESH':
            kinds=[classify(o,ma) for ma in o.data.materials if ma]
            flat=(hi[2]-lo[2])<.12 and (hi[0]-lo[0])*(hi[1]-lo[1])>.06
            poolable=flat and any(k in ['felt','asphalt','paving','water'] for k in kinds)
            for key,value in [('d10_poolable',float(poolable)),('d10_water_level',hi[2]+.006)]:
                a=o.data.attributes.get(key) or o.data.attributes.new(key,'FLOAT','POINT')
                a.data.foreach_set('value',[value]*len(a.data))
        for i,original in enumerate(list(o.data.materials)):
            if not original or not original.node_tree:continue
            kind=classify(o,original)
            key=(original.name,kind,exposure)
            if key not in cache:
                ma=original.copy();ma.name='D10 wet '+kind+' | '+original.name;h=Nodes(ma.node_tree)
                for p in [q for q in h.n if q.type=='BSDF_PRINCIPLED']:
                    q=h.node('ShaderNodeGroup','D10 WetLayer');q.node_tree=group
                    for src,dst in [('Base Color','Base Color'),('Roughness','Roughness'),('Metallic','Metallic')]:
                        inp=p.inputs[src];h.put(q.inputs[dst],inp.links[0].from_socket if inp.is_linked else inp.default_value[: ] if inp.type=='RGBA' else inp.default_value)
                    geo=h.node('ShaderNodeNewGeometry');normal=p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].is_linked else geo.outputs['Normal']
                    ripple=next((n.outputs['Normal'] for n in h.n if n.type=='GROUP' and n.node_tree and n.node_tree.name=='D4 periodic ray-traced rain ripple normals'),normal)
                    h.put(q.inputs['Normal'],normal);h.put(q.inputs['Ripple Normal'],ripple)
                    emissive=p.inputs['Emission Strength'].default_value>0 or p.inputs['Emission Strength'].is_linked
                    q.inputs['Porosity'].default_value=0 if emissive or o.get('approved_meme') else porosity[kind]
                    q.inputs['Exposure'].default_value=exposure
                    for src,dst in [('Color','Base Color'),('Roughness','Roughness'),('Coat','Coat Weight'),('Coat Roughness','Coat Roughness'),('Coat Normal','Coat Normal')]:h.put(p.inputs[dst],q.outputs[src])
                    p.inputs['Coat IOR'].default_value=1.33
                    # Retire only the old rough anisotropic asphalt water lobe.
                    if h.n.get('D5 directional water film'):
                        out=next(n for n in h.n if n.type=='OUTPUT_MATERIAL');h.put(out.inputs['Surface'],p.outputs[0])
                ma['d10_wet_layer']=True;ma['d10_surface_kind']=kind;cache[key]=ma
            o.data.materials[i]=cache[key]
        o['d10_exposure']=exposure;count+=1
    print('D10 wet-layer installed',count,'outdoor objects;',len(cache),'material variants',flush=True)
    return count


def water_material(name, flowing=False):
    ma=b.material('D10 '+name,(.015,.021,.025),.05)
    h=Nodes(ma.node_tree);p=h.n.get('Principled BSDF');geo=h.node('ShaderNodeNewGeometry')
    p.inputs['IOR'].default_value=1.33;p.inputs['Coat IOR'].default_value=1.33;p.inputs['Coat Weight'].default_value=1;p.inputs['Coat Roughness'].default_value=.012
    ripple=h.node('ShaderNodeGroup','Approved D4 ripples');ripple.node_tree=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'];ripple.inputs['Strength'].default_value=.55;h.put(ripple.inputs['Normal In'],geo.outputs['Normal'])
    normal=ripple.outputs['Normal']
    if flowing:
        uv=h.node('ShaderNodeTexCoord').outputs['UV'];phase=h.node('ShaderNodeValue','48-frame flow phase')
        phase.outputs[0].driver_add('default_value').driver.expression='((frame-1)%48)/48'
        pa=phase.outputs[0];pb=h.math('FRACT',h.math('ADD',pa,.5))
        a=h.vec('ADD',uv,h.xyz(h.math('MULTIPLY',pa,-.8),0,0));c=h.vec('ADD',uv,h.xyz(h.math('ADD',h.math('MULTIPLY',pb,-.8),.337),.179,0))
        na=h.noise(h.vec('MULTIPLY',a,(4,28,1)),3,2);nb=h.noise(h.vec('MULTIPLY',c,(4,28,1)),3,2)
        # A is zero-weight at its reset; B is zero-weight half a cycle later.
        wb=h.math('ABSOLUTE',h.math('SUBTRACT',1,h.math('MULTIPLY',pa,2)))
        val=h.math('ADD',h.math('MULTIPLY',na,h.math('SUBTRACT',1,wb)),h.math('MULTIPLY',nb,wb))
        bump=h.node('ShaderNodeBump','Two-phase advected water normal');bump.inputs['Distance'].default_value=.004;bump.inputs['Strength'].default_value=.32;h.put(bump.inputs['Height'],val);h.put(bump.inputs['Normal'],normal);normal=bump.outputs['Normal']
        ma['loop_frames']=48;ma['flow_phase_reset']='zero weight on each phase reset'
    h.put(p.inputs['Normal'],normal);h.put(p.inputs['Coat Normal'],normal)
    return ma


def pool_geometry_group():
    g=bpy.data.node_groups.new('D10 water-level field - blurred terrain height','GeometryNodeTree');interface(g,'Geometry','NodeSocketGeometry');interface(g,'Geometry','NodeSocketGeometry','OUTPUT');h=Nodes(g)
    gi=h.node('NodeGroupInput');go=h.node('NodeGroupOutput')
    height=h.node('GeometryNodeInputNamedAttribute');height.data_type='FLOAT';height.inputs['Name'].default_value='terrain_height'
    level=h.node('GeometryNodeInputNamedAttribute');level.data_type='FLOAT';level.inputs['Name'].default_value='water_level'
    blur=h.node('GeometryNodeBlurAttribute');blur.data_type='FLOAT';h.put(blur.inputs['Value'],height.outputs['Attribute']);blur.inputs['Iterations'].default_value=2
    depth=h.math('SUBTRACT',level.outputs['Attribute'],blur.outputs['Value'])
    store=h.node('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='water_depth';h.put(store.inputs['Geometry'],gi.outputs['Geometry']);h.put(store.inputs['Value'],depth)
    delete=h.node('GeometryNodeDeleteGeometry');delete.domain='FACE';h.put(delete.inputs['Geometry'],store.outputs['Geometry']);h.put(delete.inputs['Selection'],h.math('LESS_THAN',depth,-.025));h.put(go.inputs['Geometry'],delete.outputs['Geometry'])
    return g


def standing_water():
    b.layer('draft10_standing_water');g=pool_geometry_group();ma=water_material('depth-zoned pool and shoreline')
    h=Nodes(ma.node_tree);p=h.n.get('Principled BSDF');depth=h.attr('water_depth');pool=h.ramp(depth,-.001,.009)
    h.put(p.inputs['Roughness'],h.math('ADD',.012,h.math('MULTIPLY',h.math('SUBTRACT',1,pool),.31)))
    h.put(p.inputs['Coat Roughness'],h.math('ADD',.008,h.math('MULTIPLY',h.math('SUBTRACT',1,pool),.027)))
    trans=h.node('ShaderNodeBsdfTransparent');mix=h.node('ShaderNodeMixShader');h.put(mix.inputs[0],h.ramp(depth,-.025,-.006));h.put(mix.inputs[1],trans.outputs[0]);h.put(mix.inputs[2],p.outputs[0]);h.put(h.n.get('Material Output').inputs['Surface'],mix.outputs[0])
    # Bounds stay behind parapets / below kerbs. The terrain height controls
    # connected irregular basins, rather than arranging independent discs.
    regions=[('apartment roof',(-4.84,-.84,-.23,8.53),235.23,.022,1),('multiplex roof',(-3.8,-15,25,-.45),240.23,.012,2),('road low gutter',(-11,10.64,22,11.25),.18,.022,3),('road dips',(-10,11.3,22,13.42),.15,.006,4),('alley low side',(14.25,.05,14.96,9.08),.20,.028,5),('right roof',(15.05,6.50,17.45,9.04),61.17,.016,6)]
    for name,(u0,v0,u1,v1),z,level,seed in regions:
        nx=max(3,math.ceil((u1-u0)/.09));ny=max(3,math.ceil((v1-v0)/.09));verts=[];heights=[];faces=[]
        for j in range(ny+1):
            v=v0+(v1-v0)*j/ny
            for i in range(nx+1):
                u=u0+(u1-u0)*i/nx;verts.append(xyz(u,v,z))
                edge=min(u-u0,u1-u,v-v0,v1-v)
                noise=.027*math.sin(u*1.83+seed)*math.cos(v*1.39-seed)+.012*math.sin(u*4.27+v*2.8+seed)
                bowl=max(0,1-edge/.22)*.075
                heights.append(noise+bowl+.018)
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
        o=b.mesh('D10 standing water '+name,verts,faces,ma)
        for attr,values in [('terrain_height',heights),('water_level',[level]*len(verts))]:
            a=o.data.attributes.new(attr,'FLOAT','POINT');a.data.foreach_set('value',values)
        m=o.modifiers.new('Water level minus blurred terrain','NODES');m.node_group=g
        o['water_level_region']=name;o['standing_water']=True;o.visible_shadow=False
        link_exterior([o],apartment=name=='apartment roof')
    print('D10 standing-water regions authored',len(regions),flush=True)


def strip(name, points, width, ma):
    verts=[];faces=[];distance=[0]
    for i in range(1,len(points)):distance.append(distance[-1]+(points[i]-points[i-1]).length)
    for i,p in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)];side=Vector((-tangent.y,tangent.x,0)).normalized()
        w=width*(1-.65*i/(len(points)-1))
        verts.extend([p-side*w/2,p+side*w/2])
        if i:faces.append((2*i-2,2*i,2*i+1,2*i-1))
    o=b.mesh('D10 flowing '+name,verts,faces,ma);uv=o.data.uv_layers.new()
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            vi=o.data.loops[li].vertex_index;uv.data[li].uv=(distance[vi//2],vi%2)
    o['flow_to']=tuple(points[-1]);o['loop_frames']=48;o.visible_shadow=False;link_exterior([o]);return o


def flow_water():
    b.layer('draft10_flow');ma=water_material('two-phase curb gutter runoff',True)
    for drain,left,right in [(3.1,-3,5.5),(8.3,5.8,10.7),(14.3,11,20)]:
        for start in [left,right]:
            ps=[xyz(start+(drain-start)*t,10.76-.14*t*t,.19) for t in np.linspace(0,1,70)]
            strip('street to existing storm drain',ps,.27,ma)
    strip('alley to mouth drainage slots',[xyz(14.65,0.35+t*8.77,.21) for t in np.linspace(0,1,70)],.23,ma)
    for u in [2.8,6.6,10.4,12.95]:
        strip('multiplex roof gutter to hopper',[xyz(u-1.15+1.15*t,-.49,240.26) for t in np.linspace(0,1,35)],.19,ma)
    strip('apartment roof edge gutter',[xyz(-.30,1.0+7.4*t,235.28) for t in np.linspace(0,1,70)],.20,ma)
    strip('apartment roof front runoff',[xyz(-4.65+4.25*t,8.48,235.28) for t in np.linspace(0,1,50)],.18,ma)
    print('D10 two-phase curb, alley and roof drainage authored',flush=True)


def catcher_material(name,color,energy,sky=False):
    ma=bpy.data.materials.new('D10 catcher '+name);h=Nodes(ma.node_tree);h.n.clear()
    out=h.node('ShaderNodeOutputMaterial');em=h.node('ShaderNodeEmission');em.inputs['Color'].default_value=(*color,1);em.inputs['Strength'].default_value=energy
    geo=h.node('ShaderNodeNewGeometry');path=h.node('ShaderNodeLightPath');trans=h.node('ShaderNodeBsdfTransparent');mix=h.node('ShaderNodeMixShader')
    # Restrict emission to the downward-facing city reflection direction.
    # Upright glass reflects into a different hemisphere; transmission paths
    # cannot reveal an isolated luminous rectangle through that glass.
    aim=Vector((.612372,-.612372,-.5));dot=h.vec('DOT_PRODUCT',geo.outputs['Incoming'],aim)
    gate=h.math('MULTIPLY',h.ramp(dot,.91,.985),h.math('MULTIPLY',path.outputs['Is Glossy Ray'],h.math('LESS_THAN',path.outputs['Transmission Depth'],.5)))
    if sky:
        tex=h.node('ShaderNodeTexCoord');z=h.split(tex.outputs['Generated'])['Y'];h.put(em.inputs['Strength'],h.ramp(z,0,1,.35,energy))
    h.put(mix.inputs[0],gate);h.put(mix.inputs[1],trans.outputs[0]);h.put(mix.inputs[2],em.outputs[0]);h.put(out.inputs['Surface'],mix.outputs[0])
    return ma


def catchers():
    b.layer('draft10_glossy_city');view=Vector((-.612372,.612372,.5));vertical=Vector((.353553,-.353553,.866025))
    def card(name,target,distance,w,h,ma,side=0,up=0):
        center=target+view*distance+RIGHT*side+vertical*up
        pts=[center+RIGHT*x*w/2+vertical*y*h/2 for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        ob=b.mesh('D10 hidden city '+name,pts,[(0,1,2,3)],ma)
        for key,val in [('visible_camera',False),('visible_diffuse',False),('visible_glossy',True),('visible_transmission',False),('visible_shadow',False),('visible_volume_scatter',False)]:setattr(ob,key,val)
        ob['reflection_only']=True;return ob
    sky=catcher_material('sky glow',(.37,.47,.64),1.6,True)
    card('distant sky',xyz(5,7,150),37,48,17,sky)
    pink=catcher_material('distant pink tubing',(1,.16,.36),10)
    cyan=catcher_material('distant cyan tubing',(.15,.72,1),11)
    amber=catcher_material('occupied amber windows',(1,.59,.27),4.5)
    target=xyz(4.6,11.8,0)
    for side,ma in [(-5.6,pink),(.9,cyan),(7.2,pink)]:
        for j in range(4):card('fragmented neon',target,35,.10,.85,ma,side+j*.21,1.1+(j%2)*.23)
    for row in range(3):
        for col in range(8):
            if (row*7+col)%4==0:continue
            card('city window',target,37,.34,.66,amber,-7+col*1.7,-2.5+row*1.1)
    print('D10 off-camera glossy-only city reflection shapes authored',flush=True)


def drip_material():
    ma=b.material('D10 physical runoff water',(.86,.93,1),.025)
    p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.33;p.inputs['Coat Weight'].default_value=.15;p.inputs['Coat Roughness'].default_value=.025
    return ma


def crown_prototype(ma,ring=False):
    vs=[];fs=[];segments=36
    if ring:
        for j in range(segments):
            a=j*math.tau/segments
            for k in range(6):
                q=k*math.tau/6;r=.063+.0035*math.cos(q);vs.append((r*math.cos(a),r*math.sin(a),.0035*math.sin(q)+.004))
        for j in range(segments):
            for k in range(6):fs.append((j*6+k,((j+1)%segments)*6+k,((j+1)%segments)*6+(k+1)%6,j*6+(k+1)%6))
    else:
        for j in range(segments):
            a=j*math.tau/segments;spike=max(0,math.cos(a*9))**5
            for r,z in [(.027,.001),(.043,.010),(.053,.012+.030*spike)]:vs.append((r*math.cos(a),r*math.sin(a),z))
        for j in range(segments):
            for k in range(2):fs.append((j*3+k,((j+1)%segments)*3+k,((j+1)%segments)*3+k+1,j*3+k+1))
    ob=b.mesh('D10 '+('ring' if ring else 'crown')+' prototype',vs,fs,ma);ob.hide_render=True;ob.hide_set(True)
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def node_attr(h,name):
    q=h.node('GeometryNodeInputNamedAttribute');q.data_type='FLOAT';q.inputs['Name'].default_value=name;return q.outputs['Attribute']


def object_geometry(h,ob):
    q=h.node('GeometryNodeObjectInfo');q.transform_space='ORIGINAL';q.inputs['Object'].default_value=ob;return q.outputs['Geometry']


def drips(sc,target,sky):
    b.layer('draft10_stateless_drips');ma=drip_material();emit=[]
    def edge(name,a,c,spacing=.07):
        a=xyz(*a);c=xyz(*c);n=max(2,math.ceil((c-a).length/spacing))
        for j in range(n):emit.append((a.lerp(c,(j+.15+R.random()*.7)/n),name))
    # Locate current awnings and ACs from D9 geometry so later owner moves
    # cannot leave rain suspended at an obsolete position.
    for ob in list(sc.objects):
        name=ob.name.lower()
        if ob.type not in ['MESH','CURVE'] or ob.hide_render:continue
        lo,hi=bounds(ob)
        if 'awning' in name and ('soaked' in name or 'striped' in name):
            edge(ob.name,(lo[0],-lo[1]-.012,lo[2]*ZPP),(hi[0],-lo[1]-.012,lo[2]*ZPP))
        elif ' ac case' in name or 'additional hvac unit' in name:
            edge(ob.name,(lo[0],-lo[1]-.013,hi[2]*ZPP),(hi[0],-lo[1]-.013,hi[2]*ZPP),.09)
        elif ob.name=='Bus shelter steel roof':
            edge(ob.name,(lo[0],-lo[1]-.018,hi[2]*ZPP),(hi[0],-lo[1]-.018,hi[2]*ZPP))
    edge('WCAT sign bottom',(-.884,3.65,265.5),(-.884,7.44,265.5),.11)
    edge('EatFresh sign bottom',(-.684,.50,253.5),(-.684,3.10,253.5),.11)
    edge('apartment roof front',(-4.8,8.715,241.8),(-.22,8.715,241.8),.13)
    edge('apartment roof end',(-.06,0,241.8),(-.06,8.4,241.8),.18)
    edge('multiplex coping',(13.15,-.205,241),(21,-.205,241),.22)
    edge('right shop gutter',(15.03,9.12,61),(17.46,9.12,61),.10)
    # Downspout outlets: the pipes already end above the alley/service strip.
    for u in [2.8,6.6,10.4,12.95]:emit.append((xyz(u,-.44,172.5),'downspout outlet'))
    points=[];periods=[];phases=[]
    for p,name in emit:
        hit,_,_,dist=sky.ray_cast(p-Vector((0,0,.01)),Vector((0,0,-1)),30)
        if hit is None or dist<.035:continue
        points.append(p);periods.append(24 if dist<.75 else 48);phases.append(R.random()*periods[-1])
    ob=b.mesh('D10 stateless edge drips and impact crowns',points,[],None)
    for name,values in [('period',periods),('phase',phases)]:
        a=ob.data.attributes.new(name,'FLOAT','POINT');a.data.foreach_set('value',values)
    ob['drip_edge']=True;ob['timing']='pure frame modulo 24 or 48; no simulation';ob['landing']='downward Geometry Nodes Raycast against model'
    g=bpy.data.node_groups.new('D10 stateless Raycast drips crowns and landing rings','GeometryNodeTree');interface(g,'Geometry','NodeSocketGeometry');interface(g,'Geometry','NodeSocketGeometry','OUTPUT');h=Nodes(g);gi=h.node('NodeGroupInput');go=h.node('NodeGroupOutput')
    source=h.node('GeometryNodeMeshToPoints');source.mode='VERTICES';h.put(source.inputs['Mesh'],gi.outputs['Geometry'])
    pos=h.node('GeometryNodeInputPosition').outputs['Position'];clock=h.node('GeometryNodeInputSceneTime').outputs['Frame'];tau=h.math('MODULO',h.math('ADD',h.math('SUBTRACT',clock,1),node_attr(h,'phase')),node_attr(h,'period'))
    ray=h.node('GeometryNodeRaycast','Static model downward landing ray');ray.data_type='FLOAT';h.put(ray.inputs['Target Geometry'],object_geometry(h,target));h.put(ray.inputs['Source Position'],h.vec('ADD',pos,(0,0,-.01)));ray.inputs['Ray Direction'].default_value=(0,0,-1);ray.inputs['Ray Length'].default_value=30
    # Freeze the ray result on the ORIGINAL emitter points. Otherwise fields
    # evaluated after Set Position would cast from the falling bead instead.
    cached=source.outputs['Points']
    for name,typ,value in [('landing_position','FLOAT_VECTOR',ray.outputs['Hit Position']),('landing_distance','FLOAT',ray.outputs['Hit Distance']),('landing_hit','BOOLEAN',ray.outputs['Is Hit'])]:
        store=h.node('GeometryNodeStoreNamedAttribute');store.domain='POINT';store.data_type=typ;store.inputs['Name'].default_value=name;h.put(store.inputs['Geometry'],cached);h.put(store.inputs['Value'],value);cached=store.outputs['Geometry']
    hitpos=h.node('GeometryNodeInputNamedAttribute');hitpos.data_type='FLOAT_VECTOR';hitpos.inputs['Name'].default_value='landing_position'
    ishit=node_attr(h,'landing_hit')
    height=h.math('ADD',node_attr(h,'landing_distance'),.01);impact=h.math('ADD',3,h.math('MULTIPLY',24,h.math('SQRT',h.math('DIVIDE',h.math('MULTIPLY',2,height),9.81))))
    flight=h.math('DIVIDE',h.math('MAXIMUM',0,h.math('SUBTRACT',tau,3)),24);fall=h.math('MULTIPLY',4.905,h.math('MULTIPLY',flight,flight))
    moving=h.node('GeometryNodeSetPosition');h.put(moving.inputs['Geometry'],cached);h.put(moving.inputs['Offset'],h.xyz(0,0,h.math('MULTIPLY',fall,-1)))
    ico=h.node('GeometryNodeMeshIcoSphere');ico.inputs['Radius'].default_value=1;ico.inputs['Subdivisions'].default_value=2
    material=h.node('GeometryNodeSetMaterial');h.put(material.inputs['Geometry'],ico.outputs['Mesh']);material.inputs['Material'].default_value=ma
    drops=h.node('GeometryNodeInstanceOnPoints');h.put(drops.inputs['Points'],moving.outputs['Geometry']);h.put(drops.inputs['Instance'],material.outputs['Geometry']);h.put(drops.inputs['Selection'],h.math('MULTIPLY',ishit,h.math('LESS_THAN',tau,impact)))
    radius=h.math('ADD',.007,h.math('MULTIPLY',.004,h.math('MINIMUM',1,h.math('DIVIDE',tau,3))));stretch=h.math('ADD',1,h.math('MULTIPLY',flight,3))
    h.put(drops.inputs['Scale'],h.xyz(radius,radius,h.math('MULTIPLY',radius,stretch)))
    landing=h.node('GeometryNodeSetPosition');h.put(landing.inputs['Geometry'],cached);h.put(landing.inputs['Position'],h.vec('ADD',hitpos.outputs['Attribute'],(0,0,.004)))
    join=h.node('GeometryNodeJoinGeometry');h.put(join.inputs['Geometry'],drops.outputs['Instances']);age=h.math('SUBTRACT',tau,impact)
    for ring,duration in [(False,5),(True,12)]:
        proto=crown_prototype(ma,ring);inst=h.node('GeometryNodeInstanceOnPoints');h.put(inst.inputs['Points'],landing.outputs['Geometry']);h.put(inst.inputs['Instance'],object_geometry(h,proto))
        selection=h.math('MULTIPLY',ishit,h.math('MULTIPLY',h.math('GREATER_THAN',age,0),h.math('LESS_THAN',age,duration)))
        h.put(inst.inputs['Selection'],selection);a=h.math('DIVIDE',age,duration);size=h.math('ADD',.35,h.math('MULTIPLY',a,1.7 if ring else 1.0));zscale=h.math('MAXIMUM',.05,h.math('SUBTRACT',1,a));h.put(inst.inputs['Scale'],h.xyz(size,size,zscale));h.put(join.inputs['Geometry'],inst.outputs['Instances'])
    h.put(go.inputs['Geometry'],join.outputs['Geometry']);mod=ob.modifiers.new('Stateless falling water and impacts','NODES');mod.node_group=g;link_exterior([ob],True)
    print('D10 stateless GN drips',len(points),'raycast emitters',flush=True)
    pours(sc,sky,ma)


def pours(sc,sky,ma):
    verts=[];edges=[];parameters=[]
    sources=[(-.24,8.72,237),(-3.72,.825,260),(-1.02,6.805,260),(15.15,9.13,60),(2.8,-.44,172.5),(12.95,-.44,172.5)]
    for u,v,z in sources:
        p=xyz(u,v,z);hit,_,_,distance=sky.ray_cast(p-Vector((0,0,.012)),Vector((0,0,-1)),30)
        if hit is None or distance<.06:continue
        flight=math.sqrt(2*distance/9.81);base=len(verts)
        for j in range(33):
            t=j/32;seconds=flight*t;verts.append(p+Vector((.055*seconds,-.025*seconds,-4.905*seconds**2)));parameters.append(t)
            if j:edges.append((base+j-1,base+j))
    me=bpy.data.meshes.new('D10 ballistic outlet paths');me.from_pydata(verts,edges,[]);me.update();ob=bpy.data.objects.new('D10 stateless gutter and AC pours',me);sc.collection.objects.link(ob)
    attr=me.attributes.new('flow_parameter','FLOAT','POINT');attr.data.foreach_set('value',parameters)
    g=bpy.data.node_groups.new('D10 periodic ballistic pour curves to water tubes','GeometryNodeTree');interface(g,'Geometry','NodeSocketGeometry');interface(g,'Geometry','NodeSocketGeometry','OUTPUT');h=Nodes(g);gi=h.node('NodeGroupInput');go=h.node('NodeGroupOutput')
    clock=h.node('GeometryNodeInputSceneTime').outputs['Frame'];angle=h.math('MULTIPLY',h.math('SUBTRACT',clock,1),math.tau/48);pos=h.node('GeometryNodeInputPosition').outputs['Position'];xy=h.split(pos)
    noise=h.node('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=6;noise.inputs['Detail'].default_value=2
    h.put(noise.inputs['Vector'],h.xyz(xy['X'],xy['Y'],h.math('COSINE',angle)));h.put(noise.inputs['W'],h.math('SINE',angle))
    amp=h.math('MULTIPLY',.016,h.math('SINE',h.math('MULTIPLY',node_attr(h,'flow_parameter'),math.pi)))
    offset=h.vec('SCALE',h.vec('SUBTRACT',noise.outputs['Color'],(.5,.5,.5)),amp)
    move=h.node('GeometryNodeSetPosition');h.put(move.inputs['Geometry'],gi.outputs['Geometry']);h.put(move.inputs['Offset'],offset)
    curve=h.node('GeometryNodeMeshToCurve');h.put(curve.inputs['Mesh'],move.outputs['Geometry'])
    circle=h.node('GeometryNodeCurvePrimitiveCircle');circle.inputs['Resolution'].default_value=8;circle.inputs['Radius'].default_value=.007
    tube=h.node('GeometryNodeCurveToMesh');h.put(tube.inputs['Curve'],curve.outputs['Curve']);h.put(tube.inputs['Profile Curve'],circle.outputs['Curve']);tube.inputs['Fill Caps'].default_value=True
    mat=h.node('GeometryNodeSetMaterial');mat.inputs['Material'].default_value=ma;h.put(mat.inputs['Geometry'],tube.outputs['Mesh']);h.put(go.inputs['Geometry'],mat.outputs['Geometry'])
    mod=ob.modifiers.new('48-frame stateless pour','NODES');mod.node_group=g;ob['loop_frames']=48;link_exterior([ob],True)


def main():
    start=time.perf_counter();TMP.mkdir(parents=True,exist_ok=True);backup=TMP/'source_draft9.blend'
    if not backup.exists():
        assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==D9_SHA,'Source must be the saved, unmodified Draft 9'
        shutil.copy2(SOURCE,backup)
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==D9_SHA
    assert not (TMP/'render_started').exists(),'Do not rerender: recover existing buffers if postprocessing was interrupted'
    bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene;b.GROUPS.clear();b.M.clear();bpy.context.view_layer.update()
    b.layer('draft10_helpers');target,sky=collision_geometry(sc)
    count=apply_wet(sc,sky);standing_water();flow_water();catchers();drips(sc,target,sky)
    # Preserve the existing optical node tree, exposure, camera and artwork.
    quality(sc);gpu(sc);sc.cycles.use_denoising=True;sc.cycles.use_light_tree=True
    sc.render.use_motion_blur=True;sc.render.motion_blur_shutter=.5
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    sc.render.use_compositing=True;sc.frame_set(1);sc['draft10_brief']='BRIEF-22-draft10.md corrected items 1-4 plus catchers';sc['draft10_loop_frames']=48
    sc.render.filepath=str(QA/'draft_10.png');bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    print('D10 modeling complete; starting the single final-quality camera exposure with weather',flush=True)
    (TMP/'render_started').write_text(datetime.now().astimezone().isoformat(),encoding='utf-8')
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png';t=time.perf_counter()
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True);beauty_seconds=time.perf_counter()-t
    t=time.perf_counter();rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True);weather_seconds=time.perf_counter()-t
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False);alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8);write(QA/'draft_10.png',out)
    beauty.unlink();weather.unlink()
    (QA/'DRAFT-10.md').write_text(
        '# Draft 10\n\n'
        'Restarted from the hash-verified saved Draft 9; updated `roxy_pass10_draft.blend`.\n'
        f'Added the corrected owner selection: WetLayer on {count} outdoor objects (porosity, exposure/slope/cavity masks, dry/wet/drenched/pool states, IOR 1.33 coat; cutaway interior stays dry); blurred terrain-height/water-level ponding and shoreline bands on roofs, road dips, low curb and alley; two-phase 48-frame runoff to existing drains and gutters; stateless Geometry Nodes edge drops with downward model raycasts, ballistic pours, impact crowns and rings.\n'
        'Added camera/diffuse/transmission-invisible city window, neon and sky emitters for glossy reflections over dark water; emission is direction-gated to keep floating cards out of upright glass. Retained the approved D9 models/art, camera, soft ray-traced ripples and HDR glare. No car effects.\n'
        f'One delivered image: `draft_10.png`, 1280 x 720, Cycles 256 fixed samples, OptiX denoising, 0.5 shutter, with current-scene occluded weather. Render time: {beauty_seconds:.1f} s beauty + {weather_seconds:.1f} s weather = {beauty_seconds+weather_seconds:.1f} s; total build/composite {time.perf_counter()-start:.1f} s. Loop-capable nodes were authored; no clips or seam audits were run. Stopped.\n',encoding='utf-8')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: corrected Draft 10 from saved D9; wet-layer, standing water, two-phase runoff, hidden glossy catchers and stateless GN drips/pours/splashes; one 720p/256-sample weather-composited draft_10.png; DRAFT-10.md records render time; stopped.\n')
    print('D10 COMPLETE. ONE IMAGE. STOP.',flush=True)


if __name__=='__main__':main()
