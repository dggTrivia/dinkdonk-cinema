# Brief 54 - DINK DONK / CINEMAS and half-speed bell (draft only)

Delivered **one owner image**, `qa10/draft22-dinkdonk-cinemas.png`, **1280 x 720**. Left is the current `out10/lit_bg@2x.png` phase-0 sign; right is the new local Blender render in state A. Both use logical crop **[1100, 0, 680, 560]**, displayed at 640 x 527. The small strip underneath shows every A/B hold over the unchanged six-second loop. No production pack or animation was rendered or published.

## Sign and source

Opened `cloud/bundle/scene.blend` read-only, following NOTES-50. Its SHA-256 before and after is `0fa1c86fb297079b0b0b1944cad5d9ae08f6a8babaf2bd558c9a43d35417ef24`. The historical builders were read for construction details and were not rerun over the production scene.

- CINEMAS uses the **same cyan wet-glass and luminous-core materials as DINK DONK**. Cyan makes the two lines read as one sign and leaves the warm bulbs and gold bell as accents. No new fill lamp or global lighting change was introduced; the new physical tubes emit, glow through the retained HDR compositor, and participate in ray-traced wet-surface reflections.
- The subtitle is centered on the actual DINK DONK tube-path bounds, excluding the emote. Cap height is **28.8 versus 64**, or **45%**. Wide tracking is 0.34 world-u between 0.3825-wide glyphs; subtitle width is 4.7175, against the title's 6.442. Measured center discrepancy after reopening the draft is only 0.000000238 world-u.
- Real tube curves have wet glass, a luminous core, ceramic clips, steel standoffs, short carrier arms, vertical carriers, insulated feeds and a shared cable raceway attached to the lower truss. These are scene geometry, not painted text.
- There was insufficient room inside the existing frame. The lower bulb rail moves from z_px **316 to 272**, with the lower truss from **322 to 278**; the top remains **430**. The lower fastening pieces and side frame extend with it, and the existing lower/side sockets, bulbs and their local spill lights follow the frame. Original footings remain on the roof. The existing sign is an open truss, so no opaque backing board was added.
- **162 original title/emote objects** retain identical geometry, transforms and active materials. All **139 existing lights** retain their types, powers and colors. Bulb positions follow the extended frame; the phase-0 chase levels remain unchanged. State A has five lit arm/bell tube paths; the seven B paths remain visible as dark glass.

The camera transform and ortho scale **22.627416610717773** are unchanged. Captures use the native **3840 x 2160** grid, Blackman-Harris width 2.5, OptiX denoising, seed 1701, **128 maximum / 64 minimum samples**, adaptive threshold **0.02**. The final sign exposure renders logical region [1020, 0, 840, 650], with generous margin around the owner crop, retaining the full-size canvas for the compositor. AgX / Medium High Contrast / exposure +0.25 and the production HDR glare are retained. The internal 1080p images use scene-linear 2x2 area reduction before display conversion. Neither comparison panel adds the separate foreground-rain video.

## Timing read from the production source

`cloud/bundle/runtime.py`, `Renderer.phase`, currently selects:

```python
state = 'A' if (frame % 48) // 6 % 2 == 0 else 'B'
```

`cloud/bundle/production.py` renders 48 background phases; `cloud/bundle/video.py` repeats them three times to encode **144 frames at 24 fps = 6 seconds**. The later Brief 45 alley video repair did not change the sign's six-frame alternation (`out10-loopfix/NOTES-45.md`).

| | Current | Proposed draft |
|---|---|---|
| A: arm/bell down | 6 frames, 0.25 s | 12 frames, 0.50 s |
| B: raised arm/bell | 6 frames, 0.25 s | 12 frames, 0.50 s |
| Dark gap | None | None |
| Complete A/B cycle | 12 frames, 0.50 s | 24 frames, 1.00 s |
| A/B cycles in 6 seconds | 12 | 6 |
| Six-second pattern | `(A6 B6) x 12` | `(A12 B12) x 6` |

With zero-based frames, the new pattern is A **0-11**, B **12-23**, repeated every 24 frames through B **132-143**. Frame **144** returns to A exactly as frame 0. Thus every hold doubles, the existing 48-frame production cycle still contains exactly two complete A/B cycles, and **no loop-length compromise is needed**. The wrap has the same B-to-A switch as every other cycle boundary.

The staged source changes only the bell selector divisor from **6 to 12**. Rain, ripples, bulb-chase phase and video playback rate remain on their existing clocks. Slowing the entire WebM would also slow those effects and is not the proposed implementation.

`out10h/_work/timing.json` records all 144 old/new states. The strip is drawn from these arrays. An AST-based check evaluates the original and proposed source expressions and verifies `new[f] == old[f // 2]` for every frame, plus 48-frame repetition and the frame-144 endpoint. `runtime-half-speed.py` is a staged source reference only; it has not replaced or run the production pipeline. This proves the schedule, not rendered animation playback.

