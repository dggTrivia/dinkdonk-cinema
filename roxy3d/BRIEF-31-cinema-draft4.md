# Brief 31: SCENE 2 auditorium, DRAFT 4 - the owner's childhood cinema

Owner on draft 3: keep going from it, and take inspiration from photos of the cinema he grew up with - a Showcase
Cinemas multiplex in a mall, Spanish signage. Photos: `roxy3d/ref/childhood-cinema/` (02-05 are auditoriums,
01 the entrance neon, 06 the snack bar, 07 the mall). "Not everything, but take inspiration." The read-only second
opinion `reviews/review-cinema-d3-refs.md` reads the photos; its points are folded in below. Look at the photos
yourself before building.

Same strict draft rule: exactly ONE image `qa11/cinema_draft_04.png` (1920x1080, house lights up),
`qa11/CINEMA-DRAFT-04.md`, `qa11/cinema_layout_04.json`, STATUS line, STOP. New files only
(`build_cinema_draft4.py`, `roxy_cinema_draft4.blend`, `qa11/runtime04/`). Only write inside roxy3d/.

## Keep from draft 3
Whole-hall framing with dark margins, camera (60, 0, 45), ortho_scale 30 (k = 0.754247), the screen on v = 0 at
about the same size with every screen rule (clean 16:9 quad, nothing over it, matte, unlit; also remove draft 3's
small light hot spot at the screen's top edge), one joined seat-back object per row, switchable light
collections, the face-readability and screen-clearance checks, the stuck half-folded seat, wear clusters.

## Take from the photos
1. **Layout (photos 02, 03):** two or three low front rows on a flat (or gently raked) section, then the main
   stadium bank rising behind it, separated by a low stepped divider wall with a pale cap and a rail. The
   entrance becomes a passage at floor level at the bottom of the stadium, along the u = 0 side: chatters come
   out of the passage onto a lit landing, then climb the side stairs to their row. Keep the route
   door/passage -> landing -> stairs -> row fully visible. The steeper bank also fixes draft 3's "rows read as one
   flat red field" - each tier should read as its own step (shadow line / riser).
2. **Seats (photos 03-05):** big, soft, rounded high-back seats with thick upholstery and dark armrests with
   cupholders; dusty purple/mauve (~#936783) as the main colour, a few faded rose seats (~#B98387); optionally one
   small block in amber (~#B78149) like photo 04. The camera sees the rounded rear shells - make that silhouette
   read.
3. **Walls (photo 02):** closely spaced vertical pleated / ribbed acoustic fabric in muted teal (~#315B58) above a
   dark plum-charcoal dado (~#28232C), with a thin dusty-pink trim line (~#B78689) that steps up the side wall
   following the rake. This replaces draft 3's purple/green panel grid.
4. **Wall lights (photo 02):** 3-4 tall, narrow vertical deco fixtures in burgundy housings with warm ivory cores
   (~#F4DDB0) washing soft pools up the pleats. Not blown out.
5. **Wall speakers (photo 02):** a row of compact, angled black surround speakers high on the walls between the
   lights. The screen-flanking stacks become plain dark cloth-fronted multiplex speakers (no big exposed woofer
   rings).
6. **Stairs (photos 03-05):** dark stair cheek walls with cream-pink coping (~#C8B3A2) and a simple tubular rail
   (keep camera-facing parts low so walkers stay visible); small red-orange step lights (~#D94B32) as a rhythm of
   dots at the riser ends and along the passage base - dots, not continuous strips, none right behind heads.
7. **Carpet (photos 05, 06):** 90s patterned carpet on stairs, landings and aisles - charcoal navy (~#272936)
   with wine, ochre and muted teal flecks / broken rectangles, readable as texture, not confetti. Optionally a dark
   glossy floor in the flat front section (photo 02), subtle reflections only.
8. **Signage:** EXIT becomes **SALIDA** in luminous green (~#76CB55) on a dark plaque over the passage mouth (and
   over a second exit if you add one). The DINK DONK Screen 1 plaque stays, separate, with one small cyan neon
   accent (~#38C4DA) borrowed from the foyer photos (01, 06) - one cool accent only, no double neon bands in here.
9. **Ceiling (photos 04, 06):** charcoal (~#191C22) acoustic tiles in the shallow ceiling strip with a few small
   round recessed downlights and the odd square vent.
10. **A few small framed posters / pictures** on the side wall (photo 02), clear of the walking lane.

## Do NOT copy
Crushed-dark aisles, blown-out sconces, big white stair caps or tall dividers right behind or in front of walking
heads, glossy reflections or glow on/over the screen, the foyer's full-strength neon everywhere.

## Report
Same as draft 3 (Ox/Oy, k, calibration, screen corners 1080p/4K + wall coords, footprint, per-row seat line v,
tier zpx_world and seat u (JSON, flat rows included), passage/landing/stairs path points, screen clearance, per-row
visible-face fraction incl. nearer-row occlusion), which photo features you used and render time.

One image, then STOP.
