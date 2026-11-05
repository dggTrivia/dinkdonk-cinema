# Brief 15: DRAFT 4 - new draft standard + visual-fidelity tests (then stop)

Standing rules: drafts only, no full render / out10 until the owner says "final render". Work in
roxy_pass10_draft.blend (draft 3 state). Only write inside roxy3d/. The owner cares about visual fidelity, not
render time.

## New draft standard (owner)
Drafts are now ONE 1280x720 frame at FINAL quality (final samples, wet materials, real reflections) plus ONE
composited weather frame (rain streaks, splashes, puddle reflections, wet roofs) - the real look of the final,
minus the page layers. Save `qa10/draft_4.png`.

## Owner feedback for draft 4 (QUEUE-owner.md items 29-31)
29. Top-left apartment roof (extended to the restroom wall): one continuous roof - same felt, no seam line, one
    parapet all round; spread the rooftop kit (AC units, vents, skylights, hatch, pipes) believably over the
    whole roof instead of bunched together.
31. Reflections must match their real sources. The big green smear on the street is the old d.gg blade's
    reflection left in a stale reflection layer. Re-render every reflection from the CURRENT scene (DinkDonk
    blade: yellow hood, green face, gold bell, "DD"; rooftop DINK DONK; cafe; shops) - never reuse an old basis.

## Fidelity tests (from a research pass; show them side by side, owner judges)
A. **Real rain ripples, ray-traced every frame** instead of the 2D-warped reflection layer: a procedural,
   exactly periodic ripple normal node group (per grid cell: random drop centre + phase, ring phase =
   fract(t/T + rand(cell)) with T dividing 6 s; drizzle/wind from 4D noise on a circle, W = R sin(2pi f/144))
   driving the normals of puddles and wet ground (street, sidewalk, roofs). Algorithmic reference: OpenMW's
   rain ripples (GPL - re-implement the method, do not copy code). Deliver: `qa10/test_ripples_still.png`
   (720p frame with the ray-traced ripples) and `qa10/test_ripples_clip.webm` - a short seamless 720p clip
   (e.g. 24-48 frames, cropped to the street/sidewalk in front of the cinema is fine) rendered in Cycles per
   frame, showing ripples genuinely breaking the neon reflections. Use Blender's OptiX temporal denoising
   (`bpy.ops.cycles.denoise_animation`, multilayer EXR with Denoising Data + Vector, extra frames each side
   trimmed for the seam) and a fixed seed; also make the same clip with per-frame denoising for comparison
   (`test_ripples_clip_noTD.webm`) and report a flicker metric for both.
B. **Physical neon glow**: the compositor Glare node (Bloom and/or Kernel with a small streak/aperture kernel,
   slight red-weighted halation) on the neons vs the current 2D glow: `qa10/test_glare_before.png` /
   `test_glare_after.png` (720p, same frame).
Write `qa10/DRAFT-4.md`: what changed, times, the test results and your recommendation, then STOP.
