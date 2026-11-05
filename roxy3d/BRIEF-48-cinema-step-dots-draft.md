# Brief 48 (RENDER, QUICK DRAFT ONLY): dim the red step / floor marker lights a little

Owner (04 Nov 2026, screenshot of the stalls): "dim the floor lights a lil bit". These are the red/orange step-dot
markers (`STEP_DOTS`, palette `step_dots #D94B32`, emissive) along the aisles, treads and row ends, in the current
final scene `roxy_cinema_draft12_door.blend` / draft 12 full pass (`qa11/CINEMA-DRAFT-12.md`, runtime12_full/).

Local RTX 3050 GPU only; write only inside roxy3d/; no page files, no draft 11/12 assets or layouts touched.

## Do
1. From the draft 12 final scene, make two variants that change ONLY the step-dot markers' brightness (their emission
   strength, and their glow/spill on the floor if it comes from them): **V1 = ~65 %** and **V2 = ~45 %** of today's.
   They must stay readable as small markers; nothing else changes (no other lights, materials, camera, exposure).
2. Quick renders (lower samples fine) and native-pixel crops of the same stalls/aisle area as the owner's screenshot
   (left aisle and the rows around it, plus one crop of the right aisle), for: today, V1, V2 - lit state. Also one
   crop of V2 in the lights-down (dim) state. Save as `qa11/draft13_stepdots/crop_{today,v1,v2}_{left,right}.png`
   and `crop_v2_dim_left.png`, plus a side-by-side `qa11/draft13_stepdots/compare.png` with labels.
3. NO final 4K / slices / sheets / layout. Report `qa11/CINEMA-DRAFT-13-STEPDOTS.md` (what objects/materials drive
   the dots, the exact values used, and what the full pass will regenerate), STATUS line, stop.
