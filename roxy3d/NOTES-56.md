# Brief 56 production delivery, completed under Brief 58

`out10i/` is the complete current live pack plus the verified cloud replacements: **810 payload files, 136,627,161 bytes (130.30 MiB)**. There are **444 CHG and 8 NEW** paths versus live out10 and **358 byte-identical inherited files**. The exact per-file sizes, hashes and destinations are in `qa58/final-inventory.json`, `out10i/checksums.json` and `out10i-copy-list.txt`.

Test **`?artdir=out10i&mistdir=out10i`**. Claude owns page/OBS acceptance and promotion. The eight root catch/height/rim/light PNGs target `out10mist/`; every other listed delta targets `out10/`. The NEW labels on mist paths mean new relative to the main out10 pack, while the copy list also records their comparison against out10mist. No live pack or page was edited. The unchanged stopped `out10i/_work` is excluded from payload and checksums. Keep `out10i.cloud` until Claude has promoted; all new QA is in `qa58`.

## Provenance and archive verification

Delivered production was rendered on **NVIDIA GeForce RTX 4090, Cycles OptiX, Blender 5.2.3 LTS on Linux**, through the Brief 57 bundle. The SECURE EUR-IS-1 helper run used pod `dhc93hhfxqwvi1` on 2026-11-05, from 14:51 provisioning through 17:53 download/cleanup. The helper log records exit 0 / DONE and deletion of that pod and volume `lbx8rc3twh`. These are retained run records, not a new provider-state query. Brief 58 started no pod and performed no scene renders.

The downloaded `cloud/result-full.tar.gz` is **1,026,069,505 bytes**, SHA-256 **`a4e53a67f786c518ba54778216e3ab413d2b0410789363c4c6ac2d9cc040ca69`**. All **1,589 regular archive members** were streamed and hashed against the unpacked result; all 1,588 entries in its checksums file match. Every one of the **802 baseline files** matches current live out10, including inventory equality. All seven stage receipts, 500 main capture receipts, two mist passes, all 243 returned source PNGs, and three independent endpoint proof files were checked. `qa58/verification.json` and `qa58/archive-members.json` hold this evidence.

Frozen scene SHA-256: `33090d845e0c10348627b42b24f55a774691eb44b1b47326158099e657987942`. Runtime: `3775276384197ce22a08a9671f2f5491898773e047b52cc6e8538ea006c59586`. Driver: `5d601fa31a3d0f256cf41a89e28a85613c8db8b66460a4f25672fd425fe58c41`. Each matches the stopped local source, uploaded bundle source, and returned cloud evidence. The returned native EXR hashes were verified by the pod audit before sealing; the EXRs themselves were not downloaded, so home QA verifies their sealed receipts and output PNGs rather than claiming a second EXR read-back.

The staged manifest's inherited RTX 3050 label was corrected to the RTX 4090. No appearance or timing contract changed during home QA. Cloud logs contain packed-image fallback warnings for old Windows paths; preflight verified 15 packed images and the run completed successfully. Visual review covers the requested sign/floodlight area, not every poster texture or page interaction.

## Approved appearance and production contract

The exact frozen draft-23 scene retains the cyan CINEMAS subtitle, approved mounting/frame, bulb positions and camera. Source verification preserves 7,011 other reference objects and all lamp energy/color/spread values. The central fitting is re-aimed and physically hooded; its warm 24 W wash is retained. The previously covered annex face was removed in the production copy to give the alley a single receiver. Source visibility was restored for foreground, rain, doors and mist.

Native **3840x2160**, **256 max / 64 min samples**, **.01** adaptive threshold, seed **1701**, OptiX denoising, Blackman-Harris **2.5**, existing AgX/glare, and scene-linear 2x2 reduction for 1x. The 48 background and rain phases repeat three times into **144 frames / 24 fps / 6 seconds**. Bell holds are **A12/B12, 0.50 s per state**. Foreground wet sheets retain **24 unique even phases in 48 paired slots**. Mist catch/AOV and light passes retain 16 and 32 samples respectively.

Stills, both light-loop resolutions, foreground rain, 39 occluders / 107 slices, all wet receiver sheets, door/WC plates, ad crops and eight mist maps are refreshed. All existing payload dimensions, placement/timing/alpha/depth contracts and manifest top-level keys remain. Manifest differences are sign/revision/loop descriptions, cloud-contract cadence/reference, and the corrected device label. Static glow stays null/disabled. All **272 vehicle/umbrella files**, including **96 Brief 53 rain PNGs**, are byte-identical. Other byte-identical categories: `{'cat': 14, 'items': 14, 'janitor': 12, '(root)': 2, 'prop_loops': 37, 'slices': 3, 'tyre_spray': 4, 'umbrella': 24, 'vehicles': 248}`.

