# Unified OBS cinema output, connected arrivals, and optional seated POV

Adds a single OBS cinema browser output with persistent lobby/auditorium switching, a connected guest journey, expanded capture controls, and an optional seated camera view.

## Changes from the original repository

1. **Single OBS browser output.** Added `cinema.html` and host-panel Show lobby / Show auditorium buttons. Both rooms remain loaded and continue running, preserving audience, camera, animation, and lighting state across switches. The selected view persists across server restarts.

2. **Connected guest journey.** In the combined output, lobby door completion hands the same nickname, avatar, and carried snack into the auditorium entrance/seat queue. Repeated messages update existing guests instead of admitting duplicate guests into both rooms. Standalone room URLs retain independent admission.

3. **Dynamic lobby arrivals.** Added a deduplicated arrival queue. Small queues use 1.4–2.2-second spacing. Larger backlogs use faster spacing and bursts of two or three, with pauses between groups. Admission still respects crowding and capacity, and slows down as the queue clears.

4. **Extended OBS bridge.** One bridge handles both Firefox and mpv captures, selected through OBS eye icons. Enabling one disables the other. Show lobby switches both capture eyes off, and returning to the auditorium restores the selected source. A shader visibility control gates the picture separately according to Movie/Film mode. Automatic sizing uses the OBS base canvas as capture dimensions change. Direct captures stretch to fit, while helper scenes can preserve capture aspect ratio.

5. **Windows startup.** Added `cinema_dgg_lobby.bat` and its launcher chain to start or reuse the cinema server, read-only DGG relay, and unified bridge, then open the host panel in the default browser. Server/relay run hidden and the bridge opens a visible console. Startup checks port ownership and rejects conflicts. Firefox/mpv batch shortcuts now launch the same unified bridge. OBS is started manually.

6. **Isolated Blender editing workspace.** Added preparation/packing helpers and workspace notes. Prepared self-contained working copies of the current lobby, auditorium, and dim auditorium after a hash-verified backup, and checked their dependencies. The working `.blend` files and backups are local and excluded by existing ignore rules. The historical render/export chain still needs external inputs before it is portable.

7. **Optional seated POV.** Added an F10 seated view with a ceiling and right/rear enclosure, a host-panel POV button, image plates, camera/depth data, and seat-back anchors. The existing live audience is projected into this view with seat/room occlusion, distance scaling, and screen-clearance fading. The OBS bridge uses the matching POV screen corners. Switching back preserves the auditorium instance and audience.

8. **Verification and documentation.** Added startup and workspace documentation, progress notes, and automated coverage for guest handoffs, arrival pacing, capture sizing, and capture selection/visibility. Changes were staged in QA copies and checked with real DGG chat and live OBS.

## Required OBS setup

The current bridge uses these exact names. Other setups must use matching names or change the constants in `obs-bridge.js`.

| OBS object | Required name | Purpose |
| --- | --- | --- |
| Main scene | `dggCINEMAtheatre` | Contains the cinema Browser Source and screen captures |
| Firefox capture | `firefoxBrowserCinema` | Firefox Window Capture, or a helper scene containing it |
| mpv capture | `mpvCinema` | mpv.net Game/Window Capture, or a helper scene containing it |
| Capture filter | `Corner pin (live)` | Created/configured by the bridge using `cinema-screen.shader` |

At least one recognized capture is needed for the bridge. Place captures above the cinema Browser Source. The Browser Source's name is arbitrary. Its URL is `http://127.0.0.1:18770/cinema.html?everyone=1`, and it should fill the OBS canvas. Leave shutdown-when-hidden and refresh-on-activation unchecked to preserve audience state.

OBS WebSocket must be enabled on port **4455**, and **obs-shaderfilter** must be installed. Local service defaults are **18765** for DGG chat, **18770** for the cinema server, and **18790** for the unified bridge. Keep one bridge running and choose captures with OBS eye icons while controlling the room and movie phase from the host panel.

## Validation and remaining work

- All **18 automated tests** passed with `node --test tests/*.test.js`.
- Real-chat checks verified door handoffs, continued background activity, and persistent room instances across view changes.
- Live OBS checks verified Firefox/mpv selection, lobby eye-off behavior, restoration on return, shader visibility, and capture bounding boxes.
- POV remains experimental. Flat emotes still look awkward in seated perspective, and carried items/details need further work in that view.
- Local Blender working files require separate sharing. Scene/source names and launcher assumptions currently reflect the local Windows setup.
- Package file lists were updated for the bridge modules and shader. A complete rebuilt distribution has not been validated as part of these checks.
