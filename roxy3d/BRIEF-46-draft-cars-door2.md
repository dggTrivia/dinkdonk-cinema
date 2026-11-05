# Brief 46: ONE draft image - night-lit vehicles + screen-2 door brightness (out10 is live)

The owner checked the live lobby (out10, roxy.html) and approved a draft for two fixes. Drafts rule: ONE image,
nothing else for the owner. Do not change the live pack yet.

## A. Vehicles look lit by a lamp over everything
The sedans (sedan_a, sedan_b), taxi and bus have pale blue-white roofs, bonnets, boots and upper windows wherever they
drive, also where the street is dark. Claude checked: the page draws nothing over them (only the bus shelter and a
street lamp, where they stand in front of the road); the pale tops are in the body sprites
(out10/vehicles/*_plus.png, *_minus.png, slices). Cause found in cloud/bundle/build_vehicles.py `lighting()`:
'Cool overcast fill' - an AREA light, size 220, straight above at z=310, strength 5, colour (.38,.51,1), plus world
Background strength .3. The street scene has no such light, so every upward face glows.
Do: re-light the vehicle studio to match the night scene: that overhead fill far down (or gone), keeping the cyan and
warm reflection lights that tie the cars to the cinema neon. Judge the level against the scene itself (road/sidewalk
next to where cars drive, base.png / full.png), not by taste. The headlight/tail-light passes (*_light*.png) are not
affected; leave them.
For the draft render only sedan_b +u and bus +u (2x is fine), and composite them into the scene at a representative
road position the way the page stacks them (body/slices source-over, light pass plus-lighter, on base + a light-loop
frame).

## B. Screen 2 door ("LAST NIGHT IN SOHO") is much darker than screens 1 and 3
The dark leaves are in the render itself (full.png, bg/base): doors 1 and 3 are bright red, door 2 dark maroon.
Possible causes (not confirmed): the middle reflector flood is 24 W vs 28 W on the others (draft 13 notes), the red
standee next to it blocking light, something else. Find the cause in the scene with evidence.
Fix without a cloud render: a masked 2D adjustment of door 2's leaves (and their frame if needed) in every static
plate that shows them (bg, base, lit_bg, lit_bg_dry, full; 1x and @2x) so they match doors 1/3 statistically, keeping
the light loop's additive contract (the loop is a nonnegative delta above base - check it still holds). Say what the
screen_2 door-opening sheet (doors/screen_2*.png) needs to match, and do it in the draft composite if it shows.
For the next real render, say what to change in the scene.

## Deliver
- ONE image: qa10/draft15-cars-door2.png, 1280x720. Top half: before | after crop of the three screen doors.
  Bottom half: before | after crop of sedan_b and the bus on the street at the same spot. Small labels only.
- NOTES-46.md in roxy3d/: causes with evidence, the chosen light levels and door adjustment (numbers), what a full
  apply would touch (files, render count, time on this laptop), STATUS line, then stop.

Write only inside roxy3d/ (new files/folders). Do NOT modify roxy3d/out10/ or standby/roxy.html. Local GPU only
(RTX 3050, Blender in standby/tools/blender-5.2.3-windows-x64), no cloud, no test clips.
