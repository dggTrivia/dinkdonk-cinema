'use strict';

// Builds the shareable "DinkDonk Cinema" package: the lobby (lobby.html) and the auditorium (auditorium.html) with only
// the art they load, the standby server, the OBS film-screen bridge, the DSA chat relay, ready-to-import OBS scene
// collections (1080p / 1440p / 2160p) and one START.bat. The live files here are only read, never changed.
// Usage: node package/build.js [--out <folder>] [--no-zip]
// Output: ..\dist\DinkDonk-Cinema\ and ..\dist\DinkDonk-Cinema.zip (next to the standby folder's parent).

const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { artFiles } = require('./art');

const STANDBY = path.resolve(__dirname, '..');
const RELAY = path.join(process.env.USERPROFILE || '', 'Desktop', 'customchat', 'destinygg-obs-overlay');
const OBS_SCENES = path.join(process.env.APPDATA || '', 'obs-studio', 'basic', 'scenes', 'Moobies_1440p_poll.json');

const args = process.argv.slice(2);
const OUT = path.resolve(args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(STANDBY, '..', 'dist', 'DinkDonk-Cinema'));
const SCREENS = path.join(OUT, 'screens');

const log = (...a) => console.log(...a);
const fail = (msg) => { console.error(`build failed: ${msg}`); process.exit(1); };
let bytes = 0;

function copy(from, to) {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
  bytes += fs.statSync(to).size;
}
function copyTree(from, to, skip = () => false) {
  for (const e of fs.readdirSync(from, { withFileTypes: true })) {
    const a = path.join(from, e.name), b = path.join(to, e.name);
    if (skip(a, e)) continue;
    if (e.isDirectory()) copyTree(a, b, skip);
    else copy(a, b);
  }
}
// A text edit that must apply exactly once, so a changed source fails the build instead of shipping unpatched.
function patch(file, from, to) {
  const s = fs.readFileSync(file, 'utf8');
  if (s.split(from).length !== 2) fail(`patch target not found once in ${path.relative(OUT, file)}: ${from}`);
  fs.writeFileSync(file, s.replace(from, to));
}

// ---------- 0. clean ----------
if (fs.existsSync(OUT)) {
  if (!fs.existsSync(path.join(OUT, 'START.bat'))) fail(`${OUT} exists and does not look like an earlier build; not touching it`);
  fs.rmSync(OUT, { recursive: true, force: true });
}
fs.mkdirSync(SCREENS, { recursive: true });

// ---------- 1. pages, server, bridge ----------
for (const f of ['lobby.html', 'auditorium.html', 'control.html', 'standby-server.js', 'dinkdonk.js', 'obs-bridge.js', 'bridge-sizing.js', 'bridge-captures.js', 'cinema-screen.shader', 'lan-proxy.js']) {
  copy(path.join(STANDBY, f), path.join(SCREENS, f));
}
copyTree(path.join(STANDBY, 'shared'), path.join(SCREENS, 'shared'));
copyTree(path.join(STANDBY, 'assets'), path.join(SCREENS, 'assets'));
// last good dinkdonk.mov data, so the screens have film titles before the first refresh
if (fs.existsSync(path.join(STANDBY, 'cache', 'dinkdonk.json'))) copy(path.join(STANDBY, 'cache', 'dinkdonk.json'), path.join(SCREENS, 'cache', 'dinkdonk.json'));
fs.writeFileSync(path.join(SCREENS, 'index.html'),
  '<!doctype html><meta charset="utf-8"><title>DinkDonk Cinema</title><meta http-equiv="refresh" content="0; url=control.html">\n');

// The bridge uses cinema-screen.shader beside its script, included above.

// ---------- 2. art: only what the two pages load ----------
const art = artFiles(STANDBY, fail);
for (const rel of art.files) copy(path.join(STANDBY, rel), path.join(SCREENS, rel));
log(`auditorium draft ${art.draft}: ${art.audCount} files from ${art.audArt}`);

// ---------- 3. chat relay (DSA OBS overlay) ----------
if (!fs.existsSync(path.join(RELAY, 'server.js'))) fail(`chat relay not found at ${RELAY}`);
copyTree(RELAY, path.join(OUT, 'chat-relay'), (a, e) => /tests?\.c?js$/i.test(e.name) || e.name === 'start-unix.sh');

