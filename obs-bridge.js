'use strict';

// OBS bridge for the auditorium's film screen. The auditorium page inside OBS (Browser 3) sends where the screen is
// on every camera move; both capture shaders follow it, and OBS visibility selects the capture shown
// only while the phase is Film. Capture bounding boxes track changing window sizes.
//
// Page -> bridge (WebSocket on PORT, text frames of JSON):
//   { film: true|false, w: <viewport px>, h: <viewport px>, quad: [[x,y] TL, TR, BR, BL] }   (viewport px)
// Bridge -> page: { obs: true|false } whenever OBS becomes ready / goes away (the page keeps the screen green
//   when false, so a missing bridge never leaves a black screen with no film).
// The OBS password is read from obs-websocket's own config on this PC; it never goes to the page.
// Usage: node obs-bridge.js   (env: OBS_BRIDGE_PORT=18790, OBS_WS=ws://127.0.0.1:4455, OBS_PASSWORD to override)

const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { fitCapture } = require('./bridge-sizing');
const { createCaptures } = require('./bridge-captures');

const PORT = Number(process.env.OBS_BRIDGE_PORT || 18790);
const OBS_URL = process.env.OBS_WS || 'ws://127.0.0.1:4455';
const SCENE = 'dggCINEMAtheatre';
const CAPTURES = ['firefoxBrowserCinema', 'mpvCinema'];
const FILTER = 'Corner pin (live)';
const SHADER = path.join(__dirname, 'cinema-screen.shader');
const OBS_CONFIG = path.join(process.env.APPDATA || '', 'obs-studio', 'plugin_config', 'obs-websocket', 'config.json');
const log = (...a) => console.log(new Date().toTimeString().slice(0, 8), ...a);

// ---------- OBS side (obs-websocket v5) ----------
const obs = { ws: null, ready: false, pending: new Map(), seq: 0, setupAt: 0 };

function obsPassword() {
  if (process.env.OBS_PASSWORD) return process.env.OBS_PASSWORD;
  try { return JSON.parse(fs.readFileSync(OBS_CONFIG, 'utf8')).server_password || ''; } catch { return ''; }
}
const sha256b64 = (s) => crypto.createHash('sha256').update(s).digest('base64');

function obsConnect() {
  let ws;
  try { ws = new WebSocket(OBS_URL, 'obswebsocket.json'); } catch (e) { log('OBS:', e.message); return setTimeout(obsConnect, 3000); }
  obs.ws = ws;
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.op === 0) {   // Hello
      const a = m.d.authentication;
      const identify = { rpcVersion: 1, eventSubscriptions: 138 };   // Config + inputs + scene item visibility
      if (a) identify.authentication = sha256b64(sha256b64(obsPassword() + a.salt) + a.challenge);
      ws.send(JSON.stringify({ op: 1, d: identify }));
    } else if (m.op === 2) {   // Identified
      log('OBS connected');
      setup();
    } else if (m.op === 5 && m.d.eventType === 'CurrentSceneCollectionChanged') {
      setReady(false);
      setup();
    } else if (m.op === 5 && m.d.eventType === 'SceneItemEnableStateChanged') {
      if (captures.visibility(m.d.eventData)) pump();
    } else if (m.op === 5 && ['SceneItemCreated', 'SceneItemRemoved'].includes(m.d.eventType)
        && m.d.eventData.sceneName === SCENE) {
      setReady(false);
      setup();
    } else if (m.op === 5 && m.d.eventType === 'InputNameChanged'
        && (CAPTURES.includes(m.d.eventData.inputName) || CAPTURES.includes(m.d.eventData.oldInputName))) {
      setReady(false);
      setup();
    } else if (m.op === 7) {   // RequestResponse
      const p = obs.pending.get(m.d.requestId);
      if (!p) return;
      obs.pending.delete(m.d.requestId);
      if (m.d.requestStatus.result) p.resolve(m.d.responseData || {});
      else p.reject(new Error(`${m.d.requestType}: ${m.d.requestStatus.comment || m.d.requestStatus.code}`));
    }
  };
  ws.onclose = (ev) => {
    if (obs.ws !== ws) return;
    // 4009 = wrong password: say so instead of retrying silently forever
    log(ev.code === 4009 ? 'OBS refused the password (Tools > WebSocket Server Settings)' : `OBS not reachable at ${OBS_URL}, retrying`);
    obs.ws = null;
    setReady(false);
    for (const p of obs.pending.values()) p.reject(new Error('OBS closed'));
    obs.pending.clear();
    setTimeout(obsConnect, 3000);
  };
  ws.onerror = () => {};
}

