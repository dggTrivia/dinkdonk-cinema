'use strict';

// Serves the standby screens on 127.0.0.1 and relays Destiny.gg's emote list
// and emote CSS, which cdn.destiny.gg only lets www.destiny.gg read.
// Chat itself comes from the DSA OBS overlay relay (127.0.0.1:18765).

const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const dinkdonk = require('./dinkdonk');

const HOST = '127.0.0.1';
const PORT = Number(process.env.STANDBY_PORT || 18770);
const ROOT = __dirname;
const CDN = 'https://cdn.destiny.gg';
const CACHE_MS = 10 * 60 * 1000;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.gif': 'image/gif',
  '.webm': 'video/webm',
  '.mp4': 'video/mp4',
};

const cache = new Map(); // key -> { at, type, body }

async function cdnAsset(key) {
  const hit = cache.get(key);
  if (hit && Date.now() - hit.at < CACHE_MS) return hit;

  const upstream = { 'emotes.json': '/emotes/emotes.json', 'emotes.css': '/emotes/emotes.css', 'flairs.json': '/flairs/flairs.json' }[key];
  try {
    const res = await fetch(CDN + upstream, { signal: AbortSignal.timeout(15_000) });
    if (!res.ok) throw new Error(`cdn.destiny.gg answered ${res.status}`);
    let body = await res.text();
    if (key === 'emotes.css') {
      // Relative image URLs would point at this server; make them absolute.
      body = body.replace(/url\(\s*["']?(?!https?:|data:)([^"')]+)["']?\s*\)/g,
        (_, file) => `url("${CDN}/emotes/${file}")`);
    }
    const entry = { at: Date.now(), type: TYPES[path.extname(key)], body };
    cache.set(key, entry);
    return entry;
  } catch (error) {
    console.error(`Emote ${key}: ${error.message}`);
    if (hit) return hit; // stale is better than nothing
    throw error;
  }
}

// Single emote images, same-origin, so a page can read their pixels (spotting square "picture" emotes
// that don't work as a chatter's body). Only cdn.destiny.gg emote files; kept in memory once fetched.
const EMOTE_IMG = /^https:\/\/cdn\.destiny\.gg\/[0-9.]+\/emotes\/[A-Za-z0-9_-]+\.(png|gif|webp|avif)$/;
const emoteImgs = new Map(); // url -> Promise<{ type, body }>
function emoteImage(u) {
  if (!emoteImgs.has(u)) {
    const p = fetch(u, { signal: AbortSignal.timeout(15_000) }).then(async (r) => {
      if (!r.ok) throw new Error(`cdn.destiny.gg answered ${r.status}`);
      return { type: TYPES[path.extname(u)], body: Buffer.from(await r.arrayBuffer()) };
    });
    p.catch(() => emoteImgs.delete(u));
    emoteImgs.set(u, p);
  }
  return emoteImgs.get(u);
}

function send(res, status, type, body) {
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(body);
}

// Read-only qBittorrent Web UI, with localhost authentication bypass enabled by the owner.
// Share in-flight work across OBS sources; old seeds must not start tonight's film.
let qbCache = null;
let qbPending = null;
// when each torrent was last seen downloading: qBittorrent can keep an old completion_on (a torrent finished,
// stopped and resumed days later), so a finish we watched happen counts as recent whatever that date says
const qbSeenDownloading = new Map();
async function qbProgress() {
  if (qbCache && Date.now() - qbCache.at < 2000) return qbCache.value;
  if (qbPending) return qbPending;
  qbPending = (async () => {
    let value = { available: false };
    try {
      const base = (process.env.QB_URL || 'http://127.0.0.1:8080').replace(/\/+$/, '');
      const r = await fetch(`${base}/api/v2/torrents/info?sort=added_on&reverse=true`, {
        signal: AbortSignal.timeout(1500), redirect: 'error', headers: { Accept: 'application/json' },
      });
      if (!r.ok) throw new Error('Web UI unavailable');
      const list = await r.json();
      if (!Array.isArray(list)) throw new Error('Web UI needs login');
      const downloading = new Set(['downloading', 'forcedDL', 'stalledDL', 'metaDL', 'forcedMetaDL', 'queuedDL', 'checkingDL']);
      const finished = new Set(['uploading', 'stalledUP', 'forcedUP', 'queuedUP', 'pausedUP', 'stoppedUP']);
      const recent = Date.now() / 1000 - 15 * 60;
      for (const t of list) if (t?.hash && downloading.has(t.state)) qbSeenDownloading.set(t.hash, Date.now() / 1000);
      for (const [hash, at] of qbSeenDownloading) if (at < recent) qbSeenDownloading.delete(hash);
      const t = list.filter((t) => t && typeof t.name === 'string' && Number.isFinite(t.progress) &&
        (downloading.has(t.state) || (t.progress >= 1 && finished.has(t.state) &&
          (t.completion_on >= recent || qbSeenDownloading.has(t.hash)))))
        .sort((a, b) => (b.added_on || 0) - (a.added_on || 0))[0];
      if (t) {
        const completed = t.progress >= 1 && finished.has(t.state);
        value = { available: true, name: t.name, progress: Math.max(0, Math.min(1, t.progress)),
          eta_s: completed ? 0 : (Number.isFinite(t.eta) && t.eta >= 0 && t.eta < 8640000 ? t.eta : null),
          state: t.state, completed };
      }
    } catch { /* offline, timeout or login: the pre-show still runs */ }
    qbCache = { at: Date.now(), value };
    return value;
  })();
  try { return await qbPending; } finally { qbPending = null; }
}

