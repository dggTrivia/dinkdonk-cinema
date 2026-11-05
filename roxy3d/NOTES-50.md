# Brief 50 — splash-mist inputs and one baked sample

Delivered `out10mist/` and the single owner image `qa10/draft17-mist-baked.png` (1280 × 720). Samples only. All writes stayed under `roxy3d/`; no cloud work or page integration.

## Source and registration

The scene lineage begins with `build_pass10_final.py`; the capture uses the current packed production `cloud/bundle/scene.blend`, which contains approved Draft 13 plus the later Screen 2 receiver/material repair and orphan bus-plate removal. Re-running the historical builder would revert those changes. The saved source was opened read-only and never saved over.

- Source SHA-256: `0fa1c86fb297079b0b0b1944cad5d9ae08f6a8babaf2bd558c9a43d35417ef24`.
- Exact saved orthographic camera, unchanged transform/framing; ortho scale `22.627416610717773`.
- Projection: `x = 900 + 60(u-v)`, `y = 350 + 30(u+v) - z_px`; world position `(u,-v,z_px/73.4846922835)`.
- Data captures: native **3840 × 2160**, Blackman–Harris width **2.5**, phase 0. The **1920 × 1080** files use the production scene-linear **2×2 area mean before display conversion**, not a separately rendered camera or resized display PNG.
- Grey masks are scalar data, with no view transform or gamma applied. The RGB light pass is converted through the scene’s AgX / Medium High Contrast, exposure +0.25, after linear reduction.

## Pass construction and values

| Pass | Construction | Values |
|---|---|---|
| `catch` | Local Cycles GPU render with an exactly overhead, zero-angle sun; energy π; black world; zero indirect bounces. Eligible surfaces use white Lambert diffuse, other geometry black. This gives `max(0, normal.z) × overhead visibility`; blockers still occlude. | 8-bit grey, 0–255. 0 means no rain; 255 means a horizontal, fully exposed catch surface. Antialiasing carries partial edge coverage. |
| `rim` | Derived from the same capture’s world-position and normal AOVs. Checks the upper side of a persistent geometric drop within 6 native pixels (about 3 pixels at 1080p), with farther checks at 10/14 native pixels to reject narrow joints. Corrects for the local surface slope. Internal sidewalk slab joints are suppressed; the outer curb remains. | 8-bit grey, 0–255; weighted by catch, always a subset of catch. Width is approximate at filtered/curved edges. |
| `light` | Separate white-matte night render on eligible opaque receivers. Retains the scene lights, emitter materials, positions, colours, strengths and receiver linking. Multiplies scene-linear RGB by catch, then applies the production view transform without glare. Explicitly black wherever the delivered catch byte is 0. | 8-bit RGB display colour; measured ranges are listed below. This is white-matte lit colour, not calibrated lux or an untonemapped HDR irradiance map. Catch weighting is already included. |
| `height` | World Z from the same camera AOV, expressed as projected vertical distance above the actual street plane (z_px **-0.05**). Normalized by the tallest roof at z_px **425.00**, a **425.05 px** vertical difference. | 8-bit grey, 0–255. Street = 0; tallest roof = 255; taller equipment clamps to 255. Black outside delivered catch support. |

The static passes remove precipitation geometry, surface beads, crowns, drips/pours, steam, hidden weather helpers and parked/moving props. Glass looking into interiors is excluded. The cutaway cinema and annex are excluded by object identity and world-space bounds even where their real ceiling is absent from the model. Actual roofs/awnings/shelter geometry casts the overhead exposure shadow, keeping sheltered floors and undersides dry. No animation sequence was rendered.

## Physical sample and owner image

`out10mist/mist-baked.png` is one **1920 × 1080**, **48-sample**, OptiX-denoised draft exposure of phase 0. A matched before exposure uses the same camera, phase, seed, original materials and light rig. The only 3D addition is physical non-emissive water spray:
- **90,599** adaptive cells tessellated onto the visible catch surfaces, grouped into **15** receiver-link signatures. Marginal antialiased/occluded cells are rejected rather than bridging a covered area.
- A noisy white-grey scattering medium in closed, outward-facing meshes, roughly **3.5–12 cm** above the surface in scene units; volume scatter only, no emission. Existing lamps and neon illuminate it.
- **16,275** irregular water crown rims and **48,825** broken dielectric droplets, reaching at most **15 cm** above the surface, IOR 1.333. This is a deterministic frozen sample, not a simulated or exported particle animation.
- The source’s existing wet materials, reflections and phase remain. The unchanged live `out10/rain_fg.webm` frame 0 is decoded locally and added with the production plus-lighter rule to **both** before and after; it is not included in the static data passes.

