Pass 8b is complete in **roxy3d/out8b/**: **443 files, 110.2 MB**, with the existing contracts preserved.

All seven changes are included: stepped distant roofs and haze, denser rain, wetter glass, broken road reflections, darker textured forecourt and roof, removal of 18 carpet outlines, and the new `lit_bg_dry` / `lit_bg_dry_2x` fallback.

Validation passed:

- **Occlusion: 0** at 1080p and 4K.
- **Aperture:** 186,624 logical green pixels at both scales.
- **Decoded video black: 0**; loop seams passed.
- All **2,182 files** in `out/` through `out8/` remain unchanged.

I inspected the final decoded composites and comparison renders. Live OBS/CEF playback was not tested.

[Final preview](/C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa8b/final_decoded_f072.png) · [Manifest](/C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out8b/manifest.json) · [NOTES-PASS8B.md](/C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS8B.md) · [Stage status](/C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa8/STATUS.md)