# Brief 12: pass 10 - DRAFT FIRST (new workflow)

The owner reviewed out9 and wants faster feedback rounds: **this run only produces a quick draft and then
stops.** Model the changes below in the scene, render a fast lit still of the whole 1920x1080 frame (Eevee
or low-sample Cycles + denoise - minutes, not the full pipeline; no loops, no sprites, no slices, no 2x), plus
an annotated copy with the new walkable areas/footprints outlined and labelled. Save
`qa10/draft_1.png`, `qa10/draft_1_annotated.png`, a short `qa10/DRAFT-1.md` (what changed, open questions,
the coordinates below as you actually built them) and a STATUS line in `qa10/STATUS.md`. Then STOP and end
your turn - the final pass (out10) comes after the owner's feedback. Only write inside roxy3d/.

## Floor plan changes (layout 3)
1. **Only three screens, all in the right wing.** Keep the three doors on the v = 0 wall at u 4.8, 8.2, 11.2
   (they are now screens 1, 2, 3, left to right). Remove screens 1-2 on the left (doors, posters, LED housings).
2. **The auditoriums exist.** Behind the v = 0 wall build the three big halls as one block (each about a third of
   u 3..13, several tiles deep toward -v, clearly taller than the corridor wall): plain exterior walls, roofs with
   projection booths, HVAC, ducts, roof hatches, puddles. The apartment/tower block that sits right behind the
   doors today goes. Owner: "right now they look like portal doors".
3. **DINK DONK.** The cinema is now called DINK DONK (as in dinkdonk.mov). A big **rooftop neon sign on the
   auditorium block**: "DINK DONK" letters plus the DinkDonk emote drawn in neon tubes (reference:
   roxy3d/ref/dinkdonk-emote/DinkDonk.png - a green frog in a yellow warning triangle), classic 90s rooftop sign
   on a steel frame, real tubes/glow, reflected in the wet street. The entrance blade sign (today "d.gg") becomes a
   small neon of the DinkDonk emote (+ maybe "DD" or "DINK DONK" small). d.gg stays only as a small nod:
   the bus line "d.gg transit" (bus sides/front), maybe one shop or street sign. The tower billboard ad surface
   moves to a clear spot (e.g. a rooftop billboard on the auditorium block or a side wall) - keep `ad_surfaces`.
4. **The left wing becomes the restroom.** Its own cut-away room in the left wing (u 0..2.9), from about v 3.0
   down to where the box office ends (~v 8.4; the front-left bit stays a small dead corner/closet): 3-4 toilet
   stalls with doors (along the u = 0 wall), sinks with mirrors, a hand dryer, tiles, a trash can, a mop sink.
   Entrance: a door from the corridor junction (around u 1.4 on the v = 3.0 inner wall), so the route stays
   gate (3.7,3.7) -> junction (1.4,1.4) -> restroom door, or -> the right-wing corridor. Restroom sign plaque +
   the red/green occupancy light move to that door. The junction u 0..3, v 0..3 stays corridor.
   Walkable spots inside for the page: in front of each stall, each sink, the dryer.
5. **The front wall of the left wing** (beside the bus stop, today the low half wall u 0..3 at v ~9): solid,
   full height (brick/plaster, maybe a small high window), as an occluder.
6. **Ticket queue with stanchions and red velvet ropes.** The queue lane runs along v 7.4 from the windows
   (4.85, 7.4) toward +u (slots every 0.62 u, up to ~u 8.6). Front rope about v 7.8 from u ~5.2 to ~9.2; back rope
   about v 7.0 from u ~5.9 to ~9.2 (leave the gap by the windows so the next customer can step to window 2 at
   (4.85, 6.0)); the lane opens at its far end (~u 9.3) toward the entrance.
7. **Snack counter alive:** cash registers at the three registers (u 6.6, 8.2, 9.8), napkin/straw dispensers,
   cup and tub stacks, a candy display case, a tip jar, a nacho cheese pump... on/behind the counter, nothing in
   front of it.
8. **Doors open into darkness:** the door-open sheets show a dark vestibule/curtain, not brick.
9. **Corridor dressing** (right-wing corridor u 3..13, v 0..3) so it isn't empty: cardboard standees of other
   (original, fictional) films, a "COMING SOON" lightbox, a bench, a drinking fountain, an EXIT sign, a fire
   extinguisher, a trash can, carpet runner. Keep the walking band v 0.9-2.0 and each door approach
   (u = door +-0.5, v 0..1.4) clear; things go against the walls (v <= 0.5 between doors, v >= 2.4 on the
   lobby partition side).
10. **Front windows:** the full-height storefront currently reads as empty frames - make the glass itself
    visible (tint, reflections of street lights, grime, light on the edges) while people inside stay readable.

Keep everything else (camera, street, traffic, lobby, envelopes, the in-world rule: no screen-facing signs).
