'use strict';

// DinkDonk Cinema, hosted edition. Serves the lobby (lobby.html) and the auditorium (auditorium.html) to anyone with a
// room key, so streamers only need OBS: no Node, no relay, no bridge on their PC.
//   - one shared Destiny.gg chat connection, fanned out to every open screen (/__dgg_chat_ws?k=KEY)
//   - the emote list and dinkdonk.mov data, fetched once for everyone (/dgg/*, /dd/*)
//   - per-room control panel traffic (/ctl/*?k=KEY): each streamer drives only their own screens
//   - room keys: data/rooms.json, managed on /admin.html with ADMIN_TOKEN
// Pages get web/shim.js injected, which adds the key to those calls and runs the OBS film-screen bridge in the page.
// Runs behind Caddy (TLS); listens on 127.0.0.1 only. Env: PORT=8080, ADMIN_TOKEN (required), SITE=./site, DATA=./data

const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { WebSocket, WebSocketServer } = require('ws');

const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 8080);
const SITE = path.resolve(process.env.SITE || path.join(__dirname, 'site'));
const DATA = path.resolve(process.env.DATA || path.join(__dirname, 'data'));
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';
if (ADMIN_TOKEN.length < 24) { console.error('Set ADMIN_TOKEN (24+ characters).'); process.exit(1); }
process.env.DINKDONK_CACHE = process.env.DINKDONK_CACHE || path.join(DATA, 'dinkdonk.json');
// first start: film titles from the build's last good copy until dinkdonk.mov answers
const SEED = path.join(__dirname, 'seed', 'dinkdonk.json');
if (!fs.existsSync(process.env.DINKDONK_CACHE) && fs.existsSync(SEED)) {
  fs.mkdirSync(path.dirname(process.env.DINKDONK_CACHE), { recursive: true });
  fs.copyFileSync(SEED, process.env.DINKDONK_CACHE);
}
const dinkdonk = require(path.join(SITE, 'dinkdonk.js'));

const CDN = 'https://cdn.destiny.gg';
const CHAT_URL = 'wss://chat.destiny.gg/ws';
const CHAT_ORIGIN = 'https://www.destiny.gg';
const CACHE_MS = 10 * 60 * 1000;
const MAX_SCREENS_PER_ROOM = 24;
const log = (...a) => console.log(new Date().toISOString().slice(0, 19), ...a);

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.webp': 'image/webp', '.avif': 'image/avif', '.gif': 'image/gif', '.webm': 'video/webm', '.mp4': 'video/mp4',
  '.shader': 'text/plain; charset=utf-8', '.ico': 'image/x-icon',
};
// pages that need a room key; the shim goes into the ones that talk to the server
const KEYED = new Set(['lobby.html', 'roxy.html', 'auditorium.html', 'control.html', 'setup.html']);
const SHIMMED = new Set(['lobby.html', 'auditorium.html', 'control.html']);
const PRIVATE = /^(dinkdonk\.js|server\.js)$/i;

// ---------- rooms ----------
const ROOMS_FILE = path.join(DATA, 'rooms.json');
let rooms = {};
try { rooms = JSON.parse(fs.readFileSync(ROOMS_FILE, 'utf8')); } catch { rooms = {}; }
function saveRooms() {
  fs.mkdirSync(DATA, { recursive: true });
  fs.writeFileSync(`${ROOMS_FILE}.tmp`, JSON.stringify(rooms, null, 2));
  fs.renameSync(`${ROOMS_FILE}.tmp`, ROOMS_FILE);
}
const validKey = (k) => typeof k === 'string' && /^[A-Za-z0-9_-]{16,64}$/.test(k) && !!rooms[k] && !rooms[k].revoked;
const sameToken = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };

// per-room control state (same protocol as standby-server.js, one copy per key)
const live = new Map();   // key -> { screens: Map(res -> {page,id}), states: Map(id -> {at,state}), chat: Set(ws) }
function roomLive(k) {
  if (!live.has(k)) live.set(k, { screens: new Map(), states: new Map(), chat: new Set() });
  return live.get(k);
}

