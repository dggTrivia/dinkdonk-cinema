# Pass 4: art polish and small prop loops

Implements `BRIEF-5-pass4.md`. The complete delivery is `out4/`: **208 files,
63,879,292 bytes**. It includes all inherited scene and vehicle assets, refreshed
scene renders at 1920x1080 and native 3840x2160, the rebuilt ambient WebM, and
eight new additive PNG sprite sheets at both resolutions. `out/`, `out2/` and
`out3/` are unchanged: all **473** existing files match the initial SHA-256
inventory. No page or shared file was edited. All work, logs and caches are
inside `roxy3d/`; no internet or downloaded assets were used.

## Art changes

- Carpet flecks, diamonds, borders and medallion use a much quieter palette.
  Their materials are separate from candy and standees. The existing worn
  entrance path is darker. At the same unobstructed lobby coordinates, local
  luminance-detail RMS drops from 11.240 to 4.465, a **60.3% reduction**.
- Six soft warm pools are centred on the two ticket windows `(4.85,6.0)` and
  `(4.85,7.4)`, three snack registers `(6.6,5.05)`, `(8.2,5.05)`, `(9.8,5.05)`,
  and usher gate `(3.7,3.7)`. A separate lights-off render confirms a positive
  warm contribution at all six coordinates: mean added R is 29.9-37.8 and B
  is 11.3-13.5 in 8-bit display values over 11x11 pixel samples.
- Every screen door has a steady soft warm spill in addition to its existing
  periodic projector light. General lobby lighting is slightly dimmer.
- Counter stone is darker and rougher. Local ticket/snack/partition trim and
  menu backlights are reduced. Exterior neon and aperture geometry are retained.

See [before/after](qa4/before_after.png), [final still](out4/full.png), and the
[isolated action-light contribution](qa4/action_light_difference_x3.png).

## New prop assets and playback

Each loop is **72 frames, 24 fps, 3 seconds**, stored row-major in a **6-column,
12-row** RGB PNG sheet on black. The 16 sheets total **1,115,004 bytes**.
Coordinates below are 1x stage pixels; use the exact manifest values for drawing.

| Name | x | y | Frame w | Frame h | z_index |
| --- | ---: | ---: | ---: | ---: | ---: |
| `popcorn_1` | 1048 | 553 | 68 | 66 | 1980 |
| `popcorn_2` | 1112 | 585 | 68 | 66 | 2075 |
| `menu_popcorn` | 1045 | 522 | 128 | 82 | 2075 |
| `menu_soda` | 1177 | 588 | 114 | 74 | 2267 |
| `menu_nachos` | 1294 | 647 | 116 | 76 | 2458 |
| `arcade_attract` | 1177 | 889 | 32 | 42 | 3021 |
| `soda_logo` | 1172 | 631 | 46 | 36 | 2171 |
| `tickets_letter_e` | 689 | 554 | 14 | 20 | 1971 |

The two poppers contain original lobed 3D kernels rotating on periodic arcs,
with attenuation through the existing glass and occlusion by the kettle and
cabinet. Their 2x frames are rendered natively. The arcade has original tiny
pixel art, a moving sprite and blinking `INSERT / COIN`. All three menu boards
have restrained periodic backlight buzz; the fountain has a pulsing `SODA`
logo and selection buttons. Only the original E glyph in `TICKETS` receives
the brief intermittent amber flicker.

`prop_loops` retains the requested fields (`name`, `file`, `file_2x`, `x`, `y`,
`w`, `h`, `z_index`, `blend`) and adds sheet metadata, `parent`, and
`parent_slices`. Every loop sits one z unit above the highest overlapping slice
of its owning prop. Sort these entries into the same walker/occluder stack;
placing them under all occluders would cover the animation.

For a canvas consumer, use the following source-cell calculation. Draw in the
entry's sorted position, with `lighter` (the canvas additive operation).

```js
const frame = Math.floor(elapsedSeconds * loop.fps) % loop.frames;
const resourceScale = use2x ? 2 : 1;
const sw = loop.w * resourceScale;
const sh = loop.h * resourceScale;
const sx = (frame % loop.columns) * sw;
const sy = Math.floor(frame / loop.columns) * sh;
ctx.globalCompositeOperation = 'lighter';
ctx.drawImage(sheet, sx, sy, sw, sh, loop.x, loop.y, loop.w, loop.h);
ctx.globalCompositeOperation = 'source-over';
```

For DOM/CSS, clip a sheet to one cell and use `mix-blend-mode: plus-lighter`.
Keep its displayed frame size and position in 1x CSS pixels, including when
loading `file_2x`. The black cell gutters are checked at both resolutions.
For reduced motion, freeze a frame or omit the prop overlays. The underlying
static props remain complete.

