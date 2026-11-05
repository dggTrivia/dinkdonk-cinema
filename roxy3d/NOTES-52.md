# Brief 52 - stronger rendered rain, draft 21

Delivered `out10f/`, the single owner image `qa10/draft21-rain-stronger.png` (1280 x 720), and this note. Local NVIDIA RTX 3050 6GB Laptop GPU / Cycles OptiX only. No cloud job, network rendering, live integration, or changes to existing packs/page.

## Changes from draft 20

- **Umbrella:** kept the red production fabric, original ribs/handle, 88 x 80 frame and [44,68] anchor. Replaced many tiny complete crowns and persistent bead noise with **20 scheduled resolved impacts/s**, **2-4 frames** each: two broken highlight segments, occasional three-part clusters, about 1 px lift and occasional 2 px ejection. One in three hits has a preceding near-vertical 3-5 px incoming streak. Four near-side rib tips each release **1.5 drops/s**, irregularly staggered, with 1 px width, 2-3 px vertical footprint and about 6-10 px fall. The runoff contribution is capped at +35 display-luminance levels. Wet film is capped at +8; the red canopy remains legible between events.
- **Taxi:** **22 scheduled hits/s** = roof **10**, bonnet **7**, boot **5**. Events last **2-4 frames**, predominantly 1-2 px broken highlights with occasional 3 px clusters. Rejection sampling avoids the sign's sheltered footprint. The added film is multiplied by .40, with a +20 ceiling for the unusually bright reflected sign (the sign-reflection exception to the ordinary +3-8 film target). Across the recorded sign-base rectangle, the final added band/reflection is **66.4% weaker** than draft 20. The production sign face, lamps, mount, body and illumination are unchanged.
- **Bus top:** **38 scheduled impacts/s**, **2-4 frames**, on the actual roof and raised HVAC/grille heights. No added bonnet or boot on the bus. The original isolated mirror-film pass quantized mostly to black; its static GPU film capture is exposed 4 EV above the ordinary capture and then compressed to a maximum +8-level contribution. This is selective grading of the same reflected light, not an added lamp or emitting water.
- **Spray:** **48 droplet releases/s per rear wheel**, **20/s per front wheel**, with **3-6-frame** ballistic flights. Rendered contact fringes attach the fans to the tyres; short velocity-aligned streaks and separate, irregular overlapping volume puffs give the airborne structure. Approximate designed trajectories at 1x: **bus rear 27-43 px long / 4-7.5 px high**, **sedan rear 19-29 / 3-5.3 px**, **front 8-13 / 2-3 px**. Rear volumes emit 22 puffs per two seconds versus 14 front (1.57x); the longer rear droplet fan has 2.4x the front release rate. Natural vehicle occlusion is retained. The colour grade preserves restrained street/tail-light accents while reducing saturated red; combined mist/droplets are capped at +45 luminance levels.
- **Wake:** two independently deposited, broken tracks from the rear tyres, now delivered as separate road-layer sheets. Bus life **.40 s**, length **48 px**, width about **3.2 px**; sedan life **.32 s**, length **39 px**, width about **2.4 px** at the 1.8 tiles/s reference speed. A rougher, non-emissive wet-track material makes the tracks visible at this camera/light angle. The body naturally hides the near portions of the far track; two emitted tracks do not mean two equally exposed full lengths.
- **Timing:** every delivered sheet now has **48 unique frames / 2 s / 24 fps**, with stratified irregular release schedules and no duplicate terminal frame. Frame 48 is independently rendered for closure testing. Per-object phase offsets remain appropriate; never reset an active loop every second.

The numbers above are emitter/trajectory settings. They do not assert that every emitted event is equally visible after occlusion, subpixel sampling, or background rain. The following measurements are from the actual delivered images.

## Measured appearance

Each pass uses a fixed contrast curve for its entire sequence and both resolutions. There is no per-frame normalization. Values below are display-referred luminance increments (0-255), before composition clipping; p95 is over pixels with a contribution above 1. Soft edges are intentionally dimmer than the resolved cores.

| Rendered component | Frame p95 range | Maximum |
|---|---:|---:|
| umbrella_red / hits | 32.6-42.9 | 45.1 |
| umbrella_red / film | 8.0-8.0 | 8.0 |
| taxi_roof_plus / hits | 22.5-44.4 | 46.9 |
| taxi_roof_plus / film | 20.0-20.0 | 20.0 |
| bus_roof_plus / hits | 30.8-42.8 | 44.2 |
| bus_roof_plus / film | 6.9-6.9 | 7.6 |
| bus_spray_plus / drops | 33.8-37.1 | 40.2 |
| bus_spray_plus / mist | 13.5-15.4 | 16.1 |
| bus_spray_plus / wake | 11.7-13.2 | 13.9 |
| sedan_a_spray_plus / drops | 31.8-39.8 | 42.3 |
| sedan_a_spray_plus / mist | 10.9-15.8 | 16.1 |
| sedan_a_spray_plus / wake | 11.7-13.8 | 15.0 |

