# Brief 49: compact taxi roof light, draft 16

STATUS: COMPLETE — draft staged in `out10d/`. The single owner image is `qa10/draft16-taxi-sign.png`, **1280 × 720**. The live `out10/` pack and `../roxy.html` are unchanged. All writes stayed inside `roxy3d/`; all 3D renders used the local RTX 3050 through OptiX. No cloud work or full-scene render.

## Dimensions and source changes

Both `build_vehicles.py` and `cloud/bundle/build_vehicles.py` now build the smaller sign. Only their taxi-sign branches changed; each copy retains its existing unrelated source differences. The approved draft-15 studio lighting and all material definitions are unchanged.

| Part | Before | Draft 16 |
|---|---:|---:|
| Luminous box, length along car | 0.34 tiles | **0.12 tiles** |
| Luminous box, width across car | 0.46 tiles | **0.32 tiles** |
| Luminous box, height | 9 scene units | **5 scene units** |
| Black mounting base, length × width × height | 0.38 × 0.49 × 1.4 | **0.15 × 0.35 × 1.2** |
| Box bottom / top | z 34 / 43 | **z 34.2 / 39.2** |
| Clearance from steel roof top to luminous box | 1.2 units | **1.4 units** |
| Front and rear text size | 0.13 | **0.075** |
| Box bevel | 0.013 | **0.006** |

The car body is **1.72 × 0.70 tiles**; its steel roof is **0.54 × 0.526 tiles**, with its top at z **32.8**. The new box follows the brief's numerical example: its length is **7.0% of the car length / 22.2% of the roof length**, and its width is **45.7% of the car width / 60.8% of the actual steel-roof width**. Its roof footprint falls from **55.1% to 13.5%**. Compared with the old box, it is **64.7% shorter, 30.4% narrower, and 44.4% lower**.

The mount sits directly on the roof; the luminous box starts 0.2 units above the mount. Front and rear lettering is centred at z 36.7. Measured glyph bounds are approximately z **35.307–38.179**, leaving about **1.11 / 1.02 units** below / above. Both faces read `TAXI` in the native 2× inspection. The warm sign material retains RGB **(1, .68, .21)** and emission strength **1.8**.

Vehicle-only studio settings remain: overhead **0 W**, warm script reflection **8 W**, cyan reflection **11.2 W**, warm street fill **6.8 W**, world strength **.015**. Vehicle lamps and their positions are retained. The published manifest is byte-identical, including the conservative 43-unit height and the existing canvases, anchors and depth contracts.

## Body and light rendering

Rendered only the four taxi body states: **+u / -u, closed / open**. Reused the Brief 47 native camera-grid and packaging route: **3840 × 2160**, the existing **610 × 400 logical working crop**, AgX / Medium High Contrast, exposure **+.25**, Blackman-Harris width **2.5**, adaptive maximum **256** / minimum **64** samples, threshold **.01**, OptiX denoising. The 1× body is derived by the production **linear 2×2 reduction before display conversion**; both sizes retain the production contact-shadow formula.

Current position AOVs were captured with those body renders. Existing ownership is retained on compatible surfaces; newly covered antialiased pixels use the current AOV, with the usual ground-position fallback for shadows. The entire old sign/base footprint also uses the current AOV because shrinking the sign reveals different roof surfaces. This corrects **615 owner pixels at 1× and 2,399 at 2×**, across the four states, without changing slice rectangles or offsets. Every slice set reconstructs its whole body exactly.

**The separate light maps do contain the old roof-sign reflection.** It is the yellow patch on the wet-road receiver, not a direct image of the sign at roof height. A matched old-sign emission-on / emission-off diagnostic held geometry, other lamps, materials and seed fixed. In the +u road-reflection rectangle `[85,94,134,125]`, disabling only sign emission removes up to **91 / 92 channel values at 1× / 2×**, with **1,254 / 5,022 pixels** differing positively by more than five levels. See `cache/brief49/sign-emission-proof-2.png` and `light-validation.json`.

Therefore all **32 taxi light PNGs** were refreshed consistently: normal, brake, indicator and indicator-only, for all four states at both resolutions. This used **12 native road-light renders**, plus the **two diagnostic renders**. Normal/brake/indicator use the production road receiver, lamp powers, finite fade, lens halos and brake/indicator delta formulas. Indicator-only is regenerated as `max(indicator - normal, 0)`. All reduced 1× render buffers use the same linear reduction. World and studio sources are off for these road-light passes, as in the production recipe; the warm sign emission remains on. All **48 other vehicle light PNGs** are unchanged.

Measured body render/AOV time: **6.29 s**; body setup, display conversion and initial packaging: **9.23 s**. Production road-light captures: **63.02 s**; diagnostic captures: **10.15 s**. These are render-stage measurements, not total task duration.

## Staging pack and verification

`out10d/` is a copy of the current live `out10/`, retaining the applied draft-15 lighting/door changes, the curb-plate removal and the Brief 45 loops. It contains the same **706 files**. Exactly **58 differ**:

- **8 whole-body PNGs:** `vehicles/taxi_{plus,minus}{,_open}{,@2x}.png`.
- **16 depth-slice PNGs:** `vehicles/slices/taxi_{plus,minus}{,_open}_{00,01}{,@2x}.png`.
- **32 light PNGs:** `vehicles/taxi_{plus,minus}{,_open}_light{,_brake,_indicator,_indicator_only}{,@2x}.png`.
- `validation.json` and `checksums.json`.

The other **648 files are byte-identical**, including `manifest.json`, all static plates, door sheets, foreground/wet sheets, other vehicles and both live light-loop WebMs. The exact changed-file inventory is in `cache/brief49/final-receipt.json`.

Independent checks passed:

- **8 slice reconstruction checks:** zero RGBA channel error, zero overlapping nonzero-alpha pixels, zero clipped sprite-edge pixels.
- Current-AOV ownership agrees throughout the changed geometry region at both sizes; published slice dimensions, depth intervals, offsets and anchors are preserved.
- All whole bodies exactly match their production display buffer plus contact shadow and original crop.
- All **698 PNGs** retain their dimensions; all **698 unique manifest asset references** resolve.
- Brake and indicator additions are nonnegative; `normal + indicator-only` exactly reconstructs indicator. Every taxi light map has black outer edges.
- Both source files parse, have identical taxi-sign branches, and differ from their respective backups only in that branch. Studio lighting and materials are unchanged.
- All **705 checksums** verify, covering every other pack file, including hidden files and the refreshed validation. The checksum file excludes itself; its own SHA-256 is in the receipt.
- All **706 live-pack hashes** and the live-page hash match the initial snapshot.

The owner image uses native 2× panels without rescaling: **before | after**, +u above -u, small labels only. The +u centre is **(6,11)**; the -u centre is **(6,12.75)**, identical before and after. Composition uses the live base plus decoded live light-loop frame 0, the appropriate road-light map with saturated plus-lighter, then taxi slices and foreground/wet layers sorted by the page's depths. The reused loop decode's source hash matches the current live WebM. Panel pixels are checked against the composed buffers exactly.

Visually inspected the final owner image, native sign lettering in both directions, all four body states including both open doors, and the old-sign emission diagnostic / new road-light map. This is a composed-still and asset validation; no live-browser playback test is claimed. Internal scripts, backups, render logs, measurements and checks are under `cache/brief49/`.

STATUS: COMPLETE — draft 16 and `out10d/` delivered for review; live pack/page unchanged; stopped.
