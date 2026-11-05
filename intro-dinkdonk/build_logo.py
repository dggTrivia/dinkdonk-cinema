# Rebuilds the National Amusements logo card (source frames 1109-1386) as DINK DONK:
# a neon-sign DinkDonk emote replaces the slatted N, the ring text reads DINK DONK / CINEMAS
# and flips to ENJOY THE SHOW like the original, and the emote then glows up like the N does.
# Starts at 1109, before the original's slats appear, over a push-in on the last clean frame.
# Renders an opaque PNG sequence; compose.py lays it over the original video and keeps the
# original audio.
#
#   blender -b --factory-startup --python build_logo.py -- <out_dir> <height> [frame,frame,...]
import bpy, sys, math, os, random

A = sys.argv[sys.argv.index('--') + 1:]
OUT, HEIGHT = A[0], int(A[1])
ONLY = [int(f) for f in A[2].split(',')] if len(A) > 2 else None
HERE = os.path.dirname(os.path.abspath(__file__))
EMOTE = os.path.join(HERE, 'dinkdonk-emote-128.png')
FONT = r'C:\Windows\Fonts\seguisb.ttf'   # semibold: closer to the original's stroke weight
PLATE = os.path.join(HERE, 'plate_1108.png')   # last frame before the slats (1112) fly in
F0, F1 = 1109, 1386   # original: logo fades 1359-1372, black until 1387
sys.path.insert(0, HERE)
import neon_emote
# 1 unit = 100 px at 1080p; logo centre sits where the N was (953, 535)
CX, CY = (953 - 960) / 100, (540 - 535) / 100

def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1]

TEXT, TEAL, ORANGE = lin('#E6DFCC'), lin('#2DA595'), lin('#E8843E')
RAY_TEAL, RAY_ORANGE = lin('#46D6C6'), lin('#F29A48')

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 16
sc.render.resolution_x, sc.render.resolution_y = HEIGHT * 16 // 9, HEIGHT
sc.render.resolution_percentage = 100
sc.render.filter_size = 2.4 * HEIGHT / 1080   # a touch of the film transfer's softness
sc.render.fps = 24
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0, 0, 0)
sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'

def key(obj, path, pairs, interp='BEZIER', easing='AUTO', index=-1):
    for f, v in pairs:
        if index >= 0: getattr(obj, path)[index] = v
        else: setattr(obj, path, v)
        obj.keyframe_insert(path, frame=f, index=index)
    frames = {f for f, _ in pairs}
    for c in _curves(obj):
        if c.data_path != path or (index >= 0 and c.array_index != index): continue
        for k in c.keyframe_points:
            if round(k.co.x) in frames: k.interpolation, k.easing = interp, easing

def _curves(obj):
    ad = obj.animation_data
    if not ad or not ad.action: return []
    try: return list(ad.action.fcurves)
    except AttributeError:  # layered actions (Blender 4.4+)
        return [c for l in ad.action.layers for s in l.strips for b in s.channelbags for c in b.fcurves]

