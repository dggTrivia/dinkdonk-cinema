/*
 * Shared logic for the cinema standby scenes (cinema-*.html).
 * Load after shared/core.js. Gives every scene the same rooms (the last five
 * films shown on dinkdonk.mov) and the same stream of walk-ins from chat.
 *
 *   Cinema.onRooms(fn)       fn(rooms, data) now (placeholders) and on every refresh.
 *                            rooms: [{ title, year, poster, rating, votes, watchedTs, conductor, method }] x5
 *   Cinema.onWalkIn(fn)      fn(w) for every chat message that tags the host (see ?tag= below):
 *                            { nick, emote, tokens, text, color, sub, ts, roomIndex, detour, features }
 *                            emote:  first emote of this message, else the last one this
 *                                    chatter used, else a stable default for the nick
 *                            detour: null | 'popcorn' | 'bathroom' (occasional easter eggs)
 *                            features: the chat message's DGG features (e.g. 'moderator')
 *   Cinema.onCombo(fn)       fn({ emote, count }) while chat runs an emote combo
 *   Cinema.onPurge(fn)       fn(nick) when a chatter is muted/banned: remove them
 *   Cinema.showtimes(data)   upcoming movie-night sessions [{ start, end, live }]
 *   Cinema.timeLocal(ts) / Cinema.dayShort(ts)
 *   Cinema.green             'off' or a CSS colour for the chroma-key screen (?green=)
 *   Cinema.tag               nick a message must mention to walk in, or null (everyone)
 *
 * Who walks in: only chatters whose message mentions the host (default arealhumanbean),
 * plus the host's own messages. ?tag=OtherNick changes the nick, ?everyone=1 lets every
 * chatter in. With ?demo=1 everyone walks in unless ?tag= is given.
 */
