# Turns the DinkDonk emote PNG into a neon sign: each colour region (hat/body, face/arm, eyes,
# lips, bell) is traced into smooth closed outlines and built as glowing tubes, with soft additive
# halos around them. Used by build_logo.py.
import bpy, math
import numpy as np

UP = 4            # contour grid = 4x the emote's pixels
FINE = ('white', 'pupil', 'lips')   # small features: thinner tubes, lighter smoothing
CROP = (2, 111, 35, 128)   # x0, x1, y0, y1 (top-first rows) of the emote's opaque box

# region -> (tube colour, halo colour), sRGB
NEON = {
    'yellow': ('#F6FF5C', '#D9F200'),
    'green':  ('#7DFFB8', '#14D274'),
    'white':  ('#FFFFFF', '#BFE4FF'),
    'lips':   ('#FFC060', '#FF8A1C'),
    'bell':   ('#FFE070', '#F0A800'),
    'pupil':  ('#A8DCFF', '#4AA8FF'),
}

def _lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1]

def _regions(path):
    im = bpy.data.images.load(path, check_existing=True); im.colorspace_settings.name = 'sRGB'
    w, h = im.size
    p = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1]          # top row first
    rgb, a = p[..., :3], p[..., 3] > 0.5
    mx, mn = rgb.max(-1), rgb.min(-1); v = mx; s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    m = {
        'yellow': a & (hue >= 52) & (hue < 85) & (s > 0.55) & (v > 0.75),
        'green':  a & (hue >= 110) & (hue < 175) & (s > 0.35) & (v > 0.4),
        'white':  a & (s < 0.25) & (v > 0.8),
        'lips':   a & (hue >= 12) & (hue < 50) & (s > 0.45) & (v > 0.6),
        'bell':   a & (hue >= 30) & (hue < 70) & (s > 0.35) & (v > 0.18) & (v <= 0.75),
    }
    x0, x1, y0, y1 = CROP
    m = {k: v_[y0:y1, x0:x1] for k, v_ in m.items()}
    a, v = a[y0:y1, x0:x1], v[y0:y1, x0:x1]
    rows, cols = np.indices(a.shape)
    # the bell (top right) has yellow highlights and a dark rim: one gold region
    bell_box = (cols >= 85) & (rows < 43)
    m['bell'] = a & bell_box & ~m['green']
    for k in ('yellow', 'lips', 'white'):
        m[k] &= ~bell_box
    # pupils sit inside the eye band: fill them into the eye outline, then draw them as dots
    eye_box = (rows >= 40) & (rows <= 56) & (cols >= 45) & (cols <= 91)
    m['pupil'] = a & eye_box & (v < 0.3)
    m['white'] = (m['white'] & eye_box) | m['pupil']
    return m

def _blur(f, sigma):
    r = int(sigma * 3); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    f = np.apply_along_axis(lambda row: np.convolve(row, k, 'same'), 1, f)
    return np.apply_along_axis(lambda col: np.convolve(col, k, 'same'), 0, f)

# marching squares: corner bits tl=8 tr=4 br=2 bl=1; edges 0 top, 1 right, 2 bottom, 3 left
_CASES = {1: [(3, 2)], 2: [(2, 1)], 3: [(3, 1)], 4: [(0, 1)], 5: [(3, 0), (2, 1)], 6: [(0, 2)],
          7: [(3, 0)], 8: [(3, 0)], 9: [(0, 2)], 10: [(3, 2), (0, 1)], 11: [(0, 1)], 12: [(3, 1)],
          13: [(2, 1)], 14: [(3, 2)]}

def _contours(f, level):
    f = np.pad(f, 1)
    bits = (f > level).astype(np.int32)
    case = bits[:-1, :-1] * 8 + bits[:-1, 1:] * 4 + bits[1:, 1:] * 2 + bits[1:, :-1]
    def eid(i, j, e):
        return [('h', i, j), ('v', i, j + 1), ('h', i + 1, j), ('v', i, j)][e]
    adj = {}
    for i, j in zip(*np.nonzero((case > 0) & (case < 15))):
        for a, b in _CASES[int(case[i, j])]:
            ea, eb = eid(i, j, a), eid(i, j, b)
            adj.setdefault(ea, []).append(eb); adj.setdefault(eb, []).append(ea)
    def pt(e):
        k, i, j = e
        if k == 'h': v1, v2 = f[i, j], f[i, j + 1]; t = (level - v1) / (v2 - v1); return (j + t, i)
        v1, v2 = f[i, j], f[i + 1, j]; t = (level - v1) / (v2 - v1); return (j, i + t)
    loops, seen = [], set()
    for start in adj:
        if start in seen: continue
        loop, prev, cur = [start], None, start; seen.add(start)
        while True:
            nxt = [n for n in adj[cur] if n != prev]
            if not nxt: break
            prev, cur = cur, nxt[0]
            if cur == start: break
            if cur in seen: break
            seen.add(cur); loop.append(cur)
        if len(loop) > 3:
            loops.append(np.array([pt(e) for e in loop]) - 1)     # undo the pad
    return loops

