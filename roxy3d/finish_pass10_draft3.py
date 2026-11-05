"""Draft-3 annotations, owner notes and preservation checks. No output pack writes."""
from pathlib import Path
from datetime import datetime
import json,hashlib,subprocess,struct
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa10'
meta=json.loads((QA/'draft3_geometry.json').read_text())
timing=json.loads((QA/'draft3_render_timing.json').read_text())
items=[]
def p(u,v,z=0):return [900+60*(u-v),350+30*(u+v)-z]
def line(points,color='#F1CF84',width=1.6,dashed=False):items.append(dict(type='path',points=points,color=color,width=width,dashed=dashed))
def label(x,y,s,color='#F4EEE1',size=16):items.append(dict(type='text',x=x,y=y,text=s,color=color,width=1,size=size))
def callout(x,y,s,target,color='#F1CF84'):
    line([[x+8,y+23],target],color);label(x,y,s,color)
def rect(a,v,c,w,color,z=0):items.append(dict(type='polygon',points=[p(a,v,z),p(c,v,z),p(c,w,z),p(a,w,z)],color=color,width=1.5,fill=12,dashed=True))

label(18,16,'DRAFT 3 / BRIEF 14',size=25)
label(18,51,'Geometry + quick still only',size=16)
label(18,76,'No pack, loops, sprites, slices or 2x',size=14)
callout(322,115,'1  Continuous apartment / blank party wall',p(-.075,5.5,201))
callout(878,22,'2  Roof wear, tarp + fan details',p(6.6,-4.5,241))
callout(435,271,'3  Framed films + explicit wall caps',p(.025,1.65,126),'#A6ECCB')
callout(968,191,'4  Programme board / clock / history',p(1.8,.1,121),'#A6ECCB')
callout(1530,410,'5  Multiplex alley wall + EXIT',p(13.9,-.10,93),'#FFBC89')
callout(1470,1040,'6  Bins, steam, patched wet alley',p(14.06,6.6,38),'#FFBC89')
callout(14,540,'7  Cafe + wet seating',p(-5.8,8.35,32),'#F1CF84')
callout(448,1010,'8  Glass: tint + grime, no white dashes',p(6.2,9.02,70),'#A6ECCB')
callout(28,861,'9  Soft water films / quiet sealed cracks',p(1.6,11.6,.1),'#99D6F0')
callout(80,643,'10  Varied blinds / curtains / interiors',p(-2.85,8.77,142),'#C9BBFF')
rect(3,.9,13,2.0,'#76DDE6')
for u in [4.8,8.2,11.2]:line([p(u,1.4),p(u,.55)],'#76DDE6',1.7,True)
label(1198,757,'CYAN: retained clear corridor + approaches','#76DDE6',14)
rect(13.12,.35,13.55,8.8,'#FFBC89')
# Mark the future page-owned alley panel, rather than putting content in it.
for a in meta['future_ad_surfaces']:
    q=a['quad_px'];items.append(dict(type='polygon',points=q,color='#C9BBFF',width=1.2,fill=5,dashed=True))
spec={'input':str(QA/'draft_3.png'),'output':str(QA/'draft_3_annotated.png'),'items':items}
(QA/'draft3_annotation.json').write_text(json.dumps(spec,indent=2))
subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass10_draft.ps1'),'-Spec',str(QA/'draft3_annotation.json')],check=True)

before=json.loads((QA/'draft3_protected_before.json').read_text())
changed=[n for n,digest in before.items() if not (ROOT/n).is_file() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=digest]
after={str(p.relative_to(ROOT)) for folder in ROOT.glob('out*') if folder.is_dir() for p in folder.rglob('*') if p.is_file()}
before_packs={n for n in before if n.startswith('out')};added=sorted(after-before_packs)
assert not changed,changed
assert not added,added
for name in ['draft_3.png','draft_3_annotated.png']:
    assert struct.unpack_from('>II',(QA/name).read_bytes(),16)==(1920,1080)
out10_count=sum(n.startswith('out10/') or n.startswith('out10\\') for n in before)
checks={**meta['checks'],'protected_files_checked':len(before),'changed_protected_files':changed,'new_files_in_output_packs':added,'parked_out10_files_checked':out10_count,'production_scene_unchanged':True,'output_pack_writes_this_draft':0,'still_size':[1920,1080],'visual_review':'unannotated draft inspected; initial lighting and poster-overlap issues corrected; annotated copy also inspected before delivery'}
(QA/'draft3_validation.json').write_text(json.dumps(checks,indent=2))

