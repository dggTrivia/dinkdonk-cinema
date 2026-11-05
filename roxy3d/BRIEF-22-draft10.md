# Brief 22: DRAFT 10 - better rain, one image, then stop

Strict draft rule: exactly ONE image - the fixed isometric camera, 1280x720 at final quality with the weather frame
-> `qa10/draft_10.png`. Nothing else (no close-ups, review cameras, clips, extra audits or re-renders, no out10, no
cloud). One STATUS line, a few lines in `qa10/DRAFT-10.md`, then STOP. Work from the draft 9 scene. Only write
inside roxy3d/. Keep everything the owner approved (approved ripples, HDR glare, all models/art).

Read `roxy3d/research/RAIN-REALISM.md` and implement exactly these (owner's pick):
1. **Wet-layer node group on every outdoor material**: porous darkening (Lagarde-style porosity), a water coat via
   the Principled Coat (IOR 1.33, roughness ~0.02-0.05), the four states dry / wet / drenched / pool driven by masks
   (exposure, slope, cavities), so everything outdoors reads properly soaked; indoor stays dry.
2. **Standing water from a water-level mask**: real pools/sheets - roof ponding, sheets of water in road dips and
   along the low side of the street and alley, wet shoreline bands at the edges; optional clear water with visible
   bottom on roof ponds. Deep, clean reflections in it; keep the approved ripples on the water.
4. **Two-phase flow-map water along curbs and gutters** running into the storm drains (and roof gutters / downspout
   outlets), seamless at the 48-frame (2 s) cycle; the draft still shows one phase.
5. **Hidden reflection catchers**: emissive cards / shapes invisible to the camera (camera ray visibility off) but
   seen by glossy rays, placed off-frame above/behind the scene where the real city would be (signage colours,
   lit windows, a sky glow), over darker puddle bottoms, so puddles and wet surfaces show rich neon reflections.
   They must not light the scene noticeably (diffuse/transmission visibility off) and must not show in glass as
   obvious floating cards. Keep reflections physically plausible - no pasted reflections.
3. **Stateless Geometry Nodes drips, pours and splashes** off roof edges, awnings, gutters, signs and AC units:
   drip lines and little streams, each drop a pure function of the frame (period dividing 48 frames), landing
   position from a downward ray cast, a small splash/crown where it lands; the draft still shows one moment.
(Owner correction: the pick is items 1 through 4 PLUS the hidden reflection catchers.)
NOT in this draft: car effects.
Report in DRAFT-10.md what changed and the render time.
