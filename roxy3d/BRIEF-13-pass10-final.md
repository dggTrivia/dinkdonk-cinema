# Brief 13: pass 10 final (out10) - owner feedback on draft 1

Owner (12:45): "Glass tint is good enough. The stalls are okay. The DINK DONK sign is okay." Changes:
1. **The DinkDonk emote neon must be the actual emote.** Reference: roxy3d/ref/dinkdonk-emote/DinkDonk-x12.png
   (12x nearest-neighbour of the 36x30 DGG emote; the original is an APNG with 2 frames). It is Pepe (green frog,
   white eyes, orange-brown lips) wearing a big yellow pointed hood/cone, holding up a small gold hand bell on a
   stick that he rings. Your draft traced it as lips - redo both neons (rooftop emblem + entrance blade) as
   that: yellow hood outline, green frog face with white eyes and the lips, gold bell. In the loop, swing the
   bell between two positions (2-frame ring, like the emote), seamless.
2. **One building behind the theatres.** Not separate tiered blocks: the three auditoriums are one single big
   building, and it fills the WHOLE top-right part of the frame - no background buildings may be visible
   anywhere in the top right any more (it runs off the top and right edges of the frame). DINK DONK sign and the
   relocated roof billboard stay on its roof. Plain, believable 90s multiplex exterior (masonry/stucco, service
   doors, ladders, HVAC, booths, drainpipes, wet roof with puddles, rain on it).

Workflow: apply these, render `qa10/draft_2.png` (quick still, like draft 1) + a STATUS line, then DO NOT stop:
continue straight into the complete out10 pack (all the usual products: 1x/2x stills, lit_bg/lit_bg_dry,
occluders + depth slices for every new/changed foreground piece - ropes/stanchions, restroom walls/stalls,
street wall, corridor props in front of walkers - light_loop + light_loop_2x + rain_fg, prop loops incl. the
bell swing and poster bulbs, door sheets with the dark vestibules, glass water, vehicles with the d.gg transit
branding, ad_surfaces, led_signs, wc_indicator, validations, NOTES-PASS10.md).

## Manifest for layout 3 (the page switches on `"layout": 3`)
- `layout: 3`, `doors: [{screen:1..3, wall:'v0', at:4.8|8.2|11.2, approach:[[at,1.4],[at,0.55]]}]`
- `led_signs` and `poster_frames` numbered by the new screen 1-3.
- `restroom: { door: [1.4,3.0], outside: [1.4,2.6], inside: [1.4,3.5], stalls: [{spot:[1.5,4.4], door_anim:{sheet
  contract like door_anims: open-hold-close, 1x/2x, x,y,z_index}} x4], sinks: [[2.12,4.10],[2.63,4.10]],
  dryer: [0.55,3.55], door_anim: {...} }` - all standing spots verified reachable from `inside` with straight
  segments that clear every fixture (give a waypoint list if needed: `route_points`).
- `wc_indicator` at the new restroom door (vacant/occupied, as before).
- `queue: { slots: [[4.85+0.62i, 7.4] i=0..6], entry: [9.3,7.4], window2_gap: [4.4,5.79] }` (ropes as built).
- Everything else as in out9 (vehicles, stops, lanes, items, umbrella, cat, prop loops, ad_surfaces...).
Only write inside roxy3d/.
