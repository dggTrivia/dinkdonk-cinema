# Pass 6: separated screen stacks, wear, doors, umbrellas, janitor and drip

Implements `BRIEF-7-pass6.md`. The standalone delivery is `out6/`, layout 2.
The five live packs are read-only inputs. No HTML or shared file is edited.
`out6/manifest.json` retains all prior keys and contracts, with updated scene
images, ambient video, marquee coordinates and video integrity fields. The new
poster-plane, door-animation, umbrella, janitor and shelter-drip entries are
additive. The final inventory, hashes and numeric checks are in
`qa6/final_validation.json`.

Final delivery: **364 files, 79,854,424 bytes**. It includes **42 new PNGs**
(12 door sheets, 12 janitor sheets, 16 umbrella assets, 2 drip sheets),
143 updated inherited scene/ambient assets, 178 byte-identical inherited
assets, and the manifest. All **1,003 files** in `out/` through `out5/` match
the starting SHA-256 inventory. All prior manifest keys are preserved.

## Art and coordinates

The camera is unchanged: `P(u,v,z)=[900+60(u-v),350+30(u+v)-z]`.
All coordinates below are logical 1920x1080 pixels unless stated otherwise.
Every @2x source doubles source dimensions; CSS placement stays at 1x.

All five stacks now have separated title boxes, clear door heads and exposed
poster apertures beside their own doors. Screen 4's inner title height changes
from 92 to 80 px to leave clearance above its door and below the fixed video
billboard. Other title interiors remain 176x92 px. The poster bounds specify
the exact inner wall plane; the thin metal borders sit outside those bounds.

Every change to an existing placement or aperture size is listed here:

| Screen | Marquee bottom centre before | Bottom centre now | Inner size before → now | Poster wall | Poster along before → now (tiles) | Poster z before → now (px) |
|---|---|---|---|---|---|---|
| 1 | [516,418] | [490,396] | [176,92] → [176,92] | u0 | [4.85,5.65] → [5.2,5.7] | [23,128] → [20,90] |
| 2 | [660,346] | [686,315] | [176,92] → [176,92] | u0 | [2.45,3.25] → [2.8,3.3] | [23,128] → [20,105] |
| 3 | [1188,370] | [1188,350] | [176,92] → [176,92] | v0 | [5.55,6.35] → [5.5,6.1] | [23,128] → [20,105] |
| 4 | [1392,472] | [1387.2,450] | [176,92] → [176,80] | v0 | [8.95,9.75] → [8.9,9.5] | [23,128] → [20,105] |
| 5 | [1572,562] | [1582.8,540] | [176,92] → [176,92] | v0 | [11.95,12.75] → [11.9,12.5] | [23,128] → [20,105] |

For u0, along means v; for v0, along means u. The marquee supports and poster
border/light geometry and analytic rain exclusions follow these revised apertures. `qa6/coordinates.json`
also records every old/new value in machine-readable form.

Doors stay at screen 1 [0,6.4], 2 [0,4], 3 [4.8,0], 4 [8.2,0],
5 [11.2,0], WC [0,8.3]. Screen door openings remain 1.1 tiles x 114 px;
WC remains 0.8 tiles x 104 px. No walkable footprint, static sprite rectangle,
static depth-slice rectangle, staff/customer point, vehicle anchor, lane,
arrival stop, cat anchor, tyre-spray anchor or billboard aperture changes.
The billboard remains [1296,40,576,324].
Its placeholder pixels in both resolutions are copied exactly from pass 5,
isolating this video-replacement region from small indirect-light differences.

One additional measured geometry coordinate changes: snack counter
`geometry_z_px` [0,44] → [0,44.172]. This is the 0.172 px raised hairline
scratch relief on the top, recorded in `pass6_art.surface_height_changes`.
Its sorting height remains 44 px and its footprint, crop and depth-slice
rectangles remain exact. No other occluder geometry bounds change.

