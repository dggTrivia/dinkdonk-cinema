# Brief 57: frozen Brief 56 production

Run `bash run.sh full` on an authorized Linux NVIDIA OptiX host. The existing
Blender 5.2.3 pin, run lock, DONE/FAILED handling and detached watchdog are retained.
`preflight`, `smoke` and `validate-only` use the same launcher. No credentials are bundled.

The original production56.py, runtime.py and frozen scene.blend are byte-identical
to the stopped local run. Their relative folder structure is retained inside this
isolated bundle. `out10/` is the read-only live baseline; generated production is
under `out10i/`. No local EXRs or partial-run markers are uploaded. A small wrapper
restores the mist inventory dependency, runs the original seven stages in separate
Blender processes, validates contracts, and seals `out10.tar.gz`.
The copied preflight recognizes the frozen scene's rebased packed-asset paths and
78 marquee bulbs. Fallback files accompany those relative paths. No blend rewrite
or geometry/material/lighting edit is performed by this bundle preparation.

Production: native 3840x2160, adaptive 256/64/.01, seed 1701, OptiX denoising,
Blackman-Harris 2.5, original display/glare. Background and rain have 48 unique
phases; wet foreground has 24 even phases in 48 paired slots. Bell A12/B12,
144 frames / 24 fps / 6 s. ROXY_WET_FRAMES=48 is rejected because this job follows
production56.py exactly. Independent rigs and Brief 53 rain stay byte-identical.
Catch/height/rim/light maps at both scales are included, with the existing
16-sample data / 32-sample light recipe. No baked physical mist beauty is needed.

Smoke is bounded: tiny sign crops, actual A/B materials across all 144 phases,
native camera/scene/visibility checks, tiny mist data/light captures, the existing
VP9 encoder/decoder, sheet packing, result checksums and tar member hash read-back.
It creates internal diagnostics only. It does not run the old 720p/4K/draft14
smoke suite, production stages, or owner images, and cannot mark production done.

Output archive has the existing `out10/` top-level directory. The helper extracts
it under OUTDIR, so the candidate payload is OUTDIR/out10. Eight mist PNGs are at
the payload root; later live destinations are out10mist, with all other art going
to out10. `_work/cloud57/` contains verification, timings, receipt JSON and source
video frames for home QA, not web assets. EXRs remain on the pod during the run;
their hashes are verified there and included in the evidence. Home QA must use
that evidence instead of silently mixing in the stopped laptop's EXRs.

Full completion here means render and structural packaging success, with local
144-frame decoded-video/visual/page acceptance still pending. Merge only after
checking baseline hashes. Keep the original laptop out10i/_work unchanged; use a
separate QA workspace for the returned cloud evidence. Never promote live assets
or edit the page as part of this bundle job.
