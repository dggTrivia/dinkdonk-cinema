# Brief 5: pass 4 - art polish + small prop loops

out3 is live (vehicles are in and look great: a bus now pulls up and chatters step out). Same rules;
**outputs to `roxy3d/out4/`** (complete set, copy what you don't change; layout 2; keep every existing
manifest key and contract, add new keys only).

## A. Art polish (from the reviewer's design notes)
- The confetti carpet competes with the chatters (emotes ~50 px): lower its contrast/saturation a lot,
  keep the 90s pattern readable but calm; keep the walkway areas a bit darker/worn.
- Put warm light where the action is: soft warm pools at the box office windows (u 4.85, v 6.0 and 7.4),
  in front of the snack registers (v 5.05 at u 6.6 / 8.2 / 9.8), at the usher gate (3.7, 3.7) and spilling
  from each screen door. Slightly dim the rest of the lobby so people pop.
- Pale counter tops and luminous trim are a bit loud: tone them down a notch.
- Keep everything else (layout, calibration, footprints, marquees, poster frames, green rect) identical.

## B. Small pre-rendered prop loops (additive, like the light loop)
Short seamless loops that sit on top of the static occluder sprites (so they are not covered), each a
small cropped WebM (VP9, 24 fps, 2-4 s, on black, additive) or a PNG sprite sheet, with its pixel
rect in the 1920x1080 frame and the z_index to use (just above its prop):
- popcorn kernels popping and tumbling inside both popcorn machines' glass cases,
- the arcade cabinet screen in attract mode (blinking "INSERT COIN", little sprites),
- the soda fountain's backlit logo / the snack menu boards gently buzzing,
- the TICKETS board over the box office: a subtle flicker on one letter now and then.
Manifest key: `"prop_loops": [ { "name", "file", "file_2x"?, "x", "y", "w", "h", "z_index", "blend": "plus-lighter" } ]`.

## C. Fallback still
Regenerate `lit_bg` for the new look.

Report as before (what changed, calibration, timings, anything not done).
