# Brief 4: vehicles and arrivals (pass 3)

Pass 2 is live in roxy.html (out2/). Pass 3 adds traffic so chatters can arrive by bus or taxi (the
streamer asked for it). Same rules as before; **outputs to `roxy3d/out3/`** (copy over whatever of out2
you don't change so out3 is complete on its own; manifest `"layout": 2`, plus a new `"vehicles"` key).

## Street geometry (same projection P(u, v, zpx) as BRIEF.md)
The street runs along u. Lanes: near lane centre v = 11.0 (traffic going +u, i.e. screen down-right),
far lane centre v = 12.0 (traffic going -u, screen up-left). Curb at v = 10.55. Bus stop shelter at
u 0.4..2.0 (bus stops with its door at about u = 1.2, v = 10.75). Cinema entrance is at u = 9.5
(taxis pull up there, near lane).

## Deliverables
1. Vehicle sprites, RGBA, rendered with the same camera and lighting/rain mood (wet bodywork,
   lit interiors, reflections baked into the body), each in BOTH directions (+u and -u):
   - `bus` - early-90s city bus (long, boxy, lit windows, destination sign "95 ROXY"), ~2.6 tiles long.
   - `taxi` - yellow 90s sedan cab with TAXI roof light.
   - `sedan_a`, `sedan_b` - two boxy early-90s cars (different colours), one with pop-up headlights.
   For each sprite: the image, its pixel anchor = the point that sits on the lane centre at the
   vehicle's middle (so the page can place it with P(u, v)), and its footprint length in tiles.
   1x and @2x.
2. Matching additive light sprites per vehicle and direction (`*_light.png`): headlight beams on the wet
   road ahead, tail-light glow and their streaky reflections on the wet asphalt, on black, for
   `mix-blend-mode: plus-lighter` under the vehicle sprite. Same anchor convention.
3. Optional: a door-open variant of the bus (or a separate door sprite) and taxi rear door open.
4. Optional: `lit_bg.png` (+@2x) = the fully lit scene WITHOUT the occluder props (fallback for the
   page if the light loop video cannot play).
5. Manifest `"vehicles": { "bus": { "+u": { "file", "light", "anchor": [x, y], "length_tiles" }, "-u": {...} }, ... }`
   plus `"lanes": { "near": 11.0, "far": 12.0 }`.
6. A check image `qa3/vehicles_check.png`: out2 base + loop frame + each vehicle placed at a few points
   along its lane, to prove the anchors line up with the lanes.

Keep sprites tight (cropped) and file sizes sane. Report as before.
