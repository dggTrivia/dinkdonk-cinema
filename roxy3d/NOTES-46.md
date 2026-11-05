# Brief 46 — draft 15: night traffic and Screen 2

STATUS: COMPLETE — one 1280×720 owner image at `qa10/draft15-cars-door2.png`; draft only; stopped. The live `out10/` pack and `../roxy.html` are unchanged. All new work is inside this `roxy3d/` folder. No cloud job, scene-wide render, video encode or test clip was made.

## Evidence and vehicle lighting

The pale tops are in the vehicle bodies, not an overlay in the page. `cloud/bundle/build_vehicles.py:309–314` builds a studio rig which follows every sprite into every street location. There is a parameter-order correction to the brief: `build_scene.area(name, loc, power, color, size, ...)` at `cloud/bundle/build_scene.py:174` makes **Cool overcast fill 220 W, size 5**, at `(u=5,v=10,z=310)`. It is not a 5 W light of size 220. `cloud/bundle/common.py:33` also supplies a blue world of strength 0.3.

The no-overhead calibration still had pale pink roofs: the three remaining sources were also strong for the adjacent street. The selected local studio settings are:

| Source | Previous | Draft | Retained colour / geometry |
|---|---:|---:|---|
| Cool overcast fill | 220 W | **0 W** | Disabled; original size 5 and position retained |
| Current warm script reflection | 100 W | **8 W** | RGB (1, .27, .39), size 3.2 × .55; original aim/position |
| Cinema cyan reflection | 140 W | **11.2 W** | RGB (.10, 1, .92), size 3 × .4; original aim/position |
| Warm street fill | 85 W | **6.8 W** | RGB (1, .73, .45), size 3; original aim/position |
| World Background | .3 | **.015** | RGB (.095, .12, .24) retained |

These are vehicle-studio overrides. A future application must not lower the shared scene/world setup for the lobby. All vehicle lamp objects, lens emission, cabin lamps and the shipped `*_light*.png` maps were retained.

The comparison uses actual `sedan_b +u` and the current bus recipe, including its approved advertising artwork. Both are rendered on the native 3840×2160 camera grid, using the existing 610×400 logical working crop, AgX / Medium High Contrast, exposure +.25, Blackman-Harris width 2.5, Cycles adaptive maximum 256 / minimum 64 / threshold .01, and OptiX denoising on the **RTX 3050 6GB Laptop GPU**. Original anchors, sprite canvases and contact-shadow formula are retained.

Level selection uses scene pixels, not a global exposure change. The following measurements are 8-bit displayed sRGB luma `Y=.2126R+.7152G+.0722B`, not physical luminance:

| Surface | Previous median Y | Draft median Y | Draft/reference 90th percentile Y |
|---|---:|---:|---:|
| Sedan B roof interior | 166.33 | **24.13** | 25.63 |
| Bus roof interior | 198.92 | **32.88** | 39.04 |
| Nearby road, logical rect [490,840,550,865] | — | **22.63** | 33.37 |
| Nearby pavement, logical rect [520,770,565,790] | — | **37.49** | 46.22 |

Roof samples use the actual roof-plane projections, inset from edges, with opaque body pixels: 2,064 sedan and 14,820 bus samples at 2x. The cream bus remains brighter than the dark sedan and road, while its upward faces no longer resemble a blanket overhead lamp.

For the bottom comparison, bus centre `(u=3,v=11)` and sedan centre `(u=7,v=11)` are identical before and after. Composition is the shipped base plus decoded live light-loop frame 0, unchanged normal vehicle light maps using saturated plus-lighter, then source-over bodies and the depth-sorted foreground/wet layers. The before uses the shipped body slices. At these unobstructed traffic positions, the after uses the page's whole-body fallback; there are no walkers between slices. Shipped slices were verified to reconstruct their whole bodies with **zero channel error and no overlapping nonzero-alpha pixels**. The relevant street-lamp occluder remains in the sorted stack. The headlight pools are identical in both panels.

## Screen 2: confirmed setup defect

Read-only inspection of the packed `cloud/bundle/scene.blend` finds Screen 2 missing from the **`D12 unchanged cinema receivers outside restroom`** receiver collection. The collection includes **102/102** tagged door objects for Screen 1 and **102/102** for Screen 3, but only **10/102** for Screen 2. Both Screen 2 leaf bodies (`Upholstered cinema door.006/.007`) and both tufted panels (`D7 tufted diamond leather panel.002/.003`) are excluded.