## Full-cycle and ownership QA

All **432 frames** were decoded on the CPU with FFmpeg and read numerically; ffprobe independently confirms VP9, dimensions, 144 frames, 24 fps and six seconds. Every frame has a saved RGB24 hash and source-error metric. All **288 light-loop bell frames** classify correctly as `(A12 B12) x 6`. The 143-to-0 transition and every ordinary cyclic transition were measured; the expected B-to-A wrap passes the existing 1.35x ordinary-step / .05 floor gate. All **116 wet-sheet files** (58 at each resolution) pass all 48 transitions and exact paired slots, with opaque additive alpha. Both 144-frame bell contact sheets were opened and inspected.

Decoded alley offbeat block jumps are **0.375625 at 1x** and **0.386979 at 2x**, below the existing 1.5 gate. Independent background/rain/13 wet-parent phase-144 proofs pass mean < .0001 and p99 < .001 in linear RGB. All 48 raw background phases at both sizes reconstruct exactly from minimum base plus light delta.

All 107 depth slices reconstruct their 39 parents exactly at both scales with disjoint nontransparent ownership. Parent and slice alpha match live exactly. Eight door atlases retain exact alpha at both scales. Mist rim stays within catch; height/light are zero outside catch. All manifest references exist. Existing PNG dimensions remain unchanged. `qa58/validation56-details.json`, `decoded-validation.json`, `ownership-extra.json` and `raw-phase-validation.json` contain detailed results.

| Video | Bytes | Encode seconds | 143-to-0 mean RGB step | Largest ordinary step | Max mean codec error |
|---|---:|---:|---:|---:|---:|
| light_loop.webm | 5,780,126 | 34.74 | 0.334293 | 0.403965 | 0.274992 |
| light_loop_2x.webm | 20,114,483 | 90.07 | 0.387990 | 0.460747 | 0.271100 |
| rain_fg.webm | 230,000 | 11.72 | 0.060007 | 0.062131 | 0.012593 |

## Decoded memory

All staging PNGs total **340,144,788 RGBA8 bytes (324.39 MiB) at 1x**, and **1,360,579,152 bytes (1297.55 MiB) at 2x**. Each inventory has 401 PNGs. The eight companion mist maps add 31.64 MiB / 126.56 MiB to the main-pack inventory, replacing same-size active mist maps: **zero change in active image dimensions/storage**. These are inventory ceilings, not measured browser VRAM. Decoder surfaces, browser upload buffers, compositor copies and mipmaps are excluded. Video dimensions are unchanged; a single RGBA8 light+rain frame pair is 15.82 MiB at 1x and 39.55 MiB with 2x light / 1x rain, before decoder buffering.

## Actual timings and stopped local fallback

Cloud production wrapper: **10472.34 s (2.9090 h)**, including stage orchestration, audit and sealing. Retained capture/export sum is **7074.99 s**; capture-job sum including setup/read-back is **8131.61 s**. These sums are distinct from end-to-end wall time. Mist captures total 29.60 s, within their 99.21 s stage. The supplied Brief 58 reports balance 11.62 -> 8.87; no new balance query was made.

| Cloud stage | Wall seconds |
|---|---:|
| backgrounds | 3454.41 |
| weather | 878.28 |
| foreground | 5031.16 |
| doors | 609.24 |
| mist | 99.21 |
| package | 27.74 |
| videos | 203.09 |

