# Brief 14: pass 10 - DRAFT 3 only (then stop)

New standing rule from the owner: **Codex only renders quick drafts and stops; no full render (out10 pack,
loops, slices, 2x) until the owner explicitly asks for the final render.** Your interrupted out10 attempt is
parked; do not continue it. Work in roxy_pass10_draft.blend (draft 2 state), apply the owner's feedback below,
render `qa10/draft_3.png` (quick still like drafts 1-2) + `qa10/draft_3_annotated.png` where useful,
`qa10/DRAFT-3.md` (what changed, open questions), a STATUS line - then STOP. Only write inside roxy3d/.

Owner feedback on draft 2 (full text in roxy3d/QUEUE-owner.md items 18-27; the big roof is liked):
18. Top-left: drop the low annex that covers the apartment block's windows; the brick apartment block itself
    extends all the way to the restroom wall, and that part is a blank party wall (no windows facing the cinema).
19. Corridor walls look empty (esp. the junction corner by the WC / 1-3 signs and the back walls): framed
    one-sheets of fictional films, a NOW SHOWING / COMING SOON board, wall clock, fire alarm + extinguisher
    cabinet, a framed cinema-history photo or two, a vending machine or payphone in the corner, sconces/neon
    accent - attached to walls, walker routes clear.
20. Roofs (theatre roof and the other roofs): decay and imperfection - stains, patched felt, rust streaks,
    debris, a tarp, a bent vent, grime/moss in corners, uneven parapet caps. (For the later animated pass: AC
    fans spin, one dead, one wobbling; one neon tube flickers - note in DRAFT-3 how you'll do it.)
21. All puddles, rings and crack lines look artificial: roof puddles = flat dark ovals -> irregular, soft-edged,
    shallow, reflective; remove the static thin ellipse rings on street/sidewalk (ripples only animated later);
    road cracks = black scribbles -> subtle sealed cracks/tar snakes, low contrast, broken, catching wet light.
    Everywhere, not just the cropped spots.
22. The back alley (right of the lobby, toward RECORDS & REPAIR): a real back alley - cracked, patched, uneven
    wet asphalt/concrete with potholes and grime (no neat tiles); dumpsters, trash bags, recycling bin, the
    cinema's emergency exit (lit EXIT sign, maybe propped with a brick), loading door, pallets, crates, steam from
    a vent, a fire escape, a real puddle reflecting neon. Leave room: more things will come here later
    (graffiti/posters with community in-jokes in the next phase).
23. Remove the short white "static rain trace" dashes baked into the front glass.
24. Living windows (later, page-driven): note in DRAFT-3 how you'd deliver per-window data
    (`windows: [{quad_px, z_index, lit, building}]` for every visible window) + a small sprite kit per event
    (light on/off, flicker, TV glow, silhouette passing behind the curtain, curtain move, cat on a sill, smoker's
    ember, party light). Nothing to render for it in this draft beyond making windows suitable (curtains/blinds
    variety, some interiors).
25. Far top-left: the cut-off "REPAIR" building at the frame edge -> a small cafe: lit shopfront to the street
    and a little outdoor seating area on the sidewalk (tables, chairs, parasols, menu A-board, string lights),
    wet, walker spawn lane (u ~ -6, v 9.78-10.05) clear.
26. End of the back alley (right of screen 3, under the theatre building): no black wall - the cinema's own
    exterior wall in the theatre building's masonry, lit by the alley, graffiti/tags, drainpipe, the emergency
    exit, a grimy service light. No black surfaces anywhere.
27. Cutaway: the purple band along the top of the corridor walls is ambiguous. Make every cut wall read like a
    Sims cutaway - a clean cap showing the wall thickness (core, inner purple finish, outer brick/stucco) on the
    corridor walls, restroom walls, partitions, left wing.
Also keep in mind for the next phase: graffiti walls, the poster wall, street/bus ads will carry subtle
community in-jokes (content from the page) - make good surfaces for them (ad_surfaces quads).
