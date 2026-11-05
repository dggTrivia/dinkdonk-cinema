# Brief 16: DRAFT 5 (then stop)

Standing rules: drafts only - no full render / out10 until the owner says "final render". Work from the
draft 4 scene. Only write inside roxy3d/. Fidelity matters, not render time. Draft standard: one 1280x720
frame at final quality (256 samples, real wet materials, ray-traced reflections, your ripple shader) + one
composited weather frame -> `qa10/draft_5.png`, plus the tests below. Then `qa10/DRAFT-5.md`, STATUS, STOP.

Owner on draft 4: loved the ray-traced ripples ("definitely keep them"); the reflections are real but read as
fake. Items (QUEUE-owner.md 32-34 and 28):

32. **Realistic wet road** (and sidewalk/roofs): under the DD blade the asphalt is a near-perfect mirror, so the
    reflection is a crisp copy of the emote; elsewhere small lights become round red/green blobs (isotropic
    roughness). Fix in the materials: rough asphalt base with varied micro-roughness and grain, a thin water
    film of varying thickness (true puddles only in low spots), fine micro-ripple/rain normals everywhere, so
    neon reflections stretch into long, broken, vertical streaks that keep roughly the source colour/shape.
33. **Scene-wide water audit**: every upward-facing outdoor surface reacts to rain by material - water/puddles:
    your ripple rings; felt/asphalt/paving: wet sheen + rings in puddles; metal (AC tops, bus-shelter roof,
    dumpster lids, sign boxes, railings, fire escapes): beading, small splash crowns, drips off edges; glass
    (skylights, shelter roof): beads + runnels; fabric (awnings, cafe parasols): soaked darker look, drips off
    hems; ledges/sills/parapet caps: sheen, splashes, run-off streaks down walls. Deliver
    `qa10/water_coverage.png` (labelled map of which surface gets which response) - nothing missed (the owner
    noticed the shelter roof and AC tops had nothing).
34. **Small-drop sparkle**: the owner liked how the leftover render noise in the ripple clip looked like tiny
    drops hitting the water. Keep the render clean and add that on purpose: a fine micro-impact layer on WET
    surfaces only (tiny short-lived specular glints/pinpricks, many sizes, density following the rain), periodic.
    Show `qa10/test_sparkle_clip.webm` (same street crop/48 frames as draft 4's clip, if time allows a shorter
    crop is fine) next to draft 4's noisy per-frame-denoised clip.
28. **Community memes in the world, for review** (owner approved the whole Top 12 of `roxy3d/memes/SHORTLIST.md`:
    read it - concepts, placements, styles). Put them into the draft scene as real in-world art: alley graffiti
    (YEE vs PEPE turf war; ABSOLUTE CINEMA chrome throw-up on the cinema's back wall), inside the cinema (WHIPLASH
    - IN 5 MIN coming-soon board; GLORP! 50s B-movie one-sheet), the roof billboard (WCAT & ASSOCIATES), bus-shelter
    lightbox (Nothing ever happens travel ad; red/blue button call box ad), bus side (FROGS vs DINOS - THE REMATCH;
    CLIPPED & SHIPPED courier livery), poster wall (LOOKALIKE CONTEST - hear me out; RE-ELECT THE CONDUCTOR), shop
    sign (CABGE greengrocer). Subtle, in perspective, lit and weathered like everything else (wet paper, peeling
    paste, stencil overspray), original artwork made by you procedurally - no real logos, no real people's
    likenesses. For the bus, a still of one bus sprite parked at the stop is enough for review.
Report anything you could not do.
