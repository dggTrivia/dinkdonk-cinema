# Auditorium (`auditorium.html`)

Scene 2 of DinkDonk Cinema: the inside of "Screen 1". Chatters who walk in come through a tunnel at the back of the
hall, climb the stair aisle and take a seat. The page runs the pre-show on the big screen, dims the house lights,
and (inside OBS, with `obs-bridge.js`) has the real film pinned onto the screen.

Line numbers below are from the 5 Nov 2026 version of `auditorium.html` (2,137 lines). Function names are the
stable way to find things.

| File | Role |
|---|---|
| `auditorium.html` | the live scene (OBS "DinkDonk Cinema" browser source) |
| `auditorium-qa.html` | QA copy. On 5 Nov 2026 it lags behind the live page (no `bridge=` option, no Movie/Outro/Lights-on shots, older dim fade and pre-show titles). Try risky work there first. |
| `shared/core.js`, `shared/cinema.js`, `shared/live.js`, `shared/base.css` | shared code, see [server-and-shared.md](server-and-shared.md) |
| `roxy3d/qa11/` | the art: `cinema_draft_13*.png`, `cinema_layout_13.json`, `draft13/`, `draft13_bands/`, `draft13_dim/`, `draft13_dim_bands/`, `cinema_draft_13_dim*.png` |
| `roxy3d/out10/manifest.json` + `items/` | the lobby's popcorn, soda and usher-cap sprites (reused here) |
| `assets/cpMOP.webp` | the janitor penguin |

## Page structure

```
#stage                    mounted by SB.mountStage (1920x1080, letterboxed; no cover mode here)
  #cam                    camera transform (translate + scale), everything in the world zooms together
    #world                1920x1080 world, z-index 0
      img#bg              lit background (cinema_draft_13.png / @2x)
      img#bg-dim          dim twin of the background (added at start if the layout has dim art)
      svg#screenq         polygon over the screen: chroma green, or black when the OBS bridge drives the film
      #preshow            960x540 "projector" div, affine-mapped onto the screen quad
        .ps-slide x3      Up next / Now loading / In the audience
        #ps-pops          emotes floating up the screen edges
      img.slice (+ .dim-art twins)   banded depth-slice pieces, hidden unless something is behind them
      div.sheet           the entrance door's sprite sheet while it swings
      div.w               one per walker: .sh (shadow), .bod > .em (emote) + .item / .phone / cap
    #names                world-space labels: .nm names, .fl floating text, .zz z's, svg.beam (flashlight)
  #bubbles                screen-space speech bubbles (z-index 86000), do not zoom
```

Scripts load in this order: `shared/core.js`, `shared/cinema.js`, `shared/live.js`, then the inline page script.
Fonts: Oswald from Google Fonts (falls back to Arial Narrow).

Start-up (the async block at the end, lines ~2048-2133): fetch `roxy3d/qa11/cinema_layout_<DRAFT>.json` → read the
camera, rows, seats, stairs → build slices, dim twins and the door → set the screen quad and the pre-show matrix
→ `bridgeConnect()` → `applyPhase()` → add `#bg` / `#bg-dim` → `SB.mountStage` → start the frame loop →
`SB.start()` (emotes, then chat) → `pollDownload()` → `audience()` every 2 s.

If the layout JSON fails to load, `L` stays null: no seats, no walkers, no screen; only the background (as
`cinema_draft_<DRAFT>.png`) shows. The error goes to the console as `[auditorium] layout`.

## URL options

Verified against every `q.get` / `q.has` call in the page (5 Nov 2026). Options from the shared scripts are listed
after.

