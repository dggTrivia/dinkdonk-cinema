# Brief 48: the small white "floating" rectangle at the curb by the bus stop (live pack out10)

The owner keeps seeing a small white tilted rectangle that seems to float: on the sidewalk/curb edge left of the bus
stop when no car is there, and on top of cars passing in the near lane (it looked like it was "over the car").
It is baked in the render: out10/full.png at about (110, 605) in 1080p coords (world roughly u -2.3, v 10.8, next to
a dark puddle at the curb; visible in Claude's crops of full.png and of the live page). The bus_stop occluder's
footprint reaches v 11.33 and its slices (occ_bus_stop_*) are drawn above near-lane vehicles (z ~1950 vs ~1870), so
anything in those slices that lies on the road/curb shows on top of passing cars.

## Do
1. Identify the object in the scene (name, material, position, which group/slice/plates it lands in) with evidence.
   Say whether it is intended (e.g. a road marking / sign) or a stray / helper object (e.g. a reflection catcher).
2. Fix it in a new pack folder roxy3d/out10c/ (copy of live out10, only touched files replaced):
   - if stray: remove it from every image it appears in (static plates 1x+@2x, any bus_stop slice / wet sheet, and
     the light loops only if it is in them) by a clean local inpaint from the surrounding render;
   - if intended and on the ground: it must sit UNDER vehicles and walkers - move its pixels out of the occluder
     slices into the ground plates; if it is something that stands up, say what is right for depth.
   - keep every other pixel identical, the slice reconstruction exact, the loop's nonnegative-delta contract, and
     refresh checksums.json / validation.json.
3. Scan the bus_stop (and nearby curb) slices for any other pixels that lie on the road/curb (v > 10.6) and would
   wrongly cover passing vehicles; fix the same way and list them.
4. Fix the scene source for the next real render (roxy3d/ sources only, no render).

## Deliver
NOTES-48.md (what it is, what you changed, numbers, validation, before/after crop paths for Claude), STATUS line,
stop. No owner images. Do NOT modify roxy3d/out10/ or standby/roxy.html. Local only, no cloud.
