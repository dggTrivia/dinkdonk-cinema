# Brief 51: rendered rain on umbrellas + vehicle roofs, and tyre spray (DRAFT ONLY, live pack untouched)

Owner (04 Nov): rain should visibly hit the umbrellas and the tops of cars and buses, and tyres should throw a rain
streak/spray as vehicles drive through the wet - and these "more permanent" effects should come from the renderer
because they look better (Claude's in-page canvas splashes were tried and removed). Earlier queue items 32-34 asked
for the same physical rain language: crowns, beading, run-off, drips off hems (QUEUE-owner.md).

Live facts (out10 manifest): umbrellas = 4 colours, open sprite 88x80 (anchor 44,68), fold sheets 6 frames @12 fps.
Vehicles bus/taxi/sedan_a/sedan_b, +u/-u, closed + door_open, whole-body PNGs + depth slices + light passes.
tyre_spray = one-shot 12-frame 96x56 sheets per direction (the page fires one now and then off the rear wheel).
Baked loops run at 24 fps (48 unique frames per 2 s). Rain in the scene falls near-vertical.

## Do (draft quality, local GPU)
1. Umbrellas: rain impacts on the canopy (small crowns, a wet sheen/beading) and run-off dripping off the rib tips,
   as a seamless loop at 24 fps (24 or 48 frames), same frame size/anchor as the open sprite so the page can swap the
   static sprite for a sheet. One colour is enough for the draft.
2. Vehicle tops: impacts on roof, bonnet and boot (crowns + a thin water film/sheen), as an additive overlay loop at
   24 fps aligned to the whole-body sprite (say how you'd cut it into the existing depth slices for production).
   Draft: taxi +u and bus +u only.
3. Tyre spray while driving: a continuous spray plume/mist off each wheel (strongest at the rear wheels, lit by the
   vehicle's own lights and the street) plus a short wet wake behind the vehicle, as a loop sheet anchored to the
   vehicle (or per wheel) that the page shows while the vehicle moves and fades with speed. Draft: bus +u, sedan +u.
4. Keep everything physically plausible for the scene's scale and lighting (night, draft-15 vehicle lighting); no
   cartoon splashes. Say sizes, frame counts and file sizes; keep sheets small enough for the page (estimate VRAM).

## Deliver
- Staging files in roxy3d/out10e/ (new folder) only.
- ONE owner image qa10/draft20-rain-umb-veh-tyre.png, 1280x720: three rows (umbrella at 3x, taxi roof at 2x, bus
  driving with tyre spray at 1x), each before | after, the "after" showing 3 frames of the loop side by side so the
  motion reads. Small labels only.
- NOTES-51.md (what, how, sizes, render times, production plan), STATUS line, stop.
Do NOT modify roxy3d/out10/, any other pack, or standby/roxy.html. Write only in roxy3d/. No cloud.
