"""OptiX temporal denoise with cyclic warm-up and trailing verification periods."""
import sys,json,time,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from pass8_common import gpu
from build_pass10_draft4 import quality
from draft4_common import ROOT,QA,WORK,status,report,N,FPS,exr_header
raw=WORK/'ripples_raw';pad=WORK/'ripples_pad';td=WORK/'ripples_temporal_exr';png=WORK/'ripples_TD'
for p in [pad,td,png]:p.mkdir(exist_ok=True)
assert len(json.loads((WORK/'ripples_render.json').read_text())['frames'])==N
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc);sc.cycles.use_denoising=True;sc.cycles.denoiser='OPTIX'
def pixels(path):
    im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size
    if not w or not h:
        # Blender's Image.pixels does not expose multipart render layers.
        # Extract Combined through Blender's compositor into a plain, 32-bit
        # linear EXR; no denoising, resampling or display transform is applied.
        old=bpy.context.scene;flat=bpy.data.scenes.new('D4 raw Combined extraction');flat.render.engine='BLENDER_WORKBENCH'
        flat.collection.objects.link(sc.camera);flat.camera=sc.camera;flat.render.resolution_x=1280;flat.render.resolution_y=360;flat.render.resolution_percentage=100
        flat.render.use_compositing=True;flat.render.use_sequencer=False;flat.view_settings.view_transform='Raw'
        flat.render.image_settings.media_type='IMAGE';flat.render.image_settings.file_format='OPEN_EXR';flat.render.image_settings.color_mode='RGBA';flat.render.image_settings.color_depth='32';flat.render.image_settings.exr_codec='ZIP'
        tree=bpy.data.node_groups.new('D4 Combined linear extraction','CompositorNodeTree');tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');flat.compositing_node_group=tree
        node=tree.nodes.new('CompositorNodeImage');node.image=im;out=tree.nodes.new('NodeGroupOutput');tree.links.new(node.outputs.get('Combined') or node.outputs[0],out.inputs['Image'])
        folder=WORK/'endpoint_linear';folder.mkdir(exist_ok=True);target=folder/path.name;flat.render.filepath=str(target);bpy.context.window.scene=flat;bpy.ops.render.render(write_still=True)
        bpy.context.window.scene=old;bpy.data.scenes.remove(flat);bpy.data.node_groups.remove(tree);bpy.data.images.remove(im)
        im=bpy.data.images.load(str(target),check_existing=False);w,h=im.size
    assert (w,h)==(1280,360),(path,w,h)
    buf=np.empty(w*h*4,np.float32);im.pixels.foreach_get(buf);bpy.data.images.remove(im)
    assert np.std(buf.reshape(-1,4)[:,:3])>0,(path,'empty Combined image')
    return buf.reshape(h,w,4)
first=pixels(raw/'raw_0001.exr');endpoint=pixels(raw/'endpoint.exr');err=np.abs(first-endpoint);endpoint_report={'max_abs_linear':float(err.max()),'mean_abs_linear':float(err.mean()),'exact_equal':bool(np.array_equal(first,endpoint))}
assert endpoint_report['max_abs_linear']<1e-5,endpoint_report
unwrapped=pixels(raw/'endpoint_unwrapped.exr');ue=np.abs(first-unwrapped);unwrapped_report={'time_seconds':2,'mean_abs_linear':float(ue.mean()),'max_abs_linear':float(ue.max()),'p99_abs_linear':float(np.percentile(ue,99))}
for f in range(N*3):shutil.copy2(raw/('raw_%04d.exr'%(f%N+1)),pad/('pad_%04d.exr'%(f+1)))
sc.frame_start=1;sc.frame_end=N*3;sc.render.filepath=str(pad/'pad_');t=time.perf_counter();result=bpy.ops.cycles.denoise_animation(output_filepath=str(td/'td_'));elapsed=time.perf_counter()-t
assert (td/('td_%04d.exr'%(N*3))).exists(),result
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
for f in range(N):
    im=bpy.data.images.load(str(td/('td_%04d.exr'%(N+f+1))),check_existing=False);im.save_render(str(png/('f%03d.png'%f)),scene=sc);bpy.data.images.remove(im)
history=np.abs(pixels(td/'td_0049.exr')-pixels(td/'td_0097.exr'))
report('temporal.json',{'operator':'bpy.ops.cycles.denoise_animation','denoiser':'OPTIX','compute':'OPTIX GPU','frame_range':[1,N*3],'delivered_range':[N+1,N*2],'padding_frames_each_side':N,'padding_method':'exact cyclic copies of independently ray-traced unique phases; fixed seed and exact canonical playback phase make them identical to rerendered padding','trimmed_frames':N,'output_size':[1280,360],'fps':FPS,'seconds':N/FPS,'denoise_seconds':elapsed,'source_endpoint':endpoint_report,'unwrapped_shader_endpoint':unwrapped_report,'temporal_history_same_phase_after_one_more_cycle':{'mean_abs_linear':float(history.mean()),'max_abs_linear':float(history.max())},'raw_passes':exr_header(raw/'raw_0001.exr')['channels'],'motion_vector_limit':'static camera/geometry; animated normals/reflections have no material-flow velocity, so temporal lag must be judged on moving ripple highlights'})
status('test A temporal OptiX denoising finished on 144 padded inputs; middle 48 frames retained, one full period trimmed from each side; independently rendered endpoint agrees within 1e-5 linear tolerance')
