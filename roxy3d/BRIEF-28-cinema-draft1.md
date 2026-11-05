# Brief 28: SCENE 2 - the auditorium (DINK DONK Screen 1), DRAFT 1

A new, second scene for the same stream. Scene 1 is the lobby (`standby/roxy.html`, approved draft 13 look).
When a film has been picked on dinkdonk.mov and is downloading, the stream cuts to this scene: the inside of
the auditorium. Chatters (emotes, DOM layer, same as the lobby) walk in, take seats, talk; then the house lights
dim and the film plays on the big screen.

Strict draft rule: exactly ONE image -> `qa11/cinema_draft_01.png`, 1920x1080, final-ish quality (adaptive
samples + denoise are fine; no loops, no sprites, no layers, no weather). A short `qa11/CINEMA-DRAFT-01.md`, one
STATUS line, then STOP. The owner reviews the draft before anything more is rendered.

Work in NEW files only: `build_cinema_draft1.py` (scripted, re-runnable, Blender 5.2.3 headless as before),
`roxy_cinema.blend`, `qa11/`. Do not modify roxy_pass10*.blend, the cloud bundle, out10, or any page.
Only write inside roxy3d/.

## 1. Same look as the lobby (non-negotiable)
- Same camera type and scale: orthographic, rotation (60, 0, 45) deg, ortho_scale 22.627416998,
  1 tile = 1 BU projects to (60, 30) px, 1 BU of height = 73.4846922835 px, world (x, y, z) = (u, -v, zpx/73.48).
  You MAY move the camera (the origin pixel), i.e. this scene's projection is
  `P(u, v, zpx) = [Ox + (u - v) * 60, Oy + (u + v) * 30 - zpx]` with Ox, Oy of your choice - report them.
  Run the calibration check like calibrate.py (markers at 5 known points, +-1 px) and report the errors.
- Same art style: late-90s pre-rendered (Diablo 2 / Fallout / The Sims 1), dollhouse cutaway, soft GI.
  Reuse the lobby's materials and palette from the draft-13 scene (90s cinema carpet, purple/teal, warm
  incandescent light, red velvet, brass) so both scenes clearly belong to the same building.
- Emote scale matters: the page's walkers are the same size as in the lobby, so seats, steps and doors must be
  sized for them like the lobby's counters and doors.

## 2. The room
- Two walls kept, front/right cut away like the lobby (show the slab and the stepped cross-section of the
  seating tiers at the cut, Sims-style):
  - **Screen wall = the v = 0 wall** (back-right). The screen hangs on this wall plane, so it appears as a
    parallelogram (vertical sides, top and bottom sloping down to the right) - correct isometric, NOT
    camera-facing.
  - **Side wall = the u = 0 wall** (back-left), with the entrance.
- **The screen:** 16:9, flat, plain matte white/light-grey projection surface, unlit except house light, no
  logo/text/pattern on it. Make it as LARGE as the frame allows while the whole room still reads: target an
  on-frame bounding box of at least ~520 px wide. Black masking border around it, red velvet curtains drawn open
  at its sides, a low stage/apron below it.
  HARD RULE: nothing in the render overlaps the screen's 16:9 rectangle (curtains, sconces, rails, glare,
  fog all stay outside it). The page draws an exact green quad on top of it for OBS (chroma key + corner-pin
  shader puts the pre-show and the film there), so the screen must be a clean four-corner parallelogram.
  Also keep the seated audience below it: with the stage height and the tier rise you choose, a ~60 px tall
  emote seated in ANY row must not reach the screen's bottom edge in screen pixels - check this numerically.
- **Seating:** stadium rows parallel to the screen wall (constant v), facing the screen, each row a step higher
  than the one in front (rising toward the camera). Classic red velvet flip seats with armrests and cupholders.
  The camera sees the audience from behind and above: a row's own seat backs hide the lower body of the emote
  sitting in it, so only head and shoulders show above the backrest (the page will later need each row's seat
  backs as a separate occluder layer - not in this draft, but model each row as its own object). Aim for roughly 5-7 rows of 10-14 seats (40-80 seats), one side aisle along the u = 0 wall
  with lit step edges (small amber aisle lights) and a handrail, and a cross-aisle at the front by the stage.
- **Entrance:** a padded double door (like the lobby's screen doors) in the u = 0 wall at floor level near the
  stage end, with a lit EXIT sign above it; chatters come in here and climb the side aisle. Optionally a
  second EXIT sign/door further up the same wall.
- **Walls:** acoustic fabric panels / quilted padding, warm wall sconces (glowing, house lights UP for this
  draft), a small DINK DONK logo plaque or neon on the side wall (not on or over the screen).
- Lighting for this draft: house lights up (the seating phase), cozy and warm, screen not glowing. A dimmed
  state will be a later render, so keep the house lights as separate, switchable light groups.

## 3. Report in CINEMA-DRAFT-01.md (numbers matter, the page is built from them)
- Ox, Oy and the calibration errors.
- The screen's four inner corner pixels at 1920x1080 and at 3840x2160 (TL, TR, BR, BL), and its wall
  coordinates (u range, zpx range).
- Room footprint (u, v ranges), every row: v of the seat line, floor zpx of the tier, seat u positions
  (centre of each seat) - as a small table or JSON next to the md (`qa11/cinema_layout_01.json`).
- Entrance door position (u = 0, v range, height) and the aisle path points.
- The numeric check that no seated emote reaches the screen's bottom edge.
- Render time and anything you had to compromise on.

One image, then STOP.
