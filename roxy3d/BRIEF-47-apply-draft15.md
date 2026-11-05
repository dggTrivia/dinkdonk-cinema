# Brief 47: apply draft 15 as drafted (owner approved, 04 Nov 2026)

The owner approved draft 15 (qa10/draft15-cars-door2.png, NOTES-46.md) "as drafted": the vehicle studio lighting you
chose (overhead fill 0 W, reflections 8 / 11.2 / 6.8 W, world .015, vehicle-only overrides) and the Screen 2 masked
door correction. Do the full apply you scoped in NOTES-46 "Full-apply scope".

## Do
- Build a NEW pack folder roxy3d/out10b/ = a copy of the live roxy3d/out10/ with only these assets replaced:
  - the 12 vehicle body states (bus/taxi both directions closed+open, both sedans both directions): whole-body PNGs
    1x + @2x and all depth slices (and door_open slices), same names, sizes, anchors, crops and contracts; light
    passes (*_light*.png) untouched. Validate slice reconstruction as before.
  - the 10 static plates (bg, base, lit_bg, lit_bg_dry, full; 1x + @2x) with the Screen 2 offset D.
  - doors/screen_2.png + @2x with the pose-aware leather mapping, frame 0 matching the corrected static leaves.
- Keep out10's light_loop.webm / light_loop_2x.webm exactly as they are now (they were post-fixed in BRIEF-45; do
  not take them from anywhere else). Check base + loop headroom again with the new base.
- manifest.json: set lanes.far to 12.75 (the road is v 10.6-13.5 with the dashed centre line at v 12; far = 12 put
  right-to-left traffic on the dashes; the page already corrects this) and note the draft-15 revision; everything
  else unchanged.
- Refresh checksums.json (all files) and validation.json with the checks you ran.
- Fix the scene sources for the next real render too (Screen 2 receiver membership by stable door id, its dry
  leather material, the vehicle-only lighting override), only in roxy3d/ source files, without rendering the scene.

## Deliver
NOTES-47.md (what changed, numbers, validation), STATUS line, stop. No owner images (the draft was approved).
Do NOT modify roxy3d/out10/ or standby/roxy.html. Local GPU only, no cloud.
