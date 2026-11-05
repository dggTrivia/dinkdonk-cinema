"""Pass 5 additions only: vehicle surface coordinates and lamp-state renders."""
import sys,json,math,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix
import build_scene as b
import build_vehicles as v
import depth_pass
from common import ROOT,setup,xyz,render

QA=ROOT/'qa5';TIMES=[]

def crop(sc,scale):
    sc.render.resolution_x=1920*scale;sc.render.resolution_y=1080*scale
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=300.1/1920;sc.render.border_max_x=910.1/1920
    sc.render.border_min_y=50.1/1080;sc.render.border_max_y=450.1/1080

def scene(kind,direction,opened,samples):
    sc=setup(samples,1,True);b.GROUPS.clear();b.META.clear();b.GROUP='vehicle'
    sc.render.use_compositing=False;sc.compositing_node_group=None
    for aov in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(aov)
    b.FONT=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf');v.M.clear();v.palette(kind)
    before=set(sc.objects);v.bus(opened) if kind=='bus' else v.sedan(kind,opened)
    model=set(sc.objects)-before;bpy.context.view_layer.update()
    transform=Matrix.Translation(xyz(*v.ORIGIN))@Matrix.Rotation(math.pi if direction=='minus' else 0,4,'Z')
    for ob in model:ob.matrix_world=transform@ob.matrix_world
    return sc,model,transform

def positions(kind,direction,opened,name):
    sc,model,_=scene(kind,direction,opened,12)
    sc.cycles.device='CPU';sc.cycles.use_denoising=False;sc.cycles.max_bounces=1
    # Opaque nearest-surface ownership; the delivered beauty and glass alpha stay untouched.
    mat=b.material('Pass5 surface owner',(.2,.2,.2),1)
    for ob in model:
        if ob.type=='LIGHT':ob.hide_render=True
        elif hasattr(ob.data,'materials'):
            for i in range(len(ob.data.materials)):ob.data.materials[i]=mat
    folder=QA/'position_exr'/name;folder.mkdir(parents=True,exist_ok=True)
    node=depth_pass.configure(sc,folder);sc.render.use_compositing=True
    for scale,suffix in [(1,''),(2,'@2x')]:
        crop(sc,scale);node.file_name='owner'+suffix
        render(QA/'position_preview'/(name+suffix+'.png'))
        files=list(folder.glob('owner'+suffix+'*.exr'))
        if scale==1:files=[p for p in files if '@2x' not in p.name]
        assert len(files)==1,files
        target=QA/'positions'/(name+suffix+'.npz');target.parent.mkdir(parents=True,exist_ok=True)
        depth_pass.export_array(files[0],target)

def lights(kind,direction,opened,name,samples):
    sc,model,transform=scene(kind,direction,opened,samples)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    sc.render.film_transparent=False
    for ob in model:
        if ob.type!='LIGHT':ob.visible_camera=False
    receiver=v.receiver();receiver.location+=xyz(*v.ORIGIN)
    original_energy={ob:ob.data.energy for ob in model if ob.type=='LIGHT'}
    tail=v.M['tail'].node_tree.nodes.get('Principled BSDF');tail_original=tail.inputs['Emission Strength'].default_value
    amber=v.M['amber'].node_tree.nodes.get('Principled BSDF');amber_original=amber.inputs['Emission Strength'].default_value
    indicators=[]
    if kind in ['bus','taxi']:
        L=v.SPECS[kind]['length'];width=v.SPECS[kind]['width']
        for x in [-L/2+.08,L/2-.08]:
            ob=b.point('Pass5 curb amber lamp',xyz(x,-width/2-.025,31 if kind=='bus' else 13),0,(1,.20,.008),.06)
            ob.matrix_world=transform@ob.matrix_world;indicators.append(ob)
    states=['normal','brake']+(['indicator'] if indicators else [])
    for state in states:
        for ob,energy in original_energy.items():ob.data.energy=energy*(6 if state=='brake' and ob.name.startswith('Red tail reflection') else 1)
        tail.inputs['Emission Strength'].default_value=tail_original*(3.8 if state=='brake' else 1)
        amber.inputs['Emission Strength'].default_value=amber_original*(4 if state=='indicator' else 1)
        for ob in indicators:ob.data.energy=9 if state=='indicator' else 0
        for scale,suffix in [(1,''),(2,'@2x')]:
            crop(sc,scale);render(QA/'light_raw'/(name+'_'+state+suffix+'.png'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--samples',type=int,default=96);ap.add_argument('--kind',choices=list(v.SPECS));ap.add_argument('--positions-only',action='store_true')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    QA.mkdir(exist_ok=True);started=time.perf_counter()
    for kind in ([args.kind] if args.kind else v.SPECS):
        for direction in ['plus','minus']:
            for opened in ([False,True] if kind in ['bus','taxi'] else [False]):
                name=kind+'_'+direction+('_open' if opened else '');t=time.perf_counter()
                positions(kind,direction,opened,name)
                if not args.positions_only:lights(kind,direction,opened,name,args.samples)
                TIMES.append({'name':name,'seconds':round(time.perf_counter()-t,3)})
                (QA/'vehicle_render_times.json').write_text(json.dumps({'seconds':round(time.perf_counter()-started,3),'records':TIMES},indent=2))
                print('PASS5_VEHICLE',name,TIMES[-1]['seconds'],flush=True)

if __name__=='__main__':main()
