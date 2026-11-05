"""Review labels, short draft notes and read-only preservation checks. No pack."""
from pathlib import Path
from datetime import datetime
import json,hashlib,subprocess,struct
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa10'
meta=json.loads((QA/'layout3_draft_coordinates.json').read_text())
items=[]
C={'roof':'#FFD578','walk':'#69E6F0','bath':'#81F6B4','queue':'#FF91A3','prop':'#CBB6FF','white':'#F6F2E7'}
def p(u,v,z=0):return [900+60*(u-v),350+30*(u+v)-z]
def poly(rect,color,z=0,fill=12,dashed=True,width=1.8):
    a,v,c,w=rect
    items.append({'type':'polygon','points':[p(a,v,z),p(c,v,z),p(c,w,z),p(a,w,z)],'color':C[color],'width':width,'dashed':dashed,'fill':fill})
def path(points,color,width=2,dashed=True):items.append({'type':'path','points':points,'color':C[color],'width':width,'dashed':dashed})
def label(x,y,s,color='white',size=17):items.append({'type':'text','x':x,'y':y,'text':s,'color':C[color],'width':1,'size':size})
def dot(u,v,color):
    x,y=p(u,v);items.append({'type':'point','x':x,'y':y,'color':C[color],'width':2})
def callout(x,y,s,target,color):
    path([[x+8,y+22],target],color,1.5,False);label(x,y,s,color)

for s in meta['screens']:
    poly(s['hall_uv'],'roof',z=s['roof_z']+.5,fill=4,dashed=False)
    a,v,c,w=s['hall_uv'];x,y=p((a+c)/2,-.3,s['roof_z']-12)
    label(x-25,y,'HALL '+str(s['screen']),'roof',15)
poly(meta['restroom']['room_uv'],'bath',fill=10)
poly(meta['restroom']['dead_corner_uv'],'prop',fill=10)
poly(meta['restroom']['front_solid_wall_uv'],'prop',z=159,fill=30,dashed=False)
for e in meta['footprints']:
    if e['name'].startswith(('Stall ','Sink ','Hand dryer')):poly(e['uv'],'bath',fill=8,width=1.2)
    if e['kind']=='corridor_prop':poly(e['uv'],'prop',fill=20,width=1.2)
poly(meta['walkable_spots']['restroom_aisle'],'bath',fill=28,dashed=False,width=1.1)
poly(meta['corridor']['walk_band_uv'],'walk',fill=20,dashed=False)
for r in meta['corridor']['door_approaches']:poly(r,'walk',fill=18,width=1.1)
for name,route in meta['routes'].items():path([p(*q) for q in route],'walk',2.1)
for group,prefix in [('stalls','T'),('sinks','S'),('dryer','D')]:
    for i,(u,v) in enumerate(meta['walkable_spots'][group],1):
        dot(u,v,'bath');x,y=p(u,v);label(x+7,y-10,prefix+str(i),'bath',12)
poly(meta['ticket_queue']['lane_uv'],'queue',fill=18,dashed=False)
for u,v in meta['ticket_queue']['queue_slots']:dot(u,v,'queue')
path([p(9.55,8.5),p(9.3,7.4),p(4.85,7.4)],'queue',2.1)
path([p(4.85,7.4),p(5.30,6.65),p(4.85,6.0)],'queue',1.8)
for u,v in meta['snack_additions']['customer_spots']:dot(u,v,'prop')
for u,v in meta['snack_additions']['registers_uv']:poly([u-.21,v-.17,u+.21,v+.17],'prop',z=44,fill=10,dashed=False,width=1.2)
for a,c in [[3,8.4],[10.6,13]]:
    items.append({'type':'polygon','points':[p(a,9,145),p(c,9,145),p(c,9,5),p(a,9,5)],'color':C['prop'],'width':1.3,'dashed':True,'fill':4})

