// [LAYOUT=cinema_layout_NN.json] [GAP=48] node band-slices.mjs <qa11 dir> [bandPx=64] [--dry]
// Cuts every depth slice (lit + dim, 1x + 2x) into horizontal bands trimmed to their visible pixels, so the
// browser decodes ~5 screens of pixels instead of the ~25 the slices' bounding boxes cover. Bands overlap their
// lower neighbour by OV rows holding only fully opaque pixels: drawn twice they are identical, and when the
// director zooms the extra rows cover the seam between two bands. Writes <name>_bNN(@2x).png next to the
// originals' folders (draft11_bands/, draft11_dim_bands/) and adds `pieces` to each slice in the layout JSON.
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync } from 'node:fs';
import { inflateSync, deflateSync, crc32 } from 'node:zlib';
import { join, dirname } from 'node:path';

const [dir, bandArg = '64', ...flags] = process.argv.slice(2);
const B = +bandArg;
const DRY = flags.includes('--dry');
const OV = 2;    // overlap rows (1x)
const GAP = +(process.env.GAP || 48);   // empty columns (1x) that split a band into separate pieces
const PAD = 1;   // transparent border (1x) so edge sampling matches the uncut slice

function readPng(file) {
  const b = readFileSync(file);
  let o = 8, w, h, idat = [];
  while (o < b.length) {
    const n = b.readUInt32BE(o), t = b.toString('ascii', o + 4, o + 8);
    if (t === 'IHDR') {
      w = b.readUInt32BE(o + 8); h = b.readUInt32BE(o + 12);
      if (b[o + 16] !== 8 || b[o + 17] !== 6 || b[o + 20] !== 0) throw new Error(`${file}: only RGBA8 non-interlaced`);
    }
    if (t === 'IDAT') idat.push(b.subarray(o + 8, o + 8 + n));
    o += 12 + n;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const px = Buffer.alloc(w * h * 4), s = w * 4;
  for (let y = 0; y < h; y++) {
    const f = raw[y * (s + 1)], r = y * (s + 1) + 1, d = y * s;
    for (let x = 0; x < s; x++) {
      const a = x >= 4 ? px[d + x - 4] : 0, u = y ? px[d - s + x] : 0, c = x >= 4 && y ? px[d - s + x - 4] : 0;
      let v = raw[r + x];
      if (f === 1) v += a; else if (f === 2) v += u; else if (f === 3) v += (a + u) >> 1;
      else if (f === 4) { const p = a + u - c, pa = Math.abs(p - a), pb = Math.abs(p - u), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? u : c; }
      px[d + x] = v & 255;
    }
  }
  return { w, h, px };
}
function chunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0); out.write(type, 4, 'ascii'); data.copy(out, 8);
  out.writeUInt32BE(crc32(Buffer.concat([Buffer.from(type, 'ascii'), data])), 8 + data.length);
  return out;
}
function writePng(file, { w, h, px }) {
  const s = w * 4, raw = Buffer.alloc(h * (s + 1)), row = Buffer.alloc(s);
  for (let y = 0; y < h; y++) {
    // per-row filter choice: the smallest sum of absolute residuals (the usual PNG heuristic)
    let best = null, bestSum = Infinity;
    for (let f = 0; f <= 4; f++) {
      let sum = 0;
      for (let x = 0; x < s; x++) {
        const i = y * s + x, a = x >= 4 ? px[i - 4] : 0, u = y ? px[i - s] : 0, c = x >= 4 && y ? px[i - s - 4] : 0;
        let p = 0;
        if (f === 1) p = a; else if (f === 2) p = u; else if (f === 3) p = (a + u) >> 1;
        else if (f === 4) { const q = a + u - c, pa = Math.abs(q - a), pb = Math.abs(q - u), pc = Math.abs(q - c); p = pa <= pb && pa <= pc ? a : pb <= pc ? u : c; }
        const v = (px[i] - p) & 255; row[x] = v; sum += v < 128 ? v : 256 - v;
      }
      if (sum < bestSum) { bestSum = sum; best = [f, Buffer.from(row)]; }
    }
    raw[y * (s + 1)] = best[0]; best[1].copy(raw, y * (s + 1) + 1);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6;
  writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr),
    chunk('sRGB', Buffer.from([0])), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
}
function crop(img, x, y, w, h, opaqueFromRow) {
  const out = Buffer.alloc(w * h * 4);
  for (let r = 0; r < h; r++) {
    img.px.copy(out, r * w * 4, ((y + r) * img.w + x) * 4, ((y + r) * img.w + x + w) * 4);
    if (r >= opaqueFromRow) for (let i = r * w * 4; i < (r + 1) * w * 4; i += 4) if (out[i + 3] !== 255) out.fill(0, i, i + 4);
  }
  return { w, h, px: out };
}
// composite pieces back (src-over at integer positions) and compare with the original slice
function rebuildMatches(img, pieces, scale) {
  const acc = Buffer.alloc(img.w * img.h * 4);
  for (const { rx, ry, p } of pieces) {
    for (let r = 0; r < p.h; r++) for (let c = 0; c < p.w; c++) {
      const s = (r * p.w + c) * 4, d = ((ry * scale + r) * img.w + rx * scale + c) * 4, a = p.px[s + 3];
      if (a === 255) p.px.copy(acc, d, s, s + 4);
      else if (a) { const k = 255 - a; for (let j = 0; j < 3; j++) acc[d + j] = Math.round((p.px[s + j] * a + acc[d + j] * acc[d + 3] * k / 255) / Math.max(1, a + acc[d + 3] * k / 255)); acc[d + 3] = Math.round(a + acc[d + 3] * k / 255); }
    }
  }
  for (let i = 0; i < acc.length; i += 4) {
    if (img.px[i + 3] !== acc[i + 3]) return `alpha differs at px ${i / 4}`;
    if (img.px[i + 3] && (img.px[i] !== acc[i] || img.px[i + 1] !== acc[i + 1] || img.px[i + 2] !== acc[i + 2])) return `rgb differs at px ${i / 4}`;
  }
  return null;
}