| Option | Default | Effect | Where |
|---|---|---|---|
| `draft=NN` | `13` | which `roxy3d/qa11/cinema_layout_NN.json` / `cinema_draft_NN.png` to load (two digits only) | `DRAFT`, line 203 |
| `phase=seating\|dim\|film\|up` | `seating` | starting phase | `show`, line 211 |
| `screen=green` | off | screen polygon always green (never the pre-show) | `alwaysGreen` |
| `director=0` / `director=<s>` | on, 150 s | `0` turns the automatic director off; a number sets seconds between automatic follows (30-1800) | `DIRECTOR_ON`, `director.every` |
| `zoom=<1.2-3>` | `1.85` | follow-shot zoom | `ZOOM` |
| `ctl=0` | on | no connection to the control panel (`/ctl/events`, `/ctl/state`) | line 2019 |
| `bridge=0` | on (OBS only) | inside OBS: don't send screen corners to `obs-bridge.js` | `bridgeConnect()` |
| `bridge=<host:port>` | `<page host>:18790` | where the OBS bridge runs | `bridgeConnect()` |
| `maxres=<height>` | none | cap art resolution, e.g. `1080` never loads the @2x art | `MAXK`, `dpr()` |
| `slidefade=seq` | cross-fade | pre-show slides fade out (0.4 s), then the next fades in (0.4 s) | `SEQ_FADE` |
| `leave=<minutes>` | off | full house with people waiting: the longest-dozing chatter quiet that long goes home, one every 5 s (1-240) | `LEAVE_MS`, `tick()` |
| `qb=<0-1>` | none | testing: pretend a download at that progress (ETA 240 s) | `QB_TEST` |
| `qbname=<name>` | `Test feature` | testing: the pretend torrent's name (with `qb=`) | `pollDownloadOnce()` |
| `janidle=<s>` | `600` | testing: seconds without a message before a janny clocks off (20-3600) | `JAN_IDLE` |
| `doze=<s>` | `600` | testing: quiet seconds before a seated chatter nods off (10-7200; actual is ×0.8-1.6) | `DOZE` |
| `chatty=<n>` | `3` | messages within a minute that get the phone out in the dark (2-20) | `CHATTY` |
| `kick=<0-1>` | `0.5` | chance an usher visit ends in a kick | `KICK` |
| `phones=<0-1>` | `0.3` | share of chatters who carry a phone (not in the header comment) | `PHONE_SHARE` |
| `sitz=<zpx>` | `48` | seated emote's lift above the floor, for comparing looks (not in the header comment) | `SIT_Z` |
| `sitscale=<0.5-2>` | `1.2` | seated emote size (owner picked 1.2 on 4 Nov 2026; not in the header comment) | `SIT_SCALE` |

From the shared scripts (see [server-and-shared.md](server-and-shared.md)):

| Option | Effect here |
|---|---|
| `everyone=1` | every chatter walks in (use this for checks) |
| `tag=<nick>` | walk-ins must mention this nick instead of `arealhumanbean` |
| `green=<hex>` | chroma colour of the screen polygon; `green=off` gives plain `#00ff00` here (see "Looked wrong") |
| `relay=<host:port>` | where the chat relay runs (default `127.0.0.1:18765`) |
| `live=1` | reload when the page or a shared file changes on disk |
| `cmds=off` | no effect: the auditorium registers no `!commands` |
| `chat=`, `f=`, `chatbar=`, `chatcrop=`, `title=`, `sub=`, `until=` | no effect: no chat panel or headline here |
| `demo=1` | fake chat. Exists, but the project rule is real chat only (`everyone=1`); don't use it for checks |

## Layout JSON contract (`cinema_layout_13.json`)

The file is 3.2 MB and mostly provenance written by the render briefs (QA numbers, hashes, light lists). The page
reads only these keys. Paths inside `page_layers` are relative to `roxy3d/qa11/`.

| Key | Used for |
|---|---|
| `camera.k`, `camera.Ox`, `camera.Oy` | the projection `P(u, v, z) = [Ox + (u - v)·60·k, Oy + ((u + v)·30 - z)·k]` (line 585). Emote height `EH = 45·k`, max width `MAXW = 66.6·k`. |
| `rows[]` | `row` (name B..I), `v`, `floor_zpx_world`, `seat_u_by_block` (`left` / `main` / `right` → u values). A row with floor ≤ 24 counts as flat. Draft 13: 8 rows, 135 seats. |
| `stairs.treads_v0_v1_zpx_world` | `[v0, v1, z]` per tread; walkers step to each tread's middle on the way up |
| `walk_route.rear_portal_to_cross_aisle` | the entrance route `[u, v, z]` from outside the door, through the tunnel, to the cross-aisle. Point 0 is the spawn point; the last point's v is the cross-aisle. |
| `screen.corners_1920x1080` | `TL`, `TR`, `BR`, `BL` of the screen in stage px: the screen polygon, pre-show matrix, bubble avoidance and the corners sent to OBS |
| `page_layers.slices[]` | depth slices: `name`, `file`, `file_2x`, `x`, `y`, `w`, `h`, `z_index`, optional `pieces[]` (each `x`, `y`, `w`, `h`, `file`, `file_2x`). Broken entries are skipped. |
| `page_layers.key_z_divisor` | `KZ` in the depth key (90) |
| `page_layers.image`, `image_2x` | background (falls back to `cinema_draft_<DRAFT>.png`) |
| `page_layers.dim.image`, `image_2x`, `slices[]`, `door_file`, `door_file_2x` | the lights-down twins. Dim slices are matched to lit slices by `name`, pieces by index. |
| `page_layers.entrance_door` | `file`, `file_2x`, `x`, `y`, `frame_width`, `frame_height`, `frames`, `columns`, `rows`, `fps`, `z_index`, `open_hold_frames[0]` |
| `page_layers.entrance_door.static_slice_cutout` | `file`, `x`, `y`, `w`, `h`, `slices[]` (names of slices to mask while the door moves) |
| `page_layers.spawn.wait_seconds` | `DOOR_WAIT`: how long a newcomer waits outside while the door opens |

