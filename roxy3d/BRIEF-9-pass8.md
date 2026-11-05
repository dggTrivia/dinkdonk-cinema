# Brief 9: pass 8 - the city around the Roxy, heavy rain, wet glass

The owner looked at out7 this morning (02 Nov). He likes it; the two big asks are below, and he wants your own
suggestions implemented too (your review-8-suggestions.md is part of this brief - see section C).
Same rules as before: **outputs to `roxy3d/out8/`** as a complete pack (layout 2), keep every manifest key,
contract and coordinate of out7 unless this brief says otherwise; new things only add keys. Never touch
anything outside `standby/roxy3d/`. Claude integrates in `standby/roxy.html`.

## A. Surroundings: no more flat backdrop (owner, verbatim-ish)
"On the bottom left, where the street ends, there's just a hole with the background. Add other buildings
there - I think it would just be a roof or something like that. And to the left and right of the cinema
there should be other buildings. You decide: other shops, apartments, whatever."

Build real 3D geometry in the same scene, same camera, same late-90s pre-rendered look (materials, wear,
grain, palette), so the frame reads as one city block on a rainy night instead of a slab floating on a
painted skyline. Everything visible in the 1920x1080 frame should be modelled; the distant skyline can stay
simple boxes but must be 3D, in the same projection, with haze/rain depth.
1. **Across the street** (v >= 13.5, the bottom-left triangle today): far curb + far sidewalk with street
   furniture, then a row of low 90s shops whose roofs we look down on (tar/gravel, parapets, puddles,
   AC units, vents, a water tank, skylights glowing warm, the back of rooftop signs whose neon faces the
   street and spills colored light onto the road).
2. **Left of the cinema** (u < 0 along the street, top-left today): the Roxy's own auditorium block for
   screens 1-2 behind the u = 0 wall can rise above the corridor wall, then a neighbour facing the street:
   e.g. a brick apartment block with a ground-floor shop, fire escape, lit windows (some with TV flicker),
   awning dripping.
3. **Right of the cinema** (u > 13): an alley, then a neighbour building (shop or diner or laundromat or
   video rental - your call), and a real tower under the video billboard (today a flat rectangle with dots):
   facade, windows, fire escape, rooftop water tank, the billboard on its structure.
4. **Hard occlusion rule.** Geometry can only hide a point if it has both larger u and larger v. Nothing new
   may cover any pixel where walkers, vehicles, bubbles' anchors or page signs live: cinema floor u 0..13,
   v 0..9 (to 120 px up), sidewalk v 9.15..10.5 and road v 10.6..13.5 for u -12..23 (to 90 px up;
   bus 67 px), walker spawns at u -6 and 16.5 on the sidewalk. Billboard aperture 1296,40 576x324, every
   marquee box and poster frame keep their exact pixels. Verify with a holdout render and report the
   number of covered action pixels (must be 0), or deliver any unavoidable foreground piece as an occluder
   with depth slices like the existing ones.

## B. Heavy rain, wet street, wet glass (owner: "much heavier rain - the raindrops - and the water effect on
the street, on the cinema windows, the reflections")
1. **Base light loop (under walkers):** much denser, bigger, brighter rain (a real downpour, two or three
   depth layers, consistent slant), splashes and rings everywhere outdoors (road, sidewalk, roofs, awnings,
   shelter), much stronger wet reflections (neons, street lamp, lobby spill, the new shop signs) with ripples,
   puddles, gutter water flowing to a storm drain, run-off and drips from awnings, the marquee canopy, gutters
   and downspouts. Rain stays masked off indoors.
2. **Foreground rain (new, above walkers and vehicles):** today all rain is under the walkers, so drops never
   pass in front of anyone outside. Add `rain_fg`: a seamless additive loop (on black) of the nearest drops,
   masked to outdoors, drawn by the page above walkers/vehicles and below bubbles/HUD.
3. **Cinema glass:** rivulets and beads running down the front windows and glass doors, plus faint
   reflections of the street, as additive overlays split to match the glass depth slices (same z_index per
   slice), so they cover walkers inside but not those outside.

## C. Your suggestions (review-8-suggestions.md) - taken
Section A and B of your review are the design: use your u/v ranges, heights and the envelopes
H <= 60(v-13.5)-48 across the road and H <= 60(u-13)-48 beside the right wing (rooftop kit included), the
left apartments + video rental, the brick commercial building under the billboard, the alley + low annex +
right apartments, the opposite workshop roofs, one palette (Roxy keeps the pink/cyan), 6 s / 144 frames at
24 fps for both videos, the rain density numbers, the additive-limitation fix (minimum base + nonnegative
differences, or a masked replacement surface), drainage along v ~10.55 and ~13.5, canopy drips, mostly
steady neon (one troubled tube at most), VP9 CRF ~16-22 with `-b:v 0`, 8-bit 4:2:0, true black, two 1080p
streams. Also from C:
- **Entrance (C3):** recessed entrance mat and worn threshold in the base; umbrella runoff outside.
  Plus `items.wet_print` (+_2x): one small glossy wet shoe/foot print seen from this camera, ~10 x 6 px,
  anchor = centre, straight RGBA; the page fades a few of them in behind people who just came in.
- **Arcade played state (C5):** two more prop loops at exactly the `arcade_attract` rect/z/parent:
  `arcade_play` (a tiny original game round, 72 frames 24 fps, loop) and `arcade_hiscore`
  (blinking original "HI-SCORE" screen, 24 frames 24 fps, loop). The page swaps attract -> play -> hiscore.
- C1, C2, C4 (crowd spacing, bubbles off the signs, emote contact) and C6 (bench patron) are page work
  (Claude).

## Page contracts for the new things (Claude has the page side ready)
- `rain_fg`: `{ "file": "rain_fg.webm", "size": [1920,1080], "fps": 24, "frames": 144, "seconds": 6,
  "blend": "plus-lighter" }` - additive on true black; the page draws it above walkers/vehicles
  (z 70001), below bubbles and HUD. Masked indoors/sheltered/billboard as you described.
- Glass water: add entries to `prop_loops` (same sprite-sheet contract, `frames`, `columns`, `fps`, `x/y/w/h`,
  `file`/`file_2x`, `parent_slices`), one per glass depth slice, `z_index` = that slice's z_index, and set
  `"blend": "source-over"` for straight-RGBA water (edges, beads, runnels) or `"plus-lighter"` for glints
  (the page now honours `blend`). Keep the cashier glass dry; atlas budget <= 16 MiB decoded.
- Every new prop loop / item: 1x + @2x, tight crops.

## D. Delivery
- Report in `roxy3d/NOTES-PASS8.md` and the manifest as before; QA images in `roxy3d/qa8/`.
- Encoding: pick settings that keep dense rain clean (no blocking/banding) - give bitrate, size, and
  decode cost; 1080p loops are fine (page scales them for 4K).
- Keep it seamless (endpoint == frame 0) and verify as in pass 2.