def _resample(loop, step):
    p = np.vstack([loop, loop[:1]]); seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); n = max(8, int(s[-1] / step))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)

def _smooth(loop, it=8):
    for _ in range(it):
        loop = 0.5 * loop + 0.25 * (np.roll(loop, 1, 0) + np.roll(loop, -1, 0))
    return loop

def _eye_outline(mask, inset=0.9):
    """One clean outline for the eye band: its smoothed top and bottom edge per column
    (the pixel trace breaks up around the pupils and highlights)."""
    cols = np.nonzero(mask.any(0))[0]
    top = np.array([np.nonzero(mask[:, c])[0].min() for c in cols], float)
    bot = np.array([np.nonzero(mask[:, c])[0].max() + 1 for c in cols], float)
    k = np.ones(5) / 5
    top = np.convolve(np.pad(top, 2, 'edge'), k, 'valid') + inset
    bot = np.convolve(np.pad(bot, 2, 'edge'), k, 'valid') - inset
    x = cols + 0.5
    loop = np.vstack([np.stack([x, top], 1), np.stack([x[::-1], bot[::-1]], 1)])
    return _smooth(_resample(loop, 0.6), 6)

def pupils(path):
    """(x, y, radius) of each pupil in emote pixels."""
    m = _regions(path)['pupil']
    out, seen = [], np.zeros_like(m)
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]: continue
        stack, pts = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); pts.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
        if len(pts) < 6: continue
        p = np.array(pts, float) + 0.5
        out.append((p[:, 1].mean(), p[:, 0].mean(), max(1.6, math.sqrt(len(pts) / math.pi) * 0.85)))
    return out

def trace(path, inset=0.72, min_len=7.0):
    """Region name -> list of closed outlines in emote pixels (x right, y down, crop-relative)."""
    out = {}
    regions = _regions(path)
    for name, mask in regions.items():
        if name == 'white':
            out[name] = [_eye_outline(mask)]; continue
        if name == 'pupil':
            continue          # drawn as solid dots, see pupils()
        big =np.repeat(np.repeat(mask.astype(np.float32), UP, 0), UP, 1)
        f = _blur(big, UP * (0.7 if name == 'pupil' else 1.1))
        loops = []
        for lp in _contours(f, 0.45 if name == 'pupil' else inset):
            lp = (lp + 0.5) / UP
            per = np.linalg.norm(np.diff(np.vstack([lp, lp[:1]]), axis=0), axis=1).sum()
            if per < min_len: continue
            # slivers (the thin lid line above the eye, highlight holes) only clutter the face
            if name not in FINE and min(np.ptp(lp, 0)) < 4.5: continue
            loops.append(_smooth(_resample(lp, 0.6), 3 if name in FINE else 8))
        out[name] = loops
    return out