Not read by the page: `depth_key`, `z_index_formula`, `key_z_coefficient` (documentation of the formula the page
hard-codes), `coverage`, `pieces_note`, `dim.slices_dir*`, `dim.door_static_cutout_file*` (the lit cutout is used
for both sets), `static_slice_cutout.file_2x` / `polygon_1920x1080` / `active_frames`, and everything outside
`camera`, `rows`, `stairs`, `walk_route`, `screen` and `page_layers`.

`package/art.js` also depends on this file: it finds the default draft with the regex
`? q.get('draft') : 'NN'` and the art folder with `const ART = '...'` in `auditorium.html`, then packs every image
path named in the layout JSON (plus `@2x` guesses). Keep those two lines in that shape.

### Coordinates

- World coordinates are `u`, `v` (floor tiles) and `z` (height in "zpx world" units; the projection multiplies by
  `k`). Screen x grows with `u - v`, screen y with `u + v` and shrinks with `z`.
- The page always works in 1920x1080 stage px. 2x art is the same geometry at double resolution.

## Art layers and depth ordering

Draft 10 and later carry pre-rendered depth slices: each slice holds the pixels of the room in one band of camera
depth. Walkers and slices share one depth key (lines 641-646):

```
key     = (u + v) + z / KZ          bigger = nearer the camera; KZ = page_layers.key_z_divisor (90)
z-index = 1000 + round(key · 100)   for walkers (depthZ) and as each slice's z_index
```

So a walker in the tunnel sits behind the seat-block slices above it, and a seated chatter is covered by the next
row's backs. Without `page_layers` the page falls back to z-index `(u + v)·100 + 10`, fades walkers out in the
tunnel and only cuts seated emotes at the backrest.

| Layer | z-index | Notes |
|---|---|---|
| `#bg` / `#bg-dim` | auto (below) | the background already contains every slice's pixels |
| slices / pieces | 1000-4400 in draft 13 | from the JSON |
| entrance door sheet | `entrance_door.z_index` (2590) | |
| walkers | `depthZ(u, v, z)` | |
| `#screenq`, `#preshow` | 70000 | above everything in the world |
| `#names` | 1, over the whole `#world` (which is its own stacking context at 0) | names, z's, flashlight |
| `#bubbles` | 86000 | screen space, outside `#cam` |

**Banded slices.** Each slice's `pieces[]` cuts it into 64 px horizontal bands trimmed to visible pixels
(`roxy3d/tools/band-slices.mjs`). Draft 13: 159 slices, 2,332 pieces, plus the same number of dim pieces. The
whole slices were about 25 screens of pixels; the bands about 5.

**Culling** (`cullPieces()`, line 690). The background already shows every slice, so a piece is only displayed
when a walker's box (`w.box`) or the moving door is behind it in depth. A 64 px grid (`pieceGrid`) finds candidates.
Dim twins of pieces show only while the dim set is ready and the lights are down (or within 6.5 s of a change).

**Door** (`playDoor()`, `stepDoor()`, `doorCutout()`). On each arrival (and staff entries/exits) the door sheet
plays once at `fps`; a second arrival during the hold keeps it open. While it plays, the static slices named in
`static_slice_cutout.slices` that overlap the cutout rect get a CSS mask that removes the closed door's pixels.
Only overlapping pieces are masked (95 of 497 in the QA count of 4 Nov 2026).

