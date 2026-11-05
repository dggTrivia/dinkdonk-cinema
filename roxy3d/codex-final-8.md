Pass 8 is complete in **`roxy3d/out8/`**, including the brighter lighting from Brief 9b, both rain videos, wet reflections, glass water, entrance mat and threshold, wet footprint, and arcade play/HI-SCORE states. Interrupted outputs were checked and affected assets rebuilt.

- [Revised lighting preview](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa8/preview_surroundings_2.png)
- [Final decoded composite](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa8/final_decoded_f072.png)
- [Complete manifest](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out8/manifest.json)
- [Delivery notes](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS8.md) · [Timestamped status](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa8/STATUS.md)

Validation passed:

- **Occlusion: 0** at 1080p and 4K.
- **Green aperture:** 186,624 pixels at 1080p; 746,496 physical pixels at 4K—186,624 logical pixels at either scale.
- Exact loop endpoints, natural seams, and **decoded black level = 0** in the checked aperture and indoor regions.
- Glass atlases total **10.88 MiB across both resolutions**, below the 16 MiB limit.
- All **1,759 live files in `out/` through `out7/` remain unchanged**.

The pack contains 423 files. Encoding sizes, bitrates and measured Blender decode timings are in the notes; live OBS/CEF performance remains an integration check.