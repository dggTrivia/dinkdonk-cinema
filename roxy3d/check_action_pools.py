"""One independent lights-off render for measuring the six service pools."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import build_scene as b
from common import ROOT,render
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'roxy_pass4.blend'))
sc=bpy.context.scene;b.GROUPS.clear()
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
sc.cycles.device='GPU'
for ob in sc.objects:
    if 'layer' in ob:b.GROUPS.setdefault(ob['layer'],[]).append(ob)
    if ob.type=='LIGHT' and ob.name.startswith('Pass4 action pool'):ob.data.energy=0
b.set_visibility('background')
sc.render.use_border=False;sc.render.use_crop_to_border=False
sc.render.resolution_x=1920;sc.render.resolution_y=1080
render(ROOT/'qa4'/'action_pools_off.png')
