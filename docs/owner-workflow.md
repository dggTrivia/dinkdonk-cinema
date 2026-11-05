# How the owner uses DinkDonk Cinema

The streamer runs the screens on their own Windows PC, in OBS. This page describes that setup and the day-to-day
workflow, including how the AI agents are used. For code details see the other docs in this folder.

## The streaming setup

| Piece | What it is |
|---|---|
| OBS profile | "Angelthump h264 1440p" (1440p canvas) |
| OBS scene collection | "Moobies 1440p poll": a **copy** of the original "Moobies 1440p", which is never edited |
| Lobby scene | a browser source with `lobby.html` (nested as "Lobby (src)"), plus "Lobby + Poll setup" (lobby next to the dinkdonk.mov poll builder) |
| Cinema scene | "DinkDonk Cinema": a browser source with `auditorium.html`, plus "Film screen (src)", a VLC capture of the movie |
| Film on the screen | `obs-bridge.js` takes the screen corners from the auditorium page and moves the VLC capture onto them with the "Corner pin (live)" filter. It needs the obs-shaderfilter plugin. |
| Chat | a local Destiny.gg relay (the DSA OBS overlay) on port 18765, kept outside this repo |
| Control | `control.html` in a normal browser: pick the scene, run the director, send commands |

`start-all.bat` starts everything, and anything already running is left alone:

1. the chat relay (port 18765)
2. the standby server, `start-standby.bat` (port 18770)
3. the OBS bridge, `start-obs-bridge.bat` (port 18790)
4. OBS with the right profile and collection

It then opens the control panel. VLC (the movie) is opened by hand.

### Browser source URLs

| Source | URL | Notes |
|---|---|---|
| Lobby, 16:9 | `http://127.0.0.1:18770/lobby.html` | the default |
| Lobby, squarer | `…/lobby.html?fit=cover` | fills a squarer source (for example about 2028x1440) by cropping the sides instead of showing black bars. `fitx=<x>` sets where the wide shot is centred. |
| Auditorium | `http://127.0.0.1:18770/auditorium.html` | |

Old URLs with `roxy.html` still work; they redirect to `lobby.html` and keep their options. All URL options are
listed in [lobby.md](lobby.md) and [auditorium.md](auditorium.md).

Keep "hardware acceleration" on for browser sources in OBS. The lobby uses WebGL and video loops.

### Who shows up

By default only chatters who tag the streamer's DGG name walk in. `everyone=1` lets all chatters in. When the owner
is shown a scene (a screenshot or a link), it is always with `everyone=1` and real chat, never the scripted
`demo=1`.

## A movie night

1. Run `start-all.bat`. Check that OBS has loaded the "Moobies 1440p poll" collection.
2. While waiting, show the lobby. Chatters walk in from the street, queue at the box office and snack bar, and talk
   in speech bubbles. The dinkdonk.mov poll goes next to the lobby ("Lobby + Poll setup"); the lobby has no green
   screen of its own.
3. Switch to the cinema scene. In the control panel pick **Auditorium** and check that the director is on.
4. The auditorium runs its phases: people take their seats, the lights go down, the film shows on the big screen,
   and the lights come back up. The OBS bridge shows the VLC film on the screen only during the film phase.

## Working with AI agents

The owner builds this with Claude Code and the Codex CLI:

- **One session per area.** A lobby session owns `lobby.html`; a cinema session owns the auditorium; a QA session
  works only on the `-qa` copies; a packaging session owns `package/` and `web/`. Lobby problems found elsewhere are
  passed to the lobby session instead of being fixed on the side.
- **Art is rendered by Codex** from numbered briefs in `roxy3d/`. Claude writes the brief, Codex renders, and
  Claude puts the result into the page and checks it.
- **Drafts:**
  - A draft is one 1280x720 image. The owner gives feedback; nothing else is rendered until then.
  - Layout changes start as a plain-box blockout.
  - Each draft gets a read-only Codex critique before the next brief.
  - Full renders (the final art pack) happen only when the owner says "final render". Big renders go to a rented
    cloud GPU (RunPod) within a set credit.
- **Overnight goals.** The owner sometimes leaves a goal, such as "keep improving the auditorium until it's good
  or weekly usage reaches N %". Agents then work alone, log everything in `roxy3d/PROGRESS.md`, and send nothing
  until morning.
- **Queued requests** that shouldn't start yet go in `roxy3d/QUEUE-owner.md`.
- **Style.** Short answers, one question at a time with options, and results shown before moving on.

## Sharing it with others

- **Zip package.** `node package/build.js` builds `../dist/DinkDonk-Cinema/` and a zip with the two scenes, only
  the art they load, the server, the OBS bridge, the chat relay and ready-made OBS scene collections. Rebuild it
  after changes; don't edit the package by hand.
- **Hosted edition** (`web/`, in progress). The same pages served from a web server with per-streamer room keys,
  so other streamers need only OBS.
- **This repo.** For collaborators. Large render folders stay on the owner's PC (see [README.md](../README.md)).