The impact curves target +40-level cores, cap below +58, and retain darker gaps. Rear mist targets +15 with a +21 soft cap; front mist is 70% of that. Combined rear/front droplet cores are capped at +45/+28, giving a measured peak hierarchy of 1.60x on the bus and 1.60x on the sedan. The wake targets +13 reflection fragments with a +20 soft cap. The useful fade regions of both effects are lower. The supplied source targets (+25-45 cores, +10-18 useful mist, +5-10 wake with brighter fragments) are used as grading targets rather than uniform brightness across every antialiased pixel.

Temporal contrast is measured as each pixel's maximum minus minimum luminance through the entire loop, using premultiplied RGB for the umbrella so hidden RGB in transparent pixels cannot inflate the result. The table's p90 excludes spans <=2, so static body/film brightness cannot masquerade as stronger motion. Draft 20 has 24 phases and draft 21 has 48; pixel counts cover each full delivered loop, not a per-second event count.

| Asset | Draft 20 dynamic-span p90 | Draft 21 dynamic-span p90 | Pixels varying >25, old / new |
|---|---:|---:|---:|
| umbrella_red | 17.0 | 40.0 | 59 / 270 |
| taxi_roof_plus | 22.7 | 38.1 | 111 / 156 |
| bus_roof_plus | 18.7 | 38.3 | 26 / 257 |
| bus_spray_plus | 19.2 | 39.8 | 38 / 178 |
| sedan_a_spray_plus | 30.3 | 41.1 | 322 / 111 |

Full per-frame figures, the sign-base measurement rectangle, and image-integrated rear/front measurements are in `_work/grade.json` and `_work/appearance-measurements.json`. Image-integrated ratios include occlusion and the larger plume footprint; they are not per-pixel brightness ratios.

## Sizes, anchors and VRAM

All sheets are 8 columns x 6 rows, row-major. `index = floor(seconds * 24 + phaseOffset) % 48`. Black-background vehicle sheets use sRGB `plus-lighter`; umbrella uses source-over. Optional @2x sheets have twice the frame dimensions, anchor and crop offset. All atlas sides are <=4096 px.

| Sheet | Cropped frame, 1x | Cropped anchor | Crop offset from original canvas | PNG bytes 1x / 2x | RGBA8 MiB 1x / 2x |
|---|---:|---:|---:|---:|---:|
| `umbrella_red` | 88 x 80 | [44, 68] | [0, 0] | 57,822 / 179,513 | 1.29 / 5.16 |
| `taxi_roof_plus` | 136 x 64 | [70, 57] | [49, 6] | 16,830 / 49,454 | 1.59 / 6.38 |
| `bus_roof_plus` | 196 x 102 | [98, 116] | [66, 2] | 43,999 / 120,833 | 3.66 / 14.64 |
| `bus_spray_plus` | 144 x 75 | [117, 35] | [59, 69] | 20,496 / 59,660 | 1.98 / 7.91 |
| `bus_wake_plus` | 50 x 28 | [123, 37] | [53, 67] | 8,684 / 24,629 | 0.26 / 1.03 |
| `sedan_a_spray_plus` | 96 x 51 | [83, 22] | [65, 70] | 16,272 / 46,051 | 0.90 / 3.59 |
| `sedan_a_wake_plus` | 41 x 24 | [93, 25] | [55, 67] | 6,590 / 19,521 | 0.18 / 0.72 |

**Registration:** the physical ground/grip anchor is unchanged. The umbrella retains the exact original numeric anchor. Vehicle black margins are removed with a fixed all-frame/all-resolution union crop: `croppedAnchor = sourceAnchor - cropOffset`. Draw at `groundPixel - croppedAnchor`, equivalently `groundPixel - sourceAnchor + cropOffset`. `source_canvas`, `source_anchor`, `source_native_rect`, `crop_offset` and the adjusted `native_rect` are recorded. This is the necessary offset accounting for the requested margin cropping; no model, camera, lane scale or world anchor moved.

The **14 PNGs total 670,354 bytes (0.64 MiB)**. All seven 1x atlases occupy **9.85 MiB** decoded RGBA8; all @2x atlases occupy **39.42 MiB**. Draft 20's five sheets used 26.00 / 104.00 MiB. Loading both resolutions would use 49.27 MiB, before mipmaps (approximately x4/3), browser decode/upload buffers or compositor copies. Load one resolution per asset. `_work/` contains source copies, EXRs, frames, scripts and QA; it is not a web payload.

## Wake movement and page integration contract

At the reference speed, the supplied wake already scrolls backward in the vehicle's local coordinates: `localU = rearAxleU - .03 - 1.8 * ageSeconds`. The parent advances at `+1.8 * ageSeconds`, so each patch remains fixed in world space while fading over .40/.32 s. This fixes the rigid-following wake issue. Draw the dedicated wake sheet at road depth, below the body, then the body and the self-occluded airborne spray.

