Completed pass 3 in [roxy3d/out3/](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out3). **All 281 files in the live `out/` and `out2/` folders remain unchanged**, verified by SHA-256.

The delivery includes:

- Bus, yellow taxi, burgundy sedan, and blue sedan with pop-up headlights—in both directions, at 1× and native 2×.
- Matching additive headlights, tail-light glow, and wet-road reflections.
- Bus and taxi open-door variants.
- `lit_bg.png` and `lit_bg@2x.png` without occluders.
- A complete layout-2 [manifest](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out3/manifest.json), including shared body/light anchors, lengths, lane centres, and arrival coordinates. All 141 inherited assets were copied byte-for-byte.

I inspected the references, intermediate renders, and final composites. Camera calibration passed with a maximum error of **0.0112 px**. Body/light anchors match exactly, and both fallback resolutions reconstruct the original full scene with **zero pixel difference**. The 48 vehicle PNGs total **2.77 MB**.

Review the [scene preview](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa3/scene_1.png), [three-position lane check](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa3/vehicles_check.png), and [arrival/door comparison](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa3/arrivals_check.png).

New baked lettering includes **95 ROXY**, **ROXY TRANSIT**, **TAXI**, and small number plates. Existing scene footprints are unchanged; vehicle overhangs are documented. Curb-side doors are mostly hidden by the vehicle from this camera, so the near-lane open states are subtle.

Re-render commands, placement details, measurements, and limitations are in [NOTES-PASS3.md](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS3.md). The page and shared files were not edited.