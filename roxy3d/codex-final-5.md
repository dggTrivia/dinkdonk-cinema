Completed pass 5 in **`roxy3d/out5/`**: **322 files, 69.1 MB**. All **681 files** in `out/`, `out2/`, `out3/` and `out4/` remain byte-for-byte unchanged.

- **Vehicle depth slices:** 28 sections, supplied as 56 PNGs at 1×/2×, covering every direction and closed/open-door variant. Each section is at most one tile long and includes its placement rectangle and signed `du`.
- **Brake and indicator lights:** 24 brake PNGs for all variants, plus 16 optional bus/taxi indicator PNGs. Dimensions and anchors match the existing lights.
- **Ginger lobby cat:** three-second sleep and sit loops, four 10-frame walking cycles with **0.32 tiles per cycle**, and the optional two-second stretch.
- **Tyre spray:** optional half-second additive sheets for both travel directions.

Validation passes: all vehicle bodies reconstruct exactly from their slices, all six cat loop endpoints match, and maximum calibration error is **0.0112 px**. The bus comparison verifies corrected sorting with 52px proxy walkers at opposite ends. Existing layout, footprints, signs and all 207 inherited assets are preserved.

Vehicle rendering took **7m07s**, cat rendering **4m33s**, and vehicle packaging **33s**.

Files to review:

- [Complete manifest](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/out5/manifest.json>)
- [Vehicle depth comparison](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa5/vehicle_depth_check.png>)
- [Cat and spray preview](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa5/cat_preview.mp4>)
- [Integration instructions, reproduction and validation notes](</C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-PASS5.md>)

No requested assets are omitted. The pack is ready for the page agent to integrate.