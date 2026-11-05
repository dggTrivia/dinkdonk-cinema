# Replaces the slatted N on the neon dome (source frames 1388-1446) with the neon DinkDonk
# face: smooth the panel track from track_sign.py, warp sign_face.png onto the panel over its
# own red, keep the dome's bulb strings in front, and paint the slats of the second, half
# off-screen panel at the left edge out with that panel's red. Writes full frames sg_NNNNN.png.
#
#   blender -b --factory-startup --python sign_replace.py -- <frames_dir> <track.json> <out_dir>
import bpy, sys, os, json
import numpy as np

A = sys.argv[sys.argv.index('--') + 1:]
FR, TRACK, OUT = A[0], A[1], A[2]
HERE = os.path.dirname(os.path.abspath(__file__))
F0, F1 = 1388, 1452          # panel fades in from black at 1388; gone round the dome after 1452
FIT0, FIT1 = 1401, 1452      # frames with a full-strength measurement
LEFT = (1392, 1431)          # the second panel at the left edge
os.makedirs(OUT, exist_ok=True)

def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    p = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3].copy()
    bpy.data.images.remove(im)
    return p

def save(rgb, path):
    h, w = rgb.shape[:2]
    o = np.ones((h, w, 4), np.float32); o[..., :3] = np.clip(rgb, 0, 1)
    im = bpy.data.images.new('o', w, h); im.pixels = o[::-1].ravel()
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1); d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return hue, (mx - mn) / np.maximum(mx, 1e-6), mx

def blur(f, sigma):
    if sigma <= 0: return f
    r = int(sigma * 3) + 1; x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    f = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 0, f)
    return np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 1, f)

# ---- smooth the main panel track: robust polynomial per parameter. The bottom edge comes
# from the slat spacing (the thin bottom slats vanish as the panel recedes; the evenly spaced
# thick top ones stay measurable): panel height = SLATS * spacing, from the frontal frames.
SLATS = 9.1
PITCH_FIT1 = 1441            # spacing gets unreliable once the panel is ~60 px wide
tr = json.load(open(TRACK))['main']
fs = np.array(sorted(int(f) for f in tr if FIT0 <= int(f) <= FIT1))
P = np.array([[tr[str(f)]['quad'][0][0], tr[str(f)]['quad'][1][0],      # lx, rx
               tr[str(f)]['quad'][0][1], tr[str(f)]['quad'][1][1],      # left top, right top
               tr[str(f)]['pitch'][0], tr[str(f)]['pitch'][1]] for f in fs])  # slat spacing L, R

def robust_fit(x, y, deg):
    keep = np.ones(len(x), bool)
    for _ in range(4):
        c = np.polyfit(x[keep], y[keep], deg)
        res = y - np.polyval(c, x)
        mad = np.median(np.abs(res[keep])) * 1.4826 + 0.5
        keep = np.abs(res) < 2.5 * mad
    return c, int(keep.sum())

fits = []
for j in range(P.shape[1]):
    sel = (P[:, j] > 0) & ((fs <= PITCH_FIT1) if j >= 4 else True)
    c, k = robust_fit(fs[sel], P[sel, j], 3 if j >= 4 else 4)
    fits.append(c)
    print('FIT', j, 'kept', k, 'of', int(sel.sum()))

def panel(f):
    t = min(max(f, FIT0), FIT1)
    lx, rx, ylt, yrt = (np.polyval(c, t) for c in fits[:4])
    def sp(c):   # past the last reliable spacing, continue it in a straight line
        if t <= PITCH_FIT1: return np.polyval(c, t)
        return max(4.0, np.polyval(c, PITCH_FIT1) + np.polyval(np.polyder(c), PITCH_FIT1) * (t - PITCH_FIT1))
    pl, pr = sp(fits[4]), sp(fits[5])
    return np.array([[lx, ylt], [rx, yrt], [rx, yrt + SLATS * pr], [lx, ylt + SLATS * pl]], float)

def expand(q, side, top, bottom):
    """Grow the slat block to the red box: by a fraction of its width/height per side
    (the thin bottom slats are often missed by the tracker, so the bottom grows most)."""
    q = q.copy(); w = q[1, 0] - q[0, 0]
    q[[0, 3], 0] -= side * w; q[[1, 2], 0] += side * w
    for t, b in ((0, 3), (1, 2)):
        h = q[b, 1] - q[t, 1]; q[t, 1] -= top * h; q[b, 1] += bottom * h
    return q