// Video loops (the lobby's rain/neon light loop) need byte ranges: Chrome streams and loops media with them.
function sendVideo(req, res, file, type) {
  fs.stat(file, (error, st) => {
    if (error || !st.isFile() || st.size === 0) { send(res, 404, 'text/plain', 'Not found'); return; }
    const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
    let start = 0;
    let end = st.size - 1;
    if (m) {
      start = m[1] ? Number(m[1]) : Math.max(0, st.size - Number(m[2]));
      end = m[1] && m[2] ? Math.min(Number(m[2]), st.size - 1) : st.size - 1;
      if (start > end || start >= st.size) {
        res.writeHead(416, { 'Content-Range': `bytes */${st.size}` });
        res.end();
        return;
      }
    }
    const head = { 'Content-Type': type, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1, 'Cache-Control': 'no-cache' };
    if (m) head['Content-Range'] = `bytes ${start}-${end}/${st.size}`;
    res.writeHead(m ? 206 : 200, head);
    if (req.method === 'HEAD') { res.end(); return; }
    // the player cancels requests all the time (seeking, looping): close the file with the response
    const stream = fs.createReadStream(file, { start, end });
    stream.on('error', () => res.destroy());
    res.on('close', () => stream.destroy());
    stream.pipe(res);
  });
}

