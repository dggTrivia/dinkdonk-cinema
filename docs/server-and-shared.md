# Server, bridge and shared code

Everything the scenes need that isn't the scenes themselves: the local server, the OBS film bridge, the
dinkdonk.mov reader, the LAN proxy, the control panel, and the shared scripts in `shared/`. Line numbers are from
the 5 Nov 2026 versions; function names are the stable way to find things.

| File | What |
|---|---|
| `standby-server.js` | local HTTP server: static files, video byte ranges, control events, DGG emote relay, dinkdonk.mov feed, qBittorrent progress |
| `dinkdonk.js` | reads dinkdonk.mov's public pages into one JSON feed (module used by the server) |
| `obs-bridge.js` | pins the film capture onto the auditorium screen through obs-websocket |
| `lan-proxy.js` | optional proxy so phones/tablets on the LAN can watch the scenes |
| `control.html` | control panel (`control-qa.html` is its QA copy) |
| `start-all.bat`, `start-standby.bat`, `start-obs-bridge.bat` | Windows start-up |
| `shared/core.js` | `window.SB`: stage, chat, emotes, flair colors, tokens, stats, commands |
| `shared/cinema.js` | `window.Cinema`: who walks in, which emote, the dinkdonk.mov "rooms" |
| `shared/live.js` | `?live=1` auto-reload |
| `shared/base.css` | base page, emote and chat-panel styles |
| `shared/emote-facing.json` | which way each emote looks |

## Start everything

Needs Node.js. `standby-server.js` and `lan-proxy.js` run on Node 18+. `obs-bridge.js` uses Node's built-in
`WebSocket` client, which is only available by default from Node 22 (see "Looked wrong").

| How | What it does |
|---|---|
| `start-all.bat` | Starts what isn't already running (checks `netstat` for a listening port, `tasklist` for OBS), each in its own window: the chat relay on 18765 (`start-windows.bat` in the DSA overlay folder under `%USERPROFILE%\Desktop\customchat\`, not part of this repo), the standby server on 18770, the OBS bridge on 18790, and OBS with the owner's profile and scene collection. After 3 s it opens `http://127.0.0.1:18770/control.html`. VLC (the film) is opened by hand. Safe to run twice. |
| `start-standby.bat` | `node standby-server.js` in this folder |
| `start-obs-bridge.bat` | `node obs-bridge.js` in this folder |
| `node lan-proxy.js [lanAddress] [port] [--control]` | only for phones/tablets; not needed for OBS |

Then open:

- `http://127.0.0.1:18770/lobby.html?everyone=1`
- `http://127.0.0.1:18770/auditorium.html?everyone=1`
- `http://127.0.0.1:18770/control.html`

Don't stop the server on 18770 while the owner may be streaming. For tests, run a second one with
`STANDBY_PORT=18771`.

## Ports and environment variables

| Port | Process | Bound to | Set with |
|---|---|---|---|
| 18765 | DSA OBS overlay chat relay (outside this repo) | 127.0.0.1 | pages: `relay=<host:port>`; `lan-proxy.js`: `DGG_OBS_PORT` |
| 18770 | `standby-server.js` | 127.0.0.1 only | `STANDBY_PORT` (also read by `lan-proxy.js`) |
| 18780 | `lan-proxy.js` | the PC's private LAN IPv4 | 2nd command-line argument |
| 18790 | `obs-bridge.js` | 0.0.0.0, but WebSocket upgrades only from this PC's own addresses | `OBS_BRIDGE_PORT`; pages: `bridge=<host:port>` |
| 4455 | OBS obs-websocket v5 | OBS setting | `OBS_WS` (default `ws://127.0.0.1:4455`) |
| 8080 | qBittorrent Web UI | qBittorrent setting | `QB_URL` (default `http://127.0.0.1:8080`) |

| Variable | Used by | Meaning |
|---|---|---|
| `STANDBY_PORT` | server, LAN proxy | server port (default 18770) |
| `QB_URL` | server | qBittorrent Web UI base URL |
| `OBS_BRIDGE_PORT` | bridge | bridge port (default 18790) |
| `OBS_WS` | bridge | obs-websocket URL |
| `OBS_PASSWORD` | bridge | overrides the password read from OBS's config (never commit it anywhere) |
| `APPDATA` | bridge | where OBS's config lives (Windows sets it) |
| `DGG_OBS_PORT` | LAN proxy | chat relay port (default 18765) |

## Where chat comes from

