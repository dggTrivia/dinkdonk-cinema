**STATUS: COMPLETE — bundle sealed, STATUS line written, stopped.**

All four changes are implemented while retaining the out10 contract:

- Combined foreground capture with Cryptomatte and position masks. **6 groups passed; 33 retain isolated renders** because their colour or alpha differences exceeded the noise baseline. Every exception is quantified in the notes.
- **4K-only production rendering**, with linear 2×2 reduction to 1080p. The native-resolution crop comparison passed after matching the antialias filter footprint.
- Cached phase/visibility state and fewer material writes. Matched consecutive captures improved from **15.14 s to 6.04 s** on this laptop.
- Optional `ROXY_WET_FRAMES=24`, preserving the existing sheet layout and two-second/six-second timing. **Default remains 48.**

The local smoke passed, including video encode/decode, validation, cleanup, checksums, tar creation, and archive read-back. The seal verified **99 render receipts and all 572 archive members**.

Projected full-run GPU time and cost, using the default 48 frames:

| GPU | Estimated time | Estimated cost |
|---|---:|---:|
| RTX 5090 | 2.5 h — planning range 2.0–3.2 h | $2.96 — range $2.37–$3.85 |
| RTX 4090 | 3.4 h — planning range 2.7–4.4 h | $3.04 — range $2.44–$3.96 |

These are projections, not new cloud measurements. Verification covered bounded local samples, not a full animation.

- [ONE draft image — 1280×720](<C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/qa10/draft14-fast.png>)
- [Sealed cloud bundle](<C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/cloud/roxy-cloud-bundle.tar.gz>)
- [Measurements, fallback groups, and verification notes](<C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-FAST-PIPELINE.md>)

Bundle SHA-256: `0575e47602204102427e1ffce3b1e816c0b1ec0466356ca401ede47c6afaaf90`

No full local render or cloud pod was run. `roxy.html` and the approved source scene are unchanged; all writes stayed inside `roxy3d/`.