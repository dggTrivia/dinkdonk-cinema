# Pass 3: vehicles and arrivals

This pass implements `BRIEF-4-vehicles.md`. The complete deliverable is `out3/`.
Both live folders, `out/` and `out2/`, are read-only inputs. All 141 non-manifest
assets from `out2/` are copied byte for byte, including the 5-second, 24 fps VP9
light loop, both scene resolutions, all whole props, and all depth slices.
The manifest remains layout 2 and adds vehicles, lanes, arrival stops, and the
fully lit background fallback. The page and shared files are not edited.

## Assets and placement

Four original procedural models are rendered from both directions, at 1x and
native 2x in Cycles, with 96 samples and denoising:

| Key | Model | Nominal length | Body width |
| --- | --- | ---: | ---: |
| `bus` | Cream/teal early-90s city bus, lit cabin, `95 ROXY` destination | 2.60 tiles | 0.78 tiles |
| `taxi` | Yellow boxy sedan, checker stripe, illuminated `TAXI` roof box | 1.72 tiles | 0.70 tiles |
| `sedan_a` | Burgundy sedan with rectangular sealed-beam lamps | 1.64 tiles | 0.68 tiles |
| `sedan_b` | Blue coupe/sedan with raised wedge-shaped pop-up headlights | 1.68 tiles | 0.69 tiles |

Each direction has a straight-alpha body PNG and a matching RGB light PNG on
black. The wet-road light pass is rendered with the actual headlights, tail
lamps and cabin lighting, with vehicle geometry casting shadows on a textured
wet receiver. Packaging adds small lens halos and a soft contact shadow. The
body includes wet clearcoat, fine surface variation, warm seats and glazing,
chrome, tire hubs, grille details, wipers, mirrors, and reflected pink/cyan
cinema lighting. Reverse-direction images are 180-degree rotations of the 3D
models, so lettering is not mirrored.

There are 48 vehicle PNGs: 16 closed bodies, 16 closed light layers, and 16
optional open-door body/light images for the bus and taxi. Every file has an
explicit manifest reference. Both resolutions are independently rendered;
the @2x files are not enlarged 1x sprites.

For a vehicle at `(u,v)`, place its top-left at:

```js
const x = 900 + (u - v) * 60 - vehicle.anchor[0];
const y = 350 + (u + v) * 30 - vehicle.anchor[1];
```

The anchor is the ground point under the vehicle's longitudinal centre, not
the centre of its visible silhouette. Body and light files, including the open
variant, share the same crop, dimensions, and anchor for that model/direction.
The common crop is tight to the union of the body and visible light reach;
transparent body margins are intentional and compress well.

Draw road lights with `mix-blend-mode: plus-lighter` below all bodies, walkers
and occluders. Draw bodies source-over, with the existing tile-depth convention
`1000 + round((u + v) * 100)`. Use manifest `w` and `h` as CSS dimensions for
either resolution. For a physical 2x canvas, double the placement, dimensions
and anchor. Near-lane vehicles go `+u` at `v=11.0`; far-lane vehicles go `-u`
at `v=12.0`.

## Arrivals and fallback

`door_open` replaces the closed body/light pair without changing placement.
Doors are on local `-v`, which is the curb side for near-lane `+u` traffic.
The near-lane doors are mostly hidden by the vehicle from this camera; the
reverse-direction views show the open doors clearly. These are two static
states, not a multi-frame door animation.

The manifest provides concrete stops:

- Bus centre `(0.16,11.0)` puts the physical door at `(1.20,10.60)`. The
  boarding/path point is `(1.20,10.75)`, as requested, beside the shelter.
- Taxi centre `(9.73,11.0)` puts the rear door at `(9.50,10.69)`. The boarding
  point is `(9.50,10.75)`, opposite the cinema entrance.