def homography(src, dst):
    M = []
    for (x, y), (u, v) in zip(src, dst):
        M.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u]); M.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(M)); return vt[-1].reshape(3, 3)

face = load(os.path.join(HERE, 'sign_face.png'))
fh, fw = face.shape[:2]
ref_lum = load(os.path.join(FR, 'g%05d.png' % FIT0)).mean()

def sample(tex, u, v):
    h, w = tex.shape[:2]
    x = np.clip(u * (w - 1), 0, w - 1.001); y = np.clip(v * (h - 1), 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); dx, dy = (x - x0)[..., None], (y - y0)[..., None]
    return (tex[y0, x0] * (1 - dx) * (1 - dy) + tex[y0, x0 + 1] * dx * (1 - dy)
            + tex[y0 + 1, x0] * (1 - dx) * dy + tex[y0 + 1, x0 + 1] * dx * dy)

def keep_front(rgb):
    """Bulbs and the white-hot cores of the bulb strings that cross in front of the panel."""
    h, s, v = hsv(rgb)
    m = (((h > 150) & (h < 345) & (s > 0.3) & (v > 0.35)) | ((s < 0.2) & (v > 0.78))).astype(np.float32)
    return np.clip(blur(m, 1.2) * 1.4, 0, 1)

def put_sign(out, img, q, gain=1.0, blur_px=1.0):
    """Warp the neon face onto quad q (tl, tr, br, bl) over the panel's own red."""
    H, W = img.shape[:2]
    x0, y0 = np.floor(q.min(0)).astype(int) - 4; x1, y1 = np.ceil(q.max(0)).astype(int) + 4
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 - x0 <= 4 or y1 - y0 <= 4: return
    Hm = homography(q, np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float))
    X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    uvw = np.tensordot(np.stack([X, Y, np.ones_like(X)], -1), Hm.T, 1)
    u, v = uvw[..., 0] / uvw[..., 2], uvw[..., 1] / uvw[..., 2]
    inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    edge = np.clip(np.minimum.reduce([u, 1 - u, v, 1 - v]) / 0.05, 0, 1) * inside
    crop = img[y0:y1, x0:x1]
    hh, ss, vv = hsv(crop)
    reds = crop[inside & (hh < 22) & (ss > 0.6) & (vv > 0.35)]
    red = np.median(reds, 0) if len(reds) > 30 else np.array([0.75, 0.2, 0.08])
    border = np.clip((np.minimum.reduce([u, 1 - u, v, 1 - v]) - 0.06) / 0.03, 0, 1)
    base = red[None, None, :] * (1 - 0.62 * border[..., None])      # darker inside, red rim
    neon = sample(face, 0.08 + u * 0.84, 0.08 + v * 0.84) * (border[..., None] > 0)
    sign = (1 - (1 - base) * (1 - np.clip(neon * 1.05, 0, 1))) * gain   # screen; dim in the fade-in
    sign = blur(sign, blur_px * 0.6)
    a = blur(edge, blur_px)[..., None]          # always fully cover the N
    cur = out[y0:y1, x0:x1]
    mix = cur * (1 - a) + sign * a
    front = keep_front(crop)[..., None] * a
    out[y0:y1, x0:x1] = mix * (1 - front) + crop * front

def paint_out(out, box, blur_px=3.0):
    """Paint any slat pixels left in box with the panel's own red (bulbs stay in front)."""
    H, W = out.shape[:2]
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 - x0 < 3 or y1 - y0 < 3: return
    crop = out[y0:y1, x0:x1]
    hh, ss, vv = hsv(crop)
    slat = ((hh >= 33) & (hh <= 60) & (ss > 0.15) & (vv > 0.33)).astype(np.float32)
    slat = np.clip(blur(slat, blur_px) * 3.0, 0, 1)
    reds = crop[(hh < 22) & (ss > 0.6) & (vv > 0.35)]
    red = np.median(reds, 0) if len(reds) > 30 else np.array([0.72, 0.18, 0.07])
    front = keep_front(crop)
    a = (slat * (1 - front))[..., None]
    out[y0:y1, x0:x1] = crop * (1 - a) + red[None, None, :] * a

