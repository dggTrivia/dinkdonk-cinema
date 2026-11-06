# Local Windows launch

Double-click `START-CINEMA.bat` here, or `cinema_dgg_lobby.bat` in the parent MovieStream folder.
The brief batch window closes; the cinema server and read-only public DGG chat relay run hidden.
The control panel opens in the Windows default browser (Chrome if Chrome is the default), normally as a new tab.
Clicking again reuses the running services and opens the panel again. Port conflicts with another application
produce an error instead of stopping it. This launcher does not start OBS or change its scene collection.

- Control: http://127.0.0.1:18770/control.html
- OBS single source: http://127.0.0.1:18770/cinema.html?everyone=1
- Legacy OBS lobby: http://127.0.0.1:18770/lobby.html?everyone=1
- Legacy OBS auditorium: http://127.0.0.1:18770/auditorium.html?everyone=1
- Browser source size: 1920 x 1080, then Transform > Fit to Screen.
- Relay health: http://127.0.0.1:18765/healthz (`connected: true` means live DGG connection).

Requires Node 22+ and Python with aiohttp (`py -m pip install aiohttp` if missing).
Logs are under `%LOCALAPPDATA%\DinkDonkCinema`, outside this public repository.
The relay reconnects automatically, forwards real public chat without storing message text, and never posts to DGG.
No fake chat is generated. Both local services bind only to 127.0.0.1.

The film capture/OBS corner-pin bridge is a separate setup step; this launcher starts the scenes and chat only.
The original `start-all.bat` retains the upstream creator's paths/profile assumptions; use START-CINEMA instead.

Use the host panel's Show lobby / Show auditorium buttons to change the one cinema source. The Controls for selector only changes which room receives camera/lighting commands. Both rooms stay loaded and receive live chat; switching only changes which one is visible. Selected view persists across server restarts. Both rooms keep their audience, camera, animation and lighting state while hidden.

With the combined source, regular chatters first join a paced lobby queue (one arrival every 1.4-2.2 seconds,
pausing when the entrance is crowded). Repeated messages update the same person instead of adding duplicates.
After walking through the first auditorium door, that same nickname, avatar and carried snack transfer to the
theater's existing entrance/seat queue. Both rooms continue this journey while hidden. The host roster shows
people waiting to arrive. Standalone room URLs keep their original independent behavior.

Arrival pacing now adapts to the number waiting: 1-5 use 1.4-2.2 seconds; 6-11 use 0.9-1.4 seconds;
12-39 arrive in pairs; 40+ arrive in groups of three. Group members are 0.25-0.45 seconds apart,
with 0.9-1.4 seconds between groups. Every admission still checks crowding and capacity; no catch-up floods.
The pacing slows automatically as the queue clears. These thresholds count pending lobby guests.

Firefox and mpv.net: one bridge, OBS source selection

Run start-obs-bridge.bat once. start-firefox-bridge.bat and start-mpv-bridge.bat are compatibility shortcuts
for the same unified bridge; do not run two copies. It recognizes firefoxBrowserCinema and mpvCinema in
scene dggCINEMAtheatre. Each can be a direct Window/Game Capture or a helper scene containing a capture.

Use the OBS eye icon to enable the source you want. Enabling either selects it and automatically hides the
other. Hiding the selected source leaves the screen empty. Both shaders follow the theater camera.
Show auditorium + Film / Movie (no zoom) displays the selected capture. Show lobby or leaving movie mode
makes capture output transparent through the shader; the selected OBS eye remains enabled. You can select
Firefox/mpv in any mode without the eye being forced back off. Return to movie mode to see the selected source.

Sizing uses the OBS base canvas. Direct captures stretch to fill the screen; helper scenes preserve capture
aspect ratio inside a full-canvas wrapper. Window resizing or moving between monitors no longer requires
manual refitting. The bridge configures both available sources on startup/reconnect, and recognizes a newly
added source. Restart it after changing canvas resolution. Keep the cinema Browser Source fitted to canvas.
Audio is separate: check the mixer and avoid capturing the player twice through desktop and app audio.

Lobby eye gating (current behavior): Show lobby turns both capture source eyes off and remembers selection.
Returning to the auditorium restores the selected eye even in seating/dim mode. Film/Movie phase still
controls visible pixels through Cinema_Visible. Thus eye controls work in auditorium mode, and lobby
automatically disables both. Bridge polls the local /ctl/state every 500 ms to distinguish view from phase;
CINEMA_CONTROL_URL can override its endpoint. Unavailable control state or no scene page hides both.

cinema_dgg_lobby.bat now also starts/reuses the unified movie bridge hidden on 18790.
All three service ports are checked before startup; unrelated listeners cause an error rather than being stopped.
OBS remains manual. Bridge can start before OBS and reconnect when OBS opens. Logs: bridge.log/bridge-error.log
under LOCALAPPDATA/DinkDonkCinema. Repeated launches reuse services and open the host panel again.

Bridge console: cinema_dgg_lobby.bat opens a visible bridge window so it can be closed when finished.
Only the server and chat relay run hidden. An existing bridge is reused; reopening the launcher after
closing its bridge window starts a fresh visible one. Bridge diagnostics appear in its console.

Seated POV: choose Show auditorium, then POV view in Auditorium pre-show. Select mpvCinema or firefoxBrowserCinema with its OBS eye as usual. The bridge automatically uses the F10 screen corners. Movie (no zoom) or Wide returns to the open auditorium. Both views show the same live audience. The seated POV projects the audience into the F10 camera and hides sprites behind seat backs and other room geometry. Refresh the host page and OBS Browser Source once to load the updated pages.
