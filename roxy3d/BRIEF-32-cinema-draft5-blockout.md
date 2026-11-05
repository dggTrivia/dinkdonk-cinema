# Brief 32: SCENE 2 auditorium, DRAFT 5 = a quick BLOCKOUT (layout only)

Owner on draft 4: layout first. Make a really quick draft with basic boxes and simple locations of everything, so
he can give layout feedback before any styled render (the same workflow as the lobby's blockouts). No materials,
no wear, no lighting work. The owner's words override the reference photos wherever they differ.

Exactly ONE image `qa11/cinema_draft_05_blockout.png` (1920x1080), `qa11/CINEMA-DRAFT-05.md`,
`qa11/cinema_layout_05.json`, STATUS line, STOP. New files only (`build_cinema_draft5_blockout.py`,
`qa11/runtime05/`); a .blend is optional. Only write inside roxy3d/. Aim for minutes, not a polished render:
Workbench or EEVEE with flat colours per element type is fine.

## Keep
Camera (60, 0, 45), ortho_scale 30, k = 0.754247, Ox = 800, Oy = 548; whole hall in frame with dark margins; the
screen quad on v = 0 at the same corners as drafts 3/4 (u 3.4-15.4, zpx_world 90-586).

## Layout changes (owner)
1. **Seats much more level.** The stadium rise is too steep - make it 50-75 % flatter: about 12-20 zpx_world
   per row instead of draft 4's 48. Also space the rows like a real cinema: row pitch about 1.4 tiles (seat pitch
   stays ~0.8). Goal: in the image every row reads as its own line. Report, per row pair, the on-screen distance
   between the rows measured perpendicular to the row direction: `k*|2*dz - 120*dv| / sqrt(5)` px - it must be
   at least 25 px (draft 4 had about 6 px, which is why the rows merged into one band).
2. **A staircase with seats on both sides of it.** The stairs should run up between two seat blocks (a smaller
   block between the u = 0 wall and the stairs, the main block on the other side), instead of hugging the wall
   with all seats on one side. This is my reading of the owner's note "we don't have the row in between the
   staircase" - the labels let him confirm or correct it.
3. **Entrance passage** at the bottom of the stadium on the u = 0 wall (as draft 4), sign reads **EXIT** (not
   SALIDA). Route: passage -> landing / front cross-aisle -> foot of the stairs -> up the stairs -> row.
4. Keep: two low front rows on the flat floor in front, the low divider wall between them and the raised bank,
   the stage and front cross-aisle, the speaker stacks beside the screen, wall lights / wall speakers as simple
   boxes, the DINK DONK plaque as a box.

## How the blockout should look
- Flat, clearly different colours per element type: walls dark grey, floor/tiers mid grey, stairs light grey,
  each seat a simple box (seat + back) in purple, screen white, stage brown, divider dark red, entrance passage
  black with a green EXIT box, speakers black, plaque cyan. Simple sun + ambient so the tiers' step edges and the
  seat rows read.
- Draw labels onto this one image (PIL/PowerShell overlay is fine): row letters at the left end of each row,
  "STAIRS", "ENTRANCE / EXIT", "STAGE", "SCREEN", "DIVIDER", "FRONT AISLE", and the walk route as a thin dotted
  line from the passage to the back row.

## Notes for the next styled draft (do NOT do now, just keep in mind)
Owner: walls much more muted and much darker, the room less lit up overall; seats purple (not pink/mauve); EXIT
signs in English.

## Report
Ox/Oy, row table (v, floor zpx_world, seat u list, seat count per block) in JSON, the per-row-pair on-screen
separation in px, screen clearance for seated 50k x 74k emotes, the passage -> stairs -> rows route points,
render time.

One image, then STOP.
