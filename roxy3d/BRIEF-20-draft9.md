# Brief 20: DRAFT 9 - one image, then stop

Strict draft rule: exactly ONE image - the fixed isometric camera, 1280x720 at final quality with the weather frame
-> `qa10/draft_9.png`. Nothing else (no close-ups, review cameras, clips, extra audits or re-renders, no out10).
One STATUS line, a few lines in `qa10/DRAFT-9.md` (incl. what caused each problem), then STOP. Work from the draft 8
scene. Only write inside roxy3d/.

Two fixes on draft 8 (owner: "yes, fix those"):
1. Thin straight white lines run from the EatFresh billboard on the top-left roof across the theatre roof toward
   the DINK DONK sign (roughly x 520-1260, y 30-190 in draft_8.png). Find out what they are (stray cables/wires
   from the moved billboard, leftover geometry from its old spot, glare streaks from the four-point aperture
   glare, or reflections) and remove them - nothing should read as stray lines.
2. Odd white blotches on the dark roof at the bottom right (roughly x 1080-1280, y 520-600). Find the cause
   (puddle material, specular hits, litter/debris, a fireflies issue) and fix it so the roof reads as a wet dark
   roof like the others.