// ---------- helpers ----------
function send(res, status, type, body, extra = {}) {
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store', ...extra });
  res.end(body);
}
const json = (res, status, obj) => send(res, status, TYPES['.json'], JSON.stringify(obj));
function readJson(req, limit = 64 * 1024) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const parts = [];
    req.on('data', (c) => { size += c.length; if (size > limit) { reject(new Error('too large')); req.destroy(); } else parts.push(c); });
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(parts).toString('utf8') || '{}')); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}
// Requests that change things must come from our own pages (OBS browser sources send no Origin on same-origin GETs).
function foreignOrigin(req) {
  const o = req.headers.origin;
  if (!o) return false;
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  try { return new URL(o).host !== host; } catch { return true; }
}

// ---------- Destiny.gg: emotes (same as standby-server.js) ----------
const cdnCache = new Map();
async function cdnAsset(key) {
  const hit = cdnCache.get(key);
  if (hit && Date.now() - hit.at < CACHE_MS) return hit;
  const upstream = { 'emotes.json': '/emotes/emotes.json', 'emotes.css': '/emotes/emotes.css', 'flairs.json': '/flairs/flairs.json' }[key];
  try {
    const res = await fetch(CDN + upstream, { signal: AbortSignal.timeout(15_000) });
    if (!res.ok) throw new Error(`cdn.destiny.gg answered ${res.status}`);
    let body = await res.text();
    if (key === 'emotes.css') body = body.replace(/url\(\s*["']?(?!https?:|data:)([^"')]+)["']?\s*\)/g, (_, f) => `url("${CDN}/emotes/${f}")`);
    const entry = { at: Date.now(), type: TYPES[path.extname(key)], body };
    cdnCache.set(key, entry);
    return entry;
  } catch (error) {
    log(`emote ${key}: ${error.message}`);
    if (hit) return hit;
    throw error;
  }
}
const EMOTE_IMG = /^https:\/\/cdn\.destiny\.gg\/[0-9.]+\/emotes\/[A-Za-z0-9_-]+\.(png|gif|webp|avif)$/;
const emoteImgs = new Map();
function emoteImage(u) {
  if (!emoteImgs.has(u)) {
    if (emoteImgs.size > 4000) emoteImgs.clear();
    const p = fetch(u, { signal: AbortSignal.timeout(15_000) }).then(async (r) => {
      if (!r.ok) throw new Error(`cdn.destiny.gg answered ${r.status}`);
      return { type: TYPES[path.extname(u)], body: Buffer.from(await r.arrayBuffer()) };
    });
    p.catch(() => emoteImgs.delete(u));
    emoteImgs.set(u, p);
  }
  return emoteImgs.get(u);
}