The small difference between door skin and boarding point reflects body width;
the lane centres and curb were not moved. `geometry_local_footprint` records
actual local model bounds, including mirror/bumper overhang and open doors.
`length_tiles` is the nominal traffic footprint, so allow spacing beyond it.
All inherited layout-2 coordinate deviations remain documented in the manifest.

`lit_bg.png` and `lit_bg@2x.png` are base plus lossless loop frame 60, with no
occluder props. Use them instead of base + video when video playback fails,
then draw normal occluders and traffic. Do not add the video over `lit_bg`.
Drawing the unchanged occluders over each fallback exactly reconstructs its
corresponding `full.png`. The copied `full.png` remains the static environment
reference; vehicles are demonstrated in `qa3/`, not parked permanently in it.

The new baked signs are `95 ROXY` on the bus front and rear, `95` and
`ROXY TRANSIT` on its sides, `TAXI` on the cab roof, and small `RXY 95` plates.
Existing building signs and billboard/marquee/poster apertures are unchanged.

## Reproduction

From the `standby` workspace, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass3.ps1 -Mode preview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass3.ps1 -Mode all -Samples 96
```

`-Mode package` reruns calibration, packaging, and verification using existing
final raw renders. The scripts target only `qa3/`, `out3/`, and the established
`roxy3d/cache/` folders. `roxy_vehicles.blend` is a bus example scene; the Python
builder is authoritative for all models and variants. No network or downloaded
assets are used. Arial Bold comes from the local Windows font installation.

Files responsible for this pass:

- `build_vehicles.py`: model geometry, materials, lights, camera, two render passes.
- `package_vehicles.py`: common crops, contact shadows/halos, fallback, manifest,
  lane composites and arrival checks.
- `calibrate_pass3.py`: ten rendered marker checks, including lane/arrival points.
- `verify_vehicles.py`: both live inventories and hashes, copied assets, 1x/2x
  dimensions, alpha, black light borders, shared anchors, door differences,
  fallback reconstruction, and final file inventory.
- `annotate_vehicles.ps1`: labels and guide marks in QA images only.

## Evidence and checks

`qa3/vehicles_check.png` contains all eight model/direction combinations at
three positions each, with projected lane lines and ground-anchor crosses.
It uses the actual out2 base + lossless loop frame + occluders. `scene_0.png`
through `scene_2.png` are the same compositions without guides.
`vehicle_contact_sheet.png` enlarges the 1x sprites for pixel-scale inspection.
`arrivals_check.png` compares the two door states at the actual stops.

Measured camera errors, render timings, and delivery size are recorded in
`qa3/calibration.json`, `qa3/render_vehicles.json`, and
`qa3/vehicle_validation.json`. The last report includes a SHA-256 inventory of
every delivered file and verifies all 281 live files against the snapshot in
`qa3/live_before.json`.

The delivered run passed all checks. Ten rendered camera markers had a maximum
axis error of **0.011163 px**. Crop/anchor reconstruction error is **0 px**;
integer raster placement in the lane contact sheet rounds by at most **0.5 px**.
Both lit-background reconstructions have **0 maximum channel error**. Final
rendering took **212.28 seconds** for 48 Cycles image passes on the RTX 3050
Laptop GPU using OptiX. The 48 vehicle PNGs total **2,769,324 bytes**; the
largest is **169,167 bytes**. The complete out3 folder contains **192 files**,
totalling **63,911,736 bytes** (including the inherited assets and two fallback
backgrounds). All 141 copied assets and all 281 live files match their hashes.

Visual review covered all three supplied references, initial isolated renders,
revised road lighting, the final eight-view contact sheet, native 2x model and
door views, all three lane positions, and the marked arrival comparison. The
light pools have no rectangular receiver edge, vehicle wheels meet the road,
and TAXI/95 ROXY lettering remains readable in the intended directions.

The supplied art and composites are verified offline. HTML integration,
traffic scheduling, stopping, passenger movement, and browser playback are
owned by the integrating agent and are outside this asset pass.