Chat is **not** read from destiny.gg by this repo. The pages connect to the DSA OBS overlay relay, a separate
local program, at `ws://<relay>/__dgg_chat_ws` (default relay `127.0.0.1:18765`; `connect()`, `shared/core.js`
line 442). Frames are DGG chat protocol lines: `TYPE {json}` (`MSG`, `NAMES`, `JOIN`, `QUIT`, `MUTE`, `BAN`,
`BROADCAST`, `SUBSCRIPTION`, `GIFTSUB`, `MASSGIFT`, `DONATION`; `handleFrame()`, line 409).

If the relay is offline:

- `SB.status` becomes `offline` and the page keeps retrying with backoff (1, 2, 4 … up to 30 s).
- A relay that stays connected but sends nothing for 3 minutes is dropped and reconnected.
- Nobody walks in; the scenes just stay empty. Pages that mount the DSA chat panel (`SB.mountChat`, older drafts)
  show "Chat relay offline". The lobby and auditorium have no chat panel.
- Project rule: say the relay is offline. Don't switch to `demo=1` fake chat.

`SB.start()` loads emotes, flairs and facing data first (each bounded by 8 s timeouts) and only then connects chat.

## `standby-server.js` routes

Listens on `127.0.0.1:STANDBY_PORT` (line 275). Every response has `Cache-Control: no-store` except video
(`no-cache`). An exception in a route answers `502` with the error message.

| Method | Path | Purpose | Code |
|---|---|---|---|
| GET | `/ctl/events?page=lobby\|auditorium&id=<id>` | server-sent events: control commands for that screen. Starts with `retry: 3000`, a `: ping` comment every 20 s. Any `page` other than `auditorium` counts as `lobby`. | `controlRoute()` line 169 |
| POST | `/ctl/cmd` | a command from the panel, relayed to matching screens. Answers `{ "screens": <count> }`; 400 without `cmd` or with an unknown `page`. | line 178 |
| POST | `/ctl/state` | a screen reports its state (max 256 KB, `id` cut to 16 chars). 204. Entries older than 10 s are dropped. | line 193 |
| GET | `/ctl/state` | `{ controlVersion: 2, screens: [state, …] }` for the panel; screens without `page` count as `lobby` | line 201 |
| GET | `/qb/progress` | the current download from qBittorrent, see below | `qbProgress()` line 87 |
| GET | `/dgg/emotes.json` | DGG emote list, relayed from `cdn.destiny.gg` (which only lets www.destiny.gg read it) | `cdnAsset()` line 35 |
| GET | `/dgg/emotes.css` | DGG emote stylesheet, with relative image URLs rewritten to absolute `cdn.destiny.gg/emotes/…` | `cdnAsset()` |
| GET | `/dgg/flairs.json` | DGG flair list (name colours) | `cdnAsset()` |
| GET | `/dgg/emote-img?u=<url>` | one emote image, same-origin, so a page can read its pixels (`cinema.js` spots square "picture" emotes). Only URLs matching `https://cdn.destiny.gg/<version>/emotes/<name>.(png\|gif\|webp\|avif)`, else 400. Kept in memory once fetched. | `emoteImage()` line 63 |
| GET | `/dd/data.json` | the dinkdonk.mov feed (`dinkdonk.data()`) | line 237 |
| GET | `/dd/search?q=<title>` | watch-log search for `!watched` (2-60 chars, else 400) | line 241 |
| GET, HEAD | `/` | `index.html` (the gallery) | line 248 |
| GET, HEAD | `/<file>` | static files under the folder, see below | line 248 |
| GET, HEAD | `/<file>.webm`, `.mp4` | video with byte ranges | `sendVideo()` line 123 |
| other | anything | 405 (except the POST routes above) | line 214 |

There is no WebSocket handling in this server. Chat WebSocket proxying exists only in `lan-proxy.js`.

**Control route safety** (`controlRoute()`, line 163). A request with an `Origin` header other than
`http://127.0.0.1:<port>` or `http://localhost:<port>` gets 403, so other websites open in the browser can't drive
the stream. POSTs must be `Content-Type: application/json` (415 otherwise), which forces a CORS preflight that the
server never answers.

**Emote relay caching.** The three CDN files are cached 10 minutes; when a refresh fails, the stale copy is served.
With no copy at all the route answers 502 and the pages fall back to text emotes.

**qBittorrent** (`qbProgress()`). Reads `GET <QB_URL>/api/v2/torrents/info?sort=added_on&reverse=true` with a
1.5 s timeout and no redirects. It needs the Web UI with "bypass authentication for clients on localhost" on; a
login page counts as unavailable. Results are shared for 2 s across all callers. It picks the newest torrent that is
downloading, or that finished within the last 15 minutes (or was seen downloading in the last 15 minutes, because
qBittorrent can keep an old completion date). Answer:

```json
{ "available": true, "name": "…", "progress": 0.42, "eta_s": 900, "state": "downloading", "completed": false }
```

