# Brief 38 (PAGE work): auditorium - zoom director + control panel, like the lobby

This brief is page code, not rendering. You MAY edit exactly these files: `standby/auditorium.html`,
`standby/control.html`, `standby/standby-server.js` (only if the control routes need it). Claude will not touch them
while you work. Read `standby/roxy.html` (the lobby) first: it already has both features and the auditorium must
behave the same way (reuse its code and naming; match the surrounding style and comment density).

## Context
`standby/auditorium.html` = scene 2 (inside the cinema while the picked film downloads). Background + 159 depth slices
from `roxy3d/qa11/cinema_draft_10.png` / `cinema_layout_10.json` (`page_layers`), entrance door animation, chatters
(DOM emotes) walk in through the tunnel and sit; bubbles; DGG flair colours and emote facing come from shared/core.js;
emote choice from shared/cinema.js. Options already: draft=, everyone=1 / tag=, live=1, screen=green.

## 1. Zoom director (port from roxy.html: "camera + zoom director", director=, zoom=, keys F/R/W/D)
- Everything in the world zooms/pans together (bg, slices, door, walkers); speech bubbles stay screen-sized and
  follow their speaker, exactly as in the lobby.
- Wide shot most of the time; every ~2-3 min (director=<seconds>, default like the lobby) the camera follows the
  next arriving chatter from the entrance door through the tunnel exit to their seat, holds a moment on them seated,
  then eases back to the wide shot. Same easing, zoom (zoom= default 1.85, clamp 1.2-3) and edge clamping as the
  lobby. While following someone inside the tunnel, frame the tunnel mouth (they are hidden there).
- Never frame outside the 1920x1080 art. Keys F (follow next), R (release), W (wide), D (director on/off) as in the
  lobby; director=0 disables.
- Art resolution: the lobby chooses 1x / @2x art by output scale x zoom headroom (`dpr()`); do the same here, using
  `file_2x` entries in `page_layers` (bg `image_2x`, slices `file_2x`, door `file_2x`) WHEN they exist - the 4K set
  is being rendered in parallel; until then fall back to the 1x files silently.

## 2. Control panel (control.html + /ctl/ SSE, as the lobby)
- The auditorium registers with the control server like roxy.html (`/ctl/events`, `/ctl/state` with a page id) and
  shows up in control.html. control.html must make clear which page is which (lobby vs auditorium) and offer, for the
  auditorium: director on/off, follow next arrival, wide shot, zoom level, reset (everyone leaves: clear all chatters,
  seats and bubbles), and whatever lobby controls also make sense here (e.g. remove one chatter by nick, test
  arrival). Commands for one scene must not trigger the other scene's handlers by accident.
- Keep the lobby's controls working exactly as before.

## Rules
- Keep the page working at every step; no console errors. Do not change shared/core.js or shared/cinema.js (if you
  need something there, write it in your report instead). Do not touch roxy.html except reading it.
- Test it yourself (headless Edge or Chrome is fine; `?everyone=1&relay=127.0.0.1:1` + `SB.say('nick','EMOTE text')`
  in the console gives fake arrivals without live chat). The standby server is running on 127.0.0.1:18770; do not
  stop it (it reloads nothing by itself: if you change standby-server.js, say so - Claude restarts it).
- Report in `roxy3d/qa11/PAGE-38.md`: what you ported, what differs from the lobby and why, how you tested. STATUS
  line, stop.