(() => {
  'use strict';

  const q = new URLSearchParams(location.search);
  const DEFAULT_POOL = ['PEPE', 'YEE', 'AYAYA', 'FeelsGoodMan', 'Wowee', 'NOBULLY', 'Klappa', 'PepeLaugh',
    'WEOW', 'GIMI', 'monkaS', 'SoSad', 'AngelThump', 'DuckerZ', 'BINGQILIN', 'AlienPls'];
  const PLACEHOLDER = ['Feature Presentation', 'Midnight Matinee', 'Coming Soon', 'Double Feature', 'Sneak Preview']
    .map((title) => ({ title, year: '', poster: null, rating: null, votes: null, watchedTs: null, conductor: '', method: '' }));

  const demo = q.has('demo') && q.get('demo') !== '0';
  const everyone = q.get('everyone') === '1' || (demo && !q.get('tag'));
  const TAG = everyone ? null : (q.get('tag') || 'arealhumanbean').replace(/^@/, '');
  const tagRe = TAG && new RegExp(`(^|[^a-z0-9_])@?${TAG.replace(/[^a-z0-9_]/gi, '')}(?![a-z0-9_])`, 'i');
  const walksIn = (m) => !TAG || m.nick.toLowerCase() === TAG.toLowerCase() || tagRe.test(m.text || '');

  const clean = (t) => (t || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const lastEmote = new Map();     // nick -> last emote they used
  const roomOf = new Map();        // nick -> room index they last chose
  let pool = DEFAULT_POOL;
  let rooms = PLACEHOLDER;
  let data = null;
  const roomFns = [];
  const walkFns = [];

  SB.on('emotes', () => {
    const have = DEFAULT_POOL.filter((e) => SB.emotes.names.has(e));
    pool = have.length >= 4 ? have : [...SB.emotes.names].slice(0, 24);
    if (!pool.length) pool = DEFAULT_POOL;
    if (SB.emotes.css) findBoxyEmotes();
  });
  // remember a bounded number of chatters (oldest forgotten first)
  function remember(map, key, value) {
    map.delete(key);
    map.set(key, value);
    if (map.size > 4000) map.delete(map.keys().next().value);
  }

  // Emotes that don't work as a chatter's body: square "picture" emotes (an opaque rectangle, e.g. a photo)
  // are found by reading each emote's border pixels (same-origin copies via standby-server.js); the list
  // below adds ones the owner names by hand. Until the check has run, everything is allowed.
  const AVATAR_BLOCK = new Set(['JARVIS']);
  const boxy = new Set();
  const okAvatar = (name) => !!name && !AVATAR_BLOCK.has(name) && !boxy.has(name);
  async function findBoxyEmotes() {
    let list = [];
    try { list = await (await fetch('/dgg/emotes.json', { cache: 'no-store' })).json(); } catch { return; }
    const jobs = list.filter((e) => typeof e?.prefix === 'string' && e.image?.[0]?.url).map((e) => [e.prefix, e.image[0].url]);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const check = ([name, url]) => new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        if (w < 4 || h < 4) { resolve(); return; }
        canvas.width = w;
        canvas.height = h;
        ctx.clearRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0);
        const a = ctx.getImageData(0, 0, w, h).data;
        let solid = 0;
        let n = 0;
        const at = (x, y) => { n += 1; if (a[(y * w + x) * 4 + 3] > 200) solid += 1; };
        for (let x = 0; x < w; x++) { at(x, 0); at(x, h - 1); }
        for (let y = 1; y < h - 1; y++) { at(0, y); at(w - 1, y); }
        if (solid / n > 0.8) boxy.add(name);   // the picture fills its frame: a square emote
        resolve();
      };
      img.onerror = () => resolve();
      img.src = `/dgg/emote-img?u=${encodeURIComponent(url)}`;
    });
    for (let i = 0; i < jobs.length; i += 8) await Promise.all(jobs.slice(i, i + 8).map(check));
    pool = pool.filter(okAvatar).length >= 4 ? pool.filter(okAvatar) : pool;
    console.info(`[cinema] ${boxy.size} square emotes kept off chatters:`, [...boxy].sort().join(' '));
  }

  function defaultEmote(nick) { return pool[SB.hashHue(nick) % pool.length]; }

  function posterFor(entry) {
    if (!data || !entry) return null;
    const det = entry.ratingId && data.details?.ratings?.[entry.ratingId];
    if (det?.poster) return det.poster;
    const cards = [...(data.ratings || []), ...(data.best || []), ...(data.worst || [])];
    const card = cards.find((r) => r.id === entry.ratingId || clean(r.title) === clean(entry.title));
    return card?.poster || null;
  }

  function buildRooms() {
    const hist = data?.history || [];
    const picked = [];
    const seen = new Set();
    // Last five films shown; TV episodes only if there are not enough films.
    for (const pass of [(e) => e.type !== 'TV', () => true]) {
      for (const e of hist) {
        if (picked.length >= 5) break;
        const key = clean(e.title);
        if (seen.has(key) || !pass(e)) continue;
        seen.add(key);
        const det = e.ratingId && data.details?.ratings?.[e.ratingId];
        picked.push({
          title: e.title, year: e.year, poster: posterFor(e), rating: e.rating ?? null,
          votes: det?.votes?.length ?? null, watchedTs: e.watchedTs, conductor: e.conductor, method: e.method,
        });
      }
    }
    while (picked.length < 5) picked.push(PLACEHOLDER[picked.length]);
    return picked;
  }

  async function refresh() {
    try {
      const res = await fetch('/dd/data.json', { cache: 'no-store' });
      // (odd data: the last good data and rooms stay, instead of new data with old rooms)
      if (res.ok) { const prev = data; data = await res.json(); try { rooms = buildRooms(); } catch (error) { data = prev; throw error; } }
    } catch { /* keep the last rooms */ }
    // one failing handler no longer skips the others (QA 05 Nov)
    for (const fn of roomFns) { try { fn(rooms, data); } catch (error) { console.error('[cinema] rooms handler', error); } }
  }

  SB.on('msg', (m) => {
    const own = m.emotes.find(okAvatar);   // their first emote that works as a body
    if (own) remember(lastEmote, m.nick, own);
    if (!walksIn(m)) return;
    const last = lastEmote.get(m.nick);
    const emote = own || (okAvatar(last) ? last : null) || defaultEmote(m.nick);
    // Regulars mostly go back to the same room, sometimes they switch.
    let roomIndex = roomOf.get(m.nick);
    if (roomIndex == null || Math.random() < 0.3) roomIndex = Math.floor(Math.random() * 5);
    remember(roomOf, m.nick, roomIndex);
    const r = Math.random();
    const detour = r < 0.12 ? 'popcorn' : r < 0.17 ? 'bathroom' : null;
    const w = { nick: m.nick, emote, tokens: m.tokens, text: m.text, color: m.color, rainbow: m.rainbow, sub: m.sub, ts: m.ts, roomIndex, detour,
      features: m.features || [] };
    for (const fn of walkFns) {
      try { fn(w); } catch (error) { console.error('[cinema] walk-in handler', error); }
    }
  });

  function showtimes(d = data) {
    const now = Date.now();
    return (d?.schedule?.sessions || []).filter((s) => s.end > now).sort((a, b) => a.start - b.start)
      .map((s) => ({ start: s.start, end: s.end, live: s.start <= now }));
  }

  window.Cinema = {
    onRooms(fn) { roomFns.push(fn); fn(rooms, data); },
    onWalkIn(fn) { walkFns.push(fn); },
    onCombo(fn) { SB.on('combo', fn); },
    onPurge(fn) { SB.on('purge', fn); },
    showtimes,
    defaultEmote,
    get rooms() { return rooms; },
    get data() { return data; },
    tag: TAG,
    // only opaque hex colours; anything else falls back to the standard key green
    green: q.get('green') === 'off' ? 'off'
      : (/^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.test(q.get('green') || '') ? `#${q.get('green').replace(/^#/, '')}` : '#00ff00'),
    timeLocal: (ts) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    dayShort: (ts) => new Date(ts).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }),
  };

  refresh();
  setInterval(refresh, 120_000);
})();