**Resolution** (`dpr()`, `applyArtRes()`). Effective pixel ratio = stage scale × devicePixelRatio × director zoom
(when the director may zoom), capped by `maxres`. Above 1.3 the `file_2x` art is used. At a 2560x1440 OBS source
the scale is 1.33, so the 2x art is always used there. Dim pieces are fetched but not decoded up front; the full
dim background and door are decoded before `dim-ready` is set.

## Seating and walkers

Flow: `Cinema.onWalkIn` → `onMessage()` → `arrivals` queue → `spawn()` in `tick()` → walk `routeTo(seat)` → sit.

| Rule | Where |
|---|---|
| Moderators (DGG feature `moderator`) never take a seat; they become jannies | `onMessage()` line 972 |
| Arrivals enter one at a time, 0.9-1.6 s apart, and only when nobody stands within `WALK_GAP` (0.9 tiles) of the spawn point | `tick()`, `spawn()` |
| Full house (`guests() >= seats.length`): the head of the queue waits outside | `spawn()` |
| Queue limit `MAX_QUEUE` 270; a new nick over the limit drops whoever has been quiet longest | `onMessage()` |
| Queued arrivals quiet for 10 min leave the queue | `QUEUE_QUIET_MS`, `tick()` |
| A queued chatter who talks again: newest message, colour and time are updated | `onMessage()` |
| While "Everyone leaves" is on, nobody spawns | `tick()` |

**Seat choice** (`chooseSeat()`, line 898):

