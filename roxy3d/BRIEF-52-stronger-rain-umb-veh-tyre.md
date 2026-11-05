# Brief 52: STRONGER pass of draft 20 (umbrella rain, vehicle-top impacts, tyre spray + wake) - draft only

Owner on draft 20 (qa10/draft20-rain-umb-veh-tyre.png): "make a stronger pass". Claude's read: physically fine but at
the live 1x scale the impacts and the spray barely read. Your own read-only critique is in codex-51-critique.txt -
follow its numbers as the starting point (they are the spec unless you find a concrete reason, then say it):
- Umbrella: clearly readable canopy hits (1-2 px broken highlights, occasional 3 px clusters, 1 px lift, rare 2 px
  ejected glint) + tip drips that read at 1x; keep it a red canopy, not a sparkling crust.
- Vehicle tops: taxi 18-26 readable hits/s (roof 8-12, bonnet 6-8, boot 4-6), bus 30-45/s; impact cores +25-45
  levels, rare +50-60; film +3-8; 2-4 frames per event. Taxi sign: cut the added yellow band/glow by ~50-70%
  (keep a restrained wet reflection, no luminous outline).
- Tyre spray: separately readable contact origin, ballistic droplet fan and porous trailing mist; rear plume
  sedan 18-30 px long x 3-6 px high, bus 25-45 x 4-8; front 8-15 x 2-4; rear 1.5-2x front; droplets 40-60/s per
  exposed rear wheel, 15-25/s front, 1 px cores with 1-3 px streaks, 3-6 frames; mist +10-18, droplet cores +25-45;
  not a uniformly red cloud or white steam.
- Wake: two broken road-flat tracks behind the rear tyres (sedan 20-40 x 2-3 px, bus 30-50 x 3-4), +5-10 levels with
  +12-18 fragments, deposited on the road and fading in 0.25-0.5 s (the page can scroll it with the vehicle; say how).
- Loops: 48 frames / 2 s at 24 fps with irregular release timing (less visible repetition). Crop unused margins.

Same scope as draft 20 (red umbrella, taxi +u roof, bus +u roof, bus +u + sedan_a +u spray), same anchors/contracts,
staging in a new folder roxy3d/out10f/ (keep out10e as the draft-20 reference).

## Deliver
- ONE owner image qa10/draft21-rain-stronger.png, 1280x720, composited INTO the real out10 frame (lit still + baked
  rain look, not dark panels): top half = 1x crops at true page scale (an umbrella group on the sidewalk, the taxi and
  the bus driving on the street at their lanes), bottom half = the same at 2x; for each, draft 20 | draft 21 at the
  same loop phase. Small labels only.
- NOTES-52.md (what changed vs draft 20 with numbers, sizes/VRAM, times), STATUS line, stop.
Do NOT modify roxy3d/out10/, out10e/, any other pack, or standby/roxy.html. Write only in roxy3d/. Local GPU, no cloud.
