# Brief 44 (PAGE): auditorium QA + code review, and arrival-burst crowding

`standby/auditorium.html` was written in several passes tonight (Claude: base page, routes, seats, speech, facing,
walk animation; you: director/control PAGE-38, names/neighbours PAGE-40, pre-show/phases PAGE-41, dim crossfade
PAGE-43). You may edit `standby/auditorium.html` and `standby/control.html` only. Same rules as before (no shared/*.js
changes, don't use port 18780, server on 18770 stays up). Report `roxy3d/qa11/PAGE-44.md`, STATUS.

1. **Code review + QA of the whole page** as it will run for hours in OBS at 1080p/1440p/4K with live DGG chat
   (dozens to 100+ chatters, bursts, bans/mutes, the same nick chatting many times, emotes that fail to load, very
   long messages, the control panel's reset / remove / test arrival, phases switching back and forth, director
   following someone who gets removed or reset). Look for real bugs: leaks (DOM nodes, timers, listeners, growing
   maps/arrays), state left behind after reset/remove, seats never freed, z-order mistakes, bubbles/names stuck, NaN
   positions, errors in the console, performance hot spots per frame (layout thrash, querySelector in the loop, 300+
   images). Fix the real ones; list what you checked and decided not to change.
2. **Arrival bursts:** when 30+ chatters arrive within a minute, they pile up on the tunnel approach / cross-aisle and
   their names overlap into a mess. Keep a minimum spacing along the route (walkers wait behind the one in front,
   like the lobby's `blockedAhead`), and keep names of walkers short-lived (show on emerging from the tunnel for a few
   seconds and when followed/talking, as the lobby's rule) so a crowd stays readable. Arrival order and the
   one-at-a-time door stay as they are.
3. When everything is full (135 seats), say what happens now and make it sensible (e.g. newcomers wait at the back,
   or the longest-idle seated chatter leaves through the tunnel to make room) - choose the most natural, document it.

STATUS line, stop.
