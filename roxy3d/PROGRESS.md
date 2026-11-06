# Progress log

- 01 Nov 22:45 - goal set (weekly usage 25%). Codex pass 1 (stills + occluders) running.
- 01 Nov 22:40 - Codex pass 1 done: Blender scene, Cycles stills, 17 occluders / 66 depth slices, calibration 0.016 px.
- 01 Nov 22:50 - Claude: roxy.html loads roxy3d/out/manifest.json (bg + z-sorted slices, @2x at hi-res, glow under chatters),
  DOM door signs sit in the rendered marquee boxes, baked signs' DOM copies hidden, ?art=flat keeps the blockout.
- 01 Nov 22:55 - Codex pass 2 started (BRIEF-3-pass2.md -> out2/): counters against the walls (owner QA), grittier
  materials, base + seamless light loop.
- 01 Nov 23:05 - Claude: layout data per manifest ("layout": 2 switches routes), two ticket windows (2nd opens at 3+ in
  line), 3 snack registers with own clerks, light-loop video support (plus-lighter, falls back to full.png),
  ?artdir= / ?layout= / ?loop=0 for testing; door-sign flash driven by the frame loop (CSS animations stall
  in headless/throttled sources).
- 01 Nov 23:15 - Claude: umbrellas (35% of chatters, open only outside), splash rings when hopping on the wet
  pavement, arcade detour (7%: plays a round, "GAME OVER" / "NEW HIGH SCORE"). QA screenshot ok, no errors.
- 01 Nov 23:10 - Codex review #1 (reviews/review-1.md). TAKEN: P1 frozen walkers on re-talk (figures set keeps
  retiring walkers updating), P1 unbounded chat stats/maps (core.js prunes every 200 msgs, cinema.js caps maps at
  4000), door lock (doorRoom; counter goes to the door actually used), case-insensitive purge, restroom/offscreen
  bubbles held until visible, snack registers queue (one served, others wait behind), arcade route around the
  cabinet, art manifest validation + 5 s timeout, @2x->1x image fallback, poster retry after failure, loop video
  fallback to the lit still, transforms only written when changed, renderTokens ellipsis, ?green= validation,
  empty emote pool fallback. DESIGN: names only while new (7 s) or talking, dark name backing, square Verdana
  90s dialog bubbles (3 lines max), solid door signs with 2-line titles, "0 went in" hidden, "LOCAL" clock,
  staff caps (red; usher maroon with gold button), per-arrival sidewalk lanes.
  DEFERRED: self-hosted fonts (OBS is online; revisit), bubble collision layout, 30 Hz rain, staff gags.
- 01 Nov 23:25 - Codex pass 2 delivered (out2/): layout 2 (box office + snack bar as counters against the 90 px
  walls, staff behind), grittier materials, base + 5 s seamless additive light loop (2.8 MB VP9). Claude: page
  now defaults to out2 (?artdir=out for pass 1), loop plays with plus-lighter, QA at 1080p + 4K ok (green rect
  pure at 4K, @2x crisp), float texts stack instead of overlapping.
- 01 Nov 23:30 - Codex pass 3 started (BRIEF-4-vehicles.md -> out3/: bus, taxi, two sedans, both directions,
  additive headlight sprites, lit_bg fallback). Codex review #2 started (design of pass 2 + verify fixes + routes
  vs new footprints).
- 01 Nov 23:40 - Codex review #2 (reviews/review-2.md): confirmed review-1 fixes, all layout-2 routes clear the 18
  props. TAKEN: real snack lines per register (max 3, head served, line moves up; overflow skips popcorn), speech
  above announcements + 18 px + pointer no longer clipped (clamp on inner .bt), wide emotes fitted to 74 px,
  staff call-outs rate-limited (staffSays, 6 s), JS rain off while the light loop plays, loop: 6 s first-frame
  deadline -> lit still, stall nudge (never drops a working loop), ?loop=0 uses the lit still, broken manifest
  entries skipped, pending speech for hidden speakers (no longer evicts visible bubbles), film change resets its
  count, restroom: one inside + one waiting beside the door, figure ceiling 80, window 2 opens on pre-dispatch
  line length, green-off board refreshed with the HUD, emote loading bounded (8 s) + bad names filtered, arcade
  route with clearance, sidewalk lanes 9.78-10.05, arrivals staggered per side. NEW charm: warm light wedge out
  of a door when someone goes in, arcade screen flash after a round. Signs inset into the rendered marquee
  (bevel visible), screen 1 sign above screen 2.
  DEFERRED: carpet contrast + warm light at service points (-> next Codex art pass), self-hosted fonts,
  ticket-tear / umbrella-fold animations.
- 01 Nov 23:50 - Codex pass 3 delivered (out3/): bus, taxi, 2 sedans x 2 directions, additive road lights, open-door
  variants, lit_bg fallback, arrival_stops. Claude: traffic in roxy.html - a passing car every 6-16 s both ways,
  a bus every 50-100 s that stops at the shelter (dwell grows with riders), taxis (10% of arrivals) drive a
  chatter to the entrance; riders stay hidden until their vehicle stops, then step out ("thanks driver!");
  lane following keeps gaps (cars queue behind a stopped bus). Default art = out3. QA screenshot ok.
- 01 Nov 23:55 - Codex pass 4 started (BRIEF-5-pass4.md -> out4/: calmer carpet, warm light at service points,
  prop loops: popcorn popping, arcade attract mode, buzzing boards). Codex review #3 started (traffic code).
- 02 Nov 00:00 - Codex review #3 (reviews/review-3.md): review-2 fixes confirmed; 10-min crowd sim found no traffic
  leak. TAKEN: snack places reserved when the register is chosen (hard max 3 incl. people on their way), riders
  get off one at a time and the vehicle waits until all stepped away (max +10 s; riders of a departed vehicle
  walk out), rider membership tracked (purge/caps), cars never move into the one ahead + spawn only on a clear
  lane, curb-side walkers drawn behind vehicle bodies, vehicle sprites follow 1x/2x on resize + @2x->1x fallback
  + a car whose body can't load leaves the road, restroom admits the next one only after the doorway is clear,
  stalled loop -> lit still after ~18 s, emote width cap is now hard (min 16 px tall), depth_slices validated,
  one "thanks driver!" per stop, arrival name timer starts when the rider appears, splash on stepping out,
  signs 150 px wide (screens 1/2 no longer overlap much).
  DEFERRED: bus depth slices (P2, needs Codex), late emote CSS refresh, film identity keys, brake lights.
- 02 Nov 00:20 - Codex pass 4 delivered (out4/): carpet contrast -60 %, warm pools at windows/registers/gate/doors,
  dimmer lobby, quieter counter tops, 8 additive prop loops (2 popcorn machines, arcade attract mode, 3 menu
  boards, soda fountain, TICKETS "E" flicker). Claude: prop-loop sprite sheets stepped by the frame loop
  (plus-lighter, 1x/2x), default art = out4. QA screenshot ok, no errors.
- 02 Nov 00:25 - Codex pass 5 started (BRIEF-6-pass5.md -> out5/: vehicle depth slices, brake/indicator lights,
  lobby cat sprite sheets, tyre spray). Codex review #4 started (design & feel, next 10 additions).
