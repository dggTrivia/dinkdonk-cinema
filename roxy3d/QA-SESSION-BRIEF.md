# Brief for the QA + performance session (standby screens)

You are the QA and performance session for the DINK DONK cinema standby screens. DO NOT start any work yet: the owner
will set your goal in this session. For now, read this background (and skim the files it names, read-only), then
reply in one or two lines that you're ready and what you'd check first.

Remit once the goal is set:
1. Bug fixes and graphical errors/glitches: wrong overlaps, clipping, wrong depth sorting, malformed or misaligned
   sprites, flicker, broken states.
2. Performance: better frame rate and smoother frame times with minimal or no loss of fidelity (measure before/after
   with the same settings).

## Background
Project: `C:\Users\maxsp\Desktop\Angelthump_H264_4K\standby` - OBS standby screens for the d.gg / DINK DONK movie nights.
- Lobby: `standby/roxy.html` (isometric rainy-night cinema; pre-rendered art pack `standby/roxy3d/out10/` with
  `manifest.json`; chatters walk in as emotes with umbrellas, queue, buy tickets, talk in bubbles; depth-sliced
  traffic; WebGL extra-rain/weather layer `#rain2`; mist samples behind ?mist=, off by default; crowd control
  ?crowd=). The header comment lists the URL options.
- Auditorium: `standby/auditorium.html` (owned by the "Cinema Screen Map" session).
- Shared: `standby/shared/core.js`, `cinema.js`, `base.css`, `emote-facing.json`. Control panel `standby/control.html`.
- Server `standby/standby-server.js` on http://127.0.0.1:18770 (reads files fresh: page edits only need a reload;
  only the owner restarts the server). Remote view: http://100.69.76.4:18780/roxy.html?everyone=1 (Tailscale proxy,
  leave it running).
- Live OBS scene collection "Moobies 1440p": never edit it, only copies. The stream runs at 1440p.

## Coordination
The "Lobby Map" session owns `roxy.html` feature work and is on the rain/weather (`#rain2`, `stepWeather`, `RAIN2_FS`,
mist block) and a rendered rain draft (Codex BRIEF-52, staging `roxy3d/out10f/`). Before editing roxy.html, message
Lobby Map about what you'll touch; for auditorium.html, message Cinema Screen Map. Keep edits small and reviewable.

## Testing tools
Headless Edge (GPU on) via CDP node scripts in
`C:\Users\maxsp\AppData\Local\Temp\claude\C--Users-maxsp-Desktop-Angelthump-H264-4K\e37339c8-04cb-4c89-b82c-99e770541384\scratchpad\perf\`:
`perf-roxy.mjs <url> <w> <h> <secs> <label>` (fps, p50/p95/p99, long tasks, layers, errors; fills the room via
SB.say), `trace-roxy.mjs` (image decodes), `shot-roxy.mjs <url> <out.png> <W> <H> <x> <y> <w> <h>`, `crowd.mjs`
(chat flood). Copy them to your own scratchpad. Use ?tag=perfhost&director=30 for perf, ?everyone=1 for looks
(never demo=1 for the owner). Machine: RTX 3050 6GB laptop; baseline headless 1440p ~53-62 fps, 0 errors.

Perf history: 4K wet prop-loop sheets (~590 MB decoded) overflowed Chrome's GPU decode cache, so `wet_*` loops stay
1x unless ?wet2x=1; figure caps 40/55 (80 DOM max); bubbles use springs; light loop and rain_fg are 24 fps VP9 WebM
with plus-lighter blending.

## Art and rules
Codex CLI (`codex exec -m gpt-6-astra -s workspace-write --skip-git-repo-check -o <file> "<prompt>" < /dev/null`,
in the background from `standby/roxy3d`) does renders; it writes only inside `standby/roxy3d/`, local GPU, no cloud.
Any art change = one draft image shown to the owner first; full renders only when the owner says so.
Never touch files outside `standby/`; back up before big edits (`standby/roxy3d/cloud/backup-run2/`); log changes in
`standby/roxy3d/PROGRESS.md`; don't kill or restart the standby server; no accounts, passwords, tokens or payment
details. English, dates like "4 Nov 2026".
