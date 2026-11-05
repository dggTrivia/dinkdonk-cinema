'use strict';

// Reads dinkdonk.mov's public pages (watch history, ratings, polls, schedule)
// and turns them into one JSON feed for the standby screen. The site has no
// public JSON API, so this parses its server-rendered HTML. Results are cached
// in memory and on disk, so the screen keeps working while the site is
// unreachable (e.g. Cloudflare blocks during LaLiga matches).

const fs = require('node:fs');
const path = require('node:path');

const ORIGIN = 'https://dinkdonk.mov';
const UA = 'Mozilla/5.0 (compatible; dgg-obs-standby; +local)';
const REFRESH_MS = 5 * 60 * 1000;
const HISTORY_PAGES = 8;          // 25 entries each
const CACHE_FILE = path.join(__dirname, 'cache', 'dinkdonk.json');
const SITE_TZ = 'America/New_York';

// ---------- html helpers ----------
const ENTITIES = { quot: '"', amp: '&', lt: '<', gt: '>', apos: "'", nbsp: ' ', rarr: '→', hellip: '…', ndash: '–', mdash: '—' };
function decode(s = '') {
  return s.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, e) => {
    if (e[0] === '#') {
      const n = e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return Number.isFinite(n) ? String.fromCodePoint(n) : m;
    }
    return ENTITIES[e.toLowerCase()] ?? m;
  });
}
const text = (s = '') => decode(s.replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
const first = (re, s, i = 1) => { const m = re.exec(s); return m ? m[i] : null; };
const num = (v) => (v == null || v === '' ? null : Number(v));
const bigPoster = (url) => (url ? url.replace('/t/p/w92/', '/t/p/w342/') : null);

// "2026-11-06 21:00:00" in an IANA zone -> epoch ms.
function zonedToUtc(local, tz) {
  const [d, t = '00:00:00'] = local.trim().split(/[ T]/);
  const [y, mo, da] = d.split('-').map(Number);
  const [h, mi, se = 0] = t.split(':').map(Number);
  const guess = Date.UTC(y, mo - 1, da, h, mi, se);
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).formatToParts(guess).map((p) => [p.type, p.value]));
  const asZone = Date.UTC(+parts.year, +parts.month - 1, +parts.day, +parts.hour, +parts.minute, +parts.second);
  return guess - (asZone - guess);
}

async function get(pathname) {
  const res = await fetch(ORIGIN + pathname, {
    headers: { 'User-Agent': UA, 'HX-Request': 'true', Accept: 'text/html' },
    signal: AbortSignal.timeout(20_000),
  });
  if (!res.ok) throw new Error(`${pathname}: HTTP ${res.status}`);
  return res.text();
}

