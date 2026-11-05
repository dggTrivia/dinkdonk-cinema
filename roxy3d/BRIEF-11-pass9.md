# Brief 11: pass 9 - everything inside the world (outputs to roxy3d/out9/, complete pack from out8b)

The owner reviewed out8b. His main idea now: **everything belongs inside the world** - no floating,
screen-facing overlays. The page will drop its HUD (logo/intermission/schedule), the green-screen
billboard, and the screen-facing title signs. Same rules as before (camera, layout-2 floor plan, walker
routes, occlusion envelopes, depth-slice and sprite contracts, seamless loops, protected older packs).
Write NOTES-PASS9.md, qa9/, STATUS lines in qa9/STATUS.md. Only write inside roxy3d/.

## 1. Front windows: full height again (owner: "one thing I really liked was seeing the outside windows")
The street-facing glass (glass_left u 3..8.4 and glass_right u 10.6..13 at v ~9, plus the entrance) is cropped
to a low ~30 px rail - it reads like a fence. Make it a real full-height 90s storefront: mullions, transom,
door frames, a header band, glass with believable tint/reflection so walkers inside stay clearly visible.
A few (not many) window posters/decals: e.g. one small one-sheet, opening hours, "NO SMOKING", a sticker.
Deliver as occluders with depth slices (they cover walkers inside, not outside), keep the rain water on the
glass (re-fit the water loops to the taller panes). Keep the walker entrance opening clear.

## 2. Remove every screen-facing sign; replace with in-world ones (correct wall perspective)
- **Marquee title boxes above the corridors: remove** (the five big pink-framed boxes). They are replaced by:
- **LED dot-matrix signs above each of the five screen doors** (classic 90s: two rows, row 1 = film title,
  row 2 = score). Model the physical housing on the wall above each door (there is a little room above the
  doors; make it fit), with an unlit dot field (dark dots visible). The page draws the lit dots (amber row 1,
  red row 2, scrolling when long). Manifest `led_signs`: one per door `{ "door": 1..5, "wall": "u0"|"v0",
  "along": [a0, a1], "z_px": [z0, z1], "offset": <tiles out from the wall plane of the dot face>,
  "cols": N, "rows_px": [row1 top/bottom, row2 top/bottom in z_px], "dot_pitch_px": p }` so the page can
  place a dot grid exactly on the face via the projection. Choose dot pitch so ~16-20 characters fit.
- **Restroom:** the screen-facing "RESTROOM" box -> a small wall plaque in the wall's perspective, and right of
  the door a small occupancy indicator. Deliver `wc_indicator: { "vacant": {file, file_2x, x, y, w, h,
  z_index}, "occupied": {...} }` (green lit EMPTY/VACANT vs red lit OCCUPIED, same rect, straight RGBA or
  plus-lighter glow - say which) - the page swaps them.
- **Bus stop sign "BUS 95":** a real pole/shelter sign in perspective.
- **Gate sign "◀ 1-2 · 3-5 ▶":** a physical hanging cinema wayfinding sign in perspective with two distinct
  groups (screens 1-2 left wing, 3-5 right wing), not a UI pagination box.

## 3. Posters right of the doors: correct aspect + chasing-bulb frames
Today they're too small and the aspect ratio is off. Use a true one-sheet proportion (27 x 40) in world space,
a bit bigger only if it stays believable, in a frame ringed with small bulbs. Update `poster_frames`
(along/z_px = the poster aperture on the wall, true 27:40 in world units) and add per poster two additive
prop loops at the frame's depth: `poster_bulbs_<n>_idle` (steady/soft twinkle) and `poster_bulbs_<n>_chase`
(bulbs chasing around the frame). Same prop-loop sheet contract. The page plays chase now and then.

## 4. The cinema is now called d.gg (owner, verbatim-ish)
"Like the Roxy sign is right now (the vertical blade), but actual neon letters, d.gg. Play with the colors:
Destiny has a blue, then the gg maybe something else, the dot some other color. It should really look nice,
like a neon letter, it should glow." Brand: destiny.gg's logo = white wordmark over slanted bars in blue
(#59aeea / #0090ff); site accents #70b8ff, #1fd8a4 on dark grey #18191b. Make real neon: bent glass tubes
with rounded ends, visible tube body when unlit parts show, standoffs/brackets, dark backer/raceway, a thin
outline tube, bright core + soft halo, glow on the wall and a reflection on the wet sidewalk/street; maybe one
tube with an occasional flicker in the loop (seamless). Lowercase "d.gg" reads well vertically or as a
stacked blade - your call. Rename everything else that says ROXY: bus "95 ROXY"/"ROXY TRANSIT" -> d.gg,
plates "RXY 95" -> e.g. "DGG 95", etc. (vehicle sprites + slices + lights).

## 5. Surroundings fixes
- Top-left: the empty space left of VIDEO RENTAL - keep populating (more of the block, shopfront, alley).
- Bottom-right: RECORDS & REPAIR sits behind an odd empty tiled plaza. Make it make sense: continue the
  sidewalk past the alley mouth (curb cut), the shop front facing the street at the sidewalk line, and fill the
  rest with believable stuff (dumpster, newsstand, parked car, planter, steps) - respect the occlusion envelopes.

## 6. Ad surfaces for the next phase (memes/inside jokes from the community; content drawn by the page)
Model blank, lit-or-unlit advertising surfaces in the world and describe each so the page can paint content
onto it: the tower where the green billboard was (a real rooftop/facade billboard on its structure, in
perspective - remove the old screen-facing billboard frame and aperture completely), the bus shelter ad
lightbox, one wheat-paste/poster wall (alley or a shutter), and the bus sides (blank ad panel on each bus
direction/state sprite). Manifest `ad_surfaces: [{ "name", "quad_px": [[x,y] x4 clockwise from top-left of the
content], "z_index", "overlay": {file, file_2x} (frame/glass glare/shading drawn above the content, straight
RGBA), "lit": true|false, "aspect": w/h }]`; for buses add `ad_panel_quad` per direction/state in sprite-local px.

## 7. Ambient life (restrained, never everything at once)
More visible gentle puddle ripples, an occasional single neon tube flicker on a neighbour sign, steam from a
roof vent, a TV-flicker window or two, popcorn machines (exist), all seamless in the 6 s loop or as prop loops.

## 8. Zoom-ready loop
The page will add a camera that zooms 1.75-2x onto one chatter now and then. Provide `light_loop_2x.webm`
(3840x2160, same 144 frames, same contract) in addition to the 1080p one; rain_fg can stay 1080p (it is drawn
in screen space). Report its size/bitrate and decode cost.

Validation as before (occlusion 0 against the walk/road envelopes, seams, black level, protected files),
plus: no screen-facing sign left in the art.