callout(1330,18,'1  DINK DONK / steel + neon',p(8,-.61,365),'roof')
callout(1625,100,'AD / moved to roof',p(11.35,-3.55,320),'roof')
callout(420,266,'2  RESTROOM / 4 stalls + 2 sinks',p(1.5,5.2,15),'bath')
callout(785,310,'ENTRY (1.4, 3.0)',p(1.4,3,102),'bath')
callout(145,705,'3  Solid street wall / 159 px',p(1.2,8.98,140),'prop')
callout(635,917,'4  Queue / 7 slots, 0.62 u apart',p(7.33,7.4),'queue')
callout(1425,850,'5  Clear corridor band',p(9.5,1.4),'walk')
callout(1075,975,'6  Registers + counter equipment',p(8.2,4.3,61),'prop')
callout(450,1015,'7  Reflective wet glazing',p(6.6,9,83),'prop')
callout(1485,530,'8  Screen 2 open / dark curtain',p(8.2,-.4,55),'white')
callout(1640,920,'Bench / fountain / bin',p(9.5,2.6,15),'prop')

items.append({'type':'panel','x':18,'y':16,'w':460,'h':207,'color':C['white'],'width':1})
label(32,28,'LAYOUT 3 / DRAFT 1',size=26)
label(32,67,'Footprints and page walk targets',size=16)
label(32,96,'CYAN   routes + clear walking band','walk',15)
label(32,121,'MINT    restroom + fixture standing spots','bath',15)
label(32,146,'PINK     ticket queue + customer slots','queue',15)
label(32,171,'Dashed outlines show hidden floor footprints.',size=14)
label(32,194,'Roof outlines are drawn at roof height.',size=14)
spec={'input':str(QA/'draft_1.png'),'output':str(QA/'draft_1_annotated.png'),'items':items}
(QA/'draft_annotation.json').write_text(json.dumps(spec,indent=2))
subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'annotate_pass10_draft.ps1'),'-Spec',str(QA/'draft_annotation.json')],check=True)

baseline=json.loads((QA/'protected_sha256.json').read_text())
changed=[n for n,digest in baseline.items() if not (ROOT/n).exists() or hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=digest]
assert not changed,changed
assert not (ROOT/'out10').exists(),'Draft must not create out10'
for name in ['draft_1.png','draft_1_annotated.png']:
    data=(QA/name).read_bytes();assert struct.unpack_from('>II',data,16)==(1920,1080)
