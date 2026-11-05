"""H.264 motion review plus decoding of the actual exported movie."""
from pathlib import Path
import sys,json,warnings,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT
warnings.filterwarnings('ignore',category=DeprecationWarning)
QA=ROOT/'qa6';FRAMES=QA/'preview_frames'
start=time.perf_counter();sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=1280;sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.render.fps=24;sc.frame_start=1;sc.frame_end=144;sc.render.use_sequencer=True;sc.render.use_compositing=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.sequencer_colorspace_settings.name='sRGB';ed=sc.sequence_editor_create()
strip=ed.strips.new_image('Pass6 delivered sprite motion review',str(FRAMES/'f000.png'),1,1)
for i in range(1,144):strip.elements.append('f'+str(i).zfill(3)+'.png')
strip.frame_final_duration=144;sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.image_settings.color_mode='RGB'
ff=sc.render.ffmpeg;ff.format='MPEG4';ff.codec='H264';ff.audio_codec='NONE';ff.constant_rate_factor='HIGH';ff.ffmpeg_preset='GOOD'
sc.render.use_file_extension=False;sc.render.filepath=str(QA/'pass6_preview.mp4');bpy.ops.render.render(animation=True)
ed.strips.remove(strip);movie=ed.strips.new_movie('Actual pass6 decode',str(QA/'pass6_preview.mp4'),1,1)
assert movie.frame_duration==144 and (movie.elements[0].orig_width,movie.elements[0].orig_height)==(1280,800)
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
for frame in [0,24,48,71,100,143]:
    sc.frame_set(frame+1);sc.render.filepath=str(QA/('preview_decoded_f'+str(frame).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
(QA/'preview_metadata.json').write_text(json.dumps({'frames':144,'fps':24,'seconds':6,'size':[1280,800],'bytes':(QA/'pass6_preview.mp4').stat().st_size,'encode_decode_seconds':round(time.perf_counter()-start,3),'decoded_frames':[0,24,48,71,100,143]},indent=2))