- 02 Nov 00:35 - Codex review #4 (reviews/review-4.md, design & feel + 10 ranked additions). TAKEN: speaker name in the
  bubble header (floor label hides while talking, arrival names 5 s), staff call-outs replaced by gestures
  (second cashier waves = hop; usher points ◀/▶ to the chatter's wing), ticket stub carried from the box office
  and torn by the usher (#1 addition), arcade attract loop stops while someone plays (#6, partly), header now
  "INTERMISSION" + "NEXT MOVIE NIGHT · <date>" ("back in a moment" only while a night is live), signs show
  number + title + one detail (rating), subtler splash rings, hard emote width cap, bus admits max 6 riders and
  only while it can unload them; riders still inside at a forced departure get off at the shelter instead.
  FOR CODEX PASS 6: separate the screen 1/2 marquee+poster stacks, material wear on counters/thresholds,
  shaded umbrella sprites + fold frames, door leaves that open, shelter drip loop, janitor NPC, bench regular.
- 02 Nov 00:50 - Codex pass 5 delivered (out5/): vehicle depth slices (28 sections), brake + indicator lights,
  ginger lobby cat (sleep, sit, stretch, 4 walk cycles), tyre spray. Claude: vehicles drawn as z-sorted slices
  (curb-side z hack removed), brake lights while slowing/stopped, bus/taxi indicator blinks pulling in/out,
  tyre spray one-shots off the rear wheel, generic sprite-sheet helpers, the cat (sleeps at 4 spots, stretches,
  walks axis-aligned routes via a lobby hub, sits, wakes when someone hops right past). Default art = out5.
- 02 Nov 00:55 - Codex pass 6 started (BRIEF-7-pass6.md -> out6/: separate screen 1/2 stacks + poster_frames in
  the manifest, material wear, door open sheets, umbrella sprites, janitor NPC, shelter drip loop).
  Codex review #5 started (pass 5 integration code, cat routes vs footprints).
- 02 Nov 01:10 - Codex review #5 (reviews/review-5.md): no P1; slices du correct both ways, all 12 cat routes clear all
  props (3,618 checks), bus admission verified. TAKEN: vehicle slice swaps decode-then-swap with a generation
  guard (stale errors can't remove a vehicle), riders of a vanished vehicle get off at the shelter (shared
  releaseRiders), light variants preloaded, steady brake light while parked (indicator only pulling in/out),
  dt-based brake detection with 0.3 s hold, tyre spray on the ground layer (z 4), cat + one-shots follow 1x/2x on
  resize, sheet @2x->1x fallback, manifest validation for cat/spray/slices (validSheet), usher locks the door
  it points to, stub follows emote width, cat only woken by visible moving chatters, one-shot cap 12, frame
  errors caught so the loop never stops, bubbles clamped inside the stage with the pointer aimed at the speaker.
  OPEN: combined brake+indicator light (needs an indicator-only sprite), screen 1/2 stacks (pass 6).
- 02 Nov 01:45 - Codex pass 6 delivered (out6/): separated marquee/poster stacks (manifest marquees + poster_frames),
  wear on counters/thresholds/glass/pavement, 6 door open-close sheets, umbrella sprites (4 colours + fold),
  janitor (4 walks, sweep, watch-check idle), shelter drip loop. Claude: signs + posters placed from the manifest,
  doors swing open when someone goes in (and for the restroom), umbrella sprites held outside and folded at the
  door, generic NPC walker (cat refactored onto it) + the janitor (walk -> sweep -> check watch -> next spot),
  float-stacking memory = animation length. Default art = out6. QA screenshot ok, no errors.
- 02 Nov 02:00 - Codex review #6 (reviews/review-6.md): verdict "convincingly evokes a late-90s isometric game (Sims /
  Theme Hospital with a rainy neon-cinema palette)"; remaining gap = crowd presentation + interaction timing. NPC
  routes re-verified (cat 3,618 + janitor 3,216 checks clear), posters/marquees exact. TAKEN: umbrella fold animates
  in the owner's hand (follows hops/fade), grip at the asset's [10,-40], umbrellas follow 1x/2x on resize, a door
  re-opens for someone arriving while it swings, sign text fits each aperture (rating + count share one row,
  compact 1-line title for the smaller screen-4 box), "BOUGHT ONLINE"/"HAS A TICKET" replaced by the stub,
  gate/entrance spread (personal offsets), shorter + smaller rectangular combo badge, rectangular clock panel,
  shaded staff caps and stubs, bubble collision layout (overlapping bubbles stack upwards).
- 02 Nov 02:25 - Codex pass 7 delivered (out7/): rendered popcorn tub, soda cup, stub, ticket, cashier + usher caps;
  indicator-only light sprites. Claude: items attached at emote-relative points (follow emote width changes),
  flying ticket/stub use the sprites, staff wear the rendered caps, bus/taxi brake light stays steady with the
  indicator glow blinking on top (also while parked). Default art = out7. QA at 4K ok, no errors.
- 02 Nov 02:35 - Codex review #7 (final, reviews/review-7.md): no P1; "visually good enough for a first stream".
  TAKEN: doors held open while someone else arrives (animation wound back to its hold), bubble stacking bounded to
  the stage (side placement, else the older bubble waits), staff caps sit on the emote's actual height.
- 02 Nov 02:40 - LOOP STOPPED: result is good (reviewer verdict), weekly usage 27 % (< 35 % budget). README + gallery
  updated. Not verified: live DGG chat through the DSA relay, inside OBS, real 60 fps at 4K on the stream PC.

## 02 Nov morning - owner's new asks: surroundings + heavy rain (pass 8)
- 08:25 - Owner: fill the empty areas (buildings across the street = roofs bottom-left, neighbours left and right
  of the cinema), much heavier rain, stronger water on the street and the cinema glass, stronger reflections,
  and implement Codex's suggestions too.
- 08:35 - Codex review 8 (reviews/review-8-suggestions.md): surroundings plan with occlusion envelopes
  (H <= 60(v-13.5)-48 across the road, H <= 60(u-13)-48 right of the cinema), rain density numbers, 6 s/144-frame
  loops, foreground rain layer, per-glass-slice water, additive-limitation warning, VP9 CRF 16-22, plus 7 ideas.
  All taken: art in BRIEF-9-pass8.md (Codex), page ideas done by Claude.
- 08:40 - Page: generic playLoop() (first frame <= 6 s, stall nudges, drop after ~18 s) for the light loop and a new
  #rainfg video (manifest rain_fg, plus-lighter, z 70001: above walkers/vehicles, below signs/bubbles/HUD);
  procedural fallback rain 150 -> 520 drops in two depths; prop loops honour blend: source-over (glass water).
- 08:45 - Page (Codex C1-C6): usher gate line (one at the gate, holding spots beside the podium / snack counter end,
  serveGate) + personal space (a walker about to walk into the back of someone just ahead waits, max 1.5 s, then
  goes); bubbles never cover the HUD or billboard and avoid door titles + gate sign when another spot is free
  (pointer recomputed after any move); contact shadow sized to the emote and shrinking mid-hop; outdoor emotes
  slightly dimmer; arcade screens attract -> play -> hiscore (when the art has them); bench patron waits for the
  next arrival ("there you are!"); wet prints behind people coming in from the rain (items.wet_print or CSS).
- 08:45 - BUG FOUND: standby-server.js had no .webm type, so light_loop.webm was a 404 and the pre-rendered
  rain/neon loop never played through the server (the page silently used the lit still). Fixed: video MIME
  types + byte-range responses. The owner's running server (start-standby.bat) needs one restart.
- 08:45 - Codex pass 8 first preview: right layout (opposite workshops, left apartments + video rental, auditorium
  block, alley + annex + right apartments, billboard tower, 3D distant city) but far too dark; stopped and resumed
  with BRIEF-9b-lighting.md (sky, fill, lit windows, neighbour signage, roof detail).
- 09:22 - Codex pass 8 delivered (out8/): lit city block, 6 s downpour loop + rain_fg, wet reflections (minimum base +
  differences), drainage/drips, 9 glass-water slices, entrance mat/threshold, wet_print item, arcade_play/hiscore.
  Occlusion 0, aperture exact, seams/black level ok. Claude: default art = out8; both videos verified playing.
- 09:35 - Codex review 9 (reviews/review-9.md): no P1; "reads as one rainy city block". TAKEN (Claude): server empty-file
  crash + stream leak on aborted requests, bounded gate line (extras wait inside), bubble lifetime only runs while
  shown, playLoop kill/detach (no hidden restart), coordinated weather fallback (one foreground rain renderer at a
  time; tested fg-fail and base-fail), lighter marquee inserts. Art items -> BRIEF-10-pass8b.md.
- 10:10 - Fresh, context-free GPT-6 Astra xhigh feedback (reviews/fresh-xhigh-feedback.md). Owner's picks queued in
  QUEUE-owner.md - NOT to be started until his next list.
- 10:24 - Codex pass 8b (out8b/): stepped distant roofs + haze, denser rain, wetter glass, broken reflections, textured
  alley/roof, 18 carpet outlines removed, lit_bg_dry fallback. Default art = out8b; verified in the browser (both
  videos, no errors). Not verified: OBS/CEF performance on the stream PC.

## 02-03 Nov 2026 - final render (out10) on RunPod, owner asleep
- 21:18 - `bash cloud/cloud-render.sh full` from the draft-13 bundle (BRIEF-26). Pod e9drr2tw6upc4e, RTX 5090 secure,
  $1.19/h; credit ~$9.40 at launch; helper cap 7 h.
- 21:36 / 22:23 - background loops done (48 frames: 1080p ~19 s/frame, 4K ~41 s/frame).
- 23:30 - problem: every foreground group was marked dynamic (any glossy/glass/metal material) and rendered 48 frames
  x 2 scales at ~9 s/frame (4 s Cycles + ~5 s per-frame scene sync, the same at 1080p and 4K) = ~15 min per group.
  39 groups -> ~10 h: over both the 7 h cap and the credit, and the helper would have deleted the pod with nothing
  delivered. Fix (Claude): production.py `INTERIOR_STATIC` - the 25 indoor groups (podium, lobby props, queue ropes,
  restroom, corridor) render one frame per scale (no rain, constant light indoors, so their loop was ~empty
  anyway); the 10 outdoor/glass groups keep the full 48-frame wet loop. Killed the pipeline without an EXIT marker,
  moved the partial pod output to out10.run1, updated BUNDLE-SHA256SUMS, relaunched; finished Cycles buffers are
  reused from the cache (runtime.py unchanged). Original saved as cloud/bundle/production.py.orig-full1.
  Also found: the first launch had no pod watchdog (RUNPOD_POD_ID is not in the ssh env) and its EXIT marker was
  hard-wired to 0 (`$?` expanded locally). The relaunch exports the pod id (watchdog armed) and writes the real code.
- 00:20 - page (roxy.html) vs the layout-3 manifest template: stall routes read `route_points` (the template's name).
  Codex read-only review (reviews/review-10-code.md, 9 x P2/P3), all checked against the code and fixed by Claude:
  ticket window no longer pulls someone across the ropes (they walk the lane first); gate arrivals from the east go
  round the usher podium (via gateIn); arcade route passes below the back rope; removing a chatter in a stall frees
  it and refreshes the WC light (a stray line had landed in the bench callback); LED text rows use the rendered dot
  rows (rows_px); posters use the frame's wall offset (were 4.3 px off); after the layout-3 sign surgery the room
  list is reapplied and signs renumbered (films 3-5 could show on screens 1-3 for 2 min); the 4K base now plays with
  light_loop_2x (its exact complement; `?loop2x=0` keeps the 1080p loop if the stream PC struggles); random poster
  chases only pick existing screens. Smoke test with out8b + ?layout=3 and 10 test chatters: no page errors.
- 00:13-02:37 - all 10 outdoor groups (48 frames), the 25 indoor statics, weather and the 8 door animations rendered.
- 02:46 - FAILED in the last packing step. video.py's decode check of light_loop_2x (4K VP9 crf 4) found 10 of 565,684
  black probe pixels at 1/255 (an additive layer: invisible) and raised. The helper then deleted the pod as designed,
  so all 5.5 h of renders were lost. Balance after: ~$2.77, not enough for a re-run (~5.5 h x $0.89-1.19/h).
  Fixes (Claude, bundle resealed with seal_bundle.py, only video.py/validation.py changed vs run 2):
  - video.py: black probe passes with codec noise <=2/255 on <=0.05% of probe pixels (was exactly 0);
    validation.py: the duplicate `decoded_black_max != 0` test is gone (it uses the video's own pass flag).
  - cloud-render.sh: a FAILED full run whose pod watchdog is armed now KEEPS the pod (render cache intact), downloads
    run.log/progress.log, and prints the repair command: fix, then `ADOPT_POD=<id> bash cloud-render.sh full`
    (moves the old out10 aside, reuses every cached render; the watchdog stops the pod 3 h after the failure;
    KEEP_ON_FAIL=0 restores delete-on-fail). Also fixed: EXIT records the real exit code and the watchdog gets
    RUNPOD_POD_ID (both via a pod-side launch.sh), and a full run refuses to start below $7.50 balance
    (MIN_BALANCE overrides) so a run cannot die mid-way from lack of credit.
  - Backups: cloud/backup-run2/ (run-2 checksums, original production.py and video.py).
- 03:05 - Codex read-only review of the never-run packaging tail (reviews/review-run2-packaging.md). Acted on: the
  black-noise allowance is now per decoded frame (it summed 5 frames against a one-frame budget). Not changed
  (Codex agrees they are sound or low-risk; a failure there is now repairable on the kept pod): exact slice/door/bus
  byte checks (exact by construction), the rain loop-seam assert, 4K memory use (passed in run 2), WebM duration
  metadata. Repair path note: any *.py change alters out10's fingerprint, so ADOPT_POD moves out10 aside and the
  pipeline re-walks every stage from the render cache (as the run-1 relaunch did). Bundle resealed again.
- 07:46 - owner topped up ($12.77). Run 3 started: RTX 4090 secure $0.89/h, watchdog armed (fixed launch path works).
  4090 measured ~31 s/frame for 1080p backgrounds (5090: ~20 s) -> projected finish ~14:30-15:00.
- 08:22 - STOPPED on owner's request after a render-time breakdown: ~60% of a run is 14 outdoor foreground groups x
  48 frames x 2 scales = 1,344 separate full renders at ~9 s (only ~4 s Cycles; ~5 s per-render scene sync).
  Owner wants the faster pipeline first: one render per frame cut into layers (object masks), 4K only + downscale,
  less per-render sync, 24 frames for subtle wet loops (needs a draft). Pod deleted, billing 0, balance $12.27.
- 03 Nov - BRIEF-27 (fast pipeline: one render per frame cut by masks, 4K only + downscale, less per-render
  overhead, 24-frame wet loops) sent to Codex. Owner then approved 24 frames as the default for the wet loops.
- 09:20 - Codex delivered BRIEF-27 (NOTES-FAST-PIPELINE.md, draft image qa10/draft14-fast.png, same look as draft 13).
  Per-render overhead 15 s -> 6 s (local), 4K-only + linear 2x2 downscale, combined mask capture for 6 of 39 groups
  (33 keep isolated renders: glass/soft edges differed beyond noise), 24 wet frames now the default (48 override).
  Packaging tail passed end to end at smoke scale. Projected full run: 5090 ~2.1 h/$2.46, 4090 ~2.7 h/$2.43
  (not measured on the cloud). Bundle resealed (sha f5b4d7b1...).
- 09:56 - Run 4 (fast pipeline, 24 wet frames): no 5090/4090 free -> L40S secure $1.09/h, pod m0dhqr1o60n2fn.
  4K backgrounds ~71 s/frame (done 11:01); combined masked foreground done ~11:21; isolated groups started.
- 11:26 - the pod became unreachable over ssh ("No route to host") and stayed so; at ~12:29 the Claude session
  ended and the local helper died with it. The pod kept rendering; billing (~6.4 h, $7.06) fits the pipeline ending
  ~13:20 and the pod watchdog stopping it 3 h later (~16:20). `pod start` fails (no free GPU on that host) and a
  stop clears the container disk (no volume was attached), so the result is lost. Balance after: $5.16.
  Design gaps found: (1) the only copy of out10 lives on the pod's container disk, which the watchdog's stop wipes;
  (2) the local helper is tied to the Claude session; (3) no way to fetch results if the controller loses the pod.
- 03 Nov - SCENE 2 started: BRIEF-28 (auditorium draft 1, one still, qa11/) sent to Codex (log codex28.log). Owner decisions: screen = OBS green aperture (page draws the green quad, obs-shaderfilter corner-pin; edits only in a COPY of the "Moobies 1440p" collection), pre-show then film on it, download progress from qBittorrent Web UI (127.0.0.1, localhost auth bypass).
- 03 Nov - Draft 1 delivered (qa11/cinema_draft_01.png, 72 seats, screen 552 px). Owner: agrees with bigger/grittier/fill-frame -> BRIEF-29 draft 2 sent (codex29.log). Owner: the film on the in-room screen is only a short moment in the transition to the full-screen movie, so the zoom director stays free (no wide-shot lock, no live OBS corner updates).
- 17:30-18:50 - Results now survive a lost pod/controller (cloud-render.sh rewrite): a 10 GB network volume is created
  per run in a data center with a free GPU (stock list, plus a sweep of all data centers every 5th round because the
  list is sparse); the pod copies results/logs to /vol/results when the run ends (progress every 5 min) and stops
  itself 20 min after a success; the helper never deletes an unreachable pod - it waits for it to stop and reads the
  volume with a small pod in that data center (`bash cloud-render.sh fetch`, retries up to 6 h; cheap GPUs first,
  CPU last - CPU pods sat at awaiting_container 20+ min in EU-RO-1); the volume is deleted only once the result is
  home. Bugs fixed while testing: Git Bash rewrote /vol to C:/Program Files/Git/vol (runpodctl now runs with
  MSYS_NO_PATHCONV=1), search volumes leaked on Ctrl-C, a lookup of a deleted pod killed the script under
  set -e/pipefail. Credit guard 4.5 for a full run. Run the helper from the Terminal panel, not inside Claude.
  Smoke test (5090, EU-RO-1, TEST_FETCH=1): render exit 0; result fetched from the volume via a pod; pods and volume
  deleted; billing 0. Balance $4.95. Run-4 pod m0dhqr1o60n2fn left stopped (empty, no cost).
- 03 Nov - Draft 2 delivered (816 px screen, 10x20 seats, fills frame). Owner: "bigger" meant a bigger hall seen MORE ZOOMED OUT (whole hall in frame). Codex read-only critique reviews/review-cinema-d2.md (points 1-9 taken; 10 = emote test, left for page work). BRIEF-30 draft 3 sent (ortho_scale cap ~30 -> emotes ~38 px, walls ~700, 8-9 rows x 16-18).
- 18:52 - full run refused by RunPod: a network volume needs >= $5 on the account (balance $4.94). Guard raised to $5.50 (full) / $5.10 (smoke). Needs a top-up.
- 03 Nov - Draft 3 delivered (whole hall, ortho 30, 8x18 seats). Owner shared photos of his childhood cinema (Showcase Cinemas in a mall, Spanish signage) -> ref/childhood-cinema/. Codex read of the photos: reviews/review-cinema-d3-refs.md. BRIEF-31 draft 4 sent (flat front rows + stadium bank, passage entrance, mauve seats, teal pleated walls, SALIDA, red step dots, 90s carpet). Lobby/snack-bar photos (01, 06, 07) also fit scene 1 later.
- 03 Nov - Draft 4 delivered (childhood-cinema look). Owner: walls much darker/muted, room less lit, seats PURPLE not pink, EXIT not SALIDA, rows 50-75% more level, staircase between two seat blocks, and a quick BOX BLOCKOUT first for layout feedback -> BRIEF-32 (draft 5 blockout) sent, codex32.log.
- 03 Nov - Blockout 5 delivered (6 rows, level rows work). Owner: remove row A + gap to the screen, B/C too close, add 3-4 bank rows at the back, lower the too-tall walls, rows split into blocks/aisles like his seat map (ref/childhood-cinema/08-seat-map.png, indicative only) -> BRIEF-33 blockout v2 sent, codex33.log.
- 03 Nov - Owner approved blockout v2 layout (incl. ortho 32 zoom-out, emotes ~35 px). BRIEF-34 styled draft 7 sent (dark muted room, deep purple seats, dark teal pleats, EXIT, visible red step dots), codex34.log.
- 03 Nov - Draft 7 delivered (styled blockout v2, seats mean 18/255). Owner: the empty middle-left is a TUNNEL from the real entrance at the back (chatters arrive through it; screen-side door = emergency exit only), walls dark BLUE not green, more popcorn/litter, remove senseless handrails; agrees to lift darks, visible step lights, lit cut edge. Codex critique reviews/review-cinema-d7.md (1-9 taken). BRIEF-35 draft 8 sent, codex35.log.
- 03 Nov - Draft 8 delivered (tunnel, navy walls, seats 41/255, visible step lights). Owner: light the tunnel mouth -> BRIEF-36 draft 9 (lighting only), codex36.log.
- 03 Nov - Draft 9 delivered (tunnel mouth lit: warm spill on approach, 3 step inserts, EXIT on guard post; screen unchanged). Waiting for owner review.
- 03 Nov - NEW PAGE standby/auditorium.html (scene 2, Claude): bg = qa11/cinema_draft_NN.png + cinema_layout_NN.json (?draft=09 default). Chatters (Cinema.onWalkIn, everyone=1/tag) spawn one at a time at the rear portal, hidden in the tunnel, approach -> cross-aisle -> left/right stair -> legroom -> seat; own-row seat backs hide the lower body (clip at the back-top line); arrival + walking messages saved and said once seated; max 4 bubbles, stacked, never over the screen quad; seat choice: mentioned friends, middle-weighted, gap to strangers. Tested with injected SB.say messages (headless Edge, scratchpad shot.mjs): 22 walkers, all routes OK. DSA chat relay (ws 127.0.0.1:18765) was offline, so no real everyone=1 view yet. Not yet: occluder layers from Codex, stair/row-C partial occlusion, zoom director, pre-show/green, lights-down.
- 03 Nov - auditorium.html: seated emotes now cut on the backrest diagonal (slope 0.5, clip-path polygon), sitters drawn 0.2 tile back so heads centre over their own backrest. Owner let me start the DSA relay myself (customchat/destinygg-obs-overlay, node server.js): live everyone=1 filled 77 chatters / 61 seated in 90 s. NEW standby/lan-proxy.js (phone on the LAN): listens on 192.168.2.150:18780, forwards pages to 18770 and /__dgg_chat_ws to the relay; phone URL http://192.168.2.150:18780/auditorium.html?everyone=1&relay=192.168.2.150:18780. Both servers stay on 127.0.0.1; Node inbound is allowed on the Private Wi-Fi profile.
- 03 Nov - Owner notes on the live page: rear door (lobby screen door, opens per chatter) instead of the EXIT sign, wall over the cut underside, tunnel-mouth reveal, speak while entering, emergency exit closer to the screen (red EXIT, closed), front row = wheelchair row (blue wheelchair signs on row-B backs; YEE chatters only sit there), DGG flair colours, no square emotes as bodies. Done in pages: speech while walking (bubbles wait hidden in the tunnel; 4-bubble cap counts only visible), page_layers support (depth slices z = 1000+round((u+v+z/90)*100), entrance door sheet) in auditorium.html; shared/core.js DGG flair colours (flairs.json via standby-server, rainbow for tier 5) used by roxy + auditorium; shared/cinema.js keeps square emotes (border >80% opaque, found via same-origin /dgg/emote-img) + JARVIS off chatter bodies (27 found live); YEE -> row B only. standby-server.js: /dgg/flairs.json + /dgg/emote-img. BRIEF-37 (draft 10: door, cut wall, depth slices) running in Codex; items 4-5 (emergency exit, wheelchair signs) were appended after it started - check, else resume.
- 03 Nov ~21:35 - OVERNIGHT GOAL (GOAL-cinema.md): until good or 55% weekly usage (43% now). Done since: DGG name colours 1:1 with the DSA userscript (lowest-priority flair, plain #fff, roles/sub tier, gradient rainbow), emote facing table shared/emote-facing.json (Codex vision on 7 contact sheets from tools/emote-sheet.html: 132 right / 70 left / 123 front) used by both scenes, lobby walk animation in the auditorium, sitters taller (SIT_Z 48), draft 10 integrated (159 depth slices, door sheet with static-slice cutout mask, wait 0.28 s) and made the page default. Codex BRIEF-38 (page: director + control panel, codex38.log) and BRIEF-39 (render: draft 11 polish + final 4K on local GPU, codex39.log) running in parallel.
- 03 Nov ~22:00 - BRIEF-38 done by Codex (PAGE-38.md): auditorium zoom director (lobby port, follows an arrival door -> tunnel mouth -> seat, holds 3.2 s), control.html scene selector (lobby/auditorium) with reset/follow/wide/zoom/test arrival/remove, standby-server routes /ctl commands per scene (controlVersion 2; server restarted), optional @2x art selection. Verified live with director=30. Found: name labels hidden by depth slices -> BRIEF-40 (names in their own top layer + seated neighbours turn to the speaker) running, codex40.log.
- 03 Nov 21:53 - FINAL RENDER DONE (run 5, fast pipeline BRIEF-27, 24-frame wet loops): RTX 5090 EUR-NO-1, pod
  a616bp5ubdg572 + network volume xyurzmultn, 19:08-21:53 (2 h 45 m, ~$3.30). Exit 0, out10.tar.gz checksum OK, pod and
  volume deleted, billing 0, balance $11.69. Pack: validation.json passed (no failures; depth slices reconstruct exactly;
  light_loop, light_loop_2x, rain_fg decode checks pass), all 705 checksums.json entries match. Swapped in: old local
  out10 (02 Nov local build) -> out10.stale-20261102; roxy.html ART default out8b -> out10 (?artdir=out8b for the
  old pack; backup cloud/backup-run2/roxy.html.pre-out10). Live test on :18771 with demo=1: all out10 assets load,
  light_loop_2x + rain_fg play, door sheets (screen_2, stall_1), tickets/stubs, wet prints and umbrellas fire, no
  page errors (only pre-existing 400s: the emote proxy rejects .avif emotes). qa10/final/out10-full-1080p.png = the
  final composite. Not verified: OBS/CEF performance with the 4K loop on the stream PC (?loop2x=0 fallback).
  Note: manifest render_device still says the local RTX 3050 (stale metadata, harmless). Run-4 pod m0dhqr1o60n2fn
  still stopped (no cost), delete on owner OK.
- 03 Nov ~22:15 - BRIEF-40 done (PAGE-40.md): names in their own top layer (no longer hidden by slices), seated neighbours turn to a speaker 4-6 s. Live check with director=30 OK, no errors. Noted for later: big live bursts crowd the approach/cross-aisle with overlapping names.
- 03 Nov ~22:20 - Draft 11 + FINAL 4K set delivered by Codex (CINEMA-DRAFT-11.md, local RTX 3050 only): polish (tier separation, door fabric/portholes, plaques slightly toned down, cut wall variation), native 3840x2160 bg, 159 slices x2 scales, door x2, layout_11 with image_2x/file_2x. Page default -> draft 11; verified at 3840x2160 output (2x bg + slices selected, crisp, seat-shaped occlusion). qBittorrent not running and WebUI not enabled yet (WebUI\Address=127.0.0.1 only). BRIEF-41 (pre-show slides on the screen quad, /qb/progress, phases seating/dim/film/up with control panel buttons) running, codex41.log.
- 03 Nov ~22:35 - BRIEF-42 done: lights-down state cinema_draft_11_dim(.png/@2x) + draft11_dim slices/door with identical masks, layout_11 page_layers.dim. Looks right (step dots, EXITs, tunnel spill, faint sconces; screen wall black - filled by pre-show/OBS). Note: wheelchair plaques read a bit self-lit when dim. Page integration (crossfade instead of CSS brightness) after BRIEF-41.
- 03 Nov ~22:50 - BRIEF-41 done (PAGE-41.md): /qb/progress (qBittorrent WebUI 127.0.0.1:8080, QB_URL; returns available:false now), phases seating/dim/film/up (auto at 90% / 10 s after completion, manual from control.html, ?phase=), pre-show slides affine-mapped onto the screen quad (presents+title, loading %/"begins shortly", silence phones, snack bar, audience credits). Server restarted; verified live (projected slide on the screen, LAN proxy still up). BRIEF-43 (crossfade to the rendered dim set) running, codex43.log.
- 03 Nov ~23:05 - BRIEF-43 done (PAGE-43.md): dim/film phases crossfade to the rendered lights-down set (bg + paired slices + door), CSS darkening only as fallback; verified live with ?phase=dim (dark room, glowing pre-show, readable chatters). Weekly usage 44%. BRIEF-44 (code review/QA of auditorium.html, arrival-burst spacing + short-lived names, full-house behaviour) running, codex44.log.
- 03 Nov ~23:30 - BRIEF-44 done (PAGE-44.md): code review/QA fixes (full house: newcomers queue outside the rear portal instead of vanishing; bans/mutes also clear the queue; bounded pending speech; failed emote sprites show "?"; per-frame DOM write reduction; panel request timeouts), route spacing 0.9 tiles (FIFO, no overtaking), arrival names 5 s after leaving the tunnel; 12 fill/reset soak cycles leak-free. Final live check of auditorium + lobby: no errors. STOPPED for the night at 44% weekly usage: the scene is in a good state; open items for the owner in GOAL-cinema.md.
- 04 Nov ~10:10 - LOBBY PERFORMANCE (roxy.html + out10), headless Edge on this laptop (RTX 3050), harness from the
  cinema session (scratchpad perf-roxy.mjs: 170-nick burst over the cap, chat every 400 ms, director every 30 s).
  Before: 9-22 fps at 1080p/1440p, even nearly empty; trace: ~20 s of image decoding per 8 s. Cause: the director
  multiplies dpr() by its 1.85 zoom, so @2x art always loads, and the 58 wet prop-loop sheets decode to ~590 MB at
  @2x - more than Chrome's GPU image cache - so they were re-decoded every frame (same issue the cinema session found
  with its 4K slices). Fix (roxy.html applyArtRes): wet_* loops stay 1x; all other art keeps @2x. ?wet2x=1 restores
  the old way. After: ~53 fps steady at 1080p, 1440p and 4K with a full house (63 walkers), p99 ~20 ms, 0 long
  tasks, main thread ~20 % busy. Glass/pavement crops 1x vs @2x at 1440p look the same. Backup:
  cloud/backup-run2/roxy.html.pre-perf. Still ~265 composited layers (harmless now). Not verified in OBS itself.

## 04 Nov 2026 - auditorium performance (Claude)
Measured headless Edge on the RTX 3050 (GPU on, uncapped ~100-120 fps), 170 chatters arriving + chat every 0.4 s.
1. Zoom: `.w { will-change }` gave every chatter a GPU layer; the depth slices between them were then layered too and
   thrashed tile memory at the director's 1.85x zoom (~3 fps). Removed the will-change -> ~90-100 fps zoomed.
2. Full house: the slices' bounding boxes are ~25 screens of pixels (97 % transparent); at 2x they overflow Chrome's
   decode cache and PNGs were re-decoded every frame (600 decodes / 8 s, 4-17 fps). Fix:
   - `tools/band-slices.mjs` cuts every slice (lit/dim, 1x/2x) into 64 px bands split at 48 px gaps, trimmed to
     visible pixels (5.3 screens, 2327 pieces per set, opaque-only 2-row overlap against zoom seams). Verified: pieces
     rebuild every slice exactly. Files `qa11/draft11_bands/`, `qa11/draft11_dim_bands/`; layout gets `pieces`
     (backup `qa11/cinema_layout_11.before-bands.json`).
   - The page draws only the pieces that cover a chatter or the moving door (`cullPieces`, 64 px grid); the background
     already holds the same pixels, so hiding the rest looks identical (checked: culled vs all pieces = same image).
   - Lights down: the lit art stops being drawn once the dim art has faded in (`dim-done`); dim pieces aren't decoded up front.
   Result, 135 seated: 1080p ~102 fps, 1440p ~101, 4K 69-79, 1440p lights down ~103 (before: 3-17); no long tasks.
   During the arrival rush (20+ walking at once) 36-60 fps headless.
3. standby-server.js: `/dgg/emote-img` accepts .avif emotes (4 newer DGG emotes were rejected with 400).
Old page: `roxy3d/auditorium.before-perf.html`. Lobby zoom measured ~20 fps either way - not changed, separate look.
- 04 Nov ~10:50 - ALLEY FLICKER fixed (owner's phone clip). Cause (Codex BRIEF-45, NOTES out10-loopfix/NOTES-45.md):
  in the right-hand annex roof, `P8 record and repair annex` and `P8 gravel roof.005` both end at z=58
  (build_pass8.py:157 + roof() line 53) with different wet materials, so Cycles picked either face per frame:
  a cyan DINK DONK reflection + warm patch popped on/off (frames 8, 15, 17-23 of each 24). Not a light.
  Post-fix without re-render: bad phases interpolated from neighbouring good phases inside a feathered mask, both
  light_loop.webm and light_loop_2x.webm re-encoded with the bundle's VP9 settings (144 frames, 24 fps, additive).
  Checked by Claude: alley off-beat blocks 1080p ~20 -> 0, 4K 56 -> 0, street rain spots unchanged, 10 live frames
  at 1440p steady. Originals in out10.orig-loop/; out10/checksums.json is stale for those two files.
  NEXT RENDER: remove the covered annex top faces (or lift the roof slab) and check other roof()/body pairs.
- 04 Nov ~11:15 - Lobby director zoom check (asked by the cinema session, which measured ~20 fps zoomed): with the
  wet-loop fix it runs ~53 fps zoomed (scale 1.85) at 1080p and 1440p, GPU main ~22 %, no image re-decoding;
  ?wet2x=1 reproduces the old ~12 fps with ~20 s decode per 8 s. Their run predated the fix; nothing more to change.
- 04 Nov ~11:50 - DRAFT 15 (BRIEF-46, Codex, local only; qa10/draft15-cars-door2.png, NOTES-46.md). Owner saw a
  "light over everything" on cars/bus and a dark Screen-2 door. Causes: (1) vehicle studio rig in
  cloud/bundle/build_vehicles.py lighting(): 'Cool overcast fill' 220 W overhead + strong reflection lights + world .3
  -> pale roofs everywhere; draft: overhead 0 W, reflections ~8 %, world .015. (2) Screen 2's leaves are missing from
  the 'D12 unchanged cinema receivers outside restroom' collection (10/102 parts vs 102/102 for screens 1/3; they
  were posed open when memberships were assigned), so 9 lobby lights skip them; plus a wet-paint material mismatch.
  Draft fix: masked per-channel curve on door 2 in the 10 static plates (fixed nonnegative offset, loop contract
  kept; median [28,4,7] -> [90,20,33]). Full apply: 12 vehicle body renders + 56 slices + 10 plates + 2 door sheets,
  ~3-6 min locally. Claude's note: the after-cars look too dark (blue sedan reads plum, bus near-black). Waiting for
  the owner.

## 04 Nov 2026 - door, seated look, emote facing (Claude)
- Door: owner flagged the rear entrance as stretched + old (pass-9 porthole door scaled into the 2.35-tile portal).
  BRIEF-46 quick draft -> owner approved -> BRIEF-47 full pass: draft 12 = draft 11 + the lobby's current padded door
  at uniform scale (139/114, centred u 1.45, wall infill), lit + dim, 1x + 4K, slices, door sheets, cutout
  (`qa11/CINEMA-DRAFT-12.md`). Banded with `LAYOUT=cinema_layout_12.json node tools/band-slices.mjs qa11 64`
  (exact rebuild). Page default `?draft=` is now 12. Door opens and arrivals walk through (checked). 1440p full house
  ~101 fps seated, no long tasks (same as draft 11).
- Seated: emotes were raised (SIT_Z 48) so they looked perched with flat bottoms beside the backrest. Now cut along the
  backrest line also with depth slices, drawn at 1.2x (owner picked "A"); `?sitz=` / `?sitscale=` to compare.
- Facing: owner said Skip and other ambiguous emotes face the wrong way. Codex made an independent pass on large sheets
  (`reviews/facing2/emote-facing-2.json`, `tools/emote-sheet.html?big=1&labels=1&names=`); Claude checked all 67
  disagreements: Skip -> right, 44 labels changed (clear L/R fixes, near-frontal -> front). 10 ambiguous ones are with
  the owner (GIGACHAD, Normgasm, SICKO, ThisIsFine, POPPERS, NOTMYTEMPO, hesRight, WooYeah, YAM, hhhehhehe).
  Old table: `reviews/emote-facing.before-owner-review.json`.
- 04 Nov ~12:30 - Owner: "apply as drafted, but right-to-left cars drive almost on the opposite lane".
  Lanes: road v 10.6-13.5, dashed centre line at v 12 (build_scene.py); manifest lanes.far = 12 put -u traffic on
  the dashes. roxy.html now uses far = 12.75 (default and when the manifest says <= 12.05); checked with 4 passing
  -u cars. Draft 15 applied by Codex (BRIEF-47, NOTES-47.md) into out10b: 12 vehicle bodies + 56 slices (both
  scales), 10 static plates (Screen 2 offset), doors/screen_2 sheets, manifest lanes.far 12.75, checksums/validation
  refreshed, scene sources fixed for the next render. Claude checked: 705 checksums OK, 95 files differ from out10
  (92 images + 3 json), the three videos byte-identical, validation passed; live doors and 6 passing vehicles OK.
  Swapped: out10 -> out10.pre-d15, out10b -> out10 (revision 10b-local-draft15-brief47).
  Owner decided the 10 (04 Nov): current labels confirmed except POPPERS -> right, hhhehhehe -> right.
- Pre-show "Tonight:" (owner, 04 Nov): it showed the last watched film (history[0], Ali G). Now `upcomingFilm()` takes
  the winner of the newest film poll (details.polls endedAt) and drops it once it is rated or in history with that
  poll id; no unplayed poll winner -> "Tonight: Feature Presentation", no poster. Tested on live data (Last Night in
  Soho rated -> generic) and a made-up new poll (shown, then gone once rated).
- 04 Nov ~13:15 - Lobby behaviour (owner requests, roxy.html):
  - Talk spots per kind (SPOTS / HANG_P): lobby 3 (new one between box office and glass, layout 3), outside 2 on
    the sidewalk either side of the entrance (6.8 / 11.9, v 9.5), corridor 2 past the usher (5.9 / 11.4, v 2.15).
    Arrivals may stop outside before going in (50 % with something to say / 25 % without), lobby as before, corridor
    70 % / 35 %. Alone outside or in the corridor they move on after 7 s. Back from a sidewalk group they line up
    with the entrance first (no walking through the glass). Janitor chats stay a lobby thing.
  - Restroom: with layout 3, ~16 % of arrivals add a restroom visit (plus chat's ~5 %); before only ~5 %.
  - Run-overs: 6 % of arrivals on foot walk along the road with traffic; a moving vehicle that catches them:
    "BONK", knocked along 1.3 tiles, fade out, removed (riders at the curb and parked vehicles are safe).
  - Counter staff (cashiers, snack clerks) stand 18 px higher (STAFF_STEP); the usher unchanged.
  Simulated 5 min, 207 arrivals: up to 12 talking outside, 14 in the lobby, 3 in the corridor, 34 restroom visits,
  4 run-overs, 0 page errors; perf 1440p full house ~53 fps, p99 ~20.6 ms, 0 long tasks. Backup before:
  cloud/backup-run2/roxy.html.pre-perf (+ lane fix, wet-loop fix after it).
- 04 Nov ~13:45 - Every chat message is now shown once (owner: "show every one"). queueLine keeps up to 4 unsaid
  lines (a 5th says the oldest at once); soloSpeech says the next line 1.2 s after it arrives (or after their last
  bubble has been up a while) whenever the chatter is in view and not standing in a talk group; in a group they
  speak by turns as before. Arrival messages are said once they walk into view. HANG_P "without" chances raised
  (outside .35, lobby .5, corridor .4) since most say their arrival line on the way. Still max 4 bubbles on screen.
  Sim (new chatter / 6 s, message / 2.5 s, 3 min): 110 of 113 messages shown (3 still queued at the end), 0 errors.
  Perf 1440p full house with a message every 0.4 s: ~53 fps, p99 ~20.7 ms, 0 long tasks.
- Pre-show slides (owner): "Tonight's audience" -> "Tonight's movie chatters"; projectionist + snack-bar slides removed
  (3 slides now). Director checked live on this scene (first follow ~70 s, zoom 1.85).
- Props (owner): ~40% of arrivals carry the lobby's rendered popcorn (70%) / soda (out10/items, scaled by K), held over
  the backrest when seated; ~13% of seated chatters (`?phones=0..1`) take out a phone for 6-14 s every 25-70 s, a CSS
  phone with a blue screen glow (stands out with the lights down).
- 04 Nov ~14:30 - Speech bubbles (owner: they jump when making room; 4 is too few). Now: up to MAX_BUB = 8 on
  screen (?bubbles=2-14); new bubbles fade in (0.25 s), pushed-out/ended ones fade out (0.28 s) instead of vanishing;
  a bubble follows its speaker 1:1 but a change of spot (stacking/making room) moves on a critically damped spring
  (0.2 s scale); stacking tries up to 7 levels. Test (scratchpad bubtest.mjs, 45 chatters, a message / 0.6 s, 60 s at
  1080p): before - max jump 520 px in one frame, 90 jumps > 40 px, 4 visible; after - max 40 px, 0 > 40 px, ~7.7
  visible on average. 1440p full house perf ~53 fps, 0 long tasks. Comparison image qa10/bubbles-6-8-10.jpg.
- 04 Nov ~14:50 - roxy.html: (1) staff face their customers (faceStaff: cashiers -> window line, clerks -> register
  line, usher -> gate entry); FeelsGoodMan clerk now looks at the snack line. (2) Everyone carries an umbrella (was
  35 %); open outside, folds at the door as before. (3) Glass-front clipping: the glass is depth-sliced every ~0.9 tile
  and sorted at slice centres, so figures right at the glass got glass over them (outside) or sat over the glass
  (inside). frontV(): for u 2.9-13.1, outside within a tile sorts at v 10 (in front of every slice their sprite or
  umbrella can overlap), inside sorts at min(v, 16.85 - v) (behind them); the bus shelter area is unchanged.
  Checked in a simulated crowd (glass-front crops): no clipping, 0 errors. Owner's "floating thing": a small white
  rectangle baked at the curb by the bus stop (full.png ~(110,605)), drawn above near-lane cars via the bus_stop
  slices - BRIEF-48 to Codex (into out10c).
- 04 Nov ~15:10 - Floating white rectangle fixed (BRIEF-48, NOTES-48.md): the two number plates (+ "DGG 05" text) of
  the removed parked inspection bus were left in the scene - built inside build_pass10_draft6.py shelter() while the
  shelter layer was current, so prepare_scene.py kept them as bus_stop geometry and they were sliced above near-lane
  traffic. Codex removed them in out10c (19 files: full 1x/2x, occ_bus_stop + 3 slices, 3 wet_bus_stop sheets, json),
  inpainted from the clean already-rendered ground; loops untouched; sources fixed for the next render. Claude
  checked: 705 checksums OK, validation passed, before/after crop: both plates gone. Applied by copying the 19 files
  into live out10 (the folder could not be renamed while the server streams from it); originals in out10.pre-plates/;
  live out10 checksums all OK.
- Floor lights (owner): BRIEF-48 brightness draft, BRIEF-49 re-seated all 67 step markers as flat inserts on real
  surfaces (several floated), owner picked V2 45 %. BRIEF-50 full pass = draft 13 (`qa11/CINEMA-DRAFT-13.md`); banded
  (`LAYOUT=cinema_layout_13.json`), page default `?draft=` 13. Screen line "Moobies starting soon, take a seat...";
  popcorn ~85 % (80 % popcorn / 20 % soda), phones ~30 % (out 8-18 s every 15-45 s).
- 04 Nov ~15:40 - Queue quitters (owner): 6 % of people in the ticket line lose patience after 2.5-7 s (QUIT_P,
  ?quit=1 forces it for testing): a float ("nah, going home", "changed my mind", ...), out of the rope lane by its
  open end, back out of the entrance (umbrella reopens: giveUmbrella() now shared with spawn; drawFigure gives one to
  anyone stepping back out), wait at the bus stop door (1.2, ~10); the next bus is called within 6-14 s if none is
  coming; once it has stopped and its riders are off they walk to the door and fade in ("bye 👋" half the time); the
  bus waits for boarders (max 12 s past its dwell). Test with ?quit=1, 160 s: 9 quit, boardings seen, 0 errors.
- 04 Nov ~16:10 - Taxi roof sign (owner, via the intro session: "way too big"). Codex BRIEF-49 / NOTES-49.md: box
  0.34 x 0.46 tiles x 9 units -> 0.12 x 0.32 x 5 (roof footprint 55 % -> 13.5 %), smaller lettering/base, same
  warm emission and draft-15 studio light; the 4 taxi body states + all 32 taxi light maps (their wet-road sign
  reflection) re-rendered locally into staging out10d (58 files: taxi PNGs + checksums/validation; Claude checked).
  Draft qa10/draft16-taxi-sign.png sent; waiting for the owner's OK before copying into live out10.
- 04 Nov ~16:20 - Owner approved draft 16: the 58 taxi files copied from out10d into live out10 (originals in
  out10.pre-taxi/); live checksums all OK.
- 04 Nov ~16:25 - shared/emote-facing.json: WEOW "front" -> "left" (owner asked; its base frame is a 3/4 face turned
  to the viewer's left), so it now turns to face where it walks in both scenes. Backup cloud/backup-run2/.
- 04 Nov ~16:40 - Emote chat effects (owner: GSN shows emoji dolphins on top). DGG's emotes.css draws one-shot effects
  on ~20 emotes as text glyphs in ::before/::after (GSN 🐬🐬, BEARSLEEP 💤, PARDNER 🔫🔥, SNAP 💥, PepeHands tears, ...);
  they jump once in chat and hovered over standing emotes. shared/core.js textDeco() checks each emote name once
  (computed ::before/::after: text content and no background image) and marks it sb-nob / sb-noa; shared/base.css
  hides those. Image pseudo-elements (KYSNOW, BERN, RaveDoge) stay. Applies to both scenes and to bubbles.
  Verified in headless Edge. Backup cloud/backup-run2/base.css.pre-deco.

## 04 Nov 2026 - auditorium: "?" emotes recover
- Owner saw "?" instead of some chatters' emotes. Cause: the avatar check gave each cdn.destiny.gg image 5 s, and a full-house rush missed that; the "?" stayed for good, and Chrome keeps a failed CSS background broken for that emote class.
- Fix in auditorium.html (avatarLoads/checkAvatar): 12 s check, failures never cached, retries after 5/15/30/60/120/300 s, then the sprite comes back with an inline background-image (a fresh fetch).
- Test: emote requests failed for the first 15 s through CDP. The "?" marks clear by about 35 s and no chatter stays blank. Forwarded the lobby side to Lobby Map.
- 04 Nov ~17:00 - Emote load failures (tip from the cinema session): a cdn.destiny.gg emote image that fails left the
  chatter blank for good (Chrome keeps the failed CSS background for every element of that emote). roxy.html now
  does what auditorium.html does: checkEmote() after each setEmote - "?" while it fails, retries after
  5/15/30/60/120/300 s, failures never cached, on success an inline copy of the url. Test (CDP Fetch.failRequest on
  emote images for 15 s): 24 chatters "?" while blocked, all recovered within 25 s after, 0 errors.
- 04 Nov ~17:30 - Jannies (owner idea): the lobby starts with no janitor (?janitor=always = old penguin,
  ?janitor=3d = rendered one). Any message from a DGG moderator (features 'moderator', tagged or not) brings a cpMOP
  penguin wearing their name (mod colour, always shown) in from the staff corridor (J -> gate -> hub), "🧹 janny on
  duty", mops a free JAN_SPOTS spot 10-18 s, moves on; one per spot (4 max); their messages are said as bubbles;
  lonely chatters talk to any mopping janny (groups carry g.jan); 10 min without a message (?janidle=<s>) and they
  clock off back through the gate. Mods no longer walk in as chatters (shared/cinema.js walk-ins now carry
  `features`). Layout 3: janitor spot 2 moved to (6.7, 8.35) and reached round the rope lane's open end (the old
  route crossed the front rope). emote-facing.json: cpMOP "right". Test (?janidle=30): 0 -> 1 -> 4 jannies (5 mods),
  tagged mod did not walk in, all clocked off after idle, 0 errors.

## 04 Nov 2026 - auditorium: jannies (DGG mods) mop the front
- Owner, via the lobby session: "same thing should be in the auditorium scene, the jannies will mop the front part. never sit down."
- auditorium.html "jannies": any mod message (SB 'msg', features 'moderator') brings a cpMOP penguin wearing the mod's name in through the entrance. It goes down row B's aisle (u 3.475) to the front floor (v ~1.55, z 24) and mops one of 6 spots for 10-18 s before moving on; one janny per spot.
- Its messages show as bubbles. After 10 min without a message (`?janidle=<s>`) it clocks off back through the tunnel.
- Mods never walk in or sit (onMessage returns early for 'moderator'); a seated mod is swapped for their janny.
- Test: 5 mods + 2 tagged chatters, janidle=30. 5 jannies on the front floor, 0 seated mods, all clocked off by 100 s, 0 errors.

## 04 Nov 2026 - auditorium: dozing, phones in the dark, ban escorts, usher with a flashlight
- Owner picked 4 of the suggested ideas (3, 4, 5, 9).
- Dozing: a seated chatter quiet in chat (tagged or not) for ~10-16 min (`?doze=<s>` x 0.8-1.6) leans over, sinks a little, breathes, z's drift up (z's on at most 12 sleepers). Any chat message wakes them.
- Phones in the dark: with the lights down, 3 chat messages within a minute (`?chatty=<n>`) get the phone out (glowing). The nearest free janny walks into the row, "🤫 shh!", phone away, 2 min cooldown. No janny on duty: the usher does it after the current round.
- Bans/mutes: shared/core.js now also emits 'modAction' { kind, nick, by } before 'purge'. A seated chatter gets "🚫 banned" / "🔇 muted", the mod who did it (if on duty, else the nearest janny, else the mod is called in through the entrance) walks over, "👉 out", and follows them out through the tunnel, then comes back to mop. No janny possible: they leave alone. Not seated yet: removed as before.
- Usher: 4 s after the lights go down the lobby usher's emote (cap_usher) comes in, patrols the cross-aisle and stair aisles at 0.7x pace, shines along rows; whoever talks (a bubble) gets the light for 3.5 s. Never blocks or is blocked. Leaves when the lights come up.
- Tests (phase=dim, doze=25): usher in, beam on the speaker, phone + shush at 11 s, ban by an off-duty mod -> called in, escorted out; mute by an on-duty janny -> escorted out; dozers asleep and woken; usher left 30 s after phase up. 0 errors. Not checked in OBS.

## 04 Nov 2026 - splash mist samples (BRIEF-50, not live)
- Owner wants heavy-rain splash mist on every surface; asked for Claude's and Codex's versions side by side.
- Codex: out10mist/ surface passes (catch, rim, light, height; 1x + @2x) + baked sample qa10/draft17-mist-baked.png (NOTES-50.md).
- Claude: runtime layer in roxy.html behind ?mist=1|2|3 (masked scrolling noise haze + splash crowns, additive, under the rain);
  off by default. Sheet qa10/draft17-mist-claude.png. 1080p perf with mist=2: 53 fps, same as without.
- Owner: animated layer is the way, but v1 "not great"; wants 3-4 different takes. Rewrote the layer as one WebGL shader
  (masked fbm noise, spray rising from surfaces via 14 jittered taps down-screen, procedural splash crowns) with four
  styles behind ?mist=1..4 (+ ?mistgain=): 1 splash sparkle, 2 edge spray, 3 lamp-lit mist, 4 wind sheets.
  Samples qa10/draft18-mist-style0..4.png (0 = live today). Perf with style 3: 53 fps at 1080p and 1440p, 0 errors.
  Backup before: cloud/backup-run2/roxy.html.pre-mist. Still off by default.
- Owner picked style 2 (edge spray): now the lobby default (?mist=0 off, 1|3|4 other styles). Splash dots on unlit
  roofs toned down (air term .5). Perf at 1440p with the default: 61 fps, 0 errors. Needs out10mist/ next to out10/.
- Owner on the live style 2: "looks as if there was water boiling off the edges" -> back to off by default
  (samples stay behind ?mist=1..4).
- Extra rain samples (owner asked if more rain is easy): WebGL layer #rain2 over rain_fg, ?morerain=1..4
  (+ ?moreraingain=): 1 denser, 2 downpour (+ long near drops), 3 curtains (gust bands), 4 downpour + splash crowns.
  Lit by out10mist/light.png, masked out of the building. Shared helper glLayer() now also drives the mist.
  Samples qa10/draft19-rain-style0..4.png. Off by default.
- Crowd control (owner: skip people when there's a huge queue outside): spawn() skips new chatters once >= CROWD (14)
  people are outside or in the ticket line: every 2nd walks in, every 3rd from 21, every 5th from 28 or a full house
  (CAP 40). Returning chatters still talk, host always walks in; ?crowd=<n>, ?crowd=0 = off. Flood test (4 new
  chatters/s, 90 s): outside/in line ~15-22 with it vs 45-56 without, 0 errors.
- Owner liked all four rains -> weather: the extra rain is now ON by default and drifts between light / steady /
  downpour / curtains / deluge (hold 40-120 s, 12-20 s crossfade; ?weather=<x> speeds the clock, ?morerain=0 off,
  1-4 fixed). Rain now falls in front of the cinema's outer walls (mask = wall-top outline only, not the whole
  building). Owner: "rain is way too fast" -> streak speeds 900-2100 -> 380-820 px/s (time-based, not frame-based),
  near drops shorter (52 -> 30 px). 1440p perf 61.8 fps, 0 errors.
- Extra rain stepped at 24 fps like the baked loops (manifest fps 24); ?rainfps=0 smooth. Redraws only on a new step.
- Rain on umbrellas / vehicle roofs: tried in-page canvas splashes (per-sprite canvases from alpha top bands); owner:
  these "more permanent" effects should be rendered, they look better -> runtime code removed (page as before,
  smoke test 0 errors). BRIEF-51 to Codex: draft of rendered umbrella rain loop, vehicle-top impacts overlay and
  continuous tyre spray + wake (staging out10e/, owner image qa10/draft20-rain-umb-veh-tyre.png).
- 04 Nov 2026 - auditorium (owner requests): emotes 10% smaller (EH 45*K); OMEGALUL, TF, dggL, LOCKEDIN, LULW labelled "left" in shared/emote-facing.json; the front (wheelchair) row takes all 13 yee emotes from the DSA script's IDEOLOGICAL_EMOTE_MAP. qBittorrent integration verified live with a real download (Phone Booth). Loading slide: narrower bar with spacing, a DGG meme card (emote + caption, 8 jokes from memes/SHORTLIST.md, next one each time the slide comes round), chat's top emote of the last 3 min riding the bar, chat emotes floating up the outer edges while it loads (?qb=<0-1> fakes a download). Lights down: emotes and held items dim to 50%; 10 s in, the director pushes onto the screen (same framing every time, for the OBS corner-pin; no auto follows while the lights are down; W cancels; director=0 keeps it wide). Usher: walks over to whoever talks in the dark, shines the light up close, 50% chance it walks them out ("kicked"; ?kick=<0-1>); talkers queue. standby-server.js: a download seen finishing counts as recent even with a stale completion_on (needs a server restart, asked Lobby Map).
- 04 Nov 2026 - auditorium: server restarted by the owner; full real-download run verified (White Christmas: dim at 90 %, "ready" at 100 %, film ~10 s later, camera on the screen, 0 errors). Loading slide now shows what is downloading: torrent name parsed (tracker "Рус / English (Dir) [year, ...]" and scene "Title.S03.1080p..." styles) and looked up on Cinemeta (v3-cinemeta.strem.io, keyless, CORS open): poster (images.metahub.space), title, release year, genres, IMDb rating; cached a week in localStorage. "Tonight" falls back to it when no film poll is up. Test: ?qb=0.42&qbname=<torrent name>.
- BRIEF-51 draft delivered (Codex, local Cycles): out10e/ red umbrella wet loop (88x80, 24f), taxi/bus roof
  impact overlays, bus/sedan continuous tyre spray (all 24 f @ 24 fps, 1 s). Owner image qa10/draft20-*.png.
  Claude's read: physically fine but too faint to read at 1x (roof crowns, spray); shown to owner, waiting.
- Owner: 'make a stronger pass'. Codex read-only critique (codex-51-critique.txt) gave px/rate/brightness targets; BRIEF-52 -> out10f/, owner image qa10/draft21-rain-stronger.png composited into the real frame at 1x and 2x.
- Owner approved draft 21 as is ('go with draft 21 and that's it'). BRIEF-53: production set (4 umbrella colours, all vehicle tops sliced, spray+wake all types/dirs) -> staging out10g/, local GPU (owner asked about RunPod: not worth it, ~30 min GPU work). Claude wires umbrella.wet / roof_rain / spray / wake into roxy.html after.
- roxy.html wired for BRIEF-53 keys (inactive until the pack has them): umbrella.wet[c] loop replaces the open sprite; vehicles[t][dir].roof_rain per slice (additive, z = its slice); spray (z above body) + wake (road layer 4) fade in with speed; old one-shot tyre spray only without the loops. Smoke test on live out10: 0 errors.
- BRIEF-53 production delivered (Codex, local, 27 min GPU): out10g/ with 96 new PNGs (48 loops, 2.8 MiB; 40 MiB
  decoded at 1x, 160 MiB @2x): umbrella.wet x4, roof_rain per slice for all 4 vehicles x 2 dirs (+ door_open),
  spray + wake for all. Slice reconstruction exact (NOTES-53). Tested with ?artdir=out10g: wet umbrellas, roof
  loops, spray/wake fading with speed, 0 errors; 1440p 52.9 fps vs 53.4 without. LIVE: the 96 files + manifest /
  checksums / validation copied into out10 (originals of the 3 JSONs in out10.pre-rain/); 801/801 checksums OK.
- 05 Nov 2026 (night) - QA + performance session (owner's overnight goal): fixes in copies only, live pages untouched: standby/roxy-qa.html and standby/auditorium-qa.html, patches roxy3d/qa-night/roxy-qa.patch + auditorium-qa.patch, full report with measurements roxy3d/QA-REPORT.md. Lobby 55 -> 105 fps (blended rain_fg video capped Edge at ~52 Hz; now drawn in the #rain2 pass, pixel-identical), camera freeze on rider follow fixed (froze all speech), bubbles no longer overlap; auditorium 52 -> 114-146 fps uncapped (identity filters removed), plus stuck/leak fixes from code reviews.

**05 Nov 2026 - QA copies promoted to default (owner request):** roxy.html, auditorium.html, control.html and lan-proxy.js are now the QA versions (byte-identical to roxy-qa.html, auditorium-qa.html, control-qa.html, qa-night/lan-proxy-qa.js). Originals backed up in standby/backup-2026-11-05-pre-qa/. Smoke test through the server, real chat, 1440p, 60 s each: lobby 122 fps, auditorium 123 fps (headless 120 Hz), 0 page errors. Not promoted: shared-qa/ (used by ~20 other scenes) and standby-server-qa.js (needs a server restart).

**05 Nov 2026 - shared scripts + server promoted (owner request):** shared/core.js, cinema.js, live.js = qa-night/shared-qa/*, standby-server.js = qa-night/standby-server-qa.js (takes effect at the next server restart). Originals in standby/backup-2026-11-05-pre-qa/ (shared/ subfolder). Smoke test, real chat, 1440p, all 19 scenes that load shared/: all render, no errors from our files; the only messages come from the destiny.gg chat iframe (autofocus notice) and the DSA relay (emotes.click 502), same as before.

**05 Nov 2026 - Lobby Map: owner's fix list on the promoted roxy.html:** (1) everyone lines up for tickets (the random 12% skip is gone; only a full house = CAP or a line past its 14 places skips), layout 3 line snakes: 7 in the rope lane + a second row back along v 8.25; (2) walking pace 75% while the lobby has room, back to full speed between 70% and 85% of CAP (eased), hops slow with it; (3) held sodas/popcorn/ticket stubs at 2x size (HELD, @2x files); (4) BINGQILIN staff emote gets a 14 px "chair" (STAFF_CHAIR); (5) walkers past the usher go through GATE_OUT [3.75, 2.45] before J, no longer over the restroom corner; (6) black lines on the TICKETS/SNACK BAR signs: each depth-sliced occluder also gets its whole image underneath at its lowest slice z (fills the antialiased slice seams that showed the restroom floor); the black bar beside the box office was the restroom side wall's slice 01 shaded face drawn over the ticket wall - clipped to its top cap. Verified headless: 0 errors, sign seams/bar gone, 90 s chat flood fine. Still open: faint diagonal seams on the restroom wall's top cap (restroom slices sit over the ticket wall's dark top band); rain on the right cutout / window rain (asking owner). BRIEF-54 (DINK DONK "CINEMAS" line + bell at half speed) running as a Codex draft. Idea 48 (24 vs 48 fps test) logged in QUEUE-owner.md.

**05 Nov 2026 - Lobby Map, rain follow-ups (owner):** right cutout strip (u 13-15.6 by the ABSOLUTE CINEMA annex) dry: the rain mask now has two channels (red = extra rain, green = baked rain_fg inside the rain2 pass); the strip polygon up to the roof line is dry for both where the height pass < 60, the taller roof in front keeps its rain. Window streaks: the extra rain's drop light came from the surface light pass, black over the glass front -> dim grey-blue streaks there vs lamp-lit ones on the street; holes now filled with blur(light)/blur(catch) at quarter size (airL). Headless check: 0 errors. Draft 22 (BRIEF-54, DINK DONK CINEMAS + bell 12f/state) shown to owner; Codex critique in codex-54-critique.txt (tracking, 18 px bulb clearance, +2 bulbs per upright, S not $, mounts, floodlights); production estimate 5-10 h local.

**05 Nov 2026 - DINK DONK sign:** draft 23 (BRIEF-55, cleanup of draft 22 per codex-54-critique) approved by the owner ("Yes, render it"); BRIEF-56 production started with Codex (local GPU, staging pack out10i/ + out10i-copy-list.txt, plus the floodlight re-aim from codex-55-critique point 7). Live out10 untouched until Claude tests ?artdir=out10i.
- 05 Nov 14:45 - Owner: "use the GPU remote for this". Local BRIEF-56 run stopped at 34/48 background frames
  (3050: 423 s/frame vs 48 s on the run-5 5090); out10i/_work kept as fallback. BRIEF-57: Codex packs the frozen
  production scene (sign + floodlight re-aim, bell A12/B12) as cloud/roxy-cloud-bundle-56.tar.gz and makes
  cloud-render.sh take ARCHIVE/OUTDIR overrides; Claude then runs it on RunPod (balance $11.62, expected ~$3-4).
- 05 Nov 14:50 - BRIEF-57 done (NOTES-57.md): cloud/roxy-cloud-bundle-56.tar.gz (160 MiB, sha cb6d3387...), local
  preflight + smoke passed, all 8 mist maps included. Claude started the cloud run in Terminal tab "RunPod sign render":
  ARCHIVE=...bundle-56 OUTDIR=roxy3d/out10i.cloud cloud-render.sh full. RTX 4090 SECURE, EUR-IS-1, pod dhc93hhfxqwvi1,
  network volume lbx8rc3twh. Pod preflight passed 14:57, backgrounds stage started 14:58.
- 05 Nov 17:53 - Cloud run done (4090, 14:51-17:53, exit 0, DONE). Result checksum OK, unpacked to out10i.cloud/out10/
  (118 entries incl. 8 mist maps); pod + volume deleted; balance $11.62 -> $8.87 (~$2.75). BRIEF-58: Codex merges into
  out10i, decodes/QA all loops, makes qa10/draft24, copy list and NOTES-56. Then Claude tests ?artdir=out10i&mistdir=out10i.
- 05 Nov 19:20 - BRIEF-58 done (NOTES-56.md, qa58/final-validation.json passed: 432 video frames, A12/B12, wraps,
  alpha/depth, Brief 53 identity). Claude tested ?artdir=out10i&mistdir=out10i&everyone=1 (0 errors, sign + CINEMAS ok,
  restroom slice geometry unchanged so the seam/clip fixes still apply). PROMOTED: backups out10.pre-sign/ and
  out10mist.pre-sign/; copied the 452 listed files (444 CHG -> out10, 8 mist -> out10mist), sha256 all match; out10 ==
  out10i (minus _work and mist). Live page check 0 errors (qa10/live-after-sign-20261105.png). Not checked in OBS.
  Cleanup later with owner OK: out10i.cloud (990 MB), out10i/_work (local fallback), the .pre-sign backups.
- 05 Nov 19:30 - Owner OK'd cleanup: deleted out10i.cloud/, out10i/_work/ (stopped local fallback), cloud/result-full.tar.gz,
  cloud/brief57/verify/. Kept: out10i/ (staged pack == live), out10.pre-sign/, out10mist.pre-sign/ (rollback),
  cloud/roxy-cloud-bundle-56.tar.gz + brief57 build scripts (to re-run the sign render).
- 05 Nov 19:45 - Owner: extra rain looks much faster than the baked rain; wants a control to pick the speed. roxy.html:
  streaks run on their own clock (uS = rainClock += dt * rainSpeed); ?rainspeed=x (0.1-2, default 1 until owner picks),
  ?raintune=1 shows a slider (top left) with the value. Splash crowns/gusts keep page time.
  Owner: the wcat chatter emote faces the wrong way. shared/emote-facing.json wcat front -> left (3/4 view turned to
  the viewer's left; backup qa10/emote-facing.pre-wcat.json), so it now turns to face where it walks.
- 05 Nov 20:00 - Owner: rain speed varies 0.20-0.40 like the intensity. WEATHER entries got a 5th value (fall speed):
  light 0.20, steady 0.26, curtains 0.30, downpour 0.34, deluge 0.40; crossfades with the weather (12-20 s), the
  streak clock integrates so nothing jumps. ?rainspeed=x / the ?raintune=1 slider fix it for testing. Verified with
  ?weather=40 (0.20..0.40 seen), live page 0 errors.
- 05 Nov 20:30 - Owner wants a squarer OBS browser source without black bars -> "crop the sides". ?fit=cover:
  shared/core.js mountStage(el, {cover}) scales to fill (max) and exposes SB.view (visible stage rect; default
  contain = unchanged for every page). roxy.html: wide shot centres on WIDE_X 1040 (?fitx=), camera clamps to the
  visible half size, onScreen + bubble placement stay inside SB.view, art/loop resolution picked from the cover
  scale. Tested 1500x1080: view [210..1710], lobby + whole sign in frame, 0 errors (qa10/fit-cover-1500x1080.png);
  1920x1080 without fit unchanged, 0 errors. OBS source not changed (owner adds &fit=cover + its size).

## 05 Nov 2026 - auditorium: house-lights fade even across the room
Owner: "lights up and lights down are scuffed" (dark stripes over the seats, the stair/exit block lit differently).
Cause: slice dim twins were shown/hidden with `display`, so a twin started at its end opacity instead of fading:
pieces with a chatter behind them went dark at once on lights-down and popped lit on lights-up while the room took 6 s.
Fix: one `@property --dim` on #stage with a 6 s transition drives every `.dim-art` opacity, and `cullPieces` keeps the
twins up for 6.5 s after lights-up. Headless check: twin opacity = background dim at every step, 0 errors.
- 05 Nov 21:00 - Owner: emotes "going over the back wall of the snack bar". Cause: the corridor talk spots (SPOTS.hall
  c [5.9,2.15]/[11.4,2.15]) sat in the strip behind the snack bar's tall back wall (floor hidden for v > ~1.6), so
  only heads showed above the wall top. Moved to c [6.3,0.85]/[9.7,0.85], r 0.28 (between the screen doors, in front
  of the v 1.4 walking line, clear of standees/extinguisher). Sim: no one stops behind the wall any more, group fully
  visible (qa10/hall-spots-moved.png), 0 errors. Clerks checked: heads stay 45-58 px under the wall top.
  Owner's "lights up / lights down are scuffed" (auditorium) forwarded to Cinema Screen Map.
- 05 Nov 2026, rename + GitHub: the owner asked to drop the "roxy" name. roxy.html -> lobby.html, roxy-qa.html ->
  lobby-qa.html; roxy*.html are now redirect stubs that pass the query string through (OBS URLs keep working). The old
  concept lobby.html moved to concepts/cinema-lobby.html. Titles/labels updated (index, control, README, package/build.js).
  roxy3d/ folder and the 'roxy-<role>' emote keys are unchanged. Backups: backup-2026-11-05-pre-lobby-rename/.
  standby/ is now a git repo pushed to github.com/reothrowaway/dinkdonk-cinema (public): source, docs, blends,
  out10 + out10mist, and the qa11 files auditorium.html loads (package/art.js). Draft/QA/old packs/caches stay local
  (.gitignore). The "Lobby and auditorium OBS package" session was told to switch web/ to lobby.html.
- 05 Nov 2026, packaging + hosting (OBS package session): package/build.js builds dist/DinkDonk-Cinema.zip (lobby,
  auditorium, only the art they load via package/art.js, chat relay, OBS collections 1080p/1440p/2160p with lobby.html
  URLs, START.bat). web/ is the hosted edition (web/README.md): web/server.js (room keys, one shared DGG chat upstream,
  per-room control panel, emote/dinkdonk cache), web/shim.js injected into lobby/auditorium/control (adds the key,
  runs the film-screen bridge in the page: direct to OBS 4455, or relayed through the server to the control panel for
  OBS 33+, whose Chromium blocks websites from reaching 127.0.0.1), web/setup.html (creates the OBS scenes over
  obs-websocket, any film source), web/admin.html (invites). Live pages are not edited; the builds copy them.
  Tested locally on 18772 with real chat and a mock obs-websocket: setup, direct and relay film pinning, film off when
  the auditorium closes, per-room isolation, revoke. Not deployed yet: no SSH access to the Hetzner server
  (2.29.56.208); web/deploy/deploy.sh is ready once access is added (web/README.md, "Server access").
- 5 Nov 2026, local Windows startup: added START-CINEMA.bat, hidden VBS/PowerShell launcher and a parent
  MovieStream/start_cinema.bat entry point. Starts the existing standby server on 18770 and a new read-only
  aiohttp public DGG chat relay on 18765, with logs in LOCALAPPDATA outside the repo. Opens control.html in the
  default browser after readiness checks. Reuses matching processes; refuses unrelated port owners. Existing
  scene pages, OBS configuration, original launcher and trivia profiles remain unchanged. LOCAL-START.md documents
  use and prerequisites. Both ports were free before startup; no other inspected MovieStream project used them.
  Verified real NAMES/MSG frames through the local relay, live upstream health, repeated startup with identical
  process IDs, and the batch launcher opening Cinema control in Chrome. Movie corner-pin bridge remains a separate
  OBS integration step. No commit or push.
- 5 Nov 2026: renamed the parent launcher to cinema_dgg_lobby.bat at the owner's request; updated local startup notes.
- 6 Nov 2026: located installed Blender 5.2.3, matching production. Created a hash-verified pre-edit snapshot in
  sibling dinkdonk-cinema-backups/20261105T225845Z (11,353 files, 920,675,451 bytes), including runtime assets,
  code/launchers, original top-level Blender sources/scripts and current cloud lobby source. Created local-only
  roxy3d/current with auditorium, auditorium-dim and lobby working scene copies, preview/staging folders, source
  mapping and dependency/verification reports. Background Blender checked packing and reopening of the copies:
  no missing images/fonts or linked libraries; historical appended-asset filenames are weak metadata only.
  10,984 protected original files verified unchanged. No scene edits, render, live promotion, OBS changes or
  plugin installation. Original historical builder chain remains in place; missing untracked QA inputs mean a
  portable layered exporter is a separate task. Added CURRENT-WORKSPACE.md and reproducible preparation helpers.
- 6 Nov 2026: installed community MCP for Blender at the owner's request. Installed uv through winget, pinned
  the MCP server to 2.2.7, installed/enabled its Codex plugin and Blender add-on, and backed up Codex config and
  Blender preferences under LOCALAPPDATA/CodexIntegrations/blender-install-backup. Listener restricted to
  127.0.0.1:9876, telemetry off. Opened the isolated auditorium working copy and verified actual MCP stdio
  initialization, 14 tools and successful read-only scene inspection (3,024 objects). No art files saved or
  rendered. Codex restart required for this existing chat to load the new plugin tools.
- 6 Nov 2026: added local one-source cinema.html with host-panel Show lobby/Show auditorium controls. Added
  validated/persisted presentation commands and output heartbeats to the server; retained origin and JSON guards.
  Shared core propagates OBS detection only for managed same-origin children so the existing film bridge can
  work when the auditorium is embedded. One room runs at a time: switching reloads transient room state.
  Backed up affected files in sibling dinkdonk-cinema-backups/20261106-single-source-before. Built/tested in QA
  on 18771 before promoting control and cinema pages. Verified browser switching in both directions, real DGG
  arrivals, auditorium lighting, no captured browser warnings/errors, JS syntax, persistent selection file,
  rejection of invalid views/foreign Origins/non-JSON commands, and a clean scoped design detector pass.
  Confirmed OBS absent and zero OBS screens before restarting this checkout's own server on 18770; final local
  browser verification passed. Did not alter OBS collections, render art, add media sources or deploy remotely.
- 6 Nov 2026: corrected combined-source continuity at the owner's request. Both rooms now load once into
  fixed full-size frames and stay connected to chat with their simulation running. Show controls change opacity,
  focus and input/accessibility visibility only. No navigation or unloading occurs when switching. Added managed
  output visibility to shared core; auditorium bridge sends film=false while hidden without resetting its phase.
  Backups in sibling dinkdonk-cinema-backups/20261106-persistent-scenes-before. Tested QA on 18771: identical
  scene IDs after repeated switches; hidden audience growth in both rooms; dim phase preserved on return; both
  frames 1280x720. Regression check verified bridge film false/true/false across hide/show/hide without changing
  film phase. Promoted and refreshed the user's Chrome preview once: both frames 2560x1215, both logical stages
  identically scaled to 2160x1215 (16:9 fit), and live instance IDs stayed unchanged through switches. One captured
  MutationObserver error had no matching code in the project; no claim of a clean browser console. Updated panel
  help/docs. No Blender edits or renders, OBS collection edits, server restart or fake chat.

- 6 Nov 2026: connected the combined source's real guest journey at the owner's request. Added shared/journey.js
  with per-output, case-insensitive membership and buffered auditorium delivery. Lobby door completion now
  transfers the same nickname, avatar and carried snack into the auditorium entrance/seat queue. Raw chat updates
  theater guests instead of admitting them independently. Staggered lobby arrivals at 1.4-2.2 seconds with a
  deduplicated FIFO, crowd/capacity pauses, quiet expiry and waiting roster. Staff/manual host overrides retained.
  Backed up live/QA pages to sibling dinkdonk-cinema-backups/20261106-handoff-before; implemented and checked
  QA on 18771 before promoting. Seven Node tests passed, including actual lobby queue draining under virtual
  time; inline JS syntax checks passed. Real DGG QA observed 25 transfers, 17 seated and zero regular-guest
  nickname overlap between rooms. Live Chrome preview refreshed once and verified two current room instances
  with new gradual auditorium arrivals. A captured MutationObserver error has no matching project code; no clean
  console claim. Existing single-source URL remains. No live server restart, OBS collection edits, fake scene
  traffic, Blender edits or renders. Updated launch and shared-server documentation.

- 6 Nov 2026: made combined-source lobby admission dynamic at the owner's request. Small queues retain
  1.4-2.2-second spacing; 6-11 waiting use 0.9-1.4 seconds; 12-39 form pairs and 40+ groups of three,
  0.25-0.45 seconds apart with 0.9-1.4-second group pauses. One spawn per tick, FIFO, crowd/capacity
  checks and quiet expiry retained. Backed up lobby live/QA in sibling
  dinkdonk-cinema-backups/20261106-dynamic-arrivals-before. Changed QA first, passed all eight Node
  tests and inline JS syntax checks, then promoted lobby.html. Virtual-time checks cover group size,
  spacing, crowded/full pauses, no catch-up flood, FIFO and return to slow spacing. No browser chat
  injection, live server restart, OBS changes or art work. Existing loaded outputs need one refresh.

- 6 Nov 2026: fixed Explorer-launched bridge and cinema startup when Node is absent from the inherited PATH.
  Both launchers fall back to standard Node install paths and the existing Codex Node runtime. Added bridge
  --check-runtime for a non-starting diagnostic. Backups in sibling 20261106-node-launcher-before folder.

- 6 Nov 2026: matched obs-bridge.js to the owner's OBS scene name dggCINEMAtheatre.
  Replaced the upstream collection-name error hint with the actual expected scene/source names.
  Backed up bridge in sibling 20261106-bridge-scene-name-before folder; Node syntax check passed.

- 6 Nov 2026: changed the bridge capture source name to firefoxBrowserCinema at the owner's request.
  Main scene remains dggCINEMAtheatre. Updated shared-server documentation and passed Node syntax check.
  Bridge backup in sibling 20261106-bridge-firefox-source-before folder.

- 6 Nov 2026: traced port 18790 conflict to the earlier running obs-bridge.js process.
  Added an explicit duplicate-port error message instead of an unhandled Node stack trace.
  Kept page/bridge ports aligned. Automated restart was blocked by execution policy; owner must
  close the previous bridge console and relaunch. Backup in sibling 20261106-bridge-port-guard-before.

- 6 Nov 2026: added separate mpv.net and Firefox bridge preset launchers, with OBS_FILM_SOURCE
  selection and automatic hiding of the alternate preset capture after target/filter setup. Both use
  the existing auditorium connection on 18790; only one bridge runs at a time. Backed up bridge and
  base launcher in sibling 20261106-mpv-bridge-before. Node syntax passed, both batch runtime
  diagnostics passed, and isolated setup checks verified correct target filters/alternate visibility
  for both presets. Updated setup docs. Live mpv capture awaits owner OBS setup; did not restart
  the current bridge or edit OBS collections.

- 6 Nov 2026: implemented auto-fit for changing capture window dimensions/DPI via bridge-sizing.js.
  Read live OBS structure: firefoxBrowserCinema is a direct Window Capture, canvas 1920x1080; mpvCinema
  is not present yet. Main shader item now uses a fixed full-canvas stretch box; nested helpers fit capture
  children inside their canvas with aspect ratio and child crops retained. Included the module in packaging.
  Backed up code and live transforms to sibling 20261106-auto-fit-before; applied Firefox sizing via
  obs-websocket and verified 1920x1080 stretch bounds at origin, zero rotation. Current running bridge
  left connected; OBS maintains persistent bounds. Future mpv setup gets sizing when its bridge starts.
  Eleven Node tests passed (three sizing cases plus eight journey regressions), bridge/module syntax passed.
  Did not move/resize the owner's actual windows, edit live collection JSON, restart server, or render art.

- 6 Nov 2026: replaced exclusive Firefox/mpv bridge presets with one unified bridge, selected by OBS
  source eye icons as requested. Added bridge-captures.js with independent user selection and automatic
  host visibility gating; consumes own visibility echoes, keeps both shaders current, hides other capture
  before enabling selection. Configures both available captures for auto-fit/filter setup, handles optional
  missing sources and OBS item/name changes. Legacy launchers now alias the same bridge. Updated packaging
  and docs. Backup in sibling 20261106-unified-bridge-before. Identified Game Capture targeting mpvnet.exe
  in the main scene and renamed it mpvCinema via OBS API, saving its prior transform/name in backup.
  Seventeen Node tests passed and syntax checks passed. Live non-streaming OBS check passed Firefox-to-mpv
  selection, lobby hides both, auditorium restores mpv, and both shaders configured. Restored host phase/view.
  Unified bridge now running on 18790. The initial combined process-management command was policy-blocked;
  found port free, started the bridge directly in an owned tool session, and restarted only that session after
  the source-name event update. No OBS collection JSON edits, live-server restart, art work or fake chat.

- 6 Nov 2026: corrected unified bridge eye-control UX after the owner reported eyes switching back off.
  Diagnosed auditorium dim phase with film=false. Added local cinema-screen.shader derived from the
  installed GPL corner-pin shader (attribution retained), with Cinema_Visible alpha gate. Host gating
  now hides pixels rather than toggling the selected source eye. OBS eyes remain a stable source selector;
  switching still disables the other capture. Updated filters to load the local shader and packaging to
  include it. Backups in sibling 20261106-eye-controls-before. Restarted only the owned bridge session.
  All 17 tests and syntax checks passed. Live non-streaming OBS verification passed selected eye remains
  on in dim/lobby, Firefox-to-mpv switches the other eye off, and movie mode toggles shader visibility.
  Real source screenshots verified hidden alpha=(0,0) and visible alpha=(0,255); artifacts in backup folder.
  Restored host view/phase with mpv selected. Bridge running with fix; no server restart or art edits.

- 6 Nov 2026: refined eye behavior per owner: Show lobby disables both capture eyes, return to auditorium
  restores selected eye regardless of movie phase. Bridge polls confirmed presentation separately from film
  flag; phase gating remains shader alpha. Backups in sibling 20261106-lobby-eye-gate-before. Eighteen tests
  passed; live OBS check passed auditorium Firefox eye on -> lobby both off -> auditorium Firefox restored.
  Restored previous host view; restarted only owned bridge, with no cinema source reload/audience reset.

- 6 Nov 2026: updated parent cinema_dgg_lobby.bat startup chain to include hidden unified bridge,
  reusing existing service on 18790 with ownership/health checks. All ports checked before startup;
  foreign listeners rejected without stopping them. OBS manual, host opens as before. Ports
  18765/18770/18790 currently owned by cinema services; scoped other-project launcher scan found
  no matching references. Backup in sibling 20261106-full-launcher-before.

- 6 Nov 2026: made the bridge console visible in the main launcher at owner request. Server/relay
  remain hidden, running bridge is reused, OBS manual. Removed bridge output redirection so console
  displays diagnostics. Backup in sibling 20261106-visible-bridge-before.

### 6 Nov 2026 — Seated auditorium POV

Saved a separate local Blender file at `roxy3d/current/sources/auditorium-seated-pov.blend` with a linked auditorium scene and a seated camera at F11. The slight off-center angle keeps all four screen corners visible and fills roughly 88% of the frame in each dimension. The POV scene custom properties store the projected quad in the OBS bridge's 1920×1080 coordinate format for later wiring. A top-edge ray check confirmed the framing stays below the front wall cap.

Added a ceiling, a right acoustic wall and an upper rear wall to the seated POV scene. A wide camera preview confirmed the gaps are closed. Restored the F11 playback framing and verified that the stored OBS quad still matches all four screen corners.

Refined the POV enclosure with charcoal acoustic ceiling panels, recessed amber strips, and right wall pilasters and sconces. Verified in a wide material preview, then restored the playback framing. The enclosure is exclusive to the POV and all 1,620 seat objects are shared with the wide view. The playback screen quad still matches.

Moved the POV to F10, matched the right sconces to the left wall's burgundy finish, and softened the ceiling panel seams. Exported a 2000x1125 viewport plate and added POV view to the host controls. Isolated browser QA verified that POV and Movie use separate bridge quads while the auditorium instance stays mounted. Backed up the live pages before promotion.

Widened F10 to 21 mm and exported a 4K Workbench plate, perspective camera matrix, and 480x270 room-depth grid. The seated POV draws the existing live walkers through the F10 projection and clips them behind room geometry. Verified real DGG arrivals, visible sprite movement and seat clipping on a separate QA server. Switching back to Movie kept the auditorium instance mounted. Backed up the live page and Blender file before promotion.

Reduced POV sprite size, capped foreground scale, and faded avatars near the lens and movie frame. Real-chat QA confirmed movement, seat occlusion, and screen clearance.

Calibrated seated POV avatars against the projected Blender seat-back meshes. The front row shows an 11 px resting peek, with up to 23 px on the rows behind. Tilted F10 slightly down to include more seats and re-exported the matching plate, depth grid, and OBS quad. Live-chat QA captured correctly anchored seated heads in rows B, C, and D.

Increased seated POV avatar size with a distance-based scale. Verified resting peek heights of up to 18 px in B, 38 px in C, 44 px in D, and 52 px in E. The calibrated chair cutouts and movie margin still apply.

Adjusted seated POV scale relative to the previous sizes: row E +60%, D +40%, C +10%. Verified the calibrated head positions still leave the film area clear.

- 6 Nov 2026: copied cinema_dgg_lobby.bat into the repository for the owner's PR. Adjusted its
  START-CINEMA.bat path for the repository location. Verified DGG GitHub login dggTrivia and all
  18 existing Node tests passed. Original parent-folder launcher remains available.

- 6 Nov 2026: added PR-CHANGELIST.md with the upstream-relative feature summary, required OBS
  scene/source names and ports, validation, local Blender sharing requirements, and POV limitations.