1. The front row (`rows[0]`, row B) is the "wheelchair row" (owner's joke): chatters wearing a YEE emote
   (`YEE_EMOTES`: the source names of the DSA userscript's ideological emote map) sit only there, everyone else
   stays out of it. If their part of the hall is full, any free seat.
2. Mentioning someone already seated puts you next to them (same row, within 0.9 u).
3. Otherwise a weighted random seat: row weights B 0.5 … F 1.5 … I 0.8, the `main` block favored toward its middle
   (u ≈ 9.3), side blocks ×0.55, and below half full a seat beside a stranger ×0.3.

**Route** (`routeTo()`): entrance route → cross-aisle → stair aisle (u 3.475, or u 15.15 for the `right` block) →
each tread middle up to the row → the row's legroom (`row.v - 0.45`) → along it to the seat's u. On arrival the
walker sits at `[seat.u, seat.v + 0.2, seat.z + SIT_Z]`, facing the screen.

**Walking** (`step()`, `blockedAhead()`). 1.35 tiles/s on the flat, 0.85 on stairs. Earlier walkers have right of
way; a walker projects those ahead onto its next stretch and stops `WALK_GAP` short. People leaving (Everyone
leaves) queue among themselves, separately from people coming in, so the aisles don't deadlock. The walk is the
lobby's: one lazy hop about every 0.8 s, waddle, squash on landing. Emotes face the way they walk
(`SB.faceEmote`, screen x = u - v).

**Seated look.** Emotes are drawn 1.2× (`SIT_SCALE`). The row's own seat backs cut the lower body with a diagonal
`clip-path` that follows the backrest slope (30 px down per 60 across) and mirrors with the emote. A hop or a
bounce lifts them out from behind the backs.

**Walker extras** (`makeWalker()`): 85% carry popcorn (20% of those a soda) from `roxy3d/out10/` items; 30% carry a
phone. The name label shows for a few seconds after appearing or sitting, and always for the followed chatter and
for jannies. Overlapping names show one at a time (`showNames()`, rank: followed > jannies > most recent).

**Tunnel.** A walker with `u < 2.9 && v > 8.8 && z < 10` is in the tunnel and counts as not seen: no name, speech is
held (`pendingSpeech()`, first and latest message only) and comes out one bubble per 2.5 s once visible.

**Avatars.** `checkAvatar()` test-loads each emote image (12 s timeout). A failed one shows a temporary "?" and is
retried after 5, 15, 30, 60, 120 and 300 s. Square "picture" emotes are already kept off chatters by `cinema.js`.

**Speech** (`say()`, `placeBubble()`, `capBubbles()`). The lobby's 90s dialog box with the name in the chat colour
(tier-5 rainbow too). At most 4 bubbles on screen, 6 s each, 64 characters, 22 px emotes. A bubble goes below the
speaker when above would cover the film screen, and moves past bubbles already placed. Off-view bubbles (zoomed in)
hide but keep their clock. A seated speaker bounces and their neighbours turn to look (`turnNeighbours()`).

**Dozing** (`doze()`): seated chatters quiet for `doze` × 0.8-1.6 nod off (lean, sink, slow breathing, z's on up to
12 sleepers). Any chat message from them, tagged or not, wakes them (`noteMessage()`).

## Pre-show phases and lights

Phases: `seating` → `dim` → `film` → `up` (`phases`, `setPhase()`, `applyPhase()`, lines 210-254).

| Phase | Lights | Screen |
|---|---|---|
| `seating` | up | pre-show slides |
| `dim` | down | pre-show slides |
| `film` | down (unless "Lights on") | green / black polygon for the film |
| `up` | up | pre-show slides |

**Automatic phases** (`autoPhase()`, while `show.auto` is on, the default):

- download progress ≥ 90% while in `seating` or `up` → `dim`
- qBittorrent reports the download completed and it has stayed completed for 10 s → `film`
- `up` is manual only. Any manual phase command turns auto off; the panel's "Auto" button turns it back on.

The download comes from `GET /qb/progress` every 2 s (`pollDownload()`), see
[server-and-shared.md](server-and-shared.md). Without qBittorrent the pre-show shows a generic "The feature will
begin shortly" and no automatic phases happen.

**Film shots** (`show.shot`): `push` (Film: the camera pushes onto the screen 10 s after the lights go down), `movie`
(Movie, no zoom: the film plays and the wide shot stays), `outro` (Film outro: eases back out while the film keeps
playing). `show.lightsOn` (Lights on, film plays) raises the house lights during the film, e.g. for the credits.
Changing phase resets both.

**Lights down/up crossfade** (CSS lines 37-50, `applyPhase()`, `scheduleDimDone()`):

- `#stage.lights-down` toggles. With dim art, a registered custom property `--dim` (`@property`, 0 → 1) transitions
  over 6 s, and every `.dim-art` element uses `opacity: var(--dim)`. One shared value means a dim piece that appears
  mid-fade (a chatter walks behind it) has the room's current level, not its own start value (owner fix,
  5 Nov 2026).
- `dim-ready` is added once the whole dim set (background, slices, door) has loaded, so a phase change never shows a
  half-loaded dim set.
- 6.5 s after the lights are fully down, `dim-done` hides the lit background and lit slices, so only one set is
  drawn.
- Without dim art (`has-dim-art` absent): a CSS `brightness(.45)` filter with a 6 s transition.
- Emotes and carried items get `brightness(.5)` in the dark.

**The pre-show** (`#preshow`, lines 164-178 and 294-520). A 960x540 flat page mapped onto the screen with
`matrix()` built from TL, TR and BL (the screen corners form an exact parallelogram, so BR matches too). It shows
whenever the phase is not `film` and `screen=green` is off. Three slides rotate every 8 s:

1. **Up next.** The winner of the newest film poll on dinkdonk.mov (`upcomingFilm()`: film polls only, skipped if
   it already shows up in ratings or history). Without one, the downloading title once Cinemeta found it. Without
   either, "Next movie coming up".
2. **Now loading.** The download: title, season/year/genres, poster and IMDb rating, percent (held at 99% until
   qBittorrent says complete), progress bar, ETA, a DGG meme, and chat's top emote riding the bar.
3. **In the audience.** End-credits roll of everyone seated, in their chat colours.

**Release lookup** (`parseRelease()`, `lookupRelease()`, `featureInfo()`). The torrent name is parsed (tracker
style "Russian / English (…) [year, …]" or scene style "Title.S03.1080p…"), then looked up on Cinemeta
(`https://v3-cinemeta.strem.io`, Stremio's public IMDb mirror, no key) with posters from `images.metahub.space`.
Results are kept in `localStorage` for a week per release name; a failed lookup retries after a minute.

## DGG jokes and memes on the loading screen

| Bit | Detail |
|---|---|
| Meme | `MEMES` (line 394), from `roxy3d/memes/SHORTLIST.md`: emote + caption, e.g. `WWWWaiting` "Feature in 5™", `NOTHINGBURGER` "Nothing ever happens.", `Clueless` "Seeding after the movie, right?". The next one each time the loading slide comes round. |
| Rider | chat's most-posted emote of the last 3 minutes hops along the progress bar (`topEmote()`, `ride()`); `dggL` when chat is quiet |
| Pops | while a download shows, emotes chat posts float up the screen's outer edges (max 6 at once, one per 0.9 s; `popEmote()`) |
| Wheelchair row | YEE emotes sit in the front row only (`YEE_EMOTES`) |
| Phones | a seated chatter who posts `chatty` messages in a minute in the dark gets their phone out (glowing) and a 🤫 shush from a janny or the usher (`noteMessage()`, `requestShush()`, `shush()`) |
| Usher | flashlight patrol in the dark; a chatter who talks gets the light on them and, with chance `kick`, is walked out "🔦 kicked" |

## Staff: jannies and the usher

**Jannies (DGG moderators)** (lines 1020-1121). Any chat message from a user with the `moderator` feature, tagged or
not, brings a `cpMOP` penguin wearing their name in through the entrance (`onModMessage()`, `addJanny()`). If the mod
was already seated as a chatter, that figure is removed. Up to 6 jannies, one per front-floor spot (`JAN_U`, `JAN_V`
in front of row B). Each mops a spot for 10-18 s and moves on (`janNext()`); their messages become bubbles; after
`janidle` (10 min) without a message they clock off back through the entrance (`janLeave()`). "🧹 janny on duty"
floats up when they come out of the tunnel.

**Bans and mutes** (`onPurge()`, `escort()`, `escortWalk()`, `leadOut()`). `core.js` sends `modAction`
(kind, target, mod) just before `purge`. A seated target gets "🚫 banned" / "🔇 muted"; the mod who did it walks over
if on duty, else the nearest free janny, else that mod is called in through the entrance if a spot is free, else
the chatter walks out alone. Anyone not yet seated (or in the queue) is removed at once.

**Usher** (lines 1343-1521). 4 s after the lights go down an usher (key `#usher`, the lobby usher's emote plus the
`cap_usher` item, no name) comes in. Patrol: up a stair aisle shining the flashlight along a row, or along the
cross-aisle (`usherNext()`). A seated chatter who talks in the dark gets a visit (`spotlight()`, `spotVisit()`); half
the time (`kick`) they are walked out. Shushes go to the usher when no janny is on duty. The usher never blocks
anyone and leaves when the lights come up. The beam is an SVG in `#names` (`updateBeam()`).

**Everyone leaves** (`stepHouseOut()`). Seated guests stand up one at a time (every 0.35-0.9 s) and walk out the way
they came. Staff are left alone. New arrivals wait until the next Seating or a reset.

## The film screen and OBS

The page never plays the film. In the `film` phase it draws the screen quad (`#screenq`) and, inside OBS, tells
`obs-bridge.js` where that quad is so OBS can pin the VLC capture onto it.

1. `bridgeConnect()` runs only when `window.obsstudio` exists (an OBS browser source) and `bridge` isn't `0`. It
   opens `ws://<host>:18790` and reconnects every 3 s.
2. The bridge sends `{ obs: true|false }`. While `obs` is true and the phase is `film`, the quad is filled black,
   so a frame of camera lag never flashes green. Otherwise it is the chroma green (`Cinema.green`).
3. `sendScreen()` (called on every camera step and phase change) sends
   `{ film, w: innerWidth, h: innerHeight, quad: [[x,y] TL, TR, BR, BL] }` in viewport px, using the same rounded
   numbers as the camera transform plus the letterbox offset. Unchanged frames are not re-sent.
4. The bridge converts to the shader's -100..100 frame, updates the "Corner pin (live)" filter and shows the film
   item only while `film` is true. Details in [server-and-shared.md](server-and-shared.md#obs-bridge-obs-bridgejs).

Without the bridge (a normal browser, or OBS with the bridge down) the screen stays green during `film`, for a
manual chroma key.

## Director and camera

`director` object (line 1844) and `stepCamera()` (line 1886). The camera is the lobby's: critically damped springs
(`damp()`), clamped so the view never leaves the stage, reset to the wide shot if a value ever goes NaN.

| Behavior | Detail |
|---|---|
| Automatic follow | on by default. The first one 45-75 s after load, then every `every` s × 0.85-1.2, at the next arrival after that time. Follows the walker from the door to the seat, holds 3.2 s after they sit (max 150 s), then eases back out. |
| Tunnel | while the followed walker is hidden, the camera frames the tunnel mouth `[2.1, 9.4, 8]` |
| Lead | the shot leads a little in the walking direction (smoothed velocity × 0.35, max 60/40 px) |
| Screen shot | Film (`push`): 10 s after the lights go down the camera eases onto the screen (zoom fits its bounding box × 0.94, 1-3) with a slow 3.5 s spring and stays. Automatic follows stop meanwhile; manual ones (F, R, panel) still cut away. |
| Outro | eases back to the wide shot; automatic follows resume after one interval |
| Zoom | `zoom` (default 1.85) for follows |

**Keys** (page focused; in OBS right-click the source → Interact): `F` follow the next arrival, `R` follow someone
now, `W` / `Esc` wide shot (also cancels the screen shot until the lights go down again), `D` director on/off.

## Control commands

The page subscribes to `GET /ctl/events?page=auditorium&id=<pageId>` (server-sent events) and posts its state to
`POST /ctl/state` every 1.5 s (lines 2018-2042). `control()` (line 1948) ignores any command whose `page` isn't
`auditorium` or whose `id` targets another screen. Message shapes and the panel are in
[server-and-shared.md](server-and-shared.md#control-protocol).

| `cmd` | Fields | Effect |
|---|---|---|
| `phase` | `value`: `seating\|dim\|film\|up` | set phase, auto off. Same phase again turns "Lights on" off; `film` again after Movie/Outro pushes in at once. |
| `movie` | | `film` without the push-in |
| `outro` | | ease back to the wide shot; shot becomes `outro` if in `film` |
| `phaseAuto` | `on` | automatic phases on/off |
| `lights` | `on` | house lights up during `film` (ignored in other phases) |
| `houseOut` | `on` | Everyone leaves on/off |
| `reset` | | everyone (staff too) removed, queue cleared, seats freed, bubbles cleared |
| `follow` | `nick` | follow that chatter |
| `random` | | follow someone now |
| `next` | | follow the next arrival |
| `wide` | | wide shot, cancel screen shot and pending follow |
| `director` | `on` | automatic director on/off (on: next follow within 20 s) |
| `every` | `value` (s) | follow interval, 30-1800 |
| `zoom` | `value` | follow zoom, 1.2-3 |
| `remove` | `nick` | remove that chatter (and from the queue) |
| `say` / `add` | `nick`, `text` | as if `nick` said `text` (first emote in the text, or the default emote, becomes their avatar) |

State posted (`postState()`): `id`, `page: 'auditorium'`, `ts`, `size`, `obs` (true inside OBS), `preshow`
(`phase`, `shot`, `lightsOn`, `houseOut`, `auto`, `download`, `alwaysGreen`), `house` (`capacity`, `occupied`,
`waiting`, `queueLimit`), `director` (`on`, `every`, `zoom`, `wantNext`, `following`, `nextIn`), `chatters[]`
(`nick`, `emote`, `status`, `followed`; queued arrivals have status `waiting outside`). A 404 from the server stops
the connection (an old server without `/ctl/`).

## Performance notes (from comments)

| Note | Where |
|---|---|
| No CSS filter at rest: an identity `brightness(1)` made every slice its own offscreen pass (QA 4 Nov 2026: 66 → 170 fps uncapped with ~60 chatters). Filters only apply where they change something. | CSS lines 37-42 |
| No `will-change` on walkers: a GPU layer per chatter forced the slices between them onto layers too (3 fps at 1.85× zoom with 60 chatters; ~95 fps without) | CSS lines 107-108 |
| Banded slices (~5 screens of pixels instead of ~25) and culling: only pieces with something behind them are displayed, so Chrome keeps a few hundred small images decoded instead of overflowing its image cache (was 4-15 fps with a full house) | `cullPieces()`, layout load |
| Door mask only on pieces that overlap the cutout | layout load, line 2083 |
| Once the dim set is fully up, the lit set is hidden (`dim-done`) so only one set is decoded | `scheduleDimDone()` |
| `style()` caches every style write per element; bubble sizes are measured in one batch after writes; name widths measured once | lines 194-199, `tick()`, `showNames()` |
| The rAF loop requests the next frame before running `tick()`, so an exception can't end it; a 40 ms timer drives `tick()` if rAF stalls (background tabs, headless screenshots) | `frame()` |
| Bounded memory: chat-emote list trimmed to 3 min, avatar checks capped at 256, queue at 270 | various |
| Full render resolution must stay (project rule): 2x art and devicePixelRatio × zoom are there so zoom-ins stay sharp. `maxres` exists but is off by default. | `dpr()` |

## Recipes

### Use a new draft number (same layout contract)

1. The draft's files go in `roxy3d/qa11/`: `cinema_draft_NN.png` (+ `@2x`), `cinema_layout_NN.json` with
   `page_layers` (slices with `pieces`, `dim`, `entrance_door`, `spawn`), and the folders it names.
2. Test it first: `auditorium-qa.html?draft=NN&everyone=1` (or the live page with `?draft=NN` in a normal browser
   tab, not OBS).
3. Check: walkers hidden in the tunnel and behind the next row, door animation without a closed-door ghost, the
   lights-down fade without blocks, the screen polygon on the screen, and no console errors.
4. Make it the default: change `'13'` in the `DRAFT` line (line 203). Keep the shape
   `? q.get('draft') : 'NN'` because `package/art.js` parses it.
5. Track exactly the files the page loads (`roxy3d/qa11/` is git-ignored as a folder): the recipe in
   `README.md` ("Adding auditorium art").

### Use a new layout (rows, aisles or tunnel moved)

The JSON drives rows, seats, treads, the entrance route, the screen and the camera. These values are hard-coded in
the page and must be checked against the new layout:

| Constant | Meaning | Where |
|---|---|---|
| `3.475`, `15.15` | u of the main and right stair aisles | `routeTo()`, `aisleTo()`, `janNext()`, `janLeave()`, `visitPath()`, `usherNext()` |
| `24` | cross-aisle floor z | `routeTo()`, `aisleTo()`, `visitPath()`, `usherNext()` |
| `(14.1 + 4.5) / 2`, `u0/u1` 4.5-14.1 and 16.0-17.0 | middle of the main block; the usher's sweep ranges | `chooseSeat()`, `usherNext()` |
| row weights `B … I` | seat preference per row name | `chooseSeat()` |
| `rows[0]` | the front (wheelchair) row and the janny floor | `chooseSeat()`, `janNext()` |
| `u < 2.9 && v > 8.8 && z < 10` | tunnel test | `step()` |
| `[2.1, 9.4, 8]` | tunnel mouth the camera frames | `stepCamera()` |
| `JAN_U`, `JAN_V`, `2.9` | janny spots and the point where they leave the aisle | lines 1027-1028, `janNext()` |
| `SIT_DV`, `BACK_Z`, `BACK_DV`, `LEG_DV`, `SIT_Z` | seat geometry (cushion, backrest top, legroom) | line 592 |
| block names `left`, `main`, `right` | which aisle a seat uses | `routeTo()`, `chooseSeat()` |

Layout changes start as a labelled blockout the owner approves, before any styled draft (see
`docs/art-pipeline.md`).

### Other common changes

| Change | Where |
|---|---|
| A new loading-screen meme | add `[emote, caption]` to `MEMES`; check the emote exists on DGG |
| Pre-show slide texts | the `#preshow` HTML and `tonight()` |
| Default follow zoom / interval | `ZOOM`, `director.every` (or `zoom=`, `director=` in the OBS URL) |
| Phase timing | `autoPhase()` (90% → dim, completed + 10 s → film), `director.screenAt` (+10 s push-in) |
| Fade length | the three `6s` transitions in CSS, plus the 6500 ms in `scheduleDimDone()` and `cullPieces()` |

## Looked wrong or inconsistent (5 Nov 2026)

- `green=off` doesn't turn the screen off here: `screenFill()` maps `off` to `#00ff00`.
- The header comment misses `phones=`, `sitz=` and `sitscale=`, and still lists `demo=1` (against the project's
  real-chat rule).
- `auditorium-qa.html` is behind the live page (see the table at the top).
- `cinema_layout_13.json` describes `depth_key` and `z_index_formula`, but the page hard-codes the formula and
  reads only `key_z_divisor`. Changing the formula in the JSON has no effect.
- The dim set's own `door_static_cutout_file` is never read; the lit cutout masks the dim slices too. Fine while
  both cutouts are the same shape.
