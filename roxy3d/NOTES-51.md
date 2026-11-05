# Brief 51 - rendered umbrella rain, vehicle roof rain and continuous tyre spray

Delivered a draft-only additive asset set in `out10e/`, plus the single owner image `qa10/draft20-rain-umb-veh-tyre.png` (1280 x 720). No live integration. All writes are within `roxy3d/`; the staging assets and working files are within `out10e/`. No cloud job or network service was used.

## What was rendered

- **Red open umbrella:** a complete RGBA replacement loop with the exact live 88 x 80 frame and [44,68] anchor. The original eight fabric gores, rib seams, handle and red palette remain. Added a thin Fresnel water film, stable wet beading, small periodic impact crowns, short nearly vertical incoming drops, and gravity-driven drops from all eight rib tips. Tip drops fade before exceeding the existing sprite canvas.
- **Taxi +u:** a black-background additive loop aligned to the entire live body sprite. Separate exposed impact zones cover the roof, bonnet and boot; the current compact roof-sign mount shelters its footprint. The film adds reflection over the already-wet production paint.
- **Bus +u roof:** a matching whole-body additive loop. Crowns and beads land on the roof and the actual raised ventilation pod/grilles, at their respective heights. This bus has no separate car-style bonnet or boot.
- **Bus +u and sedan A +u driving spray:** continuous emitters at all four wheel-contact regions, with more droplets, higher ejection speeds and larger mist volumes at the rear axle. Water moves rearwards relative to +u travel, spreads sideways and falls under gravity. Short glossy wet tracks follow the rear tyres. Far-side spray is occluded by the actual vehicle geometry; four emitters does not imply four equally exposed plumes in the camera. Near-wheel mist remains low, with red tail-light and warm street-light colour.

All five loops have **24 unique frames at 24 fps, lasting 1 second**, packed row-major as **4 columns x 6 rows**. Frame 24 is rendered only for the endpoint check and is not duplicated into the atlas. Phase offsets and particle lifetimes use a periodic deterministic schedule. These are renderer-built procedural water effects, not in-page drawn splashes or a fluid-simulation bake.

## Lighting, rendering and registration

Local **NVIDIA GeForce RTX 3050 6GB Laptop GPU**, **Cycles / OptiX**, with CPU-render fallback disabled. Maximum 128 samples, minimum 64, adaptive threshold .012, fixed seed 5101, OptiX denoising. Camera grid 3840 x 2160; only the individual sprite rectangles are rendered. Blackman-Harris width 2.5, AgX / Medium High Contrast, exposure +0.25. The 1x files use a scene-linear premultiplied RGBA 2x2 mean before display conversion; @2x files use the native render grid.

Vehicle geometry comes from copies of the current local production builders. The route-05 bus artwork/model recipe is reused. The current live taxi sprite is byte-identical to the compact-sign `out10d` sprite. The original source files and blends are opened read-only or copied into `out10e/_work/studio/`; none is saved over.

The draft-15 vehicle studio remains at overhead 0 W, warm reflection 8 W, cyan reflection 11.2 W, warm street fill 6.8 W, world strength .015. Vehicle lamps retain their original positions and powers. Body materials become black to camera rays for effect isolation while remaining available to secondary rays and shadows. The new vehicle sheets contain the water contribution rather than another vehicle body.

For tyre spray only, three **existing production street point lamps** are also present at the reference vehicle position (u=6, v=11): `Warm street lamp pool` (65 W), `P8 far sidewalk warm pool.001` (30 W) and `.002` (30 W). Their exact positions, colours and radii are read from the current local `cloud/bundle/scene.blend`; `out10e/_work/street-lights.json` records them. This is local scene-file access, not cloud execution. The extra lamps illuminate only the isolated water render; the delivered vehicle bodies remain the live draft-15 sprites.

