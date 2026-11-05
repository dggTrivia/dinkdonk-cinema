"""Brief 9b: readable neighbourhood, indigo sky, warm shops and roof highlights."""
import math,random,json
import bpy
from mathutils import Vector
import build_scene as b
from common import ROOT,xyz,ZPP
from pass8_common import status

def apply(sc,city):
    M=city.M;box=city.box;line=city.line;cyl=city.cyl
    # A real enclosing sky dome, with volumetric-looking procedural low clouds.
    # Orthographic rays are parallel, so a world-direction gradient alone would
    # be flat. Position on this distant sphere supplies the height variation.
    mat=b.material('P8 indigo cloud dome',(.025,.012,.065),1,emit=1)
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');geo=n.new('ShaderNodeNewGeometry')
    sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');mapping=n.new('ShaderNodeMapRange')
    mapping.inputs['From Min'].default_value=-92;mapping.inputs['From Max'].default_value=-60
    mapping.inputs['To Min'].default_value=0;mapping.inputs['To Max'].default_value=1
    l.new(sep.outputs['Z'],mapping.inputs['Value']);l.new(mapping.outputs['Result'],ramp.inputs[0])
    ramp.color_ramp.elements[0].color=(.060,.018,.10,1);ramp.color_ramp.elements[1].color=(.006,.003,.018,1)
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.08;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.65
    stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(1,1,4)
    l.new(geo.outputs['Position'],stretch.inputs[0]);l.new(stretch.outputs[0],noise.inputs['Vector'])
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55
    l.new(ramp.outputs['Color'],mix.inputs[1]);l.new(noise.outputs['Fac'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Emission Color'])
    p.inputs['Base Color'].default_value=(0,0,0,1)
    ob=b.ball('P8 enclosing indigo cloud sky',(0,0,0),150,mat)
    ob.visible_shadow=False;ob.visible_diffuse=False;ob.visible_glossy=True;ob['pass8_sky']=True
    # Preserve the existing cinema light balance using receiver-linked city fill.
    receivers=bpy.data.collections.new('P8 surroundings light receivers');sc.collection.children.link(receivers)
    for ob in city.NEW:receivers.objects.link(ob)
    fills=[('indigo sky bounce',(-4,5,720),1500,(.43,.47,.70),24,(-2,5,120)),
           ('street horizon fill',(4,20,450),1100,(.61,.48,.61),24,(4,7,120)),
           ('billboard brick fill',(19,7,680),1200,(.52,.55,.67),18,(11,-1,220)),
           ('opposite wet roof fill',(4,19,520),950,(.48,.50,.69),18,(5,18,100)),
           ('rear horizon bounce',(0,-4,650),1000,(.46,.31,.61),22,(0,-4,0))]
    for name,pos,power,color,size,target in fills:
        lamp=b.area('P8 '+name,xyz(*pos),power,color,size,target=xyz(*target))
        lamp.light_linking.receiver_collection=receivers
    # Added lamps light the far sidewalk and roofs; their poles are set back
    # enough to obey the same conservative clearance envelope as the roofs.
    for u in [-2,4.3,10.2]:
        v=15.65
        cyl('far sidewalk lamp post',u,v,0,.022,68,'metal')
        cyl('far sidewalk lamp foot',u,v,0,.055,5,'metal')
        ob=b.ball('P8 warm far pavement globe',xyz(u,v,70),.06,M['amber']);city.NEW.append(ob)
        b.point('P8 far sidewalk warm pool',xyz(u,v,70),30,(1,.63,.31),.19)
    # Bright enough to read, with less saturation and luminance than the Roxy.
    sign=city.mat('lit cream sign letters',(.68,.51,.27),.55,emit=1.3)
    rental=city.mat('video fascia soft olive',(.08,.16,.13),.75,emit=.18)
    noodles=city.mat('noodle fascia faded oxblood',(.18,.055,.035),.8,emit=.18)
    for ob in sc.objects:
        if ob.name.startswith('P8 sign '):
            ob.data.materials.clear();ob.data.materials.append(sign)
            if 'TAKE AWAY' in ob.name:ob.data.body='NOODLES'
            if 'RECORDS / REPAIRS' in ob.name:ob.data.body='RECORDS & REPAIR'
        if ob.name.startswith('P8 shop fascia'):
            ob.data.materials.clear();ob.data.materials.append(rental if ob.location.x<-2.6 else noodles)
    for u in [-3.7,-1.9]:
        b.area('P8 neighbour shop sign pool',xyz(u,8.95,58),8,(.72,.80,.52) if u<-2.6 else (1,.47,.23),1.3,target=xyz(u,9.8,0))
    # Original opposite shop signage faces the street. Back bracing stays visible
    # from the camera, while the signs cast coloured real reflections on asphalt.
    for i,(u,name) in enumerate([(0.6,'NIGHT OWL DINER'),(5.65,'LAUNDERETTE'),(11.05,'AUTO ELECTRIC')]):
        ob=b.text('P8 opposite sign '+name,name,xyz(u,16.929,[114,123,130][i]),.15,sign,
                  rotation=b.FRONT_FACE);ob.rotation_euler.rotate_axis('Z',math.pi)
        city.NEW.append(ob)
    # Readable roof kit: the large top-left block is no longer an empty slab.
    box('left roof access hatch',-4.4,5.1,-3.75,5.8,236,242,'greenpaint')
    box('left roof hatch handle',-4.05,5.3,-3.99,5.5,242,244,'metal')
    box('left roof HVAC secondary',-3.5,1.0,-2.55,1.75,239,257,'metal')
    for u in [-3.23,-2.82]:cyl('second HVAC fan',u,1.36,257,.14,1,'ink')
    line('roof extraction duct',[(-3.6,1.4,246),(-4.1,1.4,246),(-4.1,3.7,246),(-3.8,3.7,246)],.10,'metal')
    cyl('steam roof outlet',-3.8,3.7,246,.10,18,'metal')
    for u in [-4.93,-1.27]:box('left parapet coping',u,-.96,u+.09,8.66,240,242,'stone')
    # 37 percent lit, predominantly amber, with a few cool television windows.
    rng=random.Random(8902);windows=[o for o in sc.objects if o.name.startswith('P8 lit recessed window')]
    rng.shuffle(windows);lit_count=round(len(windows)*.37);tv=[]
    for i,ob in enumerate(windows):
        color=('tv' if i%13==0 else 'dimwindow' if i%6==0 else 'amber') if i<lit_count else 'darkglass'
        ob.data.materials.clear();ob.data.materials.append(M[color]);ob['pass8_tv']=color=='tv'
        if color=='tv':tv.append(ob.name)
    # Shallow glossy roof pools capture the broad fills without mirror-flat roofs.
    for name in ['P8 tar','P8 gravel']:
        ma=bpy.data.materials.get(name)
        if ma:
            p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.22;p.inputs['Coat Roughness'].default_value=.16
    haze=bpy.data.materials.get('P8 distant rain haze')
    if haze:
        node=next(n for n in haze.node_tree.nodes if n.type=='PRINCIPLED_VOLUME')
        node.inputs['Emission Color'].default_value=(.055,.020,.10,1)
        node.inputs['Emission Strength'].default_value=.0025
    for ob in city.NEW:ob['pass8_surrounding']=True
    (ROOT/'qa8/lighting_changes.json').write_text(json.dumps({'window_count':len(windows),'lit_windows':lit_count,
        'lit_fraction':lit_count/len(windows),'tv_windows':tv,'fills_receiver_linked':True,
        'sky':'3D procedural indigo-violet cloud dome; warm horizon, separate distant volumetric haze.',
        'corrected_occlusion':'Left fire escape moved from v=8.84..9.24 to v=8.69..9.09, behind sidewalk v=9.15.',
        'interruption_check':'Initial .blend and preview complete; first holdout failed (198 pixels), no loops or out8 files had been written. Scene rebuilt; initial preview retained.'},indent=2))
    status('Brief 9b lighting applied: indigo cloud dome, linked city fill, readable roofs/facades, warm signs and far lamps, 37 percent lit windows; initial interrupted outputs audited')
