# Render speed: same look, less time

Researched 2 Nov 2026 for Blender 5.2.3 / Cycles / OptiX on a laptop RTX 3050 6 GB. Nothing here drops ripples, rain, reflections or the 256-sample look. **[unverified]** = not confirmed by an official source or not measured on our scene. All speed-ups are estimates for OUR pipeline until measured.

## Options at a glance

| # | Option | Est. speed-up (our loop) | Quality risk | Effort | Cost |
|---|---|---|---|---|---|
| 1 | **Wet + rain layer only per frame** (holdout everything dry, add to a static "dry" plate) | 2-4x per frame **[unverified, depends on wet-pixel share]** | measurable (edges, denoise) | medium | 0 |
| 2 | One Blender process for all frames + **Persistent Data** | 5-15% on loops; large on 10-15 s sprites (mostly startup) **[unverified]** | none | low | 0 |
| 3 | Adaptive sampling (max 256, threshold ~0.01, min ~64) if currently off | 15-40% **[unverified]** | measurable | low | 0 |
| 4 | 48-frame loop (2 s cycle) x3 instead of 144 frames | 3x | none if rain also loops at 2 s | low | 0 |
| 5 | Cloud RTX 4090/5090 (RunPod, Vast.ai) | 7-10x vs laptop **[unverified]** | none | low-medium | ~USD 0.30-0.90/GPU-h list |
| 6 | Bake static AO/Bevel/procedural masks in wet shaders to textures | 5-40% **[unverified]** | measurable (texel res) | medium | 0 |
| 7 | Bake ripple normals to an image sequence | 0-15% **[unverified]** | measurable | medium | 0 |
| 8 | Test-and-keep lower bounces (glossy 6, transmission 8, transparent 24) | 0-20% **[unverified]** | none if under noise floor | low | 0 |
| 9 | OIDN (GPU, Accurate prefilter) instead of OptiX denoiser, then try 160-192 samples | 0-35% **[unverified]** | measurable | low | 0 |
| 10 | Larger tile size (whole frame) when VRAM allows | 0-10% **[unverified]** | none | low | 0 |
| 11 | Baked lightmaps for dry objects in reflections | 1.2-2x on layer 1 **[unverified]** | visible (view-dependent gloss lost) | high | 0 |
| 12 | Laptop power/thermal settings (plugged in, max-performance mode) | 0-20% **[unverified]** | none | low | 0 |
| - | Rejected: path guiding (CPU only), Filter Glossy up / caustics off / lower clamp (changes the look), several instances on one 6 GB GPU (no gain, VRAM out of memory) | - | - | - | - |

## 1. Cycles settings

Sources: [Blender 5.2 manual, Sampling](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html) unless noted.

