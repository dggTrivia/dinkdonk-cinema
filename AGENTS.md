# Instructions for AI coding agents

This file is for any AI agent working in this repo (Claude Code, Codex, Cursor, Copilot, …). `CLAUDE.md` points
here. Read this file first, then the doc in `docs/` for the area you're touching.

## What this is

DinkDonk Cinema is a set of browser pages that run as **OBS browser sources** while the streamer waits for (and
runs) a DinkDonk movie night. People in Destiny.gg (DGG) chat become small walkers wearing their emote.

| Scene | File | Art |
|---|---|---|
| Lobby (main screen): a pre-rendered isometric late-90s cinema on a rainy night | `lobby.html` | `roxy3d/out10/`, `roxy3d/out10mist/` |
| Auditorium: seats, lights down and up, the film pinned onto the big screen | `auditorium.html` | `roxy3d/qa11/` (draft 13) |

`roxy.html` and `roxy-qa.html` are **redirect stubs** left over from the old name. Never edit them, and never put
code in them. The `roxy3d/` folder keeps its old name on purpose: briefs, scripts and paths depend on it.

Docs: [docs/README.md](docs/README.md) (index), [docs/owner-workflow.md](docs/owner-workflow.md) (how the owner
uses it), [docs/lobby.md](docs/lobby.md), [docs/auditorium.md](docs/auditorium.md),
[docs/server-and-shared.md](docs/server-and-shared.md), [docs/art-pipeline.md](docs/art-pipeline.md).

## Run and check

```bash
node standby-server.js            # serves this folder on http://127.0.0.1:18770 (start-all.bat starts everything)
```

- Lobby: `http://127.0.0.1:18770/lobby.html?everyone=1`
- Auditorium: `http://127.0.0.1:18770/auditorium.html?everyone=1`
- Control panel: `http://127.0.0.1:18770/control.html`

Chat comes from a local DGG relay on `ws://127.0.0.1:18765`, which is not part of this repo. If the relay is
offline, say so. Don't switch to fake chat instead.

There is no build step and no test suite. To check a change, load the page with `?everyone=1`, wait for real chat
to fill it, and look at it (screenshot) and at the browser console (it should show no errors).

## Hard rules

1. **Live vs QA copies.** `lobby.html` and `auditorium.html` are what OBS shows on stream. Try risky or
   experimental work in `lobby-qa.html` or `auditorium-qa.html` first. Back up a live file before replacing it.
2. **Real chat only.** Show and test scenes with `?everyone=1`. Never use `?demo=1` (scripted fake chatters) or
   synthetic chat floods. That applies to screenshots, QA and performance runs.
3. **Keep the full render resolution.** The 1920x1080 layout, the 2x art and the canvases sized to
   devicePixelRatio × zoom are there so director zoom-ins stay sharp. A performance fix must not lower them.
4. **Don't stop the server on port 18770** while the owner may be streaming. To test a package build, use another
   port (`STANDBY_PORT=18771`) and stop it afterwards.
5. **OBS.** The live scene collection is the owner's. Edit only a copy of its JSON (under
   `%APPDATA%\obs-studio\basic\scenes`), and only while OBS has a different collection loaded, because OBS
   overwrites the file it has loaded.
6. **Art workflow** (details in [docs/art-pipeline.md](docs/art-pipeline.md)):
   - A draft is **one** final-quality still from the fixed camera (lobby 1280x720 with the weather frame;
     auditorium 1920x1080). No close-ups,
     clips, extra audits or comparisons unless the owner asks.
   - Layout changes start as a quick labelled **blockout** (plain boxes). Styled drafts come only after the owner
     approves the layout.
   - Before writing the next brief, get a read-only second-opinion critique of the latest draft (for example with
     Codex) and say which points you took.
   - Run **full renders** only when the owner says so. Stage new packs in a separate folder (such as `out10i/`),
     verify them, back up the current pack, then promote.
   - Never redo something the owner already approved.
7. **Cloud GPU (RunPod)** costs real money. Use it only when the owner asks. Stay inside the credit the owner names,
   delete pods and volumes afterwards, and never put API keys in files.
8. **Files are byte-exact.** Art packs carry SHA-256 manifests, and `.gitattributes` turns off line-ending
   conversion. Don't re-save, re-encode or reformat art or manifests by hand.
9. **This repo is public.** No passwords, tokens, API keys, stream keys, OBS websocket passwords, account IDs or
   billing details, in code or in docs.
10. **Git.** Commit and push only when the owner asks. Auditorium art in `roxy3d/qa11/` is ignored as a folder;
    add exactly the files the page loads with the recipe in [README.md](README.md). Draft, QA and old pack folders
    stay local.

## How the owner likes to work

- Short, concrete answers in American English. Dates look like "5 Nov 2026".
- When a decision is needed, ask **one** question at a time and give options. Put the recommended option first.
- Show results (a screenshot or one draft image) before moving on to the next thing.
- If you don't know a DGG meme, an emote, or what dinkdonk.mov is, search the web. Don't guess.
- Log what you changed, and why, in `roxy3d/PROGRESS.md` (newest at the bottom, with the date). Queued owner
  requests live in `roxy3d/QUEUE-owner.md`.
- Several agents may work at once: one on the lobby, one on the auditorium, one on QA, one on packaging and
  hosting. Stay inside the area you were asked to work on. Before editing a shared file (`shared/*.js`,
  `control.html`, `standby-server.js`), check whether someone else is changing it.

## Working with Codex for art

Renders are made by the Codex CLI from numbered briefs (`roxy3d/BRIEF-NN-*.md`). Codex writes only inside
`roxy3d/` and reports in `roxy3d/NOTES-NN.md`. Typical call, run in the background from `roxy3d/`:

```bash
codex exec -s workspace-write --skip-git-repo-check -o codex-NN.md "Read BRIEF-NN-....md and do it." < /dev/null
```

A brief states what to change, what must stay the same, the exact deliverable (for example the single draft
image) and "write only inside roxy3d/". It ends with a STATUS line.

## Map

| Path | What |
|---|---|
| `lobby.html`, `auditorium.html` | live scenes |
| `lobby-qa.html`, `auditorium-qa.html`, `control-qa.html` | QA copies |
| `control.html` | control panel (scene, director, commands) |
| `shared/` | `core.js` (SB: stage, chat, emotes, chat tokens), `cinema.js` (walkers), `live.js`, `emote-facing.json` |
| `standby-server.js` | local server (static files, video byte ranges, control events, DGG/dinkdonk data) |
| `obs-bridge.js` | pins the film capture onto the auditorium screen through obs-websocket |
| `dinkdonk.js` | dinkdonk.mov film data |
| `lan-proxy.js` | optional view-only proxy for phones and tablets |
| `package/` | builds the shareable zip; `package/art.js` lists the art the pages load |
| `web/` | hosted edition (in progress) |
| `roxy3d/` | art: briefs, notes, Blender scripts and `.blend` files, packs, cloud render helper |
| `intro-dinkdonk/` | the DINK DONK intro video |
| `hall-*.html`, `cinema-*.html`, `0*-*.html`, `concepts/` | earlier concepts (not live) |
