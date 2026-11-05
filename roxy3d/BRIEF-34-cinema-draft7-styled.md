# Brief 34: SCENE 2 auditorium, DRAFT 7 - style the approved blockout

Owner approved the layout of blockout v2 (`qa11/cinema_draft_06_blockout.png`, `qa11/cinema_layout_06.json`,
`build_cinema_draft6_blockout.py`), including the zoom-out (ortho_scale 32). Now style it, taking from his
childhood-cinema photos (`roxy3d/ref/childhood-cinema/`, read in `reviews/review-cinema-d3-refs.md`) and from his
notes. His notes override the photos.

Strict draft rule: ONE image `qa11/cinema_draft_07.png` (1920x1080, house lights up, Cycles at the quality of
drafts 3/4), `qa11/CINEMA-DRAFT-07.md`, `qa11/cinema_layout_07.json`, STATUS, STOP. New files only
(`build_cinema_draft7.py`, `roxy_cinema_draft7.blend`, `qa11/runtime07/`). Only write inside roxy3d/.

## Layout: exactly blockout v2
Camera (60, 0, 45), ortho_scale 32, k = 0.707107, Ox = 890, Oy = 370; walls 500 on both retained sides; hall
u 0-17.5, v 0-14.9; the screen quad unchanged (u 4.924-13.876, zpx_world 90-460, same corners); row B front
(3/13/2), 2-tile cross-aisle with the divider, bank rows C-I (1.4 pitch, 16 rise), the left arrival area in
C-E, the two stair aisles, the EXIT passage on u = 0 and the route. Do not move seats, aisles or the screen; detail
may be added around them. If a styled object needs a footprint change, report it.

## Style (owner's notes first)
- **Much darker and more muted overall; the room is NOT lit up.** Low house light, warm pools from the wall
  lights, dark between them - but seated faces (emotes, drawn by the page) must still read against the seats and
  the route must stay readable. Think "lights at 30 % before the show".
- **Walls:** the photo's vertical pleated acoustic fabric, but deep and desaturated (teal around #1E3231, never the
  bright #315B58 of draft 4), dark plum-charcoal dado (~#1A161D), the stepped trim line following the rake in a
  muted dusty pink (~#7A5A5E). Tall narrow burgundy wall lights with soft ivory cores (dim), compact black surround
  speakers, a few small framed posters, all clear of the walking lanes.
- **Seats: PURPLE** - deep velvet purple (~#4B2A63 base, ~#6A3F8A on lit edges), like photos 04-06. Big, soft,
  rounded high backs, dark armrests with cupholders. No pink, no rose or amber blocks. A couple of worn/faded
  purple seats are fine as wear.
- **Stairs:** dark stair cheeks, muted coping (not cream - a dark dusty tone), simple tubular rails, red-orange
  step dots (~#D94B32) that clearly read as a rhythm of small lights on the risers (draft 4's were too faint), none
  directly behind where heads pass.
- **Carpet:** 90s pattern, dark navy (~#1E2030) with quiet wine / ochre / teal flecks - texture, not confetti.
- **Signage:** green **EXIT** (English) over the passage; the DINK DONK Screen 1 plaque on the side wall with one
  small cyan neon accent.
- **Front:** curtains, stage with a footlight lip, plain cloth-fronted speaker stacks (all outside the screen
  quad); the screen matte and unlit, no hot spots.
- **Ceiling strip:** charcoal tiles with a few small round downlights.
- **Cut section:** where the hall is cut away, show the raised bank's stepped profile and its dark structure
  instead of a tall flat grey block.
- **Wear:** 3-5 readable clusters (entrance carpet traffic, a spill by an aisle seat, a taped seat, a popcorn
  carton), as in draft 4, none bright behind seated heads.

## Checks and report
As drafts 4/6: calibration, screen visibility rays (zero blockers), per-row visible-face fraction incl. nearer-row
occlusion (50k x 74k emotes), screen clearance, row separation, route points, seat total, render time, and which
photo features you used. Note how dark the seating area is (mean luminance of the seat backs) so we can tune it.

One image, then STOP.