def emission(name, color, strength=1.0):
    m =bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = color; em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def ray_material(name, color, fade_frames):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.surface_render_method = 'BLENDED'
    nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial')
    uv = N.new('ShaderNodeTexCoord'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(uv.outputs['UV'], sep.inputs[0])
    # along the ray (u): bright core at the inner end, soft tail; across (v): soft edges
    ramp = N.new('ShaderNodeValToRGB'); L.new(sep.outputs[0], ramp.inputs[0])
    r = ramp.color_ramp; r.elements[0].color = (1, 1, 1, 1); r.elements[1].position = 1.0; r.elements[1].color = (0, 0, 0, 1)
    e = r.elements.new(0.06); e.color = (0.75, 0.75, 0.75, 1)
    e = r.elements.new(0.45); e.color = (0.32, 0.32, 0.32, 1)
    edge = N.new('ShaderNodeMath'); edge.operation = 'PINGPONG'; edge.inputs[1].default_value = 0.5
    L.new(sep.outputs[1], edge.inputs[0])
    edge2 = N.new('ShaderNodeMapRange'); edge2.inputs['From Max'].default_value = 0.5
    L.new(edge.outputs[0], edge2.inputs['Value'])
    sm = N.new('ShaderNodeMath'); sm.operation = 'POWER'; sm.inputs[1].default_value = 0.6
    L.new(edge2.outputs[0], sm.inputs[0])
    # streaks along the ray, like a spotlight beam through haze
    cx = N.new('ShaderNodeCombineXYZ'); L.new(sep.outputs[1], cx.inputs['Y'])
    sv = N.new('ShaderNodeVectorMath'); sv.operation = 'SCALE'; sv.inputs['Scale'].default_value = 7.0
    L.new(cx.outputs[0], sv.inputs[0])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 3.0
    L.new(sv.outputs[0], nz.inputs['Vector'])
    st_ = N.new('ShaderNodeMapRange'); st_.inputs['From Min'].default_value = 0.3; st_.inputs['From Max'].default_value = 0.7
    st_.inputs['To Min'].default_value = 0.3; L.new(nz.outputs['Fac'], st_.inputs['Value'])
    sm2 = N.new('ShaderNodeMath'); sm2.operation = 'MULTIPLY'
    L.new(sm.outputs[0], sm2.inputs[0]); L.new(st_.outputs['Result'], sm2.inputs[1])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(ramp.outputs[0], mul.inputs[0]); L.new(sm2.outputs[0], mul.inputs[1])
    fade = N.new('ShaderNodeValue'); fade.name = 'fade'
    mul2 = N.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    L.new(mul.outputs[0], mul2.inputs[0]); L.new(fade.outputs[0], mul2.inputs[1])
    em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = color; em.inputs[1].default_value = 2.2
    tr = N.new('ShaderNodeBsdfTransparent')
    add = N.new('ShaderNodeMixShader')
    L.new(mul2.outputs[0], add.inputs[0]); L.new(tr.outputs[0], add.inputs[1]); L.new(em.outputs[0], add.inputs[2])
    L.new(add.outputs[0], out.inputs[0])
    for f, v in fade_frames:
        fade.outputs[0].default_value = v
        fade.outputs[0].keyframe_insert('default_value', frame=f)
    # bright round head at the inner end of each ray, same fade
    h = bpy.data.materials.new(name + '_head'); h.use_nodes = True; h.surface_render_method = 'BLENDED'
    nt = h.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission')
    em.inputs[0].default_value = [min(1.0, c * 1.6) for c in color[:3]] + [1]; em.inputs[1].default_value = 3.0
    tr = N.new('ShaderNodeBsdfTransparent'); mix = N.new('ShaderNodeMixShader'); hf = N.new('ShaderNodeValue')
    L.new(hf.outputs[0], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs[0])
    for f, v in fade_frames:
        hf.outputs[0].default_value = v
        hf.outputs[0].keyframe_insert('default_value', frame=f)
    return m, h

def empty(name, parent=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o)
    o.parent = parent; o.location = loc
    return o

font = bpy.data.fonts.load(FONT)
text_mat = emission('text', TEXT, 1.0)
CAP = 0.45                # cap height of the ring letters (45 px), as in the original
SIZE = CAP / 0.375        # measured: Segoe UI caps render at ~0.375 of the curve size

def letter(ch, parent, ang, r, bottom):
    cu = bpy.data.curves.new('ch', 'FONT'); cu.body = ch; cu.font = font; cu.size = SIZE
    cu.align_x = 'CENTER'; cu.materials.append(text_mat)
    o = bpy.data.objects.new('ch_' + ch, cu); sc.collection.objects.link(o); o.parent = parent
    a = math.radians(ang)
    o.location = (r * math.cos(a), r * math.sin(a), 0)
    o.rotation_euler = (0, 0, a + (math.pi / 2 if bottom else -math.pi / 2))

def arc(word, parent, center, pitch, r, bottom):
    # equal angular pitch per letter like the original; a space is 0.6 of a step
    steps, pos = [], 0.0
    for i, ch in enumerate(word):
        if ch == ' ': pos += 0.6; continue
        steps.append((ch, pos)); pos += 1
    span = steps[-1][1] * pitch
    for ch, p in steps:
        ang = (center + span / 2 - p * pitch) if not bottom else (center - span / 2 + p * pitch)
        letter(ch, parent, ang, r, bottom)

def dot(parent, ang, color, r=3.22, size=0.065):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=size, fill_type='NGON')
    o = bpy.context.active_object; o.parent = parent
    a = math.radians(ang); o.location = (r * math.cos(a), r * math.sin(a), 0.001)
    o.data.materials.append(emission('dot', color))

