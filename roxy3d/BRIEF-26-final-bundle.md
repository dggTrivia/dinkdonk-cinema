# Brief 26: FINAL RENDER bundle from draft 13 (owner said "start the final render")

The owner approved draft 13 and asked for the final render (out10) tonight on the rented cloud GPU, while he sleeps.
Rebuild the portable cloud bundle (same structure/contract as roxy3d/cloud/bundle and roxy-cloud-bundle.tar.gz from
BRIEF-21, keep run.sh modes preflight / smoke / full / validate-only, progress.log, "SUCCESS mode=" line, result
bundle/out10.tar.gz) from the CURRENT approved scene: roxy_pass10_draft.blend as saved by draft 13.

The final pack must include everything approved through draft 13 (see BRIEF-13 to BRIEF-25 and QUEUE-owner.md):
- layout-3 manifest (BRIEF-13): 3 screens, restroom (+ stall door anims, spots, route points), rope-lane queue,
  padded screen doors (door anims), led_signs, poster_frames, wc_indicator at the restroom door, ad_surfaces,
  bus-shelter bench seat spots, vehicles with "05 DINK DONK" / d.gg transit / DGG 05 branding;
- all art: memes (wcat + EatFresh rooftop billboards, WHIPLASH board, GLORP, shelter ads, bus-side ads, posters on
  walls, CABGE, ABSOLUTE CINEMA, restroom YEE vs PEPE vandalism, "Anything else?" neon), alley, shelter, cafe;
- draft 10 rain (wet layer, standing water, drips/pours/splashes, curb/gutter flow, hidden reflection catchers),
  approved soft ray-traced ripples (2 s cycle x3 in the 6 s loop), HDR glare;
- draft 11 dark-night lighting, draft 12 quieter restroom, draft 13 sign bulbs (dim, slow chase in the loop) and
  floodlights; DINK DONK emote neon alternating A/B (bell down/up) in a ring rhythm in the loop.
Speed settings as selected in BRIEF-21 (persistent data, adaptive 256/64/0.01, 48-frame cycle; no static/wet split).
Keep the drip/crown motion-blur limitation in mind (render them sharp, consistently).

Also add a self-protection to run.sh for unattended cloud runs: when the pipeline ends (success or failure), touch
DONE or FAILED; and if a pod-local `runpodctl` + env RUNPOD_POD_ID exist, a watchdog stops the pod 3 hours after the
run ends or 8 hours after start, whichever first (so a pod can't bill forever if the controlling laptop sleeps).
Re-run the local smoke test (laptop) to prove the rebuilt bundle; write roxy-cloud-bundle.tar.gz; STATUS line; stop.
Do NOT run the full render locally. Only write inside roxy3d/.