def find_panels(img, y_min=420, cell=4):
    """Small slat panels on the far side of the dome as it turns: dense, striped blocks of
    pale-yellow slat pixels. Returns full-res boxes (x0, y0, x1, y1)."""
    hh, ss, vv = hsv(img)
    m = (hh >= 37) & (hh <= 57) & (ss > 0.22) & (ss < 0.85) & (vv > 0.45)
    m[:y_min] = False
    Hc, Wc = m.shape[0] // cell, m.shape[1] // cell
    g = m[:Hc * cell, :Wc * cell].reshape(Hc, cell, Wc, cell).any(3).any(1)
    gd = g.copy(); gd[1:] |= g[:-1]; gd[:-1] |= g[1:]; gd[2:] |= g[:-2]   # join slats vertically
    seen = np.zeros_like(gd); boxes = []
    for y, x in zip(*np.nonzero(gd)):
        if seen[y, x]: continue
        stack, cells = [(y, x)], []; seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); cells.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < Hc and 0 <= nx < Wc and gd[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
        c = np.array(cells); (ya, xa), (yb, xb) = c.min(0), c.max(0) + 1
        bw, bh = xb - xa, yb - ya
        if len(cells) < 10 or bw < 4 or bh < 4 or not (0.35 < bw / bh < 2.5): continue
        if len(cells) / (bw * bh) < 0.45: continue
        sub = m[ya * cell:yb * cell, xa * cell:xb * cell]
        occ = sub.mean(1); rows = occ > 0.3
        runs = int(np.sum(rows[1:] & ~rows[:-1]) + rows[0])
        hi = np.nonzero(rows)[0]
        gaps = int(np.sum(occ[hi[0]:hi[-1] + 1] < 0.12)) if len(hi) else 0
        # needs the stacked-slat look (bars with clear gaps)...
        if runs < 3 or gaps < 1: continue
        box = (xa * cell, ya * cell, xb * cell, yb * cell)
        # ...on the panel's red: glowing tubes and blur streaks sit on dark or orange
        if is_panel(m, red_mask(hh, ss, vv), box, 0.28, 0.2): boxes.append(box)
    return boxes

def red_mask(hh, ss, vv):
    return (hh < 22) & (ss > 0.55) & (vv > 0.3)

def is_panel(slat, red, box, min_slat, min_red):
    x0, y0, x1, y1 = box
    s, r = slat[y0:y1, x0:x1], red[y0:y1, x0:x1]
    if s.size == 0: return False
    rest = max(1, (~s).sum())
    return s.mean() >= min_slat and (r & ~s).sum() / rest >= min_red

def measure(slat, red, box, grow=0.5):
    """Re-find a tracked panel near its last box: the slat pixels' extent in a grown window."""
    H, W = slat.shape
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    X0, Y0 = max(0, int(x0 - grow * w)), max(0, int(y0 - grow * h))
    X1, Y1 = min(W, int(x1 + grow * w)), min(H, int(y1 + grow * h))
    yy, xx = np.nonzero(slat[Y0:Y1, X0:X1])
    if len(xx) < 30: return None
    nb = (int(np.percentile(xx, 4)) + X0, int(np.percentile(yy, 4)) + Y0,
          int(np.percentile(xx, 96)) + X0 + 1, int(np.percentile(yy, 96)) + Y0 + 1)
    nw, nh = nb[2] - nb[0], nb[3] - nb[1]
    if not (0.55 < nw / max(w, 1) < 1.8 and 0.55 < nh / max(h, 1) < 1.8): return None
    return nb if is_panel(slat, red, nb, 0.2, 0.15) else None

SMALL = (1430, 1530)          # further N panels come round the dome until it leaves frame
PATH0 = 1444                  # the far panel's path starts after the main sign is gone
masks = {}
for f in range(SMALL[0], SMALL[1] + 1):
    hh, ss, vv = hsv(load(os.path.join(FR, 'g%05d.png' % f)))
    masks[f] = ((hh >= 37) & (hh <= 57) & (ss > 0.22) & (ss < 0.85) & (vv > 0.45), red_mask(hh, ss, vv))
seeds = {f: find_panels(load(os.path.join(FR, 'g%05d.png' % f))) for f in masks}

def overlaps(a, b):
    ix = min(a[2], b[2]) - max(a[0], b[0]); iy = min(a[3], b[3]) - max(a[1], b[1])
    return ix > 0 and iy > 0 and ix * iy > 0.3 * min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))

