// DinkDonk Cinema, hosted edition: loaded first in roxy.html, auditorium.html and control.html (the server injects it),
// so the pages run unchanged from the local version:
//   - /ctl/* calls get the room key (?k=) from this page's own URL
//   - the chat socket (ws://127.0.0.1:18765/__dgg_chat_ws) goes to this server's shared relay instead
//   - the auditorium's film-screen bridge (ws://<host>:18790) runs right here in the page: it talks to OBS's own
//     WebSocket server on the streamer's PC (ws://127.0.0.1:4455), so obs-bridge.js and Node are not needed.
//     OBS password and port come from the URL's #fragment (#obs=PASSWORD&obsport=4455), which never leaves the PC.
(() => {
  'use strict';
  const q = new URLSearchParams(location.search);
  const h = new URLSearchParams(location.hash.slice(1));
  const KEY = q.get('k') || '';
  window.DD_WEB = { key: KEY };

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

  // ---------- OBS film-screen bridge (same protocol and behaviour as obs-bridge.js) ----------
  const SCENE = h.get('obsscene') || 'DinkDonk Cinema';
  const FILM = h.get('obsfilm') || 'Film screen (src)';
  const FILTER = 'Corner pin (live)';
  const OBS_URL = `ws://127.0.0.1:${Number(h.get('obsport')) || 4455}`;
  const PASSWORD = h.get('obs') || '';
  const log = (...a) => console.log('[obs-bridge]', ...a);

  const sha256b64 = async (s) => btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))));

  function makeBridge(page) {
    const obs = { ws: null, ready: false, itemId: null, pending: new Map(), seq: 0, setupAt: 0, closed: false };
    const want = { film: false, quad: null };
    const sent = { film: null, quad: null };
    let busy = false;
    let shaderText = null;

    function obsConnect() {
      if (obs.closed) return;
      let ws;
      try { ws = new WebSocket(OBS_URL, 'obswebsocket.json'); } catch (e) { log(e.message); setTimeout(obsConnect, 3000); return; }
      obs.ws = ws;
      ws.onmessage = async (ev) => {
        const m = JSON.parse(ev.data);
        if (m.op === 0) {
          const a = m.d.authentication;
          const identify = { rpcVersion: 1, eventSubscriptions: 2 };
          if (a) identify.authentication = await sha256b64(await sha256b64(PASSWORD + a.salt) + a.challenge);
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
        log(ev.code === 4009 ? 'OBS refused the password: run the setup page again' : `OBS not reachable at ${OBS_URL}, retrying`);
        obs.ws = null;
        setReady(false);
        for (const p of obs.pending.values()) p.reject(new Error('OBS closed'));
        obs.pending.clear();
        // a wrong password stays wrong: retry slowly instead of hammering OBS
        setTimeout(obsConnect, ev.code === 4009 ? 60000 : 3000);
      };
      ws.onerror = () => {};
    }
    function request(requestType, requestData = {}) {
      return new Promise((resolve, reject) => {
        if (!obs.ws || obs.ws.readyState !== WebSocket.OPEN) { reject(new Error('OBS not connected')); return; }
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
          shaderText = shaderText || await (await fetch('/web/corner-pin.shader')).text();
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
      }
    }
    function setReady(on) {
      if (obs.ready === on) return;
      obs.ready = on;
      page.deliver({ obs: on });
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
          log(`film ${film ? 'on' : 'off'}`);
        }
      } catch (e) {
        log(`update failed: ${e.message}`);
        if (obs.ws && Date.now() - obs.setupAt > 2000) { setReady(false); setup(); }
      } finally {
        busy = false;
      }
      if (obs.ready) setTimeout(pump, 0);
    }
    // the page went away (scene switched off, reload): no film floating over the next scene
    addEventListener('pagehide', () => {
      obs.closed = true;
      if (obs.ready && obs.itemId != null) request('SetSceneItemEnabled', { sceneName: SCENE, sceneItemId: obs.itemId, sceneItemEnabled: false }).catch(() => {});
    });
    obsConnect();
    return { onPage };
  }

  // What auditorium.html gets back from `new WebSocket('ws://<host>:18790')`: a socket-shaped object whose other end is
  // the bridge above. It "opens" at once and stays open; {obs:true|false} tells the page whether OBS is linked.
  class BridgeSocket extends EventTarget {
    constructor() {
      super();
      this.readyState = 0;
      this.onopen = this.onmessage = this.onclose = this.onerror = null;
      let last = { obs: false };
      const page = { deliver: (obj) => { last = obj; if (this.readyState === 1) this._emit('message', JSON.stringify(obj)); } };
      this._bridge = makeBridge(page);
      setTimeout(() => { this.readyState = 1; this._emit('open'); this._emit('message', JSON.stringify(last)); }, 0);
    }
    _emit(type, data) {
      const ev = type === 'message' ? new MessageEvent('message', { data }) : new Event(type);
      this.dispatchEvent(ev);
      this[`on${type}`]?.(ev);
    }
    send(text) { if (this.readyState === 1) this._bridge.onPage(String(text)); }
    close() { /* the page never closes it on purpose; keep the OBS link for its lifetime */ }
  }
  let bridgeSocket = null;

  const NativeWS = window.WebSocket;
  function PatchedWebSocket(url, protocols) {
    let u;
    try { u = new URL(String(url), location.href); } catch { return new NativeWS(url, protocols); }
    if (u.pathname === '/__dgg_chat_ws') {
      return new NativeWS(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/__dgg_chat_ws?k=${encodeURIComponent(KEY)}`);
    }
    if (u.port === '18790') {
      bridgeSocket = bridgeSocket || new BridgeSocket();
      return bridgeSocket;
    }
    return protocols === undefined ? new NativeWS(url) : new NativeWS(url, protocols);
  }
  PatchedWebSocket.prototype = NativeWS.prototype;
  for (const k of ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']) PatchedWebSocket[k] = NativeWS[k];
  window.WebSocket = PatchedWebSocket;
})();
