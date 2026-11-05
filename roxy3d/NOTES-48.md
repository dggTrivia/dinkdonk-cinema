# Brief 48: stray bus number plates at the curb

STATUS: COMPLETE — `out10c/` is ready. Both orphan plates are removed, source ownership is repaired, and validation/checksums are refreshed. The live `out10/` and `../roxy.html` are unchanged. All writes stayed inside `roxy3d/`; no cloud work, 3D render, video encode or owner image was made.

## Identification and cause

The white rectangle is **the rear number plate of the parked inspection bus**, left behind after the bus was removed for production. It is stray production geometry, not a road marking, shelter sign or reflection catcher. A second orphan plate from the same bus is also visible farther right.

| Component | Blender object | Actual world position / bounds | Production pixels and depth |
|---|---|---|---|
| Reported rear plate | `D6 bus DGG 05 number plate.001` | Centre `(u=-1.860, v=11.240, z=24.65 scene pixels)`; bounds u `[-1.863,-1.857]`, v `[11.150,11.330]`, z `[22.3,27.0]` | Projects approximately x `108.42–119.58`, y `601.61–611.89`. In `bus_stop_02`, z-index **1952**. |
| Rear lettering | `D6 bus plate DGG 05.001` | Text `DGG 05`, centre approximately `(-1.864,11.240,24.5)` | Same plate component and slice. |
| Second/front plate | `D6 bus DGG 05 number plate` | Centre `(u=.857, v=11.240, z=24.65 scene pixels)`; bounds u `[.854,.860]`, v `[11.150,11.330]`, z `[22.3,27.0]` | Projects approximately x `271.44–282.60`, y `683.12–693.40`. Split between `bus_stop_08` (**2122**) and `bus_stop_11` (**2207**). |
| Front lettering | `D6 bus plate DGG 05` | Text `DGG 05`, centre approximately `(.861,11.240,24.5)` | Same front component and slices. |

The plate meshes use **`D10 wet metal | D6 route enamel cream`**; lettering uses **`D10 wet metal | D6 route header blue`**. Both meshes and both text objects were visible to camera, with `layer=draft6_shelter` and `cloud_group=bus_stop`. Their height explains why treating the screen position as a ground point suggested roughly u -2.3, v 10.8; the actual plate is elevated.

`build_pass10_draft6.py`, in `shelter()`, created both bus plates while the current layer was still `draft6_shelter`. They lacked the parked bus's `draft5_bus` tag. `cloud/bundle/prepare_scene.py` removed the tagged bus body, then classified everything in that shelter layer as `bus_stop`, so the plates survived and inherited shelter slice depths above passing traffic. Evidence, including exact bounds, material names and original tags, is in `cache/brief48/scene-inspection.json` and `inspect.log`; the original source files are preserved in `cache/brief48/original_sources/`.

## Pack changes

`out10c/` was copied from the **current live out10**, which already includes the Brief 47 vehicle/door changes and Brief 45 loops. It has the same **706 files**. **19 files differ: 16 PNGs and 3 JSON records**. The other **687 files are byte-identical**.

Changed PNGs, at both 1× and native @2×:

- `full.png` / `full@2x.png`.
- `occ_bus_stop.png` / `occ_bus_stop@2x.png`.
- `slices/occ_bus_stop_02`, `_08`, `_11`.
- `prop_loops/wet_bus_stop_02`, `_08`, `_11`.

The slice filenames, dimensions, offsets, depth values and frame layouts remain unchanged. The now-empty rear slice remains a valid transparent image. Wet sheets retain their opaque alpha and additive contract, with the removed pixels' RGB set to zero in all **48 frames per sheet**. The front slices retain all shelter pixels above the plate.

| Removed nonzero-alpha pixels | 1× | @2× |
|---|---:|---:|
| Rear, `bus_stop_02` | 99 | 362 |
| Front, `bus_stop_08` | 41 | 146 |
| Front, `bus_stop_11` | 58 | 210 |
| Total parent footprint | **198** | **718** |
| Full-still pixels whose RGBA actually changed | **196** | **699** |
| Wet-sheet pixels whose RGB changed, summed over all affected frames/sheets | **1,596** | **9,708** |

The local inpaint uses the **already-rendered clean ground at exactly the same camera coordinates**. The original background pass excluded foreground camera rays, so `bg`, `base`, `lit_bg` and `lit_bg_dry` already had no number-plate rectangles. All eight of those background files are byte-identical. The affected full-still pixels now exactly equal their clean `lit_bg` donors. Reconstruction of the original stack found zero foreground-rain residual in those masks; no rain was erased. Every pixel outside the two native-resolution masks is unchanged. Existing puddles, shadows and reflections outside the masks were deliberately retained, rather than estimating a fresh lighting solution.

Both **144-frame light loops** were decoded at their native resolutions, **288 frames total**, with Blender's video sequencer used only for decoding. The all-phase contact sheets show wet-ground animation without either plate rectangle. Both WebMs remain byte-identical, with no recompression:

