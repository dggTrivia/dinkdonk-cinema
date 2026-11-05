# DinkDonk Cinema

OBS standby screens for DinkDonk movie nights: a rainy late-90s isometric cinema where Destiny.gg chatters walk
into the **lobby** (`lobby.html`) and take their seats in the **auditorium** (`auditorium.html`).

- **Docs:** [docs/](docs/README.md)
- **AI agents:** read [AGENTS.md](AGENTS.md) first
- **How the owner uses it:** [docs/owner-workflow.md](docs/owner-workflow.md)

## Run it

Needs Node 22+ (the OBS bridge uses its built-in WebSocket). Start `start-all.bat` (or `node standby-server.js`), then open:

- http://127.0.0.1:18770/lobby.html?everyone=1 - the lobby (`roxy.html` still works and redirects here)
- http://127.0.0.1:18770/auditorium.html?everyone=1 - the auditorium
- http://127.0.0.1:18770/control.html - the control panel

URL options are listed in the comment block at the top of each page and in `README.txt`.

## What's where

| Path | What |
|---|---|
| `lobby.html`, `auditorium.html`, `control.html` | the live pages (`*-qa.html` = QA copies) |
| `shared/` | code shared by the pages (stage, chat, emotes, cinema logic) |
| `standby-server.js`, `obs-bridge.js`, `dinkdonk.js` | local server, OBS film-screen bridge, dinkdonk.mov data |
| `package/` | builds the shareable zip package; `package/art.js` lists the art the pages load |
| `web/` | hosted edition (work in progress) |
| `roxy3d/` | the Blender art: briefs (`BRIEF-*.md`), notes (`NOTES-*.md`), render scripts, source `.blend` files |
| `roxy3d/out10/`, `roxy3d/out10mist/` | the live lobby art pack |
| `roxy3d/qa11/` | auditorium art: only the files `auditorium.html` loads are tracked |
| `roxy3d/cloud/` | the RunPod render helper (`cloud-render.sh`) and the Brief 57 production bundle |
| `intro-dinkdonk/` | the DINK DONK intro snipe |
| `concepts/`, `hall-*`, `cinema-*` | earlier design concepts |

Not in the repo (about 30 GB, local only): draft/QA renders, old art packs, render caches, backups, Blender itself
(`tools/`, Blender 5.2.3) and the cloud upload archives. Renders are made with Blender 5.2.3; see `roxy3d/NOTES-*.md`.

`.gitattributes` turns off line-ending conversion: the art packs carry SHA-256 manifests, so files must stay
byte-identical.

### Adding auditorium art

`roxy3d/qa11/` is ignored as a folder. After a new auditorium draft, add exactly the files the page loads:

```bash
node -e "const {artFiles}=require('./package/art');console.log(artFiles('.',m=>{throw m}).files.filter(f=>f.startsWith('roxy3d/qa11')).join('\n'))" > qa11-files.txt
git add -f --pathspec-from-file=qa11-files.txt && rm qa11-files.txt
```
