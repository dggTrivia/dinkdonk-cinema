# The Roxy, layout 2

This pass implements BRIEF-3-pass2.md and BRIEF-2-loops.md in `out2/`.
The live `out/`, page and shared files are not edited. No network requests,
downloaded assets, or installed packages are needed. Pass-1 helper modules are
imported, but their output runners are never invoked.

## Layout and surface work

Both lobby partitions are 90px high. The ticket counter is at
`[3.8,5.0,4.4,8.4]`, 44px high, with cashier glazing to 84px, two actual speaking
holes and tray openings at v=6.0 and 7.4. Its lightboard and showtime prices are
mounted on the u=3 wall. The register and printer shelves leave the specified
cashier floor positions clear.

The snack front counter is `[5.6,4.0,11.6,4.6]`, 44px high, with a recessed glass
candy display. The v=3 back bar has two lit popcorn machines, a four-button soda
fountain, hotdog rollers, a nacho warmer and stacked cups. All three price boards
are on the wall plane below z=90. The low cabinet is background; tall appliances
share the right partition's depth-sliced sprite, behind the clerks. All those
appliance lights are static.

The podium, bench and second standee use the exact requested new sorting
footprints. The arcade and first standee keep their requested positions. A palm
pot occupies `[12.3,3.4,12.8,3.9]`; its leaves naturally overhang that footprint.
The original gate sign is retained. `manifest.json` includes staff/customer
positions and every geometry overhang under `coordinate_deviations`.

Worn materials use fixed-seed world-space noise over fine material detail:
flattened carpet traffic paths, a faded geometric weave and medallion, water
streaks on plaster, skirting scuffs, faded poster edging, grimy glass, sidewalk
gum, asphalt aggregate, cracks and oil tide marks. Static subpixel film grain
and restrained neon halos are baked into the background. All movie-title and
poster apertures remain blank; the billboard inner rectangle stays exactly
`[1296,40,576,324]`.

## Reproduction

