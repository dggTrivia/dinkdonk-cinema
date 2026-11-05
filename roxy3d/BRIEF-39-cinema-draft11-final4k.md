# Brief 39 (RENDER): auditorium draft 11 = polish pass + the final 4K asset set (local GPU)

Owner (03 Nov, overnight): keep iterating until it is good, then the final 4K render - on THIS laptop's GPU (RTX 3050
6 GB), no cloud: the auditorium has almost no animation. Only write inside roxy3d/. Do not touch any page.

## Step 1 - fresh-eyes review of draft 10 (yourself)
Look at `qa11/cinema_draft_10.png` and the live page screenshot `qa11/page_draft10_live.png` (chatters, bubbles,
names on top of it) as a late-90s pre-rendered game background shown on a 1080p stream. Write the list of what is
not good yet into `qa11/CINEMA-DRAFT-11.md` (lighting balance, readability of the stepped tiers, cut wall, rear door,
red emergency EXIT, wheelchair plaques, litter, materials/noise, anything that looks wrong or unfinished, and
anything that fights the chatter emotes for attention).

## Step 2 - fix what is clearly fixable WITHOUT changing the approved design
Locked: camera, framing, layout, every seat centre, tier heights, aisles, stairs, tunnel, route, entrance door
position, emergency exit position, the screen quad (no light on it, no hot spots), colours the owner chose (dark and
muted, dark navy-blue pleated walls, deep purple seats, red curtains, red step dots, blue wheelchair plaques on row B
only, green EXIT at the tunnel mouth, red EXIT on the emergency door). Polish only. If something needs a design
change, list it for the owner instead of doing it.

## Step 3 - deliverables
- `qa11/cinema_draft_11.png` (1920x1080) - the owner's morning review still.
- `qa11/cinema_draft_11@2x.png` (3840x2160) - the final 4K background (render natively at 4K, or 4K + exact 2x2
  area downscale for the 1x as in the lobby pipeline; say which).
- `qa11/draft11/` - page layers for BOTH scales, regenerated from these exact images: depth slices (same contract as
  draft 10's `page_layers.slices`, plus `file_2x` per slice: same x/y/w/h in 1080p stage coordinates, the 2x file has
  double pixels), entrance door sheet + `file_2x`, and the door static-cutout mask + its 2x.
- `qa11/cinema_layout_11.json` = draft 10's layout JSON updated, with `page_layers.image_2x` (the 4K background),
  `file_2x` on every slice and on the door, everything else as draft 10 (the page reads `cinema_draft_11.png` and
  `cinema_layout_11.json` with ?draft=11).
- Checks as draft 10 at both scales (bg + slices = bg exactly; slice/ray visibility agreement; screen unchanged;
  calibration). Render times per pass. Keep runtime/caches under `qa11/runtime11/`.

If the 4K render would take more than ~3 hours on this GPU, render the 1x set first, write the report, then do the 4K
and update the report when it is done. STATUS line, stop.