Wear includes exposed stone chips and scratches on the ticket/snack counters,
scuffed metal kickplates and thresholds, corner grime, cigarette burns and gum
on the pavement, and stronger uneven glass residue. Furniture trim emits 30%
of its pass-4 level; sign neon remains. All 32 carpet objects, geometry,
transforms and material graphs compare identically with the saved pass-4 scene.
Lighting changes can alter rendered carpet pixels; its art and materials do
not change. The remaining inherited prop loops and all vehicle/cat/spray assets
are carried forward byte for byte.

No new baked text is introduced. Existing baked signs remain TICKETS/prices,
SNACK BAR/menus, gate, RESTROOM, ROXY, BUS 95, ORBIT, POPCORN and the two standee
titles. Movie-title and poster apertures remain blank for page content.

## Door animation integration

Six 16-frame open/hold/close one-shots at 18 fps (0.889 seconds), 4 columns,
4 rows, native 2x with filtered 1x. Each logical cell is 156x204 px. Screen
leaves pivot inward 79 degrees; the WC has a single inward leaf. Actual Cycles
renders reveal the shallow vestibule and add warm corridor spill.

| Door | New overlay x,y | Cell w,h | z_index |
|---|---|---|---|
| 1 | [455,403] | [156,204] | 900 |
| 2 | [599,331] | [156,204] | 900 |
| 3 | [1093,355] | [156,204] | 900 |
| 4 | [1297,457] | [156,204] | 900 |
| 5 | [1477,547] | [156,204] | 900 |
| wc | [341,460] | [156,204] | 900 |

Draw selected cells with normal source-over above base+ambient (or lit_bg),
below walkers and static occluders. They use a straight RGBA opaque doorway
core to erase closed leaves and their ambient porthole glow, with signed-change
floor replacements for warm spill. Poster and title planes are excluded. They
are not additive. First and last frames are transparent; clamp at frame 15,
then remove. Use this pack's background, not a previous pass's background.
The packaged edge feather prevents a rectangular floor-light cutoff.

## Umbrella and janitor integration

Four umbrellas: red, blue, yellow, black. Each has a shaded open PNG and a
six-frame fold sheet at 12 fps (0.5 seconds), six columns. Logical cells are
88x80 px. **Anchor [44,68] is the curved handle grip.** For a 50 px emote,
start with grip `P(u,v,40)+[10,0]`, then subtract the anchor for the sprite's
top-left. Keep the umbrella immediately above its owner in the depth stack.
Frame 0 of fold is exactly the open image; clamp at frame 5 before removal or
holding the folded state. The 3D canopy folds down around the metal shaft.

The janitor has a cap, shirt, stitched blue overalls, work boots, straw broom,
metal bucket and wristwatch. There are six sheets: four actual 3D walking
orientations, sweep, and idle leaning on the broom/checking the watch.
Logical cells are 96x96 px with ground anchor [48,78]. Place at
`P(u,v)-anchor`, sort at `1000+round((u+v)*100)`. Soft contact shadows are
included. Same entry structure and direction naming as the inherited cat.

Walking: 12 frames at 12 fps, 6 columns x 2 rows, one-second loop,
**stride_tiles=0.48** (move 0.48 tiles per second). Stance feet move backward
at the corresponding speed. Sweeping and idle: 48 frames at 16 fps, 8 columns
x 6 rows, three-second loops. The pail is carried during walking and placed
beside the stationary janitor. Independently rendered endpoint frames check
the cycle seams; those extra endpoint frames are not included in the sheets.

## Shelter drip

One new 72-frame, 24 fps, three-second additive prop loop, matching the existing
prop-loop format. Rect [320,557,52,112], six columns x twelve rows. The parent
is bus_stop, at z_index 2103, immediately above its listed shelter slices.
Roof point [u,v,z]=[0.35,9.6,84] projects to
[345,564.5]. The small puddle centre [0.35,9.6] projects to [345,648.5].
Three falling drops per period accelerate under gravity and produce expanding
dimetric rings. The independently regenerated period endpoint equals frame 0.
Use plus-lighter on black, just like the eight inherited prop loops.

