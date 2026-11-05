'use strict';

// Which files the lobby (lobby.html) and the auditorium (auditorium.html) load at runtime, shared by the zip package
// (package/build.js) and the hosted edition (web/build.js). Returns paths relative to the standby folder.

const fs = require('node:fs');
const path = require('node:path');

const ART_EXT = /\.(png|webp|webm|jpg|avif|mp4|json)$/i;
const NOT_ART = /\.(md|txt|py|ps1|log)$/i;
const with2x = (rel) => { const m = rel.match(/^(.*)(\.[a-z0-9]+)$/i); return m ? [rel, `${m[1]}@2x${m[2]}`] : [rel]; };

function walkFiles(dir, base, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const a = path.join(dir, e.name);
    if (e.isDirectory()) walkFiles(a, base, out);
    else if (!NOT_ART.test(e.name)) out.push(path.relative(base, a).replace(/\\/g, '/'));
  }
}

function artFiles(standby, fail) {
  const files = [];
  // The lobby (roxy3d/out10 + out10mist) is read through manifests that list everything, so those folders go in whole.
  // auditorium.html also loads roxy3d/out10/ (ITEM_ART), already covered.
  for (const dir of ['out10', 'out10mist']) walkFiles(path.join(standby, 'roxy3d', dir), standby, files);

  // The auditorium (roxy3d/qa11, 2 GB of drafts) loads one draft: its layout JSON names every picture it needs.
  const aud = fs.readFileSync(path.join(standby, 'auditorium.html'), 'utf8');
  const draft = aud.match(/\? q\.get\('draft'\) : '(\d{2})'/)?.[1] || fail('default draft not found in auditorium.html');
  const audArt = aud.match(/const ART = '(roxy3d\/[^']+\/)';/)?.[1] || fail('ART folder not found in auditorium.html');
  const layoutRel = `cinema_layout_${draft}.json`;
  const wanted = new Set([layoutRel, ...with2x(`cinema_draft_${draft}.png`)]);
  (function walk(o) {
    if (typeof o === 'string') { if (ART_EXT.test(o) && !/^(roxy3d|qa\d+)\//.test(o)) with2x(o).forEach((r) => wanted.add(r)); }
    else if (o && typeof o === 'object') Object.values(o).forEach(walk);
  })(JSON.parse(fs.readFileSync(path.join(standby, audArt, layoutRel), 'utf8')));
  let audCount = 0;
  for (const rel of wanted) {
    // the @2x guesses and provenance-only names may not exist
    if (fs.existsSync(path.join(standby, audArt, rel))) { files.push(audArt + rel); audCount++; }
  }
  return { files, draft, audArt, audCount };
}

module.exports = { artFiles };
