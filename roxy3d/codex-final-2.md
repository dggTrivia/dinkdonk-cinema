Completed in `roxy3d/out2/`. The layout-2 still manifest was published **before** starting the loops. All **139 live `out/` files remain byte-for-byte unchanged**.

- [Full preview](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out2/full.png) — wall-backed counters, 90px partitions, moved furniture, palm, and worn materials.
- [Final manifest](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out2/manifest.json) — `"layout": 2`, base/loop fields, staff positions, and measured decorative overhangs.
- [Light loop](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out2/light_loop.webm) — **1920×1080 VP9, 24 fps, 5 seconds, 2.80 MB**.
- [Reproduction notes](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS2.md) — scripts, timings, compositing instructions, and QA results.

The package includes minimum-light `base.png`, matching sprites, and fully lit `full.png`, with 4K `@2x` versions. There are **18 occluders and 49 depth slices** at both resolutions. The loop adds rain, splashes, rippling reflections, neon variation, projector flicker, billboard chase lights, and a restrained headlight sweep.

Validation passed:

- Camera calibration: **0.016px maximum error**.
- Depth slices reconstruct every parent sprite exactly.
- The source frame at 5 seconds matches frame 0 exactly; the encoded seam also passed.
- Decoded WebM frames were checked numerically and visually.
- All requested sorting footprints match the brief.

Baked signs include TICKETS, snack menus, gate directions, RESTROOM, ROXY, BUS 95, ORBIT, POPCORN, and standee titles. Movie-title and poster apertures remain blank. Foreground prop lights stay static so they work correctly above the additive video.

Use **base → loop with `plus-lighter` → z-sorted walkers and sprites**. The complete delivery inventory and checks are in [final_delivery.json](C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa2/final_delivery.json).