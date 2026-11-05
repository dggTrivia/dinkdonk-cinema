# Brief 47: draft 15 applied to out10b

STATUS: COMPLETE — `out10b/` is ready. The live `out10/` pack and `../roxy.html` are unchanged. All writes stayed inside `roxy3d/`. No cloud job, lobby render, video encode, test clip, or new owner image was made.

The new pack is a copy of the current live pack, including the post-fixed Brief 45 light loops. It contains the same **706 files**. Exactly **95 files differ**: **92 image assets**, `manifest.json`, `validation.json`, and `checksums.json`. The remaining **611 files are byte-identical** to live.

## Vehicles

Rendered all **12 body states** on the local **RTX 3050 6GB Laptop GPU**, using OptiX: bus and taxi in both directions, closed and open; sedan A and sedan B in both directions. Replaced **24 whole-body PNGs** and **56 depth-slice PNGs**, including the open-door slices.

The approved vehicle-only studio settings are applied in both the local legacy builder and the portable builder used by the current bus recipe:

| Source | Power / strength |
|---|---:|
| Cool overcast fill | 0 W |
| Current warm script reflection | 8 W |
| Cinema cyan reflection | 11.2 W |
| Warm street fill | 6.8 W |
| Vehicle world Background | .015 |

The warm reflection uses the approved RGB `(1, .27, .39)`; the other source colours, positions, shapes and sizes remain as drafted. The shared lobby world and lighting were not changed. Vehicle lamp objects, lens emission, cabin lamps, artwork and branding remain in the body recipe. All **80 shipped vehicle light-map PNGs** are byte-identical to live.

The 12 native 3840×2160 camera-grid renders use the existing 610×400 logical working crop, AgX / Medium High Contrast, exposure +.25, Blackman-Harris width 2.5, adaptive maximum 256 / minimum 64 samples, threshold .01, and OptiX denoising. Position AOVs were captured in the same renders. The 1× images use the production **linear 2×2 reduction before display conversion**, with the original contact-shadow formula at each size.

Existing slice ownership was reused where it had coverage after verifying model bounds against the manifest. New antialiased coverage uses the captured position AOV, with the original ground-position fallback for shadows. Every published filename, whole-body canvas, anchor, slice rectangle, depth interval and offset is retained. All **24 reconstruction checks** pass with **zero RGBA channel error**, **zero overlapping nonzero-alpha pixels**, and no sprite edge clipping.

Displayed sRGB roof luma, using the same inset regions as draft 15:

| Roof | Live median | Approved draft median | out10b median | out10b 90th percentile |
|---|---:|---:|---:|---:|
| Sedan B +u, 2,064 pixels | 166.3278 | 24.1316 | **24.1316** | 25.6290 |
| Bus +u, 14,820 pixels | 198.9162 | 32.8800 | **32.8702** | 39.0354 |

The measured native render/AOV work totalled **19.99 seconds**; body setup, rendering, both display sizes, cropping and slice packaging totalled **29.92 seconds** in the successful 12-state run. These timings exclude source inspection, door work and the rest of verification.

## Static plates, Screen 2 animation and loops

Replaced `bg`, `base`, `lit_bg`, `lit_bg_dry`, and `full`, at both resolutions. All ten images are **pixel-exact matches to the approved draft-15 staged plates**. They use the saved fixed nonnegative offset D, affecting **4,169 pixels at 1×** and **16,635 at 2×**. Alpha and pixels outside the approved mask are unchanged. Screen 2's reference-region median remains **[90, 20, 33]**, against the target **[90.5, 20, 32.5]**.

Replaced both `doors/screen_2` sheets. The original **4×4 layout, 16 frames, 18 fps, 120×181 logical frame size, row-major order and alpha** remain unchanged. The six unique poses retain the original order `[0,1,2,3,4,5,5,5,5,5,5,4,3,2,1,0]`.