Nine lights use this receiver collection: Large soft cinema key (266 W), Warm lobby pool (99 W), Concession warm ceiling bounce (78 W), Corridor left blue fill (100 W), Corridor right fill (125 W), Cool street sky reflection (450 W), P10 broad roof moon fill (700 W), P10 auditorium facade fill (200 W), and D12 retained D11 ceiling contribution outside restroom (100 W). Consequently these lights cannot directly illuminate the excluded Screen 2 surfaces, regardless of the standee.

The source chain explains the omission:

- `build_pass10_draft.py:420–425` poses Screen 2 open for the early still.
- `build_pass10_draft11.py:53–60` classifies indoor receivers by the **current** bounds centre, requiring `v >= -.02`; the open leaves extend behind that limit.
- `build_pass10_draft12.py:51–63` carries those memberships into the D12 collection.
- `cloud/bundle/prepare_scene.py:20–26` closes Screen 2 later, without rebuilding those memberships.

There is also a material-classification mismatch: Screen 2's two tufted panels have `D10 wet paint | D7 oxblood leather upholstery`, whereas Screens 1/3 use the original dry `D7 oxblood leather upholstery`. The D10 outdoor test (`build_pass10_draft5.py:187–194`, used by D10) also relies on current position. This is a secondary verified inconsistency; its separate visual contribution was not isolated with a door A/B render.

The proposed 24/28 W explanation is unrelated: the three D13 reflector floods are rooftop-sign fixtures at about z=250, aimed upward at z=363–366 and receiver-linked to the sign/local roof (`build_pass10_draft13.py:79–111`). They are not the three screen-door lights. The unlinked wall sconces near Screens 2/3 both remain 15 W. No matched shadow render was performed to quantify the standee's incidental contribution; the receiver exclusion itself is directly established, and needs correction irrespective of that shadow.

For the next real scene render: classify all screen-door leaves, padding, seams, buttons and hardware as indoor by stable `door_id`/`anim_id`, in every animation pose; explicitly include them in the cinema receiver collection. Restore Screen 2's tufted panels to the same dry leather material as Screens 1/3 and exclude indoor door parts from position-only wet wrapping. Do this before saving canonical closed matrices and producing static/animated passes. Do not brighten the rooftop floods or increase the global lobby lights. Recheck all three doors closed and the six unique Screen 2 poses before a full production run. These scene changes have **not** been saved to the source blend.

## Masked 2D draft correction

Ten corrected static copies are in **`cache/draft15/plates/`**: `bg`, `base`, `lit_bg`, `lit_bg_dry`, `full`, each as `.png` and `@2x.png`. This is an internal draft staging directory, not a replacement live pack.

The mask follows the two leaf projections at v=.045: world-u intervals [7.735,8.186] and [8.214,8.665], z=15.5..107, with an inward .85-logical-pixel edge feather. It protects the seam, black frame, kickplates, wall, signs and standee. Within the geometry mask, a red-leather gate requires R>1.65G, R>1.16B, B>.85G, R>8. It covers 4,169 pixels at 1x and 16,635 at 2x. Statistical reference samples inset each leaf by .04 tiles and use z=23..100 with the same red gate. The frame did not need lifting.

Door 1 median RGB is **[96,21,36]**, Door 3 **[85,19,29]**, and original Door 2 **[28,4,7]** at both resolutions. The desired midpoint is **[90.5,20,32.5]**; corrected Door 2 is **[90,20,33]** in every staged plate, within .5 code values per channel. The implied median increases are 3.2321× R, 5× G, 4.6429× B. Those are not uniform gains: a monotone per-channel quantile curve also matches the texture contrast and avoids amplified bright speckles.

The native 2x transfer knots, RGB source → RGB target, are:

| Quantile | Source | Target |
|---|---|---|
| 5% | [23,2,4] | [73,13.5,25.5] |
| 10% | [24,2,4] | [76.5,15,27] |
| 25% | [26,3,5] | [82.5,16.5,29] |
| 50% | [28,4,7] | [90.5,20,32.5] |
| 75% | [31,5,8] | [99.5,24,36.5] |
| 90% | [34,7,10] | [106.5,28,40.5] |
| 95% | [37,10,11] | [110.5,30.5,42.5] |
| 99% | [44,15,15] | [117.705,40,47] |