function request(requestType, requestData = {}) {
  return new Promise((resolve, reject) => {
    if (!obs.ws || obs.ws.readyState !== WebSocket.OPEN) return reject(new Error('OBS not connected'));
    const requestId = String(++obs.seq);
    obs.pending.set(requestId, { resolve, reject });
    obs.ws.send(JSON.stringify({ op: 6, d: { requestType, requestId, requestData } }));
  });
}

// Configure every available screen capture; OBS eye icons choose which one is shown.
let settingUp = false, setupAgain = false;
async function setup() {
  if (settingUp) { setupAgain = true; return; }
  settingUp = true;
  obs.setupAt = Date.now();
  try {
    const { sceneItems } = await request('GetSceneItemList', { sceneName: SCENE });
    const items = sceneItems.filter(item => CAPTURES.includes(item.sourceName));
    if (!items.length) throw new Error(`Add ${CAPTURES.join(' or ')} to ${SCENE}`);
    for (const item of items) {
      const sourceName = item.sourceName;
      await fitCapture(request, SCENE, sourceName);
      const { filters } = await request('GetSourceFilterList', { sourceName });
      if (!filters.some(f => f.filterName === FILTER)) {
        await request('CreateSourceFilter', { sourceName, filterName: FILTER, filterKind: 'shader_filter',
          filterSettings: { from_file: true, shader_file_name: SHADER, Antialias_Edges: true } });
      }
      for (const filter of filters) {
        if (filter.filterName !== FILTER && filter.filterEnabled && /corner pin/i.test(filter.filterName)) {
          await request('SetSourceFilterEnabled', { sourceName, filterName: filter.filterName, filterEnabled: false });
        }
      }
      await request('SetSourceFilterSettings', { sourceName, filterName: FILTER,
        filterSettings: { from_file: true, shader_file_name: SHADER, Cinema_Visible: false }, overlay: true });
      await request('SetSourceFilterEnabled', { sourceName, filterName: FILTER, filterEnabled: true });
    }
    captures.configure(items);
    setReady(true);
    log(`ready: ${items.map(i => i.sourceName).join(', ')} in ${SCENE}; choose with OBS eye icons`);
    log(`screen source: ${captures.selected() || 'none (enable one in OBS)'}`);
    pump();
  } catch (error) {
    setReady(false);
    log(`not ready (${error.message})`);
  } finally {
    settingUp = false;
    if (setupAgain) { setupAgain = false; setup(); }
  }
}

function setReady(on) {
  if (obs.ready === on) return;
  obs.ready = on;
  for (const c of pages) wsSend(c, { obs: on });
}

// ---------- page side: a minimal WebSocket server (text frames only) ----------
const pages = new Set();
let driver = null;   // the page whose corners we follow: the latest one to connect
const want = { film: false, quad: null, active: false };
const captures = createCaptures({ request, sceneName: SCENE, filterName: FILTER, log });
let busy = false, pumpAgain = false;

const ownAddresses = () => new Set(['127.0.0.1', '::1', ...Object.values(os.networkInterfaces()).flat().map((i) => i.address)]);

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end(`obs-bridge: OBS ${obs.ready ? 'ready' : 'not ready'}, ${pages.size} page(s), film ${want.film ? 'on' : 'off'}, selected ${captures.selected() || 'none'}\n`);
});

server.on('upgrade', (req, socket) => {
  // only pages on this PC (OBS's own browser source): a phone on the LAN must not switch the film on and off
  const from = (socket.remoteAddress || '').replace(/^::ffff:/, '');
  const key = req.headers['sec-websocket-key'];
  if (!ownAddresses().has(from) || !key) { socket.end('HTTP/1.1 403 Forbidden\r\n\r\n'); return; }
  const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
  socket.write(`HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ${accept}\r\n\r\n`);
  socket.setNoDelay(true);
  pages.add(socket);
  driver = socket;
  wsSend(socket, { obs: obs.ready });
  log(`page connected (${pages.size} open)`);
  let buf = Buffer.alloc(0);
  socket.on('data', (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    for (;;) {
      const f = readFrame(buf);
      if (!f) break;
      buf = buf.subarray(f.size);
      if (f.op === 1 && socket === driver) onPage(f.data.toString('utf8'));
      else if (f.op === 8) { socket.end(Buffer.from([0x88, 0])); break; }
      else if (f.op === 9) socket.write(frame(f.data, 0xA));
    }
  });
  const gone = () => {
    if (!pages.delete(socket)) return;
    log(`page closed (${pages.size} open)`);
    if (socket !== driver) return;
    // the auditorium source shut down (scene switched away) or reloaded: no film floating over the next page
    driver = [...pages].pop() || null;
    want.film = false;
    pump();
  };
  socket.on('close', gone);
  socket.on('error', gone);
});