The open-pose masks follow the actual transformed leaves and ray-tested leather surfaces. Geometry-only ray queries use four samples per logical pixel axis, including nearby frame, hardware and foreground occlusion; volume-only surfaces are excluded from surface ownership. The approved quantile transfer curves remain unchanged. Material ownership avoids the speckling that a hard colour threshold produced in dark open-pose shadows. The opaque opening, nonleather hardware, frame and cast-shadow pixels outside the leather masks are unchanged. The closed pose uses the approved static mask and matches the corrected static leather **exactly**, including both copies of that pose in the sheet.

Both copied live WebMs were decoded again at their native resolutions: **144 frames each**, **288 total**. The relation remains `new_base = live_base + D`, with the original nonnegative loop delta added above it. Maximum base-plus-loop channels in the changed mask are **166/255 at 1×** and **172/255 at 2×**, leaving **89** and **83** levels of headroom. There are no negative corrections or new clipped channels in that region. This check concerns the changed door pixels, not unrelated existing highlights elsewhere.

Preserved live-loop SHA-256 values:

- `light_loop.webm`: `aa6d58b8681ab5888805b226f8b2e8ab8aba1936b82a98e8f5bf436735a2236e`
- `light_loop_2x.webm`: `ff835084b14bd5f5de619a5cb05572970f04c5d4eba1f700833ba5cf3fd0b84c`

## Manifest and source repairs

Only two manifest values changed: `lanes.far` is **12.75**, and `asset_pack_revision` is **`10b-local-draft15-brief47`**. A recursive comparison confirms every other manifest value is unchanged.

Saved repairs to `roxy_pass10_draft.blend` and `cloud/bundle/scene.blend`, without rendering the lobby. Both now contain all **102/102 tagged parts for each of Screens 1, 2 and 3** in the cinema receiver collection; Screen 2 previously had only 10/102. Its **44 leather objects**—two leaf bodies, two tufted panels and 40 covered buttons—use the original dry leather. Other doors' materials and all hardware materials are unchanged.

`screen_door_fix.py` and its portable copy apply the repair by stable `door_id` / `anim_id`. The draft-5 outdoor classifier, draft-11 receiver classifier, draft-12 receiver transfer, production preparation and runtime load path now preserve indoor screen-door membership regardless of pose. Both `build_vehicles.py` files contain the vehicle-only studio override, covering the legacy sedan/taxi route and the current bus route.

Reopened both saved blends and checked object transforms, canonical door matrices, light powers/colours, world strength, camera transform, asset paths, material-change scope and repair idempotence. All three production doors match their canonical closed matrices, and Screen 2 retains correct receiver membership through all six poses. Packed unused bus artwork was retained explicitly so saving the lobby source does not discard it. Original source backups are under `cache/apply47/original_sources/`. A future real scene render must regenerate its normal smoke/fingerprint evidence for the changed sources; the old production evidence was not relabelled as current.

## Final verification

- All **698 PNGs** retain their dimensions; all **698 manifest asset references** resolve.
- Independently re-read all changed images and verified reconstruction, masks, alpha, static offset equality and animation repetition.
- Visually inspected the 12 vehicle states and six door poses using internal cache previews. No owner-facing image was produced.
- All **706 live-pack hashes**, plus the live page hash, match the initial snapshot.
- `validation.json` records this run's checks and their scope. No live browser playback or full-scene lighting validation is claimed.
- `checksums.json` contains **705 entries**, covering every other pack file, including hidden files and the refreshed validation. It excludes itself to avoid a recursive hash; its own SHA-256 is recorded in `cache/apply47/final-receipt.json`.

Reproduction scripts, measurements, source audits, loop decode results, mask data and the exact changed-file inventory are in `cache/apply47/`. The final package records are `out10b/manifest.json`, `out10b/validation.json`, and `out10b/checksums.json`.

STATUS: COMPLETE — draft 15 applied to the new `out10b/` pack; live pack and page unchanged; stopped.
