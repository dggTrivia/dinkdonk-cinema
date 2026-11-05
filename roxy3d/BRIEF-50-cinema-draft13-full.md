# Brief 50 (RENDER, FULL PASS): draft 13 = draft 12 + re-seated step markers at V2 (45 %)

Owner approved (04 Nov 2026): the BRIEF-49 placement fix (all 67 markers re-seated as flat inserts on real surfaces,
`qa11/CINEMA-DRAFT-13-STEPDOTS.md`) at brightness **V2 = 45 % (emission 1.71)**. Use that exact scene state
(`qa11/draft13_stepdots/roxy_cinema_draft13_stepdots_v2*.blend` / its builder); change nothing else.

Local RTX 3050 GPU only. Write only inside roxy3d/. No page files; do not modify draft 11/12 assets or layouts.

## Deliverables - same pipeline and checks as BRIEF-47 (draft 12)
1. `qa11/cinema_draft_13.png` + `@2x` (native 4K, 1x = exact 2x2 area reduction).
2. `qa11/draft13/slices/` both scales (same slicing rules, names, rects; bg + slices = bg exactly).
3. Entrance door sheets + static cutout for draft 13 (`qa11/draft13/`), re-rendered or verified against the new beauty
   (same geometry/fps/hold/endpoints).
4. Lights-down set: `qa11/cinema_draft_13_dim(.png/@2x)`, `qa11/draft13_dim/` slices (identical names/rects/masks),
   dim door sheet.
5. `qa11/cinema_layout_13.json` = `cinema_layout_12.json` (WITHOUT its `pieces`) with every asset path switched to
   draft 13. No `pieces` (Claude bands the slices afterwards; keep RGBA8 non-interlaced PNGs).
6. Report `qa11/CINEMA-DRAFT-13.md` (verification table incl. geometry lock vs draft 12 except the markers, slice
   reconstruction, door endpoints, dim masks identical, screen unlit), render times. STATUS line, stop.