// ---------- Destiny.gg chat: one upstream, every screen downstream ----------
// Read-only: screens never send. A screen joining later gets a NAMES frame built from the live user list, so its
// "n in chat" count is right without a second upstream connection.
const chat = { ws: null, users: new Map(), connectioncount: 0, retry: 0, idleTimer: null, clients: new Set() };
function chatConnect() {
  if (chat.ws) return;
  const ws = new WebSocket(CHAT_URL, { origin: CHAT_ORIGIN, handshakeTimeout: 15_000, headers: { 'User-Agent': 'DinkDonkCinema/1.0 (+read-only screens)' } });
  chat.ws = ws;
  ws.on('open', () => { chat.retry = 0; log(`chat: connected (${chat.clients.size} screens)`); });
  ws.on('message', (data) => {
    const text = data.toString();
    const sp = text.indexOf(' ');
    const type = sp > 0 ? text.slice(0, sp) : text;
    if (type === 'NAMES' || type === 'JOIN' || type === 'QUIT') {
      try {
        const d = JSON.parse(text.slice(sp + 1));
        if (type === 'NAMES') { chat.users = new Map((d.users || []).map((u) => [u.nick, u])); chat.connectioncount = d.connectioncount || 0; }
        else if (type === 'JOIN' && d.nick) chat.users.set(d.nick, d);
        else if (type === 'QUIT' && d.nick) chat.users.delete(d.nick);
      } catch { /* keep relaying */ }
    }
    for (const c of chat.clients) if (c.readyState === WebSocket.OPEN && c.bufferedAmount < 1 << 20) c.send(text);
  });
  const down = (why) => {
    if (chat.ws !== ws) return;
    chat.ws = null;
    chat.users.clear();
    log(`chat: closed (${why})`);
    // screens show "offline" and reconnect on their own; they come back once upstream is up again
    for (const c of chat.clients) c.close(1013, 'Destiny.gg chat reconnecting');
    if (chat.clients.size) setTimeout(chatConnect, Math.min(30_000, 1000 * 2 ** chat.retry++));
  };
  ws.on('close', (code) => down(`code ${code}`));
  ws.on('error', (e) => { down(e.message); try { ws.terminate(); } catch { /* gone */ } });
}
function namesFrame() {
  return `NAMES ${JSON.stringify({ connectioncount: Math.max(chat.connectioncount, chat.users.size), users: [...chat.users.values()] })}`;
}
const wss = new WebSocketServer({ noServer: true, maxPayload: 4096 });
wss.on('connection', (client, req, key) => {
  const room = roomLive(key);
  room.chat.add(client);
  chat.clients.add(client);
  clearTimeout(chat.idleTimer);
  if (chat.ws?.readyState === WebSocket.OPEN && chat.users.size) client.send(namesFrame());
  chatConnect();
  client.on('message', () => { /* screens are read-only */ });
  client.on('close', () => {
    room.chat.delete(client);
    chat.clients.delete(client);
    // nobody watching: drop the upstream after a minute (scene switches reconnect within seconds)
    if (!chat.clients.size) chat.idleTimer = setTimeout(() => { if (!chat.clients.size && chat.ws) { chat.ws.close(1000); } }, 60_000);
  });
});

// ---------- film-screen relay, per room (see web/shim.js) ----------
// For OBS builds whose browser may not reach 127.0.0.1 from a website: the auditorium (role=page) sends the screen
// corners here, the control panel in the streamer's own browser (role=obs) applies them in OBS and reports back
// whether OBS is linked. Same rules as obs-bridge.js: the newest page drives; when it goes, the film goes off.
const bridgeWss = new WebSocketServer({ noServer: true, maxPayload: 8192 });
function roomBridge(key) {
  const room = roomLive(key);
  if (!room.bridge) room.bridge = { host: null, ready: false, pages: new Set(), driver: null };
  return room.bridge;
}
const sendIfOpen = (ws, text) => { if (ws?.readyState === WebSocket.OPEN) ws.send(text); };
bridgeWss.on('connection', (ws, req, key, role) => {
  const b = roomBridge(key);
  const tellHost = () => sendIfOpen(b.host, JSON.stringify({ pages: b.pages.size }));
  if (role === 'obs') {
    if (b.host) b.host.close(4000, 'another control panel took over');
    b.host = ws;
    b.ready = false;
    tellHost();
    ws.on('message', (data) => {
      let m;
      try { m = JSON.parse(data.toString()); } catch { return; }
      if (typeof m.obs !== 'boolean') return;
      b.ready = m.obs;
      for (const p of b.pages) sendIfOpen(p, JSON.stringify({ obs: b.ready }));
    });
    ws.on('close', () => {
      if (b.host !== ws) return;
      b.host = null;
      b.ready = false;
      for (const p of b.pages) sendIfOpen(p, '{"obs":false}');
    });
    return;
  }
  b.pages.add(ws);
  b.driver = ws;
  sendIfOpen(ws, JSON.stringify({ obs: b.ready }));
  tellHost();
  ws.on('message', (data) => { if (ws === b.driver) sendIfOpen(b.host, data.toString()); });
  ws.on('close', () => {
    b.pages.delete(ws);
    if (b.driver === ws) {
      b.driver = [...b.pages].pop() || null;
      // the auditorium source shut down or reloaded: no film floating over the next scene
      sendIfOpen(b.host, '{"film":false}');
    }
    tellHost();
  });
});

