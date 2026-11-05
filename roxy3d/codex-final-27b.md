**STATUS: COMPLETE — resealed, STATUS line appended, stopped.**

- `ROXY_WET_FRAMES` unset now selects **24 unique wet/foreground frames**. `ROXY_WET_FRAMES=48` retains the override.
- Light and rain remain at **48 unique frames**. The existing sheet layout and 2 s / 6 s timing are preserved.
- Updated code expectations, production notes, and [NOTES-FAST-PIPELINE.md](<C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/NOTES-FAST-PIPELINE.md>), with 24 listed as the default projection rows.
- Re-ran the affected no-render scheduling and cadence checks; all passed. The reseal verified all **572 archive members**.

[Resealed cloud bundle](<C:/Users/maxsp/Desktop/Angelthump_H264_4K/standby/roxy3d/cloud/roxy-cloud-bundle.tar.gz>)

SHA-256: `f5b4d7b13a904218bae2b8bbef97f17783d16177ad731008b36f35841cc97c55`

No new draft, 3D render, full render, or cloud pod was created. The existing draft and `roxy.html` are unchanged; all writes stayed inside `roxy3d/`.