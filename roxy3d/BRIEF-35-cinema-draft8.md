# Brief 35: SCENE 2 auditorium, DRAFT 8 - entrance tunnel, blue walls, lift the darks

Owner on draft 7 (`qa11/cinema_draft_07.png`): better; agrees with my fixes (lift the darks, step lights where the
camera sees them, edge light on the cut section) and adds the tunnel, blue walls, more litter and fewer handrails.
Read-only second opinion: `reviews/review-cinema-d7.md` - points 1-9 are folded in below (point 10, an emote test,
is not part of this draft).

Strict draft rule: ONE image `qa11/cinema_draft_08.png` (1920x1080, house lights up, Cycles as draft 7),
`qa11/CINEMA-DRAFT-08.md`, `qa11/cinema_layout_08.json`, STATUS, STOP. New files only (`build_cinema_draft8.py`,
`roxy_cinema_draft8.blend`, `qa11/runtime08/`). Only write inside roxy3d/.

## Keep
Everything in draft 7 / blockout v2 not changed below: camera (ortho 32, Ox 890, Oy 370), walls 500, screen quad
and all screen rules, seat positions B-I, cross-aisle and divider, both stair aisles, purple seats, pleated walls
with the stepped trim, wall lights, plaque, curtains, stage, speakers.

## Changes
1. **Entrance tunnel (owner).** The empty middle-left area (rows C-E, u 0-2.95, v 5.2-9.4) is where a tunnel
   (vomitory) comes into the hall. The cinema's real entrance/exit is at the BACK of the hall (high v, the cut-away
   side nearest the camera). The tunnel runs from there toward the screen along the u = 0 side, under the left
   seat block F-I, and opens into the hall where the left seats end (~v 9.4). Chatters come in through it.
   - The camera sees +u, +v and +z faces only, so the mouth facing the screen is hidden. Make it read anyway: show
     the camera-facing rear portal in the cut section at v = 14.9 (jamb, slab thickness, dark interior, a little
     warm light), and a small sectional notch on the tunnel's +u cheek / roof apron at the mouth (outside row F's
     seat footprints) so the opening and the walkers coming out are visible. Check the real sightline.
   - Levels: the deck underside under F is ~99-105 zpx_world, too low over a floor at 24 for a walker (envelope
     reaches floor+86). Start from a tunnel floor at 0 and rise to the cross-aisle's 24 in the open C-E approach
     (e.g. three 8-unit steps with landings); remove the unused left C-E tier decks from that approach; open the
     divider where the approach meets the cross-aisle. Keep the main stairs unchanged.
   - Put a green EXIT sign at the tunnel (visible from the camera).
   - The page will hide walkers inside the tunnel with a foreground occluder: model the tunnel roof, lip and
     camera-side cheek as their own object(s) (named, for a later occluder export).
   - New route: rear portal (v ~14.9, floor 0) -> through the tunnel -> mouth (~v 9.4) -> approach steps -> cross-aisle
     / foot of the left stairs -> up -> rows; and the branches to row B and the right aisle. Points in the JSON.
2. **The door near the screen wall is an emergency exit only** (keep it, keep its EXIT sign; it is no longer on
   the arrival route).
3. **Walls dark BLUE instead of green:** desaturated navy around #1C2B46 for the pleats (keep them quiet), same
   dark dado and muted stepped trim, warm sconce pools.
4. **Lift the darks, keep it moody (owner agreed).** Delivered-image targets (same metric as draft 7): seat-back
   mean about 32-40/255 (draft 7: 18), rear rows H/I at least 24-28, broad shadows ~10-16, deep black only in
   cavities. Lift the seating locally (broad fill), not a global exposure bump that also brightens the screen and
   sconces. The screen stays matte grey, no hot spots.
5. **Step lights the camera can see:** small tread-top inserts near the nosing edges (+z faces) plus low lights on
   the +u-facing stair cheeks; risers face away from the camera so they cannot carry the rhythm. About 3-4 px dots
   or 5-8 px short bars at 1080p, restrained glow, outside walkers' face silhouettes.
6. **Cut section readable:** fascias ~12-20/255 with selected upper edges ~25-35 so the stepped construction reads.
7. **Handrails only where they make sense (owner):** one continuous rail per stair run and the guard along the drop
   between the stairs and the lower tunnel approach (like photo 03). Remove rails beside level platforms, along the
   cross-aisle and any rail crossing the arrival route; no floating stubs - rail ends return into a support.
8. **More litter (owner):** about 8-12 small popcorn groups, 4-6 cups, 2-3 cartons, mostly beside seat ends and
   under seats, a little at the tunnel landing; 2-3 px kernels, 6-12 px cups/cartons at 1080p. Stair centres and the
   route stay clear.

## Report
As draft 7, plus: tunnel geometry (floor, clear height, portal and notch positions), the new route points and
walker visibility along it (hidden inside the tunnel is expected; report where it is visible), the names of the
tunnel occluder objects, the rails kept, seat-back luminance per row, cut-section luminance, render time.

One image, then STOP.
