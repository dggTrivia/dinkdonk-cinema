# QA + performance report: night of 4-5 Nov 2026

Owner's goal: overnight QA (glitches) and performance for the lobby (`roxy.html`) and the auditorium
(`auditorium.html`), keeping full render resolution. All changes are in **copies**, never the live pages:

- `standby/roxy-qa.html` (from roxy.html as of 4 Nov 2026 21:55; original saved as `roxy3d/qa-night/roxy.orig.html`)
- `standby/auditorium-qa.html` (from auditorium.html as of 4 Nov 2026 21:55; `roxy3d/qa-night/auditorium.orig.html`)

To try a copy: `http://127.0.0.1:18770/roxy-qa.html?everyone=1` (same options as the real page).
To adopt a fix: each one below lists exactly what changed so the Lobby Map / Cinema Screen Map session can port it.

## Summary (for the morning)

**Security, please read: anyone on your home Wi-Fi (or tailnet) can currently send control commands to the live
scenes through the running LAN/Tailscale view proxies (fake chatter text on stream, remove, reset). Confirmed with a
harmless probe. A view-only proxy copy is ready (fix 18); until then, stop lan-proxy when you don't need it.**

Everything is in two copies; the live pages are untouched. Ready-made patches (each verified to turn today's live
file into the copy exactly): `roxy3d/qa-night/roxy-qa.patch`, `roxy3d/qa-night/auditorium-qa.patch`.

| | live page | copy |
|---|---|---|
| Lobby, 1440p, real chat, Edge | 54.8 fps (held at ~52 Hz by the blended rain video) | **105 fps** |
| Auditorium, ~95-137 seated, uncapped | 52 fps, p99 45-52 ms (visible stutter) | **114-146 fps, p99 19 ms** |

Most important fixes:
1. Lobby: following a bus/taxi rider froze the camera and hid every speech bubble for the rest of the stream
   (reproduced on the live page). Fixed.
2. Lobby: the full-screen rain video's blend mode capped the frame rate; now drawn in the existing WebGL rain
   pass, pixel-identical.
3. Auditorium: an identity `filter: brightness(1)` on every slice and emote made it re-render expensively;
   now only applied while dark. Pixel-identical.
4. Speech bubbles no longer slide through each other (lobby, ~90 % less overlap) or pile up in the corner while
   zoomed (auditorium); names no longer print on top of each other.
5. Several stuck/leak bugs from code reviews: invisible walker blocking the usher gate, jannies stopping for good,
   the auditorium dropping to ~6 fps after any error, download polling stopping, queue locking up when full, etc.

Also: 4K (3840x2160) holds 105 fps in both copies (live: 55 / 80); a 60-minute soak showed no leaks or drift.

**Confirmed in real OBS 32.2.2** (portable test copy, your OBS untouched): the live lobby drops/doubles ~53 frames a
minute and the live auditorium with ~60 people 145 (42 a full frame late, 1.48 CPU cores); both copies run a perfect
60 fps with 0 late frames, the auditorium at half the CPU. The 4K light loop costs no extra CPU in OBS (hardware
decode), so keep it. New opt-in `?maxres=<height>` (e.g. 1080) caps the art resolution if you ever want it (fix 17).

Your choices (nothing changes by default; `?maxres=1080` also available): `?leave=<minutes>` lets a full auditorium turn over (fix 15);
`?slidefade=seq` stops the pre-show slides cross-fading (fix 16). The 4K light loop: measured in OBS, no extra CPU
(hardware decode), so nothing to choose there.

## How it was measured

- Headless Edge with the GPU on (RTX 3050 laptop), 2560x1440 (the stream size), real DGG chat only (`?everyone=1`,
  no fake chatters), `ctl=0` so test pages never show up in control.html, director zooms on.
