# Brief 27 - faster pipeline, approved Draft 13

Implemented all four changes. The source scene and roxy.html are unchanged. No local full render or cloud pod was run. ONE owner draft: `qa10/draft14-fast.png` (1280x720), composed from the measured cut/fallback layers, depth ownership and additive weather.

Owner decision, 03 Nov 2026: 24 unique wet/foreground frames are now the default when ROXY_WET_FRAMES is unset; ROXY_WET_FRAMES=48 remains an override. Only the affected no-render scheduling and cadence checks were re-run for this change. The existing draft, render timings and packaging evidence below are retained; no new draft, 3D capture or clip was made.

The combined pass is deliberately conditional: 6 of 39 groups pass both colour and alpha noise gates. The other 33 retain isolated rendering. This limits the batching gain, but avoids discarding hidden surfaces or changing glass coverage.

## Pipeline and output contract

- Combined foreground beauty + antialiased Cryptomatte masks + FloorUV positions; selected groups share one capture per unique phase. Measured exceptions are rendered consecutively by group.
- All new production captures use the 4K camera grid. 1080p is a 2x2 scene-linear RGBA average before display conversion. Surface coordinates are coverage-weighted. Backgrounds, foreground, doors, WC, airborne rain and four bus states use this path.
- Unchanged phase/visibility state is cached, redundant object/material writes are skipped, and neon circuits/materials are pre-indexed. Persistent Data, adaptive 256/64/.01, OptiX denoise, HDR glare and sharp topology-changing drips remain.
- Default 24 unique foreground/wet phases when `ROXY_WET_FRAMES` is unset: even phases are duplicated into the original 48 slots. `ROXY_WET_FRAMES=48` overrides this to render every phase. Eight columns, six rows, 24 fps and the 2s/6s cadence stay unchanged. Background light and airborne rain remain 48 unique phases. No new draft or test clip was rendered for this default change.

The layout-3 manifest schema, production sizes, filenames, wet/door sheet layouts, run.sh modes, progress.log, SUCCESS line, watchdog and out10.tar.gz are retained. The earlier per-decoded-frame video tolerance and validation pass flag are untouched. The cloud launcher/credit/keep-on-failure code is untouched.

## Matched local timings

RTX 3050 6 GB laptop, same 720p camera crop, queue_front, phases 0 and 2, same final quality and seed. The first sample includes pass setup; the second measures consecutive frames. These are wall times, not cloud benchmarks.

| Item (seconds) | Old first | New first | Old consecutive | New consecutive |
|---|---:|---:|---:|---:|
| Phase + frame/GN evaluation | 0.5165 | 0.0000 | 0.9117 | 0.5983 |
| Visibility/material work | 8.9399 | 4.4780 | 8.1689 | 0.0000 |
| EXR/hash receipts | 0.0005 | 0.0099 | 0.0005 | 0.0072 |
| EXR loading | 0.0114 | 0.0122 | 0.0115 | 0.0121 |
| Total capture wall | 15.3292 | 10.3170 | 15.1387 | 6.0446 |

Old render/sync/EXR bucket: 5.853 / 5.817 s. New render/sync/compositor: 5.809 / 5.205 s; separate EXR writes 0.0019 / 0.0020 s; configuration 0.0041 / 0.2186 s. Display conversion: old 1.471, new 0.631 s.

The C++ render bucket includes Cycles tracing, Persistent Data synchronization/rebuild, denoising and compositor work. These were not independently timed inside Blender; no unsupported attribution of that bucket to pure tracing is made. The directly measured Python visibility cost is removed between unchanged passes. Fixed-Persistent/adaptive comparisons also pass the original two-seed RGB gate.

Combined 720p capture including masks and positions: 26.147 s (18.412 render/sync/compositor, 1.804 mask export). This is compared with all 39 corresponding isolated groups in the table below. Old/new matched render pixel differences are recorded in timing27.json.

## Linear reduction and quality

| Comparison | Mean RGB | p99 RGB | Pass |
|---|---:|---:|---|
| Original 720p two-seed baseline | 0.002555782 | 0.037780643 | reference |
| Persistent Data | 0.000012729 | 0.000152707 | yes |
| Adaptive 256/64/.01 | 0.000212188 | 0.002193153 | yes |
| Native 1080p crop noise | 0.002095725 | 0.028188233 | reference |
| 4K area reduction vs native 1080p | 0.001870921 | 0.024641581 | yes |

Reduction test: native 3840/1920 camera grids over logical crop [660, 230, 660, 390], high pixels [1320, 780], low pixels [660, 390]. Native 1080 A/B: 17.11/17.12 s; one 4K crop: 51.38 s. This proves a bounded actual-resolution crop, not a whole 4K frame or all surfaces/phases.

Antialias matching is part of the production path and every high-resolution receipt: BLACKMAN_HARRIS 2.5 at 4K, compared with BLACKMAN_HARRIS 1.5 at native 1080p. The initial 1.5-pixel high-resolution filter failed (mean 0.003223705, p99 0.050588796); 3.0 also failed. The measured 2.5-pixel footprint passed without changing the noise thresholds. Original results remain in filter27.json and raw receipts.