## Production pass scope, if approved later

| Output | Required work |
|---|---|
| `base.png`, `bg.png`, both @2x | Recompute the per-channel cycle minimum from the new 48 lit background frames. They are coupled to the additive light loop. |
| `lit_bg.png`, `lit_bg_dry.png`, both @2x | Replace the phase-0 lit fallback and dry fallback from the updated scene. |
| `light_loop.webm`, `light_loop_2x.webm` | Render the updated 48 background phases, including new tube illumination/reflections and the 12-frame bell holds; subtract the matching new base, repeat x3, encode and decode-validate at 144 frames / 24 fps / 6 s. Preserve the approved 256/64/0.01 production sampling contract. |
| Occluders and `prop_loops/wet_*` | The sign itself belongs to **background**, so it does not require a new character occluder. Recapture foreground receivers affected by changed neon/bell reflections, with matching parent minima, depth slices and wet sheets. Existing 24 unique foreground phases doubled into 48 slots still place 12-slot bell boundaries exactly. Retain other foreground assets only after checking their lighting contribution. |
| `rain_fg.webm` | Refresh the rain holdout where the enlarged sign, tubes and mounts now occlude falling rain. The ordinary pipeline recaptures the 48 weather phases and repeats x3; rain timing stays unchanged. |
| `full.png`, `full@2x.png` | Recompose the new shipped layers and phase-0 rain; these are compositing outputs, not additional full beauty renders. Refresh any affected derived ad-frame crops. |
| Other assets and metadata | Vehicles, umbrella/vehicle rain, spray/wake, held items and independent prop rigs do not change. Reuse door/WC sheets only where their receivers show no changed contribution. Record CINEMAS in baked-sign metadata, preserve the layout and 6-second contract, and regenerate build fingerprints, checksums and validation. |

Do not replace the current pack with a historical rebuild: retain later approved taxi, bus-plate, door and rain repairs. A full background rerender also needs to preserve the Brief 45 alley-flicker fix: its source roof/body coplanarity was documented but repaired in the videos, so a fresh render must resolve that receiver ambiguity or reproduce and validate the repair. This draft does not alter that unrelated geometry.

**Estimated local production time: roughly 5-10 hours** on this RTX 3050 laptop for the conservative background/affected-foreground/weather refresh, encoding and checks. The measured full native background exposure below is **4.37 minutes at draft settings**: 48 such phases alone are about **3.5 hours**; allowing up to roughly twice the tracing work for 256/64/0.01 gives about **3.5-7 hours for backgrounds**, before weather, foreground and packaging. This is a planning range, not a measured production benchmark; adaptive sampling, persistent-data reuse, thermal behavior and the affected receiver set matter. A tightly scoped spatial update could be faster but needs separate validation. No production run was started.

## Measurements, verification and files

Local NVIDIA GeForce RTX 3050 6GB Laptop GPU, Cycles OptiX, CPU tracing fallback disabled. Completed tracing/exposure wall times, excluding display conversion and inspection:

| Internal capture | Seconds |
|---|---:|
| Matched original, full native background | 262.18 |
| Earlier subtitle crop, replaced after completing carrier-arm connections | 76.27 |
| Final subtitle crop | 64.58 |

Only the final comparison is owner-facing. The matched original and live crop were visually checked for registration and lighting. They are not byte-identical: draft sampling and the existing pack/source history produce mean absolute RGB difference **0.842/255**, p99 **14**, max **210** across the crop. The comparison does not claim production-quality pixel equivalence. The final image was reopened and visually inspected for readable lettering, framing, physical supports and labeled timing blocks.

- `qa10/draft22-dinkdonk-cinemas.png`: the sole owner deliverable image, verified 1280 x 720.
- `out10h/_work/draft22-cinemas.blend`: reproducible draft scene, state A, saved only here.
- `out10h/_work/draft54.py`, `run.ps1`, `compose.ps1`, `verify54.py`: local draft and QA scripts. The final capture is the `refine` mode.
- `out10h/_work/runtime-half-speed.py`, `timing.json`, `design.json`, `final-render-record.json`, `verification.json`, raw EXRs and logs: internal implementation and evidence. `out10h` is not a publishable pack and has no replacement live manifest.

The preservation check covered **7,480 pre-existing files**: payloads under every existing `out*` directory (excluding their internal `_work` trees), the production scene, bundle Python sources, and `../roxy.html`. **All 7,479 pack/source files match their baseline hashes**, with no new files in those protected sets. The only mismatch is `../roxy.html`, which changed during the concurrent lobby work recorded in PROGRESS.md. **This task made no writes to that page and did not restore or overwrite the concurrent change.** All task writes are inside `roxy3d/`, limited to the new `out10h/` staging, requested owner image and this note. No cloud resources were used.

STATUS: COMPLETE - draft 22 owner comparison and timing strip delivered; NOTES-54 written; 6-to-12-frame bell schedule verified; production packs and source unchanged; no page writes by this task; draft only; stopped.