- Each run: 30-60 s warm-up while chat fills the room, then frame times in 15 s windows (fps, p50/p95/p99, long
  tasks, main-thread ms), GPU load and whether Blender (other sessions' renders) was running at the same time.
- "Uncapped" = Edge started without its frame-rate limiter, showing the real cost per frame (headroom).
- Look-alike checks: both pages frozen on the same clock and video frame, people hidden, pixel diff.
- Tools (scratchpad, not part of the project): `qa.mjs` (perf), `trace.mjs` (thread profile), `audit.mjs`
  (automatic glitch audit with close-up screenshots), `snap.mjs` + `diff.mjs` (frozen frame + pixel diff).

## Lobby, after rebasing on roxy.html 22:10 (with BRIEF-53 umbrella / vehicle rain)

Capped, real chat, director every 30 s: live page 54.8 fps (p99 20.8 ms), copy **105.1 fps (p99 10.7 ms)**. The new
vehicle roof-rain / spray / wake loops cost ~1 ms a frame uncapped (256 vs 360 fps with them hidden) and do not
bring the ~52 Hz cap back (that was only the blended <video>).

## Baseline (lobby, before any change)

| run | fps | frame p50 / p99 | walkers | notes |
|---|---|---|---|---|
| capped, Blender idle | 55.1 | 19.3 / 20.8 ms | ~50 | GPU 10 % busy, main thread ~17 % busy |
| uncapped, Blender idle | 434 | 2.3 / 7.4 ms | ~48 | the page itself costs ~2.3 ms a frame |
| capped, empty lobby (no chat) | 54.0 | 19.2 / 20.5 ms | 8 | same cap without any chatters |

The lobby never reached 60 fps whatever the load: a steady 19.2 ms per frame (~52 Hz), in headless and in a normal
visible Edge window alike.

## Fixes

### 1. Lobby: foreground rain video drawn inside the extra-rain WebGL pass (roxy-qa.html) - DONE, verified

**Problem.** `#rainfg` (the baked rain_fg.webm loop, full screen, `mix-blend-mode: plus-lighter`, above everything)
held Edge at ~52 fps. Bisected: no videos -> 103 fps; both videos `normal` blend -> 105 fps; only the base light loop
`normal` -> still 54; only `#rainfg` `normal` -> 105.8 fps. Chromium flags (vsync, video decode, surface layers)
made no difference; it is the blended video on top of the page.

**Change.** When the extra rain (#rain2, WebGL, already plus-lighter) is on, the rain_fg video is uploaded as a
texture (only when it has a new frame, 24 fps) and added in the same shader, unmasked, exactly where the video used
to add it. The `<video>` keeps playing as the texture source but is invisible (`opacity 0`, `normal` blend). With
`?morerain=0` or no WebGL the old video path is used unchanged. If the video dies, the existing fallbacks still run.

Code (roxy-qa.html): `fgPlaying` / `fgToRain2()` / `uploadFg()` next to the rain2 setup; texture unit 3 (`uV`) and
`uVid` in `RAIN2_FS` (`fg` added before the mask test and to `col`); the rain2 draw in `frame()` also redraws on a
new video frame; setupArt's rain_fg `playLoop` callbacks set `fgPlaying`.

**Result** (1440p, real chat ~48 people): **55 -> 105 fps** capped (measured with a Blender render running at the
same time), composited area 25.4 -> 21.5 Mpx per frame. Look: frozen frame, old vs new page, full frame pixel diff
mean 0.003, max 3/255 (the rain video alone contributes up to 40/255 there, so the test does see it).

### 2. Lobby: speech bubbles no longer slide through each other or bob with every hop (roxy-qa.html) - DONE, verified

**Problem.** The automatic audit (DOM check every 2 s) caught 77 overlapping speech bubbles in 6 min, plus bubbles
cut off at the top edge while zoomed. Cause: target spots never overlap, but every bubble glides to its spot on a
spring, and the stack reshuffles all the time (new bubble, dropped bubble, speakers hopping change the order), so
gliding bubbles pass through each other; a glide down from a high stacked spot during a camera pan went off-screen.
Bubbles also bobbed up and down with every hop of their speaker (and so did every bubble stacked above them).

**Change** (`layoutBubbles()`, `placeBubble()`):
- the bubble anchors to the speaker's standing height (no `w.lift`): no bobbing with hops;
- each bubble's *drawn* rectangle is checked against the bubbles already drawn this frame; on a real overlap it is
  pushed up just above (`pushOff`), at most 900 px/s (a quick slide, never a snap), and eases back down on its own
  spring only while the way down is free (no push/relax wobble); a 2/6 px dead band keeps small moves from pushing;
- a new bubble claims its height while it fades in (0.3 s), so the one above is eased up, not shoved;
- never drawn above the top edge.

**Result** (2 min of real chat, old and new page side by side):

| | old | new |
|---|---|---|
| overlap time (bubble pairs) | 48.8-76 s | 6-9.5 s |
| longest overlap | 1.1-1.5 s | 0.2 s |
| direction reversals per bubble per s, p50 / p90 | 2.0 / 2.8-3.0 | 0.8-1.0 / 2.6-2.8 |
| audit: overlaps caught | 0.22 / s | 0.05 / s, none off-screen |

Variants tried and dropped (numbers in the scratchpad): oldest-first placement (worse), push that rewrites the
spring (wobble), display-only clamp (snaps when released).
Side note: with the hop no longer moving the bubble, a speaker in an emote combo (26 px jumps) can touch the
bubble's tail for a moment.

### 3. Auditorium: no identity filters on slices and emotes (auditorium-qa.html) - DONE, verified

**Problem.** Seating phase with ~95 people: ~52 fps *uncapped* (the page's real limit), frame p99 45 ms, 158 frames
over 33 ms per 90 s: visible stutter. GPU main thread saturated with raster. The whole room (background, 4664 slice
pieces, every chatter) is one compositor layer by design (depth sorting), so every moving or animated emote repaints
tiles of it. Elimination: people hidden 66 -> 330 fps; emote animations paused 66 -> 140; and the cause:
`#bg, .slice, .sheet { filter: brightness(1) }` and the same on `.w .em` / `.w .item`, kept for the 6 s lights-down
fade. An identity filter still makes every slice/emote its own offscreen pass each time its tiles re-raster.

**Change** (CSS only): no filter at rest. The 6 s `transition: filter` stays on emotes/items (fades from `none` to
`brightness(.5)` and back, verified: none -> 0.98 -> 0.76 -> 0.5 and back to none) and on the art only where there is
no dim art (`#stage:not(.has-dim-art)`), where the `brightness(.45)` dimming still applies.

**Result** (uncapped, real chat, run one after the other):

| phase | original | copy |
|---|---|---|
| seating, ~95 people | 52.2 fps, p99 45.3 ms, 158 frames > 33 ms | **114.5 fps, p99 18.8 ms, 0 > 33 ms** |
| lights down (`phase=dim`) | 219 fps | 311 fps |
| director zooms every 30 s, filling to a full house (137) | 52.6 fps avg, worst 15 s 40.7, p99 51.8 ms | **146 fps avg, worst 105, p99 19.5 ms** |

Look: frozen frame with every one of the 4664 slices forced visible, people hidden: pixel diff mean 0.001, max 10/255
on a few pixels (none over 8 in 0.0005 %).

### 4. Auditorium: the door cutout mask only on the slice pieces it touches (auditorium-qa.html) - DONE

When the entrance door animates (every arrival), `doorCutout()` put a `mask-image` (5-8 properties) on every piece
of the 21 slices listed in `static_slice_cutout`: 497 pieces + 497 dim twins. Only 95 (+95) intersect the cutout
rectangle; outside it the mask is fully opaque, so those masks did nothing but cost style/paint work on every
opening. Now only the intersecting pieces go in `doorSlices` (fallback: all of them if the cutout has no rect).
Identical by construction. No fps change measurable on its own (fix 3 was the bottleneck then); it removes ~800
masked elements per door opening.

### 5. Auditorium: neighbours' names no longer print on top of each other (auditorium-qa.html) - DONE, verified

Names show for a few seconds after someone sits down (and always for jannies / the followed chatter). Neighbours who
sat down together showed both names on the same spot, unreadable (audit: 27-36 clashes in 4 min). Now `step()` only
decides whether a walker *wants* its name (`nameWant`, position `nx/ny`); `showNames()` (called from `tick()` after
every walker moved) shows them in order (followed, jannies, then the most recent arrival) and a name that would
overlap one already shown waits, fading out with the existing 0.6 s transition. Name widths are measured once.
Audit, old vs new side by side: **27 -> 5** and **36 -> 3** clashes in 4 min (the rest are names mid-fade).

### 6. Auditorium: speech bubbles of chatters outside the zoomed-in view are hidden (auditorium-qa.html) - DONE

While the director is zoomed in (1.85x), bubbles of speakers outside the view were clamped into the screen's corner
(audit: several at x=11, y=11 on top of each other). Now such a bubble is hidden (`visibility`) until its speaker is
in view again; unlike the tunnel case its clock keeps running, because the camera can hold on the film screen for a
whole film and hour-old bubbles must not pop up when the lights come back up.

### 7. Lobby + auditorium: logic bugs from a code review, each checked in the code before fixing

Two independent read-only reviews (one per page) looked for leaks, stuck states and per-frame exceptions. Every
finding below was confirmed in the code; the first one was also reproduced live.

**Lobby (roxy-qa.html)**
- **Camera freezes for good, and all speech with it, after following a bus/taxi rider** (`stepCamera`). Vehicles
  keep their road position in `.lane`; the follow used `P(veh.u, veh.v, 40)` (`.v` undefined), so the camera went
  NaN and could never recover. The browser ignores the invalid transform, so the view just froze mid-zoom;
  `toScreen()` returned NaN, `onScreen()` was false for everyone and every bubble waited forever. **Reproduced**:
  pressing F every 15 s on the live page, the camera froze at scale 1.73 with 0 bubbles for the remaining 2+ min of
  busy chat. Fixed (`veh.lane`) plus a guard: a non-finite camera goes back to the wide shot. Copy: 16 follows in
  4 min, never froze.
- **An invisible "ghost" could stop the usher gate for good** (new `retire()`). The 80/HARD_CAP removal, the
  panel's "remove" and the run-over path faded a walker out without taking it out of the ticket line, snack line,
  gate line or ticket window. If the line moved during the fade it got a new plan, lived on invisibly and, as head
  of the gate line (`serveGate` waits on a `removing` head), the gate stopped. `retire()` clears every line/slot.
- **Jannies stopped coming** (`removeWalker`). Only clocking off removed a janny from `jannies`; the 80-figure purge
  (oldest first, jannies stay longest) and the panel left stale entries, and after four no mod got a janny again.
- **The bus left the people waiting at the stop** (`waitBus` / `stepTraffic`). They only become boarders the frame
  after the last rider is off; if the dwell had passed, the bus left in that same frame (50-100 s wait for the next).
  The bus now also waits for anyone at the stop (`waitingBus`, same 12 s limit).
- Art without a bus: people who gave up the ticket line now walk off along the sidewalk instead of waiting forever.

**Auditorium (auditorium-qa.html)**
- **One exception would drop the scene to ~6 fps in slow motion for the rest of the stream**: `frame()` called
  `tick()` before scheduling the next frame. Now schedules first and catches (as the lobby does).
- **Download polling stopped after any error** in the result handling, and with it the automatic dim/film phases.
  `pollDownload()` now always reschedules.
- **Leak:** `chatEmotes` (every chat message's emotes) was only trimmed while a download showed; hours without one
  grew it without end. Trimmed on every message now.
- **A ban by a mod who had walked in as a chatter** (no free janny) replaced that seated figure in `walkers`: it
  stayed frozen in its seat for good, seat taken, drawn through the rows. That figure now goes first (as
  `onModMessage` already did).
- **A banned chatter could wait in their seat forever** if the janny called in to escort them was removed on the way.
  They now leave on their own (`escortT`, `standUp`).
- **Feature lookup (poster/IMDb) never retried after a failure** although the code meant to; retries after 1 min.
- Small: no phone glow while waiting to be led out; a janny clocking off from the cross aisle no longer walks down
  to the front and back first; no usher kick once the lights are back up.

Smoke tests after these: lobby 4 min with F every 15 s (no freeze, 0 errors); auditorium 4 min lit and 4 min dark
(`qb=0.95`), 0 errors.

## Soak test (20 min each, real chat, side by side)

No leaks: lobby heap 3-11 MB, ~1100 DOM nodes, ~48 people throughout; auditorium heap 5-17 MB, ~6600 nodes, full
house (137) from minute 5. Capped headless fps stayed ~105 for both, except while I ran extra test pages on the
same GPU (four 1440p pages at once), which is not a page issue.

### 8. Lobby: names one at a time, bubbles kept on screen while gliding (roxy-qa.html) - DONE

- The auditorium's name rule (fix 5) ported: `drawFigure()` sets `nameWant`, `showNames()` (in `frame()`, before
  `layoutBubbles`) shows names in order and fades out one that would overlap a name already shown. Lobby clashes
  are rare (about 1 in 5 min either way), so this mostly guards busy moments.
- A bubble could still end up past the left/right edge while its sideways offset eased and its speaker walked on
  (audit: 30 px past the right edge). The drawn x is now clamped to the stage like the top edge. Audit after:
  5 min, director every 30 s: no bubble off-screen, 0 errors.

### 9. Auditorium: the queue outside a full house no longer locks up (auditorium-qa.html) - DONE

The hall has 135 seats and fills in about 5 minutes on a busy night; nobody leaves on their own, so later chatters
wait in the arrivals queue (max 270). Two problems: queued entries never expired (whoever got a seat freed by a ban
walked in hours later with an hours-old message), and a full queue refused every new nick, so the queue stayed the
first 270 chatters for the rest of the night. Now each queued arrival carries the time of their last message
(refreshed when they chat again), anyone quiet for 10 min leaves the queue (checked once a second in `tick()`), and
a full queue drops the longest-quiet entry to let a new chatter in. Smoke test: 2.5 min, 0 errors.

Not changed (a design call for the owner): nobody ever leaves a full hall except through bans/kicks, so after ~5 min
the audience is fixed for the night. An option would be that chatters dozing for a long time get up and leave when
people are waiting outside.

### 10. A second, independent review of these patches found 6 mistakes of mine - all fixed and re-tested

- Lobby rain pass: the "new video frame" test compared `currentTime`, which changes on every display frame, so the
  pass redrew (and re-uploaded the 1080p texture) every frame. It now keys on the 24 fps frame number, and while
  the video plays its frames are the steps of the whole pass: **24 draws/s** (measured; was 48-60+). If the video
  stalls, the page clock takes over after 120 ms (measured 23.75 draws/s with the video paused), so the extra rain
  never freezes. Uncapped lobby 256 -> 350 fps. Pixel diff vs the live page still max 3/255.
- Lobby rain pass: a lost WebGL context (GPU reset/driver update) now shows the rain_fg video on its own again.
- Lobby bubbles: with the hop no longer moving the bubble, a hopping head poked into its own bubble when zoomed in
  (13 px hop x 1.85 zoom > the 16 px gap). The anchor now leaves a hop's height (bubbles sit 13 world px higher).
- Auditorium: the 4-bubble cap could drop the one visible bubble for off-view (hidden) ones; hidden ones go first.
- Auditorium: the usher's (invisible, zero-width) name could block a neighbour's name; the usher is left out.
- Auditorium escort: a mod's chatter figure was removed even when no janny could be called (all spots taken).

### 11. Shared scripts (core.js, cinema.js, live.js): fixed copies + patch, not applied

The live pages and both QA copies still load `shared/`. Fixed copies are in `roxy3d/qa-night/shared-qa/`, patch
`roxy3d/qa-night/shared-qa.patch`. Tested by having the test browser serve them in place of `/shared/*.js` (both
pages, 2.5 min each, real chat: 0 errors) plus a targeted test against the originals:

- **live.js (`?live=1`): a server restart's 404/500 page reloaded the scene** (everyone gone): reproduced, two 500s
  -> reload. Now non-OK answers are ignored and a change must be seen twice in a row: no reload.
- **core.js: a failed emote list at page load stayed failed all night** (35 fallback names as text pills).
  Reproduced with one 503. Now retried every 30 s: 35 -> 325 real emotes 30 s later, emote CSS on.
- core.js: an emote stylesheet arriving after the 8 s wait now triggers a re-measure (sizes were text estimates).
- core.js: a relay that stays connected but goes silent for 3 min is dropped and reconnected (it stayed "live").
- core.js: `MSG null` / `NAMES null` frames no longer throw.
- cinema.js: one failing rooms handler no longer skips the others; odd data.json keeps the last good data.

Checked, no problem: on connect the DSA relay sends one HISTORY frame (core.js ignores it) and only new MSG frames
after that (measured: all MSG timestamps newer than the connection), so a reconnect does not repeat walk-ins.
Not changed (reported only): `fitCanvas()` adds a permanent resize handler per call (only the old
hall-*.html pages call it repeatedly).

Note: the "Moobies 1440p" scene collection has no standby browser sources yet, so I could not see whether OBS will
use `?live=1`. Without the live.js fix, leave `live=1` out of the OBS URLs.

### 12. Lobby: the light loop matches the base art with the director off (roxy-qa.html) - DONE

`setupArt()` chose the 4K or 1080p light loop with `dpr()` before the stage was mounted (scale still 1). With the
director on, the zoom factor hid this; with `director=0` at 1440p the 1080p loop ran over the 4K base image, which is
not its exact complement (the comment in the code says they must match). Now chosen from the window size. Checked:
live page at 1440p, director=0: loop 1920 wide over base@2x; copy: loop 3840 over base@2x; copy at 1080p: loop 1920.

## OBS note: video decode cost

The lobby plays a 4K VP9 light loop (with the director on, or from 1440p). Edge decodes it on the GPU; OBS's own
browser may decode in software. Measured, whole Edge, lobby at 1440p, director on:

| | hardware decode | software decode |
|---|---|---|
| 4K light loop (default) | 0.58 CPU cores | **1.60 cores** |
| 1080p light loop (`?loop2x=0`) | 0.50 cores | 0.76 cores |

If OBS's stats show the browser source using a lot of CPU, `?loop2x=0` saves about 0.85 core, at the price of a
softer light loop in zoom-ins. Not changed: the owner's call.

**Answered in real OBS (see "Measured inside OBS" below): OBS 32.2.2's browser decodes it in hardware, so the 4K
loop costs no extra CPU there (0.77 vs 0.79 cores with the 1080p art). Keep the 4K loop.**

### 13. A third review of the newest changes: 2 more fixes, 1 gap closed

- Lobby rain pass: stepping on the video's frames but drawing at the page clock's 24 fps step let the two clocks
  drift (a rain step could repeat, then skip). New video frames now come from `requestVideoFrameCallback` (the
  browser's own "a new frame is ready", available in OBS's browser too; the frame-number test stays as fallback) and
  the pass draws at the real time. Measured with the invisible video: 24 uploads and 24 draws per second.
- Auditorium escort: a mod banning/muting themselves would still freeze their own figure; they now just walk out.
- shared-qa/core.js: a failed emote *stylesheet* is now retried every 30 s too (tested with one 503: emote CSS on
  after the retry; the original stays text pills all night).

Known, not changed (minor): resizing the OBS source across the 4K/1080p threshold re-picks the base art but not the
light loop (reload the source after changing its size); the silent-relay watchdog would reconnect every 3 min in a
completely silent chat (no messages, joins or quits for 3 min), which only flickers the offline note.

## Final regression (current copies, real chat, 1440p, director on, no Blender on the GPU)

| | fps | frame p99 | errors | memory |
|---|---|---|---|---|
| lobby copy, 6 min | 105.4 | 19.5 ms (2 min run after the last change: 10.7 ms) | 0 | heap 5.9 -> 6.3 MB, nodes flat |
| auditorium copy, 6 min, filling to 136 | 103.0 | 20.5 ms | 0 | heap 5.3 -> 11.8 MB, nodes grow with the audience |
| live roxy.html (same settings, earlier) | 54.8 | 20.8 ms | 0 | |
| live auditorium.html (same settings, earlier) | 61.1 | 30.3 ms | 0 | |

(The only console line in every run is the browser's own favicon.ico 404.)

### 14. Lobby: the light loop also follows a resize (roxy-qa.html) - DONE

Resizing the OBS source across the 4K/1080p line re-picked the base image (`applyArtRes`) but not the light loop,
so the loop ran over a base it is not the complement of. `loopSwap()` (set in `setupArt`, called from the resize
handler) now switches the loop file too, without reloading the page. Tested by resizing the viewport 1080p ->
1440p -> 1080p: live page keeps the 1920 loop over base@2x; copy: 1920 -> 3840 -> 1920 with the base, 0 errors.

## 4K check (3840x2160, director on, real chat)

| | live | copy |
|---|---|---|
| lobby | 54.7 fps, p99 20.8 ms | **105.1 fps, p99 10.7 ms** |
| auditorium | 80 fps, worst 15 s 52, p99 30.2 ms | **104.8 fps, p99 19.2 ms** |

## Tried and rejected: auditorium walkers on their own layers

Giving only the *walking* chatters `will-change: transform` (seated ones stay in the shared layer) was faster in
an interleaved test on the same page (605 -> 816 fps uncapped, +35-64 %), and the zoom collapse an earlier session
saw did not come back. But on a frozen crowd zoomed to 2.7x the layered emotes came out visibly **softer** (Chromium
keeps such layers at the scale they were first drawn at). That is the zoom sharpness the 4K art exists for, so it
is not in the copy. The lobby's walkers already have layers: checked the same way, they stay sharp when zoomed
(stale vs refreshed layers vs no layers looked the same), so nothing to fix there.

### 15. Auditorium: optional turnover for a full house, `?leave=<minutes>` (auditorium-qa.html) - OFF by default

The open design question from fix 9 (a full hall never lets anyone new in) as an opt-in option, so you can try it
without it changing anything by default. With `?leave=<minutes>`, when every seat is taken and people are waiting
outside, the chatter who has been dozing longest (quiet in chat for at least that many minutes; not jannies, the
usher, or whoever the camera follows) gets up with "💤 heading home" and walks out the way they came in, freeing
the seat; at most one every 5 s. Tested with real chat on a 24-seat version of the layout (served by the test
browser, the real layout file untouched), `leave=1&doze=20`: filled in about a minute, then 40 people headed home
and were replaced from the queue over 6 min, 0 errors. A value like `leave=20` would be a calmer setting.

### 16. Auditorium: optional fade-out-then-in for the pre-show slides, `?slidefade=seq` - OFF by default

The other open design question as an opt-in option: the slides change every 8 s with a 0.8 s cross-fade, so for a
moment two slides are half visible on the film screen (a screenshot caught "Now loading 95 %" through the credits).
With `?slidefade=seq` the old slide fades out in 0.4 s and only then the next fades in (0.4 s). Measured, 10 s at
100 ms: seq never shows two slides at once; default showed two in 7 of 100 samples.

## 60-minute soak (both copies side by side, real chat, 1440p, 05 Nov ~04:20-05:25)

| | fps at 15 / 30 / 45 / 60 min | frame p99 | heap | DOM nodes | errors |
|---|---|---|---|---|---|
| lobby copy | 108 / 106 / 106 / 106 | 10.6 ms throughout | 4-13 MB | ~820-1000 | 0 |
| auditorium copy (full house 135-136 from min 15) | 103 / 106 / 106 / 106 | 10.6-19.8 ms | 7-18 MB | ~6500, flat | 0 |

No leak, no drift. The worst 15 s windows (80 / 64 fps) fall in the first minutes, while other test pages shared the
GPU.

## Measured inside OBS itself

A portable copy of the installed OBS 32.2.2 (`roxy3d/qa-night/obs-portable/`, its own config: your OBS settings and
the live "Moobies 1440p" collection untouched) with one 2560x1440 browser source at 60 fps, started with
`--remote-debugging-port`, so the same timing collector runs inside OBS's own browser; OBS's render stats via
obs-websocket (separate port 4466, test copy only); `tools/obsmeasure.mjs`. Real chat, 60 s warm-up, 60 s measured
(05:40, quiet chat, ~15-20 people in the room):

| page in OBS | page fps | frame p99 | frames > 20 ms / > 33 ms in 60 s | browser CPU |
|---|---|---|---|---|
| live roxy.html | 59.1 | **33.3 ms** | **53 / 6** | 0.80 cores |
| roxy-qa.html | 60.0 | 16.8 ms | 0 / 0 | 0.77 cores |
| roxy-qa.html?maxres=1080 | 60.0 | 16.8 ms | 0 / 0 | 0.79 cores |
| live auditorium.html (16 people) | 60.0 | 16.8 ms | 0 / 0 | 0.68 cores |
| auditorium-qa.html (19 people) | 60.0 | 16.8 ms | 0 / 0 | 0.56 cores |
| live auditorium.html, 7 min warm-up (~62 people) | 57.5 | **33.4 ms** | **145 / 42** | **1.48 cores** |
| auditorium-qa.html, 7 min warm-up (~64 people) | 60.0 | 16.8 ms | 0 / 0 | 0.78 cores |

OBS itself never skipped a render frame (60 fps, ~0.2 ms render). So in OBS the live auditorium with ~60 people
judders (42 doubled frames a minute) at twice the browser CPU, and the live lobby drops/doubles frames
(about one in 70 frames is late, some by a whole frame: visible judder on stream); the copy is perfectly smooth. The
4K light loop costs nothing extra in OBS (hardware decode).

## Disk space (found while testing)

At ~05:20 the C: drive had 3.1 GB free (100 % used). The cause was mine: the test browser profiles in my scratchpad
had grown to ~34 GB over the night (GPU/media caches, hundreds of MB per run). Deleted: 37 GB free again. The tools in
`roxy3d/qa-night/tools/` now delete their profiles after every run. The earlier perf session's scratchpad
(`...\e37339c8-...\scratchpad\perf`) holds another ~3.4 GB (28 profiles + traces); not mine, left alone.

### 17. Both: optional resolution cap, `?maxres=<height>` - OFF by default

The cap Lobby Map offered you, in the copies as an opt-in: `dpr()` is capped at maxres/1080, and so are the two
places that bypassed it (the light-loop choice and the vehicle preload). `maxres=1080` at 1440p: lobby 0 of the 175
4K image references and the 1080p loop; auditorium 0 of 4672 4K slices. In OBS it saved no CPU (hardware decode), so
it is only worth it to save memory or for a weaker PC; zooms get softer with it.

### 18. Control panel, server and LAN proxy (review of control.html, standby-server.js, lan-proxy.js)

**Security (confirmed): the LAN/Tailscale view proxies let any device on your network drive the stream.** Both are
running (192.168.2.150:18780 home LAN, 100.69.76.4:18780 Tailscale). They forward every request, and the server
only refuses control requests that carry a *foreign* Origin header; a request without one (curl, any app) passes.
Proved with a harmless probe through both proxies: `POST /ctl/cmd` to a non-existent scene came back from the
server ("unknown page"), so a real command (a fake chatter saying anything on stream, remove, reset) would work
from any device on the home Wi-Fi. I did not restart the running proxies (yours). Fixed copy
`roxy3d/qa-night/lan-proxy-qa.js` (+ `.patch`): **view-only by default** (GET/HEAD only; of `/ctl/` only the
screens' command stream `/ctl/events`), `--control` restores the old behaviour for your own devices. Also passes a
closed connection on both ways (a phone reload left a ghost screen on the server forever, and after a server
restart the phone's screen never reconnected). Tested on a spare local port: pages 200, control 403, events 200,
with --control the control request goes through.

Server (`roxy3d/qa-night/standby-server-qa.js` + `.patch`; apply when you restart it):
- the files it must not serve were matched case-sensitively: `/Standby-Server.js`, `/DINKDONK.JS` and
  `/lan-proxy.js` were served (confirmed; no secrets in them, qBittorrent uses localhost access without a
  password). Now case-insensitive, lan-proxy.js added. Tested on a spare port: all 404, pages still 200.
- old screen states are now also pruned when a screen posts (they were only pruned while the panel polled).

Panel and scenes (copies: `control-qa.html`, and both scene copies):
- the panel showed "the biggest screen", so a preview tab on a 4K monitor won over the OBS source (its chatters,
  its director state; the director on/off button toggled from the wrong state). Scenes now report `obs: true`
  inside OBS and the panel prefers that screen (checked: OBS source picked over a 4K tab; no flags = biggest).
- switching scene in the panel now clears the old scene's rows at once (a click there during the refresh went to
  the newly selected scene).
- the lobby's state posts get the auditorium's guard (one at a time, 3.5 s timeout), so slow posts can't pile up.

Also hardened: the auditorium's IMDb rating is set as text instead of `innerHTML` (it comes from an outside API;
it was already forced to a number, so this was not exploitable).

**05 Nov 2026 - proxy swap done (owner approved):** stopped lan-proxy.js PIDs 920/24832; started roxy3d/qa-night/lan-proxy-qa.js on 192.168.2.150:18780 (PID 32804) and 100.69.76.4:18780 (PID 7928). Checked: GET pages and /ctl/events 200, POST /ctl/cmd 403 on both. After a reboot, whatever starts lan-proxy.js will start the old one again unless it is pointed at the copy.


**05 Nov 2026 - QA copies promoted to default (owner request):** roxy.html, auditorium.html, control.html and lan-proxy.js are now the QA versions (byte-identical to roxy-qa.html, auditorium-qa.html, control-qa.html, qa-night/lan-proxy-qa.js). Originals backed up in standby/backup-2026-11-05-pre-qa/. Smoke test through the server, real chat, 1440p, 60 s each: lobby 122 fps, auditorium 123 fps (headless 120 Hz), 0 page errors. Not promoted: shared-qa/ (used by ~20 other scenes) and standby-server-qa.js (needs a server restart).

**05 Nov 2026 - shared scripts + server promoted (owner request):** shared/core.js, cinema.js, live.js = qa-night/shared-qa/*, standby-server.js = qa-night/standby-server-qa.js (takes effect at the next server restart). Originals in standby/backup-2026-11-05-pre-qa/ (shared/ subfolder). Smoke test, real chat, 1440p, all 19 scenes that load shared/: all render, no errors from our files; the only messages come from the destiny.gg chat iframe (autofocus notice) and the DSA relay (emotes.click 502), same as before.
