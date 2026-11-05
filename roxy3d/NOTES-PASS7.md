# Roxy pass 7 delivery

Completed brief 8 in `out7/`: a complete layout-2 pack with six attachable
rendered items and indicator-only light maps. There are **392 files,
80,551,953 bytes**. The **363 inherited non-manifest assets are byte-identical
to out6**, including every background, animation, character, vehicle, slice,
ambient video and prop loop. The 28 additions are PNGs: twelve item images
and sixteen indicator-only light maps.

All **1,367 files** in the six live packs (`out/`, `out2/`, `out3/`, `out4/`,
`out5/`, `out6/`) match the pre-work inventory and SHA-256 hashes. No page,
shared code or file outside roxy3d was edited.

## Manifest compatibility

`out7/manifest.json` is complete and ready to consume. Every inherited key,
list and scalar value remains unchanged. The new fields are:

- `items`, `item_contract`;
- `light_indicator_only` and `light_indicator_only_2x` in each bus/taxi
  direction and each nested `door_open` entry;
- `vehicle_indicator_only_contract`;
- `asset_pack_pass: 7`, `pass7_art`, `pass7_validation`.

The brief says "only add", so the legacy `pass: 6` field is deliberately
retained. **`asset_pack_pass: 7` identifies this pack**; the inherited scene
art is still pass 6. No old field or contract was repurposed.

## Attachable items

Files are `items/<name>.png` and `items/<name>@2x.png`. Each entry has `file`,
`file_2x`, `w`, `h`, `anchor` and `attach_point`. All coordinates below are
logical 1x pixels; the high-resolution files are exactly twice the dimensions.

| Name | Canvas w x h | Anchor | Attachment |
| --- | --- | --- | --- |
| popcorn | 16 x 20 | [8, 18] | bottom centre of tub |
| soda | 12 x 18 | [6, 16] | bottom centre of cup |
| stub | 12 x 8 | [6, 4] | centre |
| ticket | 18 x 11 | [9, 5.5] | centre |
| cap_cashier | 28 x 12 | [14, 10] | bottom centre |
| cap_usher | 28 x 12 | [14, 10] | bottom centre |

Place the image top-left at `attachmentScreenPoint - anchor`, displaying
either resolution at `w` by `h`. Use ordinary source-over with straight RGBA.
The outer pixel border is transparent at both scales, and all fully transparent
pixels have zero RGB. Internal shadows and material highlights are baked in;
these floating accessories have no ground shadow.

The page chooses the carried item's point at the emote's lower right. Place
a staff cap's attachment point at the emote's top centre, allowing for any
transparent padding in the emote itself. Draw attached items with their owner,
immediately above the emote. Ticket flight is a page translation/rotation
around its centre anchor; the half-pixel Y value is intentional for an 11px
canvas. No new timing or floor footprint is imposed.

The original geometry includes a tapered red/cream striped tub with individually
lobed popcorn kernels; a waxed paper cup with rolled lid, print and bent striped
straw; thick paper tickets with ink rules, serial marks, notches/perforations
and a torn stub edge; a red peaked staff cap with gold trim; and a maroon
pillbox with gold band and button. Paper creases, fibre edges, subdued cloth
texture and worn seams carry the established palette and material treatment.

`render_items_pass7.py` loads `roxy_pass6.blend` read-only, retaining its exact
camera, world and lights. Existing scene geometry is camera-invisible but
continues to affect illumination. The props are lit at `P(8,7,50)` in the lobby.
Only uniform model sizing/placement is used when fitting the rendered bounds;
the caps' shallow crown and fore-aft profiles are model geometry. The card
faces are tilted toward the overhead light. No extra lamps, image textures,
downloaded assets or painted-over renders are used.

Finals use Cycles CPU, 96 samples, denoising, the inherited AgX treatment,
and a 4x render crop. Premultiplied area averaging produces the 2x image,
then the 1x image; each PNG stores straight alpha. Native-size, 2x and enlarged
reviews are in `qa7/item_contact_sheet.png`, with attachment crosses.

## Indicator-only lights

Both resolutions are provided for these eight states:

- bus +u closed and door-open;
- bus -u closed and door-open;
- taxi +u closed and door-open;
- taxi -u closed and door-open.

Names are `vehicles/<vehicle>_<plus|minus>[_open]_light_indicator_only.png`
and the matching `@2x.png`. They are RGB on black, with the same canvas and
anchor as their corresponding existing light and body:

| Vehicle/direction | Logical canvas | Anchor (same for open/closed) |
| --- | --- | --- |
| bus +u | 433 x 261 | [164, 118] |
| bus -u | 437 x 291 | [272, 137] |
| taxi +u | 354 x 185 | [119, 63] |
| taxi -u | 357 x 256 | [238, 121] |

