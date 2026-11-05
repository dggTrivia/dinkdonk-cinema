# Art and render pipeline

How the pre-rendered art for DinkDonk Cinema is made, packed and loaded: the lobby (`lobby.html`, formerly
`roxy.html`) and the auditorium (`auditorium.html`). State as of 5 Nov 2026.

All art lives in `roxy3d/`. The folder kept its old "roxy" name on purpose: briefs, scripts, manifests and page paths
depend on it. The page side of each scene is in [lobby.md](lobby.md) and [auditorium.md](auditorium.md).

## 1. Overview

```
Blender scene (.blend + builder .py)          roxy3d/*.blend, build_*.py, cloud bundle scene.blend
   -> render passes (Cycles, OptiX, 4K)       backgrounds, weather, foreground groups, doors, mist, sprites
   -> packaging                               2x2 downscale, depth slices, sprite sheets, VP9 loops,
                                              manifest.json, checksums.json, validation.json
   -> staging pack (out10<letter>/)           tested in the page with ?artdir=...&mistdir=...
   -> promote into the live pack              roxy3d/out10/ + roxy3d/out10mist/ (lobby), roxy3d/qa11/ (auditorium)
   -> page                                    lobby.html / auditorium.html draw the layers over live DOM walkers
```

Blender 5.2.3 is used everywhere. Locally it lives in `tools/blender-5.2.3-windows-x64/` (not in git). The cloud
bundle downloads the same release and checks its official SHA-256.

### Who does what

| Who | Role |
|---|---|
| Owner (the streamer) | Asks for changes, reviews drafts, approves full renders and cloud spend. Nothing is final without the owner's OK. |
| Claude (Claude Code) | Writes the numbered briefs, checks every render, runs read-only critiques, tests staging packs in the page, promotes packs, writes page code, logs in `roxy3d/PROGRESS.md`, runs the RunPod helper. |
| Codex (Codex CLI) | Renders from the briefs: builds and edits the Blender scenes, renders drafts and production passes, packs the art, writes `NOTES-*.md`. Writes only inside `roxy3d/`. |
| Codex, read-only | Second opinion on each draft before the next brief (`codex-NN-critique.txt`, `reviews/review-*.md`). |
| RunPod | Rented GPU for the big lobby production passes, only when the owner asks. |

### Where things are

| Path | What | In git |
|---|---|---|
| `roxy3d/BRIEF*.md` | Numbered briefs (`BRIEF.md` = brief 1, then 2 to 58) | yes |
| `roxy3d/NOTES-*.md` | What each pass delivered (`NOTES-PASS2..9`, `NOTES-FAST-PIPELINE.md`, `NOTES-46..57`) | yes |
| `roxy3d/GOAL.md`, `GOAL-cinema.md` | Overnight goals and the Claude/Codex split | yes |
| `roxy3d/PROGRESS.md` | Running log, newest at the bottom | yes |
| `roxy3d/QUEUE-owner.md` | Owner requests, numbered, collected per review round | yes |
| `roxy3d/QA-REPORT.md`, `QA-SESSION-BRIEF.md` | QA/performance night of 4-5 Nov 2026 (page side) | yes |
| `roxy3d/*.py`, `*.ps1`, `*.blend` | Builder, render, package, verify scripts and source scenes (top level) | yes (`*.blend1` no) |
| `roxy3d/codex-*.txt`, `codex-final-*.md` | Codex final messages and critiques | yes (`*.log` no) |
| `roxy3d/out10/` | Live lobby art pack | yes |
| `roxy3d/out10mist/` | Live surface/mist maps for the lobby rain layer | yes |
| `roxy3d/qa11/` | Auditorium drafts; only the files `auditorium.html` loads are tracked | partly |
| `roxy3d/cloud/` | `cloud-render.sh` (RunPod helper), `README-CLOUD.md`, Brief 27 build scripts | yes |
| `roxy3d/cloud/brief57/` | Brief 57 production bundle sources (`upload/bundle/`) and build scripts | yes, except `upload/bundle/out10/` and `local-cache/` |
| `roxy3d/tools/band-slices.mjs` | Cuts auditorium depth slices into bands | yes |
| `roxy3d/memes/`, `ref/`, `research/` | Meme shortlist, reference images (emotes, childhood cinema photos), research notes | yes |
| `intro-dinkdonk/` | DINK DONK intro video scripts and outputs | yes |
| `package/art.js` | Lists exactly which art files the pages load (used by `package/build.js` and `web/build.js`) | yes |
| `roxy3d/qa*/`, `out/`..`out9/`, `out10b`..`out10i/`, `out10.pre-*/`, `out10.stale-*`, `out10-loopfix/`, `out10.orig-loop/`, `cache/`, `progress/`, `reviews/`, `qa-night/`, `cloud/bundle/`, `cloud/*.tar.gz` | Drafts, QA shots, old and staging packs, rollback backups, render caches, review notes, cloud archives (about 30 GB) | **no, local only** |

## 2. The lobby art pack (`out10/`) contract

The page reads everything through `out10/manifest.json` (layout 3, `asset_pack_revision`
`brief56-draft23-dinkdonk-cinemas`). The pack has 802 files (126 MB); 397 distinct PNGs, each at 1x and @2x.

### Coordinates