checks={**meta['draft_checks'],'protected_files_checked':len(baseline),'changed_protected_files':changed,'out10_exists':False,'required_still_sizes':[1920,1080]}
(QA/'draft_validation.json').write_text(json.dumps(checks,indent=2))
t=json.loads((QA/'draft_render_timing.json').read_text())
notes=f'''# Pass 10 / draft 1 — layout 3

Built from `roxy_pass9.blend` for **BRIEF-12-pass10-draft.md**. Review
[draft still](draft_1.png) and [annotated copy](draft_1_annotated.png).
Editable source: `../roxy_pass10_draft.blend`. Camera and street placement are unchanged.
The final 1920×1080 still used 24-sample Cycles + denoise and took {t['render_seconds']:.1f} seconds.

The left cinema doors/posters/LEDs and the rear commercial tower are gone. Three
roofed auditorium shells now connect to the surviving doors, with projection booths,
HVAC, ducts, hatches and puddles. DINK DONK is a physical steel-supported tube sign;
the supplied frog/triangle reference is traced in neon on the roof and entrance blade.
The tower ad has moved to the roof. Small d.gg branding remains on transit signage.

The tiled restroom has four stalls, two recessed basins/mirrors, a dryer, bin and
mop sink. Its inward door is hinged on the right to keep the dryer reachable; the
green occupancy plaque is on that new door wall. The solid street wall is an occluder.
Red velvet ropes define the queue. Registers and small concession props stay on or
behind the counter. Original fictional standees, a lightbox, bench, fountain, EXIT
sign, extinguisher, bin and runner dress the corridor. Glass now has stronger tint,
reflection, grime and wet edge traces. **Screen 2 is posed open to show its black
curtain vestibule**; the other two remain closed.

Coordinates as built use page tiles `(u,v)` and vertical pixels `z`:

| Element | Built coordinates |
|---|---|
| Screens 1 / 2 / 3 | Doors `(4.8,0)`, `(8.2,0)`, `(11.2,0)`; each approach `u=door±0.5, v=0..1.4` |
| Auditorium shells | `u=3..6.3333 / 6.3333..9.6667 / 9.6667..13`, all `v=-4.4..-0.23`; roof z `238 / 246 / 240`, booths +32 |
| Rooftop neon | `u=3.7..12.55, v=-0.61, z=312..425`; small blade `u=-0.83..-0.03, v=9.12..9.35, z=132..247` |
| Relocated roof ad | `u=10..12.7, v=-3.55, z=283..357`; blank/lit, aspect 2.681:1; shelter/paste-wall ads retained |
| Restroom / closet | Room `u=0..2.9, v=3..8.4`; dead corner `v=8.4..8.9` |
| Restroom door / indicator | Door center `(1.4,3.0)`, clear opening `u=0.95..1.85`, z `0..105`; indicator `(2.055,3.12,99)` |
| Stall fixtures / walk spots | Four stall fronts at `u≈1.1`; standing spots `(1.5,4.4)`, `(1.5,5.4)`, `(1.5,6.4)`, `(1.5,7.4)` |
| Sink / dryer walk spots | Sinks `(2.12,4.10)`, `(2.63,4.10)`; dryer `(0.55,3.55)` |
| Street wall | `u=0..3, v=8.90..9.05`, wall z 155 / coping 159 |
| Ticket queue | Slots `(4.85+0.62i,7.4), i=0..6` (last u=8.57); opens at `(9.3,7.4)` |
| Ropes / window 2 gap | Front `v=7.8, u=5.2..9.2`; back `v=7.0, u=5.9..9.2`; gap `u=4.4..5.79` to window `(4.85,6.0)` |
| Snack registers | `(6.6,4.3)`, `(8.2,4.3)`, `(9.8,4.3)`; new equipment v≤4.51, within counter front v=4.6 |
| Corridor clear band | `u=3..13, v=0.9..2.0`; props confined to `v≤0.5` or `v≥2.4` |
| Corridor prop footprints | Standees `[3.36,0.22,3.84,0.38]`, `[6.94,0.21,7.42,0.37]`; bench `[8.8,2.43,10.22,2.87]`; fountain `[6.91,2.48,7.36,2.86]`; bin `[12.51,2.48,12.85,2.82]` |
| Glazing / entrance | Panes `u=3..8.4` and `10.6..13`, `v≈9, z=5..145`; entrance `u=8.4..10.6` stays open |

Routes retain gate `(3.7,3.7)` → junction `(1.4,1.4)` → restroom `(1.4,3.0)`
or the right corridor. All exact footprints, branches, sign/ad quads and standing
spots are in [layout3_draft_coordinates.json](layout3_draft_coordinates.json).
The annotation uses floor outlines even where walls hide the floor; roof outlines
are at roof height. The low bench/fountain and rear cleaning fixtures are partly
hidden by the retained ticket/snack partitions and new front wall.

**Open decisions for owner feedback:**

- Keep this single-line cyan wordmark and yellow/green emblems, or adjust the neon weight/colors?
- Keep the restroom cutaway and partition heights, or reveal more of the low fixtures/bench?
- Is this glass tint/reflection strength sufficient while retaining the lobby view?

Draft checks: exactly three screen IDs, unchanged camera, zero corridor-prop
footprint overlaps with the walking band/door approaches, zero restroom route hits
at a 0.12-tile radius, and no camera-facing text. All {len(baseline)} protected live-pack/source
files are byte-identical. This is geometry/still review; production occlusion,
animation seams, slice exports and alternate door/WC states await the approved pass.

**Stopped at the draft boundary. No out10, loops, sprites, slices or 2× renders.**
'''
(QA/'DRAFT-1.md').write_text(notes,encoding='utf-8')
def status(s):
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:f.write(datetime.now().astimezone().isoformat(timespec='seconds')+' | Finished: '+s+'\n')
status('Annotated 1920x1080 copy and DRAFT-1.md written with actual layout coordinates and owner feedback questions')
status('Draft preservation checks passed: %d protected files unchanged; out10 absent; no loops/sprites/slices/2x exports'%len(baseline))
print(json.dumps(checks,indent=2))
