// DinkDonk Cinema, hosted edition: loaded first in lobby.html, auditorium.html and control.html (the server injects it),
// so the pages run unchanged from the local version:
//   - /ctl/* calls get the room key (?k=) from this page's own URL
//   - the chat socket (ws://127.0.0.1:18765/__dgg_chat_ws) goes to this server's shared relay instead
//   - the auditorium's film-screen bridge (ws://<host>:18790) is answered right here, by the same logic as
//     obs-bridge.js, talking to OBS's own WebSocket server on the streamer's PC (ws://127.0.0.1:4455):
//       direct: the auditorium (inside OBS) talks to OBS itself. OBS password/port come from the URL's #fragment
//               (#obs=PASSWORD&obsport=4455), which never leaves the PC.
//       relay:  where OBS's browser may not reach 127.0.0.1 from a website (OBS 33+, Chromium's local network access
//               rules), the auditorium sends the screen corners through this server to the control panel, open in the
//               streamer's normal browser, which talks to OBS instead (password saved there by setup.html).
(() => {
  'use strict';
  const q = new URLSearchParams(location.search);
  const h = new URLSearchParams(location.hash.slice(1));
  const KEY = q.get('k') || '';
  const PAGE = location.pathname.split('/').pop() || '';
  window.DD_WEB = { key: KEY };
  const wsBase = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`;

  const keyed = (u) => {
    try {
      const url = new URL(u, location.href);
      if (url.origin === location.origin && url.pathname.startsWith('/ctl/')) { url.searchParams.set('k', KEY); return url.href; }
    } catch { /* not a URL: leave it */ }
    return u;
  };
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, init) => nativeFetch(typeof input === 'string' || input instanceof URL ? keyed(String(input)) : input, init);
  const NativeES = window.EventSource;
  window.EventSource = class extends NativeES { constructor(url, opts) { super(keyed(String(url)), opts); } };
  const NativeWS = window.WebSocket;

  // ---------- OBS film-screen bridge (same protocol and behaviour as obs-bridge.js) ----------
  const SCENE = h.get('obsscene') || 'DinkDonk Cinema';
  const FILM = h.get('obsfilm') || 'Film screen (src)';
  const FILTER = 'Corner pin (live)';
  const log = (...a) => console.log('[obs-bridge]', ...a);
  const sha256b64 = async (s) => btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))));

  // page.deliver({obs}) reports whether OBS is linked; onPage(text) takes the auditorium's {film, w, h, quad}.
  // onUnreachable fires once if the very first connection attempt never opens (blocked or nothing listening).
  function makeBridge({ port, password, deliver, onUnreachable }) {
    const OBS_URL = `ws://127.0.0.1:${port || 4455}`;
    const obs = { ws: null, ready: false, itemId: null, pending: new Map(), seq: 0, setupAt: 0, closed: false, everOpen: false, filmShown: false };
    const want = { film: false, quad: null };
    const sent = { film: null, quad: null };
    let busy = false;
    let shaderText = null;

    function obsConnect() {
      if (obs.closed) return;
      let ws;
      try { ws = new NativeWS(OBS_URL, 'obswebsocket.json'); } catch (e) {
        log(e.message);
        if (!obs.everOpen && onUnreachable) { onUnreachable(); onUnreachable = null; return; }
        setTimeout(obsConnect, 3000);
        return;
      }
      obs.ws = ws;
      ws.onopen = () => { obs.everOpen = true; };
      ws.onmessage = async (ev) => {
        const m = JSON.parse(ev.data);
        if (m.op === 0) {
          const a = m.d.authentication;
          const identify = { rpcVersion: 1, eventSubscriptions: 2 };   // Config: scene collection switches
          if (a) identify.authentication = await sha256b64(await sha256b64(password + a.salt) + a.challenge);
          ws.send(JSON.stringify({ op: 1, d: identify }));
        } else if (m.op === 2) {
          log('OBS connected');
          setup();
        } else if (m.op === 5 && m.d.eventType === 'CurrentSceneCollectionChanged') {
          setReady(false);
          setup();
        } else if (m.op === 7) {
          const p = obs.pending.get(m.d.requestId);
          if (!p) return;
          obs.pending.delete(m.d.requestId);
          if (m.d.requestStatus.result) p.resolve(m.d.responseData || {});
          else p.reject(new Error(`${m.d.requestType}: ${m.d.requestStatus.comment || m.d.requestStatus.code}`));
        }
      };
      ws.onclose = (ev) => {
        if (obs.ws !== ws) return;
        obs.ws = null;
        setReady(false);
        for (const p of obs.pending.values()) p.reject(new Error('OBS closed'));
        obs.pending.clear();
        if (!obs.everOpen && onUnreachable && ev.code !== 4009) { log(`OBS not reachable at ${OBS_URL}`); onUnreachable(); onUnreachable = null; return; }
        log(ev.code === 4009 ? 'OBS refused the password: run the setup page again' : `OBS not reachable at ${OBS_URL}, retrying`);
        // a wrong password stays wrong: retry slowly instead of hammering OBS
        setTimeout(obsConnect, ev.code === 4009 ? 60000 : 3000);
      };
      ws.onerror = () => {};
    }
    function request(requestType, requestData = {}) {
      return new Promise((resolve, reject) => {
        if (!obs.ws || obs.ws.readyState !== 1) { reject(new Error('OBS not connected')); return; }
        const requestId = String(++obs.seq);
        obs.pending.set(requestId, { resolve, reject });
        obs.ws.send(JSON.stringify({ op: 6, d: { requestType, requestId, requestData } }));
      });
    }
    async function setup() {
      obs.setupAt = Date.now();
      try {
        const { sceneItemId } = await request('GetSceneItemId', { sceneName: SCENE, sourceName: FILM });
        const { filters } = await request('GetSourceFilterList', { sourceName: FILM });
        if (!filters.some((f) => f.filterName === FILTER)) {
          // the shader travels inline, so it works wherever obs-shaderfilter is installed
          shaderText = shaderText || await (await nativeFetch('/web/corner-pin.shader')).text();
          await request('CreateSourceFilter', { sourceName: FILM, filterName: FILTER, filterKind: 'shader_filter',
            filterSettings: { from_file: false, shader_text: shaderText, Antialias_Edges: true } });
          log(`created filter "${FILTER}" on "${FILM}"`);
        }
        for (const f of filters) {
          if (f.filterName !== FILTER && f.filterEnabled && /corner pin/i.test(f.filterName)) {
            await request('SetSourceFilterEnabled', { sourceName: FILM, filterName: f.filterName, filterEnabled: false });
          }
        }
        await request('SetSourceFilterEnabled', { sourceName: FILM, filterName: FILTER, filterEnabled: true });
        obs.itemId = sceneItemId;
        sent.quad = null;
        sent.film = null;
        setReady(true);
        log(`ready: "${FILM}" is item ${sceneItemId} in "${SCENE}"`);
        pump();
      } catch (e) {
        log(`not ready (${e.message}); run the setup page to create the "${SCENE}" scene`);
        // the scenes may be created while this page is open: look again
        const ws = obs.ws;
        setTimeout(() => { if (obs.ws === ws && ws?.readyState === 1 && !obs.ready) setup(); }, 10000);
      }
    }
    function setReady(on) {
      if (obs.ready === on) return;
      obs.ready = on;
      deliver({ obs: on });
    }
    function onPage(text) {
      let m;
      try { m = JSON.parse(text); } catch { return; }
      const ok = Array.isArray(m.quad) && m.quad.length === 4 && m.w > 0 && m.h > 0
        && m.quad.every((p) => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]));
      if (ok) {
        // viewport px -> the shader's -100..100 frame (the browser source fills the canvas, so the viewport is the canvas)
        const [TL, TR, BR, BL] = m.quad.map(([x, y]) => [+(x / m.w * 200 - 100).toFixed(3), +(y / m.h * 200 - 100).toFixed(3)]);
        want.quad = { Top_Left_X: TL[0], Top_Left_Y: TL[1], Top_Right_X: TR[0], Top_Right_Y: TR[1],
          Bottom_Right_X: BR[0], Bottom_Right_Y: BR[1], Bottom_Left_X: BL[0], Bottom_Left_Y: BL[1] };
      }
      if (typeof m.film === 'boolean') want.film = m.film;
      pump();
    }
    // latest-only: a slow OBS never builds a queue that plays back late
    async function pump() {
      if (busy || !obs.ready) return;
      const quadKey = want.quad && JSON.stringify(want.quad);
      const film = want.film && !!want.quad;
      if (quadKey === sent.quad && film === sent.film) return;
      busy = true;
      try {
        if (quadKey && quadKey !== sent.quad) {
          await request('SetSourceFilterSettings', { sourceName: FILM, filterName: FILTER, filterSettings: want.quad, overlay: true });
          sent.quad = quadKey;
        }
        if (film !== sent.film) {
          await request('SetSceneItemEnabled', { sceneName: SCENE, sceneItemId: obs.itemId, sceneItemEnabled: film });
          sent.film = film;
          if (film) obs.filmShown = true;
          log(`film ${film ? 'on' : 'off'}`);
        }
      } catch (e) {
        log(`update failed: ${e.message}`);
        if (obs.ws && Date.now() - obs.setupAt > 2000) { setReady(false); setup(); }
      } finally {
        busy = false;
      }
      // a microtask, not a timer: the relay host may sit in a background tab, where timers are throttled
      if (obs.ready) Promise.resolve().then(pump);
    }
    function close() {
      obs.closed = true;
      // only the bridge that put the film up takes it down (a relay host closing must not hide a direct page's film)
      if (obs.ready && obs.itemId != null && obs.filmShown) request('SetSceneItemEnabled', { sceneName: SCENE, sceneItemId: obs.itemId, sceneItemEnabled: false }).catch(() => {});
      if (obs.ws) obs.ws.close();
    }
    addEventListener('pagehide', close);
    obsConnect();
    return { onPage, close, isReady: () => obs.ready };
  }

  // What auditorium.html gets back from `new WebSocket('ws://<host>:18790')`: a socket-shaped object that answers like
  // obs-bridge.js. It "opens" at once and stays open; {obs:true|false} tells the page whether the film screen is linked.
  class BridgeSocket extends EventTarget {
    constructor() {
      super();
      this.readyState = 0;
      this.onopen = this.onmessage = this.onclose = this.onerror = null;
      this._last = { obs: false };
      this._target = null;
      this._direct();
      setTimeout(() => { this.readyState = 1; this._emit('open'); this._emit('message', JSON.stringify(this._last)); }, 0);
    }
    _deliver(obj) { this._last = obj; if (this.readyState === 1) this._emit('message', JSON.stringify(obj)); }
    _direct() {
      const bridge = makeBridge({ port: Number(h.get('obsport')) || 4455, password: h.get('obs') || '', deliver: (o) => this._deliver(o),
        onUnreachable: () => { log('switching to relay through the control panel'); this._relay(); } });
      this._target = { send: (t) => bridge.onPage(t) };
    }
    _relay() {
      let ws = null, queued = null;
      const open = () => {
        ws = new NativeWS(`${wsBase}/__bridge?k=${encodeURIComponent(KEY)}&role=page`);
        ws.onopen = () => { if (queued) ws.send(queued); queued = null; };
        ws.onmessage = (e) => { try { const m = JSON.parse(e.data); if (typeof m.obs === 'boolean') this._deliver({ obs: m.obs }); } catch { /* ignore */ } };
        ws.onclose = () => { this._deliver({ obs: false }); setTimeout(open, 3000); };
      };
      open();
      // corners arrive many times a second while the camera moves: send the newest, drop the rest while connecting
      this._target = { send: (t) => { if (ws?.readyState === 1) ws.send(t); else queued = t; } };
    }
    _emit(type, data) {
      const ev = type === 'message' ? new MessageEvent('message', { data }) : new Event(type);
      this.dispatchEvent(ev);
      this[`on${type}`]?.(ev);
    }
    send(text) { if (this.readyState === 1) this._target.send(String(text)); }
    close() { /* the page never closes it on purpose; keep the OBS link for its lifetime */ }
  }
  let bridgeSocket = null;

  function PatchedWebSocket(url, protocols) {
    let u;
    try { u = new URL(String(url), location.href); } catch { return new NativeWS(url, protocols); }
    if (u.pathname === '/__dgg_chat_ws') return new NativeWS(`${wsBase}/__dgg_chat_ws?k=${encodeURIComponent(KEY)}`);
    if (u.port === '18790') {
      bridgeSocket = bridgeSocket || new BridgeSocket();
      return bridgeSocket;
    }
    return protocols === undefined ? new NativeWS(url) : new NativeWS(url, protocols);
  }
  PatchedWebSocket.prototype = NativeWS.prototype;
  for (const k of ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']) PatchedWebSocket[k] = NativeWS[k];
  window.WebSocket = PatchedWebSocket;

  // ---------- relay host: the control panel in the streamer's own browser ----------
  // Uses the OBS password setup.html saved in this browser. Shows a small status line at the top of the panel.
  if (PAGE === 'control.html') {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem('dd-obs') || 'null'); } catch { /* storage blocked */ }
    addEventListener('DOMContentLoaded', () => {
      const badge = document.createElement('div');
      badge.style.cssText = 'margin:-6px 0 14px;font:13px/1.4 system-ui,sans-serif;color:#8b90a0';
      document.querySelector('h1')?.after(badge);
      const state = { relay: false, obs: false, pages: 0 };
      const show = () => {
        badge.textContent = !saved ? 'Film screen link: run setup.html on this PC once to let this panel reach OBS (needed for OBS 33 and newer).'
          : `Film screen link: OBS ${state.obs ? 'connected' : 'not connected'} · server ${state.relay ? 'connected' : 'connecting'}` +
            (state.pages ? ` · auditorium using this panel` : '') + ' · keep this tab open during the film';
      };
      show();
      if (!saved) return;
      let ws = null;
      const bridge = makeBridge({ port: saved.port, password: saved.pw || '', deliver: (o) => { state.obs = o.obs; show(); if (ws?.readyState === 1) ws.send(JSON.stringify(o)); } });
      const open = () => {
        ws = new NativeWS(`${wsBase}/__bridge?k=${encodeURIComponent(KEY)}&role=obs`);
        ws.onopen = () => { state.relay = true; show(); ws.send(JSON.stringify({ obs: bridge.isReady() })); };
        ws.onmessage = (e) => {
          let m;
          try { m = JSON.parse(e.data); } catch { return; }
          if (typeof m.pages === 'number') { state.pages = m.pages; show(); return; }
          bridge.onPage(e.data);
        };
        ws.onclose = () => { state.relay = false; state.pages = 0; show(); setTimeout(open, 3000); };
      };
      open();
    });
  }
})();
