# Brief 3: pass 2 - counters against the walls, grittier 90s look, pre-rendered loops

Great work on pass 1 (it is live in roxy.html now). Pass 2 = three things, same rules as BRIEF.md
(work only in roxy3d/, scripts re-runnable, same camera + calibration, don't touch the page/shared).
**Write all new outputs to `roxy3d/out2/`** (same file/manifest format as out/, plus the new keys
below) so the live page keeps using out/ until I have checked out2. Add `"layout": 2` to the manifest.

## A. Owner QA: the counters must be against walls (layout 2)

The streamer: "the ticket booth and the place with the soda and popcorn are islands in the middle of
the lobby - in reality they are counters against the wall: you have the entrance, the lobby, a counter,
and behind it the people who serve the customers." New lobby plan (tiles; lobby is u 3..13, v 3..9):

- **Both partitions become 90 px high back walls** on the lobby side (they were 34 px): along u = 3 for
  v 4.4..9 and along v = 3 for u 4.4..13 (same 0.2 thickness, centred on 3). At 90 px they still do not
  hide walkers in the corridors behind them (checked). Give their lobby faces proper finish: wainscot,
  neon strip, the back-bar dressing below.
- **Box office** against the u = 3 wall: counter u 3.8..4.4, v 5.0..8.4, 44 px, glass cashier screen on
  top to ~84 px with two ticket windows (at v = 7.4 and v = 6.0, speaking holes / tray slots).
  Staff area behind it u 3.1..3.8 (cashiers stand at (3.45, 7.4) and (3.45, 6.0)). On the wall behind
  them: a backlit "TICKETS" sign / showtime light board (static, baked), ticket printer, cash register.
  Customers stand at u = 4.85 and queue along +u from (4.85, 7.4).
- **Snack bar** against the v = 3 wall: counter u 5.6..11.6, v 4.0..4.6, 44 px, with a glass candy display
  in its front face. Back bar against the wall v 3.1..3.45: two popcorn machines (glowing), soda
  fountain, hot-dog roller, nacho warmer, cups stacked; backlit menu boards mounted on the wall's upper
  part (keep them within the 90 px wall height so they never cover the corridor). Clerks stand at
  (6.6, 3.75), (8.2, 3.75), (9.8, 3.75). Customers at v = 5.05, u = 6.6 / 8.2 / 9.8.
- **Usher podium** u 4.55..5.0, v 3.55..4.0; usher stands at (5.3, 3.8). Gate stays at the lobby's back
  corner (u, v 3..4.4) with the hanging "◀ 1-2 · 3-5 ▶" sign.
- Lobby furniture moves out of the way: arcade stays (u 12.0..12.7, v 7.5..8.2); bench to u 11.2..12.6,
  v 6.0..6.4; standee_1 stays (u 12.2..12.62, v 5.0); standee_2 to u 7.2..7.62, v 8.5..8.56; add a big
  potted palm at u 12.3..12.8, v 3.4..3.9 and maybe a round carpet medallion in the lobby centre.
- Remove the old islands (old box office at u 4..7, v 7..7.8 and old snack island at u 8.2..11.8,
  v 4.6..6.0) and the old bench position.
- Occluder sprites (+ depth slices, same scheme) for: both 90 px walls, box office (counter + glass),
  snack bar counter (the back bar is BEHIND the clerks, so it belongs in the background unless it is
  taller than them), podium, bench, arcade, standees, palm, front low wall, glass, posts, bus stop, lamp,
  ROXY blade.

## B. Grittier late-90s pre-rendered look

Less clean modern low-poly, more Fallout 2 / Diablo 2 / Sims 1 pre-render: worn and patterned
carpet with traffic paths, scuffs on skirting, water stains and posters' sun-faded edges, dirty wet
asphalt with oil sheen and cracks, chewing-gum dots on the sidewalk, grimy glass, subtle film grain.
Keep it cozy and readable (emotes ~50 px must pop on the floor).

## C. Pre-rendered ambient loops (do BRIEF-2-loops.md, adapted)

Exactly as in BRIEF-2-loops.md, but in out2/: `base.png` (+@2x) with animated lights at minimum,
`light_loop.webm` (1920x1080 VP9, additive "animated minus base", seamless, 24 fps, 4-6 s, < 15 MB),
occluder sprites matching base. Manifest keys: `"base"`, `"light_loop"`, `"loop_seconds"`, `"fps"`.
The page will put the loop with mix-blend-mode: plus-lighter over base, under posters/chatters.
Also keep `full.png` (one fully lit frame) for checking.

Order: do A + B with stills first and write the manifest (so I can integrate early), then C.
Report like before; also list in the manifest any coordinate that differs from this brief.
