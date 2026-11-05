import sys,time,json,hashlib,math,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from build_pass10_draft4 import quality
from build_pass10_draft5 import set_phase
from pass8_common import gpu
from common import xyz
from draft5_common import *

def optical(sc):
    tree=bpy.data.node_groups.new('D5 HDR optical glare','CompositorNodeTree');tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');sc.compositing_node_group=tree;n=tree.nodes;l=tree.links
    src=n.new('CompositorNodeRLayers');out=n.new('NodeGroupOutput');base=src.outputs['Image'];acc=base
    for kind,strength,size,threshold,tint in [('Bloom',.22,.025,2.8,(1,1,1,1)),('Fog Glow',.045,.012,3.2,(1,.34,.18,1)),('Streaks',.018,.01,5.,(1,1,1,1))]:
        q=n.new('CompositorNodeGlare');q.inputs['Type'].default_value=kind;q.inputs['Quality'].default_value='High';q.inputs['Threshold'].default_value=threshold;q.inputs['Smoothness'].default_value=.15;q.inputs['Strength'].default_value=strength;q.inputs['Size'].default_value=size;q.inputs['Tint'].default_value=tint;l.new(base,q.inputs['Image'])
        if kind=='Streaks':q.inputs['Streaks'].default_value=4;q.inputs['Streaks Angle'].default_value=math.pi/4;q.inputs['Iterations'].default_value=2;q.inputs['Fade'].default_value=.74;q.inputs['Color Modulation'].default_value=.03
        mix=n.new('ShaderNodeMix');mix.data_type='RGBA';mix.blend_type='ADD';mix.clamp_result=False;mix.inputs[0].default_value=1;l.new(acc,mix.inputs[6]);l.new(q.outputs['Glare'],mix.inputs[7]);acc=mix.outputs[2]
    l.new(acc,out.inputs['Image']);sc.render.use_compositing=True
def setup():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass10_draft.blend'));sc=bpy.context.scene;gpu(sc);quality(sc);sc.cycles.use_denoising=True;sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    optical(sc);return sc
def frame(sc,path,t=0):
    set_phase(sc,t);sc.render.filepath=str(path);st=time.perf_counter();bpy.ops.render.render(write_still=True);return time.perf_counter()-st
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['preview','loop','details','endpoint','sparkle_off']);ap.add_argument('--only',default='');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);sc=setup()
    if args.mode=='preview':
        sec=frame(sc,QA/'draft_5_clean.png');report('preview.json',{'samples':256,'size':[1280,720],'seconds':sec,'seed':1701,'adaptive':False,'denoise':'per-frame OptiX','glare':'same HDR compositor settings as draft4','source_sha256':hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest()});status('native 720p clean still rendered at 256 samples with current wet surfaces, micro-impacts and HDR glare (%.1f seconds)'%sec)
    elif args.mode in ['loop','endpoint','sparkle_off']:
        sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=0;sc.render.border_max_x=1;sc.render.border_min_y=0;sc.render.border_max_y=.5
        folder=WORK/'sparkle_frames';folder.mkdir(exist_ok=True);rows=[];signature=hashlib.sha256((ROOT/'roxy_pass10_draft.blend').read_bytes()).hexdigest();checkpoint=WORK/'sparkle_render.json'
        if args.mode=='sparkle_off':
            sc['d5_control_off']=True;frame(sc,WORK/'sparkle_off.png',0);status('matched current-material sparkle-off control rendered by collapsing droplet geometry, preserving object/light-link membership, fixed seed and 256 samples');return
        if checkpoint.exists():
            prior=json.loads(checkpoint.read_text());assert prior['source_sha256']==signature;rows=prior['frames']
        if args.mode=='loop':
            for f in range(N):
                out=folder/('f%03d.png'%f)
                if any(row['frame']==f for row in rows) and out.exists():continue
                sc.frame_set(f+1);sec=frame(sc,out,f/FPS);rows.append({'frame':f,'seconds':sec});report('sparkle_render.json',{'source_sha256':signature,'samples':256,'seed':1701,'size':[1280,360],'fps':FPS,'frames':rows,'method':'native ray-traced wet-only geometry micro-impacts, retained D4 ripple normals; per-frame OptiX; current HDR glare'});status('sparkle test frame %02d/48 complete at 256 samples (%.1f seconds)'%(f+1,sec))
        sc.frame_set(49);sec=frame(sc,WORK/'sparkle_endpoint.png',2.);status('independent canonical 2-second sparkle endpoint rendered for seam validation')
    elif args.mode=='details':
        sc.render.resolution_x=1000;sc.render.resolution_y=750
        # Same dimetric camera orientation, moved/zoomed only for review.
        for name,target,scale in [('shelter_bus',(-.20,10.1,60),5.4),('alley',(14.8,3.4,85),5.8),('service_art',(14.9,-.1,110),4.6),('rooftop_ac',(-2.5,4.0,248),6.7),('inside',(2.35,.1,103),4.1),('billboard',(11.35,-3.5,320),3.7),('cabge',(-1.98,8.9,32),2.2)]:
            if args.only and name not in args.only.split(','):continue
            sc.camera.location=xyz(*target)+sc.camera.matrix_world.to_quaternion()@Vector((0,0,30));sc.camera.data.ortho_scale=scale
            sec=frame(sc,WORK/(name+'.png'));status('detail review '+name+' rendered at 256 samples (%.1f seconds)'%sec)
if __name__=='__main__':main()
