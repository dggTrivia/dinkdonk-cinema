# Brief 21: cloud render bundle for the final render (build + 1-frame local test, NO full render)

The owner will run the FINAL render (out10) on a rented cloud GPU (RunPod, RTX 4090, Linux, NVIDIA drivers, OptiX).
Your job now: turn the final-render pipeline into a portable bundle and prove it works with a tiny local test.
Do NOT run the full render anywhere. Only write inside roxy3d/.

## Content of the final render
The approved scene is the draft 9 state of roxy_pass10_draft.blend (all owner feedback through draft 9; see
QUEUE-owner.md and BRIEF-13 to BRIEF-20). The final pack is out10 with the layout-3 manifest from BRIEF-13 (three
screens, restroom, rope-lane queue, doors, led_signs, poster_frames, wc_indicator, ad_surfaces incl. the new
rooftop billboards, vehicles with the 05 d.gg transit branding, bus-shelter bench seat spots, etc.) plus:
- the approved ray-traced periodic ripples on all wet surfaces (2-second cycle, repeated 3x in the 6 s loop),
  per-frame OptiX denoise, HDR glare; the two-state DINK DONK neon (A/B alternating) in the loop;
- light_loop (1080p) and light_loop_2x (4K) + rain_fg as before, every contract of out9 that still applies.
Old out10 contents are a stale parked attempt - build fresh into a new folder (out10).

## Speed plan (from research/RENDER-SPEED.md - read it); quality must stay identical
1. Static plate + per-frame wet layer: render the dry/static parts once; per frame only the wet surfaces/rain
   (holdout the rest, Film > Transparent, recombine, glare applied after compositing).
2. One Blender process for all frames, Persistent Data on.
3. Adaptive sampling with max 256 (noise threshold tuned so the result matches fixed 256 within the noise
   baseline), the 48-frame ripple cycle.
4. Reuse unchanged renders (e.g. vehicles if only labels changed? - re-render where branding changed).
Verify each change with the baseline test: render frame 1 at 720p twice with different seeds (= noise baseline);
an optimisation passes if its difference from the reference stays within that baseline. Report the numbers.

## Bundle (roxy3d/cloud/)
- `bundle/`: the .blend with everything packed (textures, fonts, images), all scripts, nothing with Windows paths
  (use paths relative to the bundle root), a `run.sh` that: downloads Blender 5.2.3 Linux x64 from
  download.blender.org (verify its SHA-256), enables OptiX, runs the whole pipeline headless, writes progress lines
  to `progress.log`, and packs the result into `out10.tar.zst` (or .tar.gz) with the manifest and a validation json.
  It must be restartable (skip finished frames) and fail loudly.
- `README-CLOUD.md`: how it runs, expected time on an RTX 4090 and on the laptop, disk/VRAM needs, what to copy back.
- Local test: run the same pipeline on this laptop in a "smoke" mode (one 720p frame of the loop + one sprite + the
  manifest skeleton) from the bundle folder, to prove portability; report time and the quality-check numbers.
Then STOP and report (codex-final-cloud.md + STATUS line in qa10/STATUS.md).
