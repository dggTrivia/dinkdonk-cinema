# Brief 47 (RENDER, FULL PASS): draft 12 = draft 11 + the approved lobby door, final quality, all page assets

Owner approved the BRIEF-46 quick draft look on 04 Nov 2026 ("Yes, do the full pass"): the lobby's current padded door
at uniform scale (139/114), centred at u = 1.45, fixed infill either side (`roxy_cinema_draft12_door.blend`,
`build_cinema_draft12_door.py`, report `qa11/CINEMA-DRAFT-12-DOOR.md`). Change nothing else in the scene: no new
lights, same camera, same exposure/view, same materials.

Local RTX 3050 GPU only. Write only inside roxy3d/. Do not edit any page file and do not modify draft 11 assets or
`cinema_layout_11.json` (the live page keeps using them until Claude switches).

## Deliverables (same pipeline and checks as draft 11 / BRIEF-39, and the dim pass / BRIEF-42)
1. Lit beauty at final quality: `qa11/cinema_draft_12.png` (1920x1080) and `qa11/cinema_draft_12@2x.png` (native 4K,
   1x = exact 2x2 area reduction as before).
2. Depth slices for draft 12 at both scales (`qa11/draft12/slices/`), same slicing rules / key ranges / naming as
   draft 11, with bg + slices = bg exactly.
3. Entrance door: new 16-frame 4x4 sheets for the new leaves (`qa11/draft12/door_entrance(.png/@2x)`), same fps / open
   hold frames 5-10 / closed endpoints exact, new static cutout + affected slice list, the new spawn wait if the
   smaller leaves open faster (keep the arrival route straight through u = 1.45).
4. Lights-down set for draft 12 exactly like BRIEF-42: `qa11/cinema_draft_12_dim(.png/@2x)`, `qa11/draft12_dim/`
   slices with identical names / rects / masks, dim door sheet.
5. `qa11/cinema_layout_12.json`: a copy of `cinema_layout_11.json` with every draft-11 asset path switched to the
   draft-12 ones (incl. `page_layers.dim`, `entrance_door`, `static_slice_cutout`), and the door geometry updated.
   Do NOT add `pieces` (Claude re-runs `tools/band-slices.mjs` on your slices afterwards; your slices must keep the
   RGBA8 non-interlaced PNG format the tool reads).
6. Report `qa11/CINEMA-DRAFT-12.md` with the verification table (geometry lock vs draft 11 except the door, slice
   reconstruction, door endpoints, dim masks identical, screen unlit/unchanged), render times. STATUS line, stop.
