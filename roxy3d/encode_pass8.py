"""Constant-quality VP9 via Blender's bundled FFmpeg, followed by real decoding."""
import sys,json,time,hashlib,warnings
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from pass8_common import ROOT,QA,OUT,status
warnings.filterwarnings('ignore',category=DeprecationWarning)

def main():
    assert json.loads((QA/'weather_validation.json').read_text())['passed']
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
    sc.render.fps=24;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=144
    sc.render.use_sequencer=True;sc.render.use_compositing=False
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.sequencer_colorspace_settings.name='sRGB';sc.render.threads_mode='FIXED';sc.render.threads=6
    sc.render.dither_intensity=0
    ed=sc.sequence_editor_create();reports={}
    for kind in ['light_loop','rain_fg']:
        folder=QA/(kind+'_frames');encoded=QA/('encode_'+kind);encoded.mkdir(exist_ok=True)
        for ob in list(ed.strips):ed.strips.remove(ob)
        strip=ed.strips.new_image(kind,str(folder/'f000.png'),1,1)
        for i in range(1,144):strip.elements.append('f'+str(i).zfill(3)+'.png')
        strip.frame_final_duration=144
        sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.image_settings.color_mode='RGB'
        ff=sc.render.ffmpeg;ff.format='WEBM';ff.codec='WEBM';ff.audio_codec='NONE'
        ff.constant_rate_factor='CUSTOM';ff.custom_constant_rate_factor=18;ff.ffmpeg_preset='GOOD';ff.gopsize=144
        ff.video_bitrate=0;ff.minrate=0;ff.maxrate=0;ff.buffersize=0;assert ff.video_bitrate==0
        sc.render.filepath=str(encoded/(kind+'.webm'));t=time.perf_counter();bpy.ops.render.render(animation=True);encode_time=time.perf_counter()-t
        paths=list(encoded.glob(kind+'*.webm'));assert len(paths)==1,paths
        data=paths[0].read_bytes();assert b'V_VP9' in data
        target=OUT/(kind+'.webm');pending=OUT/(kind+'.pending.webm');pending.write_bytes(data);pending.replace(target)
        status(kind+' encoded as constant-quality VP9: CRF 18, bitrate 0, '+str(len(data))+' bytes')
        ed.strips.remove(strip);movie=ed.strips.new_movie(kind+' decoded',str(target),1,1)
        assert movie.frame_duration==144 and movie.elements[0].orig_width==1920 and movie.elements[0].orig_height==1080
        sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
        sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30
        decoded=QA/('decoded_'+kind);decoded.mkdir(exist_ok=True);samples=[0,1,36,72,108,142,143]
        # Time sequential real decoding through Blender VSE. This includes VSE
        # processing/color conversion and is explicitly not an OBS/CEF benchmark.
        t=time.perf_counter()
        for i in range(144):
            sc.frame_set(i+1);sc.render.filepath=str(decoded/('f'+str(i).zfill(3)+'.png'))
            bpy.ops.render.render(write_still=i in samples)
        decode_time=time.perf_counter()-t
        reports[kind]={'codec':'VP9','container':'WebM','size':[1920,1080],'fps':24,'frames':144,'seconds':6,
            'crf':18,'video_bitrate_setting_kbps':0,'minrate':0,'maxrate':0,'preset':'GOOD','bytes':len(data),
            'average_mbps':len(data)*8/6/1e6,'sha256':hashlib.sha256(data).hexdigest(),'encode_seconds':round(encode_time,3),
            'decode_vse_wall_seconds':round(decode_time,3),'decode_vse_ms_per_frame':round(decode_time/144*1000,3),
            'decode_measurement':'144 sequential decoded frames through Blender VSE including color conversion/render overhead and seven PNG saves; not isolated decoder time or CEF/OBS.'}
        (QA/'video_metadata.json').write_text(json.dumps(reports,indent=2))
        status(kind+' all 144 encoded frames decoded; seven lossless decoded samples saved for black-level and seam checks')
    print('PASS8_VIDEOS_ENCODED',json.dumps(reports),flush=True)

if __name__=='__main__':main()
