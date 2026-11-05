"""Exact page coordinates and reproducible Cycles configuration. No external assets."""
import bpy
import math
import os
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for key, folder in [('OPTIX_CACHE_PATH','optix'), ('CUDA_CACHE_PATH','cuda'), ('TEMP','temp'), ('TMP','temp')]:
    cache = ROOT/'cache'/folder
    cache.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(cache)
PPU = 60 * math.sqrt(2)
ZPP = PPU * math.cos(math.pi / 6)
RIGHT = Vector((2**-0.5, 2**-0.5, 0))
UP = Vector((-math.sqrt(0.125), math.sqrt(0.125), math.sqrt(0.75)))
NORMAL = RIGHT.cross(UP)

def xyz(u, v, z=0):
    return Vector((u, -v, z / ZPP))

def project(u, v, z=0):
    return [900 + (u-v)*60, 350 + (u+v)*30-z]

def screen_point(x, y, depth=0):
    return RIGHT*((x-900)/PPU) + UP*((350-y)/PPU) + NORMAL*depth

def setup(samples=32, scale=1, transparent=False):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.adaptive_threshold = 0.025
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.seed = 1701
    sc.render.resolution_x = int(1920*scale)
    sc.render.resolution_y = int(1080*scale)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    sc.render.image_settings.compression = 30
    sc.render.film_transparent = transparent
    sc.render.use_persistent_data = True
    sc.render.threads_mode = 'AUTO'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.25
    world = bpy.data.worlds.new('Night ambient')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.095, .12, .24, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .3
    sc.world = world
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = 'Page exact dimetric camera'
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 1920/PPU
    cam.data.lens = 50
    cam.data.clip_end = 200
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    cam.location = RIGHT*(60/PPU) - UP*(190/PPU) + NORMAL*38
    sc.camera = cam
    device = 'CPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            found = [d for d in prefs.devices if d.type == backend]
            if found:
                for d in prefs.devices:
                    d.use = d.type == backend
                sc.cycles.device = 'GPU'
                device = backend + ': ' + ', '.join(d.name for d in found)
                break
        except Exception as ex:
            print('DEVICE_FALLBACK', backend, str(ex))
    print('RENDER_DEVICE', device, flush=True)
    sc['render_device'] = device
    return sc

def render(path):
    sc = bpy.context.scene
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(path)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as ex:
        if sc.cycles.device != 'GPU':
            raise
        print('GPU render failed, retrying CPU:', ex, flush=True)
        sc.cycles.device = 'CPU'
        bpy.ops.render.render(write_still=True)