## Every foreground group

Two independent seeds provide each group's noise baseline on the same frame and crop. Both mean/p99 RGB and mean/p99 alpha must pass. No threshold was relaxed. JSON includes every p99 and maximum as well as receipts.

| Group | RGB mean / noise | RGB p99 / noise | Alpha mean / noise | Path |
|---|---:|---:|---:|---|
| partition_left | 0.0126605 / 0.00102209 | 0.469135 / 0.0184471 | 0.144366 / 0.000489929 | isolated fallback |
| partition_right | 0.000918835 / 0.00149971 | 0.023283 / 0.0333742 | 0.0106339 / 0.000197265 | isolated fallback |
| boxoffice | 0.0167637 / 0.00232607 | 0.272408 / 0.032449 | 0.101619 / 0.00118909 | isolated fallback |
| snack | 0.000665715 / 0.00230978 | 0.0104461 / 0.0364425 | 0.0107121 / 0.000311583 | isolated fallback |
| podium | 0.00217637 / 0.0029051 | 0.0523023 / 0.0561965 | 0.0253556 / 0.000671069 | isolated fallback |
| bench | 0.000619304 / 0.000790089 | 0.00641195 / 0.00959504 | 0.00899104 / 0.000678706 | isolated fallback |
| arcade | 0.00194466 / 0.00141482 | 0.0488685 / 0.0225311 | 0.0376117 / 0.000639246 | isolated fallback |
| standee_1 | 0.000737129 / 0.00116378 | 0.0154617 / 0.0198793 | 3.68461e-06 / 0.000673763 | combined |
| standee_2 | 0.0204485 / 0.00127893 | 0.401983 / 0.0193471 | 0.182425 / 0.000596386 | isolated fallback |
| palm | 0.000698186 / 0.00052178 | 0.0110279 / 0.00834009 | 0.000256046 / 0.00114328 | isolated fallback |
| street_lamp | 0.00464731 / 0.00131364 | 0.104154 / 0.0281376 | 2.40384e-05 / 0.000677089 | isolated fallback |
| bus_stop | 0.000338722 / 0.000261019 | 0.00728814 / 0.00439606 | 0.00289647 / 0.000853701 | isolated fallback |
| glass_left | 0.00387424 / 0.00117306 | 0.0689736 / 0.0192873 | 0.0456475 / 0.00324612 | isolated fallback |
| glass_right | 0.000945141 / 0.000723767 | 0.00650899 / 0.0120268 | 0.0574767 / 0.00504883 | isolated fallback |
| entrance_post_1 | 0.00622075 / 0.00199735 | 0.186232 / 0.0275841 | 0.0228095 / 0.00123695 | isolated fallback |
| entrance_post_2 | 0.00185777 / 0.00140327 | 0.0350355 / 0.0193868 | 0.0570142 / 0.00125381 | isolated fallback |
| entrance_header | 0.000735993 / 0.000657202 | 0.0210505 / 0.011693 | 0.00730136 / 0.000566011 | isolated fallback |
| paste_wall | 0 / 0 | 0 / 0 | 0 / 0 | combined |
| entrance_neon | 0.00260511 / 0.00401153 | 0.0690716 / 0.0948597 | 1.7439e-05 / 0.000866309 | combined |
| restroom_entry_wall | 0.00212082 / 0.000289664 | 0.0254293 / 0.00347017 | 0.184674 / 0.000478093 | isolated fallback |
| restroom_stall_1 | 0.00019565 / 0.000301996 | 0.00393606 / 0.00554808 | 0.21523 / 0.000695935 | isolated fallback |
| restroom_stall_2 | 0.000262018 / 0.000327023 | 0.00553714 / 0.00611199 | 0.215282 / 0.000652545 | isolated fallback |
| restroom_stall_3 | 0.000368824 / 0.000277989 | 0.00863303 / 0.00534987 | 0.195528 / 0.000995143 | isolated fallback |
| restroom_stall_4 | 0.00197033 / 0.000178389 | 0.0223855 / 0.00313965 | 0.28175 / 0.00125804 | isolated fallback |
| restroom_sinks | 0.0117633 / 0.00144898 | 0.195059 / 0.0237011 | 0.136395 / 0.000897294 | isolated fallback |
| restroom_dryer | 0.00090536 / 0.00113666 | 0.0134777 / 0.0131797 | 0.0132088 / 0.00083257 | isolated fallback |
| restroom_service | 0.00781127 / 0.000429556 | 0.148661 / 0.00899939 | 0.198435 / 0.000717303 | isolated fallback |
| front_solid_wall | 0.00422955 / 0.000514774 | 0.0447246 / 0.00581166 | 0.221863 / 0.000559293 | isolated fallback |
| queue_front | 0.00178195 / 0.00041243 | 0.0407433 / 0.0100308 | 0.016062 / 0.000336029 | isolated fallback |
| queue_back | 0.000814688 / 0.00044614 | 0.026402 / 0.0104685 | 0.0127486 / 0.000439979 | isolated fallback |
| corridor_standee_1 | 0.000412624 / 0.00127961 | 0.0071039 / 0.0203741 | 9.59877e-07 / 0.000592351 | combined |
| corridor_standee_2 | 0.000582403 / 0.00177353 | 0.0106818 / 0.0359235 | 1.40336e-06 / 0.000684382 | combined |
| corridor_bench | 0.00957512 / 0.000678424 | 0.246613 / 0.0159481 | 0.208655 / 0.000569324 | isolated fallback |
| corridor_fountain | 0.0904243 / 0.00288914 | 1.04144 / 0.0484605 | 0.32104 / 0.000920631 | isolated fallback |
| corridor_bin | 0.0017401 / 0.000227929 | 0.0361333 / 0.00436658 | 0.195476 / 0.000815434 | isolated fallback |
| corridor_extinguisher | 0.000801367 / 0.0016235 | 0.0160915 / 0.0358637 | 4.24618e-06 / 0.00114523 | combined |
| restroom_side_wall | 0.00278318 / 0.000675444 | 0.0871041 / 0.0146305 | 0.0251327 / 0.000248374 | isolated fallback |
| restroom_closet_wall | 0.00121304 / 5.82852e-05 | 0.0228121 / 0.0012442 | 0.38259 / 0.000554208 | isolated fallback |
| restroom_entry_leaf | 0.00108743 / 0.000248191 | 0.0202809 / 0.002489 | 0.062207 / 0.000566779 | isolated fallback |

