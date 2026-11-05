# Brief 37: SCENE 2 auditorium, DRAFT 10 - entrance door, closed underside, page layers

The auditorium page now runs: `standby/auditorium.html` reads `qa11/cinema_draft_NN.png` + `qa11/cinema_layout_NN.json`
(?draft=NN). Chatters spawn just outside the rear portal, walk the tunnel route (`walk_route.rear_portal_to_cross_aisle`),
climb the stairs and sit. Owner reviewed it live; changes:

1. **Rear entrance (bottom-left):** remove the green EXIT sign over the rear portal (keep the small EXIT on the guard
   post at the tunnel mouth and the emergency EXIT by the screen). Put a door in the portal: the SAME padded double
   door with portholes as the lobby's screen doors (pass 9 / draft 13 lobby, `out9/doors/`), scaled to the portal.
   Closed in the still. It opens for every chatter who comes in (see layers below).
2. **Close the underside:** the cut-away of the raised floor (bottom-left / bottom, where the piers, joists and the
   dark void under the tiers show) gets a solid wall on the cut faces, like the lobby's cut walls - dark, plain,
   with the stepped top edge still readable (keep the edge light). The tunnel portal (with its door) is an opening
   in that wall. Nothing of the under-deck structure visible any more.
3. **Walkers show too early at the tunnel mouth** (they appear through the structure before they clear it). The page
   needs real occlusion layers instead of its own hide/clip guesses - see below.

4. **Emergency exit (owner, added):** the door on the u = 0 wall near the screen end (today's passage at v ~3.7-4.6
   with a green EXIT) becomes a real emergency exit: move it closer to the screen on the SAME wall (e.g. v ~1.2-2.1,
   clear of row B's left block and the cross-aisle route), a plain closed fire door (push bar, closed by default,
   no dark open passage), with a RED illuminated "EXIT" sign above it (red lettering, typical emergency exit box).
   Nobody uses it in the page.
5. **Front row = wheelchair row (owner, added, an inside joke):** row B (the single front row) is "reserved": put the
   blue wheelchair symbol (the accessibility sign: white wheelchair pictogram on a blue square, like the emoji) on
   the BACK of every row-B seat (the camera sees the rear of the seat backs) - readable at 1080p, a clean little
   decal/plaque on each back - and optionally a painted blue wheelchair marking on the floor of row B's legroom
   if it stays readable and not noisy. Only row B.

Everything else stays exactly as draft 9 (`build_cinema_draft9.py`, `qa11/cinema_layout_09.json`).

## Output
Owner review: ONE still `qa11/cinema_draft_10.png` (1920x1080, Cycles as draft 9, door closed). Plus the page layers
below (not for review, for the page) in `qa11/draft10/`, and `qa11/cinema_layout_10.json` = draft 9's layout JSON
(same keys, the page reads them) plus a `page_layers` object. New files only (`build_cinema_draft10.py`,
`roxy_cinema_draft10.blend`, `qa11/runtime10/`). Only write inside roxy3d/. No 4K yet.

## Page layers (`page_layers` in the layout JSON)
- **Depth key.** The page sorts walkers with `key(u, v, zpx_world) = (u + v) + zpx_world / 90` (camera-depth order
  for this camera: bigger = nearer the camera; 1/90 = sin30 / (cos30/sqrt2) / 73.4847 per zpx_world unit - check
  it against the camera and report the exact constant if it differs) and `z_index = 1000 + round(key * 100)`.
  A walker's key uses its foot point; a seated chatter's foot point is `(seat_u, row_v + 0.2, floor + 36)`.
- **Depth slices** (`page_layers.slices`): cut from the delivered beauty, with exact anti-aliased alpha, every pixel
  whose first camera hit can occlude a walker or a seated chatter (seats, seat backs, armrests, rails, stair cheeks /
  coping / risers, divider, tunnel roof / lip / cheek / portal jambs, the new cut wall and door, anything else near the
  routes). Group pixels into slices by their surface depth key in bands of about 0.1-0.25, merged per object/row
  where it does not change the order, cropped tight; target well under 200 files. Each entry:
  `{ "file": "draft10/slices/...png", "x", "y", "w", "h", "z_index", "key_min", "key_max", "name" }` with z_index from
  the formula above using the band's key_min. Floors / carpets / walls that never overlap a walker standing or
  sitting on the walkable areas can stay out. The bg still stays the full beauty (slices are exact copies on top).
- **Door animation** (`page_layers.entrance_door`): same format as the lobby's `door_anims` entries:
  `{ "x", "y", "frame_width", "frame_height", "frames": 16, "columns": 4, "rows": 4, "fps": 18, "loop": false,
  "z_index", "file": "draft10/door_entrance.png", "open_hold_frames": [a, b] }` - opening, a short hold open, closing,
  first and last frame identical to the closed still. Say which z_index it needs relative to a walker standing just
  outside (at the route's first points, v ~15.12 -> 14.9) and passing through.
- **Spawn:** confirm the route's first point is outside the closed door and say where the walker should wait while the
  door opens (the page starts the door when the walker spawns).

## Checks / report
The still matches draft 9 apart from the three changes; screen untouched (same corners, zero light change); calibration
unchanged. For the slices: composite bg + all slices = bg exactly (report max abs difference); for a few sample walker
positions along the tunnel route, the mouth, the stairs at row C and a seated chatter in each row, report which slices
draw above/below them and the resulting visible fraction vs your ray-cast visibility (they should agree). Render time.

One review still + the layers, then STOP.
