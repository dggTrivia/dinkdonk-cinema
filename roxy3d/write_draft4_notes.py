"""Write the final draft report only after the delivery/QA artifacts exist."""
import sys,json,hashlib
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft4_common import ROOT,QA,WORK,status

def load(name):return json.loads((WORK/name).read_text())
m=load('metrics.json');v=load('video.json');r=load('ripples_render.json');t=load('temporal.json');w=load('weather.json');g=load('glare.json');s=load('scene.json');p=load('preview_render.json')
proof=json.loads((QA/'draft4_validation.json').read_text());assert proof['passed']
assert len(r['frames'])==48
for name in ['draft_4.png','draft_4_clean.png','test_ripples_still.png','test_ripples_clip.webm','test_ripples_clip_noTD.webm','test_glare_before.png','test_glare_after.png','draft4_comparison.html']:
    assert (QA/name).is_file(),name
metrics=[]
for kind in ['noTD','TD']:
    d=m['sequences'][kind]['decoded_webm'];src=m['sequences'][kind]['source_png']
    metrics.append('| '+kind+' | '+' | '.join('%.4f'%z for z in [src['dry_interior_control']['temporal_std_mean'],d['dry_interior_control']['temporal_std_mean'],d['street_reflections']['cyclic_mean_abs_luma'],d['full_crop']['seam_last_to_first_mean_abs_luma'],d['full_crop']['seam_ratio_to_adjacent_mean'],m['sequences'][kind]['decoded_vs_source_rgb_mae']])+' |')