The existing ambient video contract remains 1920x1080, VP9/WebM, 24 fps,
120 frames / 5 seconds, now **2,842,609 bytes**. `base` + video is the animated
background. `lit_bg` is rebuilt from base plus lossless ambient frame 60 and
contains no occluder props. Use it instead of base + video for fallback;
adding the video over it would double the ambient light. The new prop sheets
can be used with either background. `full` remains the fallback with all
ordinary occluders composed, preserving its previous contract.

All previous manifest keys remain. Layout, projection, occluder coordinates,
49 depth slices, all footprints, marquee/poster apertures, billboard rectangle,
staff/customer positions, lanes and arrival stops remain identical. All 48
vehicle PNGs and their metadata are copied unchanged. Existing baked signs are
retained; new animated lettering is `SODA` and `INSERT / COIN`. No footprint
changes were introduced in pass 4.

## Validation and visual review

[final_validation.json](qa4/final_validation.json) records the complete delivery
inventory and SHA-256 hashes, plus the following successful checks:

- Ten rendered calibration markers, including street/arrival anchors: maximum
  axis error **0.011163 px**, against the required 1 px tolerance.
- Every parent sprite reconstructs exactly from its depth slices at both
  resolutions. Transparent pixels have zero RGB. Composing occluders over
  each `lit_bg` reconstructs the corresponding `full` exactly.
- Geometry bounds match pass 3. Previous manifest keys and fixed contract
  values match, and live inventories and vehicle files are unchanged.
- Independently regenerated prop frame 72 equals frame 0 exactly in every
  loop. Last-to-first changes are below the maximum ordinary adjacent change
  for each prop. The ambient endpoint likewise matches exactly before encoding.
- Seven frames decoded from the actual VP9 have RGB mean absolute errors
  0.062-0.305/255 and PSNR 46.88-53.17 dB. The decoded wrap change is
  0.193/255, within the ordinary source-frame change range. Billboard interior
  stays black. At two sampled times, two edge channel values ring to 3/255;
  this is tiny VP9 edge compression, not content in the protected aperture.

Reference art, low-sample iterations, final before/after images, masks,
the isolated light difference and nine loop phases were visually inspected.
The [prop contact sheet](qa4/prop_loops_check.png) shows all key regions.
[prop_preview.mp4](qa4/prop_preview.mp4) is a 9-second H.264 close-up preview
with three prop cycles and a full-scene thumbnail, holding the ambient at the
fallback frame. Three frames decoded from this actual MP4 were also inspected.

`qa4/review.html` is a local canvas preview using the delivered manifest,
ambient video and depth-sorted sheets; it has pause/toggles and close-up views.
The browser automation host was unavailable, and automatic approval review
rejected launching VLC because computer-use access to VLC was not approved.
Interactive playback was therefore not verified. Source/decoded frame review
and numerical sequence checks are complete. HTML/OBS integration remains with
the page agent, as specified by the original brief. No requested asset is
omitted.

## Reproduction and measured time

Run from `standby` in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass4.ps1 -Mode all -Samples 96
```

`-Mode preview` renders the material/light preview at 32 samples.
`-Mode package` reuses existing `qa4` render sources and recreates all packaged
assets, videos, manifest and validation. The wrapper preserves the original
live SHA inventory and checks it at the end. It redirects temporary/OptiX/CUDA
caches into `roxy3d/cache/` and restores the calling environment afterward.

Main scripts are `build_pass4.py`, `render_prop_sources.py`,
`compose_pass4.py`, `encode_pass4.py`, `package_prop_loops.py`,
`preview_pass4.py`, `calibrate_pass4.py`, `check_action_pools.py` and
`verify_pass4.py`. Prior builders are reused read-only. `roxy_pass4.blend`
contains the polished scene and packed font. All component stages were run;
the PowerShell wrapper was also syntax checked.

| Stage | Measured time |
| --- | ---: |
| Final Cycles job: 44 renders, 96 samples, OptiX + denoise | 8 min 35 s wall; 482.5 s rendering |
| Independent full scene, 1x / 2x | 26.9 s / 102.4 s |
| Background minimum, 1x / 2x | 25.8 s / 105.3 s |
| Prop surface masks and 73 popcorn frames, 32 samples | 21.9 s |
| Ambient frame synthesis, static packaging and slices | 232.9 s |
| VP9 encode and seven actual decoded samples | 20.8 s |
| Independent action-lights-off verification render | about 28 s |

These are production-stage timings, excluding art iterations and additional
QA. The ambient loop uses fixed Cycles light bases and periodic compositing,
so it does not require 120 expensive beauty renders and avoids independent
per-frame denoiser flicker.