## Packaging proof

End-to-end smoke pack passed production VP9 encode and actual decode (144 repeated smoke frames), validator, all depth reconstructions, 8x6 and 4x4 sheet dimensions/endpoints, real rebuilt bus bodies in four states at both output scales, cleanup of an unreferenced sentinel, checksum inventory, tar creation and every-member SHA-256 read-back. Archive fixture: `cloud/bundle/work/smoke_tail/out10.tar.gz`; 95 files. Codec maximum black channel: 0/255. The video's own per-frame pass flag remains authoritative.

The repeated-frame video/sheets exercise packaging and codec branches; they are not a motion/seam quality claim. No extra owner preview or test clip is delivered. Preflight and contract/watchdog fixtures pass; watchdog pod commands are mocked. Cache resume is exercised by the final smoke rerun loading completed captures from hash-checked receipts.

Visual QA caught a shared-wall depth issue in the layer assembly: independently spaced cap and support-wall bins exposed the shadowed black wall top in alternating spans. The six cap bins now share the five supporting-wall boundaries, with one extra entry span and a one-unit depth offset. The physical footprint and slice count remain unchanged; the final draft was recomposed from the same captures and inspected with the cap continuous. The smoke fixture also clears RGB when downscaled alpha rounds to zero, as production already does, so exact RGBA slice reconstruction passes.

The focused independent-reference check reports zero bright-cap pixels turning into black holes after the correction. A 0.025-tile ownership guard handles fractional coverage at the shared boundaries. It is not a claim that the display-space glass stack is pixel-identical to a single physical scene render; visual27.json records the remaining differences in that narrow diagnostic band.

## Cloud projection (not measured)

Run-2 foreground 4s render + 5s overhead scaled separately by matched local ratios, with a visibility refresh amortized every six phases for bell-circuit changes; combined/isolated local ratio; 4K background 41s from 5090; doors halved; entire run-2 remainder retained. 4090 render stages multiplied by 31/19 observed background ratio. Planning interval -20%/+30%; no cloud measurements.

| GPU / wet unique frames | Central hours | Planning hours | Central cost | Planning cost |
|---|---:|---:|---:|---:|
| RTX 5090 / 24 (default) | 2.07 | 1.65-2.69 | $2.46 | $1.97-$3.20 |
| RTX 4090 / 24 (default) | 2.73 | 2.19-3.56 | $2.43 | $1.95-$3.16 |
| RTX 5090 / 48 (override) | 2.49 | 1.99-3.23 | $2.96 | $2.37-$3.85 |
| RTX 4090 / 48 (override) | 3.42 | 2.74-4.45 | $3.04 | $2.44-$3.96 |

Rates supplied by owner: RTX 4090 $0.89/h, RTX 5090 $1.19/h. Dynamic isolated exceptions: 12 of 14; static isolated exceptions: 21 of 25. Native 4K rain/mask overhead, GPU clocks, packing and cache behavior can shift these projections. No rental or spend occurred.

## Delivery limits

The one draft and bounded local smoke are complete. Full animation, every camera pixel at native 4K, all-time glass comparisons, Linux/GPU behavior and browser/OBS playback remain untested. No full render was launched to fill those gaps. The source scene and page were preserved. The sealed archive identity is recorded separately in cloud/bundle-delivery.json and qa10/STATUS.md.

Cryptomatte API reference used during implementation: https://docs.blender.org/api/5.2/bpy.types.CompositorNodeCryptomatteV2.html
