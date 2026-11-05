# Pass 5: vehicle depth, lamp states and the lobby cat

Implements `BRIEF-6-pass5.md`. The complete pack is **out5/**: **322 files,
69,102,502 bytes**. All **207 non-manifest assets from out4** are copied byte
for byte. All **681 files** in the four live folders (`out/`, `out2/`, `out3/`,
`out4/`) match the initial SHA-256 inventory. All existing manifest keys and
values are preserved, except the pass number becoming 5; new contracts and
references are additive. Layout remains 2. No page or shared file was edited.

All requested work and all three optional additions are included: bus/taxi
indicators, cat stretch, and tyre spray. No new lettering or footprint changes
were introduced. The original camera, static environment, prop loops, ambient
video, fallback images, marquees, posters, billboard aperture, vehicle bodies,
normal lights, arrival stops and lane positions remain unchanged.

## Vehicle slices

There are **28 logical slices / 56 PNGs** at 1x and 2x, covering every vehicle,
both directions, and both closed and open-door variants. Each bus body has
three slices; each taxi and sedan body has two. Every longitudinal section is
at most one tile long, including model overhang rather than only nominal body
length. Surface-position AOVs from the actual 3D models determine ownership;
shadow-only pixels use their projected floor position.

The new `slices` array is inside each vehicle direction and each `door_open`.
It includes `file`, `file_2x`, `x`, `y`, `w`, `h`, `du`, plus the section's
`u_range` for inspection. `x/y` are relative to the inherited whole sprite's
top-left. `du` is signed **world-u** offset from the vehicle centre, including
for traffic facing -u; do not reverse it a second time.

```js
const variant = doorIsOpen ? vehicle.door_open : vehicle;
const left = 900 + (u - v) * 60 - vehicle.anchor[0];
const top  = 350 + (u + v) * 30 - vehicle.anchor[1];
for (const s of variant.slices) {
  // Draw this cropped image into the same z-sorted stack as walkers.
  const x = left + s.x;
  const y = top + s.y;
  const z = 1000 + Math.round((u + s.du + v) * 100);
}
```

The slices replace the body only; draw its light once, whole, underneath the
bodies and walkers. Use one common vehicle origin and retain logical 1x sizes
when using 2x files. Whole body files and the old centre-depth contract remain
available as a compatibility fallback.

All 12 body variants reconstruct **pixel-exactly** from their slices at both
resolutions. Each nontransparent pixel belongs to exactly one slice. The
[depth comparison](qa5/vehicle_depth_check.png) places two 52px proxy walkers
beside opposite bus ends. Centre sorting incorrectly draws the curbside front
walker on the bus and hides the rear walker; slice sorting corrects both in
both vehicle directions. This is a compositing fixture, not a live-page test.
[The colour ownership chart](qa5/vehicle_slices_check.png) covers closed and
open-door geometry for every model.

## Brake and indicator states

- **24 brake PNGs:** every model/direction at both resolutions, including the
  bus and taxi door-open variants.
- **16 indicator PNGs:** bus and taxi in both directions, closed/open, both
  resolutions. The amber lamps face the local curb side.

The fields are `light_brake`, `light_brake_2x`, and, where provided,
`light_indicator`, `light_indicator_2x`. These are complete replacement light
sprites with the **exact existing dimensions and anchor**. They retain the
normal headlights and cabin spill. Brake light adds brighter red tail halos
and ray-traced wet-road reflections; the indicator state adds amber halos and
wet-road spill. All have black backgrounds for additive blending.

Choose the relevant replacement instead of the normal `light`; adding both
would double the headlights. Blink indicators by alternating normal and
indicator states. For simultaneous brake and indicator, the additive increment
is `max(indicator - normal, 0)`; add that to brake and clamp to 255. This rule
is also recorded in `vehicle_lamp_variant_contract`.

The [lamp comparison](qa5/vehicle_lights_check.png) shows the normal, braking
and optional signalling states in the actual street environment. Added light
is nonnegative, retains a black border, and is checked at both resolutions.

## Cat

An original small ginger tabby has cream paws/chest, pointed ears, whiskers,
eyes and a striped coat. It is about 0.45 tiles long including its tail and
uses the exact camera and lighting from `roxy_pass4.blend`, rendered near the
arcade at `(10.75,7.75)`. `roxy_cat.blend` saves that scene with the cat. The
background geometry remains available for indirect light while invisible to
the camera in the RGBA character renders. A soft contact shadow is included.

| Manifest key | Frames | FPS | Duration | Sheet columns | Behavior |
| --- | ---: | ---: | ---: | ---: | --- |
| `sleep` | 48 | 16 | 3 s | 8 | Curled up, breathing and an ear twitch |
| `sit` | 48 | 16 | 3 s | 8 | Tail swish, blink and brief lick |
| `walk_plus_u` | 10 | 12 | 0.8333 s | 5 | Walk +u |
| `walk_minus_u` | 10 | 12 | 0.8333 s | 5 | Walk -u |
| `walk_plus_v` | 10 | 12 | 0.8333 s | 5 | Walk +v |
| `walk_minus_v` | 10 | 12 | 0.8333 s | 5 | Walk -v |
| `stretch` | 32 | 16 | 2 s | 8 | Standing to stretch to standing, one-shot |

The 14 cat PNG sheets total **1,019,928 bytes**. Every logical frame is
**64x64**, with ground anchor **[32,44]**, and straight alpha. The 2x frames
are rendered natively at 128x128; 1x frames use area averaging in premultiplied
alpha followed by conversion back to straight alpha. This keeps translucent
edges clean. Empty pixels have zero RGB and every cell has a clear border.

For a cat at `(u,v)`, position the frame at `P(u,v)-anchor` and sort at
`1000 + Math.round((u+v)*100)`. Source frame is
`Math.floor(seconds*fps) % frames`; its cell is
`[frame % columns, Math.floor(frame / columns)]`. Clamp at `frames-1` for the
one-shot. On 2x sheets, double the source cell dimensions, retaining the 1x
display size and anchor. `cat_contract.walk_mapping` maps the four floor
directions to their animation keys.

All walks advance **0.32 tiles per cycle**, so normal playback at 12fps means
0.384 tiles/second. The stance feet travel backward at that same rate within
the stationary sprite. The page supplies the translation; none is baked into
the sheets. Each direction is a true 3D rotation rather than a mirrored image.

All six loops have independently rendered endpoint frames identical to their
first frames. Their last-to-first changes are below their largest ordinary
adjacent-frame change. The optional stretch starts and ends in the same
standing pose. See [cat poses](qa5/cat_contact_sheet.png),
[native-size scene placements](qa5/cats_in_scene.png), and
[15-second preview](qa5/cat_preview.mp4). The scene placement image intentionally
shows several cats to inspect scale and depth, including one partly behind
the arcade; the pack does not bake any cats into the static environment.

## Tyre spray

Both `+u` and `-u` have 12-frame, 24fps, **0.5-second one-shots** in
`tyre_spray`. Each 1x cell is 96x56 with anchor `[48,31]`; the sheets have six
columns and two rows. The four files total **38,770 bytes**. They are additive
RGB images on black, with cool highlights from deterministic ballistic water
droplets. The first and last frames are black.

Attach the anchor to the wheel's ground contact, choose the travel direction,
and add under vehicle bodies and walkers. Trigger while moving on wet road;
do not loop a single emission indefinitely. The ground-contact attachment and
several times are shown in [spray QA](qa5/tyre_spray_check.png).

## Verification and reproduction

[final_validation.json](qa5/final_validation.json) contains the delivery
inventory and hashes, live preservation proof, inherited-contract checks,
slice reconstruction, lamp comparisons, alpha/cell checks and calibration.
Ten independently rendered calibration markers, including lane and arrival
anchors, have maximum axis error **0.011163 px** against the 1px tolerance.

The reference art, cat previews, final poses, slice ownership, both depth
comparisons, all lamp directions, native-size cat placements and spray frames
were visually inspected. The preview MP4 is encoded with bundled FFmpeg and
decoded again to verify its 1280x720 dimensions, 360 frames and 24fps. Decoded
preview frames were inspected. HTML/OBS integration and interactive playback
in the live page are outside this asset pass and were not performed.

From `standby`, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass5.ps1 -Mode all -Samples 96
```

`-Mode preview` renders enlarged cat pose previews. `-Mode package` reuses
the existing render sources in `qa5/` and rebuilds the output pack, manifest,
visual QA, MP4 and validation. The wrapper retains the original live inventory,
redirects temporary/OptiX/CUDA caches into `roxy3d/cache/`, and restores the
calling environment afterward. Its syntax was checked, and every component
stage was executed successfully.

| Production stage | Measured time |
| --- | ---: |
| Vehicle AOVs and normal/brake/indicator sources, both scales | 427.4 s |
| Vehicle slices and light packaging | 33.1 s |
| Cat final frames and independent endpoints, native 2x | 273.1 s |
| Preview MP4 encode plus decoded checks | See `qa5/preview_metadata.json` (about 9 s) |

Vehicle lights use Cycles OptiX, 96 samples and denoising. Ownership maps use
12 CPU samples with no denoising. Cat frames use 48 CPU samples and denoising
inside the existing lighting scene. These timings exclude previews, modeling
iterations and extra QA. The main scripts are `render_vehicle_pass5.py`,
`package_vehicle_pass5.py`, `render_cat_pass5.py`, `package_cat_pass5.py`,
`qa_pass5.py`, `encode_preview_pass5.py`, `calibrate_pass5.py` and
`verify_pass5.py`. All changes are inside `roxy3d/`; no network assets or
additional software were required.
