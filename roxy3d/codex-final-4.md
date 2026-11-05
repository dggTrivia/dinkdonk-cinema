Completed pass 4 in **`roxy3d/out4/`**. All **473 files** in `out/`, `out2/` and `out3/` remain byte-for-byte unchanged.

- Calmed the carpet, reducing measured local detail contrast by **60.3%**, and darkened the worn walkway.
- Added warm pools at both ticket windows, all three snack registers, the usher gate and all five screen doors. Reduced general lobby light, countertop brightness and local luminous trim.
- Added **eight additive prop loops**: both popcorn machines, arcade attract mode, three menu boards, soda fountain and the E in TICKETS. Each has 72 frames at 24 fps, lasting 3 seconds, with 1× and 2× PNG sheets.
- Regenerated the stills, occluders, depth slices, `lit_bg` fallbacks and ambient VP9 loop. All previous manifest keys remain; geometry, footprints, placement contracts and all 48 vehicle PNGs are unchanged.

Validation passes at both resolutions. Maximum calibration error is **0.0112 px**; slice and fallback reconstruction are pixel-exact. Loop endpoints match exactly before encoding. Final scene rendering took **8m35s**, prop rendering **22s**, compositing **3m53s**, and ambient encoding/decoding **21s**.

Files to review:

- [Manifest and integration contract](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out4/manifest.json>)
- [Before-and-after comparison](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa4/before_after.png>)
- [Prop animation preview](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa4/prop_preview.mp4>)
- [Reproduction, timings and validation notes](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS4.md>)

No requested assets are omitted. Interactive playback remains unverified: the browser host was unavailable, and automatic approval review rejected opening VLC because computer-use access to VLC was not approved. I inspected source frames, contact sheets and frames decoded from the actual videos.