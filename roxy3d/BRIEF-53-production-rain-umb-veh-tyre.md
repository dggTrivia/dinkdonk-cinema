# Brief 53: PRODUCTION of draft 21 (umbrella rain, vehicle-top rain, tyre spray + wake) for the live page

Owner (04 Nov, on qa10/draft21-rain-stronger.png): "let's go with draft 21 and that's it". So: the full set, in exactly
the draft-21 look and parameters (out10f/ + NOTES-52.md are the reference; no new look decisions), packaged so Claude
can wire it into roxy.html. Local GPU only, no cloud.

## Render
- Umbrellas: wet loops for all 4 colours (red, blue, yellow, black), same 88x80 frame and [44,68] anchor as the open
  sprites, 48 frames / 24 fps, source-over (full replacement sprite, like draft 21's red).
- Vehicle tops: bus, taxi, sedan_a, sedan_b; +u and -u; closed and door_open where the manifest has a door_open
  state. Additive (plus-lighter) loops, 48 f / 24 fps, CUT INTO THE EXISTING DEPTH SLICES as your NOTES-51/52 plan
  says (partition by landing surface/local u, slices sum exactly to the unsliced overlay, crop per slice with its
  offset, zero double-addition) so each water slice is drawn right above its body slice.
- Tyre spray + wake: all 4 vehicle types, +u and -u, spray (additive, rises from the wheels) and wake (road-flat)
  as separate loops anchored to the vehicle ground centre (the vehicle sprite anchor point), 48 f / 24 fps.
- Crop transparent/black margins. Report total 1x and @2x decoded VRAM (the page loads 1x at 1080p, @2x at dpr>1.3).

## Package (new staging pack roxy3d/out10g/ = full copy of live out10 + the new files; Claude tests it with
?artdir=out10g, then copies the new files into out10 itself)
Manifest additions (exact keys, so the page can rely on them):
- `umbrella.wet[colour]` = sheet { file, file_2x, frames, columns, rows, fps, frame_width, frame_height, anchor, loop: true }.
- `vehicles[type][dir].roof_rain` = array with the SAME length and order as that state's `slices`, each
  { file, file_2x, x, y, w, h, frames, columns, rows, fps } where x/y/w/h are in the same sprite-local coordinates as
  the slice entries (the page places it like the slice, adding x/y); same under `door_open.roof_rain` for open states.
- `vehicles[type][dir].spray` and `.wake` = sheet { file, file_2x, frames, columns, rows, fps, frame_width,
  frame_height, anchor, full_speed } where anchor is the pixel in the frame that sits on the vehicle's ground centre
  (P(u, lane)) and full_speed is the tiles/s the plume was rendered for.
Refresh checksums.json / validation.json for out10g. Live out10/ and roxy.html stay untouched.

## Deliver
NOTES-53.md (files, sizes, VRAM, render time, validation incl. slice reconstruction), STATUS line, stop. No owner
image needed (the look is approved); Claude checks it in the page.
