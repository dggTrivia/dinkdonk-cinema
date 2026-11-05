# Brief 49 (RENDER, QUICK DRAFT ONLY): step markers must sit ON the steps (several look like they float)

Follows BRIEF-48 (`qa11/CINEMA-DRAFT-13-STEPDOTS.md`, `qa11/draft13_stepdots/`). Owner (04 Nov 2026, screenshot of the
left stair head by the green EXIT, top-left of the stalls): "some of these lights actually look like they are floating".
In that crop: a marker hangs at the top edge of the raised platform/landing, and several on the stair and row ends sit
in front of / above the tread edge instead of being set into it. The owner has not picked the brightness yet.

Local RTX 3050 GPU only; write only inside roxy3d/; no page files, no draft 11/12 assets or layouts touched.

## Do
1. Audit EVERY step marker (`STEP_DOTS`, the red emissive markers) in the draft 12 final scene against the real
   geometry: each must be mounted flush on an actual surface - a small recessed light in the RISER face just under
   the tread nosing (like real cinema step lights), or on the vertical face of a platform/landing edge, or in the
   floor at an aisle edge - never hovering in front of a nosing, over a gap, or at an edge with no surface under it.
   Re-seat each one onto the surface it belongs to (same aisle / step), and remove any that have no sensible surface.
   Keep a regular rhythm (one per step on the stair aisles, consistent row-end markers) so it still reads as
   wayfinding. List each marker with before/after position or "removed" in the report.
2. Quick renders with the corrected markers at both brightness levels from BRIEF-48: **V1 65 %** and **V2 45 %**.
   Native-pixel crops of: the owner's area (left stair head by the green EXIT, landing edge, first rows), the left
   stair aisle, the right aisle; lit state for both levels, plus V2 lights-down of the owner's area. Put a labelled
   side-by-side `qa11/draft13_stepdots/compare_placement.png` (today vs fixed V1 vs fixed V2) and a 2x-magnified crop
   of the owner's area (today vs fixed) `qa11/draft13_stepdots/owner_area_zoom.png`.
3. NO final 4K / slices / sheets / layout. Append to `qa11/CINEMA-DRAFT-13-STEPDOTS.md`, STATUS line, stop.