# follow every seed forwards and backwards; hold the last box through short misses
tracks = []
for f0 in sorted(seeds):
    for seed in seeds[f0]:
        if any(f0 in t and overlaps(t[f0], seed) for t in tracks): continue
        t = {f0: seed}
        for step in (1, -1):
            box, miss, g = seed, 0, f0 + step
            while SMALL[0] <= g <= SMALL[1] and miss <= 2:
                nb = measure(*masks[g], box)
                if nb: box, miss = nb, 0
                else: miss += 1
                t[g] = box; g += step
        tracks.append(t)
# panels that are the main sign (already replaced up to F1) are not far panels
def is_main(f, b):
    if f > F1: return False
    q = expand(panel(f), 0.06, 0.05, 0.08)
    return overlaps(b, (q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max()))
for t in tracks: print('TRACKED', min(t), max(t), t[min(t)])
# All far detections lie on one smooth path: the next panel on the dome swings from the
# left of the dome (~1453) down past the bottom of the frame (~1530). Fit that path
# (centre, size over time) through every seed and tracked box, so the panel is covered
# in every frame, not just where it was detected.
obs = [(g, b) for g, bs in seeds.items() for b in bs] + [(g, b) for t in tracks for g, b in t.items()]
obs = [(g, b) for g, b in obs if g >= PATH0 and not is_main(g, b)]
# where it swings in from behind the dome its slats are motion-blurred and the detector
# misses them: boxes read off those frames by eye anchor the start of the path
ENTRY = {1446: (195, 505, 265, 630), 1450: (250, 505, 335, 655), 1454: (330, 520, 420, 655),
         1458: (415, 550, 500, 675), 1462: (500, 560, 590, 670)}
obs += [(g, b) for g, b in ENTRY.items() for _ in range(3)]
far = {}
if len(obs) >= 8:
    T = np.array([g for g, _ in obs], float)
    B = np.array([b for _, b in obs], float)
    C = np.stack([(B[:, 0] + B[:, 2]) / 2, (B[:, 1] + B[:, 3]) / 2, B[:, 2] - B[:, 0], B[:, 3] - B[:, 1]], 1)
    keep = np.ones(len(T), bool)
    for _ in range(5):
        cs = [np.polyfit(T[keep], C[keep, j], 3) for j in range(4)]
        pred = np.stack([np.polyval(c, T) for c in cs], 1)
        err = np.hypot(*(C[:, :2] - pred[:, :2]).T) / np.maximum(pred[:, 2], 8)
        keep = err < 0.6
    print('PATH inliers', int(keep.sum()), 'of', len(T), 'frames', int(T[keep].min()), int(T[keep].max()))
    for g in range(int(T[keep].min()) - 2, int(T[keep].max()) + 3):
        cx, cy, w, h = (np.polyval(c, g) for c in cs)
        far[g] = [(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)]

def motion_blur(c_prev, c_next):
    """The footage smears with the camera; soften the sign by how fast its panel moves."""
    speed = np.hypot(*(np.asarray(c_next) - np.asarray(c_prev))) / 2
    return min(4.0, 1.0 + 0.09 * speed)

def centre(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

for f in range(F0, SMALL[1] + 1):
    img = load(os.path.join(FR, 'g%05d.png' % f))
    gain = min(1.0, img.mean() / ref_lum) if f < FIT0 else 1.0
    out = img.copy()
    if f <= F1:
        # --- main panel
        put_sign(out, img, expand(panel(f), 0.06, 0.05, 0.08), gain,     # slat block -> its red box
                 motion_blur(panel(f - 1).mean(0), panel(f + 1).mean(0)))
    # --- left-edge panel: paint the slats out with its own red
    if LEFT[0] <= f <= LEFT[1]:
        paint_out(out, (0, 300, 200, 720))
    # --- the far panels that follow round the dome: small, so an upright box is enough
    boxes = far.get(f, [])
    for x0, y0, x1, y1 in boxes:
        w, h = x1 - x0, y1 - y0
        nb = [far.get(f + d, boxes)[0] for d in (-1, 1)]
        put_sign(out, img, expand(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float), 0.1, 0.08, 0.12),
                 blur_px=motion_blur(centre(nb[0]), centre(nb[1])) * 0.8)
        paint_out(out, (x0 - 0.4 * w, y0 - 0.3 * h, x1 + 0.4 * w, y1 + 0.4 * h), 1.5)
    save(out, os.path.join(OUT, 'sg_%05d.png' % f))
    print('SIGN', f, 'gain %.2f' % gain, 'far', [tuple(int(v) for v in b) for b in boxes])
