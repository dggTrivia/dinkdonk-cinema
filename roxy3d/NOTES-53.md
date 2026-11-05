# Brief 53 - production draft-21 rain pack

`out10g/` is a full copy of the live `out10/` payload with the approved draft-21 water expanded to the requested production set. Test with `?artdir=out10g`; Claude owns the page acceptance and later copy into live. `out10/`, `out10f/`, the approved notes and `standby/roxy.html` have matching before/after hashes. All writes are under `roxy3d/`. No cloud or network render was used.

## Delivered contract

- Four full-replacement wet umbrella loops: red, blue, yellow and black, source-over, 88 x 80 frames, anchor [44,68]. Existing dry/fold artwork is retained.
- Twelve roof states: bus/taxi/sedan_a/sedan_b, +u and -u, plus bus/taxi door_open. Their 28 additive roof sheets match the exact length and order of each state's existing `slices` array.
- Eight airborne spray loops and eight separate road-flat wake loops, one per vehicle/direction; plus-lighter, cropped and anchored to the vehicle ground centre. `full_speed` is 1.8 tiles/s.
- Every sheet has 48 frames at 24 fps, packed 8 columns x 6 rows; the independently rendered frame 48 is validation only. Dimensions, anchors and x/y offsets in the manifest are logical 1x pixels. @2x doubles the source sampling dimensions.

Exact requested keys are present: `umbrella.wet[colour]`, `vehicles[type][dir].roof_rain`, `door_open.roof_rain`, `.spray` and `.wake`. All inherited manifest values remain identical after stripping these additions and the new explanatory `rain_production_contract`.

## Approved appearance and source reuse

The copied draft-21 schedules, impact density/lifetimes, runoff, spray/wake trajectories, water materials, reference street lighting and fixed grading curves are retained. There is no per-frame renormalization. The red wet umbrella and bus/sedan-A +u spray/wake atlases are byte-identical to out10f at both resolutions. The taxi/bus +u closed roof slices reconstruct the approved unsliced out10f pixels exactly in every frame and resolution.

The other umbrella colours use their original dry production sprites plus newly captured water contributions on the matching coloured geometry. Other vehicles use the existing body builders, actual direction/door state and ground anchor. Cars inherit the taxi hit schedule/density; roof height and exposed bonnet/boot extent follow each car geometry, with sign sheltering only on the taxi. Sedan B retains its lower roof, and bonnet impacts land on its raised headlamp pods where those shelter the bonnet. -u effects and emitters rotate in 3D with the vehicle, and the reference rear/front grade follows travel direction.

Local Cycles OptiX on NVIDIA GeForce RTX 3050 6GB Laptop GPU. CPU fallback disabled. Same 3840 x 2160 camera grid, cropped 2x captures, 128 max / 64 minimum samples, adaptive threshold .012, fixed seed 5101, OptiX denoising, Blackman-Harris width 2.5, AgX Medium High Contrast, exposure +.25. Bus film retains the approved +4 EV capture exception and +8-level compression. 1x is the scene-linear premultiplied 2x2 reduction before display conversion.

## Slice ownership and reconstruction

Each impact carries its landing local-u band through its complete lifetime. Rendered RainOwner AOVs capture coverage against the actual body and door geometry. Film ownership comes from its surface world-u position. Direction is included before selecting the existing manifest u-ranges; there is no screen-x depth split. Component coverage is weighted by its graded contribution, and a deterministic winning owner receives each final integer RGB pixel exactly once. Sparse filter/denoiser halo pixels inherit the nearest expanding rendered matte neighbourhood; the radius and count are recorded in `_work/package-checks.json`.

Every slice uses an all-frame/all-resolution union crop with a two-logical-pixel black border. Its x/y is relative to the unchanged whole-body sprite top-left, not to the body slice crop. Draw at `P(u,lane) - parent.anchor + [roof.x,roof.y]`, immediately above the matching body slice using that body slice's depth/du. Do not add a second unsliced roof overlay. Reopening and summing delivered atlas frames yields **maximum channel error 0 and maximum nonblack contributors 1** for all 12 states x 48 frames x both resolutions (1,152 reconstructed frames). Independent verification is recorded in `validation.json`; unsliced beauty and owner arrays are retained under `_work/reconstruction/`.

For spray/wake crops, `croppedAnchor = captureAnchor - cropOffset`. Anchors may lie outside the cropped frame, particularly for trailing wakes; this is intentional. Wake goes at road depth below the vehicle, spray above the body; roof slices keep the existing foreground depth ordering. Spray and wake are whole loops as requested, with vehicle self-occlusion baked in. Page-level foreground sorting of airborne spray remains an integration concern.