Black and white endpoints stay [0,0,0] and [255,255,255]. Duplicate input knots use the first target. The 1x curve is independently measured from its native plate; exact knots, measured output quantiles and masks for both sizes are in `cache/draft15/adjustment-report.json` and `door-correction-{1,2}.npz`. At 2x the corrected median and 90th percentile are [90,20,33] and [106,28,40]. The original detail, stitching and lighting pattern are retained; no neighbouring door texture was copied over Screen 2.

The grade produces a **fixed nonnegative per-pixel RGB offset D**. The same D is added to all five static plates of that resolution. Alpha and all pixels outside the mask are byte-identical. This preserves the runtime relationship:

`new_base = base + D; new_composite(t) = base + D + existing_loop(t)`

Thus the existing loop remains the nonnegative delta above the new base. Both actual live WebMs were decoded at native resolution with Blender VSE, Standard/sRGB, exposure 0, gamma 1, no dither; **all 144 frames at each resolution** were checked. The maximum new base-plus-loop channel in the changed mask is **166/255 at 1x** and **172/255 at 2x**, leaving 89 and 83 levels of headroom. No headroom limiting was needed in the final grade. No negative offsets, new clipping, loop edits or recompression occurred. This is a local proof for the changed door pixels, not a claim that unrelated existing highlights elsewhere never saturate.

`doors/screen_2.png` and `doors/screen_2@2x.png` must receive the same leaf-colour mapping in a full application: preserve their 4×4 arrangement, 16 frames, 18 fps, 120×181 logical frame size and original alpha. Derive a **pose-aware leather mask** for each of the six unique source poses; keep the opaque dark opening, cast shadows and brass unchanged. Repeat the six corrected poses in the existing 16-frame order. Closed frame 0 must match the corrected static leaves so opening does not produce a dark flash. A flat rectangular brighten or a fixed closed-leaf mask across every frame would be wrong. The draft shows closed static doors, with no door-opening sheet composited, so those two animation sheets are not modified here.

## Full-apply scope and laptop estimate

After accepting the draft, a complete apply using the 2D door route would touch:

1. A vehicle-only lighting override in the source builder, including the legacy sedan/taxi rebuild route as well as `cloud/bundle/vehicles.py`'s bus route. Keep the live artwork, branding, geometry, anchors and light maps.
2. **12 native 2x body renders**: bus and taxi, both directions, closed/open (8); both sedans, both directions (4). Capture position AOVs in those same renders if needed; derive 1x with the production linear 2×2 reduction. Rebuild 24 whole-body PNGs and **56 depth-slice PNGs** (28 slices per resolution). Reuse compatible ownership only after geometry/alpha validation. Do not render normal/brake/indicator/tail/headlight maps.
3. The **10 static plates** listed above and **2 Screen 2 sheets**, using the protected masks and unchanged additive video. That is **92 image assets** in total, plus refreshed checksums/validation records; no page or manifest timing/layout changes are required. The mask/curve recipes and renderer scripts are staged internally in `cache/draft15/`.

Measured on this laptop: final sedan body **4.31 s**, final bus body **6.62 s**, including scene setup/render/save/crop; **10.93 s** for the selected pair. The earlier no-overhead calibration pair took 5.49 + 7.43 s. Only these four body renders were made, all for the two requested +u models; no door or full scene rendering was performed. A simple 8-car/4-bus extrapolation gives approximately **61 seconds of body work** for 12 states. Allow roughly **3–6 minutes total** for a full draft application, production AOV/slice packaging, pose masks, both 144-frame loop checks and image validation. This is an estimate, not a measured 12-state run; open-bus/taxi and AOV overhead can differ. A future full 3D lobby rerender has not been timed by this task and is not included.

## Verification and files

`cache/draft15/verification.json` passes: one owner image exactly **1280×720**, two lossless shipped-slice reconstruction checks, 10 masked static copies, both 144-frame loop checks, and **708 protected-file hashes unchanged** (all 706 files under live `out10/`, the page, and packed source scene). Pixel checks assert zero outside-mask and alpha differences. The final owner image was visually inspected for the three-door comparison, matching street positions, occluder stacking, labels and clipping.

Evidence: `cache/draft15/scene-inspection.json`, `vehicle-renders.json`, `adjustment-report.json`, `loop-decode.json`, `verification.json`, the body-render logs, and the standalone local scripts. Intermediate images and corrected plates there are internal working buffers, not additional owner drafts. No existing source, live pack or page was written. `qa10/draft15-cars-door2.png` is the single owner-facing image.

STATUS: DRAFT DELIVERED — ready for owner review; no full apply; stopped.
