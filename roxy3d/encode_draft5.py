import sys,time,json,hashlib,warnings
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft5_common import *
warnings.filterwarnings('ignore',category=DeprecationWarning)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1280;sc.render.resolution_y=360;sc.render.resolution_percentage=100;sc.render.fps=FPS;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=N;sc.render.use_sequencer=True;sc.render.use_compositing=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.sequencer_colorspace_settings.name='sRGB';sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.dither_intensity=0
ed=sc.sequence_editor_create();folder=WORK/'sparkle_frames';encoded=WORK/'encoded';encoded.mkdir(exist_ok=True)
assert all((folder/('f%03d.png'%i)).exists() for i in range(N))
strip=ed.strips.new_image('sparkle',str(folder/'f000.png'),1,1)
for i in range(1,N):strip.elements.append('f%03d.png'%i)
strip.frame_final_duration=N;sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.image_settings.color_mode='RGB'
ff=sc.render.ffmpeg;ff.format='WEBM';ff.codec='WEBM';ff.audio_codec='NONE';ff.constant_rate_factor='CUSTOM';ff.custom_constant_rate_factor=14;ff.ffmpeg_preset='GOOD';ff.gopsize=N;ff.video_bitrate=0;ff.minrate=0;ff.maxrate=0;ff.buffersize=0
sc.render.filepath=str(encoded/'test_sparkle_clip.webm');bpy.ops.render.render(animation=True);files=list(encoded.glob('test_sparkle_clip*.webm'));assert len(files)==1
data=files[0].read_bytes();assert b'V_VP9' in data;target=QA/'test_sparkle_clip.webm';target.write_bytes(data);ed.strips.remove(strip)
movie=ed.strips.new_movie('decoded sparkle',str(target),1,1);assert movie.frame_duration==48 and movie.elements[0].orig_width==1280 and movie.elements[0].orig_height==360
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25;decoded=WORK/'decoded';decoded.mkdir(exist_ok=True)
for i in range(N):sc.frame_set(i+1);sc.render.filepath=str(decoded/('f%03d.png'%i));bpy.ops.render.render(write_still=True)
report('video.json',{'codec':'VP9','container':'WebM','size':[1280,360],'fps':24,'frames':48,'seconds':2,'crf':14,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'all_frames_decoded':True})
status('sparkle VP9 encoded at CRF 14 and all 48 frames decoded for QA; native 1280x360 crop at 24 fps')
