# Brief 57 - cloud bundle for the frozen Brief 56 production

Bundle preparation and bounded local verification are complete. No pod was started,
no cloud-render.sh execution occurred, and no full-resolution frame or owner image
was rendered. The stopped out10i/_work fallback is unchanged.

## Archive and provenance

- Archive: `cloud/roxy-cloud-bundle-56.tar.gz`
- Size: **167,296,502 bytes (159.55 MiB)**
- SHA-256: `cb6d338753a3a0da2c402d976d4c3db45ee910e27024f5651c6932d364145883`
- 888 regular archive members, all under `bundle/`; all member hashes read back.
- Source/build: `cloud/brief57/build57.py`, `pipeline57.py`, and `upload/bundle/`.
- Final verification: `cloud/brief57/verification.json`, `bundle-delivery.json`,
  `preservation.json`, and `verify/bundle/smoke/validation.json`.

The production scene is the exact frozen `out10i/_work/pipeline/scene.blend`,
SHA-256 `33090d845e0c10348627b42b24f55a774691eb44b1b47326158099e657987942`. `production56.py` is byte-identical
(`5d601fa31a3d0f256cf41a89e28a85613c8db8b66460a4f25672fd425fe58c41`), as is the local A12/B12 `runtime.py`
(`3775276384197ce22a08a9671f2f5491898773e047b52cc6e8538ea006c59586`). The verified draft-23 sign, central flood re-aim/
physical hood, and covered-annex-face fix are inherited without a blend rewrite.
The original cloud scene is also bundled only because the unchanged driver hashes
it before restoring the original production visibility; it is not the render scene.

## What differs from run 5

The previous archive `cloud/roxy-cloud-bundle.tar.gz` and `cloud/bundle/` are untouched.
This new bundle retains the local Brief 56 folder layout and uses its seven original
stages: backgrounds, weather, foreground, doors/WC, mist, composition/ads and videos.
It includes the current 802-file live baseline, including Brief 53 rain, so all
independent rigs and unaffected payloads can be preserved exactly. It does not
upload or reuse the stopped laptop's partial buffers.

Production remains **3840x2160, 256 max / 64 min / .01 adaptive threshold, seed 1701,
OptiX denoising, Blackman-Harris 2.5, retained AgX/glare, linear 2x2 reduction for 1x**.
The driver uses **24 unique wet phases**, repeated into the existing 48 atlas slots;
48 background/rain phases repeat three times in 144-frame / 24 fps / 6 s VP9 loops.
Bell holds are **A12/B12, 0.50 s per state**. ROXY_WET_FRAMES=48 is rejected for this
bundle because production56.py fixes 24. No sampling or appearance setting changed.

The wrapper runs stages in separate Blender processes and keeps stage records,
logs and content-checked EXR receipts for resumption. It preserves the original
isolated foreground/alpha/depth method instead of importing the old combined-cut
policy. Full packaging checks the expected 500 native captures, original alpha,
slice reconstruction, wet-sheet wraps/pairs, video receipts, mist support, baseline
inheritance, checksums and every result-archive member hash. These production checks
will run on the pod; they have not been executed at production resolution locally.

The copied preflight now expects 78 bulbs and accepts the frozen scene's rebased
relative packed-asset paths; all fallback files are included and resolved inside
the extracted bundle. The actual scene, rendering runtime and driver are unchanged.
The existing `smoke` entry point is bounded for Brief 57: the old smoke27 suite
includes 720p/4K captures and an owner draft, so it is not dispatched here.

## Mist and returned archive

**All eight mist files are included**: `catch.png`, `catch@2x.png`, `height.png`,
`height@2x.png`, `rim.png`, `rim@2x.png`, `light.png`, `light@2x.png`. Catch/height/rim
derive from the original 16-sample native data/AOV pass; light uses the original
32-sample denoised matte night-light pass. The production driver restores source
visibility and applies its existing hood shadow handling. The wrapper supplies the
scene-inventory file required by mist processing. No physical mist beauty bake is
required. There is **no laptop mist-render tail**; only home QA and packaging remain.

`bash run.sh full` produces `bundle/out10.tar.gz` with the same `out10/` archive
prefix and media/manifest contracts as the existing helper. The eight mist maps
sit at the result payload root, ready to stage in out10i and later copy separately
to out10mist. `_work/cloud57/` in the result contains pod audit/timing/receipt data
and background/light/rain source PNGs for local QA; it is not web payload.
Full EXRs stay on the pod, where their hashes are verified before sealing; do not
mix the returned evidence with the stopped laptop's EXRs or blindly run its old
audit/finish scripts, which assert local RTX 3050 provenance.

The result metadata explicitly leaves home 144-frame decoding, visual review and
page acceptance pending. The helper's existing launch.sh copies the archive,
checksum and logs to `/vol/results` before its normal successful-pod stop path.

## Local proof and limits

Preflight and smoke passed using the archive extracted into
`cloud/brief57/verify/bundle/`, on Blender 5.2.3 / local RTX 3050 OptiX. Checks cover
all seven CINEMAS glyphs, the exact frozen source hashes, flood aim, 39 foreground
groups, eight doors, routes/holdouts/packed paths, and actual A/B material selection
at every frame 0 through 144, including 143 -> 0.

