# Pass 8b — focused polish of out8

Complete pack: `out8b/manifest.json`, **443 files / 110,166,336 bytes**. Source scene: `roxy_pass8b.blend`. Work follows BRIEF-10-pass8b.md and the scoped visual/fallback findings in reviews/review-9.md.
All **2,182 files** in the eight live packs (out through out8) match the before-run SHA-256 inventory. 394 inherited files are byte-identical in the new pack. All old manifest contracts, render-layer crops, footprints, parent depths, billboard/marquee/poster coordinates, item and vehicle entries remain intact. The numeric asset_pack_pass stays 8; asset_pack_revision is `8b`.
Each completed stage is appended with a timestamp to `qa8/STATUS.md`. Other revision-specific QA is in `qa8b/`. No page or server file was changed.

## The seven requested changes

1. **Upper-center transition:** five real stepped rear buildings, parapets, rooftop stair heads, chimneys and dim windows break the straight y≈175 edge. They sit behind v=0 and have linked soft fill. Uneven cloud light and the rear atmosphere extend around their facades. The final preview was inspected after a second lighting adjustment; the original dark-fronted trial was superseded.
2. **Downpour:** 1,800 fine + 700 medium base streaks, and 1,800 fine + 950 medium foreground streaks. The 24 nearest streaks retain their previous count and brightness. Source rain therefore fills more space between large drops, without raising a uniform white layer. Brighter impact crowns and localized spray follow the curbs and lamp pool. Both streams remain 144 frames / 24 fps / 6 seconds.
3. **Wet glass:** the existing nine 72-frame runnel crops retain every placement/timing/depth field and get stronger dark edges and brighter highlights. Nine additional pane-wide static films provide uneven wetness and brighter sill accumulation. The films are one-cell RGBA spritesheets at the exact same glass-slice z_index and parent_slices, using source-over. A regular striped trial was replaced by irregular low-contrast film variation after visual inspection. Cashier glass stays dry.
4. **Reflections:** rough asphalt islands, fine aggregate relief and interrupted water-film coverage break the broad neon/lamp pools. Periodic impacts create localized radial distortion, limited to about ±3 px horizontally and ±2 px vertically on the wet surfaces. The exact per-channel temporal-minimum base plus nonnegative video differences remains in use, so moving reflections can both brighten and darken correctly.
5. **Right forecourt and roof:** darker mottled wet concrete/felt, world-aligned joints, grime, irregular feathered puddles and localized warm records-sign spill replace the uniform gray surfaces. Wet materials retain actual light-source reflections.
6. **Carpet rectangles:** removed 18 `Worn carpet diamond` outline meshes. Their world-space diamond vertices project into screen-aligned rectangles with this camera; these were intentional old motifs, not debug render boxes. The original woven flecks, soft traffic wear, carpet color, medallion, routes and floor geometry remain.
7. **No-video fallback:** new `lit_bg_dry.png` and `lit_bg_dry@2x.png`, exposed by manifest keys `lit_bg_dry` and `lit_bg_dry_2x`. These are fully lit background renders with wet surfaces and fixed real reflections, without baked falling rain, impacts, spray, animated runoff or steam. The inherited `lit_bg` files remain the regular frame-60 fallback for older consumers.

## Integration and memory

The new weather-free still is a background, not a flattened prop stack: retain the existing render_layers/prop_loops above it, then let the page provide procedural weather. Review-9 #6 also calls for coordinated main/foreground-video failure handling; that page lifecycle work is separate from these asset files.
Existing `water_glass_*` entries are unchanged in the manifest. New `film_glass_left_00..05` and `film_glass_right_00..02` entries use frames=columns=rows=1, fps=12, straight RGBA and source-over. Render them at their supplied slice depth. There is no new video decoder. Existing arcade, item, cat, staff, vehicle, lamp-state, umbrella, door, shelter and tyre-spray assets are copied unchanged.
All glass animations and films, including both 1x and 2x allocations, occupy **11,970,000 bytes / 11.415 MiB**, below the 16 MiB budget. Fully transparent texels have RGB zero.
The existing full-composition contract remains: frame 60 of base weather, sorted props and default arcade attract, then foreground rain. full.png/full@2x.png now include the revised pane-wide films. Old pass8_art/pass8_checks metadata remains as source-pack history; pass8b_art/pass8b_checks and pass8b_validation describe this revision.