- **Adaptive sampling:** Noise Threshold stops sampling a pixel once it is clean enough (typical 0.1-0.001). With max 256 it only removes samples. Keep the seed fixed (not animated) so static parts do not boil.
- **Light tree:** keep it on. It cuts noise with many lights (neon) at a little time per sample.
- **Path guiding:** the 5.2 manual still says "CPU rendering only". A GPU prototype (r/blender, 24 May 2026) has very high memory use and was up to 23x slower on glass.
- **OptiX vs CUDA:** keep OptiX. The RTX 3050 6 GB Laptop scores a median of 68 s with OptiX vs 110 s with CUDA (Blender 3.3 Classroom; [Notebookcheck](https://www.notebookcheck.com/GeForce-RTX-3050-6GB-Laptop-GPU-vs-GeForce-RTX-3070-Ti_11576_11450.247532.0.html)).
- **Persistent Data:** keeps BVH, modifiers and textures between frames, at a memory cost ([rB50782df4258](https://developer.blender.org/rB50782df4258)). It helps only when one process renders many frames, and it saves sync time, not sampling time. Watch VRAM at 4K.
- **6 GB VRAM:** the 5.2 texture cache "significantly reduces memory usage and startup time" at a small render cost ([5.2 notes](https://developer.blender.org/docs/release_notes/5.2/cycles/)). Avoid Simplify > Texture Limit, because it changes the look.
- **Tile size:** "Use Tiling" was removed in 5.0; a tile at least the frame size means no tiling ([5.0 notes](https://developer.blender.org/docs/release_notes/5.0/cycles/)). At 4K, try 4096 and fall back to 2048 on out-of-memory.
- **Denoiser:** in 5.2, Prefilter and Quality apply to OIDN only, and "Automatic" prefers OIDN over OptiX ("typically the highest quality"). Fewer samples is still a trade, so accept it only if the noise-floor test passes.
- **Expensive nodes:** an AO node in a shader roughly doubled one user's render time (6 min to 3:30 after removal; r/blenderhelp, 19 Nov 2025). Wet masks often use AO, Bevel or Pointiness. Bake the static ones (option 6).

## 2. Render only what changes

- **Option 1 (main win):** this splits the image into two layers that add up exactly.
  1. **Dry plate (once per resolution):** set the wet surfaces and rain to Holdout. Holdout objects still cast shadows and appear in reflections ([T70668](https://developer.blender.org/T70668)). Turn Film > Transparent on, or holdout does nothing ([T99179](https://developer.blender.org/T99179)).
  2. **Per frame:** set every dry collection to Holdout and leave wet surfaces and rain visible. Use a fixed seed, and crop the render border to the bounding box of the wet regions.
  3. **Combine:** final = plate + frame, adding premultiplied RGBA. Render the background/world into the plate.
  4. **Glare:** turn compositor glare off in both renders. Apply it once to the summed EXR in a compositor-only pass, because glare must see the whole image. One r/blenderhelp thread found that the "noise" on a wet floor came from the flare filter, not the render (17 Mar 2023).
  - Dry pixels end at the first hit and converge at once under adaptive sampling, so cost scales with the wet-pixel share.
- **Crop:** 37 s for 1280x360 vs 65 s for full 720p suggests about 9 s of fixed per-frame overhead (extrapolated), which options 1 and 2 remove. Cryptomatte helps build and check masks but saves no time.
- **Lightmaps (option 11):** baked light is view-independent, so glossy props seen in puddles lose highlights. Last resort.
- **Ripple image sequence (option 7):** saves shader evaluation only, not ray tracing. Worth it only if the ripple shader is heavy ([Dynamic Paint wave bake, BlendSwap 2014](https://www.blendswap.com/blend/12049)).
- **Diffuse/glossy split:** Cycles computes all passes together, and ripples also change diffuse shading. Option 1 does the job without this error.

## 3. Extra hardware

| Option | Notes | Fit |
|---|---|---|
| **RunPod** | RTX 4090 about USD 0.34/h community, 0.69-0.89/h secure, list prices mid-2026, VAT basis not stated ([runpod.io/pricing](https://www.runpod.io/gpu-cloud/pricing); [Hostinger 2026](https://www.hostinger.com/tutorials/?p=158956)) **[unverified today]** | Good |
| **Vast.ai** | RTX 4090 typical about USD 0.29-0.52/h, RTX 5090 about 0.34-0.75/h, marketplace prices ([computeprices](https://computeprices.com/providers/vast/gpus/rtx4090)) **[unverified]**. Community hosts are third parties, so check data sensitivity first. | Good |
| **SheepIt** (free) | Rendering earns 38 points per render minute, ordering costs 10. Contributing needs Blender 5.1+. Owners cannot run scripts. EXR max 4096x2160 ([FAQ](https://www.sheepit-renderfarm.com/faq)). Our .blend goes to strangers' machines. | Backup only |
| Flamenco 3 | Free, GPL-3, job queue for your own machines ([flamenco.blender.org](https://flamenco.blender.org/)); no gain with a single laptop | No |
| Crowdrender | Last listing supports Blender 3.0-4.2 ([Superhive](https://superhivemarket.com/products/distributed-rendering-addon/docs)) | No |
| Several instances on one GPU | No official benchmark; forum reports mixed or worse results ([BlenderArtists](https://blenderartists.org/t/dual-gpus-for-rendering-in-cycles/1506532)). Two scenes do not fit in 6 GB. | No |

**Speed:** Open Data medians are RTX 4090 about 11,000-11,700 and RTX 5090 about 15,000 ([Spheron, 20 Oct 2026](https://www.spheron.network/blog/blender-cloud-rendering-gpu/); [Renderjuice](https://www.renderjuice.com/gpus/compare/rtx-4090-vs-rtx-5090)), against about 1,470 for a desktop RTX 3050. That makes a cloud 4090 roughly 7-8x faster than our laptop **[unverified]**.

**Headless in the cloud:** pack the scene (`bpy.ops.file.pack_all()`), upload it with rsync/scp, and use the same Blender 5.2.3 Linux build. Then run `blender -b scene.blend -P pipeline.py -E CYCLES -o //out/f_#### -s 1 -e 48 -a -- --cycles-device OPTIX`. Set Overwrite off and Placeholders on so a spot instance can resume, and stop the pod when done.

## 4. GitHub tools (checked 2 Nov 2026)

| Repo | Stars | Last push | Licence | Use |
|---|---|---|---|---|
| [LogicReinc/LogicReinc.BlendFarm](https://github.com/LogicReinc/LogicReinc.BlendFarm) | 533 | 2 Feb 2025 | GPL-3.0 | LAN farm, split frames; 5.2 support **[unverified]** |
| [MKlimenko/PseudoRenderingFarm](https://github.com/MKlimenko/PseudoRenderingFarm) | 19 | 7 Aug 2026 | GPL-3.0 | Multi-instance on one PC; gains reported for EEVEE |
| [jeinselen/Blender-RenderKit](https://github.com/jeinselen/Blender-RenderKit) | 41 | 19 Sep 2026 | none detected | Render-region controls, autosave |
| [n4dirp/Render-Commander](https://github.com/n4dirp/Render-Commander) | 0 | 22 May 2026 | GPL-3.0 | One instance per device |

No maintained frame-diff or caching tool found. Scripting option 1 in plain `bpy` is simpler.

## 5. Reddit opinions

Atom feeds (two 429s), comments via [Arctic Shift](https://arctic-shift.photon-reddit.com).

- Noise threshold (r/blenderhelp, 24 Jan 2022): the top answer (51 points) saw no difference and picked the faster setting.
- Persistent Data (r/blender, 3 Nov 2025; 13 Mar 2024): it skips the BVH rebuild per frame, not sampling. It can max out VRAM, so render to single files to make crashes resumable.
- SheepIt (r/blender, Mar-Sep 2026): free and liked, but small (about 600 machines) with queue delays.

## Recommended plan

Baseline first: render frame 1 at 720p twice with seeds A and B. The **noise floor** is the per-pixel difference between them. A change counts as "same quality" if its difference from seed A is at or below the noise floor (mean and 99th percentile), with no visible structure in a 10x-amplified difference image. Compute it with numpy inside Blender on linear EXR, glare off.

1. **One process + Persistent Data + one tile** (option 2, 10). V: the same frame should come out pixel-identical with the same seed; log the time per frame.
2. **Adaptive sampling** max 256, threshold 0.01, min 64 (option 3). V: noise-floor test on 3 frames (puddle, neon, rain).
3. **Bake static shader masks** (option 6). V: noise-floor test plus an A/B of the baked mask image.
4. **Two-layer split, plate + wet/rain** (option 1), with glare applied afterwards. V: the sum against a full render at the same seed should pass the noise-floor test. Also inspect alpha edges at 400%.
5. **48-frame loop** with ripples and rain both on a 2 s period (option 4). V: the difference between frame 48 and frame 0 (wrapped) should match the difference between neighbouring frames.
6. **Bounce test** (option 8). V: the noise-floor test per setting. Keep a lower value only if it passes.
7. **OIDN at 192 samples** (option 9), optional. V: the noise-floor test plus a 48-frame flicker check.
8. **If it is still too slow, rent a 4090** (option 5) for the 4K pass. V: render one frame locally and in the cloud with the same seed, Blender version and denoiser; they should match within the noise floor.

**Time estimate [unverified]:**

| | Now | After steps 1-5, locally | Cloud 4090 |
|---|---|---|---|
| 144-frame loop, 1080p + 4K | about 16 h | about 4-5 h | about 2 h (about USD 1-2) |
| 48-frame loop x3, 1080p + 4K | about 5.4 h | about 1-2 h | about 15 min |
| Stills, sprites, vehicles (with step 1) | about 45 min | about 30 min | - |
