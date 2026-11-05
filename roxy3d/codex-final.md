Completed the scene and exports entirely inside `roxy3d/`. Existing page files were left untouched.

- **Final renders:** [1080p preview](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out/full.png) · [4K preview](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out/full@2x.png)
- **Assets:** background, optional glow, 17 cropped RGBA prop sprites, and 49 additional pieces for correct depth sorting—all at both resolutions.
- **Integration:** [manifest.json](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out/manifest.json)
- **Source and instructions:** [Blender scene](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/roxy.blend) · [NOTES.md](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES.md)

Rendered with **Cycles OptiX, 96 samples and denoising**. I inspected successive previews, the assembled layers, transparency edges, and 4K details. Calibration’s maximum measured error is **0.016 pixels**. The depth pieces reconstruct their parent sprites with **zero pixel error**.

Baked signs include **TICKETS, SNACK BAR and prices, the gate directions, RESTROOM, and ROXY**, plus smaller prop labels. Film marquees and poster apertures remain blank for DOM content; restroom occupancy remains dynamic.

No prop footprint or visible walkable area moved. Off-screen paving extends from `u −9..19` to `−12..23`. Small height increases for the bench, podium lamp, and bus-stop plaque are documented. Minor glass-blending and denoising differences from the independent Cycles render are measured in the notes. HTML/OBS integration remains with the integrating agent, as specified.

Automatic approval review blocked optional decoder-cache cleanup with “blocked by policy.” The generated cache remains in `roxy3d/cache/png`; all deliverables are complete.