- `light_loop.webm`: `aa6d58b8681ab5888805b226f8b2e8ab8aba1936b82a98e8f5bf436735a2236e`
- `light_loop_2x.webm`: `ff835084b14bd5f5de619a5cb05572970f04c5d4eba1f700833ba5cf3fd0b84c`

Because both base and video bytes are unchanged, the existing nonnegative-delta relation is preserved exactly. There are **zero new negative corrections and zero new clipped channels**. In the removed-object masks, the maximum decoded base-plus-loop channel is **146/255 at 1×** and **157/255 at 2×**. This is a local headroom check, not a claim about unrelated highlights elsewhere. A harmless Blender `frame_duration` deprecation warning appears in `decode.log`; both 144-frame decodes completed and their stored array dimensions were independently checked.

## Nearby curb scan

Scanned **all 39 foreground parents at both resolutions**, including every bus-stop and street-lamp slice. The checked nearby road region is ground-projected **u -4 to 6, v >10.6 to 13.5**. This uses pixel centres and nonzero alpha, independently of the existing slice labels. Original scene object bounds were also inspected so elevated shelter geometry was not mistaken for ground debris.

The only foreground pixels in that region were the two number plates: **198 at 1× and 718 at 2×**. The second/front plate is the additional defect found and fixed. There are **zero remaining foreground pixels in that region** after the edit. No other object was moved into the ground or deleted. Correct shelter and lamp geometry is retained at its existing depth.

## Scene source repair for the next render

- Added `parked_bus_fix.py` and its identical portable copy, `cloud/bundle/parked_bus_fix.py`.
- `build_pass10_draft6.py` now tags both plate meshes and both labels with `draft5_bus=True` and `layer=draft5_parked_bus` when it creates them.
- `cloud/bundle/prepare_scene.py` also removes the four known plate objects from legacy drafts before classification, covering previously saved drafts with the erroneous tags.
- Saved **`cloud/bundle/scene.blend`** with those four orphan objects removed. Updated its `production.json` bus-stop object list and bounds. The source footprint changes from `[-1.865,9.080,3.235947,11.330]` to `[-.170,9.080,3.235947,10.248799]`; its recomputed parent z-index is 2120. The existing shipped pack's layout metadata stays fixed for pixel/depth compatibility.
- Saved **`roxy_pass10_draft.blend`** with the four plates correctly attached by ownership tags to its still-present parked bus. It retains the intended draft bus appearance; production removal will now take the plates with it.

Both saved blends were reopened and compared with their backups. All **6,900 remaining production objects** retain their transforms, materials, collections and visibility. In the draft, the only object changes are the ownership properties of the four plates; **7,109 other objects** are unchanged. Lights, world strength, camera transform and asset paths are unchanged. The production removal is idempotent and every production metadata object reference resolves. No 3D scene frames were rendered. The next real render must produce fresh smoke/fingerprint evidence for these changed sources; existing production evidence was not relabelled.

## Validation and internal crops for Claude

`out10c/validation.json` records **78 exact reconstruction checks**: 39 foreground parents × two resolutions, with **zero RGBA channel error and zero overlapping nonzero-alpha pixels**. Changed outputs were freshly decoded and checked against the saved masks. All **698 PNG dimensions** are retained and **698 unique manifest asset paths** resolve. Only `asset_pack_revision` changes as a manifest value, to `10c-local-orphan-bus-plates-brief48`.

`out10c/checksums.json` has **705 SHA-256 entries**, covering every other pack file, including hidden files and refreshed validation. Its own hash and the exact 19-file change inventory are in `cache/brief48/final-receipt.json`. All **706 live-pack hashes** and the live page hash match the initial snapshot.

Internal evidence only; no owner image was made:

| View | Before | After |
|---|---|---|
| Both plates, native 1× crop, logical rect `[70,570,340,710]` | `cache/brief48/full-before-crop-1.png` | `cache/brief48/full-after-crop-1.png` |
| Same crop, native @2× | `cache/brief48/full-before-crop-2.png` | `cache/brief48/full-after-crop-2.png` |
| Transparent bus-stop parent | `cache/brief48/bus-stop-before.png` | `cache/brief48/bus-stop-after-1.png` |

`cache/brief48/comparison-2.png` puts native @2× before above after. `loop-contact-{rear,front}-{1,2}.png` contains all decoded phases in 12×12 grids. `visual-review.md` records the inspected views. Reproduction and audit scripts, masks, source audits, pixel counts and decoded-loop crops are all under `cache/brief48/`.

No live browser playback is claimed. Zero remaining alpha/additive RGB at the removed plate footprints establishes that those slices cannot draw the rectangles over a vehicle or walker at any position or wet-sheet phase.

STATUS: COMPLETE — local `out10c/` delivered; both orphan plates removed; next-render sources fixed; live pack/page unchanged; stopped.