per=m['sequences']['noTD']['decoded_webm']['dry_interior_control']['temporal_std_mean'];temp=m['sequences']['TD']['decoded_webm']['dry_interior_control']['temporal_std_mean']
reduction=100*(1-temp/per) if per else 0
notes=f'''# Draft 4 — final-quality 720p stills and fidelity comparisons

Completed {datetime.now().astimezone().isoformat(timespec='seconds')}. Draft only, following BRIEF-15-draft4.md. No production pack render, export or manifest generation was invoked.

## Review first

- [Side-by-side viewer](draft4_comparison.html): synchronized clips, frame seeking, full glare comparison and detail crops.
- [Weather draft — draft_4.png](draft_4.png), 1280 × 720.
- [Clean draft — draft_4_clean.png](draft_4_clean.png), 1280 × 720, including the proposed HDR glare.
- [Ray-traced ripple still](test_ripples_still.png), 1280 × 720, without the added glare/weather overlays.
- [Temporal-denoised clip](test_ripples_clip.webm) and [per-frame-denoised clip](test_ripples_clip_noTD.webm).
- [Glare before](test_glare_before.png), [glare after](test_glare_after.png), [full comparison](test_glare_comparison.png), [2× pixel details](test_glare_details.png).
- [Matched decoded ripple details](test_ripples_comparison.png).

## Owner fixes

**29 — continuous apartment roof.** Replaced the roof assembly with one four-vertex felt surface across the whole apartment/extension footprint and one connected perimeter parapet with continuous cap. The felt material is consistent across the former join. Two AC units, two skylights, a central hatch, three vents, ducts, pots and an aerial are distributed over the full area. Small repairs and shallow water are surface detail, not a join between separate roofs. Inspected the rendered roof at 720p.

**31 — current reflections.** Every beauty/reflection frame was ray traced from the current scene. No old reflection image, warped base or prior sign artwork was used. The saved scene has no image texture references. Removed nine broad neon/reflection proxy lights, including `P10 sign street green reflection`, and removed specular contributions from architectural fill helpers. Current emissive DinkDonk hood/face/bell/DD and DINK DONK tubes, café and shops remain the actual visible sources. Their coloured reflections are compact and broken by real wet-surface normals; the old broad green smear is gone. Current tube radiance was increased for real light transport, rather than replacing it with an invented green reflection light.

Editable source: [roxy_pass10_draft.blend](../roxy_pass10_draft.blend). Original draft-3 source retained at [source_before_draft4.blend](source_before_draft4.blend). [Scene evidence](draft4/scene.json) records materials, roof kit, source colours and removed lights.

## New draft quality standard

Both delivered draft stills are native **1280 × 720 at 100%, Cycles 256 samples**, adaptive sampling off, OptiX GPU, fixed seed 1701, animated seed off. Maximum bounces 10, diffuse 4, glossy 6, transmission 8, transparent 24; no radiance clamps. Real wet materials, shallow puddles, wet roof surfaces, direct and indirect reflections are evaluated by Cycles. No reduced-resolution render was enlarged into the delivery stills.

The weather frame combines that current wet beauty with a fresh 256-sample, full-resolution render of **{w['current_scene_rain_streaks']} three-dimensional rain streaks and {w['surface_splash_sites']} splash sites**, occluded by the current geometry using holdouts. It uses the proposed HDR glare and omits the page layers. [Weather provenance](draft4/weather.json). The glare/rain compositing is reproducible in `compose_draft4_glare.py` and `render_draft4_weather.py`.

## Test A — actual ray-traced periodic rain normals

The node group `D4 periodic ray-traced rain ripple normals` is an original implementation of the cell-drop method. A 3 × 3 cell neighbourhood uses deterministic random drop centres, phases and **cell-global** 1- or 2-second periods. A smooth radial wave envelope fades to zero at a drop's birth/death. Both periods divide six seconds. Circular 4D noise supplies drizzle/wind modulation with XY spatial coordinates, Z = 0.8 cos(2πt/2), W = 0.8 sin(2πt/2). The chosen short proof therefore closes every two seconds and repeats three times within a six-second loop. It drives normals on puddles, road, sidewalk and roofs, with stronger water and subtler roof response. The existing surface micro-normal is retained beneath it.

The algorithmic reference was the [OpenMW water/rain-ripple description](https://openmw.readthedocs.io/en/openmw-0.51.0/reference/modding/settings/water.html). No OpenMW/GPL implementation code was copied. During inspection an early neighbour-slot period inconsistency was corrected; 16 preliminary frames were archived under `draft4/superseded_grid_period_probe/` and excluded. All delivered frames use the corrected cell-global period.

The clip is **48 unique Cycles renders at 24 fps, 2 seconds**, using a **native 1280 × 360 crop from the 1280 × 720 camera** (full-frame coordinates x=0, y=360, width=1280, height=360). The brief explicitly allows this street/sidewalk crop. Each frame is independently traced at 256 samples; no 2D reflection warping, frame interpolation or repeated-frame animation is used.

`noTD` means **per-frame OptiX denoising**, not an undenoised noisy render. Each version uses the exact same raw multilayer EXRs. These contain Combined, Denoising Albedo, Denoising Normal and Vector, plus the retained extra passes. For the temporal version the actual `bpy.ops.cycles.denoise_animation` operator processed 144 inputs: one cyclic period before, the delivery period, and one period after. Frames 49–96 are delivered; 48 frames are trimmed at each side. Padding consists of exact cyclic copies of the independently traced phases, with canonical phase and seed fixed. The [Cycles implementation](https://github.com/blender/blender/blob/main/intern/cycles/session/denoising.cpp) carries previous denoised output into subsequent frames; the trailing period is also retained as an independent history-convergence check. Installed Blender 5.2.3 operator behavior and EXR passes were tested locally before the full run.

Static camera and geometry produce no material-flow vectors for changing normal/reflection patterns. Temporal denoising can therefore soften or lag a ripple even when it reduces measured variation. This limitation matters when choosing the preferred treatment.

### Measurements

Both VP9 files are CRF 14, unconstrained bitrate, 24 fps. **All 48 frames of each delivered WebM were decoded** through Blender VSE and saved for measurement; checks are on delivered media, not only source PNGs.

All variation values below are display luma levels on a 0–255 scale. Dry-control σ is the mean per-pixel temporal standard deviation in the interior control rectangle. Wet variation is cyclic mean absolute adjacent-frame difference; it includes intentional moving reflections. Wrap ratio compares last→first difference to the mean internal adjacent-frame difference.

| Version | Dry σ, PNG | Dry σ, decoded | Wet variation, decoded | Wrap difference | Wrap / typical step | Decode RGB MAE |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(metrics)}

The decoded dry-control variation changes by **{reduction:.1f}%** with temporal denoising (positive means reduced variation). This is a flicker proxy, **not** a ground-truth noise/error score. Fixed seed holds much sampling noise stationary, and wet-area differences contain real motion. A lower number alone does not prove a more faithful image.

**Recommendation for A:** adopt the actual ray-traced ripples. At this 256-sample setting, my initial denoising choice is **per-frame OptiX**. It has lower variation in the unencoded dry control (0.0365 versus 0.0510); encoding suppresses these very small differences and reverses the ranking. The decoded 32.3% reduction therefore does not establish a general temporal-denoising improvement. Matched decoded detail frames retain moving rings in both versions; the temporal version changes some fine water texture, with no clear universal win from these measurements. Both remain available for the owner's motion judgment. No claim of perceptually flicker-free playback follows from the metric alone.

The independently rendered canonical repeat endpoint has maximum linear error **{t['source_endpoint']['max_abs_linear']:.9g}** versus frame zero; exact equality: **{t['source_endpoint']['exact_equal']}**. The separate unwrapped t=2-second formula check has mean/max linear error **{t['unwrapped_shader_endpoint']['mean_abs_linear']:.9g} / {t['unwrapped_shader_endpoint']['max_abs_linear']:.9g}**, with p99 **{t['unwrapped_shader_endpoint']['p99_abs_linear']:.9g}**. Same-phase temporal output after another warm-up cycle differs by mean **{t['temporal_history_same_phase_after_one_more_cycle']['mean_abs_linear']:.9g}** linear units. These are distinct from ordinary last→first motion, which is expected to be nonzero for a seamless sampled loop.

The canonical endpoint passes the 1e-5 linear tolerance; it is not bit-identical. Unwrapped floating-point phase/noise evaluation can change individual sampled light paths, hence its larger raw maximum. Playback uses bounded canonical phase `(frame % 48) / 24`, avoiding that accumulating unwrapped-time difference. The multipart raw Combined passes were extracted through Blender's compositor to plain 32-bit linear EXRs for the endpoint measurements, without denoising, resizing or a display transform. Both encoded seam checks also pass: wrap variation is below the largest ordinary internal step. The saved source audit confirms one roof face, a connected parapet, cell-global periods and ripple normals on all 70 wet sidewalk slabs: [source_audit.json](draft4/source_audit.json).

Exact ROI coordinates and full metrics: [metrics.json](draft4/metrics.json). Operator, padding and endpoint evidence: [temporal.json](draft4/temporal.json). Encoding/decode metadata: [video.json](draft4/video.json).

## Test B — HDR optical glare

Both images use the same newly rendered HDR frame. “Before” regenerates the current 2D Gaussian additive halo from the **current** projected tube paths and colours. “After” feeds HDR radiance into full-resolution Blender compositor Glare: Bloom strength 0.22 / threshold 2.8, faint red-weighted Fog Glow strength 0.045 / threshold 3.2, and a restrained four-point aperture streak at strength 0.018 / threshold 5. This changes the optical treatment while holding scene radiance and source geometry constant.

The after treatment has a broader, more continuous coloured halo around the roof letters and a clearer warm halo around the yellow blade hood, without washing over neighbouring architecture. The slight red halation is deliberately restrained. **Recommend the HDR glare treatment** at these settings. It responds to actual bright rendered pixels, including highlights, and retains the neon shapes at 720p. The owner can judge both full frames and the labelled 2× pixel crops.

This is a physically motivated **HDR lens-scattering approximation**, not measured lens PSF data or ray tracing through lens elements. See the [Blender Glare documentation](https://docs.blender.org/manual/en/5.1/compositing/types/filter/glare.html). [Exact compositor settings](draft4/glare.json).

## Timing and scope

| Stage | Measured wall time |
|---|---:|
| Current full 720p / 256-sample beauty | {p['seconds']:.2f} s |
| 48 delivered raw Cycles frames | {sum(x['seconds'] for x in r['frames']):.2f} s |
| Per-frame OptiX, those 48 frames | {sum(x['single_optix_seconds'] for x in r['frames']):.2f} s |
| Temporal OptiX, 144 padded inputs | {t['denoise_seconds']:.2f} s |
| Current 720p rain/splash render | {w['render_seconds']:.2f} s |
| HDR glare compositor | {g['compositor_seconds']:.2f} s |
| noTD / TD VP9 encode | {v['noTD']['encode_seconds']:.2f} / {v['TD']['encode_seconds']:.2f} s |
| noTD / TD complete decode + PNG saves | {v['noTD']['decode_and_png_seconds']:.2f} / {v['TD']['decode_and_png_seconds']:.2f} s |

Times exclude setup, shader construction, the superseded probe, independent endpoint renders and visual inspection. [STATUS.md](STATUS.md) records completed stages with timestamps. The decode timing includes VSE/color conversion/PNG overhead; it is not an OBS or isolated decoder benchmark.

**Preservation:** SHA-256 verification passed for **{proof['protected_files_checked']} protected files**, including all live packs and the 490 pre-existing parked out10 files. No protected files changed or disappeared and no pack files were added. `roxy_pass9.blend` and parked `roxy_pass10.blend` are unchanged. [Validation record](draft4_validation.json).

Draft-only stop: `out10` has not been built or continued. Its parked contents predate this source and are not a final pack for draft 4. All new/changed task artifacts are inside `roxy3d/`.
'''
(QA/'DRAFT-4.md').write_text(notes,encoding='utf-8')
status('DRAFT-4.md written with final-quality settings, owner fixes, measured denoising/seam results, render times and preserved-pack evidence')