// ---------- control panel, per room ----------
async function controlRoute(req, res, pathname, key) {
  if (foreignOrigin(req)) return send(res, 403, 'text/plain', 'Forbidden');
  if (req.method === 'POST' && !/^application\/json\b/.test(req.headers['content-type'] || '')) return send(res, 415, 'text/plain', 'JSON only');
  const room = roomLive(key);
  const url = new URL(req.url, 'http://x');
  if (pathname === '/ctl/events' && req.method === 'GET') {
    if (room.screens.size >= MAX_SCREENS_PER_ROOM) return send(res, 429, 'text/plain', 'Too many screens open');
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
    res.write('retry: 3000\n\n');
    room.screens.set(res, { page: url.searchParams.get('page') === 'auditorium' ? 'auditorium' : 'lobby', id: url.searchParams.get('id') || '' });
    const ping = setInterval(() => res.write(': ping\n\n'), 20000);
    req.on('close', () => { clearInterval(ping); room.screens.delete(res); });
    return;
  }
  if (pathname === '/ctl/cmd' && req.method === 'POST') {
    const cmd = await readJson(req);
    if (!cmd || typeof cmd.cmd !== 'string') return json(res, 400, { error: 'no cmd' });
    const page = cmd.page || 'lobby';
    if (!['lobby', 'auditorium'].includes(page)) return json(res, 400, { error: 'unknown page' });
    const line = `data: ${JSON.stringify(cmd)}\n\n`;
    let count = 0;
    for (const [s, target] of room.screens) {
      if (target.page !== page || (cmd.id && cmd.id !== target.id)) continue;
      s.write(line);
      count++;
    }
    return json(res, 200, { screens: count });
  }
  if (pathname === '/ctl/state' && req.method === 'POST') {
    const st = await readJson(req, 256 * 1024);
    if (st && typeof st.id === 'string' && (room.states.has(st.id.slice(0, 16)) || room.states.size < MAX_SCREENS_PER_ROOM)) {
      room.states.set(st.id.slice(0, 16), { at: Date.now(), state: st });
    }
    for (const [id, s] of room.states) if (Date.now() - s.at > 10000) room.states.delete(id);
    return send(res, 204, 'text/plain', '');
  }
  if (pathname === '/ctl/state' && req.method === 'GET') {
    for (const [id, s] of room.states) if (Date.now() - s.at > 10000) room.states.delete(id);
    return json(res, 200, { controlVersion: 2, screens: [...room.states.values()].map((s) => ({ ...s.state, page: s.state.page || 'lobby' })) });
  }
  return send(res, 404, 'text/plain', 'Not found');
}

