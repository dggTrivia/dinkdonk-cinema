# Brief 46 (RENDER, QUICK DRAFT ONLY): auditorium entrance door = the lobby's current door, not stretched

Owner (04 Nov 2026, screenshot of the auditorium's rear entrance): "the door looks kinda stretched, and it's using the
old door version".

Both are true:
- Draft 10/11 reused the pass-9 lobby screen-1 leaves (orange lit portholes). The lobby has since moved on: owner
  item 46 in `QUEUE-owner.md` = classic padded theatre doors (diamond-button upholstered leather/vinyl, brass push and
  kick plates), NO lit porthole windows. That is the door in the approved lobby pass (`out10`, see
  `out10/NOTES-PASS10.md`, `out10/manifest.json` `door_anims` / `doors`, and the lobby build scripts that made them).
- The leaves were scaled non-uniformly into the tunnel portal: the lobby opening is 1.1 tiles x 114 zpx (height/width
  1.73), the portal opening is u 0.30-2.65 (2.35 tiles) x 139 zpx (0.99), so each leaf is ~1.75x too wide.

## Do (quick draft, local RTX 3050 GPU only, write only inside roxy3d/)
1. Start from the draft 11 scene (`roxy_cinema_draft11.blend` / `build_cinema_draft11.py`). Change nothing else.
2. Put the lobby's CURRENT padded double door (same model/materials as out10, read-only from the lobby files) in the
   portal at UNIFORM scale, so it reads as the same door as in the lobby. Keep its height close to the portal (about
   130-139 zpx) and its width at the lobby proportion (~1.3 tiles at that height). Fill the rest of the portal width
   with the same wall finish (or a matching fixed side panel/frame if that reads better), keeping the door centred on
   the walk route (spawn u = 1.45; route `rear_portal_to_cross_aisle` in the layout) so arrivals still walk straight
   through. The green EXIT on the guard post and everything else stays.
3. Render a QUICK 1080p draft: `qa11/cinema_draft_12_door.png` and a native-pixel 4x crop of the door area
   `qa11/cinema_draft_12_door_crop.png` (closed), plus one crop of the door fully open (the pose the page's sheet holds
   at frames 5-10) as `qa11/cinema_draft_12_door_open_crop.png`. Lower samples are fine; this is for the owner to judge.
4. NO final 4K, NO slices / door sheets / dim set / layout changes yet - those follow only after the owner approves
   the look. Do not touch `cinema_layout_11.json`, `draft11*`, or any page file.
5. Report `qa11/CINEMA-DRAFT-12-DOOR.md`: what you used from the lobby (file/object names), the final door and
   opening dimensions (u range, height), and what the full pass would need to regenerate afterwards (beauty 1x/2x,
   depth slices, entrance sheet + static cutout, dim set; the page also uses banded slices made by
   `tools/band-slices.mjs`, which must be re-run on the new slices). STATUS line, stop.
