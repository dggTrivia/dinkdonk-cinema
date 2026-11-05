"""Six independently hinged open/hold/close door sequences, actual scene lighting."""
import sys,json,math,time,argparse,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Matrix
import build_scene as b
from build_pass6 import DOORS
from common import ROOT,xyz,project,render
from render_loop_basis import crop
QA=ROOT/'qa6'

def amount(i):
    # 5-frame ease open, 6-frame hold, 5-frame ease shut; endpoints identical.
    p=min(1,i/5,(15-i)/5);return .5-.5*math.cos(math.pi*max(0,p))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--resume',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass6.blend'));sc=bpy.context.scene
    sc.render.use_compositing=False;sc.render.film_transparent=False;sc.cycles.samples=48;sc.cycles.adaptive_threshold=.02
    sc.render.threads_mode='AUTO'
    # Hidden props keep their indirect influence exactly as in the background pass.
    for ob in sc.objects:
        if ob.type in ['MESH','FONT','CURVE']:ob.visible_camera=ob.get('layer')=='background';ob.is_holdout=False
    sc.render.resolution_x=3840;sc.render.resolution_y=2160
    original={ob.name:ob.matrix_world.copy() for ob in sc.objects if 'door_id' in ob}
    b.GROUP='background';b.GROUPS.clear();records=[];start=time.perf_counter()
    for idx,(wall,at) in enumerate(DOORS+[('u',8.3)],1):
        number=idx if idx<6 else 'wc';width=.8 if idx==6 else 1.1
        x,y=project(0,at) if wall=='u' else project(at,0)
        # Includes the full doorway, both leaves and the feathered floor spill.
        rect=[int(x)-61,int(y)-139,156,204] if wall=='u' else [int(x)-95,int(y)-139,156,204]
        crop(sc,dict(zip(['x','y','w','h'],rect)))
        point=b.point('Pass6 opening spill',b.wp(wall,at,45,-.22),0,(1,.49,.16),.28)
        leaves=[ob for ob in sc.objects if ob.get('door_id')==str(number)]
        for i in ([0,7] if args.preview else range(16)):
            opened=amount(i)
            for ob in leaves:
                side=ob['door_side'];hinge_at=(7.95 if idx==6 else at+side*.465)
                pivot=b.wp(wall,hinge_at,0,.028 if idx<6 else .031)
                angle=math.radians(79)*opened*side*(1 if wall=='u' else -1)
                ob.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-pivot)@original[ob.name]
            point.data.energy=7.5*opened
            target=QA/('doors_preview' if args.preview else 'doors_raw')/str(number)/('f'+str(i).zfill(3)+'.png')
            canonical=min(i,15-i,5)
            source=target.with_name('f'+str(canonical).zfill(3)+'.png')
            if canonical!=i and source.exists():shutil.copyfile(source,target)
            elif not args.resume or not target.exists():render(target)
        for ob in leaves:ob.matrix_world=original[ob.name]
        bpy.data.objects.remove(point,do_unlink=True)
        records.append({'door':number,'wall':wall+'0','at':at,'x':rect[0],'y':rect[1],'frame_width':rect[2],'frame_height':rect[3],
            'frames':16,'columns':4,'rows':4,'fps':18,'seconds':16/18,'loop':False,'z_index':900})
        print('PASS6_DOOR',number,round(time.perf_counter()-start,2),flush=True)
    (QA/('doors_preview_metadata.json' if args.preview else 'doors_metadata.json')).write_text(json.dumps({'seconds':round(time.perf_counter()-start,3),'unique_rendered_states_per_door':6,'timing':'Six eased opening poses, hold fully open, reverse the exact poses to close. Sixteen delivered frames.','doors':records},indent=2))

if __name__=='__main__':main()