// ---------- admin ----------
async function adminRoute(req, res, pathname) {
  const token = req.headers['x-admin-token'] || '';
  if (!sameToken(token, ADMIN_TOKEN)) return json(res, 403, { error: 'wrong admin token' });
  if (foreignOrigin(req)) return send(res, 403, 'text/plain', 'Forbidden');
  if (pathname === '/api/admin/rooms' && req.method === 'GET') {
    return json(res, 200, { rooms: Object.entries(rooms).map(([key, r]) => ({ key, ...r, screens: live.get(key)?.states.size || 0, chat: live.get(key)?.chat.size || 0 })) });
  }
  if (pathname === '/api/admin/rooms' && req.method === 'POST') {
    const body = await readJson(req);
    const name = String(body.name || '').trim().slice(0, 40);
    if (!name) return json(res, 400, { error: 'name needed' });
    const key = crypto.randomBytes(18).toString('base64url');
    rooms[key] = { name, created: new Date().toISOString() };
    saveRooms();
    log(`room created: ${name}`);
    return json(res, 200, { key, name });
  }
  if (pathname === '/api/admin/revoke' && req.method === 'POST') {
    const body = await readJson(req);
    if (!rooms[body.key]) return json(res, 404, { error: 'no such room' });
    rooms[body.key].revoked = new Date().toISOString();
    saveRooms();
    for (const c of live.get(body.key)?.chat || []) c.close(4003, 'room revoked');
    const b = live.get(body.key)?.bridge;
    if (b) { b.host?.close(4003, 'room revoked'); for (const p of b.pages) p.close(4003, 'room revoked'); }
    for (const s of live.get(body.key)?.screens.keys() || []) s.end();
    log(`room revoked: ${rooms[body.key].name}`);
    return json(res, 200, { ok: true });
  }
  return send(res, 404, 'text/plain', 'Not found');
}

