# Standing goal: keep improving The Roxy (overnight loop, started 01 Nov 2026 ~22:45)

Owner's words, condensed: keep improving all of it on your own; expand on the concept with your own
features; do real QA passes; use Codex (gpt-6-astra) for a share of the work - two AIs split the
tasks. Stop when Claude's weekly usage ("Weekly · all models" in get_usage) reaches **35 %**
(it was 25 % at the start) or when the result is genuinely good, whichever comes first.

## The product
`standby/roxy.html` - OBS standby screen. Late-90s pre-rendered isometric look (Diablo 2, Fallout,
The Sims 1): rainy night 90s cinema. Pre-rendered still + pre-rendered seamless ambient light loop
(rain, splashes, reflections, neon flicker) from Blender; live DOM layer on top: chatters as hopping
emotes with bubbles (only chatters who tag arealhumanbean walk in, unless ?everyone=1), door titles,
posters, counters. Green screen = DinkDonk poll billboard at x1296 y40 576x324 (never cover it).

## Split of work
- **Codex** (`codex exec` / `codex exec resume --last`, model gpt-6-astra, sandbox workspace-write,
  cwd standby/, only writes roxy3d/): Blender scene, materials, renders, loops, vehicle/prop sprites.
  Briefs live in roxy3d/BRIEF*.md. Always check its renders yourself before using them.
- **Claude**: page integration (roxy.html), walk routes, behaviour, features, QA, reviewing Codex's
  output, writing Codex's next brief. Never let both edit the same file.
- **Codex as second opinion (owner's request, 01 Nov 23:20):** after every pass, run a separate
  read-only Codex session (`codex exec -i <shot> -m gpt-6-astra -s read-only --skip-git-repo-check
  -o roxy3d/reviews/review-N.md "<prompt>" < /dev/null` - the `< /dev/null` matters, or it waits on stdin)
  for (a) a design critique of fresh screenshots, (b) QA / bug hunting, (c) a code review of
  roxy.html (and shared/cinema.js when touched). Weigh its findings, fix the real ones, log what was
  taken or rejected and why in PROGRESS.md.

## Backlog (top = next)
1. Integrate Codex pass 1 (out/manifest.json): bg + occluder sprites (z-sorted chunks), 1x/2x by
   output scale; align DOM door signs + posters to the rendered boxes/frames; remove DOM copies of
   baked signs.
2. **Owner QA note:** box office and snack bar must be COUNTERS AGAINST A WALL with staff behind
   them, not islands in the middle of the lobby. Plan: box office along the lobby side of the u = 3
   partition, snack bar (popcorn, soda, menu boards on a back bar) along the lobby side of the v = 3
   partition; raise those partition stretches to ~90 px back-bar height (at 90 px they still don't hide
   corridor walkers - checked), staff walk between wall and counter; open lobby centre. Re-route the
   queue and snack spots in JS; Codex re-models it.
3. Codex pass 2 = BRIEF-2-loops.md (+ the layout change in 2, + grittier 90s materials).
4. Page: base.png + light_loop.webm (mix-blend-mode: plus-lighter) + fallback to the still.
5. Features to add (own ideas welcome): arrivals by bus / taxi / car on the street (pre-rendered
   vehicle sprites, chatters step out), umbrellas outside, splashes when hopping through puddles,
   usher tearing tickets, someone loitering at the arcade, occasional lobby staff gags, poster
   lightbox flicker, "SOLD OUT" moments when a room is busy, etc.
6. Every iteration: QA (screenshots at 1080p and 4K, walkers stand on the floor, occlusion right,
   labels/bubbles readable, no JS errors, green rect untouched, perf sane), log in PROGRESS.md.

## Keeping the owner posted (asked 01 Nov 23:25)
- `roxy3d/progress-shots.sh` runs in the background: a page screenshot every 5 min into
  `roxy3d/progress/` plus a copy of Codex's newest out2 render when it changes (no Claude usage).
- Owner (23:30): do NOT send images overnight (one was sent at 23:30). The progress/ folder is the
  timeline; summarise with a few key images only in the final report.

## Rules
- Small verifiable steps; keep roxy.html working at every step (live=1 auto-reloads).
- Never touch files outside standby/ ; never delete the owner's things; no pushes/publishing.
- Keep the old pages working (hall-*, cinema-*, shared/cinema.js API).
