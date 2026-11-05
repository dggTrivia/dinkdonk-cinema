# Brief 33: SCENE 2 auditorium, DRAFT 6 = blockout v2 (layout only)

Owner on blockout 5: better - the level rows work and the last rows are fine. Changes below. Same quick blockout
format as draft 5 (Workbench boxes, flat colours, labels drawn on the one image), same strict rule: ONE image
`qa11/cinema_draft_06_blockout.png`, `qa11/CINEMA-DRAFT-06.md`, `qa11/cinema_layout_06.json`, STATUS, STOP.
New files only (`build_cinema_draft6_blockout.py`, `qa11/runtime06/`). Only write inside roxy3d/.

Reference: `roxy3d/ref/childhood-cinema/08-seat-map.png` - the seat map of the owner's cinema ("PANTALLA" =
screen at the top). The owner says it is INDICATIVE, a guide to how the layout feels, not a rule to copy 1:1.
Reading it with the audience facing the screen: audience-left = low u (the u = 0 wall, our entrance side),
audience-right = high u (the cut-away side).

## Changes
1. **Remove row A** and leave a clear, generous gap between the stage/screen and the first seats.
2. **Front section (near the screen):** a short section split into blocks by aisles, like the top of the seat
   map: a small block (2-3 seats) at each side, the main block in the middle, an aisle between each. Keep it to the
   former row B plus at most one more row; it must not feel close to the screen.
3. **Clear separation between the front section and the bank:** B and C currently read as one lump. Put a wide
   cross-aisle (at least ~1.5 tiles, with the divider wall) between the front section and the raised bank.
4. **Extend the hall backwards: 3-4 more rows** in the raised bank (so about 7-8 bank rows), same gentle rise
   (~16 zpx_world per row) and ~1.4-tile row pitch. To fit this in the frame, **lower the walls** on both
   sides (the owner finds them too tall; ~500-550 zpx_world instead of 650) and let the screen shrink with them
   (keep it as large as the lower wall allows, all screen rules unchanged). If it still does not fit, you may
   raise ortho_scale up to 32 (report k). Whole hall in frame with dark margins, as before.
5. **Bank rows are not straight full-width rows** (seat map, lower part): along each row, from u = 0 side to the
   cut side: a short block of 1-3 seats, then an aisle running up to the back of the hall, then the long main
   block, then another aisle, then a narrow block of ~2 seats at the right edge. On the left (u = 0 side), the
   first several bank rows leave a blank area where the stairs from the entrance come up into the hall; further
   back the left seats return. The last row may run the full width.
6. **Entrance:** EXIT passage on the u = 0 wall opening onto the cross-aisle; route passage -> cross-aisle ->
   left aisle / stairs (the blank area) -> up -> row. Draw the route as before.
7. **Fix:** draft 5's stair block that hangs below the floor slab; the cluttered labels (row letters sitting on
   other labels, a stray "OUT" text fragment near the top). Put row letters in a clean column outside the room.

## Notes for the styled draft later (do NOT do now)
Walls much more muted and darker, room less lit overall, seats purple (not pink), EXIT in English.

## Report
Ox/Oy, ortho_scale/k if changed, wall height, screen corners 1080p/4K + wall coordinates, row table (v, floor
zpx_world, seat u list split by block) in JSON, aisle positions, per-row-pair on-screen separation (>= 25 px),
screen clearance for seated 50k x 74k emotes, route points, seat total, render time.

One image, then STOP.