R_TOP, R_BOT = 2.93, 3.53   # baseline radii (top letters face out, bottom letters face in)
logo = empty('logo', loc=(CX, CY, 0))
ring1 = empty('ring_dinkdonk', logo)
arc('DINK DONK', ring1, 90, 17.0, R_TOP, False)
arc('CINEMAS', ring1, 270, 18.5, R_BOT, True)
for a in (-4, 184): dot(ring1, a, TEAL)
ring2 = empty('ring_enjoy', logo)
arc('ENJOY', ring2, 90, 17.0, R_TOP, False)
arc('THE SHOW', ring2, 270, 18.5, R_BOT, True)

# --- the DinkDonk emote as a neon sign where the N was
W_E = 4.4
FLIP = 1276                  # the ring starts turning; the N lights up warm here in the original
# halos stay low while the pieces are close to the lens (no screen-filling wash), full once it settles
GLOW = [(F0, 0.12), (1150, 0.15), (1178, 0.6), (FLIP, 0.6), (1288, 1.7), (1300, 1.2)]
SWEEP = [(F0, 4.0), (FLIP, 2.6), (1290, -2.6)]   # a bright band runs down the tubes on the flip
neon = empty('neon', logo, (0, 0.02, 0.002))
parts = neon_emote.build(sc, neon, EMOTE, W_E, GLOW, SWEEP)

# the emote assembles from its tubes like the original's slats: each part sweeps in from off
# screen on its own path and locks into place, staggered
ASSEMBLE = {   # part: (offset at F0 in logo units, z-turn in degrees, frame it locks in)
    'yellow': ((-3.2, 2.6, 1.6), 40, 1150),
    'green': ((3.6, -1.8, 2.4), -35, 1156),
    'bell': ((4.0, 3.0, 1.4), 60, 1160),
    'white': ((-2.6, -3.0, 2.8), -50, 1164),
    'lips': ((1.8, -3.8, 2.0), 45, 1167),
}
groups = {}
for o in parts:
    part = o.name.split('_', 1)[1].split('.')[0] if '_' in o.name else 'white'   # pupils ride with the eyes
    if part == 'pupil': part = 'white'
    if part not in groups:
        off, turn, lock = ASSEMBLE[part]
        g = groups[part] = empty('part_' + part, neon)
        key(g, 'location', [(F0, off), (lock, (0, 0, 0))], 'CUBIC', 'EASE_OUT')
        key(g, 'rotation_euler', [(F0, (0, 0, math.radians(turn))), (lock, (0, 0, 0))], 'CUBIC', 'EASE_OUT')
    o.parent = groups[part]
    # far-off specks of the parts would flicker on the first frames after the cut: show from 1116
    for f, h in ((F0, True), (1116, False)):
        o.hide_render = h; o.keyframe_insert('hide_render', frame=f)
    for c in _curves(o):
        for k in c.keyframe_points: k.interpolation = 'CONSTANT'

# a dim painted backing so the emote still reads as a shape between the tubes
img = bpy.data.images.load(EMOTE)
H_E = W_E * 93 / 109
bpy.ops.mesh.primitive_plane_add(size=1)
em_o = bpy.context.active_object; em_o.parent = neon
em_o.scale = (W_E, H_E, 1); em_o.location = (0, 0, -0.08)
u0, u1, v0, v1 = 2 / 128, 111 / 128, 0.0, 93 / 128
for loop in em_o.data.loops:
    co = em_o.data.vertices[loop.vertex_index].co
    em_o.data.uv_layers.active.data[loop.index].uv = (u0 if co.x < 0 else u1, v0 if co.y < 0 else v1)
m = bpy.data.materials.new('backing'); m.use_nodes = True; m.surface_render_method = 'BLENDED'
nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
tex = N.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'; tex.extension = 'CLIP'
# additive, so it never darkens what's behind it (it sweeps right past the camera on the fly-in)
emn = N.new('ShaderNodeEmission'); st = N.new('ShaderNodeMath'); st.operation = 'MULTIPLY'
for f, v in ((F0, 0.0), (1166, 0.0), (1182, 0.13)):   # only once the parts have locked together
    st.inputs[1].default_value = v; st.inputs[1].keyframe_insert('default_value', frame=f)
