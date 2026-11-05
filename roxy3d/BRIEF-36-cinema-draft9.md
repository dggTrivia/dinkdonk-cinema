# Brief 36: SCENE 2 auditorium, DRAFT 9 - light the tunnel mouth

Owner on draft 8 (`qa11/cinema_draft_08.png`): go ahead with lighting the tunnel mouth. Only this change;
everything else stays exactly as draft 8 (`build_cinema_draft8.py`, `qa11/cinema_layout_08.json`).

Strict draft rule: ONE image `qa11/cinema_draft_09.png` (1920x1080, same Cycles settings), `qa11/CINEMA-DRAFT-09.md`,
`qa11/cinema_layout_09.json`, STATUS, STOP. New files only (`build_cinema_draft9.py`, `roxy_cinema_draft9.blend`,
`qa11/runtime09/`). Only write inside roxy3d/.

## The change
In draft 8 the tunnel mouth (v ~9.4) and its lower approach (the three 8-unit steps up to the cross-aisle, u ~0.3-2.95,
v ~5.2-9.4) read as a dark pit; walkers only become readable a few steps past the mouth.
- Warm light spilling out of the tunnel mouth onto the approach floor and steps (as if the corridor behind is lit),
  a soft pool that makes the approach read as a walkway; a little warm light on the sectional notch's jamb/soffit.
- A few low step lights on the approach steps (same red-orange style as the stairs, on +z / +u faces the camera sees).
- A small green EXIT sign at the mouth that is visible from the camera (e.g. on the +u face of the notch / on the
  guard post), in addition to the rear-portal EXIT.
- Keep it moody: no hot spots, nothing bright behind where walkers' faces pass, the screen unaffected (zero light on
  it from these lamps).
- No geometry, seat, rail, stair, route or screen change. If a tiny geometry tweak at the notch would clearly help
  the walkers' reveal, describe it in the report instead of doing it.

## Report
Approach-floor and notch luminance before/after (same delivered-image metric as draft 8), the new light objects and
their collection (switchable), the walker visibility table along the route (unchanged geometry, for reference),
screen luminance unchanged check, render time.

One image, then STOP.