// ---------- 4. OBS scene collections ----------
// From the live collection: the two cinema scenes and the lobby/film sub-scenes, with their sources. Everything else
// (the movie scene, audio devices, scripts, projectors, filters) stays out; the bridge creates the corner-pin filter.
const live = JSON.parse(fs.readFileSync(OBS_SCENES, 'utf8'));
const byName = Object.fromEntries(live.sources.map((s) => [s.name, s]));
const SCENES = ['DinkDonk Cinema', 'Lobby + Poll setup', 'Lobby (src)', 'Film screen (src)'];
const DROP = new Set(['Poll setup label']);   // a scratch text label ("testing")
for (const n of SCENES) if (!byName[n]) fail(`scene "${n}" missing from ${OBS_SCENES}`);
const W0 = live.resolution?.x || 2560;

function collection(w, h) {
  const f = w / W0, keep = new Set(SCENES), sources = [];
  for (const n of SCENES) for (const it of byName[n].settings.items) if (!DROP.has(it.name)) keep.add(it.name);
  for (const n of keep) {
    const s = structuredClone(byName[n]);
    s.filters = [];
    delete s.hotkeys;
    if (s.id === 'scene') {
      s.settings.items = s.settings.items.filter((it) => !DROP.has(it.name)).map((it) => {
        it.pos = { x: Math.round(it.pos.x * f), y: Math.round(it.pos.y * f) };
        if (it.bounds_type) it.bounds = { x: Math.round(it.bounds.x * f), y: Math.round(it.bounds.y * f) };
        else if (it.name === 'Poll builder') it.scale = { x: it.scale.x * f, y: it.scale.y * f };   // keep the site's own layout width
        for (const k of ['crop_left', 'crop_top', 'crop_right', 'crop_bottom']) if (it[k]) it[k] = Math.round(it[k] * f);
        return it;
      });
    }
    if (s.id === 'browser_source' && /^http:\/\/127\.0\.0\.1:18770\//.test(s.settings.url)) {
      s.settings.url = s.settings.url.replace('/roxy.html', '/lobby.html');   // renamed 05 Nov; the package has no redirect stub
      s.settings.width = Math.round(s.settings.width * f);
      s.settings.height = Math.round(s.settings.height * f);
    }
    if (s.id === 'game_capture') {
      // any VLC window, whatever skin or film title (the live setup matches the skinned window by class)
      s.settings.window = 'VLC media player:Qt5QWindowIcon:vlc.exe';
      s.settings.priority = 2;
    }
    sources.push(s);
  }
  return {
    name: `DinkDonk Cinema ${h}p`, sources, groups: [],
    scene_order: SCENES.map((name) => ({ name })),
    current_scene: 'DinkDonk Cinema', current_program_scene: 'DinkDonk Cinema',
    current_transition: 'Fade', transition_duration: 300, transitions: [], quick_transitions: [], saved_projectors: [],
    preview_locked: false, scaling_enabled: false, modules: {}, resolution: { x: w, y: h }, version: live.version,
  };
}
for (const [w, h] of [[1920, 1080], [2560, 1440], [3840, 2160]]) {
  fs.writeFileSync(path.join(OUT, 'obs', `DinkDonk Cinema ${h}p.json`), JSON.stringify(collection(w, h), null, 2));
}

// ---------- 5. launcher + readme ----------
copy(path.join(__dirname, 'START.bat'), path.join(OUT, 'START.bat'));
copy(path.join(__dirname, 'README.txt'), path.join(OUT, 'README.txt'));

log(`package: ${OUT} (${(bytes / 1048576).toFixed(0)} MB)`);

// ---------- 6. zip ----------
if (!args.includes('--no-zip')) {
  const zip = `${OUT}.zip`;
  fs.rmSync(zip, { force: true });
  // Windows' own bsdtar writes real zips; a Git Bash tar earlier on PATH would write a tar named .zip
  const tar = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe');
  execFileSync(tar, ['-a', '-c', '-f', zip, '-C', path.dirname(OUT), path.basename(OUT)], { stdio: 'inherit' });
  log(`zip: ${zip} (${(fs.statSync(zip).size / 1048576).toFixed(0)} MB)`);
}
