# Brief 27: faster final-render pipeline (same approved draft-13 look)

The owner stopped the final render (run 3, 03 Nov 2026 08:22) to get a faster pipeline first. The LOOK stays the
approved draft 13 (BRIEF-26 lists everything it includes). The OUTPUT CONTRACT stays the layout-3 out10 manifest the
page already reads: same files, keys, sizes and sprite layout, so standby/roxy.html needs no change. What changes is
how the frames are produced.

## Measured baseline (cloud run 2, RTX 5090; see PROGRESS.md "02-03 Nov 2026")
- ~5.5 h total. Foreground: 14 outdoor/glass groups x 48 frames x 2 scales = 1,344 separate renders at ~9 s each
  = ~3.4 h (~60%). Of the 9 s only ~4 s is Cycles; ~5 s is per-render overhead, the same at 1080p and 4K.
  Backgrounds: 48 frames at 1080p ~19 s + 48 at 4K ~41 s. Doors 8 x 6 poses x 2 scales ~20 min.
- RTX 4090 (run 3): 1080p background ~31 s/frame wall vs ~20 s on the 5090.

## Changes the owner approved (implement all four)
1. **One render per frame, cut into layers.** Replace the per-group holdout renders with a single render per
   frame (per scale) plus per-object masks (cryptomatte / object-index / your choice) and the position AOV the depth
   slices already use, then cut every foreground group, wet highlight sheet and depth slice from it. Glass and soft
   edges are the risk: compare each group cut from the combined render against the current per-group render on the
   same frame. Keep a per-group render ONLY for a group whose difference exceeds the existing noise baseline, and
   list those groups with numbers.
2. **4K only.** Render each image once at 3840x2160 and derive 1080p by a 2x2 area downscale (in linear light if the
   pipeline is linear at that point). Compare the result with a native 1080p render against the noise baseline.
3. **Less per-render overhead.** First profile where the ~5 s goes (visibility/holdout toggles on ~6,800 objects,
   frame change and geometry-nodes drip evaluation, Persistent Data rebuilds, 32-bit EXR writing, hashing, display
   conversion). Then fix the biggest ones (e.g. order renders so visibility changes once per pass, not per frame).
   Report before/after numbers per item.
4. **24-frame option for the subtle wet loops.** Add a switch for 24 unique frames instead of 48 on wet/foreground
   loops (the light loop and the 2 s marquee chase/ring rhythm must stay in sync with the page's 6 s loop; say how
   you keep that). Default stays 48 (the approved look). Do not render a test clip: the owner decides later.

## Keep
- Everything fixed on 03 Nov: video.py black tolerance (per decoded frame), validation.py using the video's own
  pass flag, cloud/cloud-render.sh (keep pod on failure, launch.sh, credit guard). Same run.sh modes (preflight /
  smoke / full / validate-only), progress.log, "SUCCESS mode=" line, watchdog, out10.tar.gz, seal_bundle.py checks.
- Render cache with receipts, so a repaired relaunch on the same pod reuses finished renders.
- The drip/crown motion-blur rule (sharp, consistently), HDR glare, adaptive 256/64/0.01, OptiX denoise.

## Deliver
- **ONE draft image** made with the new pipeline: the fixed iso camera, 1280x720, final quality + weather frame,
  composed from the cut layers exactly as the page would stack them, so the owner can compare it with draft 13.
  No other images or clips for the owner (drafts rule).
- Local smoke test on this laptop (RTX 3050 6 GB) proving the new bundle, with old-vs-new timings for the same
  renders, and a projected cloud time and cost for a full run (RTX 4090 $0.89/h and RTX 5090 $1.19/h).
- Exercise the packaging tail (video encode/decode checks, validate, cleanup, checksums, tar) end to end at least at
  smoke scale, so no step meets real data for the first time on the cloud.
- Rebuilt cloud/roxy-cloud-bundle.tar.gz (sealed), notes in NOTES-PASS10.md or a new NOTES file, STATUS line, stop.

Do NOT run the full render locally and do NOT start any cloud pod. Do not touch standby/roxy.html. Only write
inside roxy3d/.

## Owner decision (03 Nov 2026, after this brief was sent)
The owner approved the 24-frame option: make 24 unique frames the DEFAULT for the subtle wet/foreground loops
(change 4). The light loop and the 2 s marquee chase / ring rhythm keep their timing in sync with the page's 6 s loop.
