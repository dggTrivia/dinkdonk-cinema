# Brief 41 (PAGE): auditorium - pre-show on the screen, download progress, house-lights phases

Page work. You may edit `standby/auditorium.html`, `standby/control.html`, `standby/standby-server.js`. Same rules as
BRIEF-38/40 (read roxy.html conventions, no shared/*.js changes, test with `?everyone=1&relay=127.0.0.1:1` +
`SB.say`, server on 18770 stays up - say if Claude must restart it). Report `roxy3d/qa11/PAGE-41.md`, STATUS.

## What the scene is for (owner's decisions)
After a film is picked on dinkdonk.mov it downloads (qBittorrent); meanwhile the stream shows this auditorium. The big
screen shows a page-drawn PRE-SHOW while people take their seats; near the end of the download the house lights dim;
when the film is ready the screen turns into the OBS green aperture (`Cinema.green`, exact quad from
`L.screen.corners_1920x1080`) and OBS shows the film there (corner-pin shader) and then cuts to the full-screen film.

## 1. Download progress (standby-server.js)
`GET /qb/progress` -> qBittorrent Web API on `http://127.0.0.1:8080` (env `QB_URL` overrides; the owner will enable
the Web UI with "bypass authentication for localhost"). Return the most recently added torrent that is downloading
or just completed: `{ available: true, name, progress (0..1), eta_s, state, completed }`, or `{ available: false }` when
qBittorrent/the Web UI is not reachable or needs a login. Short timeout, small cache (~2 s). qBittorrent is NOT
running right now, so test the unavailable path for real and the available path with a tiny local fake.

## 2. Phases (page + control panel)
- `seating` (start): house lights up, pre-show on the screen.
- `dim`: automatically when progress >= 0.9 (or manual). The art darkens smoothly over ~6 s: CSS brightness on the
  background and all depth slices / door (e.g. ~0.45), emotes a little (~0.8), names and bubbles unchanged; the
  pre-show keeps running but dimmer is fine (it's "projected").
- `film`: automatically ~10 s after the download completes (or manual): the pre-show is replaced by the exact green
  quad for OBS; lights stay down.
- `up`: manual only (back to lights up + pre-show, e.g. after the film).
- `?phase=` forces a starting phase; `screen=green` keeps working as before (always green).
- control.html (auditorium section): show the phase and download progress; buttons Seating / Lights down / Film /
  Lights up, and "auto" on/off (manual press switches auto off until re-enabled).

## 3. The pre-show (drawn on the screen quad)
- Lay the slides out on a flat 16:9 element and map it onto the screen parallelogram with an affine CSS `matrix()`
  (the quad's sides are vertical, top/bottom slope 0.5), inside the camera so it zooms with the world. Nothing may
  draw outside the quad. It must look PROJECTED onto a matte screen in a dark 90s cinema, not like a web UI: soft,
  slightly warm/dim, vignetted, grain optional; big simple type.
- Slides, cycling (~7-9 s each, short cross-dissolve):
  - "DINK DONK presents" + "Tonight: <film title>" (+ its poster if available) - the film = the newest entry from
    dinkdonk data (`Cinema.data` / `Cinema.rooms`, see shared/cinema.js; read only).
  - Download: "Now loading the feature..." with a big percentage + bar and ETA when progress is available; when it is
    not, a calm "The feature will begin shortly" instead (no 0 %).
  - "Please silence your phones" / "No talking during the film" (90s policy-trailer style; a little DGG humour ok).
  - "Visit the snack bar" style slide.
  - "Tonight's audience": the nicks currently seated, as a slow credits roll (DGG flair colours from their walker).
  - "This row is reserved" for the wheelchair joke is optional, keep it tasteful.
- No external images/fonts beyond what the page already loads (posters from the dinkdonk data are fine).

Keep everything else as it is. STATUS line, stop.
