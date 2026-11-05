"""Render five isolated spheres, measure PNG alpha centroids, assert <= 1 pixel.

Run: tools/blender-5.2.3-windows-x64/blender.exe -b -P roxy3d/calibrate.py
Pixel coordinates use pixel centres (index + .5), matching the canvas convention.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import numpy as np
import json
from bpy_extras.object_utils import world_to_camera_view
from common import ROOT, setup, xyz, project, render

sc = setup(32, transparent=True)
sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
points = [(0,0,0), (13,0,0), (0,9,0), (13,9,0), (0,0,170)]
mat = bpy.data.materials.new('Calibration unlit white')
nodes = mat.node_tree.nodes
nodes.clear()
em = nodes.new('ShaderNodeEmission')
out = nodes.new('ShaderNodeOutputMaterial')
mat.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
for p in points:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.075, location=xyz(*p))
    bpy.context.object.data.materials.append(mat)
path = ROOT/'qa2'/'calibration.png'
render(path)
im = bpy.data.images.load(str(path), check_existing=False)
w,h = im.size
pixels = np.empty(w*h*4, np.float32)
im.pixels.foreach_get(pixels)
alpha = pixels.reshape(h,w,4)[::-1,:,3]
results = []
for p in points:
    x,y = project(*p)
    x0,y0 = int(x)-12, int(y)-12
    crop = alpha[y0:y0+24,x0:x0+24]
    yy,xx = np.mgrid[y0:y0+24,x0:x0+24]
    measured = [float(((xx+.5)*crop).sum()/crop.sum()), float(((yy+.5)*crop).sum()/crop.sum())]
    errors = [measured[0]-x, measured[1]-y]
    coord = world_to_camera_view(sc, sc.camera, xyz(*p))
    results.append({'uvz':p,'expected':[x,y], 'measured':measured,'error_px':errors,
                    'analytic':[coord.x*1920,(1-coord.y)*1080]})
    assert max(map(abs,errors)) <= 1, results[-1]
report = {'size':[1920,1080], 'pixel_convention':'pixel centers = index + 0.5',
          'max_axis_error_px':max(abs(e) for r in results for e in r['error_px']),
          'passed':True, 'points':results}
(ROOT/'qa2'/'calibration.json').write_text(json.dumps(report,indent=2))
print('CALIBRATION',json.dumps(report),flush=True)