notes=f'''# Pass 10 / draft 3

**Draft only, stopped for owner review.** Built for `BRIEF-14-pass10-draft3.md`.
Review [draft_3.png](draft_3.png) and [draft_3_annotated.png](draft_3_annotated.png).
Editable scene: [roxy_pass10_draft.blend](../roxy_pass10_draft.blend).
The delivered 1920 x 1080 still uses 24-sample denoised Cycles and took
{timing['render_seconds']:.1f} seconds. Several quick stills were inspected while correcting lighting,
poster overlap and visibility; no production render pipeline was invoked.

The interrupted out10 attempt is parked. Its partial files remain exactly as they
were at the start of this draft. `roxy_pass10.blend` and every live output pack are
also unchanged. The editable draft file had still contained draft 1, while draft 2's
accepted roof/neons had been saved in the production scene. This draft restores
those approved changes from their source functions before applying brief 14;
it does not use the closed-door production preparation. Screen 2 and the restroom
entry remain posed open for still review. The original draft source is preserved
as `qa10/source_before_draft3.blend`.

## Changes applied

| Owner item | Draft 3 result |
|---|---|
| 18 / top-left neighbour | The low service annex is removed. The apartment extends from u=-5 to u=-0.075, v=-1..8.7, roof z=235. Its cinema-facing side is a blank brick party wall; all window assemblies on the formerly buried side were removed. Street-facing windows and video rental frontage remain. |
| 19 / corridor dressing | Original fictional one-sheets, a NOW SHOWING / COMING SOON board, a physical wall clock, two framed 1936 cinema photos, a shallow wall payphone, alarm, extinguisher cabinet and warm sconces. The three page-owned poster apertures and LED planes remain clear. |
| 20 / roof character | Multiplex and neighbouring roofs have mottled felt, irregular damp stains, ragged repairs, rust on equipment, small debris, corner moss and uneven exterior coping. The main roof has an anchored blue tarp and a bent vent. Fans have modeled rotors/grilles and future state tags. |
| 21 / water and cracks | Rebuilt all {meta['water_revision']['old_pools_replaced']} inherited roof/street/alley pools with irregular shallow reflective films and feathered vertex coverage. Removed static oil/ripple ellipse outlines. Reworked {meta['water_revision']['old_crack_paths_reworked']} old asphalt paths into much thinner, lower-contrast broken tar seals. No static ripple strokes were added. |
| 22 + 26 / back alley | The old black gap is now the multiplex's own brown-brick wall, with a lit emergency EXIT, steel door, loading shutter, drainpipe and grimy bulkhead light. The floor has no regular tile grid: patched wet asphalt, subtle seams and shallow potholes. A dumpster, recycling bin, tied bags, pallets/crate, fire escape/ladder and a thin vent-steam volume furnish the edges. A reflective water film catches coloured light. |
| 23 / glass marks | Removed all 36 baked rain traces and the short safety-etch bars that could still read as white dashes. Approved glass tint, edge grime and long edge highlights remain. No animated glass water was rendered. |
| 24 / living windows | Added varied half blinds, parted/single curtains and small interior lamp/bookcase shapes across the remaining in-frame neighbour windows. {len(meta['windows'])} candidate window quads are recorded in the draft geometry JSON for planning; they are not a final visibility-filtered manifest. |
| 25 / cafe | The far-left cropped repair shop is now CAFE LUNA: a warm shopfront, small awning, two wet tables with chairs, folded parasol, menu A-board and string lights. It deliberately continues past the left frame edge. All furniture stays behind v=9.03, clear of the spawn lane at v=9.78..10.05 near u=-6. |
| 27 / cutaway | The purple corridor cornice is replaced by a pale core cap with narrow outer masonry and inner finish bands. Matching exposed sections run across the junction, restroom, left wing, street wall and ticket/concession partitions. Thin stall panels show a laminate core. The top of the exterior apartment wall remains an exterior parapet. |

Coordinates, objects removed, window candidates, fan pivots, caps and future ad
quads are in [draft3_geometry.json](draft3_geometry.json). The annotation's cyan
floor band is u=3..13, v=0.9..2.0; screen approaches remain at u=4.8, 8.2 and 11.2.
The new payphone footprint is u=0.15..0.49, v=2.35..2.88. Restroom/queue positions
retain the approved layout 3. The alley keeps a narrow continuous strip at
u=13.12..13.55, v=0.35..8.8, plus larger open areas above the bins for later dressing.
Short furnishings were shifted away from the foreground annex roof so they read
from the fixed camera. The wall-mounted ladder, pallets and upper-wall clutter
remain closer to the records-shop edge.

The roof billboard, bus shelter ad and west paste-up surface are retained. The
new alley paste-up rectangle has a recorded clockwise `quad_px` and is left blank
for page-authored community material. The small generic wall tag is only atmosphere;
community in-jokes, bus/street ad content and future graffiti remain page-owned.

## Later animation delivery, only after an explicit final-render request

**Roof fans and neon:** export tight native 1x/2x transparent crops with canonical
world pivots. Most fan rotors rotate smoothly; fan id 1 stays dead, and id 4 gets
a small once-per-turn axle wobble. Keep stationary grille geometry separate above
the rotor. Use integer turns over the approved loop length for exact seam closure.
One short cyan roof-sign segment gets a separately controlled glow/tube patch;
the page triggers infrequent brief voltage dips, leaving the other tubes stable.
Keep the DinkDonk bell's two physical poses (20 fps, matching the supplied two-frame
emote) as its own tiny event sheet. Nothing is animated or exported in this draft.

**Rain/wet surfaces:** rebuild rain, subtle water ripples and glass runnels after
approval using this geometry. Ripples appear only as faint expanding animated
coverage inside the irregular water masks. Glass gets soft beads/runnels and
continuous trails rather than isolated white rectangles. New bins/walls/props
must receive appropriate foreground ownership/slices in the final pass; the old
partial out10 assets must not be treated as matching this draft.

**Living windows:** deliver `windows: [{{id, quad_px, z_index, lit, building, ...}}]`
for every actually visible opening on every building, including small distant
ones. Keep the window registry independent of the six-second weather loop.
In the final pass, derive corners from world geometry, use camera visibility tests
and rendered masks to reject fully hidden openings, clip partial openings to their
reveals, and export curtain/mullion occlusion masks. The {len(meta['windows'])} draft entries
are in-frame candidates, so hidden or overlapping entries still need that final
filter. Existing street-facing frames stay the stationary top layer.

Deliver a compact kit per perspective/size family: persistent light-on/off patches,
short bulb flicker, TV colour changes, a silhouette crossing behind the curtain,
a curtain sway, a sill cat, a smoker/ember event and restrained party colours.
Use straight-alpha source-over for silhouettes, curtains and cats; additive light
for TV/party/ember glow; opaque or source-over replacement patches for persistent
room-light state changes. Each event supplies pivot/quad, crop, native 1x/2x files,
fps, frame count, blend mode and matching mask. The page schedules sparse events
over minutes with per-building/window cooldowns, keeps changed light states until
the next event and limits simultaneous activity. No perpetual synchronized
six-second window cycles. Nothing from this kit was rendered now.

## Review questions

- Is the roof wear restrained enough, or should selected roof corners and repair patches be more pronounced?
- Is the visible sliver of CAFE LUNA enough at the fixed frame edge, or should the seating/shop sign move closer to the camera in a later draft?
- Is the alley density right before adding community graffiti/posters, or should the bin group move farther toward the street?

## Draft checks and boundary

- Unchanged camera; three screen IDs; no camera-facing text.
- Zero new-fixture footprint overlaps with the protected corridor band, door approaches or cafe-side spawn strip.
- No old static ripple/oil-ring curves, glass rain traces, scribble crack objects or alley grid joints remain.
- Two delivered stills are 1920 x 1080. Image quality is draft Cycles/denoise, not final anti-aliasing or animation QA.
- {len(before)} protected files checked byte-for-byte, including {out10_count} parked out10 files: **zero changed files and zero added files in output packs**.
- Full holdout, animated occlusion, slice ownership, window-event masks, seams and decoded-video checks were deliberately not run for this draft.

Validation: [draft3_validation.json](draft3_validation.json). Stage journal:
[STATUS.md](STATUS.md). **Stopped here: no out10 build/resume, loops, sprites,
slices or 2x renders.**
'''
(QA/'DRAFT-3.md').write_text(notes,encoding='utf-8')
def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: Draft 3: '+s+'\n')
status('draft_3_annotated.png and DRAFT-3.md written, including owner review questions and deferred fan/neon/window-event delivery plan')
status('preservation verified: %d protected files unchanged, including %d parked out10 files; zero added pack files; stopped at draft-only boundary'%(len(before),out10_count))
print(json.dumps(checks,indent=2))
