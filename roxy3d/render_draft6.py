import sys,time,json,hashlib,argparse,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from common import xyz
from pass8_common import gpu
from build_pass10_draft4 import quality
from build_pass10_draft6 import neon_state
from render_draft5 import optical
from draft6_common import *

VIEWS={
 'restroom':((1.45,5.60,58),4.10,(5,-5,6.5)),
 'alley':((14.85,.85,105),5.4,(2,-5,5.7)),
 'alley_ground':((14.10,6.05,4),3.2,(.7,-1.6,6)),
 'bus_stop':((1.17,9.52,64),4.65,(1.7,-6,.45)),
 'roof_A':((4.63,-.58,364),2.20,(1,-6,1.8)),
 'roof_B':((4.63,-.58,364),2.20,(1,-6,1.8)),
 'eatfresh':((2.435,9.06,130),1.1,(.7,-6,1.6)),
 'frontage':((-4.30,8.1,51),8.4,(2,-6,3)),
 'greengrocer':((-1.60,8.9,43),3.4,(1.2,-6,2.7)),
 'restroom_mirror':((2.36,3.16,79),1.55,(1.5,-6,2.4)),
 'entrance_script':((-.45,9.28,188),1.85,(1.3,-6,2.5)),
}

def main():
    names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['preview']
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    optical(sc);sc.compositing_node_group.name='D6 retained HDR glare'
    initial=sc.camera.matrix_world.copy();scale=sc.camera.data.ortho_scale;signature=hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest()
    rp=WORK/'renders.json';rows=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {}
    for name in names:
        neon_state(sc,'B' if name=='roof_B' else 'A')
        if name=='preview':
            sc.camera.matrix_world=initial;sc.camera.data.ortho_scale=scale;sc.render.resolution_x=1280;sc.render.resolution_y=720;out=QA/'draft_6_clean.png'
        else:
            target,ortho,offset=VIEWS[name];off=Vector(offset).normalized()*(5 if name=='bus_stop' else 30);sc.camera.location=xyz(*target)+off;sc.camera.rotation_mode='QUATERNION';sc.camera.rotation_quaternion=(-off).to_track_quat('-Z','Y');sc.camera.data.ortho_scale=ortho;sc.render.resolution_x=1280;sc.render.resolution_y=960;out=QA/('draft_6_'+name+'.png')
        sc.render.filepath=str(out);st=time.perf_counter();bpy.ops.render.render(write_still=True);sec=time.perf_counter()-st
        rows[name]={'file':out.name,'size':[sc.render.resolution_x,sc.render.resolution_y],'samples':256,'seed':1701,'adaptive':False,'denoise':'per-frame OptiX','glare':'retained D4/D5 HDR bloom, fog glow, restrained aperture streaks','state':sc['d6_neon_state'],'seconds':sec,'source_sha256':signature,'camera_matrix':[v for row in sc.camera.matrix_world for v in row]};report('renders.json',rows)
        status(name+' final-quality still rendered at 256 samples (%.1f seconds)'%sec)
if __name__=='__main__':main()