The owner image is before | after with small labels only. Both panels use the identical logical crop `[240, 0, 1024, 1080]`, displayed as 640 × 675 within the 1280 × 720 canvas. It includes the street, bus stop, neighbouring lit sign tops, cinema roof edge and left marquee light. Only this one owner image is delivered.

## Files

| File | Dimensions | Format |
|---|---|---|
| `out10mist/catch.png`, `rim.png`, `height.png` | 1920 × 1080 | 8-bit grey PNG |
| `out10mist/catch@2x.png`, `rim@2x.png`, `height@2x.png` | 3840 × 2160 | 8-bit grey PNG |
| `out10mist/light.png` | 1920 × 1080 | 8-bit RGB PNG |
| `out10mist/light@2x.png` | 3840 × 2160 | 8-bit RGB PNG |
| `out10mist/mist-baked.png` | 1920 × 1080 | Baked sample PNG |
| `qa10/draft17-mist-baked.png` | 1280 × 720 | Single owner comparison |
| `NOTES-50.md` | — | This delivery record |

Scripts, raw linear EXRs, position/normal AOVs, decoded rain frame, protected hashes, measurements and the reproducible sample scene `mist-sample-final.blend` are internal working files under `cache/brief50/`. They are not live-pack assets.

## Measured render times

Local NVIDIA GeForce RTX 3050 6GB Laptop GPU, Cycles OptiX; CPU rendering fallback disabled. Times below are capture wall times, excluding setup, image conversion, verification and reading files.

| Capture | Samples | Seconds |
|---|---:|---:|
| Final native catch + position/normal/index AOVs | 16 | 11.50 |
| Final native night white-matte light | 32 | 51.54 |
| Matched before exposure | 48 | 33.30 |
| Final physical mist exposure | 48 | 96.38 |

There was one earlier draft bake of the same phase (**322.70 s**) which revealed inward volume-face winding during visual review. Its normals were corrected and the delivered image rerendered. Earlier data captures (12.29 s catch, 51.18 s light) were also replaced after removing residual surface beads from the static inputs. No alternate loop phase or video was rendered.

## Verification and limits

- **6,516 protected file hashes unchanged**, covering every pre-existing `out*` pack, `standby/roxy.html`, and the checked draft/production source blends.
- Correct PNG dimensions, bit depths and grey/RGB colour types verified. Scalar 1× outputs exactly match the stored native floating-point 2×2 reduction plus declared byte/support quantization. Rim is a catch subset; light and height are zero wherever the delivered catch is zero.
- Independent upward-ray audit: **2048/2048** fully exposed samples clear of physical overhead geometry. The source’s non-shadowing standing-water overlays are excluded as blockers; an initial audit counted three such overlay intersections. Filtered position AOVs mix surfaces at silhouettes, so partial boundary coverage is not evidence of a separate interior receiver.
- The camera-space masks, full sample and owner comparison were visually inspected. This is a static draft and map handoff; it does not validate page animation, temporal behaviour, splash lifetime or moving-vehicle coverage.
- **Optional vehicle passes skipped.** The vehicles are separate sprite rigs with per-direction crops and anchors; producing correctly registered roofs/bonnets-only passes for all closed bodies was not a trivial extension of the static scene capture. No vehicle mist files are present.
- The baked volume is generated for the camera-visible catch regions. Tiny rejected boundary cells and unseen surfaces are not claimed as a complete fluid simulation. The rim is a camera-space geometric-drop estimate, not an independently modelled volumetric edge field.

Measured delivered light ranges: `out10mist/light.png` 0–255, `out10mist/light@2x.png` 0–255.

STATUS: COMPLETE — static 1×/@2× inputs, one baked mist sample and one owner comparison delivered; optional vehicle passes skipped; protected packs/page unchanged; stopped.
