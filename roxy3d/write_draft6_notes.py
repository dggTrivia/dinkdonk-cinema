from pathlib import Path
from datetime import datetime
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft6_common import *
v=json.loads((WORK/'validation.json').read_text(encoding='utf-8'));scene=json.loads((WORK/'scene.json').read_text(encoding='utf-8'));renders=json.loads((WORK/'renders.json').read_text(encoding='utf-8'));weather=json.loads((WORK/'weather.json').read_text(encoding='utf-8'));audit=json.loads((WORK/'source_audit.json').read_text(encoding='utf-8'))
assert v['same_source_all_stills'] and audit['roof_A_saved']
now=datetime.now().astimezone().isoformat(timespec='seconds')
rows=[]
labels={'restroom':'Restroom stall vandalism','restroom_mirror':'Mirror scratches and etching','alley':'Back wall, service alley and ground','alley_ground':'Broken pavement and loose wet litter','bus_stop':'Route 05 bus shelter and parked bus','roof_A':'Rooftop neon A — arm and bell DOWN','roof_B':'Rooftop neon B — arm raised, bell UP','eatfresh':'EatFresh wall advertisement','frontage':'Café and neighbouring shopfronts','greengrocer':'Separate CABGE / NOODLES bays','entrance_script':'Anything else? script blade'}
for name,label in labels.items():rows.append(f'| {label} | [{renders[name]["file"]}]({renders[name]["file"]}) | {renders[name]["seconds"]:.1f} s |')
body=f'''# Draft 6 — owner feedback, stills only

Completed {now}, following [BRIEF-17-draft6.md](../BRIEF-17-draft6.md). Built from the saved Draft 5 scene. **Draft only: no clips, no production pack build and no out10 continuation.**

Review [draft_6.png](draft_6.png), the native **1280 × 720 / 256-sample** weather still, with rooftop neon **state A**. The matching [clean still](draft_6_clean.png) is also retained.

| Close-up | File | Render time |
|---|---|---:|
{chr(10).join(rows)}

Every close-up is a fresh **1280 × 960 / 256-sample** render. Rooftop A and B use identical camera transforms. They are stills of two physical tube circuits, not frames from an animation render.

**35 — restroom vandalism.** Removed the alley YEE/PEPE poster and its old framed board. The second stall door now has small, uneven monoline marker writing: `YEE NEVA LOSE`, two red strike-throughs, `PEPE WINS`, and a tiny dino re-tag. Other marks are distributed on a partition, tile and another door; thin pale etched marks sit on the mirror surfaces. These are surface-attached strokes with no rectangular poster backing. ABSOLUTE CINEMA remains on the actual alley brick wall.

**36 — two-state rooftop neon.** The head/hood/face stay shared. Separate arm, hand, handle, bell and clapper tubes form DOWN circuit A and UP circuit B; B also has two short ringing ticks. The inactive circuit stays visible as dark glossy glass with zero emission. No objects disappear, no physical bell is rotated between poses, and no extra DinkDonk emote remains on the entrance blade. The saved scene is state A. For a later approved final loop, `build_pass10_draft6.neon_state(scene, 'A' or 'B')` switches the circuits; the final ring rhythm is not rendered in this draft.

**37 — EatFresh.** The supplied [EatFresh emote](../ref/eatfresh-emote/EatFresh.png) is used in an original cream/coral/ink-violet 90s poster, with the exact slogan **EAT OUR FRESH NOTHING BURGERS**. It has no sandwich-chain logo, name, palette or brand typeface. The poster is framed on the solid restroom exterior wall above the shelter, with normal world perspective and scene lighting. Its physical aspect matches the artwork, preserving the original emote proportions. [Flat artwork](draft6/art/eatfresh.png).

**38 — entrance script.** Replaced the small frog and DD caption with two-line **Anything else?** script neon. Its letters are rounded 3D tubes following readable script contours, with mounting spacers and a dark blade backer. The big rooftop sign is now the sole DinkDonk emote neon.

**39 — alley ground.** Rebuilt the visible walking surface with {scene['alley']['displaced_vertices']:,} actual displaced vertices, four depressed water-filled potholes, crumbling aggregate, six irregular asphalt repairs, three heaved concrete fragments, branching cracks, oil stains, wall-foot grime and 29 weed clumps. Loose litter lies directly on the ground: three flattened soggy cardboard pieces, a wet newspaper, twelve papers/flyers, six collapsed cups/cans, 23 cigarette butts and a low open takeaway carton. The old tied trash bags were removed. The reserved walking strip remains at **u 13.12–13.55, v 0.35–8.8**; debris and major breaks are concentrated beside it. The close-up camera looks down the alley so the low foreground building does not conceal the requested pavement work.

**40 — shelter and Route 05.** A full-depth steel shelter now has a glazed back and two side panels, rubber seals, scratched/etched perspex, a wet lipped roof, illuminated header, underside diffusers, slatted bench, travel lightbox, PICK ONE call box, glazed timetable/route map, stop pole/sign and litter bin. Stickers, etching and gum provide modest wear. The new roof has 70 water beads and 18 edge drips; side glazing has beads and runnels. All current bus destination/route signs read **05**, **05  DINK DONK** and **d.gg transit**. The two added plates read **DGG 05**. The timetable reads Route 05 / every 5 min, with a slightly crooked 5 sticker over an old 15. [Flat timetable](draft6/art/timetable.png).

Seat coordinates for later riders, in scene u/v/z-pixel units:

| Seat | u | v | Seat z | Facing |
|---|---:|---:|---:|---|
| shelter_05_left | 1.94 | 9.43 | 25.5 | Street, +v |
| shelter_05_right | 2.35 | 9.43 | 25.5 | Street, +v |

The reserved door-to-sidewalk corridor is **u 0.25–1.10, v 9.68–10.90**. The parked bus door is **u 0.38–0.72, v 10.82–10.87**. The geometry check reports **0 solid furniture intersections** with that boarding reserve. This is a static clearance check; no rider animation or live-page integration was attempted.

**Frontage and wall-placement fixes.** CABGE and NOODLES now occupy separate complete shop bays divided by a brick pier, each with its own sign, window and doorway. CABGE retains its awning, crates and exactly one red cabbage. Café Luna remains in place. An early café-side CABGE placement was rejected because it fell outside the approved main camera; the delivered placement keeps CABGE visible. LOOKALIKE / RE-ELECT sheets are pasted onto the solid wall. The obsolete alley board is gone, and the other alley tags sit on brick. Ten reviewed artwork surfaces all have physical backing in the saved scene.

**Approved water and glare.** Kept the Draft 4 periodic ray-traced ripple node group and the inherited Draft 5 street/roof wetness and reflection treatment. Reduced the ripple bump distance from **0.012 to 0.0045** to soften hard ring outlines in stills. The rebuilt alley uses an opaque rough aggregate surface with variable wet coat, the same ripple group and shallow dielectric pothole water. Its upward face winding and lowered substrate were corrected after close-up review. Paper/cardboard corner clearances are at most **{max(r['max_clearance_z_px'] for r in audit['ground_litter_contact']):.2f} scene z pixels** above the actual ground mesh. Removed inherited droplets attached to moved/rebuilt pieces; the rest of the surface-water geometry stays. The HDR Bloom / faint Fog Glow / restrained aperture-streak compositor is retained. There is no new ripple, temporal-denoise or sparkle experiment.

The final weather still combines the current wet beauty with a fresh, current-geometry-occluded render of **{weather['airborne_streaks']} 3D rain streaks** at 256 samples. Main beauty: {renders['preview']['seconds']:.1f} s; weather rendering/compositing: {weather['seconds']:.1f} s. Cycles uses OptiX, fixed seed 1701, adaptive sampling off, full native resolution and per-frame denoising. No delivery image is a scaled-up low-quality preview.

**Source and checks.** Editable source: [roxy_pass10_draft.blend](../roxy_pass10_draft.blend). Preserved Draft 5 source: [source_before_draft6.blend](source_before_draft6.blend). All delivered stills match source SHA-256 `{v['source_sha256']}`. The main camera is unchanged. [Scene/seat coordinates](draft6/scene.json), [read-only source audit](draft6/source_audit.json), [render records](draft6/renders.json), [delivery validation](draft6/validation.json), [STATUS](STATUS.md).

SHA-256 preservation passed for **{v['protected']['protected_files']:,} protected files**, including all live packs and the pre-existing parked out10 files. No protected file changed or disappeared, and no pack file was added. [Preservation evidence](draft6/preservation.json).

Draft 5's interrupted clip job was not resumed; its partial frames are left in place. This run created no clip, no out10 pack and no production manifest. The work stops here for owner review. Final-loop timing, rider integration, sprite/occlusion exports and production video validation remain for a separately authorized final render.
'''
(QA/'DRAFT-6.md').write_text(body,encoding='utf-8')
status('DRAFT-6.md written with reviewed stills, owner-change notes, seat/boarding coordinates and preservation evidence; draft-only stop, no clips or out10')
