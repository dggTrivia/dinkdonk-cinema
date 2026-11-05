# Approved Draft 13 - faster cloud pipeline (Brief 27)

The output remains layout-3 out10: 1920x1080 / 3840x2160 images, existing filenames and manifest keys, 48-slot 8x6 wet sheets, 16-slot 4x4 doors, and six-second 24 fps VP9 loops. The approved source scene is unchanged. No page edit is required.

## Execution and resume

On an explicitly authorized Linux NVIDIA pod, extract the archive on persistent storage and run `bash run.sh full`. The result is `bundle/out10.tar.gz`; success prints `SUCCESS mode=full archive=out10.tar.gz`. `preflight`, `smoke`, and `validate-only` remain available. Blender 5.2.3 and its official download checksum remain pinned in run.sh. No pod was started for Brief 27.

The same-process renderer retains SHA-256 receipts for EXRs, position arrays and Cryptomatte masks. Interrupted captures cannot count as finished. A repaired relaunch can reuse valid buffers; the output fingerprint includes the selected wet-frame count and prevents mixing different builds. Keep the bundle's work directory when repairing a run.

The launcher retains DONE/FAILED markers, progress.log, locking and the detached watchdog: stop after three hours from completion/failure or eight hours from launch, whichever comes first. The cloud helper retains launch.sh, the credit guard, and cache-preserving failure handling. Shell fixtures use fake pod commands; no real pod stop was tested here.

## Production changes

* One combined foreground capture supplies antialiased Cryptomatte group masks and a world-position AOV. Every one of the 39 groups was compared with its isolated holdout render and a second seed. Only groups within both colour and alpha noise limits use cuts. The exact measured exception list is in `smoke/fast-validation.json`; exceptions retain their isolated passes. Backgrounds retain their separate unobstructed camera pass, which is necessary for walkers and transparent overlays.
* All newly traced production images use the 3840x2160 camera grid, including cropped sprites, doors, rain and rebuilt bus bodies. The 1920x1080 assets derive from a 2x2 area reduction of linear RGBA before the approved display transform. A measured 2.5-pixel Blackman-Harris filter at 4K matches the approved 1.5-pixel native-1080 footprint within the tested noise baseline; the filter is included in every native-render receipt. Position reduction uses alpha-weighted surface coordinates. The published rain video remains 1080p.
* Unchanged visibility states and material slots are not rewritten. Phase updates skip unchanged times and use pre-indexed neon circuits/materials. Exceptions render all phases consecutively, retaining Persistent Data. Receipts separately record phase, visibility, configuration, render/sync/compositor, EXR write/read and hashing. The C++ render bucket includes tracing, scene synchronization, denoising and compositor work; it is not claimed as pure tracing.
* With `ROXY_WET_FRAMES` unset, the default is 24 unique foreground/wet phases, as approved by the owner on 03 Nov 2026. Each even phase occupies two of the existing 48 output slots. `ROXY_WET_FRAMES=48 bash run.sh full` restores 48 unique foreground/wet phases. Sheet dimensions, fps, filenames and keys stay unchanged. The A/B bell transitions remain at six-slot boundaries; the chase/ripples retain two-second periods repeated three times in the page's six seconds. Background light and airborne rain stay at 48 unique frames. No new draft or test clip was rendered for this default change.

Quality remains adaptive max 256 / min 64 / threshold 0.01, OptiX denoising, Persistent Data and approved HDR glare. Geometry-node drips/crowns/pours remain sharp with motion blur disabled. No dry/wet split was introduced.

## Evidence and boundaries

See `NOTES-FAST-PIPELINE.md`, `smoke/validation.json`, and immutable copies in `proof/fast27/`. The laptop smoke covers all group comparisons at one 720p time, a genuine native 4K/1080p camera-grid crop comparison, matched old/new captures, the preflight and geometry contracts, and four bus states through the production reduction and depth-slicing path.

The packaging fixture uses real smoke pixels and repeated-frame sheets/video. It runs the production VP9 encoder and actual decoder, all 144-frame seam/repetition branches, the validator, cleanup, checksums, tar and member hash read-back. It does not prove temporal appearance or a full animation. Video black acceptance remains the video's own per-decoded-frame pass flag.

ONE owner draft is saved outside the upload bundle at `roxy3d/qa10/draft14-fast.png`: fixed camera, 1280x720, final quality, depth-sorted cut/fallback foreground and additive weather. Work buffers and codec fixtures are internal diagnostics, not additional owner drafts.

Native full-frame 4K memory, all animation phases, Linux runtime behavior, browser/OBS playback and actual cloud time remain untested in this bounded local run. Cloud time/cost estimates in the notes use the owner's measured run-2/run-3 baseline plus local ratios; they are projections.
