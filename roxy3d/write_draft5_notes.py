import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft5_common import *
def j(name):return json.loads((WORK/name).read_text())
scene=j('scene.json');water=scene['water_summary'];audit=j('source_audit.json');metrics=j('metrics.json');video=j('video.json');pres=j('preservation.json');preview=j('preview.json');weather=j('weather.json');render=j('sparkle_render.json')
assert audit['passed'] and pres['passed'];assert preview['source_sha256']==audit['source_sha256']==render['source_sha256']
rows='\n'.join('| '+a+' | '+b+' |' for a,b in [
('YEE / PEPE turf war','Layered purple and green paint on the service-shutter paste-up panel, a buff patch and an original tiny dinosaur.'),
('ABSOLUTE CINEMA','Chrome-coloured throw-up and two outline hands on the cinema service wall; no face.'),
('WHIPLASH — IN 5 MIN','Replaces the interior programme board; grooved felt, cream letters, a tilted yellowed 5 card and tape marks.'),
('GLORP!','Interior framed B-movie one-sheet; antennaed green cat above the city, halftone and one gold cat in the crowd.'),
('WCAT & ASSOCIATES','Faded rooftop law-firm billboard with an original folded-arms cat in a navy suit.'),
('Nothing ever happens','Shelter travel lightbox with palms, suitcase and the small-print reversal.'),
('PICK ONE','Scuffed shelter call box, two physical red/blue buttons, taped note and tiny drawn green option.'),
('FROGS vs DINOS','Red/gold boxing advertisement on the parked bus with original green/purple glove art.'),
('CLIPPED & SHIPPED','Brown/yellow courier panel beside the boxing ad, box icon and Mondays & Fridays wording.'),
('LOOKALIKE CONTEST','Weathered street-wall flyer showing a generic person and a floor lamp.'),
('RE-ELECT THE CONDUCTOR','Three two-colour posters on the street wall above the shelter, with a cap silhouette; one is physically half torn.'),
('CABGE — fresh daily','Greengrocer sign, soaked awning and crates of green cabbages with exactly one red cabbage.')])
text=f'''# DRAFT 5 — Brief 16

Completed {datetime.now(timezone.utc).isoformat(timespec='seconds')}. **Draft only. No out10 build or continuation.**

Built from the preserved draft 4 scene, `qa10/source_before_draft5.blend`. Editable current source: `../roxy_pass10_draft.blend`. The final source SHA-256 is `{audit['source_sha256']}`.

## Review files

- [Draft 5 weather still](draft_5.png) and [clean counterpart](draft_5_clean.png), both native 1280 × 720.
- [Water coverage map](water_coverage.png), including AC, shelter and alley detail views.
- [Sparkle clip](test_sparkle_clip.webm): 1280 × 360, 48 unique frames, 24 fps, 2 seconds, VP9 CRF 14.
- [Side-by-side review](draft5_comparison.html): synchronized Draft 4 per-frame-denoised baseline and Draft 5; frame seeking, current sparkle on/off stills, the coverage map and detail renders.
- [The twelve original artwork sources](draft5_approved_art.png). Fine print is intended for the close review views, not universal readability in the 720p overview.
- In-world details: [shelter and parked bus](draft5/shelter_bus.png), [alley](draft5/alley.png), [service-wall art](draft5/service_art.png), [unobstructed high-angle art view](draft5/service_art_front.png), [AC/skylights](draft5/rooftop_ac.png), [interior](draft5/inside.png), [billboard](draft5/billboard.png), [CABGE](draft5/cabge.png).

## 32 — Wet road, paving and roofs

The road now combines rough, varied asphalt grain with a separate directional wet reflection lobe. Its strength varies spatially, and both its roughness and normals break up the reflected light. The explicit tangent connection aligns that lobe in the camera's ground-depth direction. The former crisp reflected sign is no longer copied onto a nearly smooth road. Existing shallow puddle objects remain localized, with stronger ring normals than the surrounding felt and paving.

Draft 4's ray-traced periodic ripple node group is retained. The road keeps its 0.42 ripple strength; localized water uses 0.85, and other wet paving/felt uses the gentler response. The film and aggregate have separate roughness, with directional fine rain normals layered over the existing ripple field. There is no resampled reflection plate, 2D reflection basis or reflection-only proxy light added by this pass.

The parked bus was moved slightly along the stop to expose the DD blade's reflected light. Actual current geometry and lights produce the reflections. The small-source reflections are restrained, broken streaks; their colours mingle where bus lamps, warm signage and cool street lighting overlap.

Material limit: this is a calibrated layered BSDF approximation, not a measured water-film thickness or fluid solver. The wet-lobe coverage is 0.14–0.34, with a two-sided Schlick angle term. The camera remains the established dimetric view. Early reflection probes are retained under `draft5/probe_*.png` as development evidence; they are not delivery stills.

## 33 — Surface water audit

The audit checks both sides of mesh polygons because legacy boxes have inward winding. It tests several points against a static BVH of actual evaluated scene geometry. The upward slope threshold includes the steep folded parasol. Interior cutaway surfaces, section edges, the sky and atmosphere, and sky-occluded faces are excluded from falling-impact placement.

**{water['audited_objects']} exposed objects / {water['exposed_upward_polygons']} upward polygons** were assigned a material-specific wet response. The audit records **{water['unhandled_exposed_objects']} unhandled objects among those exposed candidates**. The complete per-object list and exclusions are in [scene.json](draft5/scene.json). Named checks explicitly require the shelter steel roof, both apartment AC cases, both apartment skylights, café awning, folded parasol, dumpster lid and fire-escape landing.

| Surface | Response |
|---|---|
| Water / puddles | Retained expanding ring normals; fine transient impacts. |
| Asphalt / paving / felt | Aggregate or felt grain, varied wet sheen, thin-film response, ring normals and micro-impacts; localized puddles retain stronger rings. |
| Metal | Beads and small crown geometry, edge droplets and runoff. AC cases, fans, ducts, sign boxes, shelter roof, dumpster lids, railings and fire escapes are included. |
| Glass | Beads and runnels on skylights. Shelter glazing has an explicit wind-facing treatment beneath its overhang: 32 beads and 11 downward runnels. |
| Fabric | Darkened soaked canvas and hem drops on awnings and folded parasol. |
| Caps / sills / ledges / walls | Sheen, splash details, edge drops and vertically stretched runoff staining. |

The final scene contains **{sum(water['static_beads_by_material'].values())} sampled surface bead sites**, **{water['splash_crowns']} crown paths**, and **{water['edge_drips_and_runnels']} edge-drip/runnel paths**, plus the explicit shelter glass treatment. These are sparse physical water details sized for this camera, not a fluid simulation. The coverage map and the rendered closeups are the visual evidence for the named targets.

## 34 — Intentional small-drop sparkle

There are **{water['micro_impact_sites']} deterministic impact sites** on actual exposed wet surfaces. The droplets use nonemissive dielectric water, four radii and short smooth growth/decay envelopes. They catch existing scene lighting. Their support is in world space on the treated surfaces; there is no uniform image-noise overlay. Density follows the heavy-rain treatment and surface area, with fewer impacts on small solid fittings. The still uses phase zero.

The sequence uses an analytic 2-second phase, shared with the retained ripple clock. The independently audited mesh at phase 0 and phase 2 is bit-identical. Per-frame OptiX cleans the render while the modeled glints remain. [Sparkle-off control](draft5/sparkle_off.png) uses the current materials, current camera and the same fixed render seed, with the micro-impact droplets collapsed to zero size while preserving object/light-link membership. The earlier hidden-object control affected roof lighting and is retained only as `superseded_hide_object_control.png`, not used for the A/B.

The requested old/new video comparison includes all Draft 5 changes. It therefore is **not** an isolated denoising or sparkle-only A/B test: materials, surface details, bus, art and HDR glare also differ from the old clip. The current-scene on/off stills provide the narrower control.

## 28 — Approved community art

All twelve are implemented as original procedural artwork generated by `make_draft5_art.ps1`, packed into the blend and mapped onto real wall/sign/paper geometry. No external meme pictures, real logos or real-person likenesses were used. Artwork has wet paper/paint shaders, physical perspective and scene lighting; pasted posters have lifted corners and one torn copy. All fourteen artwork instances also pass a backing-surface ray check; see [art support](draft5/art_support.json). The old shop lettering was removed so CABGE is clear.

| Approved item | Implementation |
|---|---|
{rows}

One parked bus is modeled for this draft review. No vehicle sprite pack or production manifest was generated.

## Quality and validation

- Cycles / OptiX GPU, **256 samples**, adaptive sampling off, fixed seed 1701, animated seed off. Native 1280 × 720 camera; the clip is its lower-half crop, without resizing.
- 10 total bounces / 6 glossy / 8 transmission / 24 transparent; no direct/indirect radiance clamp. Current HDR bloom, small optical streaks and mild halation use the Draft 4 settings.
- The clean overview took {preview['seconds']:.1f} seconds. The {weather['airborne_streaks']} airborne rain streaks are newly rendered with current-scene holdouts, then composited over this current clean frame. Surface water is already present in the beauty render.
- All 48 delivery frames were decoded. Encoded file: {video['bytes']:,} bytes, SHA-256 `{video['sha256']}`.
- Independent canonical rendered endpoint: mean RGB difference **{metrics['canonical_endpoint']['mean_0_255']:.6f}**, maximum **{metrics['canonical_endpoint']['max_0_255']:.0f}** on a 0–255 scale. This is a same-phase check, not a demand that consecutive loop frames be identical.
- Decoded wrap mean difference **{metrics['decoded_wrap']['mean_0_255']:.6f}**, versus ordinary-step mean **{metrics['ordinary_step_mean']:.6f}** and maximum **{metrics['ordinary_step_max']:.6f}**. Wrap / largest ordinary step: **{metrics['decoded_wrap_to_max_step']:.3f}**.
- Decoded RGB range: {metrics['decoded_min_channel']}–{metrics['decoded_max_channel']}. Compression mean absolute RGB error: **{metrics['compression']['mean_0_255']:.6f}**. Wet street temporal standard deviation: **{metrics['wet_street_temporal_std']:.6f}**; dry interior ROI: **{metrics['dry_interior_temporal_std']:.6f}**. These are 8-bit image metrics, not perceptual scores.
- Saved-source audit: twelve approved concepts, packed originals, exactly one red cabbage, **zero indoor/sky micro-impact sites**, nonemissive micro-impact material, named coverage targets and exact canonical impact geometry all pass. See [source audit](draft5/source_audit.json) and [frame metrics](draft5/metrics.json).
- **{pres['protected_files']} protected files remain byte-identical**, with no new files in any output pack. `out10/` remains parked and untouched. See [preservation check](draft5/preservation.json).

## Review limits / stopping point

All requested draft deliverables are present. Tiny artwork copy and the smallest droplets need the closeups to inspect; the overview intentionally keeps their in-world scale. Some bright glints merge under denoising/compression, which is why the decoded clip and magnified contact sheet are included. Rain is a deterministic procedural visual model, not a hydraulic simulation. No final-pack acceptance, production loop rebuild or layout-3 manifest is claimed.

The stills, in-world detail renders, source artwork, coverage map and sampled decoded motion frames were visually inspected. Rendering and validation stop here for owner review.
'''
(QA/'DRAFT-5.md').write_text(text,encoding='utf-8')
status('DRAFT-5.md written with owner requests, artwork placements, quality settings, water audit, periodicity/compression measurements and protected-pack evidence')
