/*
 * Standby core: Destiny.gg chat through the DSA OBS overlay relay, emotes,
 * chat stats, chat commands, demo traffic and the 1920x1080 stage.
 *
 * URL parameters (all optional):
 *   relay=127.0.0.1:18765  where the DSA overlay relay runs
 *   f=4                    on-stream chat text size, passed to the relay (1..10)
 *   chat=dsa|native|off    DSA chat iframe (default), our own chat list, or none
 *   chatbar=1              keep the DSA toolbar visible (for OBS Interact)
 *   chatcrop=40            px of the DSA iframe cut off at the bottom
 *   title=BE RIGHT BACK    headline;  sub=...  subline
 *   until=21:30            count down to a local time instead of "away for"
 *   cmds=off               ignore !commands from chat
 *   demo=1                 fake chat traffic, for previewing without the relay
 */
(() => {
  'use strict';

  const q = new URLSearchParams(location.search);
  // cinema.html is the top-level OBS browser source. Its same-origin child
  // must retain OBS detection for the existing film bridge and panel priority.
  if (q.get('managed') === '1' && window.parent !== window) {
    try {
      if (window.parent.location.origin === location.origin && window.parent.obsstudio) {
        window.obsstudio = window.parent.obsstudio;
      }
    } catch { /* standalone or foreign parent: ordinary browser preview */ }
  }
  const demo = q.has('demo') && q.get('demo') !== '0';
  const cfg = {
    relay: q.get('relay') || '127.0.0.1:18765',
    f: q.get('f') || '4',
    demo,
    chat: q.get('chat') || (demo ? 'native' : 'dsa'),
    chatbar: q.get('chatbar') === '1',
    chatcrop: Number(q.get('chatcrop') || 40),
    title: q.get('title'),
    sub: q.get('sub'),
    until: q.get('until'),
    cmds: q.get('cmds') !== 'off',
  };

  // ---------- events ----------
  const handlers = {};
  const on = (type, fn) => { (handlers[type] ||= []).push(fn); };
  const emit = (type, data) => {
    for (const fn of handlers[type] || []) {
      try { fn(data); } catch (error) { console.error(`[standby] ${type} handler`, error); }
    }
  };
  const isOutputActive = () => q.get('managed') !== '1' || window.parent === window
    || window.frameElement?.dataset.active !== 'false';
  addEventListener('message', (event) => {
    if (event.source === window.parent && event.origin === location.origin
        && event.data?.type === 'cinema-output-visibility') emit('outputVisibility', isOutputActive());
  });

  // ---------- stage ----------
  const W = 1920;
  const H = 1080;
  // view = the part of the stage the window shows, in stage px [x0, y0, x1, y1]
  const stage = { scale: 1, el: null, view: [0, 0, W, H] };

  // cover: fill the window and crop the stage's overflowing sides (centred) instead of letterboxing
  function mountStage(el, { cover = false } = {}) {
    stage.el = el;
    Object.assign(el.style, {
      position: 'absolute', left: '0', top: '0',
      width: `${W}px`, height: `${H}px`, transformOrigin: '0 0', overflow: 'hidden',
    });
    const fit = () => {
      stage.scale = (cover ? Math.max : Math.min)(innerWidth / W, innerHeight / H);
      const x = (innerWidth - W * stage.scale) / 2;
      const y = (innerHeight - H * stage.scale) / 2;
      stage.view = [Math.max(0, -x / stage.scale), Math.max(0, -y / stage.scale),
        Math.min(W, (innerWidth - x) / stage.scale), Math.min(H, (innerHeight - y) / stage.scale)];
      el.style.transform = `translate(${x}px, ${y}px) scale(${stage.scale})`;
      emit('resize', stage.scale);
    };
    addEventListener('resize', fit);
    fit();
  }

  // Sizes a canvas to the real pixels it covers so it stays sharp at 1440p/4K.
  function fitCanvas(canvas, w = W, h = H) {
    const ctx = canvas.getContext('2d');
    const apply = () => {
      const k = stage.scale * (devicePixelRatio || 1);
      canvas.width = Math.round(w * k);
      canvas.height = Math.round(h * k);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(k, 0, 0, k, 0, 0);
    };
    on('resize', apply);
    apply();
    return ctx;
  }

  // ---------- emotes ----------
  const FALLBACK_EMOTES = ['PEPE', 'YEE', 'AYAYA', 'LUL', 'OMEGALUL', 'monkaS', 'Klappa', 'FeelsGoodMan',
    'FeelsBadMan', 'SoSad', 'Kappa', 'NOBULLY', 'DuckerZ', 'Wowee', 'GIMI', 'PepeLaugh', 'WEOW',
    'BINGQILIN', 'AngelThump', 'Abathur', 'AlienPls', 'Aware', 'Askers', 'COGGERS', 'ASLAN', 'WAYTOODANK',
    'PepoTurkey', 'Hhhehhehe', 'OOOO', 'SPY', 'MiyanoHype', 'DANKMEMES', 'POTATO', 'CuckCrab', 'GODSTINY'];
  const emotes = { names: new Set(), css: false, sizes: new Map() };
  let measureBox = null;

  // A failed list (server or its CDN not ready at page load) is retried every 30 s: before, the 35 fallback names
  // stayed for the whole night (QA 05 Nov). Every success or late stylesheet emits 'emotes' again (handlers are safe).
  let emoteTry = 0;
  async function loadEmotes() {
    emoteTry++;
    try {
      // bounded: chat must connect even if the emote relay hangs
      const res = await fetch('/dgg/emotes.json', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
      if (!res.ok) throw new Error(res.status);
      const names = new Set();
      for (const e of await res.json()) if (typeof e?.prefix === 'string' && e.prefix) names.add(e.prefix);
      if (!names.size) throw new Error('empty emote list');
      emotes.names.clear();   // (drops the fallback names of a failed first try)
      names.forEach((n) => emotes.names.add(n));
      emotes.sizes.clear();
      await new Promise((resolve) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/dgg/emotes.css';
        let late = false;
        // a stylesheet that arrives after the 8 s wait: sizes measured meanwhile were text estimates, so measure again
        link.onload = () => { emotes.css = true; if (late) { emotes.sizes.clear(); emit('emotes', emotes); } resolve(); };
        // a failed stylesheet is tried again every 30 s (else every emote stays a text pill all night)
        link.onerror = () => { resolve(); retryCss(link); };
        setTimeout(() => { late = true; resolve(); }, 8000);
        document.head.append(link);
      });
    } catch {
      // Opened as a file or without standby-server.js: names only, drawn as text (and tried again in 30 s).
      FALLBACK_EMOTES.forEach((n) => emotes.names.add(n));
      if (location.protocol !== 'file:' && emoteTry < 60) setTimeout(loadEmotes, 30_000);
    }
    emit('emotes', emotes);
  }

  let cssTry = 0;
  function retryCss(failed) {
    if (++cssTry > 60) return;
    setTimeout(() => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = `/dgg/emotes.css?retry=${cssTry}`;
      link.onload = () => { failed.remove(); emotes.css = true; emotes.sizes.clear(); emit('emotes', emotes); };
      link.onerror = () => { link.remove(); retryCss(failed); };
      document.head.append(link);
    }, 30_000);
  }

  // Real per-frame size from emotes.css (emotes.json reports whole sprite sheets).
  function emoteSize(name) {
    if (emotes.sizes.has(name)) return emotes.sizes.get(name);
    let size = { w: 32, h: 32 };
    if (emotes.css) {
      if (!measureBox) {
        measureBox = document.createElement('div');
        measureBox.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden';
        document.body.append(measureBox);
      }
      const el = document.createElement('span');
      el.className = `emote ${name}`;
      measureBox.append(el);
      const r = el.getBoundingClientRect();
      if (r.width > 2 && r.height > 2) size = { w: r.width, h: r.height };
      el.remove();
    } else {
      size = { w: Math.max(40, name.length * 13), h: 30 };
    }
    emotes.sizes.set(name, size);
    return size;
  }

  // An emote scaled to `height` px, laid out at its scaled size.
  // DGG's chat CSS hangs one-shot effects on some emotes as text glyphs in ::before/::after (GSN's dolphins,
  // BEARSLEEP's 💤, PARDNER's 🔫, ...): they jump once in chat but would hover over an emote standing here. Those are
  // hidden (sb-nob / sb-noa in base.css); pseudo-elements that draw an image are part of the emote and stay.
  // Checked once per emote name.
  const textDecos = new Map();
  function textDeco(name) {
    if (textDecos.has(name)) return textDecos.get(name);
    const probe = document.createElement('span');
    probe.className = `emote ${name}`;
    probe.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden';
    document.body.append(probe);
    const glyph = (pe) => {
      const cs = getComputedStyle(probe, pe);
      return !['none', 'normal', '""', "''"].includes(cs.content) && cs.backgroundImage === 'none';
    };
    const d = { before: glyph('::before'), after: glyph('::after') };
    probe.remove();
    textDecos.set(name, d);
    return d;
  }

  function emoteEl(name, height = 32) {
    const { w, h } = emoteSize(name);
    const k = height / h;
    const box = document.createElement('span');
    box.className = 'sb-emote';
    box.style.width = `${w * k}px`;
    box.style.height = `${height}px`;
    const inner = document.createElement('span');
    if (emotes.css) {
      inner.className = `emote ${name}`;
      const deco = textDeco(name);
      if (deco.before) inner.classList.add('sb-nob');
      if (deco.after) inner.classList.add('sb-noa');
      inner.style.transform = `scale(${k})`;
    } else {
      inner.className = 'sb-emote-text';
      inner.textContent = name;
      inner.style.fontSize = `${height * 0.55}px`;
    }
    box.append(inner);
    box.dataset.w = String(w * k);
    return box;
  }

  const URL_RE = /\bhttps?:\/\/\S+|\bwww\.\S+/gi;

  function tokenize(text) {
    const out = [];
    for (const part of text.replace(URL_RE, '🔗').split(/(\s+)/)) {
      if (!part) continue;
      const [base, ...mods] = part.split(':');
      if (emotes.names.has(base) && mods.every((m) => /^[a-z]+$/.test(m))) {
        out.push({ t: 'emote', name: base, mods });
      } else {
        out.push({ t: 'text', v: part });
      }
    }
    return out;
  }

  // Appends text and emotes to `el` using text nodes only (never innerHTML).
  function renderTokens(el, tokens, emoteHeight = 28, maxChars = 160) {
    let used = 0;
    for (const tok of tokens) {
      if (used >= maxChars) { el.append('…'); break; }
      if (tok.t === 'emote') {
        el.append(emoteEl(tok.name, emoteHeight));
        used += 4;
      } else {
        const v = tok.v.slice(0, maxChars - used);
        el.append(v);
        used += v.length;
        if (v.length < tok.v.length) { el.append('…'); break; }
      }
    }
    return el;
  }

  // ---------- people ----------
  function hashHue(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    return h % 360;
  }
  const nickColor = (nick, s = 75, l = 68) => `hsl(${hashHue(nick)} ${s}% ${l}%)`;
  const isSub = (features) => features.some((f) => f === 'subscriber' || /^flair(?:1|3|8|13)$/.test(f));

  // Name colours exactly as DGG chat shows them (same rules as the DSA userscript's dggUsernamePresentation):
  // the colour of the user's flair with the lowest priority number (admin = Destiny, sub tiers, mods, bots ...),
  // plain users white; tier 5 is a moving rainbow. flairs.json (via standby-server.js) replaces this built-in
  // copy when it loads.
  const PLAIN_NICK = '#fff';
  const SUB_TIER_FLAIRS = { 1: 'flair13', 2: 'flair1', 3: 'flair3', 4: 'flair8', 5: 'flair42' };
  let flairs = [
    ['flair17', 1, '#FCE205'], ['admin', 1, '#EE1F1F'], ['flair18', 2, '#f082bb'], ['flair33', 3, '#eb79da', true],
    ['flair42', 3, '#eb79da', true], ['flair7', 3, '#FC4C02'], ['flair12', 3, '#E79015'], ['flair26', 4, '#DD29D2'],
    ['flair8', 4, '#DD29D2'], ['flair24', 5, '#4DB524'], ['flair3', 5, '#4DB524'], ['flair22', 6, '#2ADDC8'],
    ['flair1', 6, '#2ADDC8'], ['flair32', 7, '#59AEEA'], ['flair13', 7, '#59AEEA'], ['flair9', 8, '#59AEEA'],
    ['subscriber', 9, '#59AEEA'], ['bot', 10, '#0088CC'], ['flair11', 11, '#929292'], ['flair125', 126, '#ffd88c'],
    ['moderator', 127, '#DB4C1C'],
  ].map(([name, priority, color, rainbow]) => ({ name, priority, color, rainbow: !!rainbow }));
  function flairColor(features, roles, tier) {
    const has = new Set(features.map((f) => String(f).trim().toLowerCase()).filter(Boolean));
    for (const r of Array.isArray(roles) ? roles : []) {
      const role = String(r).trim().toLowerCase();
      if (role) { has.add(role); has.add(role.replace(/^role[_:-]?/, '')); }
    }
    if (SUB_TIER_FLAIRS[Number(tier)]) { has.add(SUB_TIER_FLAIRS[Number(tier)]); has.add('subscriber'); }
    let best = null;
    for (const f of flairs) if (has.has(f.name) && (!best || f.priority < best.priority)) best = f;
    return best ? { color: best.color, rainbow: best.rainbow } : { color: PLAIN_NICK, rainbow: false };
  }
  // Which way each emote looks by default ('left' | 'right' | 'front'), labelled once from contact sheets
  // (tools/emote-sheet.html); pages mirror an emote so it faces the way it walks. Unknown = 'front' (never mirrored).
  let facing = {};
  async function loadFacing() {
    try { facing = await (await fetch('shared/emote-facing.json', { cache: 'no-store', signal: AbortSignal.timeout(8000) })).json(); } catch { facing = {}; }
  }
  const emoteFacing = (name) => facing[name] || 'front';
  // mirror an emote element so it looks toward dirX (screen x direction: >0 right, <0 left, 0 keeps it)
  function faceEmote(el, name, dirX) {
    const f = emoteFacing(name);
    if (!el || f === 'front' || !dirX) return;
    const flip = (f === 'right') !== (dirX > 0);
    if (el.dataset.flip !== String(flip)) { el.dataset.flip = String(flip); el.style.transform = flip ? 'scaleX(-1)' : ''; }
  }

  async function loadFlairs() {
    try {
      const res = await fetch('/dgg/flairs.json', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
      if (!res.ok) throw new Error(res.status);
      const list = (await res.json()).filter((f) => typeof f?.name === 'string' && /^#[0-9a-f]{3,8}$/i.test(f.color || ''));
      if (list.length) flairs = list.map((f) => ({ name: f.name.toLowerCase(), color: f.color, rainbow: !!f.rainbowColor, priority: Number(f.priority) || 0 }));
    } catch { /* keep the built-in copy */ }
  }

  // ---------- stats ----------
  const STOP = new Set(('the and for you that this with are was but not have just what its it\'s his her they them ' +
    'all can get got like dont don\'t im i\'m out yes yeah now one about from your how why who when there their ' +
    'would will been were has had did does into more some than then lol any she him our too very also only').split(' '));
  const stats = {
    times: [], emoteHits: [], wordHits: [], chatters: new Map(),
    connections: 0, users: 0, startedAt: Date.now(), ingested: 0,
  };

  function prune(arr, ms, now) {
    while (arr.length && now - (arr[0].ts ?? arr[0]) > ms) arr.shift();
  }

  function countTop(arr, n) {
    const counts = new Map();
    for (const { k } of arr) counts.set(k, (counts.get(k) || 0) + 1);
    return [...counts].sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, c]) => ({ k, c }));
  }

  const api = {
    mpm: () => { prune(stats.times, 60_000, Date.now()); return stats.times.length; },
    topEmotes: (n = 5) => { prune(stats.emoteHits, 600_000, Date.now()); return countTop(stats.emoteHits, n); },
    topWords: (n = 20) => { prune(stats.wordHits, 300_000, Date.now()); return countTop(stats.wordHits, n); },
    activeChatters(ms = 300_000) {
      const now = Date.now();
      return [...stats.chatters.values()].filter((c) => now - c.last < ms);
    },
    topChatters(n = 5, ms = 600_000) {
      return api.activeChatters(ms).sort((a, b) => b.recent - a.recent).slice(0, n);
    },
  };

  // ---------- messages, combos, commands ----------
  const combo = { emote: null, count: 0, nicks: new Set() };
  const commands = new Map(); // name -> { cooldown, fn, last }
  const userCooldown = new Map();

  function command(names, cooldownMs, fn) {
    for (const name of [].concat(names)) commands.set(name, { cooldown: cooldownMs, fn, last: 0 });
  }

  function ingestMessage(d) {
    const nick = String(d.nick || '');
    const text = String(d.data || '');
    if (!nick || !text) return;
    const now = Date.now();
    const features = Array.isArray(d.features) ? d.features : [];
    const tokens = tokenize(text);
    const emoteNames = tokens.filter((t) => t.t === 'emote').map((t) => t.name);
    const meaningful = tokens.filter((t) => t.t === 'emote' || t.v.trim());
    const onlyEmote = meaningful.length > 0 && meaningful.every((t) => t.t === 'emote') &&
      new Set(emoteNames).size === 1 ? emoteNames[0] : null;

    const fc = flairColor(features, d.roles, d.subscription?.tier ?? d.subTier);
    const msg = {
      nick, text, tokens, features, ts: now, onlyEmote,
      emotes: emoteNames, color: fc.color, rainbow: fc.rainbow, sub: isSub(features),
    };

    stats.times.push(now);
    for (const e of emoteNames) stats.emoteHits.push({ k: e, ts: now });
    for (const tok of tokens) {
      if (tok.t !== 'text') continue;
      for (const w of tok.v.toLowerCase().match(/[a-z][a-z0-9']{2,18}/g) || []) {
        if (!STOP.has(w)) stats.wordHits.push({ k: w, ts: now });
      }
    }
    const c = stats.chatters.get(nick) || { nick, count: 0, recent: 0, first: now, color: msg.color };
    c.recent = now - (c.last || 0) > 600_000 ? 1 : c.recent + 1;
    c.count += 1;
    c.last = now;
    c.sub = msg.sub;
    stats.chatters.set(nick, c);
    // keep the buffers bounded even in scenes that never read the stats
    if (++stats.ingested % 200 === 0) {
      prune(stats.times, 60_000, now);
      prune(stats.emoteHits, 600_000, now);
      prune(stats.wordHits, 300_000, now);
      for (const [k, v] of stats.chatters) if (now - v.last > 1_800_000) stats.chatters.delete(k);
      for (const [k, t] of userCooldown) if (now - t > 60_000) userCooldown.delete(k);
    }

    emit('msg', msg);

    if (onlyEmote && onlyEmote === combo.emote && !combo.nicks.has(nick)) {
      combo.count += 1;
      combo.nicks.add(nick);
      emit('combo', { emote: combo.emote, count: combo.count, nick });
    } else if (onlyEmote !== combo.emote || !onlyEmote) {
      if (combo.count >= 2) emit('comboEnd', { emote: combo.emote, count: combo.count });
      combo.emote = onlyEmote;
      combo.count = onlyEmote ? 1 : 0;
      combo.nicks = new Set(onlyEmote ? [nick] : []);
    }

    if (cfg.cmds && text.startsWith('!')) {
      const [head, ...args] = text.slice(1).split(/\s+/);
      const cmd = commands.get(head.toLowerCase());
      if (cmd && now - cmd.last >= cmd.cooldown && now - (userCooldown.get(nick) || 0) >= 8_000) {
        cmd.last = now;
        userCooldown.set(nick, now);
        try { cmd.fn({ nick, args, msg }); } catch (error) { console.error(error); }
        emit('command', { name: head.toLowerCase(), nick, args });
      }
    }
  }

  function handleFrame(raw) {
    const sp = raw.indexOf(' ');
    const type = sp < 0 ? raw : raw.slice(0, sp);
    let d = {};
    try { d = JSON.parse(raw.slice(sp + 1)); } catch { /* not every frame has JSON */ }
    if (!d || typeof d !== 'object') d = {};   // 'MSG null' and the like
    switch (type) {
      case 'MSG': ingestMessage(d); break;
      case 'NAMES':
        stats.connections = d.connectioncount || 0;
        stats.users = Array.isArray(d.users) ? d.users.length : 0;
        emit('names', { connections: stats.connections, users: stats.users });
        break;
      case 'JOIN': stats.users += 1; emit('join', d); break;
      case 'QUIT': stats.users = Math.max(0, stats.users - 1); emit('quit', d); break;
      case 'MUTE': case 'BAN':
        // who did it and how, for the auditorium's janny escort (DGG: nick = the mod, data = the target)
        emit('modAction', { kind: type, nick: String(d.data || ''), by: String(d.nick || '') });
        emit('purge', String(d.data || ''));
        break;
      case 'BROADCAST': emit('broadcast', { text: String(d.data || '') }); break;
      case 'SUBSCRIPTION': case 'GIFTSUB': case 'MASSGIFT': case 'DONATION':
        emit('support', { kind: type, nick: String(d.nick || d.user?.nick || 'someone'), text: String(d.data || '') });
        break;
      default: break;
    }
  }

  // ---------- relay connection ----------
  let status = 'connecting';
  const setStatus = (s) => { status = s; emit('status', s); };
  let retry = 0;

  function connect() {
    if (status !== 'offline') setStatus('connecting'); // retries stay "offline" until one succeeds
    let ws;
    try {
      ws = new WebSocket(`ws://${cfg.relay}/__dgg_chat_ws`);
    } catch {
      setTimeout(connect, 5_000);
      return;
    }
    // a relay that stays connected but goes silent (lost its DGG upstream, hung) is dropped after 3 min without a
    // single frame (busy chat, joins and quits never pause that long) and the reconnect below takes over
    let lastFrame = Date.now();
    const watch = setInterval(() => { if (ws.readyState === 1 && Date.now() - lastFrame > 180_000) ws.close(); }, 15_000);
    ws.onopen = () => { retry = 0; lastFrame = Date.now(); setStatus('live'); };
    ws.onmessage = (ev) => { lastFrame = Date.now(); handleFrame(String(ev.data)); };
    ws.onclose = () => {
      clearInterval(watch);
      setStatus('offline');
      setTimeout(connect, Math.min(30_000, 1_000 * 2 ** retry++));
    };
    ws.onerror = () => ws.close();
  }

  // ---------- demo traffic ----------
  const DEMO_NICKS = ['Mooby', 'cocoFan', 'gamer_dad', 'PepoAnon', 'yeeyee', 'Rightoid', 'leftie_lucy', 'Bingus',
    'ThumbAngel', 'popcorn_andy', 'xX_lurk_Xx', 'NeoDGG', 'tinfoilhat', 'MovieBuff', 'kneegrow', 'okayeg',
    'sleepyhead', 'Tuesday', 'Sir_Reginald', 'smolbean', 'directorscut', 'Uberwatch', 'lemonparty', 'ClipThat'];
  const DEMO_LINES = ['what did i miss', 'brb popcorn', 'is the movie over already', 'this standby screen goes hard',
    'who picked this film', 'LETS GO', 'the ending tho', 'my stream is lagging or is it just me',
    'hydrate chat', 'that plot twist was so obvious', 'how long is the break', 'bathroom break respected',
    'sound was off for a sec', 'next one better be good', 'first time catching the watch party', 'CINEMA',
    'pepe vs yee who wins', 'the vibes are immaculate', 'love the music here', 'rate the movie 1-10'];
  const DEMO_EMOTES = ['PEPE', 'YEE', 'AYAYA', 'OMEGALUL', 'monkaS', 'Klappa', 'FeelsGoodMan', 'SoSad', 'Wowee',
    'PepeLaugh', 'WEOW', 'BINGQILIN', 'AngelThump', 'NOBULLY', 'GIMI', 'LUL', 'DuckerZ', 'AlienPls', 'Aware'];

  function startDemo() {
    const pick = (a) => a[Math.floor(Math.random() * a.length)];
    const pool = DEMO_EMOTES.filter((e) => emotes.names.has(e));
    const emotePool = pool.length > 4 ? pool : [...emotes.names].slice(0, 40);
    const cmdList = () => [...commands.keys()];
    handleFrame(`NAMES ${JSON.stringify({ connectioncount: 3120, users: new Array(2480).fill(0) })}`);
    setStatus('demo');
    let comboLeft = 0;
    let comboEmote = null;
    const tick = () => {
      const r = Math.random();
      let data;
      if (comboLeft > 0) { data = comboEmote; comboLeft -= 1; }
      else if (r < 0.06) { comboEmote = pick(emotePool); comboLeft = 3 + Math.floor(Math.random() * 10); data = comboEmote; }
      else if (r < 0.10 && cmdList().length) data = `!${pick(cmdList())}`;
      else if (r < 0.38) data = Array.from({ length: 1 + Math.floor(Math.random() * 3) }, () => pick(emotePool)).join(' ');
      else if (r < 0.60) data = `${pick(DEMO_LINES)} ${pick(emotePool)}`;
      else data = pick(DEMO_LINES);
      const features = Math.random() < 0.3 ? ['subscriber'] : [];
      handleFrame(`MSG ${JSON.stringify({ nick: pick(DEMO_NICKS), features, data })}`);
      const burst = Math.sin(Date.now() / 9_000) * 0.5 + 0.5; // waves of activity
      setTimeout(tick, comboLeft > 0 ? 260 : 250 + Math.random() * (1_800 - burst * 1_300));
    };
    setTimeout(tick, 400);
  }

  // ---------- chat panel ----------
  function mountChat(el, { emoteHeight = 30, max = 40 } = {}) {
    el.classList.add('sb-chat');
    if (cfg.chat === 'off') { el.remove(); return; }
    if (cfg.chat === 'dsa') {
      const frame = document.createElement('iframe');
      frame.src = `http://${cfg.relay}/?f=${encodeURIComponent(cfg.f)}`;
      frame.setAttribute('allowtransparency', 'true');
      frame.className = 'sb-chat-frame';
      if (!cfg.chatbar) frame.style.height = `calc(100% + ${cfg.chatcrop}px)`;
      el.append(frame);
      const note = document.createElement('div');
      note.className = 'sb-chat-note';
      note.textContent = 'Chat relay offline — start the DSA overlay (start-windows.bat)';
      el.append(note);
      on('status', (s) => { note.hidden = s !== 'offline'; });
      note.hidden = true;
      return;
    }
    const list = document.createElement('div');
    list.className = 'sb-chat-list';
    el.append(list);
    on('msg', (m) => {
      const line = document.createElement('div');
      line.className = 'sb-chat-line';
      line.dataset.nick = m.nick.toLowerCase();
      const who = document.createElement('span');
      who.className = 'sb-chat-nick';
      who.style.color = m.color;
      who.textContent = m.nick;
      line.append(who, ': ');
      renderTokens(line, m.tokens, emoteHeight, 400);
      list.append(line);
      while (list.children.length > max) list.firstChild.remove();
    });
    on('purge', (nick) => {
      for (const line of list.querySelectorAll(`[data-nick="${CSS.escape(nick.toLowerCase())}"]`)) line.remove();
    });
  }

  // ---------- clock / timer ----------
  function timerText() {
    const now = new Date();
    if (cfg.until && /^\d{1,2}:\d{2}$/.test(cfg.until)) {
      const [h, m] = cfg.until.split(':').map(Number);
      const target = new Date(now);
      target.setHours(h, m, 0, 0);
      const left = Math.max(0, target - now);
      const s = Math.floor(left / 1000);
      return { label: left ? 'back in' : 'any second now', value: `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`, left };
    }
    const s = Math.floor((now - stats.startedAt) / 1000);
    return { label: 'away for', value: `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`, left: null };
  }

  const clockText = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // ---------- misc ----------
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

  function start() {
    Promise.all([loadEmotes(), loadFlairs(), loadFacing()]).then(() => {
      if (cfg.demo) startDemo();
      else connect();
    });
  }

  window.SB = {
    cfg, on, emit, start, mountStage, fitCanvas, mountChat, command, stats, isOutputActive, ...api,
    emoteEl, emoteSize, emoteFacing, faceEmote, tokenize, renderTokens, nickColor, hashHue, timerText, clockText,
    rand, pick, get status() { return status; }, get emotes() { return emotes; }, get view() { return stage.view; }, W, H,
    // For testing from the console: SB.say('someone', '!claw')
    say: (nick, data, features = []) => handleFrame(`MSG ${JSON.stringify({ nick, data, features })}`),
  };
})();
