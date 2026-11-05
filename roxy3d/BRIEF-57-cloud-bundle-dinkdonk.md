# Brief 57: move the Brief 56 production to RunPod (bundle only - no pod)

Owner (05 Nov, 14:30): "You should use the GPU remote for this". The local Brief 56 run was stopped by Claude after
34/48 background_2 frames (7 min/frame on the 3050; the run-5 5090 did the same frame in 48 s). Its workspace
out10i/_work/ stays exactly as it is - it is the fallback (produce.ps1 resume). Do not delete or rewrite its buffers.

## Build
A new cloud bundle that renders the Brief 56 production on a Linux RunPod GPU with the existing helper
cloud/cloud-render.sh (same flow as run 5, 03 Nov: network volume, launch.sh, watchdog, DONE/FAILED, results to /vol):
- scene = the frozen production copy out10i/_work/pipeline/scene.blend (draft 23 sign + the floodlight re-aim you
  already verified in scene-verification.json); bell A12/B12 = the runtime.py change in out10i/_work/pipeline;
  production settings exactly as production56.py (4K grid, 256/64/.01, seed, OptiX denoise, glare, 24 wet phases
  unless production56 used 48 - say which). No new look decisions.
- everything Brief 56 needs from the GPU: backgrounds, weather, foreground, doors/WC, and the mist passes if they can
  run on the pod (catch/height/light/rim for out10mist). If mist cannot go in the bundle, say so and how long it
  takes on the laptop afterwards.
- `bash run.sh full` on the pod should produce the result archive in the out10 contract (same names/keys), plus the
  mist files if included, so it can be compared and merged into out10i.
- archive: cloud/roxy-cloud-bundle-56.tar.gz (keep the old roxy-cloud-bundle.tar.gz untouched).
- cloud-render.sh: back it up first (cloud-render.sh.pre57), then make only these changes: ARCHIVE overridable by env
  (default unchanged), and the full-mode unpack dir overridable by env (default out10.new unchanged), so Claude can run
  `ARCHIVE=... OUTDIR=roxy3d/out10i.cloud bash cloud-render.sh full`. Keep the credit guard, watchdog and
  never-delete-an-unreachable-pod logic as they are.

## Verify locally (cheap)
Preflight + the bundle's existing smoke mode on the laptop (minutes, tiny resolution) to prove the archive extracts,
the scene loads with the new sign, the bell cadence is A12/B12 and the packaging path runs. No full-res frames, no
owner images. Do NOT start any pod and do NOT run cloud-render.sh - Claude runs it.

## Deliver
NOTES-57.md: archive path, size, sha256; what differs from the run-5 bundle; mist handling; expected pod time and cost
from the run-5 timings (5090 ~$1.19/h); the exact command line for Claude; what you will do once the result is home
(merge into out10i, QA, copy list, NOTES-56, qa10/draft24 check image - Brief 56's remaining steps). STATUS line, stop.
Write only inside roxy3d/. Never modify out10/, out10mist/ or standby/roxy.html.