- Logical stage is 1920x1080. Every `x`, `y`, `w`, `h`, anchor and `z_index` in the manifest is in 1x pixels, also
  when the @2x file is drawn.
- Isometric projection (from `NOTES-PASS9.md`): `x = 900 + 60(u - v)`, `y = 350 + 30(u + v) - z_px`; 73.48 z-pixels
  per tile (`projection` in the manifest).
- Depth: walkers, vehicles, cat and janitor sort at `1000 + round((u + v) * 100)`; occluders and slices carry their
  own `z_index`.
- PNG alpha is straight (unassociated), drawn source-over; additive layers are RGB on black, drawn `plus-lighter`.

### Files

| Files | Manifest key | What it is |
|---|---|---|
| `base.png`, `base@2x.png` | `base` | Background at the per-channel temporal minimum of the light cycle: the plate the light loop adds onto. |
| `bg.png`, `bg@2x.png` | `bg` | Byte-identical alias of `base` (older integrations). |
| `lit_bg.png`, `lit_bg@2x.png` | `lit_bg`, `lit_bg_2x` | Fully lit phase-0 background; foreground layers go on top. |
| `lit_bg_dry.png`, `@2x` | `lit_bg_dry`, `lit_bg_dry_2x` | Lit wet scene without animated rain/impacts baked in. Used as the still when the loop is off. |
| `full.png`, `full@2x.png` | `full` | Flattened fallback: background phase 0 + foreground + wet highlights + vacant WC + rain. Do not draw sprites over it. |
| `light_loop.webm` | `light_loop` | 1920x1080 VP9, 144 frames, 24 fps, 6 s. Positive difference above `base` (lights, reflections, rain). `plus-lighter` over base, under walkers. |
| `light_loop_2x.webm` | `light_loop_2x` | 3840x2160 version of the same loop, the exact complement of `base@2x`. |
| `rain_fg.webm` | `rain_fg` | 1920x1080 VP9 foreground rain, 144 frames / 24 fps / 6 s, `plus-lighter`, z 70001. 1080p only. |
| `occ_<group>.png` (39 groups) | `occluders[]` | Foreground parents (partitions, box office, snack bar, glass fronts, posts, restroom walls, street lamp, bus stop...). Each has `footprint`, `tile_clips`, `depth_slices`. |
| `slices/occ_<group>_NN.png` (107) | `render_layers[]` | Depth slices: disjoint world-position-AOV masks that rebuild their parent exactly. These are what the page actually stacks. |
| `prop_loops/wet_<group>_NN.png` (58) | `prop_loops[]` (`wet_*`) | Wet highlight sheets for outdoor/glass slices: 8x6 = 48 slots, 24 fps, 2 s, `plus-lighter`, same depth as their `parent_slices`. |
| `prop_loops/*` (16 others) | `prop_loops[]` | Popcorn, menu boards, arcade, soda logo, TICKETS letter E, poster bulbs (idle 1 frame / chase 72 frames at 12 fps). Rules in `prop_loop_contract`. |
| `doors/<door>.png` (8 doors) | `door_anims[]`, `restroom.door_anim` | 16 frames 4x4, 18 fps, open-hold-close, source-over at z 900. Screens 1-3, restroom entry, stalls 1-4. |
| `wc_vacant.png`, `wc_occupied.png` | `wc_indicator` | Restroom door light, pick one. |
| `ads/*.png` | `ad_surfaces[]` | In-world ad quads (`quad_px` TL, TR, BR, BL) and their overlays (wcat, EatFresh, shelter, paste wall). |
| `vehicles/<bus|taxi|sedan_a|sedan_b>_<plus|minus>[_open]*.png` | `vehicles` | Bodies (straight RGBA), `light`, `light_brake`, `light_indicator`, `light_indicator_only`; bus/taxi also `door_open`. Contracts: `vehicle_sprite_contract`, `vehicle_lamp_variant_contract`, `vehicle_indicator_only_contract`. |
| `vehicles/slices/*` | `vehicles.*.slices` | Longitudinal depth slices per body (`vehicle_slice_contract`). |
| `vehicles/rain/*` | `roof_rain`, `spray`, `wake` | Brief 53 rain on roofs, tyre spray and wake: 48 frames 8x6, 24 fps (`rain_production_contract`). |
| `umbrella/<colour>_<open|fold|wet>.png` | `umbrella` | 4 colours, 88x80 cells, anchor = handle grip; `wet` replaces `open` in rain. |
| `cat/*`, `janitor/*` | `cat`, `janitor` | Character sheets (walk in 4 directions, idle states). |
| `items/*` | `items` | Popcorn, soda, stub, ticket, staff caps, wet footprint. |
| `tyre_spray/*` | `tyre_spray` | Older one-shot spray (12 frames), used only without the Brief 53 loops. |
| `manifest.json` | - | The contract (placement, timing, blend, z, routes, staff and queue spots, LED signs, posters). |
| `checksums.json` | - | Array of `{file, bytes, sha256}` for every pack file (see the note on mist below). |
| `validation.json` | - | Packaging validation result (`passed`, loop counts, roof states...). |
| `.cloud-build.json` | - | Build fingerprint and provenance of the cloud run. |
| `NOTES-PASS10.md` | `notes` | Short notes for this pack (not loaded by the page). |