def _tube_material(name, tube, band):
    """Neon tube: saturated colour with a whiter core, brightened by the sweep band."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission')
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
    L.new(lw.outputs['Facing'], inv.inputs[1])
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3
    L.new(inv.outputs[0], pw.inputs[0])
    core = N.new('ShaderNodeMath'); core.operation = 'MULTIPLY'; core.inputs[1].default_value = 0.6
    L.new(pw.outputs[0], core.inputs[0])
    whiter = N.new('ShaderNodeMath'); whiter.operation = 'ADD'; whiter.use_clamp = True
    L.new(core.outputs[0], whiter.inputs[0]); L.new(band(N, L), whiter.inputs[1])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = tube; mix.inputs['B'].default_value = (1, 1, 1, 1)
    L.new(whiter.outputs[0], mix.inputs['Factor'])
    L.new(mix.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.6
    L.new(em.outputs[0], out.inputs[0])
    return m

def _halo_material(name, halo, strength, glow_keys, band):
    """Additive soft glow: brightest along the tube's centre line, fading to its silhouette."""
    m = bpy.data.materials.new(name); m.use_nodes = True; m.surface_render_method = 'BLENDED'
    m.use_backface_culling = True     # only the front shell adds light
    nt = m.node_tree; nt.nodes.clear(); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = halo
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
    L.new(lw.outputs['Facing'], inv.inputs[1])
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
    L.new(inv.outputs[0], pw.inputs[0])
    glow = N.new('ShaderNodeValue'); glow.name = 'glow'
    for f, v in glow_keys:
        glow.outputs[0].default_value = v; glow.outputs[0].keyframe_insert('default_value', frame=f)
    boost = N.new('ShaderNodeMath'); boost.operation = 'MULTIPLY_ADD'; boost.inputs[1].default_value = 1.5
    L.new(band(N, L), boost.inputs[0]); L.new(glow.outputs[0], boost.inputs[2])
    k = N.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; L.new(pw.outputs[0], k.inputs[0]); L.new(boost.outputs[0], k.inputs[1])
    k2 = N.new('ShaderNodeMath'); k2.operation = 'MULTIPLY'; k2.inputs[1].default_value = strength
    L.new(k.outputs[0], k2.inputs[0]); L.new(k2.outputs[0], em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent'); add = N.new('ShaderNodeAddShader')
    L.new(tr.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs[0])
    return m

def build(scene, parent, path, width, glow_keys, sweep_keys, tube_r=0.034, lin=_lin):
    """Neon emote centred on `parent`, `width` units wide. glow_keys: [(frame, halo gain)];
    sweep_keys: [(frame, y)] position of a bright band that runs over the tubes (the flip flash)."""
    x0, x1, y0, y1 = CROP
    sc_ = width / (x1 - x0); cx, cy = (x1 - x0) / 2, (y1 - y0) / 2
    sweep_holder = []

    def band(N, L):
        # brightness band around y = sweep (in the neon's own space)
        tc = N.new('ShaderNodeTexCoord'); tc.object = parent
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
        sw = N.new('ShaderNodeValue'); sw.name = 'sweep'
        for f, v in sweep_keys:
            sw.outputs[0].default_value = v; sw.outputs[0].keyframe_insert('default_value', frame=f)
        d = N.new('ShaderNodeMath'); d.operation = 'SUBTRACT'; L.new(sep.outputs['Y'], d.inputs[0]); L.new(sw.outputs[0], d.inputs[1])
        ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; L.new(d.outputs[0], ab.inputs[0])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = 0.7
        mr.inputs['To Min'].default_value = 1; mr.inputs['To Max'].default_value = 0
        L.new(ab.outputs[0], mr.inputs['Value'])
        return mr.outputs['Result']

    objs = []
    for name, loops in trace(path).items():
        if not loops: continue
        tube_c, halo_c = (lin(c) for c in NEON[name])
        cu = bpy.data.curves.new('neon_' + name, 'CURVE'); cu.dimensions = '3D'
        r_ = tube_r * (0.6 if name in FINE else 1.0)
        cu.bevel_depth = r_; cu.bevel_resolution = 3; cu.use_fill_caps = True
        for lp in loops:
            sp = cu.splines.new('POLY'); sp.points.add(len(lp) - 1); sp.use_cyclic_u = True
            for p_, (x, y) in zip(sp.points, lp):
                p_.co = ((x - cx) * sc_, (cy - y) * sc_, 0, 1)
        tube = bpy.data.objects.new('neon_' + name, cu); scene.collection.objects.link(tube); tube.parent = parent
        cu.materials.append(_tube_material('tube_' + name, tube_c, band))
        objs.append(tube)
        # two halo shells: a tight bright one and a wide faint one
        for i, (r, st) in enumerate(((r_ * 3.2, 0.9), (r_ * 8.0, 0.25))):
            hc = cu.copy(); hc.bevel_depth = r; hc.materials.clear()
            hc.materials.append(_halo_material(f'halo{i}_{name}', halo_c, st, glow_keys, band))
            ho = bpy.data.objects.new(f'halo{i}_{name}', hc); scene.collection.objects.link(ho); ho.parent = parent
            ho.location.z = -0.02 * (i + 1)
            objs.append(ho)
    # pupils: solid glowing dots (flattened spheres, so the core/halo shading still works)
    tube_c, halo_c = (lin(c) for c in NEON['pupil'])
    core_m = _tube_material('tube_pupil', tube_c, band)
    halo_m = _halo_material('halo_pupil', halo_c, 0.9, glow_keys, band)
    for x, y, r in pupils(path):
        for rad, mat, z in ((r * sc_, core_m, 0.0), (r * sc_ * 2.6, halo_m, -0.03)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=rad)
            o = bpy.context.active_object; o.parent = parent
            o.location = ((x - cx) * sc_, (cy - y) * sc_, z); o.scale.z = 0.3
            o.data.materials.append(mat); objs.append(o)
    return objs