// ---------- static files ----------
const SHIM_TAG = '<script src="/web/shim.js"></script>';
const htmlCache = new Map();   // file -> { mtime, body }
function sendStatic(req, res, file, rel) {
  fs.stat(file, (error, st) => {
    if (error || !st.isFile()) return send(res, 404, 'text/plain', 'Not found');
    const type = TYPES[path.extname(file).toLowerCase()];
    const base = path.basename(rel).toLowerCase();
    if (type.startsWith('text/html')) {
      let hit = htmlCache.get(file);
      if (!hit || hit.mtime !== st.mtimeMs) {
        let body = fs.readFileSync(file, 'utf8');
        // first thing in <head>, so the pages' own scripts already see the wrapped fetch/EventSource/WebSocket
        if (SHIMMED.has(base)) body = body.replace(/<head>/i, `<head>\n${SHIM_TAG}`);
        hit = { mtime: st.mtimeMs, body };
        htmlCache.set(file, hit);
      }
      return send(res, 200, type, hit.body, { 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff' });
    }
    const etag = `"${st.size.toString(36)}-${Math.floor(st.mtimeMs).toString(36)}"`;
    // art changes only on a redeploy: browsers revalidate daily, OBS keeps its copy between scene switches
    const cache = /^roxy3d\/|^assets\//.test(rel) ? 'public, max-age=86400' : 'no-cache';
    if (req.headers['if-none-match'] === etag) { res.writeHead(304, { ETag: etag, 'Cache-Control': cache }); return res.end(); }
    const head = { 'Content-Type': type, ETag: etag, 'Cache-Control': cache, 'Accept-Ranges': 'bytes', 'X-Content-Type-Options': 'nosniff' };
    let start = 0, end = st.size - 1;
    const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
    if (m) {
      start = m[1] ? Number(m[1]) : Math.max(0, st.size - Number(m[2]));
      end = m[1] && m[2] ? Math.min(Number(m[2]), st.size - 1) : st.size - 1;
      if (start > end || start >= st.size) { res.writeHead(416, { 'Content-Range': `bytes */${st.size}` }); return res.end(); }
      head['Content-Range'] = `bytes ${start}-${end}/${st.size}`;
    }
    head['Content-Length'] = end - start + 1;
    res.writeHead(m ? 206 : 200, head);
    if (req.method === 'HEAD') return res.end();
    const stream = fs.createReadStream(file, { start, end });
    stream.on('error', () => res.destroy());
    res.on('close', () => stream.destroy());
    stream.pipe(res);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', 'http://x');
    const pathname = url.pathname;
    const key = url.searchParams.get('k') || '';

    if (pathname === '/healthz') return json(res, 200, { ok: true, chat: chat.ws?.readyState === WebSocket.OPEN, screens: chat.clients.size });
    if (pathname.startsWith('/api/admin/')) return await adminRoute(req, res, pathname);
    if (pathname === '/api/room') return validKey(key) ? json(res, 200, { name: rooms[key].name }) : json(res, 403, { error: 'unknown or revoked key' });
    if (pathname.startsWith('/ctl/')) return validKey(key) ? await controlRoute(req, res, pathname, key) : send(res, 403, 'text/plain', 'Room key needed');

    if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'text/plain', 'Method not allowed');
    // the qBittorrent download bar needs the streamer's own PC; hosted, the pre-show just runs without it
    if (pathname === '/qb/progress') return json(res, 200, { available: false });
    if (pathname === '/dgg/emote-img') {
      const u = url.searchParams.get('u') || '';
      if (!EMOTE_IMG.test(u)) return send(res, 400, 'text/plain', 'Not an emote image');
      const img = await emoteImage(u);
      return send(res, 200, img.type, img.body, { 'Cache-Control': 'public, max-age=86400' });
    }
    if (['/dgg/emotes.json', '/dgg/emotes.css', '/dgg/flairs.json'].includes(pathname)) {
      const a = await cdnAsset(path.basename(pathname));
      return send(res, 200, a.type, a.body);
    }
    if (pathname === '/dd/data.json') return json(res, 200, await dinkdonk.data());
    if (pathname === '/dd/search') {
      const q = (url.searchParams.get('q') || '').trim().slice(0, 60);
      if (q.length < 2) return json(res, 400, { error: 'query too short' });
      return json(res, 200, await dinkdonk.search(q));
    }

    const rel = pathname === '/' ? 'index.html' : decodeURIComponent(pathname).replace(/^\/+/, '');
    const file = path.resolve(SITE, rel);
    const type = TYPES[path.extname(file).toLowerCase()];
    if (!file.startsWith(SITE + path.sep) || !type || PRIVATE.test(path.basename(file)) || /(^|[\\/])\./.test(rel)) return send(res, 404, 'text/plain', 'Not found');
    if (KEYED.has(path.basename(file).toLowerCase()) && !validKey(key)) {
      return send(res, 403, TYPES['.html'], '<!doctype html><meta charset="utf-8"><title>DinkDonk Cinema</title><body style="background:#111;color:#ddd;font:16px system-ui;padding:40px">This link needs a valid room key. Ask for an invite link.</body>');
    }
    return sendStatic(req, res, file, rel.replace(/\\/g, '/'));
  } catch (error) {
    log(`error ${req.url}: ${error.message}`);
    if (!res.headersSent) send(res, 502, 'text/plain', 'Upstream unavailable');
    else res.destroy();
  }
});

server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url || '/', 'http://x');
  const key = url.searchParams.get('k') || '';
  if (!validKey(key) || foreignOrigin(req)) { socket.end('HTTP/1.1 403 Forbidden\r\n\r\n'); return; }
  if (url.pathname === '/__bridge') {
    const role = url.searchParams.get('role') === 'obs' ? 'obs' : 'page';
    if (role === 'page' && roomBridge(key).pages.size >= MAX_SCREENS_PER_ROOM) { socket.end('HTTP/1.1 429 Too Many Requests\r\n\r\n'); return; }
    bridgeWss.handleUpgrade(req, socket, head, (ws) => bridgeWss.emit('connection', ws, req, key, role));
    return;
  }
  if (url.pathname !== '/__dgg_chat_ws') { socket.end('HTTP/1.1 404 Not Found\r\n\r\n'); return; }
  if (roomLive(key).chat.size >= MAX_SCREENS_PER_ROOM) { socket.end('HTTP/1.1 429 Too Many Requests\r\n\r\n'); return; }
  wss.handleUpgrade(req, socket, head, (ws) => wss.emit('connection', ws, req, key));
});

server.listen(PORT, HOST, () => log(`DinkDonk Cinema on http://${HOST}:${PORT} (${Object.keys(rooms).length} rooms, site ${SITE})`));