The uncached smoke took **130.30 s**; the final-archive verification took
**104.42 s**, retaining valid tiny sign/codec receipts. Internal sign
captures are **280x216 pixels** on a 640x360 camera grid (phases 0 and 12); both were
reopened and visually checked for the CINEMAS sign and bell states. Mist smoke maps
are 320x180 / 160x90. The existing production VP9 encoder/decoder exercised a real
144-frame, six-second A/B delta fixture, 48-slot wet and 16-slot door packing, then
the shared checksum/tar/member read-back path. Fixture pixels do not prove native
production quality or full animation appearance.

The initial preflight caught the rebased packed-texture paths; the final bundle
includes and validates those paths. Prior diagnostic logs are retained. Bash syntax
checks passed; original run.sh/watchdog.sh are byte-identical. Linux execution,
remote GPU behavior, full production loops, browser/OBS and page acceptance remain
untested here. No pod, network render or helper launch was used as verification.

Hash preservation passed for **2,690 files** across out10, out10mist,
the whole stopped out10i/_work tree, the old cloud/bundle, old upload archive and
standby/roxy.html. No protected file was changed or added. All task writes are in
roxy3d/cloud/brief57, the new archive, the backed-up/edited helper and this note.

## Time and cost estimate

Run-5 evidence is in `cloud/progress-full.log` and
`cloud/brief57/timing-baseline.json`: total production **9,828.50 s = 2 h 43 min 49 s**
on the RTX 5090; mean background capture including bookkeeping **48.46 s**
(46.73 s render/write), foreground **10.49 s**, weather **14.75 s**, door **8.44 s**.
This job plans 50 background/dry/endpoint captures, 49 weather captures, 351
foreground captures, 48 door poses, two WC states, plus the two mist passes.
It retains the already-produced independent vehicle/umbrella assets.

Expected render/package time is **about 2.75-3.5 hours**; allow **3-4 billed hours**
including provisioning, upload, warm-up, validation and transfer. At the brief's
historical **~$1.19/hour**, this is **~$3.27-$4.17** render/package, or
**~$3.57-$4.76** with that allowance, plus any volume/storage/network charges.
These are projections from run 5, not a new benchmark or current provider quote.
The existing $5.50 full-mode credit guard, six-hour helper limit and detached
watchdog (three hours after completion/failure or eight hours after launch) remain.

## Exact command for Claude - not executed here

In Git Bash, from the standby directory:

```bash
cd /c/Users/maxsp/Desktop/Angelthump_H264_4K/standby
ARCHIVE="$PWD/roxy3d/cloud/roxy-cloud-bundle-56.tar.gz" \
OUTDIR=roxy3d/out10i.cloud \
bash roxy3d/cloud/cloud-render.sh full
```

The helper backup is `cloud/cloud-render.sh.pre57`. Only ARCHIVE and the full-mode
unpack destination are overridable; defaults remain the old archive and out10.new.
Credit guard, watchdog, network-volume flow and unreachable-pod handling are unchanged.
OUTDIR is the unpack container, so the returned candidate is
**`roxy3d/out10i.cloud/out10/`**. The existing helper clears OUTDIR before unpacking;
keep it pointed at that dedicated candidate directory. For a later fetch from the
same standby working directory, retain the destination override:

```bash
OUTDIR=roxy3d/out10i.cloud bash roxy3d/cloud/cloud-render.sh fetch
```

## Once the result is home - Brief 56 still to finish

1. Verify downloaded archive/member checksums, exact frozen hashes and baseline
   compatibility against live out10. Review the pod audit, endpoint proofs, timings
   and complete capture set. Keep returned cloud evidence in a separate QA workspace;
   keep the stopped out10i/_work fallback unchanged.
2. Merge candidate **payload only** into out10i, retaining the full inherited live
   pack. Keep the eight mist maps at the staging root. Adapt the existing qa56/
   finish56/write_notes56 workflow in the separate QA workspace to the cloud proof
   and correct device/timing provenance; do not overwrite the local fallback scripts
   or mislabel the cloud run as local.
3. Decode all 144 frames of light_loop, light_loop_2x and rain_fg. Verify A12/B12,
   143 -> 0 and every wet-loop wrap, alley receiver stability, alpha/depth ownership,
   inherited Brief 53 byte identity, all manifests/files and decoded 1x/@2x memory.
   Inspect internal contact sheets and the production sign/flood result.
4. Create and inspect the single **1280x720 qa10/draft24-dinkdonk-production.png**:
   live/out10i sign crops in A and B, per Brief 56. Then refresh manifest/checksums/
   validation and the exact **out10i-copy-list.txt** NEW/CHG delta. Mist destinations
   must be explicitly out10mist; the other payload deltas target out10.
5. Write **NOTES-56.md** from verified file sizes, memory, actual cloud/local timings,
   full decoded-loop evidence and byte-identical checks. Claude tests
   `?artdir=out10i&mistdir=out10i` and owns the later promotion. No live pack or page
   edit is part of this bundle-only delivery.

STATUS: COMPLETE - Brief 57 bundle and local preflight/smoke verified; no pod started; protected files unchanged; stopped for Claude's cloud run.
