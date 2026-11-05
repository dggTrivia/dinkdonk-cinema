"""Portable shared coordinates and strict OptiX configuration."""
from pathlib import Path
import os,math
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
for key,sub in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),('OPTIX_CACHE_PATH','optix')]:
    p=ROOT/'work/cache'/sub;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
PPU=60*math.sqrt(2);ZPP=PPU*math.cos(math.pi/6)
RIGHT=Vector((2**-.5,2**-.5,0));UP=Vector((-math.sqrt(.125),math.sqrt(.125),math.sqrt(.75)));NORMAL=RIGHT.cross(UP)
def xyz(u,v,z=0):return Vector((u,-v,z/ZPP))
def project(u,v,z=0):return [900+60*(u-v),350+30*(u+v)-z]
def screen_point(x,y,depth=0):return RIGHT*((x-900)/PPU)+UP*((350-y)/PPU)+NORMAL*depth
def gpu(sc):
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.refresh_devices()
    devices=[d for d in p.devices if d.type=='OPTIX']
    if not devices:raise RuntimeError('An NVIDIA OptiX device is required; CPU fallback is disabled')
    for d in p.devices:d.use=d in devices
    sc.cycles.device='GPU';return [d.name for d in devices]
def quality(sc,width=1280,height=720,adaptive=False,threshold=.001):
    sc.render.engine='CYCLES';sc.cycles.samples=256;sc.cycles.use_adaptive_sampling=adaptive;sc.cycles.adaptive_threshold=threshold;sc.cycles.adaptive_min_samples=64
    sc.cycles.use_denoising=True;sc.cycles.denoiser='OPTIX';sc.cycles.denoising_use_gpu=True
    sc.cycles.seed=1701;sc.cycles.use_animated_seed=False;sc.cycles.max_bounces=10;sc.cycles.diffuse_bounces=4;sc.cycles.glossy_bounces=6;sc.cycles.transmission_bounces=8;sc.cycles.transparent_max_bounces=24
    sc.cycles.sample_clamp_direct=0;sc.cycles.sample_clamp_indirect=0
    sc.render.use_persistent_data=True;sc.cycles.tile_size=4096
    sc.render.resolution_x=width;sc.render.resolution_y=height;sc.render.resolution_percentage=100
    sc.render.use_border=False;sc.render.use_crop_to_border=False;sc.render.use_sequencer=False;sc.render.use_compositing=False;sc.render.film_transparent=False
    sc.render.fps=24;sc.render.fps_base=1
def setup(samples=256,scale=1,transparent=False):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;quality(sc,round(1920*scale),round(1080*scale));gpu(sc);sc.render.film_transparent=transparent
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
    world=bpy.data.worlds.new('Night ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.095,.12,.24,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3;sc.world=world
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Page exact dimetric camera';cam.data.type='ORTHO';cam.data.ortho_scale=1920/PPU;cam.data.lens=50;cam.data.clip_end=200
    cam.rotation_euler=(math.radians(60),0,math.radians(45));cam.location=RIGHT*(60/PPU)-UP*(190/PPU)+NORMAL*38;sc.camera=cam
    return sc
def render(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);sc=bpy.context.scene
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.filepath=str(p)
    bpy.ops.render.render(write_still=True)
