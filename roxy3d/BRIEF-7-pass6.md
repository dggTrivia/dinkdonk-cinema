# Brief 7: pass 6 - the reviewer's art notes (signs, wear, doors, umbrellas, janitor, drip)

out5 is live (cat, brake lights and vehicle slices work). Same rules; **outputs to `roxy3d/out6/`**
(complete set, layout 2, keep every existing manifest key/contract, only add or update).

## A. Separate the screen 1 / screen 2 stacks
Their marquee boxes and posters overlap (screen 2 sits right above/behind screen 1 on the u = 0 wall).
Re-place the marquee boxes and poster frames of ALL five screens so each door has a clean, readable
stack with a visible gap: marquee above its own door, poster beside it, nothing overlapping another
screen's stack (you may move a marquee sideways along the wall, raise it, or shrink the poster a bit).
Keep the doors where they are. Publish the result in the manifest:
- `"marquees"`: [{ "screen", "bottom_center": [x, y], "inner_size": [w, h] }] (as now),
- `"poster_frames"`: [{ "screen", "wall": "u0" | "v0", "along": [a0, a1], "z_px": [z0, z1] }] where
  along is the v-range (wall u = 0) or u-range (wall v = 0) of the poster's inner area in tiles, and z_px
  its bottom/top height in page pixels (the page maps the poster image onto that plane).

## B. Material wear (Fallout 2 / Diablo 2 feel)
Scuffed, chipped edges on the counters' fronts and tops, worn door thresholds and kick plates, a few
cigarette burns / gum spots on the sidewalk, grime in corners, slightly dirty glass. Fewer immaculate
luminous edges: keep neon on signs, tone down glowing trim on furniture. Keep the carpet as in pass 4.

## C. Doors that open (one-shot sheets)
For each of the five screen doors and the restroom door: a short open-hold-close animation of the door
leaves (~0.9 s, ~16 frames) with warm light spilling out while open, as an RGBA sprite sheet positioned
over the closed door in the background: `"door_anims": [{ "door": 1..5 | "wc", "file", "file_2x",
"x", "y", "frame_width", "frame_height", "frames", "columns", "fps", "z_index" }]`
(z_index low: behind anyone standing in front of the wall).

## D. Umbrella sprites
Small shaded umbrella sprites (open, and a 6-frame fold one-shot), 4 colours (red, blue, yellow,
black), held above a ~50 px emote: anchor = the handle grip point. `"umbrella": { "colors": [...],
"open": { per colour file/file_2x/anchor/w/h }, "fold": { per colour sheet } }`.

## E. Janitor NPC
A pre-rendered janitor (cap, overalls, broom or mop + bucket), same camera, sprite sheets:
`walk` in the four floor directions (stride_tiles), `sweep` loop (2-3 s), `idle` loop (leaning on the
broom, checking a watch). Manifest `"janitor": { ...same format as "cat" }`.

## F. Shelter drip (prop loop)
A drip falling from one corner of the bus-shelter roof into a small puddle with a ring, seamless 2-3 s,
additive or RGBA, as a new entry in `"prop_loops"` with its rect and z_index.

Report as before (list every changed coordinate).