For changing speed, retain world-space rear-contact samples (or a road-space decal buffer), advect the wake UV/sample position by the measured travelled distance and expire each sample at the stated lifetime. Do not simply drag an unchanged patch behind the body. A different speed needs matching trajectory/scroll variants or road-stamped samples; the reference atlas alone is not physically exact during acceleration. Use `smoothstep(.15, 1.8, abs(speedTilesPerSecond))` for the draft spray opacity, with about .15 s stop/start crossfade and continuous phase. Full strength is no longer reached at the old .40 tiles/s crawling threshold.

Production depth slicing remains the draft-20 contract: partition roof events by landing-surface local-u ownership into the existing body slice u-ranges; carry that ownership through each event's lifetime, use matching coverage mattes so slices sum to the unsliced overlay once, and apply the crop offsets above. Draw each roof slice immediately above its corresponding body slice. Split airborne spray by emitter for scene-foreground sorting. Lighting remains baked at the original (u=6,v=11) reference; moving through other light pools requires lighting-basis/location controls. Other umbrella colours, directions and vehicle states are beyond this draft.

## Owner image and evidence boundary

`qa10/draft21-rain-stronger.png` is the one owner image. The top half compares **draft 20 | draft 21 at true 1x page scale**, with two red umbrellas on the sidewalk and the taxi/bus in the +u lane (v=11). Both sides use the real current `out10/base.png`, the same decoded frame 13 from `light_loop.webm`, current occluder/vehicle/character sprites and frame 13 of `rain_fg.webm`. This is the actual lit/rain composition, not dark asset panels or a relit substitute. Existing janitor sprites act as sample walkers under the umbrellas.

The bottom half compares the same subjects at **exact 2x integer enlargement of those 1x pixels**. It uses a full taxi crop, the umbrella group, and a roof-to-road **bus rear detail** so contact, droplets, wake and roof can be read together within 1280 x 720. The full bus remains visible above. These are detail crops, not a smaller rescaling of the bus labelled 2x. `_work/composition.json` records every crop and page position. Main phase is 13/24 = .542 s on both sides; the second umbrella uses an offset clock of 31/24 s (old loop phase 7, new phase 31).

This is offline draft composition and sprite/loop QA. No live browser, moving production page or 1080p/1440p stream-encode acceptance is claimed.

## Render times and checks

Local Cycles OptiX; CPU render fallback disabled. Same 3840 x 2160 camera grid, cropped captures, 128 maximum / 64 minimum samples, adaptive threshold .012, OptiX denoising, fixed seed 5101, AgX Medium High Contrast, ordinary exposure +.25. Pixel filter remains Blackman-Harris width 2.5. The 1x reduction is a scene-linear premultiplied RGBA 2x2 mean before display conversion. All water/mist materials are non-emissive; contrast changes occur in the isolated rendered passes. See the bus-film exposure exception above.

| Retained capture set | GPU capture wall seconds |
|---|---:|
| umbrella_red | 151.311 |
| taxi_roof_plus | 12.206 |
| bus_roof_plus | 22.693 |
| bus_spray_plus | 124.469 |
| sedan_a_spray_plus | 90.760 |
| **Total** | **401.439** |

These are 444 retained captures: 49 independently constructed phases for each of nine changing components and three static film captures. The spray times include its separate wake. Timings exclude setup, PNG conversion, previews, discarded/repeated captures, packing and composition. The full per-capture device/timing record is `_work/delivered-render-times.json`.

- All 14 delivered atlases contain 48 distinct frames; dimensions, RGBA8 memory, file bytes and hashes are recorded.
- All nine changing component geometries match exactly at phase 0/48. A short contact-fringe subcycle initially failed this check; it was wrapped to the 48-frame phase and the endpoint rerendered before delivery.
- Endpoint image mean error is at most **0.000051/255** across delivered resolutions. Sparse GPU/denoiser residuals are retained in the validation report rather than hidden by copying frame 0.
- Every cropped frame boundary is zero-alpha/black. All phase-47-to-0 steps pass the ordinary-step range gate; maximum seam/median ratio is **1.376**.
- Ground/grip registration is checked algebraically for every crop; no scale changes. The final image is exactly 1280 x 720.
- **7,231 pre-existing files hash unchanged**, covering every prior `out*` pack, including `out10` and `out10e`, and `standby/roxy.html`. Receipts: `_work/protected-before.json` and `_work/protected-after.json`.

Reproduce locally with `_work/run.ps1 -Mode final`, then Blender's bundled Python on `_work/finish.py`, `_work/compose.py` and `_work/audit.py`; use `_work/decode_scene.py` for the two reference video frames and `_work/label.ps1` for the final small labels. The retained audit includes the completed resume's timing/geometry records. All working/cache/output paths are under `roxy3d/out10f/`; the only other new deliverables are this note and the owner image under `roxy3d/qa10/`.

STATUS: COMPLETE - Brief 52 draft 21 assets, one owner image and notes delivered; prior packs/page unchanged; stopped.