function readFrame(b) {
  if (b.length < 2) return null;
  const op = b[0] & 0x0f, masked = b[1] & 0x80;
  let len = b[1] & 0x7f, at = 2;
  if (len === 126) { if (b.length < 4) return null; len = b.readUInt16BE(2); at = 4; }
  else if (len === 127) { if (b.length < 10) return null; len = Number(b.readBigUInt64BE(2)); at = 10; }
  const mask = masked ? b.subarray(at, at + 4) : null;
  if (masked) at += 4;
  if (b.length < at + len) return null;
  const data = Buffer.from(b.subarray(at, at + len));
  if (mask) for (let i = 0; i < data.length; i++) data[i] ^= mask[i & 3];
  return { op, data, size: at + len };
}

function frame(data, op = 0x1) {
  const len = data.length;
  const head = len < 126 ? Buffer.from([0x80 | op, len])
    : len < 65536 ? Buffer.from([0x80 | op, 126, len >> 8, len & 255])
    : Buffer.concat([Buffer.from([0x80 | op, 127]), (() => { const x = Buffer.alloc(8); x.writeBigUInt64BE(BigInt(len)); return x; })()]);
  return Buffer.concat([head, data]);
}
const wsSend = (socket, obj) => { if (!socket.destroyed) socket.write(frame(Buffer.from(JSON.stringify(obj)))); };

function onPage(text) {
  let m;
  try { m = JSON.parse(text); } catch { return; }
  const ok = Array.isArray(m.quad) && m.quad.length === 4 && m.w > 0 && m.h > 0
    && m.quad.every((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
  if (ok) {
    // viewport px -> the shader's -100..100 frame (Browser 3 fills the 2560x1440 canvas, so the viewport is the canvas)
    const [TL, TR, BR, BL] = m.quad.map(([x, y]) => [+(x / m.w * 200 - 100).toFixed(3), +(y / m.h * 200 - 100).toFixed(3)]);
    want.quad = { Top_Left_X: TL[0], Top_Left_Y: TL[1], Top_Right_X: TR[0], Top_Right_Y: TR[1],
      Bottom_Right_X: BR[0], Bottom_Right_Y: BR[1], Bottom_Left_X: BL[0], Bottom_Left_Y: BL[1] };
  }
  if (typeof m.film === 'boolean') want.film = m.film;
  pump();
}

// Latest-only: while one update is on its way to OBS, newer corners overwrite the waiting ones, so a slow OBS
// never builds a queue that plays back late.
async function pump() {
  if (!obs.ready) return;
  if (busy) { pumpAgain = true; return; }
  busy = true;
  try {
    do {
      pumpAgain = false;
      await captures.render({ film: want.film, quad: want.quad, active: want.active });
    } while (pumpAgain && obs.ready);
  } catch (error) {
    log(`update failed: ${error.message}`);
    if (obs.ws && Date.now() - obs.setupAt > 2000) { setReady(false); setup(); }
  } finally { busy = false; }
}

// View gating is independent of film phase: lobby closes both OBS eyes, whereas
// dim/seating in the auditorium keeps the selected eye available for switching.
let checkingView = false;
async function refreshView() {
  if (checkingView) return;
  checkingView = true;
  let active = false;
  try {
    const response = await fetch(process.env.CINEMA_CONTROL_URL || 'http://127.0.0.1:18770/ctl/state',
      { signal: AbortSignal.timeout(1500) });
    if (!response.ok) throw new Error(`Control HTTP ${response.status}`);
    const state = await response.json();
    active = state.presentation?.view === 'auditorium' && pages.size > 0;
  } catch { /* no confirmed output: keep captures hidden */ }
  finally { checkingView = false; }
  if (want.active !== active) { want.active = active; pump(); }
}
setInterval(refreshView, 500);
refreshView();

server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    log(`Port ${PORT} is already in use. A bridge may already be running; close its window before restarting.`);
    process.exit(1);
  }
  log(`Bridge server failed: ${error.message}`);
  process.exit(1);
});

server.listen(PORT, '0.0.0.0', () => {
  log(`obs-bridge on :${PORT} (pages on this PC only), OBS at ${OBS_URL}`);
  obsConnect();
});