At 1.8 tiles/s the wake scrolls opposite travel so deposited patches stay fixed in world space (.40 s bus / .32 s cars). For changing speed, use the travelled-distance/road-stamped handling in NOTES-52.md; do not treat the reference wake as physically exact under arbitrary acceleration. Suggested opacity remains smoothstep(.15,1.8,abs(speed)) with about .15 s stop/start crossfade and continuous phase. Lighting remains baked at (u=6,v=11).

## Files, sizes and decoded memory

New payload: **96 PNGs / 48 loops / 2,977,591 bytes (2.84 MiB)**, plus refreshed `manifest.json`, `validation.json` and `checksums.json`. The full staging payload contains **802 files / 124,988,665 bytes (119.20 MiB)** including the copied live files. `_work/` is reproducibility/QA data, not a web payload.

New loops total **39.90 MiB at 1x** and **159.61 MiB at @2x**, decoded RGBA8 with no mipmaps. The page should load 1x at 1080p and @2x for dpr > 1.3, one resolution per sheet. Both resolutions together would use 199.51 MiB; a full mip chain adds approximately one third.

For the entire staging pack, all shipped 1x PNGs total 292.75 MiB decoded RGBA8; the @2x set with unpaired 1x fallbacks totals 1170.99 MiB. These are storage-derived PNG inventory ceilings, not measured browser residency: legacy variants may not be loaded together. Video surfaces/decoders, browser decode/upload buffers and compositor copies are excluded.

Each row lists the 1x filename; its paired @2x filename has `@2x` before `.png`. Full exact bytes and VRAM values are in `_work/inventory.json` and `validation.json`.

