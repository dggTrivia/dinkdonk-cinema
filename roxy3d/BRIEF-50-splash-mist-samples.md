# Brief 50: heavy-rain splash mist, inputs + one baked sample (samples only, live pack untouched)

Owner: "on the street, on the rooftops, every surface that I use for splash on. I wanted more heavy rain effect. Like
it's when it's pouring and you get like this mist at any surface that splashes with water." He wants to SEE samples
first. Real reference: in a downpour every hard surface hit by rain wears a thin white-grey spray layer (crown
splashes + broken droplets) a few cm to ~20 cm tall that hugs the surface; it reads only where light hits it (street
lamps, neon, headlights, the marquee) and is strongest as a bright rim along roof edges, ledges, curbs and parapets
seen against the dark. Far surfaces read as a soft haze; there is none under cover (lobby, awnings' undersides, bus
stop shelter floor, the annex interior).

Claude builds the animated mist in the page (scrolling noise + splash sprites, masked). For that Claude needs exact
surface data from the out10 scene. Source: build_pass10_final.py (the out10 scene, approved draft 13 + later fixes).

## Do
1. Render, on the exact out10 camera grid (4K, then 1080p by the production 2x2 reduction; 1x and @2x), single
   static passes (no rain particles, no animation, no props that move), into roxy3d/out10mist/:
   - `catch.png` 8-bit grey: how much rain lands here = max(0, normal.z) x sky exposure (0 under any cover; ray up or
     a top-down shadow from a sun straight overhead), only for surfaces that get rain in the scene (outdoor ground,
     sidewalk, road, roofs, parapet tops, awnings' tops, bus stop roof, bins, benches, signs' tops). Exclude glass
     you look through to the interior and everything inside the building.
   - `rim.png` 8-bit grey: the same, but only the outer ~2-4 px (1080p) of catch areas that end at an edge with a drop
     (roof edges, parapets, ledges, curbs, awning fronts): where spray shows against what's behind.
   - `light.png` RGB: the light that falls on those surfaces in the lit night scene (diffuse irradiance / or lit
     colour on a white matte override), 0 where catch = 0. This tints and brightens the mist (lamps, neon, marquee).
   - `height.png` 8-bit grey: screen-space height of each catch pixel above the street plane (0 street, 255 = top of
     the tallest roof), so Claude can make far/high surfaces hazier.
   - ALSO the same 4 passes for the vehicles (+u and -u closed bodies, roofs/bonnets only) if trivial; else skip, say so.
2. ONE baked sample still, draft quality, local GPU: the out10 frame (one loop phase) with a physically-made heavy
   splash mist added in Blender (e.g. many short-lived crown/droplet particles + a thin low-density volume slab
   hugging every catch surface, lit by the scene lights; no other change). Same camera. Keep it to one frame.
3. ONE owner image qa10/draft17-mist-baked.png, 1280x720: before | after crop of the same busy area (street + bus stop
   + cinema roof edge + marquee light). Small labels only.

## Deliver
NOTES-50.md (how each pass was made, value ranges, file list, render times, what you could not do), STATUS line, stop.
Do NOT modify roxy3d/out10/, any other pack, or standby/roxy.html. Local GPU only, no cloud. Write only in roxy3d/.