| Output family | Captures | Render/export seconds | Capture-job seconds |
|---|---:|---:|---:|
| background | 49 | 2743.11 | 2842.63 |
| door_restroom_entry | 6 | 52.33 | 52.46 |
| door_screen_1 | 6 | 53.54 | 58.20 |
| door_screen_2 | 6 | 54.59 | 54.77 |
| door_screen_3 | 6 | 53.89 | 54.02 |
| door_stall_1 | 6 | 51.23 | 51.36 |
| door_stall_2 | 6 | 52.70 | 52.82 |
| door_stall_3 | 6 | 53.24 | 53.38 |
| door_stall_4 | 6 | 53.75 | 53.87 |
| dry fallback | 1 | 55.28 | 55.67 |
| foreground arcade | 1 | 8.59 | 13.63 |
| foreground bench | 1 | 8.54 | 13.48 |
| foreground boxoffice | 25 | 220.10 | 275.46 |
| foreground bus_stop | 25 | 227.68 | 283.53 |
| foreground corridor_bench | 1 | 9.28 | 13.97 |
| foreground corridor_bin | 1 | 9.36 | 13.99 |
| foreground corridor_extinguisher | 1 | 9.55 | 14.24 |
| foreground corridor_fountain | 1 | 9.52 | 14.19 |
| foreground corridor_standee_1 | 1 | 9.66 | 14.34 |
| foreground corridor_standee_2 | 1 | 9.17 | 13.85 |
| foreground entrance_header | 25 | 210.57 | 265.17 |
| foreground entrance_neon | 25 | 236.22 | 296.52 |
| foreground entrance_post_1 | 25 | 196.66 | 251.34 |
| foreground entrance_post_2 | 25 | 202.74 | 258.52 |
| foreground front_solid_wall | 25 | 246.77 | 303.31 |
| foreground glass_left | 25 | 242.35 | 298.30 |
| foreground glass_right | 25 | 214.90 | 269.86 |
| foreground palm | 1 | 8.79 | 13.91 |
| foreground partition_left | 25 | 224.30 | 282.00 |
| foreground partition_right | 25 | 253.38 | 308.53 |
| foreground paste_wall | 1 | 9.09 | 13.68 |
| foreground podium | 1 | 8.71 | 13.80 |
| foreground queue_back | 1 | 9.63 | 14.28 |
| foreground queue_front | 1 | 9.52 | 14.21 |
| foreground restroom_closet_wall | 1 | 8.72 | 13.34 |
| foreground restroom_dryer | 1 | 9.39 | 14.05 |
| foreground restroom_entry_leaf | 1 | 8.66 | 13.35 |
| foreground restroom_entry_wall | 1 | 9.76 | 14.39 |
| foreground restroom_service | 1 | 9.49 | 14.11 |
| foreground restroom_side_wall | 1 | 9.69 | 14.31 |
| foreground restroom_sinks | 1 | 9.51 | 14.18 |
| foreground restroom_stall_1 | 1 | 9.55 | 14.24 |
| foreground restroom_stall_2 | 1 | 9.45 | 14.10 |
| foreground restroom_stall_3 | 1 | 9.63 | 14.32 |
| foreground restroom_stall_4 | 1 | 9.37 | 14.02 |
| foreground snack | 25 | 230.45 | 286.44 |
| foreground standee_1 | 1 | 8.95 | 14.09 |
| foreground standee_2 | 1 | 8.52 | 13.61 |
| foreground street_lamp | 25 | 204.13 | 259.84 |
| rain foreground | 49 | 651.88 | 745.15 |
| wc | 2 | 19.50 | 25.17 |
| Mist catch/AOV + night light | 2 | 29.60 | 29.60 |

Local RTX 3050 activity was setup/probes and an earlier stopped fallback, never the delivered production. Its logs retain **6 completed probes totaling 237.99 s** and **34 partial background captures totaling 14390.53 s**; none were mixed into the cloud result. The fallback was not resumed or rewritten. Brief 57 local tiny smoke took **130.30 s**, and final-archive smoke verification **104.42 s**. Home decode/source QA took **235.58 s**; independent audit took **52.07 s**. No new render was needed.

## Check image, preservation and handoff

`qa10/draft24-dinkdonk-production.png` is the requested **1280x720** comparison: live | out10i in A above, live | out10i in B below. It uses decoded native 2x base-plus-light composites at phase 0 and phase 18, matching bulb-chase phases. All four use the same logical crop `[1100,0,680,460]` and scaling. It was reopened and inspected together with the native sign detail and both contact sheets. Visual findings: CINEMAS is legible in cyan, all seven glyphs are intact, the two bell poses are distinct, and the contact sheets alternate complete twelve-frame rows. The upper amber bulb rhythm is clean. No stray white aperture glint is visible above the O. The central wash remains restrained; no broad new white hotspot is visible on the sign or roof. The A/B comparison has readable labels, equal crops and no panel clipping. SHA-256: `e96b56e62277aa37f7b0ba37cee036faa71cf2109fe6f09ba893b7be0fb9a1cf`.

All **2757 protected hashes** match the starting snapshot, including live out10/out10mist, standby/roxy.html, source/reference files, the entire stopped fallback and downloaded cloud result. Final metadata/checksum/delta verification is recorded in `qa58/final-validation.json`. Home asset QA is complete; browser/OBS, moving-actor interactions and promotion remain Claude's handoff work.

STATUS: COMPLETE - Brief 56 cloud production staged and verified under Brief 58; NOTES-56, exact destination copy list and draft24 delivered; live packs/page/fallback/cloud evidence preserved; no pod started or scene rendered; stopped for Claude's page test and promotion.
