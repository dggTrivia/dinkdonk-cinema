# Brief 30: SCENE 2 auditorium, DRAFT 3 - the big hall, seen whole (zoomed out)

Owner on draft 2: he wanted a BIGGER cinema, but seen MORE ZOOMED OUT - the whole hall visible in the frame like
draft 1, not the room taking more of the screen. This replaces BRIEF-29's "fill the frame" rule. A read-only
second opinion (`reviews/review-cinema-d2.md`) agrees; its points 1-9 are folded in below (point 10, a test with
emotes, is not part of this draft - the page side does that later).

Same strict draft rule: exactly ONE image `qa11/cinema_draft_03.png` (1920x1080, house lights up),
`qa11/CINEMA-DRAFT-03.md`, `qa11/cinema_layout_03.json`, one STATUS line, STOP. New files only
(`build_cinema_draft3.py`, `roxy_cinema_draft3.blend`, `qa11/runtime03/`). Only write inside roxy3d/.

## Changes vs draft 2
1. **Whole hall in frame.** Every row with both seat ends, the full entrance -> aisle -> back-row route, both
   speaker stacks, the stepped slab/cut section and the ceiling strip are visible, with about 40-70 px of dark
   breathing room around the silhouette (Sims-style cutaway like draft 1). Camera angle stays (60, 0, 45).
2. **Zoom the camera out (this relaxes the locked scale).** Increase ortho_scale so the hall fits - but cap it at
   **about 30** (0.75x of the lobby's 22.627; the page will draw emotes ~38 px tall instead of 50). Pick the room
   size so the whole hall fits at or below that cap, rather than zooming out further. Report the final
   ortho_scale and the resulting px per tile (u, v) and px per BU of height, and express the projection as
   `P(u, v, zpx_world) = [Ox + (u - v) * 60k, Oy + (u + v) * 30k - zpx_world * k]` with k = 22.627/ortho_scale
   (zpx_world = heights in the lobby's pixel units, so the scene keeps its own units).
3. **Room proportions.** Lower the walls to about 650-700 zpx_world (draft 2: 945 = eight door heights). Grandeur
   comes from breadth, curtains and proscenium; the ceiling is a shallow visible strip with the truss/clouds.
   Capacity target about 8-9 rows x 16-18 seats (roughly twice draft 1); fewer if that is what fits the cap.
4. **Screen** shrinks with the overview (16:9, on v = 0, as large as the room allows; all screen rules from
   BRIEF-28 unchanged). Reduce the heavy diagonal ceiling shadow across the blank screen surface.
5. **Seated faces readable.** With emotes at 50k px tall, about 55-70 % of the emote must show above its own
   backrest; adjust cushion anchor and backrest height together. Check rows against each other too: the nearer,
   higher row must not swallow a face in the row in front of it. Report the visible-face fraction per row.
6. **Arrival route legible.** EXIT doorway, the first turn and every aisle landing visible; the brass rail crosses
   walkers below face height; no bright step lamps directly behind where heads pass; a little clear space
   between wall, walking lane and the first seat column.
7. **Light hierarchy like the lobby (draft 13):** selective warm pools, cool accents, readable mid shadows.
   Lift the seating and aisle by about 1/2-1 stop locally, keep ceiling recesses dark, subdue the broad purple
   wall wash so the sconces and brass highlights carry the mood.
8. **Wear that reads at overview scale:** replace tiny scattered litter with 3-5 recognisable clusters (an
   entrance traffic track, a spill beside an aisle seat, one conspicuous taped repair, a faded upholstery patch,
   a discarded popcorn carton), some marks 12-30 px in the 1080p frame, none bright right behind seated heads.
   The worn carpet paths must look like wear, not painted stripes (draft 2's cross-aisle reads as yellow bands).

## Keep from draft 2
Picture-palace detailing (cornice, fluted pillars, speaker stacks, footlight stage lip, curtains, plaque, EXIT,
padded door), switchable light collections, one joined seat-back object per row, the stuck half-folded seat,
procedural detail that holds up at 4K and 1.85x zoom.

## Report
Same as draft 2 (Ox/Oy, ortho_scale, k, calibration errors, screen corners at 1080p and 4K, wall coordinates,
footprint, per-row seat line v / tier zpx_world / seat u in JSON, door + aisle path, audience clearance against
the screen using 50k x 74k px emotes) plus the per-row visible-face fraction and render time.

One image, then STOP.