Each is the **exact positive pixel difference** between the existing delivered
indicator-on and normal light maps, independently at each resolution:

```text
indicatorOnly = max(light_indicator - light, 0)
normal + indicatorOnly = light_indicator
brakingAndIndicating = min(light_brake + indicatorOnly, 255)
```

These operations are per sRGB RGB channel, matching the existing asset
contract. Use additive/plus-lighter compositing and position at
`P(u,v) - direction.anchor`. Draw one normal **or** brake light map below the
bodies, then add the indicator-only layer while the signal is on. Hide only
the indicator-only layer while it is off. The amber glow and its existing
ray-traced wet-road reflection are retained without adding the normal lights
twice. Black borders prevent rectangle seams.

The old `light_indicator` fields remain complete replacement maps and retain
their original contract. The new files are additive deltas, as described by
`vehicle_indicator_only_contract`. Directional body depth slices, tyre spray,
door geometry and every other vehicle field are unchanged.

## Coordinates, signs and calibration

**No existing coordinate, anchor, canvas, rectangle, geometry bound, footprint,
sorting value or baked sign changed.** The only new attachment coordinates
are listed above. The inherited black billboard placeholder, aperture,
marquees, poster mappings, carpet and doors remain byte-identical.

Existing baked signs remain: `tickets`, `showtime_prices`, `snackbar`, `gate`,
`restroom`, `roxy`, `bus95`, `arcade_orbit`, `popcorn`, `standee_midnight` and
`standee_voyager`. Inherited animated lettering includes SODA and
INSERT / COIN. No new scene sign is introduced.

`calibrate_pass7.py` opens the actual saved pass-6 camera and independently
renders eleven markers, including the new item illumination point. Maximum
axis error is **0.01116302970842753 px**, within the required +/-1 px at
1920 x 1080. Detailed expected/measured positions are in `qa7/calibration.json`.

## Review and acceptance

Reviewed the style reference and delivered scene, several item render
iterations, the final item/attachment contact sheets, all eight light states,
and actual decoded on/off preview frames. Review artifacts:

- `qa7/item_contact_sheet.png`: native, 2x and enlarged delivered items;
- `qa7/attachment_check.png`: actual items on 50px emote-size proxies;
- `qa7/indicator_contact_sheet.png`: normal, delta alone, normal+delta and
  brake+delta for every requested vehicle state;
- `qa7/pass7_preview.mp4`: four seconds, 1280 x 720, 24 fps, 96 frames,
  844,397 bytes; an illustrative ticket flight and indicator blink;
- `qa7/final_validation.json`: all assertions and SHA-256 output inventory.

The emote proxies are labelled QA rulers only and are not part of out7.
The preview transforms impose no page timing. Six actual decoded MP4 frames
were compared numerically with their source images; mean RGB error ranges
from **1.112873 to 1.318326 levels out of 255**. Selected decoded on/off frames
were also inspected visually. This is asset/compositing QA, not a claim that
the separate HTML integration has been executed.

Acceptance passes for every inherited manifest value, all six protected live
inventories and hashes, all 363 inherited asset hashes, the exact 28-file
addition set, both item resolutions, source/downsample equality, transparent
borders, straight alpha, attachment edges/centres, light dimensions/anchors,
opaque black backgrounds, exact indicator subtraction, exact normal-light
reconstruction, brake combination, marker calibration and decoded video.
No known asset defects remain.

## Reproduction

Run from the standby workspace:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass7.ps1 -Mode all -Samples 96
# Repackage the existing final raw item renders and repeat acceptance:
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass7.ps1 -Mode package
# Six 24-sample 4x look-development renders, without touching out7:
powershell -NoProfile -ExecutionPolicy Bypass -File .\roxy3d\render_pass7.ps1 -Mode preview
```

The package mode was run end-to-end successfully. The wrapper fails on Python
errors, preserves its first live baseline, and redirects caches/temporary
files beneath roxy3d. Helper modules from earlier passes are imported for pure
geometry, image IO and compositing functions; their old entry points are not
run. No live output folder is a write target.

Measured final production timings: **5.507 seconds** for the six item models
and renders after scene setup (individual render calls total 3.743 seconds),
**1.806 seconds** for copying/packaging, and **2.585 seconds** for review
MP4 encoding plus six decodes. Metadata and logs are in qa7. Recreating the
unchanged base scene from scratch remains the pass-6 pipeline; pass 7 reuses
its saved scene and published pack.