tr = N.new('ShaderNodeBsdfTransparent'); add = N.new('ShaderNodeAddShader')
out = N.new('ShaderNodeOutputMaterial')
L.new(tex.outputs['Color'], emn.inputs[0]); L.new(tex.outputs['Alpha'], st.inputs[0]); L.new(st.outputs[0], emn.inputs['Strength'])
L.new(tr.outputs[0], add.inputs[0]); L.new(emn.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs[0])
em_o.data.materials.append(m)

# warm aura behind the emote once it lights up (ENJOY THE SHOW), additive
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=3.0, fill_type='NGON')
aura = bpy.context.active_object; aura.parent = neon; aura.location = (0, -0.1, -0.12)
m = bpy.data.materials.new('aura'); m.use_nodes = True; m.surface_render_method = 'BLENDED'
nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
tc = N.new('ShaderNodeTexCoord'); ln = N.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
L.new(tc.outputs['Object'], ln.inputs[0])
fall = N.new('ShaderNodeMapRange'); fall.inputs['From Max'].default_value = 3.0
fall.inputs['To Min'].default_value = 1; fall.inputs['To Max'].default_value = 0
L.new(ln.outputs['Value'], fall.inputs['Value'])
sq = N.new('ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 3.0; L.new(fall.outputs['Result'], sq.inputs[0])
amt = N.new('ShaderNodeValue')
for f, v in ((F0, 0.0), (FLIP, 0.0), (1288, 0.5), (1300, 0.26)):   # a soft warm lift, not a disc
    amt.outputs[0].default_value = v; amt.outputs[0].keyframe_insert('default_value', frame=f)
k = N.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; L.new(sq.outputs[0], k.inputs[0]); L.new(amt.outputs[0], k.inputs[1])
emn = N.new('ShaderNodeEmission'); emn.inputs['Color'].default_value = lin('#FF8A2A'); L.new(k.outputs[0], emn.inputs['Strength'])
tr = N.new('ShaderNodeBsdfTransparent'); add = N.new('ShaderNodeAddShader'); out = N.new('ShaderNodeOutputMaterial')
L.new(tr.outputs[0], add.inputs[0]); L.new(emn.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs[0])
aura.data.materials.append(m)

# --- light rays: a burst behind the ring while it flies in (teal), side rays for ENJOY THE SHOW (orange)
def ray(parent, ang, r0, length, w0, w1, mats, head=0.07):
    mat, head_mat = mats
    a = math.radians(ang); d = (math.cos(a), math.sin(a)); n = (-d[1], d[0])
    p = lambda r, w: (d[0] * r + n[0] * w, d[1] * r + n[1] * w, -0.01)
    me = bpy.data.meshes.new('ray')
    me.from_pydata([p(r0, -w0), p(r0 + length, -w1), p(r0 + length, w1), p(r0, w0)], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new()
    for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uvl.data[i].uv = uv
    o = bpy.data.objects.new('ray', me); sc.collection.objects.link(o); o.parent = parent
    o.data.materials.append(mat)
    bpy.ops.mesh.primitive_circle_add(vertices=20, radius=head, fill_type='NGON')
    c = bpy.context.active_object; c.parent = parent; c.location = (d[0] * r0, d[1] * r0, -0.005)
    c.data.materials.append(head_mat)

random.seed(7)
burst = empty('burst', logo)
mat_a = ray_material('ray_teal', RAY_TEAL, [(F0, 0.0), (1130, 0.0), (1146, 1.0), (1188, 1.0), (1208, 0.0)])
for i in range(26):
    ang = i * 360 / 26 + random.uniform(-4, 4)
    ray(burst, ang, 3.85, random.uniform(2.5, 5.0), 0.07, random.uniform(0.35, 0.6), mat_a)
side = empty('side_rays', logo)
mat_d = ray_material('ray_orange', RAY_ORANGE, [(1286, 0.0), (1298, 1.0)])
# spotlights as in the original: bright heads just outside the ring, beams flaring outward
for ang in (33, 13, -7, 147, 167, 187):
    ray(side, ang, 3.2, 2.6, 0.06, 0.62, mat_d, 0.09)
key(side, 'scale', [(1286, (0.85, 0.85, 1)), (1300, (1, 1, 1))])

# --- camera: starts close and tilted, pulls back as the ring spins into place (like the original)
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 37.5; cam_data.sensor_fit = 'HORIZONTAL'
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, 0, 20)
# the neon emote sweeps in from right in front of the camera (where the slats came from), then
# scale vs the settled logo: ~2.7x at 1168, ~1.5x at 1188, ~1.15x at 1200 (measured on the original)
key(cam, 'location', [(F0, (CX + 1.4, CY - 0.8, 1.6)), (1146, (CX * 0.6, CY, 3.5)), (1170, (CX * 0.3, CY * 0.5, 8)),
                      (1188, (0, 0, 13)), (1206, (0, 0, 20))])
key(logo, 'rotation_euler', [(F0, (math.radians(62), math.radians(-35), 0)), (1204, (0, 0, 0))], 'CUBIC', 'EASE_OUT')
key(ring1, 'rotation_euler', [(F0, (0, 0, math.radians(-140))), (1204, (0, 0, 0))], 'CUBIC', 'EASE_OUT')
key(burst, 'rotation_euler', [(F0, (0, 0, math.radians(-40))), (1206, (0, 0, 0))], 'CUBIC', 'EASE_OUT')

# background: the original's last clean neon-city frame, pushing in and fading to black
# under the fly-in (the original's own background is gone by ~1170)
bpy.ops.mesh.primitive_plane_add(size=1)
plate = bpy.context.active_object; plate.parent = cam
DIST = 60.0; pw = 36 / cam_data.lens * DIST
plate.location = (0, 0, -DIST)
# keeps the original camera's drift (measured 1092-1108: ~6.8 px/frame right, ~3 px/frame up at
# 1080p) so the cut doesn't freeze; the push-in grows faster than the drift so no edge shows
key(plate, 'scale', [(F0, (pw, pw * 9 / 16, 1)), (1168, (pw * 1.5, pw * 1.5 * 9 / 16, 1))], 'LINEAR')
key(plate, 'location', [(F0, (0, 0, -DIST)), (1168, (pw * 0.2, pw * 9 / 16 * 0.16, -DIST))], 'LINEAR')
key(plate, 'rotation_euler', [(F0, (0, 0, 0)), (1168, (0, 0, math.radians(-4)))], 'LINEAR')
m = bpy.data.materials.new('plate'); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
tex = N.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(PLATE); tex.extension = 'EXTEND'
emn = N.new('ShaderNodeEmission'); out = N.new('ShaderNodeOutputMaterial')
L.new(tex.outputs['Color'], emn.inputs['Color']); L.new(emn.outputs[0], out.inputs[0])
for f, v in ((F0, 1.0), (1134, 0.85), (1166, 0.0)):
    emn.inputs['Strength'].default_value = v; emn.inputs['Strength'].keyframe_insert('default_value', frame=f)
plate.data.materials.append(m)
cam_data.clip_end = 200

# --- the flip: DINK DONK turns edge-on, ENJOY THE SHOW comes round from behind
key(ring1, 'rotation_euler', [(1274, 0), (1283, math.radians(90))], 'SINE', 'EASE_IN', index=1)
key(ring2, 'rotation_euler', [(1283, math.radians(-90)), (1292, 0)], 'SINE', 'EASE_OUT', index=1)
# ring1 from 1116: before that its letters are far-off specks right after the cut
for o, shown in ((ring1, (1116, 1283)), (ring2, (1283, F1 + 1))):
    for ch in [o] + list(o.children):
        for f, h in ((F0 - 1, True), (shown[0], False), (shown[1], True)):
            ch.hide_render = h; ch.keyframe_insert('hide_render', frame=f)
        for c in _curves(ch):
            if c.data_path == 'hide_render':
                for k in c.keyframe_points: k.interpolation = 'CONSTANT'

os.makedirs(OUT, exist_ok=True)
frames = ONLY or range(F0, F1 + 1)
for f in frames:
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, f'dd_{f:05d}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'dinkdonk_logo.blend'))