| File | Frame 1x | Anchor or sprite x,y | PNG bytes 1x / 2x | RGBA8 MiB 1x / 2x |
|---|---:|---:|---:|---:|
| `umbrella/red_wet.png` | 88 x 80 | [44, 68] | 57,822 / 179,513 | 1.289 / 5.156 |
| `vehicles/rain/bus_spray_plus.png` | 144 x 75 | [117, 35] | 20,496 / 59,660 | 1.978 / 7.910 |
| `vehicles/rain/bus_wake_plus.png` | 50 x 28 | [123, 37] | 8,684 / 24,629 | 0.256 / 1.025 |
| `vehicles/rain/sedan_a_spray_plus.png` | 96 x 51 | [83, 22] | 16,272 / 46,051 | 0.896 / 3.586 |
| `vehicles/rain/sedan_a_wake_plus.png` | 41 x 24 | [93, 25] | 6,590 / 19,521 | 0.180 / 0.721 |
| `umbrella/blue_wet.png` | 88 x 80 | [44, 68] | 57,655 / 179,344 | 1.289 / 5.156 |
| `umbrella/yellow_wet.png` | 88 x 80 | [44, 68] | 58,249 / 181,617 | 1.289 / 5.156 |
| `umbrella/black_wet.png` | 88 x 80 | [44, 68] | 55,453 / 171,599 | 1.289 / 5.156 |
| `vehicles/rain/bus_roof_plus_00.png` | 96 x 52 | [66, 2] | 14,703 / 42,405 | 0.914 / 3.656 |
| `vehicles/rain/bus_roof_plus_01.png` | 103 x 54 | [115, 28] | 17,188 / 47,313 | 1.018 / 4.074 |
| `vehicles/rain/bus_roof_plus_02.png` | 91 x 48 | [171, 56] | 10,895 / 28,948 | 0.800 / 3.199 |
| `vehicles/rain/bus_roof_plus_open_00.png` | 96 x 52 | [66, 2] | 14,727 / 42,407 | 0.914 / 3.656 |
| `vehicles/rain/bus_roof_plus_open_01.png` | 103 x 54 | [115, 28] | 17,167 / 47,328 | 1.018 / 4.074 |
| `vehicles/rain/bus_roof_plus_open_02.png` | 91 x 48 | [171, 56] | 10,891 / 28,981 | 0.800 / 3.199 |
| `vehicles/rain/bus_roof_minus_00.png` | 91 x 48 | [174, 22] | 12,563 / 34,472 | 0.800 / 3.199 |
| `vehicles/rain/bus_roof_minus_01.png` | 103 x 53 | [218, 45] | 15,127 / 42,566 | 1.000 / 3.998 |
| `vehicles/rain/bus_roof_minus_02.png` | 95 x 50 | [275, 73] | 14,119 / 40,140 | 0.870 / 3.479 |
| `vehicles/rain/bus_roof_minus_open_00.png` | 91 x 48 | [174, 22] | 12,563 / 34,472 | 0.800 / 3.199 |
| `vehicles/rain/bus_roof_minus_open_01.png` | 103 x 53 | [218, 45] | 15,172 / 42,521 | 1.000 / 3.998 |
| `vehicles/rain/bus_roof_minus_open_02.png` | 95 x 50 | [275, 73] | 14,117 / 40,091 | 0.870 / 3.479 |
| `vehicles/rain/bus_spray_minus.png` | 194 x 73 | [77, 16] | 29,135 / 85,886 | 2.593 / 10.373 |
| `vehicles/rain/bus_wake_minus.png` | 103 x 48 | [-20, -15] | 16,355 / 46,838 | 0.905 / 3.621 |
| `vehicles/rain/taxi_roof_plus_00.png` | 77 x 34 | [49, 6] | 9,326 / 28,133 | 0.479 / 1.917 |
| `vehicles/rain/taxi_roof_plus_01.png` | 82 x 49 | [103, 21] | 6,962 / 19,213 | 0.736 / 2.943 |
| `vehicles/rain/taxi_roof_plus_open_00.png` | 77 x 34 | [49, 6] | 9,373 / 28,164 | 0.479 / 1.917 |
| `vehicles/rain/taxi_roof_plus_open_01.png` | 82 x 49 | [103, 21] | 6,959 / 19,140 | 0.736 / 2.943 |
| `vehicles/rain/taxi_spray_plus.png` | 99 x 52 | [85, 22] | 16,273 / 46,254 | 0.943 / 3.771 |
| `vehicles/rain/taxi_wake_plus.png` | 41 x 23 | [95, 25] | 6,478 / 18,897 | 0.173 / 0.691 |
| `vehicles/rain/taxi_roof_minus_00.png` | 68 x 33 | [168, 64] | 8,802 / 27,851 | 0.411 / 1.644 |
| `vehicles/rain/taxi_roof_minus_01.png` | 69 x 50 | [223, 79] | 6,641 / 18,823 | 0.632 / 2.527 |
| `vehicles/rain/taxi_roof_minus_open_00.png` | 68 x 33 | [168, 64] | 8,826 / 27,763 | 0.411 / 1.644 |
| `vehicles/rain/taxi_roof_minus_open_01.png` | 69 x 50 | [223, 79] | 6,642 / 18,790 | 0.632 / 2.527 |
| `vehicles/rain/taxi_spray_minus.png` | 143 x 53 | [58, 10] | 21,329 / 61,152 | 1.388 / 5.551 |
| `vehicles/rain/taxi_wake_minus.png` | 89 x 42 | [-6, -7] | 13,150 / 36,671 | 0.684 / 2.738 |
| `vehicles/rain/sedan_a_roof_plus_00.png` | 77 x 32 | [48, 10] | 8,473 / 23,976 | 0.451 / 1.805 |
| `vehicles/rain/sedan_a_roof_plus_01.png` | 76 x 48 | [103, 25] | 3,354 / 9,133 | 0.668 / 2.672 |
| `vehicles/rain/sedan_a_roof_minus_00.png` | 79 x 31 | [171, 65] | 7,765 / 23,045 | 0.448 / 1.794 |
| `vehicles/rain/sedan_a_roof_minus_01.png` | 64 x 50 | [229, 80] | 3,430 / 8,912 | 0.586 / 2.344 |
| `vehicles/rain/sedan_a_spray_minus.png` | 139 x 50 | [56, 9] | 21,397 / 62,325 | 1.273 / 5.090 |
| `vehicles/rain/sedan_a_wake_minus.png` | 88 x 42 | [-5, -6] | 13,813 / 38,030 | 0.677 / 2.707 |
| `vehicles/rain/sedan_b_roof_plus_00.png` | 79 x 33 | [46, 9] | 8,919 / 26,268 | 0.477 / 1.909 |
| `vehicles/rain/sedan_b_roof_plus_01.png` | 77 x 54 | [103, 27] | 5,773 / 15,314 | 0.761 / 3.045 |
| `vehicles/rain/sedan_b_spray_plus.png` | 97 x 52 | [84, 22] | 16,034 / 46,534 | 0.924 / 3.694 |
| `vehicles/rain/sedan_b_wake_plus.png` | 41 x 24 | [94, 25] | 6,619 / 19,404 | 0.180 / 0.721 |
| `vehicles/rain/sedan_b_roof_minus_00.png` | 81 x 29 | [177, 73] | 7,965 / 21,988 | 0.430 / 1.720 |
| `vehicles/rain/sedan_b_roof_minus_01.png` | 65 x 48 | [237, 88] | 3,348 / 8,791 | 0.571 / 2.285 |
| `vehicles/rain/sedan_b_spray_minus.png` | 141 x 51 | [57, 9] | 20,948 / 61,172 | 1.317 / 5.267 |
| `vehicles/rain/sedan_b_wake_minus.png` | 89 x 41 | [-5, -7] | 13,657 / 37,347 | 0.668 / 2.673 |

