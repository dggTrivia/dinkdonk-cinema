# Brief 29: SCENE 2 auditorium, DRAFT 2 - bigger, lived-in, fills the frame

Owner reviewed `qa11/cinema_draft_01.png`: the direction is right (camera, screen, stadium rows, door, aisle,
plaque). Draft 2 = the same scene, changed as below. Same strict draft rule: exactly ONE image
`qa11/cinema_draft_02.png` (1920x1080, house lights up), `qa11/CINEMA-DRAFT-02.md`, `qa11/cinema_layout_02.json`,
one STATUS line, STOP. New files only (`build_cinema_draft2.py`, `roxy_cinema_draft2.blend`); keep draft 1's files
as they are. Everything in BRIEF-28 still applies unless changed here. Only write inside roxy3d/.

## Changes
1. **A bigger cinema.** It should feel like a large single-screen picture palace, not a small multiplex room:
   - more rows (about 9-10) and longer rows (about 16-20 seats), keep the stadium rise;
   - a taller room with a visible ceiling structure at the top (dark ceiling, lighting truss / cloud panels /
     ornate cornice - your call, 90s picture-palace feel);
   - the screen grows with the room: make it as big as the new room allows (still 16:9, still on the v = 0 wall,
     every BRIEF-28 screen rule unchanged: clean four-corner quad, nothing overlapping it, matte, unlit).
2. **Fill the frame.** Draft 1 left a lot of black around the room. The room may now run off the frame edges
   (left, right, bottom - the rows and the slab can be cut by the frame), like the lobby's surroundings fill its
   frame. Only small dark corners are acceptable. You may move Ox, Oy (report them).
3. **Lived-in, like the lobby (same grit level as draft 13):** worn traffic paths in the aisle and cross-aisle
   carpet, spilled popcorn and a few cups/boxes under seats, a couple of faded / patched (gaffer tape) seats and
   one seat stuck half-folded, dust and sun-fade on the curtains, scuffed brass handrail, slightly stained
   acoustic panels, warmer and moodier pools of sconce light (less even fill, darker between the pools). No haze
   or fog (it would cross the screen).
4. **The front is less bare:** a narrower stage with a footlight lip, speaker stacks / proscenium pillars either
   side of the screen (outside the quad), the front cross-aisle kept walkable (chatters use it).
5. **Zoom headroom:** the page's zoom director magnifies the world up to 1.85x while following a chatter, and
   the final will be 4K. Prop and material detail (seats, plaque, door, carpet) must hold up at that zoom. The
   draft stays 1920x1080.

## Keep
- Camera, ortho scale, ZPP, projection form; calibration check as in draft 1.
- Entrance door + EXIT near the stage on the u = 0 wall, side aisle with lit half-steps and handrail, DINK DONK
  Screen 1 plaque (off the screen), house-light collections switchable, each row's seat backs as its own object.
- Seat pitch around 0.88 tiles is fine.
- No projection booth / beam (the booth wall is on the cut-away side and a beam would cross the screen).

## Report (same as draft 1, for the new layout)
Ox/Oy + calibration errors; screen corners at 1080p and 4K + wall coordinates; room footprint; per-row seat
line v, tier floor zpx and seat u positions (JSON); door and aisle path points; the audience clearance check
using the page's real emote size: height 50 px, width up to 74 px, bottom-anchored on the cushion; render time.

One image, then STOP.
