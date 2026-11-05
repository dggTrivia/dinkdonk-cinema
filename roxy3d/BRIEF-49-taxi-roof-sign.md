# Brief 49: smaller TAXI roof sign (draft first, live pack untouched)

Owner: "the taxi sign on top of the taxi is kinda scuffed, like way too big". In the live lobby the cream TAXI box is
almost as long as the cabin and nearly as tall as the body; it should read as a small roof light.
Source: cloud/bundle/build_vehicles.py:286-288 (and the roxy3d/build_vehicles.py copy):
`box('Illuminated TAXI roof box',-.18,-.23,.16,.23,h+3.0,h+12.0,'sign',.013)` + front/rear 'TAXI' labels (.13).
That is 0.34 tile long, 0.46 wide on a 1.72 x 0.70 car, 9 units tall.

## Do
- Make it a believable small taxi roof light: roughly a third of the roof width across the car, short along it, low
  (e.g. ~0.10-0.12 long, ~0.30-0.34 wide, ~5 units tall, a small gap above the roof), with the TAXI lettering scaled
  to fit and still readable at 2x; keep its warm emissive look and the draft-15 night vehicle lighting overrides
  (the approved studio levels). Judge it against the car, not by taste; say the numbers.
- Re-render ONLY the taxi body states (both directions, closed + open, native 2x -> 1x by the production reduction),
  rebuild their whole-body PNGs and depth slices exactly as BRIEF-47 did, into a staging pack roxy3d/out10d/ = copy
  of live out10 with only taxi files (+ checksums/validation) replaced. Check whether the taxi light passes
  (*_light*.png) show the roof sign glow; if they do, update them consistently; if not, leave them.
- Update the source (both build_vehicles.py copies) for the next render.

## Deliver
- ONE owner image qa10/draft16-taxi-sign.png, 1280x720: before | after of the taxi (+u and -u) on the street at
  the same spot, composed as the page stacks it. Small labels only.
- NOTES-49.md (sizes, files changed, validation), STATUS line, stop.
Do NOT modify roxy3d/out10/ or standby/roxy.html. Local GPU only, no cloud.
