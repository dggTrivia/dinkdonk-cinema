# Brief 26 final cloud bundle — 2026-11-03T02:56:56+00:00

Rebuilt `cloud/bundle/` and `cloud/roxy-cloud-bundle.tar.gz` from the approved Draft 13 scene. Preserved the original scene and live packs. No local full render or production out10 was created. All 490 reused out9 input files are byte-identical to their sources.

The bundle includes the layout-3 contracts and approved art, Draft 10 physical wet/rain effects with hidden helpers preserved and sharp GN rain, Draft 11 lighting, Draft 12 restroom, Draft 13 dim chase/floods, and wet A/B bell circuits. Speed plan is fixed at Persistent Data + adaptive 256/64/.01, 48 unique frames, no dry/wet split.

`run.sh` retains preflight/smoke/full/validate-only, progress logging, `SUCCESS mode=` and future `bundle/out10.tar.gz`. EXIT handling writes DONE or FAILED. With pod-local runpodctl and RUNPOD_POD_ID, its detached watchdog requests a stop three hours after completion or eight hours after launch, whichever comes first. Mock shell tests passed; real cloud execution and pod stopping were not performed.

See `cloud/README-CLOUD.md` for launch, persistent storage, checkpoint/resume and copy-back instructions. The 720p smoke scene, sprite and difference evidence were visually inspected. Contract fixtures exercise PNG roundtrip/depth slices and both bus geometry states without additional 3D renders.

Archive: 151,707,587 bytes; 560 files, all read back and hash-verified. SHA-256: `2a86b89c08504317b86ff1af7f5bad25971299270e56d859f8d0b7beb463f3a6`.

## Fresh Draft 13 local results

| Scene-linear RGB comparison | Mean | p99 | Result |
|---|---:|---:|---|
| Two fixed-256 seeds | 0.0025560810 | 0.0377855667 | Reference |
| Persistent Data | 0.0000127173 | 0.0001516640 | Pass |
| Adaptive 256/64/.01 | 0.0002125752 | 0.0021987415 | Pass |

The six bounded Cycles captures total 276.57 seconds. Fixed-seed reference A: 69.99 s; adaptive comparison: 54.37 s. Single-frame thermal timing is not a cloud speed benchmark. No split comparison or production animation was rendered.

One-frame 720p VP9 decoding: 709,599 black probe pixels, maximum channel 0, nonzero pixels 0. Preflight: 39 foreground groups, eight door animations, phase 0/48 equality including evaluated GN rain, 0 holdout mismatches, seven restroom paths / 718 collision probes with zero fixture hits. The sprite/AOV and packaging fixture passed; the fixture's 2x scale is synthetic.

Approved source SHA-256: `8a03da7a47714e85e681e1211a29ec19de9ed072cde2ccd5309fd361e2d0c7c8`. Packaged scene SHA-256: `9e563c4c1f071488e396c21881e61204a33062405fbf44c61b76d986ffb2756e`. Linux startup, native 1080p/4K production frames, full rendered seams and live pod stopping remain unexecuted in this local rebuild.
