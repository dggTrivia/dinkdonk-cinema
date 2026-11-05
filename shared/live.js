/*
 * ?live=1 - reloads the page a moment after its file (or a shared script) changes on disk,
 * so a browser window or OBS source shows edits without touching it. Does nothing otherwise.
 */
(() => {
  'use strict';
  if (new URLSearchParams(location.search).get('live') !== '1') return;
  const files = [location.pathname, 'shared/core.js', 'shared/cinema.js', 'shared/base.css'];
  const seen = new Map();
  const changed = new Map();   // a change must be seen twice in a row (a file caught half-written)
  async function check() {
    for (const f of files) {
      try {
        // a restarting server's 404/500 page is not a change (it reloaded the scene and lost everyone; QA 05 Nov)
        const res = await fetch(f, { cache: 'no-store' });
        if (!res.ok) continue;
        const text = await res.text();
        if (seen.has(f) && seen.get(f) !== text) {
          if (changed.get(f) === text) { location.reload(); return; }
          changed.set(f, text);
          continue;
        }
        changed.delete(f);
        seen.set(f, text);
      } catch { /* server restarting - try again next round */ }
    }
    setTimeout(check, 1500);
  }
  check();
})();