From the standby workspace, using the bundled Blender and its bundled Python:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass2.ps1 -Mode preview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass2.ps1 -Mode stills
powershell.exe -NoProfile -ExecutionPolicy Bypass -File roxy3d/render_pass2.ps1 -Mode loops
```

`-Mode all` runs stills, publishes their manifest, then creates the animation.
`-Samples` defaults to 96. The wrapper uses a process-local execution-policy flag
and restores its cache/temp environment variables on exit. All explicit caches,
renders and logs remain within roxy3d. `roxy_pass2.blend` contains the layout-2
scene with its font packed.

## Still delivery and QA

The packaging step validates all referenced 1x/2x PNGs and exact parent
reconstruction before atomically publishing `out2/manifest.json`. Its early
snapshot is retained at `qa2/manifest_stills_ready.json`, so the layout can be
integrated before animation finishes.

The same orthographic camera is used without changes. A fresh five-marker
render in `qa2/calibration.png` measures a maximum axis error of
**0.0159983873 pixels**. The machine-readable check is `qa2/calibration.json`.
Layer dimensions and SHA-256 hashes are recorded by packaging; a separate
layout validator checks the requested coordinates and the original live output
hashes. `staff_depth_witness.png` uses 50px stand-ins at the exact requested
staff/customer positions, using the delivered z-sorted layers.

The references, successive layout previews, full render and individual sprites
were visually inspected. Inspection caught and fixed moved-object transforms
and an opaque candy-display front before final rendering.

## Animation

`out2/base.png` and `base@2x.png` contain the background at the animated lights'
minimum values, with no rain or splashes. `bg.png` and `bg@2x.png` are identical
aliases for integrations using the earlier field. Every parent sprite was
rendered again at this lighting state, and its depth pieces were rebuilt from
the unchanged geometry position AOVs. Static halos and grain are baked into
base; `glow` is null.

`out2/light_loop.webm` is 1920x1080 VP9, 120 frames, 24fps, five seconds, without
audio. Each source video frame is exactly `max(animated_background - base, 0)`
in sRGB display space. Stack it with **plus-lighter** over base, below the
z-sorted walkers and supplied `render_layers`. The video is opaque RGB on black;
it does not require an alpha-capable video decoder. Use its natural 1920x1080
coordinates and scale the entire composition together for a 4K source.

`full.png` is the flattened scene at frame 60, including its static sprites.
`full@2x.png` uses the true 4K base/sprites plus a bilinearly scaled copy of that
same 1080p light frame, matching the intended page stack. When using full as a
still fallback, do not draw the sprite layers over it again. Composite previews
at frames 0, 30, 60, 90 and 119 are in `qa2/loop_fNNN.png`; previews made from the
actual decoded WebM are in `qa2/decoded_preview_fNNN.png`.

The moving environment includes falling rain, pavement impact flecks and
expanding rings, waves in wet neon reflections, a restrained offscreen headlight
sweep, neon intensity/color variation, projector light flicker, and a chase
around the billboard bezel. Rain is excluded from the indoor building and blank
marquee boxes. The exact billboard aperture is black in the additive source,
with an additional two-pixel dark collar to limit codec ringing at the boundary.

The video is intentionally below all occluders. Counter, appliance, partition,
arcade, bus-shelter, entrance-post, street-lamp and ROXY-blade lights remain
static. Their opaque sprites cover video in those regions; fractional-alpha
glass can show light/rain behind it. The tall back bar is also static and sorted
behind its clerks. This is the requested integration contract, not a simulated
light change on foreground walkers or prop surfaces.

Four fixed 96-sample Cycles light bases and one minimum background are used.
Their denoised results stay fixed, so there is no independent per-frame denoiser
shimmer. Integer-frequency periodic functions drive all movement. The exact
period endpoint is regenerated independently and compared byte-for-byte with
frame 0, and last-to-first change is compared with ordinary adjacent changes.
The encoder is Blender's bundled FFmpeg, with VP9 CRF 4. The final check reads
the WebM container metadata and decodes seven frames through Blender, compares
their pixels with the input PNGs, checks the dark aperture, and reconstructs
the complete source-over composition. Only then is the final manifest published.

## Output boundary and coordinate details

All ten requested layout-2 sorting footprints are checked numerically. Natural
visual overhangs are listed separately under `coordinate_deviations` and
`geometry_footprint` / `geometry_z_px` per occluder: standee feet, palm leaves,
wall-facing finish and back-bar nozzles, small neon trims, the bus route plaque,
and the preserved raised ROXY/ORBIT lettering and podium lamp. These bounds are
measured from the saved scene. They do not move the staff/customer floor points
or the requested sorting footprints.

The live output inventory contains 139 files. `qa2/live_out_before.json` records
their original SHA-256 values; `verify_pass2.py` checks every byte hash and the
file count after the pass. No live-page or OBS integration changes are part of
this art task. The standalone depth witness uses proxies, not real chatters.

## Final measured results

The final package contains **140 PNGs**, the WebM, and its manifest: **142 files,
47,549,207 bytes** in total. There are **18 parent occluders and 49 depth slices**,
each at 1x and 2x. The loop is **2,802,653 bytes** (2.80 MB), with 120 decoded
frames and a five-second container duration. Its VP9 track reports a default
frame duration of 41,666,666 ns, the integer representation of 24fps.

| Check | Result |
| --- | --- |
| Maximum calibrated axis error | 0.0159983873 px |
| Parent reconstruction from depth slices, both sizes | 0 maximum channel error |
| Exact periodic endpoint, source frames 0 and 120 | Identical, maximum error 0 |
| Source last-to-first mean absolute RGB change | 0.192897 / 255 |
| Average ordinary adjacent source-frame change | 0.271219 / 255 |
| Decoded last-to-first mean absolute RGB change | 0.193396 / 255 |
| Decoded first adjacent / last adjacent change | 0.208729 / 0.201190 |
| Rebuilt base + source light + sprite preview | Identical, maximum error 0 |
| Decoded sample mean absolute RGB errors | 0.0621 to 0.3071 / 255 |
| Decoded sample PSNR | 47.01 to 53.32 dB |
| Source billboard aperture | Exact black |
| Decoded billboard aperture maximum | 2 / 255, within lossy-codec tolerance |
| Original live out/ files checked unchanged | 139 of 139 |

The 96-sample still pass used 415.364 seconds of rendering including the four
corrective crop renders. Minimum-light scene/sprites plus four light bases took
351.257 render seconds. Final 120-frame composition took 141.546 seconds, and
VP9 encoding plus seven decoded QA frames took 19.666 seconds: approximately
8.5 minutes for the final loop pipeline's measured work, excluding small setup
and inventory checks. Iteration logs are retained under `qa2/`.

Visual review covered all reference images, successive previews, 4K details,
transparent sprite sheets, staff-depth witnesses, several source loop frames,
and composite frames decoded from the actual final video. The crop correction
uses a 0.1px normalized-border bias before Blender's integer truncation; all
delivered dimensions and offsets are exact integer 1x / doubled 2x values.

Baked static text comprises TICKETS and its prices, SNACK BAR and price menus,
the gate directions, RESTROOM, ROXY, BUS 95, ORBIT, POPCORN and the original
MIDNIGHT/VOYAGER standee titles. Dynamic movie titles, wall posters, restroom
occupancy, chatters and UI remain for page integration.

The final checks and complete SHA-256 inventory are in `qa2/final_delivery.json`.
Other evidence: `layout_validation.json`, `slice_validation.json`,
`loop_validation.json`, `video_validation.json` and `video_metadata.json`.
The only video approximation is normal VP9 color subsampling/quantization;
the lossless source frames and exact periodic/compositing checks are retained.