## Review and reproduction

Review `out6/full.png`, `qa6/stack_layout_check.png`,
`qa6/wear_comparison.png`, `qa6/door_contact_sheet.png`,
`qa6/umbrella_contact_sheet.png`, `qa6/janitor_contact_sheet.png`,
`qa6/shelter_drip_check.png`, and `qa6/pass6_preview.mp4`.
The six-second review movie composites the delivered sheets over the new
scene, with walking translation, prop depth and inherited ambient/prop loops.
Actual decoded MP4 and VP9 frames are checked against their source frames.
This is asset and local render QA; the separate page integration is not changed.

The source ambient frames are exactly black inside the billboard aperture.
Decoded VP9 introduces at most 3/255 at its edges and 1/255 on a few interior
pixels in one sampled frame; total aperture mean error stays below 0.001/255.
The page's video covers this region. The static placeholder is byte-identical
to pass 5 at both resolutions.

Run from the standby workspace:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass6.ps1 -Mode all -Samples 96
# Repackage existing final render inputs and repeat all acceptance checks:
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass6.ps1 -Mode package
# Fast scene look development only:
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass6.ps1 -Mode preview
```

The wrapper serializes render jobs to avoid GPU contention. It redirects
temporary files and renderer caches under roxy3d. No network or downloaded
assets are used. The scene is saved as `roxy_pass6.blend`; every model and
animation is reproducible from the Python sources. Timings are recorded in
`qa6/scene_render_times.json`, `characters_metadata.json`,
`doors_metadata.json`, `loop_validation.json`, `video_metadata.json` and
`preview_metadata.json`. Trial render logs remain under qa6 for traceability.

Acceptance covers all prior manifest keys, live SHA-256 inventories, inherited
asset hashes, both resolutions, exact parent/depth-slice reconstruction,
fallback reconstruction, straight alpha, transparent cell borders, one-shot
endpoints, loop seams, marquee/poster/door polygon separation, unchanged
carpet data, marker calibration, video format/duration and decoded pixels.
See `qa6/final_validation.json` for the final measured results and inventory.

Final measured results:

- Marker calibration maximum axis error: **0.011163 px** (required <=1 px).
- All 18 parent sprites and 49 depth slices reconstruct exactly at both scales;
  static crop, slice and sorting footprints remain unchanged.
- All 32 saved carpet objects/material graphs match pass 4 exactly.
- Marquee-border to upper-door-corner gaps: screens 1–5 respectively
  **12.5, 21.5, 10.5, 12.5, 12.5 px**. Projected marquee, poster and door
  polygons have no intersections.
- New sprite-sheet dimensions, native 2x/downsampled 1x correspondence,
  transparent borders, one-shot endpoints and loop endpoints pass. Both old
  porthole positions in each open screen door match the actual open render;
  the adjoining poster plane remains excluded.
- Ambient output: VP9, 1920x1080, 120 frames, 24 fps, five seconds. Seven actual
  decoded samples have mean RGB error between 0.059 and 0.329 levels out of 255.
- Review MP4: 1280x800, 144 frames, 24 fps, six seconds, 1,770,824 bytes.
  Six actual decoded frames were checked numerically; selected decoded frames
  were also inspected visually during review.

Measured production timings on this run: 561.614 seconds for the 44 final
scene render calls (622 seconds including scene setup/overhead); 759.136
seconds for native 2x janitor/umbrella rendering; 248.838 seconds for the final
door finishing batch, which reused door 1's six opening poses from the earlier
partial batch; 227.013 seconds for scene/ambient packaging; 21.979 seconds for
VP9 encode/decode; 4.377 seconds for review MP4 encode/decode. Earlier preview
and superseded render attempts are separate and remain in the QA logs.

All requested asset work is complete. Live page integration remains the
separate consumer's task; this pass edits no page or shared files.
