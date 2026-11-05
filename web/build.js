'use strict';

// Builds the hosted edition into ..\..\dist\web\ (next to the zip package): server.js + ws, and site\ with the lobby
// and auditorium pages, only the art they load (package/art.js), the shim, setup/admin pages and the corner-pin shader.
// The live files are only read. Deploy with web/deploy/deploy.sh.
// Usage: node web/build.js [--out <folder>]

const fs = require('node:fs');
const path = require('node:path');
const { artFiles } = require('../package/art');

const WEB = __dirname;
const STANDBY = path.resolve(WEB, '..');
const SHADER = 'C:/Program Files/obs-studio/data/obs-plugins/obs-shaderfilter/examples/corner-pin.shader';
const args = process.argv.slice(2);
const OUT = path.resolve(args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(STANDBY, '..', 'dist', 'web'));
const SITE = path.join(OUT, 'site');

const fail = (msg) => { console.error(`build failed: ${msg}`); process.exit(1); };
let bytes = 0;
function copy(from, to) {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
  bytes += fs.statSync(to).size;
}
function copyTree(from, to) {
  for (const e of fs.readdirSync(from, { withFileTypes: true })) {
    if (e.isDirectory()) copyTree(path.join(from, e.name), path.join(to, e.name));
    else copy(path.join(from, e.name), path.join(to, e.name));
  }
}
// A text edit that must apply exactly `times` times, so a changed source fails the build instead of shipping unpatched.
function patch(file, from, to, times = 1) {
  const s = fs.readFileSync(file, 'utf8');
  if (s.split(from).length !== times + 1) fail(`patch target not found ${times}x in ${path.relative(OUT, file)}: ${from}`);
  fs.writeFileSync(file, s.split(from).join(to));
}

if (fs.existsSync(OUT)) {
  if (!fs.existsSync(path.join(OUT, 'server.js'))) fail(`${OUT} exists and does not look like an earlier build; not touching it`);
  fs.rmSync(OUT, { recursive: true, force: true });
}

// server
for (const f of ['server.js', 'package.json']) copy(path.join(WEB, f), path.join(OUT, f));
copyTree(path.join(WEB, 'node_modules'), path.join(OUT, 'node_modules'));
copyTree(path.join(WEB, 'deploy'), path.join(OUT, 'deploy'));
// they run on Linux: no CRLF from a Windows checkout
for (const f of fs.readdirSync(path.join(OUT, 'deploy'))) {
  const p = path.join(OUT, 'deploy', f);
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replace(/\r\n/g, '\n'));
}
if (fs.existsSync(path.join(STANDBY, 'cache', 'dinkdonk.json'))) copy(path.join(STANDBY, 'cache', 'dinkdonk.json'), path.join(OUT, 'seed', 'dinkdonk.json'));

// pages (unchanged; the server injects web/shim.js into them)
// roxy.html is the redirect stub left by the lobby's rename to lobby.html (05 Nov), for old URLs
for (const f of ['lobby.html', 'roxy.html', 'auditorium.html', 'control.html', 'dinkdonk.js']) copy(path.join(STANDBY, f), path.join(SITE, f));
copyTree(path.join(STANDBY, 'shared'), path.join(SITE, 'shared'));
copyTree(path.join(STANDBY, 'assets'), path.join(SITE, 'assets'));
for (const f of ['index.html', 'setup.html', 'admin.html']) copy(path.join(WEB, f), path.join(SITE, f));
copy(path.join(WEB, 'shim.js'), path.join(SITE, 'web', 'shim.js'));
copy(SHADER, path.join(SITE, 'web', 'corner-pin.shader'));

// the server keeps dinkdonk.mov's cache in its data folder, outside the served site
patch(path.join(SITE, 'dinkdonk.js'), "const CACHE_FILE = path.join(__dirname, 'cache', 'dinkdonk.json');",
  "const CACHE_FILE = process.env.DINKDONK_CACHE || path.join(__dirname, 'cache', 'dinkdonk.json');");
patch(path.join(SITE, 'control.html'), 'The standby server is not reachable (start-standby.bat).', 'The cinema server is not reachable, or this room key is no longer valid.', 2);

// art
const art = artFiles(STANDBY, fail);
for (const rel of art.files) copy(path.join(STANDBY, rel), path.join(SITE, rel));
console.log(`auditorium draft ${art.draft}: ${art.audCount} files from ${art.audArt}`);
console.log(`web build: ${OUT} (${(bytes / 1048576).toFixed(0)} MB)`);
