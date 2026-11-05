# Brief 54: rooftop DINK DONK sign - "CINEMAS" line + slower bell (DRAFT ONLY, live pack untouched)

Owner (05 Nov): "the dink donk sign emote should swing the bell like 100% slower, and that [sign] should have a
' CINEMAS ' below it".

Live facts: the rooftop sign is the DinkDonk emote neon (2-state tube sets: A arm + bell DOWN, B arm raised + bell
UP, BRIEF-17 item 36) + the "DINK DONK" letters with the bulb-chase frame, on the theatre roof. The A/B ring rhythm is
baked into the 6 s / 144-frame / 24 fps light_loop.webm (out10, BRIEF-26). Current production scene:
cloud/bundle/scene.blend (as used for BRIEF-50/53; open read-only, never save over it).

## Do (draft quality, local GPU, no cloud)
1. "CINEMAS" below "DINK DONK": a second, smaller line of neon tube lettering centred under DINK DONK, inside the
   sign's existing bulb frame if it fits (extend the frame/backing downward if it doesn't), same neon family as
   DINK DONK (tube colour may be the same cyan or a complementary warm white/pink - pick what reads as one sign and
   say why), wide letter spacing, about 40-50% of the DINK DONK cap height. Lit like the rest of the sign (its glow,
   reflections on the roof/wet surfaces). Physically mounted (raceway/standoffs like the existing letters).
2. Bell 100% slower = the A/B ring rhythm at half speed: every state (and any gap) held twice as long as now. Read
   the current timing from the light-loop source and report it (frames per state, pattern). The loop must stay
   seamless at 6 s / 144 frames (if the halved pattern doesn't divide 6 s, say what you'd do: e.g. a 6 s pattern with
   fewer rings - do not change the loop length on your own).

## Deliver
- ONE owner image qa10/draft22-dinkdonk-cinemas.png, 1280x720: left = current sign (out10 lit frame crop), right =
  draft with CINEMAS (same crop, same lighting, state A), plus a small timing strip under it: current vs new A/B
  pattern over the 6 s loop (two rows of coloured blocks, labelled). Small labels only.
- NOTES-54.md (what/how, timing before/after, which outputs a production pass would re-render: base/bg/lit_bg/
  light_loop/occluders/others, and estimated local render time), STATUS line, stop.
Do NOT modify roxy3d/out10/, any other pack, or standby/roxy.html. Write only in roxy3d/ (new folder out10h/ for any
staging). Local GPU only.
