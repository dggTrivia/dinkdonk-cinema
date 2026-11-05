# Brief 45: alley reflection flicker in the out10 light loop (post-fix, no re-render)

The owner watched the final lobby (out10, live on roxy.html) and reports a flicker: in the alley between the lobby's
outer wall and the right-hand building (1080p coords roughly x 1440-1720, y 800-1000), the cyan DINK DONK reflection
on the wet ground and a warm patch on the roof ledge switch on and off.

## What Claude measured (light_loop.webm, decoded in Edge, mean 8-bit level per region)
- DINK DONK letters: steady (~0.7, they live in base.png). Pepe tube: 6.0 <-> 10.9, switching exactly every 6 frames
  (the designed circuit alternation).
- Alley patch (x 1515-1598, y 868-950): two exact levels, 12.6 and 6.4, in an irregular pattern that repeats every
  24 frames: on 0-7, off 8, on 9-14, off 15, on 16, off 17-23 (then frame 24 = frame 0). It follows no light in the
  scene: a reflection switches on/off by itself.
- Block scan (40 px blocks, jumps > 1.5 levels that do not fall on a 6-frame boundary): ~20 blocks in
  x 1440-1720, y 800-1000 (jumps up to 15 levels). Smaller hits: x 520-600, y 920-960 (street, mean ~37, jumps ~3-4)
  and the left edge x 0-160, y 440-720 (jumps ~2-4). These may be legitimate rain/ripples; judge them.
- With ?loop=0 the page shows no flicker, so it is in the video, not the page.

## Do
1. Find the cause in the scene/bundle (read-only): which object/material/geometry makes that reflection toggle
   (reflection-only catchers, puddle/ripple geometry, GN drips, the 24-frame wet phase leaking into the background
   loop, something else). Explain with evidence; this is for the next render, do not re-render now.
2. Post-fix BOTH light_loop.webm (1920x1080) and light_loop_2x.webm (3840x2160) from roxy3d/out10/:
   make the alley reflection steady in the "on" state (the reflection is nice; it must just stop blinking), keeping
   rain ripple motion there if you can (e.g. replace the off frames by the nearest on frames inside a feathered
   mask, or another method you can justify). Fix the street/left-edge spots only if they are the same defect.
   Everything else in the videos must stay as it is. Keep the contract the page relies on: same size, 24 fps,
   144 frames (48 unique x 3), seamless loop, VP9 settings as in the bundle's video.py, a nonnegative difference
   above base.png / base@2x.png, the 2x video still the exact complement of base@2x.
3. Verify with numbers: per-frame region means before/after for the alley, Pepe tube and a few untouched regions,
   plus a block scan like the one above (after: no off-beat jumps in the alley); max difference outside the mask.

## Deliver
- roxy3d/out10-loopfix/: light_loop.webm, light_loop_2x.webm, NOTES-45.md (cause, method, numbers), and ONE QA
  image for Claude: the alley crop, 24 frames before (top row) and after (bottom row). No clips, nothing else.
- STATUS line at the end of NOTES-45.md, then stop.

Do NOT touch roxy3d/out10/, standby/roxy.html or anything outside roxy3d/. No cloud pods. Blender is in
standby/tools/blender-5.2.3-windows-x64 (it has the video encoder/decoder the bundle used).
