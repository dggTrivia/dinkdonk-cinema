# Tracks the slatted N panels on the neon dome (source frames ~1388-1450) so sign_replace.py
# can put the DinkDonk sign on them. The slats are the only pale-yellow (hue 40-56) thing in
# these shots apart from thin neon rims; per frame we take the dense block of slat pixels in a
# window around the last position and read its four corners from extreme projections.
#
#   blender -b --factory-startup --python track_sign.py -- <frames_dir> <out.json>
# frames_dir holds gNNNNN.png at 1920x1080 (the original frames).
import bpy, sys, os, json
import numpy as np

A = sys.argv[sys.argv.index('--') + 1:]
FR, OUT = A[0], A[1]

def load(f):
    im = bpy.data.images.load(os.path.join(FR, 'g%05d.png' % f))
    w, h = im.size
    p = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]   # top row first
    bpy.data.images.remove(im)
    return p

def slat_mask(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1); d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = (mx - mn) / np.maximum(mx, 1e-6)
    return (hue >= 37) & (hue <= 57) & (s > 0.22) & (s < 0.85) & (mx > 0.45), mx

def block(m, x0, y0, x1, y1, col_frac=0.3, row_frac=0.25):
    """Dense slat block inside the window -> (corners tl,tr,br,bl, pixel count) or None."""
    h, w = m.shape
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    sub = m[y0:y1, x0:x1]
    if sub.sum() < 150: return None
    cols = sub.sum(0); keep_c = cols > col_frac * cols.max()
    xs = np.nonzero(keep_c)[0]
    # longest run of dense columns (drops the thin rim lines on either side)
    runs, start = [], xs[0]
    for a, b in zip(xs[:-1], xs[1:]):
        if b - a > 6: runs.append((start, a)); start = b
    runs.append((start, xs[-1]))
    cx0, cx1 = max(runs, key=lambda r: r[1] - r[0])
    sub2 = sub[:, cx0:cx1 + 1]
    wd = cx1 - cx0 + 1
    if wd < 6: return None
    # every slat row starts on the panel's straight left edge and ends on its right edge;
    # the neon rim arcs crossing the window don't, so the edges are the most common
    # first / last pixel of the well-filled rows, and slat rows are the rows that hit them
    cnt = sub2.sum(1)
    full = np.nonzero(cnt > 0.3 * wd)[0]
    if len(full) < 4: return None
    first = np.array([np.argmax(sub2[r]) for r in full])
    last = np.array([wd - 1 - np.argmax(sub2[r][::-1]) for r in full])
    tol = max(3, int(0.03 * wd))
    def mode(v):
        hist = np.bincount(v, minlength=wd)
        k = np.convolve(hist, np.ones(2 * tol + 1), 'same')
        return int(k.argmax())
    lx, rx = mode(first), mode(last)
    def span(rows):
        """Largest cluster of rows (gaps between slats allowed) -> (top, bottom)."""
        if len(rows) == 0: return None
        best, s0 = None, rows[0]
        for a, b in zip(list(rows[:-1]) + [rows[-1]], list(rows[1:]) + [rows[-1] + 10 ** 6]):
            if b - a > max(30, 0.25 * wd):
                if best is None or a - s0 > best[1] - best[0]: best = (s0, a)
                s0 = b
        return best
    lrows, rrows = full[np.abs(first - lx) <= tol], full[np.abs(last - rx) <= tol]
    Ls = span(lrows); Rs = span(rrows)
    if not Ls or not Rs: return None
    def pitch(rows, top):
        """Spacing of the slats (evenly spaced) from the first few slat tops below `top`;
        the thin bottom slats fade out as the panel recedes, the thick top ones don't."""
        rows = rows[rows >= top]
        if len(rows) < 3: return 0.0
        starts = rows[np.concatenate([[True], np.diff(rows) > 1])]
        d = np.diff(starts[:6])
        d = d[d > 2]
        return float(np.median(d)) if len(d) else 0.0
    X = lambda v: float(v + cx0 + x0); Y = lambda v: float(v + y0)
    quad = [(X(lx), Y(Ls[0])), (X(rx), Y(Rs[0])), (X(rx), Y(Rs[1])), (X(lx), Y(Ls[1]))]
    return quad, int(sub2.sum()), pitch(lrows, Ls[0]), pitch(rrows, Rs[0])

def track(frames, start_win, pad=70):
    out, win = {}, start_win
    for f in frames:
        m, _ = slat_mask(load(f))
        r = block(m, *win)
        if r:
            q, n, pl, pr = r
            out[f] = {'quad': [[round(float(a), 1), round(float(b), 1)] for a, b in q], 'n': n, 'pitch': [pl, pr]}
            xs = [p[0] for p in q]; ys = [p[1] for p in q]
            win = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    return out

main = track(range(1392, 1491), (700, 250, 1250, 760))
left = track(range(1392, 1432), (0, 250, 420, 640), pad=50)
json.dump({'main': main, 'left': left}, open(OUT, 'w'), indent=0)
for k, d in (('main', main), ('left', left)):
    for f in sorted(d): print('TRACK', k, f, d[f]['quad'], d[f]['pitch'])