// Control panel (control.html) <-> the screens: commands go to the selected scene as server-sent events;
// each screen posts its state (chatters, director) back so the panel can list them. 127.0.0.1 only.
const screens = new Map();          // open SSE response -> { page, id }; legacy connections are the lobby
const states = new Map();           // screen id -> { at, state }
const outputs = new Map();          // unified cinema.html instances
const presentationFile = path.join(ROOT, 'cache', `presentation-${PORT}.json`);
let activeView = 'lobby';
try {
  const saved = JSON.parse(fs.readFileSync(presentationFile, 'utf8'));
  if (['lobby', 'auditorium'].includes(saved.view)) activeView = saved.view;
} catch { /* first start: lobby */ }
function freshOutputs() {
  for (const [id, output] of outputs) if (Date.now() - output.at > 10000) outputs.delete(id);
  return [...outputs.values()].map(({ at, ...output }) => output);
}
function readJson(req, limit = 64 * 1024) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const parts = [];
    req.on('data', (c) => { size += c.length; if (size > limit) { reject(new Error('too large')); req.destroy(); } else parts.push(c); });
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(parts).toString('utf8') || '{}')); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}
async function controlRoute(req, res, pathname) {
  // only the panel and the screens themselves: other websites open in the browser must not drive the stream
  // (a JSON content type forces a CORS preflight, which this server never answers; foreign Origins are refused)
  const origin = req.headers.origin;
  if (origin && origin !== `http://${HOST}:${PORT}` && origin !== `http://localhost:${PORT}`) { send(res, 403, 'text/plain', 'Forbidden'); return true; }
  if (req.method === 'POST' && !/^application\/json\b/.test(req.headers['content-type'] || '')) { send(res, 415, 'text/plain', 'JSON only'); return true; }
  if (pathname === '/ctl/output' && req.method === 'POST') {
    const output = await readJson(req, 4096);
    if (!output || typeof output.id !== 'string' || !['lobby', 'auditorium'].includes(output.view)) {
      send(res, 400, TYPES['.json'], '{"error":"invalid cinema output"}'); return true;
    }
    outputs.set(output.id.slice(0, 32), { at: Date.now(), view: output.view, obs: output.obs === true });
    freshOutputs();
    send(res, 204, TYPES['.json'], ''); return true;
  }
  if (pathname === '/ctl/events' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
    res.write('retry: 3000\n\n');
    const params = new URL(req.url, `http://${HOST}:${PORT}`).searchParams;
    screens.set(res, { page: params.get('page') === 'auditorium' ? 'auditorium' : 'lobby', id: params.get('id') || '' });
    const ping = setInterval(() => res.write(': ping\n\n'), 20000);
    req.on('close', () => { clearInterval(ping); screens.delete(res); });
    return true;
  }
  if (pathname === '/ctl/cmd' && req.method === 'POST') {
    const cmd = await readJson(req);
    if (!cmd || typeof cmd.cmd !== 'string') { send(res, 400, TYPES['.json'], '{"error":"no cmd"}'); return true; }
    if (cmd.cmd === 'present') {
      if (!['lobby', 'auditorium'].includes(cmd.value)) {
        send(res, 400, TYPES['.json'], '{"error":"unknown cinema view"}'); return true;
      }
      // Persist before acknowledging, so a failed save never claims a switch succeeded.
      fs.mkdirSync(path.dirname(presentationFile), { recursive: true });
      fs.writeFileSync(presentationFile + '.tmp', JSON.stringify({ view: cmd.value }));
      fs.renameSync(presentationFile + '.tmp', presentationFile);
      activeView = cmd.value;
      send(res, 200, TYPES['.json'], JSON.stringify({ view: activeView })); return true;
    }
    const page = cmd.page || 'lobby';   // old panels keep controlling every lobby screen
    if (!['lobby', 'auditorium'].includes(page)) { send(res, 400, TYPES['.json'], '{"error":"unknown page"}'); return true; }
    const line = `data: ${JSON.stringify(cmd)}\n\n`;
    let count = 0;
    for (const [s, target] of screens) {
      if (target.page !== page || (cmd.id && cmd.id !== target.id)) continue;
      s.write(line);
      count++;
    }
    send(res, 200, TYPES['.json'], JSON.stringify({ screens: count }));
    return true;
  }
  if (pathname === '/ctl/state' && req.method === 'POST') {
    const st = await readJson(req, 256 * 1024);
    if (st && typeof st.id === 'string') states.set(st.id.slice(0, 16), { at: Date.now(), state: st });
    // closed screens drop out here too: with the panel closed, every scene reload left an entry (up to 256 KB)
    for (const [id, s] of states) if (Date.now() - s.at > 10000) states.delete(id);
    send(res, 204, 'text/plain', '');
    return true;
  }
  if (pathname === '/ctl/state' && req.method === 'GET') {
    for (const [id, s] of states) if (Date.now() - s.at > 10000) states.delete(id);   // closed screens drop out
    send(res, 200, TYPES['.json'], JSON.stringify({ controlVersion: 2,
      presentation: { version: 1, view: activeView, outputs: freshOutputs() },
      screens: [...states.values()].map((s) => ({ ...s.state, page: s.state.page || 'lobby' })) }));
    return true;
  }
  return false;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', `http://${HOST}:${PORT}`);
    if (url.pathname.startsWith('/ctl/') && await controlRoute(req, res, url.pathname)) return;
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      send(res, 405, 'text/plain', 'Method not allowed');
      return;
    }

    if (url.pathname === '/qb/progress') {
      send(res, 200, TYPES['.json'], JSON.stringify(await qbProgress()));
      return;
    }

    if (url.pathname === '/dgg/emote-img') {
      const u = url.searchParams.get('u') || '';
      if (!EMOTE_IMG.test(u)) { send(res, 400, 'text/plain', 'Not an emote image'); return; }
      const img = await emoteImage(u);
      send(res, 200, img.type, img.body);
      return;
    }
    if (url.pathname === '/dgg/emotes.json' || url.pathname === '/dgg/emotes.css' || url.pathname === '/dgg/flairs.json') {
      const asset = await cdnAsset(path.basename(url.pathname));
      send(res, 200, asset.type, asset.body);
      return;
    }

    if (url.pathname === '/dd/data.json') {
      send(res, 200, TYPES['.json'], JSON.stringify(await dinkdonk.data()));
      return;
    }
    if (url.pathname === '/dd/search') {
      const q = (url.searchParams.get('q') || '').trim().slice(0, 60);
      if (q.length < 2) { send(res, 400, TYPES['.json'], '{"error":"query too short"}'); return; }
      send(res, 200, TYPES['.json'], JSON.stringify(await dinkdonk.search(q)));
      return;
    }

    const rel = url.pathname === '/' ? 'index.html' : decodeURIComponent(url.pathname).replace(/^\/+/, '');
    const file = path.resolve(ROOT, rel);
    const type = TYPES[path.extname(file).toLowerCase()];
    // (case-insensitive: Windows serves /Standby-Server.js for standby-server.js; QA 05 Nov)
    const lower = file.toLowerCase();
    if (!file.startsWith(ROOT + path.sep) || !type || ['standby-server.js', 'dinkdonk.js', 'lan-proxy.js'].includes(path.basename(lower)) ||
        lower.startsWith(path.join(ROOT, 'cache').toLowerCase())) {
      send(res, 404, 'text/plain', 'Not found');
      return;
    }
    if (type.startsWith('video/')) { sendVideo(req, res, file, type); return; }
    fs.readFile(file, (error, body) => {
      if (error) send(res, 404, 'text/plain', 'Not found');
      else send(res, 200, type, body);
    });
  } catch (error) {
    send(res, 502, 'text/plain', error.message);
  }
});

server.on('error', (error) => {
  console.error(error.code === 'EADDRINUSE'
    ? `Port ${PORT} is already in use. Close the other standby server or set STANDBY_PORT.`
    : error);
  process.exitCode = 1;
});

server.listen(PORT, HOST, () => {
  console.log('Standby screens are running.');
  console.log(`Gallery:        http://${HOST}:${PORT}/`);
  console.log(`Browser Source: http://${HOST}:${PORT}/dinkdonk.html  (drafts: 01..05)`);
  console.log('Chat comes from the DSA overlay relay - keep that window open too.');
});
