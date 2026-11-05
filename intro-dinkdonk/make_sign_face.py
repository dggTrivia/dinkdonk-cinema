# Renders the neon DinkDonk emote flat-on, on black, as the face for the dome sign
# (sign_replace.py screens it over the sign's own red panel).
#
#   blender -b --factory-startup --python make_sign_face.py -- <out.png>
import bpy, sys, os, math

OUT = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import neon_emote

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'

root = bpy.data.objects.new('neon', None); sc.collection.objects.link(root)
W = 4.4
neon_emote.build(sc, root, os.path.join(HERE, 'dinkdonk-emote-128.png'), W, [(1, 1.0)], [(1, 9.0)])

cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = W * 1.12
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, 0, 10)
sc.frame_set(1)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