`package/art.js` takes `out10/` and `out10mist/` whole (minus `.md/.txt/.py/.ps1/.log`), because the page reads them
through the manifest.

### Resolution rules

- Production images are rendered once on the 3840x2160 camera grid. The 1x files are a 2x2 area reduction of
  linear RGBA before the display transform (Brief 27), with a Blackman-Harris 2.5 px pixel filter at 4K to match the
  approved 1.5 px footprint at native 1080p. Depth positions are reduced coverage-weighted.
- @2x files have exactly twice the pixels of the 1x file; placement stays in 1x units.
- `rain_fg.webm` stays 1080p and is scaled with the stage.
- Production settings (Brief 57 run): adaptive 256 max / 64 min samples, threshold 0.01, OptiX denoising,
  Persistent Data, AgX with the approved HDR glare, geometry-node drips sharp (no motion blur).
- Page side: the lobby loads @2x when output scale x devicePixelRatio x zoom > 1.3, and plays `light_loop_2x` with
  `base@2x` (`?loop2x=0` keeps the 1080p loop). The 58 `wet_*` sheets always stay 1x (they decode to ~590 MB at @2x
  and thrashed Chrome's image cache; `?wet2x=1` restores @2x).
- Decoded size of all pack PNGs: 324 MiB at 1x, 1,298 MiB at @2x (inventory ceilings from `NOTES-56.md`, not measured
  VRAM).

### Loop rules

| Loop | Frames | Timing | Notes |
|---|---|---|---|
| `light_loop`, `light_loop_2x`, `rain_fg` | 144 | 24 fps, 6 s | 48 unique background/rain phases (a 2 s cycle) repeated 3 times. Frame 143 must wrap cleanly to 0. |
| DINK DONK bell (inside the light loop) | - | A12/B12 = 0.50 s per state | Two physical tube circuits alternate; the off circuit stays dark glass (Brief 54-56). |
| Marquee bulb chase, ripples | - | 2 s period, 3 times per 6 s | Kept in sync with the 6 s page loop. |
| Wet sheets (`wet_*`) | 48 slots (8x6) | 24 fps, 2 s | Default since 3 Nov 2026: 24 unique even phases, each in two slots. `ROXY_WET_FRAMES=48` renders all 48 (Brief 27 bundle only; the Brief 57 bundle rejects it). |
| Prop loops | per entry | e.g. 72 frames / 24 fps / 3 s; poster chase 72 / 12 fps | Each entry has its own `fps`/`frames`; never assume one length. |
| Door sheets | 16 (4x4) | 18 fps, 0.889 s, one-shot | Both endpoints transparent; clamp at the last frame and remove. |

Validation decodes every video frame (VP9 decode with FFmpeg), checks the 143 -> 0 wrap against the ordinary
frame-to-frame step, checks every wet-sheet transition and paired slots, and checks that slices rebuild their parents
exactly. Black-level tolerance is per decoded frame (codec noise up to 2/255 on at most 0.05 % of probe pixels).

### Mist maps (`out10mist/`)

Eight surface passes from the same camera (Brief 50, re-rendered with the sign change in Brief 57), 1x + @2x:

| Map | Meaning |
|---|---|
| `catch.png` | Where rain lands |
| `rim.png` | Edges with a drop (roofs, curbs, ledges) |
| `height.png` | Height above the street |
| `light.png` | Light falling on the surface (tints rain/mist) |

Catch/height/rim come from a 16-sample data/AOV pass, `light` from a 32-sample denoised matte light pass. The lobby
loads the 1x maps from `?mistdir=` (default `out10mist`): `light/catch/height` for the extra-rain layer (on by default)
and all four for the splash-mist shader (`?mist=1..4`, off by default). `mist-baked.png` is the Brief 50 baked
sample image only; nothing loads it.

### Checking a pack

`checksums.json` in the live `out10/` also lists the eight mist maps, under pack-root names (`catch.png` ...),
because it was copied from the staging pack where they sat at the root. Resolve those against `out10mist/`.
Read-only check, run from `standby/`:

```bash
node -e "
const fs=require('fs'),c=require('crypto'),d='roxy3d/out10/',list=JSON.parse(fs.readFileSync(d+'checksums.json'));let bad=0;
for(const e of list){let p=d+e.file;if(!fs.existsSync(p))p='roxy3d/out10mist/'+e.file;
 if(!fs.existsSync(p)||c.createHash('sha256').update(fs.readFileSync(p)).digest('hex')!==e.sha256){bad++;console.log('BAD',e.file)}}
console.log(list.length,'entries,',bad,'bad')"
```

On 5 Nov 2026 this reports 809 entries, 0 bad. `.gitattributes` (`* -text`) keeps files byte-exact; never re-save,
re-encode or reformat art or manifests by hand.

## 3. Render workflow and rules

### The loop

1. **Request.** The owner asks for a change; Claude logs it in `QUEUE-owner.md` or `PROGRESS.md`.
2. **Blockout first** for layout changes: a quick labelled box blockout (Workbench boxes, flat colours, labels on the
   image) before any styled draft (auditorium Briefs 32-33; lobby Brief 12 annotated draft).
3. **Brief.** Claude writes `roxy3d/BRIEF-NN-<topic>.md`: what to change, what must stay identical, the exact
   deliverable, "write only inside roxy3d/", where to put staging output, and "STATUS line, stop".
4. **Codex renders** in the background from `roxy3d/`:
   `codex exec -s workspace-write --skip-git-repo-check -o codex-NN.md "Read BRIEF-NN-....md and do it." < /dev/null`
   (`< /dev/null` matters or it waits on stdin). It reports in `NOTES-NN.md` (lobby) or `qa11/CINEMA-DRAFT-NN.md`
   (auditorium).
5. **Claude checks** the result itself, then runs a **read-only Codex critique** of the draft
   (`codex exec -i <image> -s read-only --skip-git-repo-check -o ...`), weighs it, and says which points it took.
6. **Owner review** of the one draft image. Feedback becomes the next brief.
7. **Full render only when the owner says so** ("render it", "start the final render").
8. **Stage, verify, promote** (below).

### Draft rules (owner, Briefs 14-19)

- A draft is **one** image: the fixed isometric camera, 1280x720, at final quality (final samples, wet materials,
  ray-traced reflections, approved ripples, HDR glare) with one composited weather frame. Target about 1-2 minutes.
- Nothing else: no close-ups, extra review cameras, clips, extra audits, test clips or experiments the owner did not
  ask for. Ask before adding a test clip.
- Approved things are not re-drafted.
- Exceptions seen in practice: auditorium drafts are 1920x1080 stills; small lobby fixes (Briefs 54-56) deliver one
  1280x720 side-by-side crop (live | new) instead of the whole frame.

Lobby drafts are saved as `qa10/draft_N.png` (1-13) and `qa10/draftNN-<topic>.png` (14-24); auditorium drafts as
`qa11/cinema_draft_NN.png`. Both folders are local only.

### Staging and promotion

1. A production brief writes a **full copy** of the live pack plus the re-rendered files into a new staging folder
   (`out10b` ... `out10i`), refreshes its `manifest.json`, `checksums.json`, `validation.json`, and writes a copy list
   (`out10i-copy-list.txt`, `rain-copy-list.txt`): every NEW/CHG file and its destination (`out10` or `out10mist`).
   Unchanged files must stay byte-identical; the notes say how that was checked.
2. Claude tests the staging pack in the page with real chat:
   `lobby.html?everyone=1&artdir=out10i&mistdir=out10i` (no `?demo=1`), console clean.
3. **Back up**, then promote: copy the originals to `out10.pre-<tag>/` (and `out10mist.pre-<tag>/`), copy only the
   listed files into `out10/` (the folder cannot be renamed while the server streams from it), verify all SHA-256.
   Existing rollbacks: `out10.pre-d15`, `.pre-plates`, `.pre-taxi`, `.pre-rain`, `.pre-sign`, `out10mist.pre-sign`,
   `out10.orig-loop`, `out10.stale-20261102`.
4. Log it in `PROGRESS.md`. Clean up work folders only with the owner's OK.

### Local GPU or cloud

The laptop has an RTX 3050 6 GB. Small jobs run locally (Brief 53 rain sprites: 27 min; auditorium draft 13 full set:
about 9.5 min of render time). Whole-frame lobby production does not: a 4K background frame took about 7 min locally
versus about 48 s on a cloud RTX 5090, so Brief 56 was moved to RunPod (Brief 57).

## 4. Cloud rendering on RunPod

### Pieces

| Piece | Where | Role |
|---|---|---|
| Bundle | `cloud/brief57/upload/bundle/` (Brief 57) or `cloud/bundle/` (Brief 27, local only) | `run.sh`, `pipeline.py`, `watchdog.sh`, scene and scripts, `BUNDLE-SHA256SUMS`, `blender-5.2.3.sha256`. |
| Archive | `cloud/roxy-cloud-bundle-56.tar.gz` (160 MiB), `cloud/roxy-cloud-bundle.tar.gz` | The sealed bundle, all members under `bundle/`. Local only (`*.tar.gz` is ignored). |
| Helper | `cloud/cloud-render.sh` | Runs on the PC (Git Bash): rents the pod, uploads, watches, downloads, cleans up. |
| Build/seal | `cloud/brief57/build57.py` (`prepare`, `seal`, `extract`, `preservation`), `deliver57.py`, `local57.ps1` (local `preflight`/`smoke`) | Builds and verifies the archive. |

### Bundle side (`run.sh`)

- Modes: `preflight`, `smoke`, `full`, `validate-only`. Linux x86_64 with an NVIDIA GPU only.
- Takes a run lock (`flock`), checks `BUNDLE-SHA256SUMS`, downloads Blender 5.2.3 from download.blender.org and
  checks the pinned SHA-256, then runs `pipeline.py` in Blender. Caches go inside the bundle (`work/`).
- Writes `progress.log`, `DONE` or `FAILED`, and on success `SUCCESS mode=full archive=out10.tar.gz`.
- Render cache with SHA-256 receipts: a repaired relaunch on the same pod reuses finished captures.
- `watchdog.sh` is detached when the pod's id is known: it stops (never deletes) the pod 3 h after the run ends or
  8 h after launch, whichever is first.
- Brief 57 stages, each in its own Blender process: backgrounds, weather, foreground, doors/WC, mist,
  composition/ads, videos; then contract validation, checksums and `out10.tar.gz` with every member hash read back.
  The result holds the `out10/` payload, the eight mist maps at its root and `_work/cloud57/` QA evidence (not web
  payload). EXRs stay on the pod; their hashes are verified there.

### Helper side (`cloud-render.sh`)

Start it from a terminal of its own (for example the Terminal panel), not inside a Claude session, so it outlives
the session. It needs `runpodctl` at `tools/runpodctl/runpodctl.exe` with the owner's API key configured, and the
SSH key named in the script. No keys are stored in the repo.

```bash
cd standby
bash roxy3d/cloud/cloud-render.sh smoke     # tiny end-to-end check, a few cents
ARCHIVE="$PWD/roxy3d/cloud/roxy-cloud-bundle-56.tar.gz" OUTDIR=roxy3d/out10i.cloud \
  bash roxy3d/cloud/cloud-render.sh full    # the production run (Brief 57 command)
OUTDIR=roxy3d/out10i.cloud bash roxy3d/cloud/cloud-render.sh fetch   # collect a finished run later
```

What `full` does:

1. **Credit guard:** refuses to start when the account credit is below `MIN_BALANCE` (RunPod needs at least $5 on
   the account to create a network volume, and a pod that runs out of credit stops mid-render).
2. **GPU and volume:** picks the first in-stock pair of data center and GPU from `GPUS` (RTX 5090, RTX 4090, L40S),
   creates a 10 GB network volume there, then the pod (SECURE cloud, `runpod/base` image, volume at `/vol`). Every
   5th round with nothing listed it sweeps all data centers; it keeps trying for `WAIT_GPU_MIN` (30) minutes.
   Unused volumes are deleted at once.
3. **Upload and start:** uploads the archive, installs the GL/EGL libraries Blender needs, writes a pod-side
   `launch.sh` (exports the pod id so the watchdog arms, copies `progress.log` to `/vol/results` every 5 min, writes
   the real exit code), unpacks and starts `run.sh`.
4. **Watch:** prints the last progress line every minute; gives up after `MAX_HOURS` (6 for full).
5. **Results survive a lost PC or pod:** at the end the pod copies the archive, its `.sha256` and logs to
   `/vol/results` and stops itself 20 minutes after a success. The helper downloads the archive, checks the SHA-256,
   unpacks it into `OUTDIR` (default `roxy3d/out10.new`), then deletes the pod and the volume.
6. **Failure:** a failed full run whose watchdog is armed keeps its pod (render cache intact) for repair:
   fix the bundle, then `ADOPT_POD=<id> bash cloud-render.sh full` (old `out10` moved aside). `KEEP_ON_FAIL=0` deletes
   it instead. A pod that stops answering SSH is never deleted: the helper waits until it has stopped, then reads
   `/vol/results` with a small pod in the same data center (`fetch`, cheapest GPUs first, CPU last, retries up to
   `FETCH_WAIT_MIN` = 360 min). A volume is deleted only once the result is home (a kept volume costs about
   $0.70/month).

Environment overrides:

| Variable | Default | Meaning |
|---|---|---|
| `ARCHIVE` | `cloud/roxy-cloud-bundle.tar.gz` | Bundle archive to upload (added in Brief 57) |
| `OUTDIR` | `roxy3d/out10.new` | Full-mode unpack folder; the payload lands in `OUTDIR/out10/`. It is cleared first. |
| `GPUS` | RTX 5090, RTX 4090, L40S | GPU preference list |
| `CLOUD`, `IMAGE` | `SECURE`, `runpod/base:0.7.0-ubuntu2004` | Cloud type and base image |
| `MAX_HOURS` | 6 (full), 0.75 (smoke) | Helper time limit |
| `MIN_BALANCE` | set per mode in the script | Credit guard threshold |
| `WAIT_GPU_MIN`, `BOOT_MIN`, `LOST_MIN` | 30, 20, 20 | Wait for a GPU, for SSH, before treating the pod as lost |
| `PIN_DC` | - | Only use this data center |
| `KEEP_ON_FAIL`, `ADOPT_POD` | 1, - | Keep a failed pod; reuse a kept pod |
| `FETCH_MODE`, `FETCH_GPUS`, `FETCH_WAIT_MIN` | full, cheap GPU list + CPU, 360 | `fetch` options |
| `TEST_FETCH=1` | - | Test the lost-pod path (delete the GPU pod, fetch via a second pod) |

### Runs so far

| Run | Date | GPU | Bundle | Time | Cost (approx.) | Outcome |
|---|---|---|---|---|---|---|
| 1-2 | 2-3 Nov 2026 | RTX 5090 | Brief 26 (draft 13) | ~5.5 h | not recorded | Failed in the last packaging step (over-strict black check on the 4K loop); pod deleted, all renders lost. Fixes: per-frame codec tolerance, keep pod on failure, real exit code, armed watchdog. |
| 3 | 3 Nov 2026 | RTX 4090 | Brief 26 | ~35 min | small | Stopped by the owner to get a faster pipeline first (Brief 27). |
| 4 | 3 Nov 2026 | L40S | Brief 27 | ~6.4 h billed | ~$7 | Pod became unreachable; result lived only on the container disk and was lost. Led to the network-volume / `fetch` rewrite. |
| 5 | 3 Nov 2026 | RTX 5090 | Brief 27, 24 wet frames | 2 h 45 min | ~$3.30 | Success: first live `out10`. |
| 6 | 5 Nov 2026 | RTX 4090 | Brief 57 (Brief 56 sign production) | 3 h 02 min wall (pipeline 2.91 h) | ~$2.75 | Success: promoted into `out10`/`out10mist` the same evening. |

Run 6 stage times: backgrounds 3454 s, weather 878 s, foreground 5031 s, doors 609 s, mist 99 s, package 28 s,
videos 203 s. Rates noted at the time: RTX 4090 $0.89/h, RTX 5090 $1.19/h, L40S $1.09/h. Plan on **about 3-4 billed
hours and $3-5** for a full lobby production run.

## 5. Auditorium art (`roxy3d/qa11/`)

The auditorium is one fixed camera with almost no animation, so it is rendered locally on the laptop GPU. The page
reads `qa11/cinema_draft_NN.png` + `qa11/cinema_layout_NN.json`; `?draft=NN` picks a draft, default `13`
(set in `auditorium.html`). The layout contract is documented in [auditorium.md](auditorium.md).

### Files of a full draft (draft 13 is live)

| Files | What |
|---|---|
| `cinema_draft_13.png`, `@2x` | Lit room (house lights up), 1920x1080 and native 3840x2160 |
| `cinema_draft_13_dim.png`, `@2x` | Lights-down state (`page_layers.dim`) |
| `cinema_layout_13.json` | Camera, rows/seats (135), aisles, stairs, screen corners (1080p and 4K), walk routes, tunnel, `page_layers` |
| `draft13/slices/depth_NNN(@2x).png` | 159 depth slices (lit), `z_index = 1000 + round(key * 100)`, key = `(u + v) + zpx_world / 90` |
| `draft13_dim/slices/...` | Dim twins: identical names, rectangles, keys, z-index and alpha bytes |
| `draft13/door_entrance(@2x).png`, `door_static_cutout(@2x).png` (+ `draft13_dim/`) | Entrance door sheet (16 frames 4x4, 18 fps, hold frames 5-10) and the static cutout mask |
| `draft13_bands/`, `draft13_dim_bands/` | Banded pieces of every slice (below); 2,332 pieces per state |
| `cinema_layout_13.before-bands.json` | Layout as delivered, before banding |
| `CINEMA-DRAFT-13.md`, `runtime13_full/` | Codex report and evidence; `runtime13_full/run.ps1` reproduces it (local only) |

Draft 13 production: Cycles OptiX on the RTX 3050, native 4K, adaptive 64-384 samples, threshold 0.007, seed 341997,
inherited AgX; 1x is an exact 2x2 area reduction of the 4K display bytes; slice RGB comes from the delivered beauty,
coverage from 4K first-hit depth AOV batches. Total render time 565 s. Reproduce with
`runtime13_full/run.ps1 -Mode render|package|dim-render|dim-package|verify|report` (calls
`build_cinema_draft13.py` in Blender). Sources: `roxy_cinema_draft13.blend`, `roxy_cinema_draft13_dim.blend`.

Drafts 1-9 are single stills (5 and 6 are blockouts); draft 10 added page layers (door, slices); draft 11 was the
first final 4K set; draft 12 changed the door; draft 13 re-seated the step lights.

### Banded slices (`roxy3d/tools/band-slices.mjs`)

Slice bounding boxes cover about 25 screens of pixels; the browser decoded far too much. Claude runs this after a
Codex delivery:

```bash
cd standby
LAYOUT=cinema_layout_13.json node roxy3d/tools/band-slices.mjs roxy3d/qa11 64 --dry   # check only
LAYOUT=cinema_layout_13.json node roxy3d/tools/band-slices.mjs roxy3d/qa11 64
```

- Cuts every slice (lit + dim, 1x + 2x) into 64 px horizontal bands trimmed to visible pixels; columns closer than
  `GAP` (48) stay one piece; 2 overlap rows hold only fully opaque pixels so zoomed seams stay covered; 1 px pad.
- Rebuilds each slice from its pieces and requires an exact RGBA match before writing anything.
- Writes `<name>_bNN(@2x).png` into `draftNN_bands/` and `draftNN_dim_bands/`, adds `pieces` to each slice in the
  layout JSON (in place) and saves `cinema_layout_NN.before-bands.json` once.
- The page draws pieces only near chatters; whole slices remain a fallback.

## 6. Intro video (`intro-dinkdonk/`)

A 1998-style cinema curtain-raiser snipe re-branded as DINK DONK for the cinema scene (3 Nov 2026, polished 4 Nov):
the neon DinkDonk emote replaces the logo letter, the ring text reads DINK DONK / CINEMAS, and the dome signs are
replaced. Original audio is kept. No BRIEF covers it; it was built directly with Blender scripts. All scripts run
as `blender -b --factory-startup --python <script> -- <args>` (no FFmpeg needed).

| Script | Does |
|---|---|
| `neon_emote.py` | Turns `dinkdonk-emote-128.png` into neon tubes + halos (module) |
| `build_logo.py` | Renders the logo card, source frames 1109-1386, over `plate_1108.png` (`dd_NNNNN.png`) |
| `track_sign.py` | Tracks the dome sign panels in the original frames (`gNNNNN.png`, 1920 px) -> track JSON |
| `make_sign_face.py` | Renders `sign_face.png` (flat neon emote) |
| `sign_replace.py` | Warps the face onto the tracked panels, keeps bulbs in front (`sg_NNNNN.png`) |
| `compose.py` | Lays the frames over the original video and writes H.264/AAC MP4 with the original audio |

Drafts were 720p (`draft01..03_dinkdonk_720p.mp4`); the final is
`DinkDonk Cinemas Neon Curtain Raiser and Coming Attractions (1080p).mp4`. The original source video and its frame
dumps are not in the repo. `dinkdonk_logo.blend` is the saved logo scene.

## 7. History of briefs and passes

Dates are the day each brief was written (from its text or `PROGRESS.md`). Briefs 46-50 are numbered twice: one
lobby brief and one auditorium ("cinema") brief each.

| Brief | Date | Scene | Output | What changed |
|---|---|---|---|---|
| 1 (`BRIEF.md`) | 1 Nov 2026 | Lobby | `out/` | Pass 1: pre-rendered isometric background + occluder sprites for the canvas blockout |
| 2-3 | 1 Nov | Lobby | `out2/` | Pass 2: counters against the walls, grittier 90s look, `base` + `light_loop` |
| 4 | 1 Nov | Lobby | `out3/` | Pass 3: bus/taxi/cars and arrivals |
| 5 | 1 Nov | Lobby | `out4/` | Pass 4: art polish, small prop loops |
| 6 | 2 Nov | Lobby | `out5/` | Pass 5: vehicle depth slices, brake lights, lobby cat |
| 7 | 2 Nov | Lobby | `out6/` | Pass 6: signs, wear, door animations, umbrellas, janitor, drip |
| 8 | 2 Nov | Lobby | `out7/` | Pass 7: carried items, staff caps, indicator-only lights |
| 9, 9b, 10 | 2 Nov | Lobby | `out8/`, `out8b/` | Pass 8/8b: surrounding city, heavy rain, wet glass, lighting fixes |
| 11 | 2 Nov | Lobby | `out9/` | Pass 9: everything in-world (no screen-facing overlays), ad quads, LED signs |
| 12-14 | 2 Nov | Lobby | `qa10/` drafts 1-3 | Pass 10 "draft first": layout 3 (three screens on the right, one auditorium building), real DinkDonk emote neon; drafts-only rule |
| 15-20 | 2 Nov | Lobby | drafts 4-9 | New draft standard; wet road realism, restroom graffiti, rooftop billboards, stray-line fixes |
| 21 | 2 Nov | Lobby | cloud bundle | First portable cloud bundle + 1-frame local test |
| 22-25 | 2 Nov | Lobby | drafts 10-13 | Rain realism, really dark night, quieter restroom, lit DINK DONK sign; draft 13 approved |
| 26 | 2 Nov | Lobby | final bundle | Production bundle from draft 13; cloud runs 1-3 |
| 27 | 3 Nov | Lobby | fast pipeline, `qa10/draft14-fast.png` | 4K-only + downscale, combined mask capture where it passes, less overhead, 24 wet frames default; run 5 -> live `out10` |
| 28-36 | 3 Nov | Auditorium | drafts 1-9 | New scene; childhood-cinema look, blockouts 5-6, styled 7, tunnel 8-9 |
| 37 | 3 Nov | Auditorium | draft 10 | Entrance door, closed underside, depth slices for the page |
| 38, 40, 41, 43, 44 | 3 Nov | Auditorium | page code | Codex page work: director/control, names, pre-show phases, dim crossfade, QA |
| 39, 42 | 3 Nov | Auditorium | draft 11 + dim | Polish + first final 4K set (local); lights-down state |
| 45 | 4 Nov | Lobby | `out10-loopfix/` | Alley reflection flicker fixed in the light loops without a re-render |
| 46-47 (cinema) | 4 Nov | Auditorium | draft 12 | Lobby's padded door at uniform scale; full pass |
| 46-47 (lobby) | 4 Nov | Lobby | draft 15, `out10b/` | Night-lit vehicles, Screen 2 door; promoted |
| 48-49, 50 (cinema) | 4 Nov | Auditorium | draft 13 | Step lights dimmed (V2 45 %) and re-seated; full pass, live |
| 48 (lobby) | 4 Nov | Lobby | `out10c/` | Stray bus number plates removed; copied into `out10` |
| 49 (lobby) | 4 Nov | Lobby | draft 16, `out10d/` | Smaller taxi roof sign; copied into `out10` |
| 50 (lobby) | 4 Nov | Lobby | `out10mist/`, draft 17 | Splash-mist surface maps + baked sample |
| 51-53 | 4 Nov | Lobby | drafts 20-21, `out10e-g/` | Rendered rain on umbrellas and roofs, tyre spray and wake; production promoted |
| 54-55 | 5 Nov | Lobby | drafts 22-23 | DINK DONK "CINEMAS" line, bell at half speed, cleanup |
| 56 | 5 Nov | Lobby | `out10i/` | Production of draft 23 + floodlight re-aim (local run stopped) |
| 57 | 5 Nov | Lobby | `roxy-cloud-bundle-56.tar.gz` | Brief 56 moved to RunPod; `ARCHIVE`/`OUTDIR` overrides |
| 58 | 5 Nov | Lobby | `out10i/`, draft 24 check image | Verified the cloud result, copy list, `NOTES-56.md`; promoted 5 Nov 2026 |

## 8. How to change or re-render art

### Prerequisites

- Windows PC with an NVIDIA GPU (OptiX), Blender 5.2.3 in `tools/blender-5.2.3-windows-x64/`, Node 18+, Git Bash,
  the Codex CLI. For cloud runs: `runpodctl` with your own API key and SSH key, and the owner's go-ahead.
- Drafts, QA shots and staging packs are not in git; you start from the `.blend` files and scripts that are.

### Change lobby art

1. Find the current source scene. The newest lobby production scene in git is
   `roxy3d/cloud/brief57/upload/bundle/out10i/_work/pipeline/scene.blend` (draft 23 sign + floodlight fix). Older
   steps: `roxy_pass10_draft.blend` (draft 13 state) and the local-only `cloud/bundle/scene.blend`. Vehicles,
   umbrellas, cat, janitor and items come from separate rigs (`build_vehicles.py`, `roxy_vehicles*.blend`, ...) and
   are carried byte-identical through later runs.
2. Write `BRIEF-NN-<topic>.md` (next free number) with the change, what must stay identical, "ONE draft image" or the
   production deliverable, a staging folder name, and "write only inside roxy3d/".
3. Run Codex in the background (command in section 3), check its draft yourself, get a read-only critique, show the
   owner the one image. Repeat until approved.
4. Production after the owner says so: local for sprite-sized jobs; for whole-frame passes, a cloud bundle (copy the
   Brief 57 layout: frozen scene, `pipeline.py` stages, `BUNDLE-SHA256SUMS`, seal with every member hash read back),
   local `preflight` + `smoke` first, then `cloud-render.sh full` with `ARCHIVE`/`OUTDIR`.
5. Stage into a new `out10<letter>/` with a copy list, test with `?artdir=` / `?mistdir=` and real chat, back up,
   promote, verify checksums, log in `PROGRESS.md`.
6. Commit only when the owner asks. `out10/` and `out10mist/` are tracked, so changed files show up in `git status`.

Re-running the Brief 56 sign render as-is needs `cloud/roxy-cloud-bundle-56.tar.gz`, which exists only on the owner's
PC. `build57.py seal` reads `out10i/_work/`, deleted on 5 Nov 2026, and `upload/bundle/out10/` (the 802-file
baseline) is not in git, so rebuilding the archive from git needs those inputs restored or the script adapted.

### Change auditorium art

1. Brief Codex with the last builder (`build_cinema_draftNN.py`) and scene (`roxy_cinema_draftNN.blend`); layout
   changes need a blockout first. New drafts go to `qa11/` as `cinema_draft_NN.png`, `cinema_layout_NN.json`,
   `CINEMA-DRAFT-NN.md`; a full pass adds `@2x`, `_dim`, `draftNN/`, `draftNN_dim/`.
2. Band the slices with `band-slices.mjs` (section 5).
3. Test with `auditorium.html?everyone=1&draft=NN`, then make it the default in `auditorium.html` (see
   [auditorium.md](auditorium.md), "Recipes").
4. Add exactly the files the page loads to git. `roxy3d/qa11/` is ignored as a folder; from `standby/` (from
   `README.md`):

```bash
node -e "const {artFiles}=require('./package/art');console.log(artFiles('.',m=>{throw m}).files.filter(f=>f.startsWith('roxy3d/qa11')).join('\n'))" > qa11-files.txt
git add -f --pathspec-from-file=qa11-files.txt && rm qa11-files.txt
```

`art.js` reads the default draft from `auditorium.html`, then adds the layout JSON, both beauties and every art path
named anywhere in that JSON (with `@2x` guesses) that exists on disk.

## 9. Known gaps and inconsistencies (5 Nov 2026)

- `out10/checksums.json` lists the eight mist maps at the pack root; they live in `out10mist/` (see "Checking a pack").
- Live `out10/` still carries staging wording from Brief 58: `validation.json` scope says promotion is pending,
  `.cloud-build.json` has `page_acceptance_pending: true`, and `NOTES-PASS10.md` says to test `?artdir=out10i` and
  points to `out10i/_work` and `out10i.cloud`, both deleted on 5 Nov 2026.
- `manifest.json` says `seed: 1997`; `NOTES-56.md`, `NOTES-57.md` and `NOTES-PASS10.md` say the production seed was 1701.
- The `lobby.html` comment next to `ART` still describes `out10` as the 3 Nov draft-13 cloud run.
- `cloud/README-CLOUD.md` documents the Brief 27 bundle internals, not how to use `cloud-render.sh` (its usage is in
  the script header). The Brief 57 bundle went back to isolated foreground renders instead of Brief 27's combined
  mask cuts.
- `cinema_layout_13.json` inherits draft 12 metadata: `brief` names BRIEF-47 and the `render` block is historical;
  current evidence is in `qa11/runtime13_full/` (local only). `CINEMA-DRAFT-13.md` says "No pieces"; banding was
  added afterwards.
- Because `art.js` follows every path in the layout JSON, provenance-only files are tracked and packaged too:
  `qa11/draft10/` (161 files, ~61 MB), `cinema_draft_10.png`, `runtime12_full/verification.json`.
- Auditorium drafts are 1920x1080, not the 1280x720 lobby draft size.
