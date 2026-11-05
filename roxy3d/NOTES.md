# The Roxy — procedural Blender background

The scene is built entirely from Python in Blender 5.2.3 LTS. The three reference
images and the complete `../roxy.html` were read before modeling. All generated
files, scripts, logs and caches are inside `roxy3d/`; the HTML and shared files
were not edited. No network requests or downloaded assets were used. Arial Bold
comes from Windows and is packed into `roxy.blend`.

## Pass 5

Vehicle depth slices, brake/indicator lights, the animated lobby cat, tyre spray
and the complete `out5/` delivery are documented in [NOTES-PASS5.md](NOTES-PASS5.md).
All four live folders (`out/` through `out4/`) are unchanged. See `qa5/` for
depth comparisons, pose/light contact sheets, the preview movie and validation.

## Pass 4

Art polish, warm service lighting, eight prop loops and the complete `out4/`
delivery are documented in [NOTES-PASS4.md](NOTES-PASS4.md). All three live
folders (`out/`, `out2/`, `out3/`) remain byte for byte unchanged. See `qa4/`
for before/after renders, a movie preview and delivery validation.

## Pass 3

Vehicles, arrival anchors, door variants and the complete `out3/` delivery are
documented in [NOTES-PASS3.md](NOTES-PASS3.md). The live `out/` and `out2/`
folders are preserved byte for byte; QA and delivery hashes are in `qa3/`.

## Pass 2