The umbrella uses the original `roxy_pass6.blend` scene lights and the original umbrella geometry placement. Its replacement loop adds wet material response. Water has IOR 1.333 and no emission. Crowns use a transmissive dielectric with an effective scattering component for unresolved aerated droplets (transmission .82 on the umbrella, .50 on vehicle tops); atomized tyre droplets use a stronger effective scattering lobe. Mist is actual non-emissive volume scattering in closed meshes, with noise and density tapering to zero at each puff boundary. This is an artistic small-sprite approximation of aerated water, not a calibrated drop-size or spray-density measurement.

Projection remains `x = 900 + 60(u-v)`, `y = 350 + 30(u+v) - z_px`. Roof sheets retain the exact whole-body sizes/anchors. Spray sheets use smaller dedicated canvases with sufficient upper margin for far-wheel droplets; their anchors are still the same vehicle ground centre. Dimensions and sampling metadata are in `out10e/manifest.json`.

## Sheet sizes and memory

Both 1x and optional @2x PNGs are provided. Frame dimensions and anchors below are logical pixels; multiply both by 2 when sampling @2x. File sizes are exact bytes. VRAM assumes decoded RGBA8, even for RGB PNGs, without mipmaps.

| Sheet | Frame | Anchor | 1x atlas | PNG bytes, 1x / @2x | VRAM MiB, 1x / @2x |
|---|---:|---:|---:|---:|---:|
| `umbrella_red.png` | 88 x 80 | [44, 68] | 352 x 480 | 113,038 / 359,490 | 0.64 / 2.58 |
| `taxi_roof_plus.png` | 354 x 185 | [119, 63] | 1416 x 1110 | 61,327 / 196,776 | 6.00 / 23.98 |
| `bus_roof_plus.png` | 433 x 261 | [164, 118] | 1732 x 1566 | 59,104 / 184,653 | 10.35 / 41.39 |
| `bus_spray_plus.png` | 300 x 192 | [176, 104] | 1200 x 1152 | 48,169 / 149,993 | 5.27 / 21.09 |
| `sedan_a_spray_plus.png` | 246 x 166 | [148, 92] | 984 x 996 | 80,591 / 256,355 | 3.74 / 14.95 |

The ten PNGs total **1,509,496 bytes (1.44 MiB)** on disk. Loading all five 1x sheets uses approximately **26.00 MiB** of texture memory; all five @2x sheets use **104.00 MiB**. Loading both resolutions uses **130.00 MiB**, or about **173.33 MiB** with a full mip chain. Browser decode buffers, upload staging and compositor copies are additional. Prefer 1x at native page scale and load only one resolution per effect. Every atlas side is <=4096 pixels; the largest @2x atlas is the bus roof at 3464 x 3132. `_work/` contains internal EXRs, temporary frames, source copies and diagnostics and is not a web payload.

## Use and production plan

1. **Umbrella:** draw frame `floor(elapsedSeconds*24) % 24` with source-over at the existing open-sprite position and [44,68] anchor. The fold sheets are unchanged. Production would render the remaining blue, yellow and black wet loops and use per-character phase offsets.
2. **Vehicle roofs:** draw the black-background RGB sheet with **sRGB plus-lighter** over the current body at the identical anchor. The film is reflection-only, consistent with the requested additive contract; it cannot subtract/darken the existing paint. For production, partition the water into the existing local-u depth bands: taxi boundaries -0.8943 / 0.00185 / 0.898; bus boundaries -1.357 / -0.424667 / 0.507667 / 1.44. Tag impacts by their landing surface and local u; carry that ownership through the crown/drop lifetime. Capture coverage/ownership mattes with the combined water beauty, partition pixels once so slices sum exactly to the unsliced overlay, and crop at each existing slice's x/y offset. Do not split by screen x. Expand an overlay crop with corresponding offset metadata if airborne water exceeds an existing body-slice rectangle. Preserve the body's slice registration, u ranges and draw depth; add each water slice immediately above its matching body slice so page foreground occluders still cover it. Validate zero double-addition and exact reconstruction before publishing.
3. **Driving spray:** position at the vehicle ground centre using the supplied dedicated anchor. Add with plus-lighter only while moving. Suggested draft opacity is `smoothstep(0.03, 0.40, abs(speed_tiles_per_second))`; the illustrated plume length corresponds roughly to 1.8 tiles/s. Crossfade over about 0.15 seconds near stops, keeping phase continuous while visible. For a broad speed range, render slow/fast plume variants rather than scaling the entire sprite. For production, split by wheel/emitter and road-level wake ownership, then sort against vehicle and page depth; the current sheet already includes vehicle self-occlusion but has no page-foreground slices.
4. Render the remaining directions, sedan B and required door/lamp states only after draft approval. Keep the same camera grid, shared phase conventions and anchors. Trim transparent/black margins per production slice to reduce memory. Street lighting here is baked at one representative lane position: moving through differently lit parts of the scene needs lighting-basis variants or location-dependent crossfades. Full street-position, weather-intensity, speed-fade and browser integration tests remain production work.

