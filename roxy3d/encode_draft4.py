"""Encode both matched ripple tests and decode all delivery frames for QA."""
import sys,json,time,hashlib,warnings
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from draft4_common import ROOT,QA,WORK,N,FPS,status,report
warnings.filterwarnings('ignore',category=DeprecationWarning)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=1280;sc.render.resolution_y=360;sc.render.resolution_percentage=100
sc.render.fps=FPS;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=N
sc.render.use_sequencer=True;sc.render.use_compositing=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.sequencer_colorspace_settings.name='sRGB';sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.dither_intensity=0
ed=sc.sequence_editor_create();reports={}
for kind,name in [('noTD','test_ripples_clip_noTD'),('TD','test_ripples_clip')]:
    folder=WORK/('ripples_'+kind);encoded=WORK/('encode_'+kind);encoded.mkdir(exist_ok=True)
    assert all((folder/('f%03d.png'%i)).exists() for i in range(N))
    for ob in list(ed.strips):ed.strips.remove(ob)
    strip=ed.strips.new_image(kind,str(folder/'f000.png'),1,1)
    for i in range(1,N):strip.elements.append('f%03d.png'%i)
    strip.frame_final_duration=N
    sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.image_settings.color_mode='RGB'
    ff=sc.render.ffmpeg;ff.format='WEBM';ff.codec='WEBM';ff.audio_codec='NONE'
    ff.constant_rate_factor='CUSTOM';ff.custom_constant_rate_factor=14;ff.ffmpeg_preset='GOOD';ff.gopsize=N
    ff.video_bitrate=0;ff.minrate=0;ff.maxrate=0;ff.buffersize=0
    sc.render.filepath=str(encoded/(name+'.webm'));t=time.perf_counter();bpy.ops.render.render(animation=True);et=time.perf_counter()-t
    paths=list(encoded.glob(name+'*.webm'));assert len(paths)==1,paths
    data=paths[0].read_bytes();assert b'V_VP9' in data
    target=QA/(name+'.webm');target.write_bytes(data)
    ed.strips.remove(strip);movie=ed.strips.new_movie(kind+' decoded',str(target),1,1)
    assert movie.frame_duration==N and movie.elements[0].orig_width==1280 and movie.elements[0].orig_height==360
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30
    decoded=WORK/('decoded_'+kind);decoded.mkdir(exist_ok=True);t=time.perf_counter()
    for i in range(N):
        sc.frame_set(i+1);sc.render.filepath=str(decoded/('f%03d.png'%i));bpy.ops.render.render(write_still=True)
    dt=time.perf_counter()-t
    reports[kind]={'codec':'VP9','container':'WebM','size':[1280,360],'native_camera_crop':[0,360,1280,360],'camera_size':[1280,720],'fps':FPS,'frames':N,'seconds':N/FPS,'crf':14,'video_bitrate_setting_kbps':0,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'encode_seconds':et,'decode_and_png_seconds':dt,'all_frames_decoded':True}
    report('video.json',reports)
    status('test A '+kind+' VP9 encoded at CRF 14; all 48 delivery frames decoded and saved, native 1280x360 crop at 24 fps')
