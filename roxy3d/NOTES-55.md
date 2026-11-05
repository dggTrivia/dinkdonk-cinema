# Brief 55 — DINK DONK / CINEMAS cleanup, draft 23 only

Delivered **one owner image**, `qa10/draft23-dinkdonk-cinemas.png`, **1280 × 720**. Left: the preserved draft-22 capture. Right: the new draft-23 capture. Both show **state A**, the same logical crop **[1100, 0, 680, 560]**, and the same 640 × 527 comparison scale. Small labels only; no timing strip. The image was reopened and visually inspected at delivery size.

## Fixes and measurements

Screen-pixel measurements below refer to one 640-pixel-wide comparison panel. Clearances measure projected geometry edges, including tube/support thickness, rather than bloom. Negative support clearances indicate overlapping silhouettes. The final saved scene was reopened for verification.

| Fix | Draft 22 | Draft 23 |
|---|---|---|
| Subtitle tracking | 0.34 world-u | **0.27 world-u** |
| Subtitle width | 4.7175 world-u; 73.23% of title | **4.2975 world-u; 66.71%** of the 6.442-world-u title |
| Title-only centering | Center 8.98099995 world-u | Same center; measured discrepancy **0.000000238 world-u** |
| Cap height / color | 28.8 / 64 = 45%; cyan glass/core | **Unchanged**; measured cap ratio 0.450000345; same glass/core materials and tube sections |
| Baseline-to-lower-bulb-rail clearance | 12 logical px; baseline z284, rail z272 | **18 logical px**; baseline z284, rail **z266** |
| Connected lower structure | Lower truss z278 | **z272**; lower rail fasteners, bus wire, uprights, cross-brace connections, sockets, bulbs and local spill lights follow the extended frame; original sign roof anchors retained |
| Upright bulb count | 7 centers per side including shared corners | **9 per side**, adding **2 bulbs per upright**, each with socket, collar and local spill light |
| Upright pitch | 26.333 logical z units after the draft-22 extension; original pitch 19 | **20.5** uniformly; **7.89% above original**, within the 10% requirement |
| Clips per C / I / N / E / M / A / S | 4 / 6 / 4 / 6 / 5 / 5 / 3; 33 total | **3 per glyph; 21 total** |
| Mounting | One shared raceway plus heavy individual carriers and numerous arms | One continuous shared raceway at the lower truss, with connected carriers, short arms, standoffs, clips and insulated feeds |
| Shared raceway radius | 0.022 world-u | **0.009 world-u** |
| Individual carrier radius / maximum projected diameter | 0.013 world-u / 2.08 px | **0.0063 world-u / 1.01 px** |
| S central carrier | Local u offset +0.19; closest terminal clearance 1.78 px | Local u offset **+0.01**, a **−0.18-world-u shift relative to the glyph**; closest terminal clearance **5.56 px** |

The narrower tracking is applied to the original subtitle tube paths, preserving their glyph shapes. The S reads as S in the delivered image. The carrier offset above excludes the whole glyph's separate recentering movement.

Four supports around M/A/S were rerouted locally. The vertical posts retain their original roof and upper attachment points; the cross braces connect to the extended lower truss and retain their upper attachments. Their nearest edge clearances to M/A/S are:

| Existing support | Draft 22 | Draft 23 |
|---|---:|---:|
| Vertical truss `.003` | 7.35 px | **5.09 px** |
| Vertical truss `.004` | −4.03 px | **4.98 px** |
| Cross brace `.003` | −2.17 px | **4.95 px** |
| Cross brace `.004` | −2.17 px | **5.12 px** |

Tracking reduction alone would have reduced the first support's clearance to 3.40 px, so it was adjusted too. All four final clearances meet the requested 4–6 px band. Other original roof braces remain clear of M/A/S.

## Floodlights — one measured exception

Both fittings move as complete assemblies: roof shoe, yoke, housing, reflector, emitting glass, cable and actual lamp. Their roof height, lamp powers, colors and aim remain unchanged.

| Fitting | Movement at comparison size | Clearance from title/subtitle, before → after |
|---|---|---|
| Central/rear, `D13 truss reflector flood 1` | **53 px**, approximately 22.40 px right and 48.03 px up | Projected overlap with the O → **6.57 px** |
| Right/front, `D13 truss reflector flood 2` | **10 px down**, away from the sign | **68.09 → 77.06 px** |

