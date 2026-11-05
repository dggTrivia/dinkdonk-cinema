"""Encode and decode-check the VP9 loop using Blender's bundled FFmpeg.

No external ffmpeg executable or network dependency. Standard/sRGB view settings
preserve the display-space additive PNG values. Publish manifest only on success.
"""
import sys,json,time,hashlib,struct,warnings
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT
warnings.filterwarnings('ignore',category=DeprecationWarning)

QA=ROOT/'qa2';OUT=ROOT/'out2';FRAMES=QA/'loop_frames';ENCODE=QA/'encode'

def settings(sc):
    sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.render.fps=24;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=120
    sc.render.use_sequencer=True;sc.render.use_compositing=False
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
    sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.sequencer_colorspace_settings.name='sRGB'
    sc.render.image_settings.color_mode='RGB'

def main():
    start=time.perf_counter();ENCODE.mkdir(exist_ok=True)
    assert (QA/'loop_validation.json').exists()
    sc=bpy.context.scene;settings(sc);ed=sc.sequence_editor_create()
    strip=ed.strips.new_image('Positive light frames',str(FRAMES/'f000.png'),1,1)
    for i in range(1,120):strip.elements.append('f'+str(i).zfill(3)+'.png')
    strip.frame_final_duration=120
    sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG'
    ff=sc.render.ffmpeg;ff.format='WEBM';ff.codec='WEBM';ff.audio_codec='NONE'
    ff.constant_rate_factor='CUSTOM';ff.custom_constant_rate_factor=4;ff.ffmpeg_preset='GOOD';ff.gopsize=120
    ff.video_bitrate=6000;ff.minrate=0;ff.maxrate=12000;ff.buffersize=4000
    sc.render.filepath=str(ENCODE/'light_loop.webm')
    bpy.ops.render.render(animation=True)
    candidates=list(ENCODE.glob('light_loop*.webm'));assert len(candidates)==1,candidates
    source=candidates[0];assert source.stat().st_size<15_000_000,source.stat().st_size
    data=source.read_bytes();assert b'V_VP9' in data,'Output must identify VP9'
    target=OUT/'light_loop.webm';target.write_bytes(data)
    # Decode the actual encoded file through Blender, not just its input frames.
    ed.strips.remove(strip)
    movie=ed.strips.new_movie('Encoded VP9 verification',str(target),1,1)
    metadata={'codec':'VP9','container':'WebM','width':movie.elements[0].orig_width,
        'height':movie.elements[0].orig_height,'decoded_frames':movie.frame_duration,
        'fps':24,'seconds':movie.frame_duration/24,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert metadata['width']==1920 and metadata['height']==1080,metadata
    assert movie.frame_duration==120,metadata
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30
    for frame in [0,1,30,60,90,118,119]:
        sc.frame_set(frame+1);sc.render.filepath=str(QA/('decoded_f'+str(frame).zfill(3)+'.png'))
        bpy.ops.render.render(write_still=True)
    metadata['encode_and_decode_seconds']=round(time.perf_counter()-start,3)
    (QA/'video_metadata.json').write_text(json.dumps(metadata,indent=2))
    # The independent Python check validates decoded pixels before publication.
    print('ENCODED_VP9',json.dumps(metadata),flush=True)

if __name__=='__main__':main()