## Encoding and acceptance results

Both WebMs use VP9 CRF 18, bitrate=0, GOOD preset, GOP 144, no audio. Parsed keyframe headers confirm profile 0, 8-bit 4:2:0 and limited-range signaling. The same two 1080p streams scale for 4K.
| Stream | Bytes | Average Mb/s | Encode seconds | VSE decode ms/frame |
|---|---:|---:|---:|---:|
| light_loop | 3,158,981 | 4.212 | 26.355 | 9.573 |
| rain_fg | 1,818,957 | 2.425 | 20.205 | 7.856 |

Decode timing covers 144 sequential decoded frames through Blender VSE, including conversion/render overhead and seven saved PNG samples. It is not isolated codec timing or concurrent OBS/CEF performance.
- Geometry holdouts: **0 covered action pixels** at both 1920x1080 and 3840x2160. The independently rendered protected masks contain 893,839 and 3,579,808 full-coverage pixels. Action alpha >0.999 and solid alpha >1/255; antialiased partial boundary pixels are excluded from the hard count.
- Green aperture after decoded videos and all default overlays: **186,624 physical pixels at 1080p; 746,496 at 4K**, equal to **186,624 logical pixels at either scale**. Frames 0,72,143 pass, as does the weather-free fallback at both scales.
- Fresh camera calibration: eleven rendered markers, maximum axis error **0.011163 px**.
- Mathematical frame 144 equals frame 0 exactly for both source videos; all 144 source frames are distinct. Dynamic glass period endpoints are identical, and source/decoded last-to-first differences remain within normal adjacent movement.
- All 144 encoded frames of each stream were sequentially decoded. Seven saved frames per stream were checked for active-rain accuracy, sample uniqueness and exact black in the full aperture and indoor sample. Decoded black maximum is **0**.
- Weather-free fallback pixels exactly match the grain-treated unanimated Cycles backgrounds, with only the preserved aperture pixels restored. Reconstruction error is **0** at both resolutions.
- Physical forecourt sample: 30,153 visible surface pixels; average luma fell from **116.38 to 73.77** on the 0–255 scale.
- Actual foreground pixels brighter than 8/255 increased by **1.95–2.30x** across four matched source frames, with the nearest streak count unchanged.

## QA and reproduction

- `qa8b/preview_surroundings.png`: lit model/material preview before loops.
- `qa8b/final_decoded_f072.png`: final composite using decoded videos.
- `qa8b/fallback_dry_full.png` and `@2x`: weather-free still with inherited static props for visual inspection.
- `qa8b/glass_before_after.png`: delivered glass comparison, source pane on the left and revised pane on the right.
- `qa8b/carpet_before_after_4k.png`: requested 4K carpet region, out8 left and out8b right.
- `qa8b/backdrop_before_after.png`, `rain_depth_before_after.png`, `right_forecourt_before_after.png`, `road_reflection_before_after.png`, `glass_in_scene_before_after.png`: targeted evidence. Comparisons use source/decoded delivered images; no retouching.
- `qa8b/final_validation.json`: contract, live SHA-256 and complete output inventory; additional numeric records are video_validation, weather_validation, glass_validation, polish_validation and surroundings_occlusion JSONs.

From standby: `powershell -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass8b.ps1 -Mode all`. `-Mode preview` stops after the lit preview and both holdouts. `-Mode package` rechecks completed renders, republishes the manifest and rewrites these notes. All outputs, logs and caches stay inside roxy3d.
The pack has been inspected in rendered stills and decoded-frame comparisons. Live OBS/CEF playback, coordinated fallback behavior and video restart pacing remain page acceptance checks. Server, crowd, bubble and DOM marquee findings outside the seven items in Brief 10 are outside this asset pass.