The newer layout and ambient-loop work is documented in [NOTES-PASS2.md](NOTES-PASS2.md).
Its scripts and products target **out2/** and **qa2/**. The live **out/** files are
protected by a before/after SHA-256 inventory. Everything below describes pass 1.

## Deliverables

- `out/bg.png`, `out/full.png`, `out/glow.png`, and their `@2x` equivalents.
- Seventeen cropped RGBA `out/occ_<name>.png` sprites, each also at 2x.
- Forty-nine additional sprites under `out/slices/`, at both resolutions, for
  correct tile-level depth sorting with walkers.
- `out/manifest.json`: offsets, crop sizes, footprints, heights, baked signs,
  per-tile z-indices, exact marquee anchors and billboard aperture.
- `roxy.blend`: complete scene with packed font, camera, procedural materials,
  and lights. `build_scene.py` is the source of truth.
- `qa/`: calibration, independent Cycles full renders, compositing differences,
  alpha contact sheet, registration overlay, 4K details and validation reports.

The 1x scene is 1920 x 1080. The 2x scene is 3840 x 2160 with identical framing.
All manifest coordinates are in 1x stage pixels. For 2x resources, insert `@2x`
before `.png`, including the files in `slices/`. Their pixel dimensions and offsets
are exact doubles. In a 1920 CSS-pixel stage, retain the manifest's 1x CSS sizes.

## Reproduction

From the `standby` directory, using Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render.ps1 -Mode final -Samples 96
```

The execution-policy option applies only to this process; it does not change the
machine's script policy. It is needed with this machine's default script policy.
This calibrates, rebuilds, renders both resolutions, packages layers and runs the
registration/slice checks. It uses Blender's bundled Python, NumPy, and the Windows
System.Drawing PNG decoder; there are no pip installs. A small stdlib/NumPy PNG
decoder is also present. Native and stdlib decoding were compared on translucent
glass and agreed exactly, including fractional-alpha pixels.

For a quick visual iteration:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render.ps1 -Mode preview -Samples 24
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render.ps1 -Mode calibrate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render.ps1 -Mode package
```

The direct commands are:

```powershell
& .\tools\blender-5.2.3-windows-x64\blender.exe -b -P roxy3d/build_scene.py -- --mode final --samples 96
& .\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe roxy3d/package_layers.py
& .\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe roxy3d/qa/check_registration.py
```

`--mode layers --scale 1|2 --only full,bg,boxoffice` can rerender selected passes
while iterating. Use a complete final render before packaging a changed scene.
`--mode preview --tag preview_03` retains a separately named preview.

OptiX on the NVIDIA RTX 3050 Laptop 6 GB was used. The code tries OptiX, then CUDA,
then CPU, and retries on CPU after a GPU render error. Final passes use 96 maximum
samples, adaptive threshold 0.01 and denoising. Preview passes use a looser 0.025
threshold. The recorded peak observed GPU allocation was about 2.6 GB including
the desktop during the first full pass. Caches and temporary paths are redirected
inside `roxy3d/cache/`; the PowerShell wrapper restores its environment afterward.

## Camera calibration

World coordinates are `(x,y,z) = (u,-v,zpx / 73.4846922835)`. The orthographic
camera uses rotation `(60°,0°,45°)` and scale `22.627416998`. Its translation puts
the origin at pixel `(900,350)` without altering the page's projection.

`calibrate.py` renders isolated spheres, reads their PNG coverage and computes
alpha-weighted centroids. Pixel centres are at index + 0.5. The measured maximum
axis error was **0.015999 pixels**, well inside the required ±1 pixel.

| Tile point / z pixels | Expected pixel centre | Measured pixel centre | Error x, y pixels |
| --- | --- | --- | --- |
| 0, 0, 0 | 900, 350 | 900.004492, 350.012398 | +0.004492, +0.012398 |
| 13, 0, 0 | 1680, 740 | 1679.992251, 740.010348 | -0.007749, +0.010348 |
| 0, 9, 0 | 360, 620 | 360.015998, 619.999396 | +0.015998, -0.000604 |
| 13, 9, 0 | 1140, 1010 | 1140.005142, 1009.996932 | +0.005142, -0.003068 |
| 0, 0, 170 | 900, 180 | 899.994545, 180.001242 | -0.005455, +0.001242 |

The machine-readable results and marker image are `qa/calibration.json` and
`qa/calibration.png`. `qa/registration.png` outlines the actual movie marquee
interiors, wall-plane poster apertures and exact `(1296,40,576,324)` billboard slot.
Yellow crosses mark the calibration points; white crosses mark the staff and
gate/junction positions. Film/title graphics remain intentionally blank.

## Integration and alpha

1. Draw `bg` at the stage origin.
2. Prefer `manifest.render_layers`, which contains the 49 supplied depth pieces.
   Position each by its x/y/w/h and use its `z_index`, alongside the existing
   walker depth rule. Draw these files directly; do not additionally clip them.
3. Draw `glow` over the scene with `mix-blend-mode: screen` if desired.
4. Keep the DOM movie text, mapped poster images, emotes, rain and live status.
   Keep the green-screen element above the glow. Its aperture contains no baked
   text or important scenery.

The complete 17 prop sprites are included as requested. A single z-index for a
long partition or counter is insufficient for walkers along its length. The
additional depth pieces use the exact tile subdivision of the original
`addProp()`, with ownership derived from a Cycles world-position AOV. Their masks
are disjoint, so recombining all pieces restores each parent sprite byte for byte.
The reference `polygon_px` values in the manifest are informational only.

PNG uses **straight/unassociated RGBA**, ready for browser source-over blending.
Do not manually premultiply RGB. Fully transparent pixels have zero RGB. Partial
glass coverage and antialiased edges remain intact. The sprites have small padded
crops to retain clean antialiasing, with common 1x/2x bounds.

For the background pass, props are invisible only to camera rays: their shadows,
reflections and indirect lighting remain. For each sprite pass, all background
geometry remains as holdouts. This matters where a baked hanging sign is in front
of a counter or partition; the corresponding sprite has a deliberate transparent
cutout that reveals that sign from `bg.png`. Other props remain present for
lighting but are hidden to the camera. These sprites are authored for the fixed
layout and should not be moved to different positions.

`out/full.png` is the exact browser-style assembly of the delivered layers with
the optional screen-blend glow. The independently rendered physical scene is
preserved in `qa/cycles_full.png` and `qa/cycles_full@2x.png`. Independent denoising
and display-space alpha blending can produce small color differences, especially
in glass, when compared with Cycles' linear-light composition. The numerical
comparison is in `qa/layer_validation.json`, with a difference image amplified 4x.

## Baked signs and preserved dynamic content

Remove the duplicate DOM versions of **TICKETS**, **SNACK BAR and all three menu
prices**, and the **◀ 1-2 · 3-5 ▶** gate sign. **RESTROOM** is baked, but its
VACANT/OCCUPIED state must remain dynamic; place that state separately. **ROXY**
is baked into its prop. BUS 95, ORBIT, POPCORN, and the two original standee titles
MIDNIGHT/VOYAGER are also baked into their respective sprites.

The five camera-facing marquee interiors are 176 x 92 pixels, with bottom-centres
at `P(door,124)`. They contain no screen numbers, film names, ratings or attendance
counts. Poster inner areas remain 0.8 tiles wide at z pixels 23..128, on the exact
original wall planes. Preserve the page's DOM overlays for that dynamic content.

## Geometry and scope notes

No prop footprint or visible walkable area moved. The standee base and bus-stop
roof already extended beyond their sorting footprints in the original page;
those original extensions are preserved and listed as `geometry_footprint`.

Only invisible exterior padding extends the ground beyond the old u endpoints:
street/paving u -9..19 becomes -12..23. All added padding projects outside the
image (left of x=0 or below y=1080). This is recorded under `footprint_changes`.

Visual height changes, without footprint changes: bench 18 → 28 px for a padded
back; podium 46 → 49 px including its small lamp; bus stop 86 → 96 px including
its route plaque. The snack machine reaches the brief's specified 108 px. The
room walls, partitions, entrances, box-office heights and standee heights retain
their specified limits.

The scene uses a soft overcast procedural backdrop and a separate bloom/haze
layer rather than expensive volumetric fog. Animated rain is left to the page.
There are no people baked into the art. HTML/OBS integration and live walkers
were deliberately left to the integrating agent, as required by the brief.

## Visual review and timing

The references, calibration PNG, successive previews, complete renders, 4K
closeups, checkerboard sprite sheet and assembled output were opened for visual
inspection. Inspection caught and corrected wall cornices intersecting marquees,
raised lettering intersecting its backing, standee text placement, and sprite
occlusion over the baked hanging signs. The earlier comparison is retained as
`qa/layer_validation_before_holdout.json`.

The optimized procedural build takes about 0.8 seconds for 3,581 objects. The first
complete 96-sample render set took about six minutes: 1080p full/background about
26–27 seconds each, 4K full/background about 105 seconds each, and cropped sprites
about 2–7 seconds each. The corrected final run has per-pass measurements in
`qa/render_times.json`; its full log is `final_render_corrected.log`. Low-sample
full previews took about 16–17 seconds. Packaging and validation are separate from
these render times.

Final delivery verification passed for all **138 PNGs** (29,891,304 bytes), the
17 parent occluders, and 49 depth pieces at each resolution. The corrected run
spent **354.635 seconds in 38 render passes**, about 6 minutes 9 seconds including
build, scene updates, position-pass extraction and saving.

| Final check | 1920 x 1080 | 3840 x 2160 |
| --- | --- | --- |
| Parent reconstructed from its pieces: maximum channel error | 0 | 0 |
| Assembly versus independent Cycles: mean absolute RGB error, 0..255 | 0.2362 | 0.1719 |
| Assembly versus Cycles: 99th-percentile channel error | 5 | 3 |

The comparison excludes the optional added glow. The remaining differences are
chiefly independent denoising and glass compositing; they do not indicate a
projection offset. Every delivered PNG has a SHA-256 entry in
`qa/final_delivery.json`. Final calibration was rerun successfully through the
PowerShell wrapper and reproduced the values in the table above.
