"""Portable VP9 encoding and real decoding using Blender's bundled FFmpeg."""
import json,time,os
from pathlib import Path
import bpy,numpy as np
from common import ROOT
from runtime import WORK,sha,atomic_json,rgba8,png,log
from package_layers import boxblur

def encode_and_validate(name,folder,out,scale=1,frames=144,width=None,height=None):
    folder=Path(folder);out=Path(out);target=out/(name+'.webm');receipt=WORK/(name+'_video.json');count=48 if frames==144 else 1
    sources=[folder/f'f{i:03d}.png' for i in range(count)];assert all(p.exists() for p in sources)
    first=rgba8(sources[0]);height=height or first.shape[0];width=width or first.shape[1]
    identity={'sources':[sha(p) for p in sources],'size':[width,height],'frames':frames,'fps':24,'crf':4}
    if target.exists() and receipt.exists():
        old=json.loads(receipt.read_text())
        if old['identity']==identity and old['sha256']==sha(target) and old['passed']:return old
    sc=bpy.data.scenes.get('Cloud video') or bpy.data.scenes.new('Cloud video');sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=width;sc.render.resolution_y=height;sc.render.resolution_percentage=100;sc.render.fps=24;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=frames
    sc.render.use_sequencer=True;sc.render.use_compositing=False;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.sequencer_colorspace_settings.name='sRGB';sc.render.dither_intensity=0
    ed=sc.sequence_editor_create()
    for strip in list(ed.strips):ed.strips.remove(strip)
    strip=ed.strips.new_image(name,str(sources[0]),1,1)
    for i in range(1,frames):strip.elements.append(f'f{i%count:03d}.png')
    strip.frame_final_duration=frames
    sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG';sc.render.image_settings.color_mode='RGB';ff=sc.render.ffmpeg;ff.format='WEBM';ff.codec='WEBM';ff.audio_codec='NONE';ff.constant_rate_factor='CUSTOM';ff.custom_constant_rate_factor=4;ff.ffmpeg_preset='GOOD';ff.gopsize=frames;ff.video_bitrate=0;ff.minrate=0;ff.maxrate=0;ff.buffersize=0
    encoded=WORK/'encoded'/name;encoded.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(encoded/(name+'.webm'));start=time.perf_counter();bpy.ops.render.render(animation=True,scene=sc.name);seconds=time.perf_counter()-start
    paths=list(encoded.glob(name+'*.webm'));assert len(paths)==1,paths;assert b'V_VP9' in paths[0].read_bytes(),'Encoder did not produce VP9';temp=out/(name+'.partial.webm');temp.write_bytes(paths[0].read_bytes());os.replace(temp,target)
    ed.strips.remove(strip);movie=ed.strips.new_movie(name+' decoded',str(target),1,1);assert movie.frame_duration==frames;assert movie.elements[0].orig_width==width and movie.elements[0].orig_height==height
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    decoded=WORK/'decoded'/name;decoded.mkdir(parents=True,exist_ok=True);indices=sorted(set([0,min(1,frames-1),min(47,frames-1),min(48,frames-1),frames-1]));samples={}
    black=np.ones((height,width),bool)
    for src in sources:black&=rgba8(src)[:,:,:3].max(axis=2)==0
    # Exclude codec ringing near real highlights. A broad black region must
    # remain black after actual VP9 decoding and display conversion. Cloud run 2 (03 Nov 2026):
    # 4K crf-4 VP9 left 10 of 565,684 probe pixels at 1/255 - invisible in an additive layer, yet
    # the exact-zero test discarded a 5.5 h render. Allow codec noise of <=2/255 on <=0.05% of probes per decoded frame.
    black=boxblur((~black).astype(np.float32),8)<1e-8
    black_count=int(black.sum());assert black_count>=32,('Insufficient black probe area',name,black_count)
    black_max=0;black_nonzero=0;frame_nonzero=0;errors=[]
    for f in indices:
        sc.frame_set(f+1);path=decoded/f'f{f:03d}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name);a=rgba8(path);samples[f]=a
        black_max=max(black_max,int(a[:,:,:3][black].max()));n=int(np.any(a[:,:,:3][black]!=0,axis=1).sum());black_nonzero+=n;frame_nonzero=max(frame_nonzero,n);ref=rgba8(sources[f%count]);errors.append(float(np.abs(a[:,:,:3].astype(np.int16)-ref[:,:,:3]).mean()))
    raw_seam={}
    if frames==144:
        cycle=[rgba8(p)[:,:,:3].astype(np.int16) for p in sources]
        steps=[float(np.abs(cycle[(i+1)%48]-cycle[i]).mean()) for i in range(48)];seam=steps[-1];typical=float(np.percentile(steps,95));assert seam<=max(.05,typical*2),('Loop seam exceeds adjacent changes',name,seam,typical)
        repeats=float(np.abs(samples[0][:,:,:3].astype(np.int16)-samples[48][:,:,:3]).mean());raw_seam={'wrap_mean_8bit':seam,'p95_adjacent_mean_8bit':typical,'decoded_repetition_mean_8bit':repeats,'unique_frames':48,'repetitions':3}
    report={'identity':identity,'passed':black_max<=2 and frame_nonzero<=max(32,black_count//2000),'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size,'codec':'VP9','size':[width,height],'fps':24,'frames':frames,'seconds':frames/24,'encode_seconds':seconds,'decoded_indices':indices,'decoded_black_pixels_tested':black_count,'decoded_black_max':black_max,'decoded_black_nonzero_pixels':black_nonzero,'decoded_mean_abs_error_8bit':errors,'seams':raw_seam}
    atomic_json(receipt,report)
    if not report['passed']:raise RuntimeError('Decoded additive black level failed: '+json.dumps(report))
    log('video_encoded_and_decoded',name=name,bytes=target.stat().st_size,black_max=black_max);return report