// ---------- parsers ----------
function parseHistory(html) {
  return html.split('<tr data-id="').slice(1).map((chunk) => {
    const id = Number(chunk.slice(0, chunk.indexOf('"')));
    const fields = {};
    for (const m of chunk.matchAll(/data-field="(\w+)" data-value="([^"]*)"/g)) fields[m[1]] = decode(m[2]);
    const yearText = first(/wl-title-year">([^<]*)</, chunk);
    return {
      id,
      title: decode(first(/wl-title-text"[^>]*>([^<]*)</, chunk) || ''),
      year: yearText ? decode(yearText).replace(/[()]/g, '').trim() : '',
      imdb: first(/href="(https:\/\/www\.imdb\.com\/title\/[^"]+)"/, chunk),
      type: text(first(/<td class="wl-nowrap">([^<]*)<\/td>/, chunk) || ''),
      watchedAt: fields.watchedAt || null,
      // The log is kept in New York time; this matches when ratings close.
      watchedTs: fields.watchedAt ? zonedToUtc(fields.watchedAt.replace('T', ' '), SITE_TZ) : null,
      method: fields.method || '',
      conductor: fields.conductorName || '',
      picker: fields.pickerName || '',
      ratingId: fields.ratingId || null,
      rating: num(first(/wl-rating-average-tag">[\s\S]*?value-value="([\d.]+)"/, chunk)),
      polls: (fields.polls || '').split(',').filter(Boolean),
      notes: fields.notes || '',
    };
  }).filter((e) => e.id && e.title);
}

function parseRatingCards(html) {
  return html.split('<a class="rating-card" href="/rate/').slice(1).map((chunk) => {
    const values = [...chunk.matchAll(/value-value="([\d.]+)"/g)].map((m) => Number(m[1]));
    return {
      id: chunk.slice(0, chunk.indexOf('/')),
      title: decode(first(/rating-card__title">([^<]*)</, chunk) || ''),
      poster: bigPoster(first(/<img src="([^"]+)"/, chunk)),
      avg: values[0] ?? null,
      votes: values[1] ?? null,
    };
  });
}

function parseRatingDetail(id, html) {
  const tmdb = /value-value="([\d.]+)"[^>]*>[^<]*<\/span>% \(<span[^>]*value-value="(\d+)"/.exec(html);
  const votes = first(/data-ratings="(\[[^\]]*\])"/, html);
  // Extra details come in order: runtime, languages, genres, TMDB score. Long
  // lists sit in a tooltip, single values only in the span.
  const extra = (first(/class="option__details-extra">([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>/, html) || '')
    .split('option__details-extra--group').slice(1)
    .map((g) => decode(first(/data-tippy-content="([^"]*)"/, g) || first(/<span>([^<]*)<\/span>/, g) || '').trim())
    .filter((g) => g && !/^\d+h|^\d+m$|%/.test(g));
  const genres = extra.length >= 2 ? extra[1] : '';
  return {
    id,
    title: decode(first(/<a class="link" href="https:\/\/imdb\.com[^"]*"[^>]*>([^<]+)<\/a>/, html) || ''),
    poster: bigPoster(first(/class="option__top">\s*<img src="([^"]+)"/, html)),
    by: decode(first(/Created by ([^<]+)</, html) || ''),
    endedAt: num(first(/unix-value="(\d+)"/, html)) * 1000 || null,
    overview: decode(first(/class="option__overview"[^>]*>([^<]*)</, html) || ''),
    runtime: first(/<span>(\d+h(?: \d+m)?|\d+m)<\/span>/, html),
    age: decode(first(/badge--neutral"[^>]*>([^<]+)</, html) || ''),
    genres,
    tmdbScore: tmdb ? Number(tmdb[1]) : null,
    tmdbVotes: tmdb ? Number(tmdb[2]) : null,
    votes: votes ? JSON.parse(votes) : [],
  };
}

function parsePollCards(html) {
  return html.split('<a class="poll-card" href="/poll/').slice(1).map((chunk) => {
    const kind = /<span>([^<]*?) Poll by ([^<]+)<\/span>/.exec(chunk);
    const winners = chunk.split('class="poll-card__winner"').slice(1).map((w) => ({
      label: /Runner-up/.test(w.slice(0, 200)) ? 'Runner-up' : 'Winner',
      poster: bigPoster(first(/<img src="([^"]+)"/, w)),
      title: decode(first(/<span>([^<]*)<\/span>/, w) || ''),
    }));
    return {
      id: chunk.slice(0, chunk.indexOf('/')),
      title: decode(first(/poll-card__title">([^<]*)</, chunk) || ''),
      kind: kind ? decode(kind[1]) : '',
      by: kind ? decode(kind[2]) : '',
      winners,
    };
  });
}

function parsePollDetail(id, html) {
  const type = first(/data-poll-result-type-value="([a-z_]+)"/, html) || '';
  const detail = {
    id,
    type,
    title: decode(first(/section-header__heading">([^<]*)</, html) || ''),
    by: decode(first(/Poll created by ([^<]+)</, html) || ''),
    endedAt: num(first(/unix-value="(\d+)"/, html)) * 1000 || null,
    voters: num(first(/data-poll-result-users-value="(\d+)"/, html)),
    options: [],
    rounds: null,
  };
  if (type === 'instant_runoff') {
    const opts = first(/data-options="([^"]*)"/, html);
    const rounds = first(/data-result="([^"]*)"/, html);
    detail.options = opts ? JSON.parse(decode(opts)).map((o) => ({
      id: o.id,
      title: o.option.title,
      year: o.option.year || '',
      poster: bigPoster(o.option.img),
      tmdb: o.option.rating ?? null,
      lastWatched: o.option.lastWatched ?? null,
      playCount: o.option.playCount ?? null,
      runtime: o.option.runtime || '',
    })) : [];
    detail.rounds = rounds ? JSON.parse(decode(rounds)) : [];
  } else {
    detail.options = html.split('class="option-group"').slice(1).map((chunk) => {
      const vp = /value-value="([\d.]+)"[^>]*>[^<]*<\/span> votes \(<span[^>]*value-value="([\d.]+)"/.exec(chunk);
      const link = first(/<a class="link"[^>]*>([^<]+)<\/a>/, chunk);
      const label = link || first(/option__details">\s*<span>([^<]+)<\/span>/, chunk) || '';
      const m = /^(.*) \((\d{4})\)$/.exec(decode(label));
      return {
        title: m ? m[1] : decode(label),
        year: m ? m[2] : '',
        poster: bigPoster(first(/<img src="([^"]+)"/, chunk)),
        votes: vp ? Number(vp[1]) : 0,
        pct: vp ? Number(vp[2]) : 0,
      };
    }).filter((o) => o.title);
  }
  return detail;
}

function parseSchedule(html) {
  const tz = first(/data-timezone="([^"]+)"/, html) || SITE_TZ;
  const sessions = [];
  for (const m of html.matchAll(/class="tv-guide__session"\s*data-start="([^"]+)"\s*data-end="([^"]+)"([\s\S]*?)(?=class="tv-guide__session"|<\/main>)/g)) {
    const body = text(first(/tv-guide__card-body">([\s\S]*?)<\/div>\s*<\/div>/, m[3]) || '');
    sessions.push({
      start: zonedToUtc(m[1], tz),
      end: zonedToUtc(m[2], tz),
      events: body && !/No events scheduled/i.test(body) ? body : '',
    });
  }
  return { tz, sessions };
}

// ---------- refresh + cache ----------
let cache = null;
let refreshing = null;
let lastError = null;

const CACHE_VERSION = 3; // bump when the feed's shape changes

try {
  const disk = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
  if (disk.version === CACHE_VERSION) cache = disk;
} catch { /* first run */ }

async function refresh() {
  const prev = cache || {};
  const details = { ratings: { ...(prev.details?.ratings || {}) }, polls: { ...(prev.details?.polls || {}) } };

  const ratingsList = (order) => get(`/api/page/ratings?page=1&order=${encodeURIComponent(order)}`).then(parseRatingCards);
  const [schedule, ratingsPage, best, worst, pollsPage, ...historyPages] = await Promise.all([
    get('/schedule').then(parseSchedule),
    ratingsList('endTime,DESC'),
    ratingsList('average,DESC'),
    ratingsList('average,ASC'),
    get('/api/page/polls').then(parsePollCards),
    ...Array.from({ length: HISTORY_PAGES }, (_, i) => get(`/api/page/history?page=${i + 1}`).then(parseHistory).catch(() => [])),
  ]);
  const history = historyPages.flat().filter((e, i, all) => all.findIndex((o) => o.id === e.id) === i);

  // Detail pages: always re-read the newest few (they may still collect votes),
  // keep the rest from cache since finished polls do not change.
  const wantRatings = [...new Set([...history.slice(0, 10).map((h) => h.ratingId), ...ratingsPage.slice(0, 8).map((r) => r.id)])].filter(Boolean);
  const wantPolls = pollsPage.slice(0, 6).map((p) => p.id);
  const jobs = [];
  wantRatings.forEach((id, i) => {
    if (i < 3 || !details.ratings[id]) jobs.push(get(`/rate/${id}/results`).then((h) => { details.ratings[id] = parseRatingDetail(id, h); }).catch(() => {}));
  });
  wantPolls.forEach((id, i) => {
    if (i < 2 || !details.polls[id]) jobs.push(get(`/poll/${id}/results`).then((h) => { details.polls[id] = parsePollDetail(id, h); }).catch(() => {}));
  });
  await Promise.all(jobs);
  // Keep the cache file small: only details still referenced.
  const keepR = new Set([...wantRatings, ...ratingsPage.map((r) => r.id)]);
  for (const id of Object.keys(details.ratings)) if (!keepR.has(id)) delete details.ratings[id];
  for (const id of Object.keys(details.polls)) if (!wantPolls.includes(id)) delete details.polls[id];

  cache = { version: CACHE_VERSION, fetchedAt: Date.now(), schedule, ratings: ratingsPage, best, worst, polls: pollsPage, history, details };
  fs.mkdirSync(path.dirname(CACHE_FILE), { recursive: true });
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));
  lastError = null;
  return cache;
}

function startRefresh() {
  if (!refreshing) {
    refreshing = refresh()
      .catch((error) => { lastError = error.message; console.error(`dinkdonk.mov: ${error.message}`); })
      .finally(() => { refreshing = null; });
  }
  return refreshing;
}

// Stale-while-revalidate: answer from cache, refresh in the background.
async function data() {
  if (!cache) await startRefresh();
  else if (Date.now() - cache.fetchedAt > REFRESH_MS) startRefresh();
  if (!cache) throw new Error(lastError || 'dinkdonk.mov unreachable and no cached data yet');
  return { ...cache, stale: Date.now() - cache.fetchedAt > REFRESH_MS * 2, error: lastError };
}

// "Have we watched X?" for the !watched chat command.
const searches = new Map();
async function search(q) {
  const key = q.toLowerCase();
  const hit = searches.get(key);
  if (hit && Date.now() - hit.at < 10 * 60 * 1000) return hit.result;
  const rows = parseHistory(await get(`/api/page/history?search=${encodeURIComponent(q)}`));
  const result = { q, more: rows.length >= 25, entries: rows };
  searches.set(key, { at: Date.now(), result });
  if (searches.size > 200) searches.delete(searches.keys().next().value);
  return result;
}

module.exports = { data, search, _parse: { parseHistory, parseRatingCards, parseRatingDetail, parsePollCards, parsePollDetail, parseSchedule } };