**Exception to the suggested 8–12 px central movement:** the complete central fitting's projected silhouette sits within the O, and none of the tested 8–12 px translations clears it by 6 px. Searching whole-pixel distances at 5-degree angular increments first found a compliant placement at 53 px. This is the first feasible sampled radius, not a claim of a continuous mathematical minimum. Clearance uses a conservative convex outline of the shoe/yoke/housing/reflector/glass, subtracts the neon tube radius, and includes a 0.25 px sampling allowance. The saved-scene verification independently measures **6.5669 px**. The fitting remains anchored on the roof and is visibly separated from DONK in the final image.

The right compact fitting was already more than 6 px from the neon under this measurement; its requested 10 px downward move increases separation and takes it farther from the frame. This is a concrete measurement difference from the rough critique, rather than an invented pre-existing tube collision.

## Timing, capture and preservation

Bell timing stays **A12/B12**, **0.50 seconds per state**, no gap, **6 cycles in 6 seconds**, **144 frames at 24 fps**. The staged `timing.json` and `runtime-half-speed.py` are **byte-identical to draft 22**. This delivery is a state-A still; no animation or production pack was rendered or published.

The scene was loaded from **`cloud/bundle/scene.blend`**, never saved over. The historical helper was reused only to reconstruct draft 22 in memory before cleanup. Draft 22 remains in **`out10h/_work/`**; all new staging is in **`out10h/draft23/`**.

The camera matrix and orthographic scale **22.627416610717773** are unchanged. The native 3840 × 2160 render uses the same logical region **[1020, 0, 840, 650]**, seed 1701, 128 maximum / 64 minimum samples, adaptive threshold 0.02, OptiX denoising, Blackman-Harris width 2.5, retained HDR glare, AgX / Medium High Contrast / exposure +0.25. The @2x capture supplies the comparison directly through the same bicubic crop operation on both panels. No separate foreground-rain overlay is added.

**Final completed exposure: 64.19 seconds** on the local **NVIDIA GeForce RTX 3050 6GB Laptop GPU**, Cycles OptiX, CPU tracing fallback disabled. Scene construction, saving and the exposure/display exports reached the final PNG at **80.42 seconds** in the render log. The 64.19-second figure excludes setup, earlier interrupted attempts, verification and composition. Two earlier startup attempts entered the legacy helper's render dispatch during import and were interrupted; import dispatch is now explicitly disabled. No reference artifact changed, as confirmed by hashes. No cloud resources were used.

Verification passed:

- **162 title/emote objects** retain identical geometry, transforms and materials.
- All **139 existing lights** retain their powers, colors and aim. Four small local spill lights accompany the four added bulbs; the two requested floodlight assemblies change position.
- Both upright intervals measure 20.5 logical z units throughout; subtitle cap height, centering, three clips per glyph, S terminal clearance, support clearances and both fitting clearances pass the saved-scene checks.
- **7,480 protected files** match this task's starting hashes, with **zero changes and zero additions**: pre-existing pack payloads, the source scene, bundle Python sources and `../roxy.html`. All **28 draft-22 reference files** also match their starting hashes.
- Source SHA-256 before/after: `0fa1c86fb297079b0b0b1944cad5d9ae08f6a8babaf2bd558c9a43d35417ef24`.
- Owner image SHA-256: `99449a30d88f88362c9c3d1ebcde25a26bddfe5f03f81d04db822c99c9349122`.

Reproducible staging: `out10h/draft23/draft23-cinemas.blend`, `draft55.py`, `run.ps1`, `compose.ps1`, `cleanup-design.json`, `render-record.json`, `verification.json`, protected/reference hash baselines, render captures and logs. This staging is not a replacement live pack. All task writes are inside `roxy3d/`, limited to that staging folder, the requested owner image and this note.

STATUS: COMPLETE — draft 23 comparison and NOTES-55 delivered; central-fitting movement exception documented; A12/B12 timing unchanged; protected packs/source/page and draft-22 references unchanged; draft only; stopped.
