# Brief 6: pass 5 - long-vehicle depth, brake lights, a lobby cat

out4 is live (calmer carpet + prop loops look great). Same rules; **outputs to `roxy3d/out5/`** (complete
set, layout 2, keep every existing manifest key/contract, only add).

## A. Depth slices for long vehicles (reviewer P2)
The page sorts each vehicle by its centre depth, so a person on the curb beside the long bus is drawn
wrong at one end. Give every vehicle sprite (both directions, closed + door-open) depth slices like the
static occluders: cut along its length into pieces no longer than ~1 tile, each with its own pixel rect
(relative to the sprite's top-left), its own anchor ground point offset along the lane (in tiles,
relative to the vehicle centre) so the page can compute its z as 1000 + round((u + du + v) * 100).
Light sprites stay whole. Manifest: add `"slices": [ { "file", "file_2x", "x", "y", "w", "h", "du" } ]`
inside each vehicle direction (and inside door_open).

## B. Brake / indicator light variants
Per vehicle and direction an extra additive light sprite with brake lights on (brighter red tail glow and
its wet-road reflection), same anchor/size as the normal light sprite: `"light_brake"`, `"light_brake_2x"`.
Bus and taxi also an amber indicator-on variant for when they pull in (`"light_indicator"`), optional.

## C. A lobby cat (the streamer liked a sleeping-cat easter egg in an earlier draft)
A small black (or ginger) cat, same camera/lighting, RGBA sprite sheets, anchor = ground point under the
cat's body centre, size about 0.45 tiles long:
- `sleep` loop (curled up, breathing, maybe an ear twitch), 2-4 s,
- `sit` loop (sitting, tail swishing, occasional lick), 2-4 s,
- `walk` cycles for the four floor directions (+u, -u, +v, -v), 8-12 frames each, with the distance per
  cycle in tiles so the page can match the stride,
- optional `stretch` one-shot.
Manifest: `"cat": { "<anim>": { "file", "file_2x", "frames", "columns", "fps", "frame_width",
"frame_height", "anchor": [x, y], "stride_tiles"? } }`.

## D. Tyre spray (optional)
A small additive sprite sheet of water spray kicked up behind a wheel on the wet road (one per
direction), ~0.5 s one-shot, anchor at the wheel's ground contact: `"tyre_spray": { "+u": {...}, "-u": {...} }`.

Report as before.