`{ "available": false }` when qBittorrent is off, needs a login, or nothing qualifies. The auditorium's pre-show and
automatic phases use it (see [auditorium.md](auditorium.md#pre-show-phases-and-lights)).

**Static files.** Only these extensions are served: `.html .js .css .json .png .svg .woff2 .webp .avif .gif .webm
.mp4` (everything else, e.g. `.md`, `.mjs`, `.bat`, is 404). Refused with 404: paths outside the folder,
`standby-server.js`, `dinkdonk.js`, `lan-proxy.js` (case-insensitive, QA 5 Nov 2026) and anything under `cache/`.
`obs-bridge.js` is served; it holds no secret.

**Byte ranges** (`sendVideo()`). `Range: bytes=a-b`, `a-` and `-n` give 206 with `Content-Range`; an impossible
range gives 416; no range gives 200 with `Accept-Ranges: bytes`. HEAD sends headers only. The file stream closes
with the response, because players cancel requests all the time when seeking or looping. Needed for the lobby's
`.webm` loops.

## Control protocol

Panel → server → screens:

```
control.html  --POST /ctl/cmd {cmd, page, ...}-->  server  --SSE "data: {json}"-->  every screen with that page (and id)
screens       --POST /ctl/state {id, page, ...} every 1.5 s-->  server  <--GET /ctl/state every 1 s--  control.html
```

**Command** (`POST /ctl/cmd`, JSON):

| Field | Meaning |
|---|---|
| `cmd` | command name (required string) |
| `page` | `lobby` (default, for old panels) or `auditorium`; the server sends only to screens of that page |
| `id` | optional: one screen only (the screen's random `pageId`) |
| other fields | per command: `value`, `on`, `nick`, `text` |

The server forwards the whole JSON object unchanged. Each page also checks `page` itself: the auditorium ignores
anything not addressed to `auditorium` (older servers broadcast everything). The auditorium's commands are listed
in [auditorium.md](auditorium.md#control-commands); the lobby's in [lobby.md](lobby.md).

**State** (`POST /ctl/state`, JSON): at least `id` (string). The pages also send `page`, `ts`, `size` `[w, h]`,
`obs` (true inside OBS), `director`, `chatters[]` and, in the auditorium, `preshow` and `house`. A screen that gets
404 here stops (an old server without control routes).

## Control panel (`control.html`)

One page for both scenes. It polls `GET /ctl/state` every second and sends commands with `POST /ctl/cmd` (3.5 s
timeout).

| Part | Controls | Sends |
|---|---|---|
| Scene | Lobby / Auditorium select; clears the old scene's rows at once | (added as `page` to every command) |
| Auditorium pre-show (auditorium only) | Seating, Lights down, Film, Movie (no zoom), Film outro, Lights on (film plays), Everyone leaves, Lights up, Auto | `phase` + `value`, `movie`, `outro`, `lights` + `on`, `houseOut` + `on`, `phaseAuto` + `on` |
| Camera | Wide shot, Follow the next arrival, Follow someone now, Automatic director; Every (s), Zoom | `wide`, `next`, `random`, `director` + `on`, `every` + `value`, `zoom` + `value` |
| Add a chatter / make someone talk | nick + message | `say` + `nick`, `text` |
| In the cinema | seat counts, Reset (auditorium only), per chatter Follow / Remove | `reset`, `follow` + `nick`, `remove` + `nick` |

- It shows the state of the OBS screen (`obs: true`) first, else the biggest screen, so a 4K preview tab doesn't
  hide the stream's state.
- Status lines: phase and shot, download name / percent / ETA, director state, "n/135 seats … waiting outside".
- With an auditorium selected and a server older than `controlVersion` 2, every control is disabled with "Restart
  standby-server.js to enable safe auditorium controls."
- Keys on the screen itself (OBS: right-click the source → Interact): `F`, `R`, `W`/`Esc`, `D`.

## OBS bridge (`obs-bridge.js`)

Pins the film onto the auditorium's big screen. The auditorium page inside OBS sends where the screen is on every
camera move; the bridge moves a VLC capture there with a corner-pin shader and shows it only during the Film phase.

**OBS objects it expects** (constants at the top, lines 22-25):

| Constant | Value in code | What |
|---|---|---|
| `SCENE` | `dggCINEMAtheatre` | the scene that holds the film item |
| `CAPTURES` | `firefoxBrowserCinema`, `mpvCinema` | screen captures selected with OBS visibility |
| `FILTER` | `Corner pin (live)` | the shader filter the bridge drives |
| `SHADER` | `cinema-screen.shader` beside obs-bridge.js | corner pin plus transparent-output gate |

**Password.** obs-websocket v5 authentication (`obsConnect()`, line 38). The password comes from `OBS_PASSWORD` if
set, otherwise from obs-websocket's own config file on this PC (`%APPDATA%\obs-studio\plugin_config\obs-websocket\
config.json`, its server password field; `obsPassword()`, line 32). It is only used to compute the challenge
response and never goes to a page or a log. If OBS refuses it (close code 4009), the bridge logs "OBS refused the
password". Never put the password in a file in this repo.

**What it changes in OBS** (`setup()`, line 87; `pump()`, line 211):

1. Once: creates the `Corner pin (live)` shader filter on `firefoxBrowserCinema` if it doesn't exist.
2. Disables any other enabled filter on that source whose name contains "corner pin" (the old fixed pins stay as a
   manual fallback).
3. Enables `Corner pin (live)`.
4. On each update: sets the filter's eight corner values (`Top_Left_X` … `Bottom_Left_Y`), then shows or hides the
   `firefoxBrowserCinema` item in `dggCINEMAtheatre`. Corners always go first, so the film never flashes at the
   previous shot's corners.

Capture transforms are also configured by bridge-sizing.js; current visibility gating is described below. It subscribes to Config events and re-runs setup when the scene collection changes.
If an update fails (item or filter renamed, another collection), it looks again at most every 2 s. "not ready" in
the log usually means the expected collection isn't loaded.

**Page ↔ bridge** (plain WebSocket on `OBS_BRIDGE_PORT`, JSON text frames; a minimal frame parser is built in):

| Direction | Message |
|---|---|
| page → bridge | `{ film: true\|false, w: <viewport px>, h: <viewport px>, quad: [[x,y] TL, TR, BR, BL] }` |
| bridge → page | `{ obs: true\|false }` on connect and whenever OBS becomes ready or goes away |

- The bridge maps viewport px to the shader's -100..100 frame (`onPage()`, line 194). This assumes the auditorium
  browser source fills the whole OBS canvas (2560x1440 for the owner), unscaled and uncropped. A source placed
  differently puts the film in the wrong place.
- Only the most recently connected page drives (`driver`). When it closes (scene switched, reload), the film is
  hidden, then the next open page takes over.
- Updates are latest-only: while one request is with OBS, newer corners replace the waiting ones, so a slow OBS
  never plays back a queue.
- Only connections from this PC's own addresses are accepted (403 otherwise), so a phone on the LAN can't switch
  the film on and off. Any plain HTTP request gets a one-line status (`OBS ready/not ready, n page(s), film on/off`).
- The page only connects when it runs inside OBS (`window.obsstudio`). While `obs` is true, the page paints the
  screen black under the film; otherwise green for a manual chroma key.

## `dinkdonk.js` (dinkdonk.mov data)

dinkdonk.mov has no public JSON API, so this module parses its server-rendered HTML (requests send
`HX-Request: true` and a descriptive user agent, 20 s timeout).

| Source page | Parser | Feed key |
|---|---|---|
| `/schedule` | `parseSchedule()` | `schedule: { tz, sessions: [{ start, end, events }] }` (times converted from the site's zone, default America/New_York) |
| `/api/page/ratings?page=1&order=endTime,DESC` | `parseRatingCards()` | `ratings` (newest) |
| same, `order=average,DESC` / `average,ASC` | `parseRatingCards()` | `best`, `worst` |
| `/api/page/polls` | `parsePollCards()` | `polls: [{ id, title, kind, by, winners: [{ label, poster, title }] }]` |
| `/api/page/history?page=1..8` (25 each) | `parseHistory()` | `history: [{ id, title, year, imdb, type, watchedAt, watchedTs, method, conductor, picker, ratingId, rating, polls, notes }]` |
| `/rate/<id>/results` | `parseRatingDetail()` | `details.ratings[id]` (poster, overview, runtime, genres, TMDB score, votes …) |
| `/poll/<id>/results` | `parsePollDetail()` | `details.polls[id]` (type, options, instant-runoff rounds, voters, endedAt) |

Feed (`GET /dd/data.json`): `{ version, fetchedAt, schedule, ratings, best, worst, polls, history, details, stale,
error }`.

**Caching** (`refresh()`, `data()`, lines 212-266):

- Stale-while-revalidate: answers from cache and refreshes in the background when older than 5 minutes. Refreshes
  happen only when a page asks (`cinema.js` every 2 minutes, `dinkdonk.html`).
- Detail pages: the newest 3 ratings and 2 polls are always re-read; the rest come from cache because finished
  polls don't change. Details no longer referenced are dropped.
- The last good feed is written to `cache/dinkdonk.json` (git-ignored, never served) and loaded at start if its
  `version` matches `CACHE_VERSION` (3; bump it when the feed's shape changes).
- `stale: true` when the data is older than 10 minutes; `error` holds the last refresh error. With no cache and the
  site unreachable (for example Cloudflare blocks during LaLiga matches in Spain), the route answers 502.
- `search(q)` (`/dd/search`): `{ q, more, entries }` from the history search, cached 10 minutes, at most 200 queries.

## LAN proxy (`lan-proxy.js`)

For watching the scenes on a phone or tablet in the same network. The server and relay stay on 127.0.0.1; the
proxy listens on the PC's first private IPv4 (or the address given) on port 18780.

| Request | Goes to |
|---|---|
| HTTP | `standby-server.js` (Host rewritten). If the phone leaves, the upstream request is closed too, so the server doesn't keep a dead screen. If the server restarts mid-stream, the phone's response ends so its EventSource reconnects. |
| WebSocket `/__dgg_chat_ws` | the chat relay, with the `Origin` header removed (the relay expects local pages) |
| other WebSocket | `standby-server.js` (which has no WebSocket handler) |

**View-only by default** (QA 5 Nov 2026). Without `--control` only GET and HEAD pass, and of `/ctl/*` only
`GET /ctl/events`. Everything else gets 403 "view-only proxy". Reason: the server's control routes only refuse
foreign `Origin`s, so through the proxy any device on the LAN or tailnet could otherwise post commands (a fake
chatter saying anything on stream, remove, reset). `--control` passes everything, for the control panel on your own
phone (e.g. over Tailscale); see "Looked wrong" for a likely problem with that.

Phone URL (printed at start): `http://<lan>:18780/auditorium.html?everyone=1&relay=<lan>:18780`. The `relay=` makes
the page's chat WebSocket go through the proxy. Each new device's first connection is logged.

## `shared/core.js` (`window.SB`)

Loaded first by every scene. Builds `window.SB` (line 571).

**URL options read here** (`cfg`, line 21): `relay` (default `127.0.0.1:18765`), `f` (DSA chat text size, default
4), `chat=dsa|native|off` (default `dsa`, `native` with demo), `chatbar=1`, `chatcrop` (default 40), `title`,
`sub`, `until=HH:MM`, `cmds=off`, `demo=1`.

**Stage**

| Member | Meaning |
|---|---|
| `SB.W`, `SB.H` | 1920, 1080: every page lays out a 1920x1080 stage |
| `SB.mountStage(el, { cover })` | positions `el` as the 1920x1080 stage and scales it to the window on every resize. Default: fit (letterbox, centred). `cover: true`: fill the window and crop the overflowing sides, centred (the lobby's `fit=cover` for a squarer OBS source). Emits `resize` with the scale. |
| `SB.view` | the part of the stage the window shows, `[x0, y0, x1, y1]` in stage px (smaller than the stage only in cover mode) |
| `SB.fitCanvas(canvas, w, h)` | sizes a canvas to the real pixels it covers (scale × devicePixelRatio) and keeps it so on resize; returns its 2D context |

**Chat events** (`SB.on(type, fn)`, `SB.emit(type, data)`; a throwing handler is logged and the others still run):

| Event | Data |
|---|---|
| `msg` | `{ nick, text, tokens, features, ts, onlyEmote, emotes, color, rainbow, sub }` (`ingestMessage()`, line 343) |
| `combo` / `comboEnd` | `{ emote, count, nick }` while different chatters post the same single emote / `{ emote, count }` when it ends (count ≥ 2) |
| `command` | `{ name, nick, args }` after a registered `!command` ran |
| `names` / `join` / `quit` | user counts / the raw JOIN or QUIT data |
| `modAction` | `{ kind: 'MUTE'\|'BAN', nick: <target>, by: <mod> }`, sent just before `purge` |
| `purge` | the muted or banned nick |
| `broadcast` | `{ text }` |
| `support` | `{ kind, nick, text }` for SUBSCRIPTION, GIFTSUB, MASSGIFT, DONATION |
| `status` | `connecting`, `live`, `offline` or `demo` (also `SB.status`) |
| `emotes` | the emote store, after each successful load or a late stylesheet |
| `resize` | the stage scale |

`color` / `rainbow` follow DGG's own name colours (`flairColor()`, line 267): the user's flair with the lowest
priority number wins, plain users are white, tier 5 is the moving rainbow. A built-in flair table is replaced by
`/dgg/flairs.json` when it loads.

**Emotes**

| Member | Meaning |
|---|---|
| `SB.emotes` | `{ names: Set, css: bool, sizes: Map }`. Names from `/dgg/emotes.json`; `css` once `/dgg/emotes.css` loaded. A failed list falls back to 35 built-in names (drawn as text) and is retried every 30 s (60 tries); a failed stylesheet likewise. |
| `SB.emoteSize(name)` | real per-frame size measured from the emote CSS (`{ w, h }`), or a text estimate without CSS |
| `SB.emoteEl(name, height)` | a `span.sb-emote` scaled to `height`, or a text pill without CSS. DGG's one-shot text glyph effects (`::before`/`::after`, e.g. 💤) are hidden (`textDeco()`). |
| `SB.emoteFacing(name)` | `left`, `right` or `front` from `emote-facing.json` |
| `SB.faceEmote(el, name, dirX)` | mirrors `el` so the emote looks toward `dirX` (> 0 right, < 0 left, 0 keeps it). `front` emotes are never mirrored. |

**Bubbles.** There is no bubble code in `core.js`. Each scene draws its own speech bubbles and uses
`SB.renderTokens()` for their text (auditorium: `say()` and `placeBubble()`).

**Text and tokens**

| Member | Meaning |
|---|---|
| `SB.tokenize(text)` | splits on whitespace into `{ t: 'emote', name, mods }` (a known emote name, optionally with lower-case `:modifiers`) or `{ t: 'text', v }`. URLs become 🔗. |
| `SB.renderTokens(el, tokens, emoteHeight, maxChars)` | appends text nodes and emotes (never `innerHTML`); an emote counts as 4 characters; cut with "…" |
| `SB.nickColor(nick)`, `SB.hashHue(s)` | a stable colour / hue from a string |

**Other**

| Member | Meaning |
|---|---|
| `SB.start()` | load emotes, flairs and facing, then connect to the relay (or start demo traffic) |
| `SB.command(names, cooldownMs, fn)` | register `!commands`: global cooldown per command, 8 s per user; off with `cmds=off` |
| `SB.mountChat(el, opts)` | the DSA chat iframe, a native list, or nothing (older drafts; not used by lobby or auditorium) |
| `SB.stats`, `SB.mpm()`, `SB.topEmotes(n)`, `SB.topWords(n)`, `SB.activeChatters(ms)`, `SB.topChatters(n, ms)` | chat statistics |
| `SB.timerText()`, `SB.clockText()` | "away for" or `until=` countdown; local clock |
| `SB.rand(a, b)`, `SB.pick(arr)` | helpers |
| `SB.say(nick, text, features)` | console testing: feeds a fake `MSG` frame |
| `SB.cfg` | the parsed URL options |

## `shared/cinema.js` (`window.Cinema`)

Loaded after `core.js` by the lobby, the auditorium and the older `cinema-*` / `hall-*` pages. (Its header comment
still says it is for `cinema-*.html` only.)

**Mention filter (who walks in)** (lines 34-38):

| URL | Who walks in |
|---|---|
| (default) | chatters whose message mentions `arealhumanbean` (with or without `@`, case-insensitive, as a whole word), plus that user's own messages |
| `tag=<nick>` | the same for another nick |
| `everyone=1` | every chatter |
| `demo=1` | everyone, unless `tag=` is given |

`Cinema.tag` is the nick in force, or `null` for everyone. The filter only decides walk-ins: pages can still listen
to `SB.on('msg')` for everyone (the auditorium does, for moderators, dozing and phones).

**Which emote a walker wears** (message handler, line 144): the first emote in this message that works as a body,
else the last such emote this chatter used, else `Cinema.defaultEmote(nick)`. "Works as a body" excludes
`AVATAR_BLOCK` (`JARVIS`) and square "picture" emotes: `findBoxyEmotes()` loads every emote image through
`/dgg/emote-img` and marks one boxy when more than 80% of its border pixels are opaque. Until that check finishes,
every emote is allowed.

| Member | Meaning |
|---|---|
| `Cinema.onWalkIn(fn)` | `fn({ nick, emote, tokens, text, color, rainbow, sub, ts, roomIndex, detour, features })` for each walk-in. `roomIndex` 0-4 (regulars mostly keep theirs), `detour` `null`, `'popcorn'` (12%) or `'bathroom'` (5%). |
| `Cinema.defaultEmote(nick)` | a stable emote for a nick from a pool of common emotes that exist on DGG (minus boxy ones) |
| `Cinema.onRooms(fn)` | `fn(rooms, data)` now and after every feed refresh (`/dd/data.json`, every 2 minutes). `rooms`: the last five films shown, `{ title, year, poster, rating, votes, watchedTs, conductor, method }`, padded with placeholders. `data`: the raw feed. |
| `Cinema.onCombo(fn)`, `Cinema.onPurge(fn)` | shortcuts for `SB.on('combo')` / `SB.on('purge')` |
| `Cinema.showtimes(data)` | upcoming sessions `[{ start, end, live }]` |
| `Cinema.rooms`, `Cinema.data` | current rooms and feed |
| `Cinema.green` | `'off'` (`green=off`), the `green=` hex colour, or `#00ff00` |
| `Cinema.timeLocal(ts)`, `Cinema.dayShort(ts)` | formatting helpers |

## `shared/live.js`

With `?live=1`: every 1.5 s fetches the page itself plus `shared/core.js`, `shared/cinema.js` and
`shared/base.css`, and reloads when one changed. A change must be seen twice in a row (a file caught half-written),
and error answers from a restarting server don't count (QA 5 Nov 2026). Does nothing without `live=1`.

## `shared/base.css`

`html, body` fill the window, black, no scrollbars; `#stage` absolute. Emote classes: `.emote` (DGG's CSS sets image
and size), `.sb-emote` (scaled box), `.sb-nob` / `.sb-noa` (hide glyph effects), `.sb-emote-text` (text pill).
Chat panel: `.sb-chat`, `.sb-chat-frame`, `.sb-chat-note`, `.sb-chat-list`, `.sb-chat-line`, `.sb-chat-nick`.
`.sb-cmds` for command legends.

## `shared/emote-facing.json`

A flat JSON object: DGG emote name → `"left"`, `"right"` or `"front"`, the way the emote looks in its original
image.

```json
{ "Abathur": "right", "AbaW": "front", "ALO": "left" }
```

On 5 Nov 2026: 326 entries (148 front, 111 right, 67 left). Names are case-sensitive and must match DGG's emote
prefix. Missing names count as `front` and are never mirrored. Pages mirror an emote so it faces the way it walks
(`SB.faceEmote`). The labels were made from contact sheets with `tools/emote-sheet.html`, which is in the
git-ignored `tools/` folder (local only). To label a new emote, add its line by hand.

## Looked wrong or inconsistent (5 Nov 2026)

- **`lan-proxy.js --control` likely can't send commands.** The HTTP proxy passes the phone's `Origin` header
  (`http://<lan>:18780`) through, and the server refuses POSTs from any Origin other than 127.0.0.1/localhost on its
  own port. Browsers send `Origin` on same-origin POSTs, so `POST /ctl/cmd` from the panel on a phone would get 403.
  Not tested.
- **Node version.** `obs-bridge.js` calls the global `WebSocket`, which Node only has by default from version 22. On
  Node 18 or 20 (README says "Node 18+") it logs "OBS: WebSocket is not defined" every 3 s and never connects.
- `AGENTS.md` lists "bubbles" under `core.js`; bubbles are drawn by each scene.
- `lan-proxy.js` routes "anything else (e.g. live reload)" WebSockets to the server, but the server has no WebSocket
  handler and `live.js` polls over HTTP.
- `README.txt` says dinkdonk.js makes "about 15 requests every 5 minutes"; the code makes 13 list requests plus at
  least 5 detail requests (3 ratings, 2 polls) per refresh, more for new items.
- `cinema.js`'s header describes it as shared logic for `cinema-*.html` only; the lobby and auditorium use it too.
- `green=off` means "no green" in `cinema.js`, but the auditorium paints its screen `#00ff00` for it.
- The server's control routes accept requests with no `Origin` header at all (curl, scripts on this PC). Fine while
  it is bound to 127.0.0.1; it matters only through the LAN proxy with `--control`.

## One OBS cinema source (local edition)

Use `http://127.0.0.1:18770/cinema.html?everyone=1` as one OBS Browser Source, at the canvas size.
`control.html` now has Show lobby and Show auditorium buttons. They send `{cmd:"present",value:"lobby"|"auditorium"}`
to `/ctl/cmd`. The existing Controls for selector changes the camera/lighting command target without changing
what is shown. A successful Show command also selects that room's controls.

`GET /ctl/state` additionally returns `presentation: {version:1, view, outputs}`. The selection is atomically
saved to the ignored `cache/presentation-<port>.json` file. Test ports have their own selection. `/ctl/output`
accepts small JSON heartbeats from unified outputs (`id`, `view`, `obs`); they expire after ten seconds.
These routes retain the existing same-origin/JSON-only control protections. An invalid view gets 400.

`cinema.html` polls once per second and loads both rooms once in full-size same-origin frames. Its URL
options are forwarded, everyone=1 is the default unless a tag/everyone option was supplied, and managed=1
lets shared/core.js preserve top-level OBS detection. Switching changes opacity, input focus and accessibility
visibility; neither frame navigates, shrinks or unloads. Both continue receiving real chat and running their
simulation. Audiences, camera positions and phase/lighting state survive switching. The pages' existing fallback
animation timers handle background rAF throttling. Both scenes use more resources than one alone.

shared/core.js exposes isOutputActive() and a same-origin parent-only outputVisibility event. The auditorium's
film bridge requires both film phase and output visibility before showing the external capture. Hiding it sends
film=false without changing its internal phase; returning restores the capture if it is still in film phase.
Selected view survives server restart. Reloading the entire Browser Source still reloads both rooms. A server
outage leaves both loaded and retries selection polling.
This does not provision OBS sources or configure the corner-pin plugin. Standalone lobby/auditorium URLs still
work, and the hosted edition requires its own server support before the new switching buttons can be enabled.

## Continuous guest journey (combined source)

`shared/journey.js` creates a coordinator per combined output before the two frames load. Managed same-origin
rooms use case-insensitive nickname membership so regular guests belong to one room at a time. Each output
has its own journey; this is not server-persisted state and a full source reload starts over.

Lobby arrivals use a FIFO Map capped at 512 pending guests. Repeated messages update the pending payload
without changing queue order. The animation loop admits at most one guest every 1.4-2.2 seconds, pauses at
the lobby's 40-person cap or crowded entrance, and never catches up with a burst. Pending guests expire after
ten minutes without chat. The roster includes pending guests as `waiting to arrive` with Follow disabled.

Managed lobby guests use the first auditorium door. On completing the door animation, `finishEnter` transfers
the nickname, current emote and carried snack through the coordinator, then removes the lobby walker.
The auditorium admits new regular guests only from that handoff; its raw chat connection updates existing
or queued guests. Its existing paced entrance, 135-seat capacity and 270-person waiting queue remain in use.
Coordinator delivery buffers until the auditorium is ready and retries failures without counting extra transfers.
Removal, queue expiry and reset release membership so a guest can return on later chat. State heartbeats expose
journey counts and lobby waiting counts for QA. Moderator/janitor staff retain their separate behavior; the
host's explicit Walk in action can still add someone directly to the selected room. Standalone room URLs keep
the original independent admission behavior. No extra chat connection, trivia integration or art changes.

Arrival pacing now adapts to the number waiting: 1-5 use 1.4-2.2 seconds; 6-11 use 0.9-1.4 seconds;
12-39 arrive in pairs; 40+ arrive in groups of three. Group members are 0.25-0.45 seconds apart,
with 0.9-1.4 seconds between groups. Every admission still checks crowding and capacity; no catch-up floods.
The pacing slows automatically as the queue clears. These thresholds count pending lobby guests.

Capture sizing: setup calls fitCapture from bridge-sizing.js for each available capture. GetVideoSettings supplies baseWidth/baseHeight.
Each capture item gets a full-canvas OBS_BOUNDS_STRETCH box at (0,0), rotation zero, and no outer crop.
This is after the shader, ensuring normalized corners span the correct canvas even when a direct capture
changes dimensions. Nested helper scenes/groups also give Window/Game Capture children centered
OBS_BOUNDS_SCALE_INNER boxes with crops preserved; unrelated children are untouched. Persistent OBS
bounds respond to source dimension changes without per-frame API traffic. Canvas changes require a bridge
restart. A direct capture fills the screen with stretching; helper capture boxes letterbox instead.

Unified capture selection (6 Nov 2026): bridge-captures.js maintains both shader/visibility states.
OBS Config, InputNameChanged and SceneItems events are subscribed (bitmask 138). Scene eye-on selects
that capture, eye-off clears the selected capture. Automatic switching echoes are consumed separately. Host lobby/phase gating uses shader alpha,
so the selected eye stays enabled in every mode. Both shaders get camera corners and Cinema_Visible, which is true
only when the auditorium page requests film=true and valid screen corners are available. Inactive sources hide before the next one shows.
Missing optional captures are allowed; none present reports not ready. New/removed/renamed sources trigger
setup. Legacy Firefox/mpv launchers now alias the same bridge and ignore OBS_FILM_SOURCE.
Selection survives visibility gating and reconnect within a process; full bridge restart uses current OBS
visibility (topmost visible recognized item if both are on, none if both are hidden). No host source buttons.

Eye-control correction: cinema-screen.shader retains the upstream corner-pin license/attribution and
adds Cinema_Visible (default false). setup points both filters to this repo-local shader. bridge-captures
sets this uniform from film/quad availability; source enable states now express only user selection.
Thus the selected source eye remains enabled in dim/lobby and the shader outputs transparent pixels.
The other source eye is disabled when switching. Host gating does not mute player audio.

Lobby eye gating (current behavior): Show lobby turns both capture source eyes off and remembers selection.
Returning to the auditorium restores the selected eye even in seating/dim mode. Film/Movie phase still
controls visible pixels through Cinema_Visible. Thus eye controls work in auditorium mode, and lobby
automatically disables both. Bridge polls the local /ctl/state every 500 ms to distinguish view from phase;
CINEMA_CONTROL_URL can override its endpoint. Unavailable control state or no scene page hides both.