## Owner image

`qa10/draft20-rain-umb-veh-tyre.png` contains exactly three rows, each **before | after frame 0 | after frame 8 | after frame 16**. Umbrella is displayed at 3x, taxi roof at native 2x, and bus driving at 1x. Small labels show the phases 0.000 / 0.333 / 0.667 s. The taxi row crops around the upper body; the bus row shows the new roof loop and wheel spray together. Before panels use current `out10` sprites. Neutral dark panels keep the changes readable; this is an asset comparison, not a screenshot of integrated page playback. Sampling/crop records are in `_work/composition.json`.

## Measured render times and validation

Times below are final capture wall times for each asset, including its 25th endpoint-check capture. They exclude scene setup, image conversion, atlas packing and exploratory/discarded renders. There is no cloud-time estimate or claimed browser performance measurement.

| Final asset | Capture seconds |
|---|---:|
| umbrella_red | 95.58 |
| taxi_roof_plus | 8.71 |
| bus_roof_plus | 14.44 |
| bus_spray_plus | 119.83 |
| sedan_a_spray_plus | 130.79 |
| **Total** | **369.34** |

Validation in `out10e/validation.json` checks every delivered resolution:

- Exactly 24 distinct frames per sheet, at the declared dimensions and anchors.
- Phase 24 and phase 0 have **identical geometry hashes** for all five loops, including all water mesh coordinates and topology. Repeated fixed-seed GPU renders are not entirely bit-identical: endpoint mean absolute channel error is below **.004 / 255** for every delivered resolution. The largest individual difference is **17 / 255** in sparse @2x sedan mist denoising speckles (6 / 255 at 1x); the other passes peak at 0 or 1. Endpoint 99.9th-percentile channel error is <=1 in every case. The raw values are preserved in the validation report, rather than substituting a duplicate first frame for this check.
- Every frame has zero effect coverage at the sprite boundary, with no clipped umbrella alpha or nonblack additive edge.
- The 23->0 step is within the measured ordinary frame-step range gate; the largest seam-to-median ratio across all assets/resolutions is **1.519**. This numeric test complements visual review; it is not browser playback verification.
- Atlas dimensions stay within 4096; PNG payload sizes, decoded-memory estimates and SHA-256 checksums are recorded.
- The final owner image, umbrella, both roof passes and both spray sheets were visually inspected, including the low native-size mist and the softened volume boundaries.
- **6,522 pre-existing pack/page hashes unchanged**, covering every existing `out*` pack and `standby/roxy.html`. The final protection receipt is `_work/protected-after.json`.

The deliverable is the ten root-level PNGs plus `manifest.json`, `validation.json` and `checksums.json` in `out10e/`, this note, and the one owner image. Reproduction scripts and intermediate evidence are under `out10e/_work/`. These files are a reviewable draft, with no modification to the live page, live pack, other pack or cloud deployment.

STATUS: COMPLETE - Brief 51 draft loops, one owner image and notes delivered; live packs/page unchanged; stopped.