## Render time and validation

New retained GPU captures: **1,632**, including 33 independently constructed phase-48 closure captures and 15 static film captures. Summed render/capture wall time is **1627.783 s (27.13 min)**. Summed job wall time including setup, conversion and AOV export is **1948.664 s (32.48 min)**. These exclude the initial two-capture AOV probe, packaging, QA and already approved reused captures. Detailed receipts: `_work/delivered-render-times.json`; approved reuse timing remains in out10f.

| New capture job | Captures | Capture seconds | Job wall seconds |
|---|---:|---:|---:|
| bus_roof_minus | 50 | 32.826 | 44.265 |
| bus_roof_minus_open | 50 | 29.731 | 39.809 |
| bus_roof_plus | 50 | 28.366 | 37.044 |
| bus_roof_plus_open | 50 | 30.208 | 40.099 |
| bus_spray_minus | 147 | 139.263 | 154.686 |
| sedan_a_roof_minus | 50 | 22.138 | 31.535 |
| sedan_a_roof_plus | 50 | 20.618 | 29.189 |
| sedan_a_spray_minus | 147 | 114.873 | 129.115 |
| sedan_b_roof_minus | 50 | 26.559 | 37.876 |
| sedan_b_roof_plus | 50 | 15.297 | 21.920 |
| sedan_b_spray_minus | 147 | 151.200 | 168.552 |
| sedan_b_spray_plus | 147 | 144.555 | 161.262 |
| taxi_roof_minus | 50 | 19.495 | 28.106 |
| taxi_roof_minus_open | 50 | 19.052 | 26.894 |
| taxi_roof_plus | 50 | 17.380 | 24.327 |
| taxi_roof_plus_open | 50 | 16.488 | 23.122 |
| taxi_spray_minus | 147 | 112.239 | 126.145 |
| taxi_spray_plus | 147 | 113.878 | 126.797 |
| umbrella_black | 50 | 197.202 | 240.388 |
| umbrella_blue | 50 | 183.654 | 222.248 |
| umbrella_yellow | 50 | 192.761 | 235.283 |

- All 33 new changing-component geometry hashes match at phase 0/48. Maximum delivered endpoint mean channel error: 0.000139/255; maximum 99.9th-percentile error: 0.000/255. Sparse GPU/denoiser differences are retained.
- All 96 PNGs have correct atlas dimensions, zero-alpha/black frame boundaries and wrap steps within the ordinary-step range gate (wrap <= 1.35 x the largest ordinary step). Maximum atlas side: 3104 px. Roof slices may repeat idle frames; full sequences still have 48 timed frames.
- All 12 roof states have the required array length/order; reconstruction and no-double-addition checks pass at both resolutions. Requested anchors, full_speed and timing keys are present. All referenced files exist.
- 703 inherited payload files are byte-identical in staging; 4607 protected source/reference/page files are unchanged. Checksums cover every staging payload file except checksums.json itself and `_work/`.
- Internal contact sheets are asset QA only. No owner image is delivered. Browser motion, live-page depth interaction and stream-encode acceptance are reserved for Claude's page test; this pack has not been copied into live.

## Reproduce or integrate

Local reproducibility scripts are `_work/render53.py`, copied/annotated `draft21.py` and `reference_renderer.py`, `_work/run.ps1`, `_work/package53.py`, `_work/audit53.py` and `_work/contact53.py`. `run.ps1` resumes completed jobs; package/audit use Blender's bundled Python. All working/cache paths stay inside out10g. `production53_setup.py` documents the initial protected copy and refuses to overwrite an existing pack.

After Claude verifies `?artdir=out10g`, the promotion set is the 96 PNG paths in `_work/inventory.json` (both resolutions) plus the refreshed manifest/checksum/validation files. The inherited images/videos need not be recopied. This task stops at staging delivery.

STATUS: COMPLETE - Brief 53 production pack out10g and NOTES-53.md delivered; 48 loops validated; live pack/page unchanged; stopped.