const layoutName = process.env.LAYOUT || 'cinema_layout_11.json';   // LAYOUT=cinema_layout_12.json for draft 12
const layoutFile = join(dir, layoutName);
const L = JSON.parse(readFileSync(layoutFile, 'utf8'));
const P = L.page_layers;
let before = 0, after = 0, count = 0;
const bad = [];
for (const [i, s] of P.slices.entries()) {
  const t = P.dim.slices[i];
  if (t.name !== s.name || t.x !== s.x || t.y !== s.y || t.w !== s.w || t.h !== s.h) throw new Error(`dim twin mismatch ${s.name}`);
  const imgs = [[readPng(join(dir, s.file)), 1], [readPng(join(dir, s.file_2x)), 2], [readPng(join(dir, t.file)), 1], [readPng(join(dir, t.file_2x)), 2]];
  for (const [im, k] of imgs) if (im.w !== s.w * k || im.h !== s.h * k) throw new Error(`${s.name}: size ${im.w}x${im.h} != ${s.w * k}x${s.h * k}`);
  // visible pixels at 1x: union of all four images (2x pixels folded onto their 1x pixel)
  const mask = new Uint8Array(s.w * s.h);
  for (const [im, k] of imgs) for (let y = 0; y < im.h; y++) for (let x = 0; x < im.w; x++) if (im.px[(y * im.w + x) * 4 + 3]) mask[Math.floor(y / k) * s.w + Math.floor(x / k)] = 1;
  before += s.w * s.h;
  const rects = [];
  for (let y0 = 0; y0 < s.h; y0 += B) {
    const yEnd = Math.min(s.h, y0 + B);           // rows this band owns
    const yExt = Math.min(s.h, yEnd + OV);        // + opaque-only overlap rows
    // columns in use across the band; runs closer than GAP are one piece (a gap costs less than another image)
    const col = new Uint8Array(s.w);
    for (let y = y0; y < yExt; y++) for (let x = 0; x < s.w; x++) if (mask[y * s.w + x]) col[x] = 1;
    const runs = [];
    for (let x = 0; x < s.w; x++) if (col[x]) {
      const last = runs.at(-1);
      if (last && x - last[1] <= GAP) last[1] = x; else runs.push([x, x]);
    }
    for (const [a, b] of runs) {
      let top = -1, bot = -1;
      for (let y = y0; y < yEnd; y++) for (let x = a; x <= b; x++) if (mask[y * s.w + x]) { if (top < 0) top = y; bot = y; break; }
      if (top < 0) continue;                      // only overlap rows here: the band below owns them
      // a top pad only over an empty row this band owns: the row above y0 belongs to the band above
      const x = Math.max(0, a - PAD), y = top > y0 ? top - PAD : top;
      const w = Math.min(s.w, b + 1 + PAD) - x, h = Math.min(s.h, Math.max(bot + 1 + PAD, yExt)) - y;
      rects.push({ x, y, w, h, opaqueFrom: yEnd - y });
    }
  }
  const pieces = [[], [], [], []];
  for (const [n, r] of rects.entries()) {
    after += r.w * r.h; count++;
    for (const [j, [im, k]] of imgs.entries()) pieces[j].push({ rx: r.x, ry: r.y, p: crop(im, r.x * k, r.y * k, r.w * k, r.h * k, r.opaqueFrom * k), n });
  }
  for (const [j, [im, k]] of imgs.entries()) { const e = rebuildMatches(im, pieces[j], k); if (e) bad.push(`${s.name} img${j}: ${e}`); }
  if (DRY) continue;
  const name = (f, n, two) => f.replace(/\/slices\//, '_bands/').replace(/(@2x)?\.png$/, `_b${String(n).padStart(2, '0')}${two ? '@2x' : ''}.png`);
  const meta = [[], []];
  for (const [j, [, k]] of imgs.entries()) {
    const src = j < 2 ? s : t;
    for (const { rx, ry, p, n } of pieces[j]) {
      const out = join(dir, name(k === 2 ? src.file_2x : src.file, n, k === 2));
      mkdirSync(dirname(out), { recursive: true });
      writePng(out, p);
      const m = meta[j < 2 ? 0 : 1];
      if (!m[n]) m[n] = { x: s.x + rx, y: s.y + ry, w: p.w / k, h: p.h / k };
      m[n][k === 2 ? 'file_2x' : 'file'] = name(k === 2 ? src.file_2x : src.file, n, k === 2);
    }
  }
  s.pieces = meta[0].filter(Boolean);
  t.pieces = meta[1].filter(Boolean);
  if (i % 20 === 0) console.log(`${i}/${P.slices.length} ${s.name}: ${rects.length} bands`);
}
console.log(`band ${B}px: ${(before / 1e6).toFixed(1)} -> ${(after / 1e6).toFixed(1)} Mpx at 1x (${(after / 2073600).toFixed(1)} screens), ${count} pieces per set`);
console.log(bad.length ? `REBUILD MISMATCH (${bad.length}):\n${bad.slice(0, 10).join('\n')}` : 'rebuild: every slice matches its pieces exactly');
if (!DRY && !bad.length) {
  const backup = join(dir, layoutName.replace(/.json$/, '.before-bands.json'));
  if (!existsSync(backup)) copyFileSync(layoutFile, backup);
  P.pieces_note = `slices cut into ${B}px bands trimmed to visible pixels (tools/band-slices.mjs); each slice's pieces replace its file/file_2x on the page`;
  writeFileSync(layoutFile, JSON.stringify(L, null, 2));
  console.log('layout updated, backup at', backup);
}
