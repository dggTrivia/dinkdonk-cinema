"""48 final-quality Cycles frames, with a native crop from the 720p camera.
Each unique frame is ray traced. No reflection resampling or 2-D warping.
"""
import sys,json,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from pass8_common import gpu
from build_pass10_draft4 import quality
from draft4_common import ROOT,QA,WORK,status,report,N,FPS,exr_header
raw=WORK/'ripples_raw';png=WORK/'ripples_noTD';raw.mkdir(exist_ok=True);png.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc)
sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=0;sc.render.border_max_x=1;sc.render.border_min_y=0;sc.render.border_max_y=.5
time_node=bpy.data.node_groups['D4 periodic ray-traced rain ripple normals'].nodes['Time seconds']
signature=hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest()
checkpoint=WORK/'ripples_render.json'
rows=json.loads(checkpoint.read_text())['frames'] if checkpoint.exists() else []
if checkpoint.exists():assert json.loads(checkpoint.read_text())['source_sha256']==signature
for f in range(N):
    target=raw/('raw_%04d.exr'%(f+1));out=png/('f%03d.png'%f)
    if any(r['frame']==f for r in rows) and target.exists() and out.exists():continue
    quality(sc);sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=0;sc.render.border_max_x=1;sc.render.border_min_y=0;sc.render.border_max_y=.5
    sc.frame_set(f+1);time_node.outputs[0].default_value=(f%N)/FPS;sc.render.filepath=str(target)
    t=time.perf_counter();bpy.ops.render.render(write_still=True);rt=time.perf_counter()-t
    channels=exr_header(target)['channels'];assert any('Denoising Normal' in c for c in channels) and any('.Vector.' in c for c in channels)
    sc.cycles.use_denoising=True;td=raw/('single_%04d.exr'%(f+1));t=time.perf_counter();bpy.ops.cycles.denoise_animation(input_filepath=str(target),output_filepath=str(td));dt=time.perf_counter()-t;assert td.exists()
    im=bpy.data.images.load(str(td),check_existing=False);sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';im.save_render(str(out),scene=sc);bpy.data.images.remove(im)
    rows.append({'frame':f,'seconds':round(rt,3),'single_optix_seconds':round(dt,3),'raw_bytes':target.stat().st_size})
    report('ripples_render.json',{'source_sha256':signature,'frames':rows,'samples':256,'seed':1701,'animated_seed':False,'camera_size':[1280,720],'native_crop':[0,360,1280,360],'fps':FPS,'seconds':N/FPS,'raw_channels':channels})
    status('test A ray-traced frame %02d/%d complete (%.1f s); matching per-frame OptiX output saved'%(f+1,N,rt))
# Render the mathematical wrap independently rather than comparing cached files.
quality(sc);sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=0;sc.render.border_max_x=1;sc.render.border_min_y=0;sc.render.border_max_y=.5
sc.frame_set(N+1);time_node.outputs[0].default_value=(N%N)/FPS;sc.render.filepath=str(raw/'endpoint.exr');t=time.perf_counter();bpy.ops.render.render(write_still=True)
status('test A all 48 unique frames and independent canonical periodic endpoint rendered; exact source-pixel and temporal checks follow')
# Also check the unwrapped shader formula at 2 seconds, rather than only the
# canonical playback phase. Tiny FP differences are measured, not concealed.
time_node.outputs[0].default_value=N/FPS;sc.render.filepath=str(raw/'endpoint_unwrapped.exr');bpy.ops.render.render(write_still=True)
status('test A unwrapped 2-second shader endpoint rendered independently for floating-point periodicity measurement')
