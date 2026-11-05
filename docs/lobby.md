# Lobby (`lobby.html`)

Developer documentation for the lobby scene of DinkDonk Cinema. Written from the code as of 5 Nov 2026.

- `lobby.html` was renamed from `roxy.html` on 5 Nov 2026. `roxy.html` is now a redirect stub that keeps the
  query string (`location.replace('lobby.html' + location.search + location.hash)`). Don't put code in it.
- `lobby-qa.html` is the QA copy. Try risky changes there first. It can lag behind or run ahead of `lobby.html`.
- Line numbers like `lobby.html:1600` point at the 5 Nov 2026 file and drift as it changes. Search for the
  function or constant name next to them.

Related: [server-and-shared.md](server-and-shared.md) (server, `SB`, `Cinema`), [art-pipeline.md](art-pipeline.md)
(how the art packs are made), [auditorium.md](auditorium.md).

---

## 1. The scene and how the page is built

A pre-rendered isometric late-90s cinema on a rainy night, inside a city block. The street is in front, with
traffic, a bus stop and taxis. Glass doors lead into the lobby, which has the box office (rope queue lane, two
windows), the snack bar (three registers), an arcade cabinet, a bench and the usher's podium at the back corner.
Behind the usher, a corridor leads to the screen doors. With the current art (layout 3), the right wing has
screens 1-3 and the left wing is the restroom. DGG chatters walk in as small figures wearing their emote. They
buy a ticket, sometimes get popcorn, talk in speech bubbles, and go through their screen's door.

The art is a Blender render (`roxy3d/out10/`, plus rain/mist passes in `roxy3d/out10mist/`). Everything that
moves or changes (people, vehicles, signs, rain extras, camera) is a live DOM/canvas/WebGL layer on top.

### DOM (`lobby.html:160-176`)

```
#stage                      mounted and scaled by SB.mountStage (shared/core.js)
  #cam                      camera: one CSS transform (translate + scale) for the whole world
    canvas#bg               flat fallback background (only without art)
    img#bgimg               background still (base.png when the light loop runs, else a lit still)
    #world                  every depth-sorted thing: occluders, walkers, vehicles, signs, NPCs, sprite sheets
    img#glow                old static glow layer (only for art without a light loop)
    video#loop              6 s light loop (plus-lighter)
    canvas#mist             WebGL splash mist (off by default)
    canvas#rain             procedural 2D rain (only while the video rain isn't running)
    video#rainfg            baked foreground rain video (hidden and fed into #rain2 when that runs)
    canvas#rain2            WebGL extra rain + weather (+ the rain_fg video frames)
    #hang                   flat-fallback hanging signs, restroom sign
    #fx                     floating texts, flying tickets
  #bubbles                  speech bubbles (screen space, outside the camera, never zoomed)
```

### Script sections, in file order

| Lines (approx.) | Section | Key names |
|---|---|---|
| 1-17 | Header comment (partial list of URL options) | |
| 181-273 | Setup: helpers, `q`, `ART` folder, iso projection, floor plan, layouts | `P`, `depth`, `DOORS`, `LAYOUTS`, `useLayout`, `CAP`, `HARD_CAP`, `JAYWALK` |
| 275-467 | Flat fallback drawing (sky, street, building, doors) | `drawSky`, `drawStreet`, `drawBuilding`, `redrawBg`, `dpr` |
| 469-596 | Flat fallback props, cut into depth-sorted chunks | `addProp`, `redrawProps`, `buildProps` |
| 598-653 | Door signs, posters, hanging signs | `signs`, `hangSign`, `flatSigns`, `wcSign`, `signMeta` |
| 655-767 | LED dot-matrix door signs | `FONT`, `textCols`, `makeLed`, `stepLeds` |
| 769-788 | Restroom light, poster bulb chase | `makeWcLights`, `chaseUntil`, `bulbKind` |
| 790-816 | Rooms (films) from dinkdonk.mov | `applyRooms`, `Cinema.onRooms` |
| 818-1088 | Walkers: figures, emotes, items, staff, floats, bubbles | `makeFigure`, `setEmote`, `checkEmote`, `placeStaff`, `itemEl`, `placeItem`, `say`, `dropBubble` |
| 1090-1420 | Routes: doors, snack bar, gate, restroom, bench, queue, quitting, bus, umbrellas | `doorSteps`, `serveSnacks`, `afterTicket`, `serveGate`, `tryWC`, `tryBench`, `joinQueue`, `giveUp`, `serveQueue` |
| 1421-1586 | Arrivals, crowd control, removal | `spawn`, `crowdSkip`, `retire`, `enforceCap`, `removeWalker` |
| 1588-1877 | Traffic | `setImg`, `vehSprites`, `addVehicle`, `pickRide`, `stepTraffic`, `vehRain`, `runOver`, `place` |
| 1879-1945 | Sprite sheets, door animations, umbrella grip | `validSheet`, `sheetStyle`, `sheetShot`, `playDoor`, `stepShots` |
| 1947-2208 | NPCs: cat, cpMOP penguin, jannies, 3D janitor | `makeNpc`, `stepCat`, `stepMopper`, `onModMessage`, `addJanny`, `janNext`, `janLeave`, `stepJanitor` |
| 2210-2501 | Per-frame walker update, names, bubble layout | `blockedAhead`, `stepPace`, `stepPlan`, `frontV`, `drawFigure`, `showNames`, `placeBubble`, `layoutBubbles` |
| 2503-2537 | Procedural 2D rain | `drawRain`, `setRain` |
| 2539-2712 | Splash mist (WebGL) and the shared WebGL helper | `MIST_FS`, `glLayer`, `drawGL` |
| 2714-2994 | Extra rain + weather (WebGL) | `WEATHER`, `stepWeather`, `fgToRain2`, `uploadFg`, `RAIN2_FS` |
| 2996-3018 | Door glow, arcade flash | `doorGlow`, `arcadeFlash` |
| 3020-3144 | Talk groups and solo speech | `SPOTS`, `HANG_P`, `queueLine`, `soloSpeech`, `hangOut`, `stepGroups` |
| 3146-3215 | Layout 3 (pass 10) and the restroom | `setupLayout3`, `tryRestroom` |
| 3217-3314 | Camera and zoom director, keys | `cam`, `director`, `toScreen`, `stepCamera`, `startFollow` |
| 3316-3384 | Control panel link | `statusOf`, `control`, SSE + `postState` |
| 3386-3455 | Main loop | `frame`, `loop`, 40 ms fallback timer |
| 3457-3714 | Art loading | `loadArt`, `playLoop`, `setupArt`, `stepPropLoops`, `applyArtRes` |
| 3716-3734 | Boot | async IIFE |

### Setup order

1. **Module scope** (top to bottom): constants and `useLayout(1)`; door signs and posters are created for five
   doors; handlers are registered (`SB.on('emotes', placeStaff)`, `Cinema.onRooms`, `Cinema.onWalkIn(spawn)`,
   `Cinema.onPurge`, `Cinema.onCombo`, `SB.on('msg', onModMessage)`); the mist and extra-rain passes start
   loading (async); the `raintune` slider is added; key handler; control SSE; the 40 ms fallback timer.
2. **Boot IIFE** (`lobby.html:3716`):
   1. `loadArt()` fetches `ART/manifest.json` (5 s timeout).
   2. `useLayout(?layout || manifest.layout || 1)`.
   3. `setupArt(m)` with art, else `buildProps()` (flat fallback).
   4. `SB.on('resize', ...)`: re-picks @2x art, swaps the light loop, refreshes sprites. In flat mode it redraws
      the canvases.
   5. `SB.mountStage($('stage'), { cover: FIT_COVER })`, which fires the first `resize`.
   6. `requestAnimationFrame(loop)`, then `SB.start()`. That loads emotes, flairs and `emote-facing.json`, then
      connects to the chat relay (or demo traffic with `?demo=1`, which is not allowed for showing or QA; see
      `AGENTS.md`).

### Main loop (`frame(t)`, `lobby.html:3389`)

`dt` is clamped to 0.1 s. Order: `stepCamera` → `serveQueue` → `serveSnacks` → `serveGate` → `stepGroups` →
`stepTraffic` → `stepPropLoops` → `stepLeds` → `stepShots` → `stepCat` → `stepJanitor` → `stepPace` → for each
figure: `stepPlan`, `drawFigure`, pending/solo speech, `placeBubble` → staff (`drawFigure` + `placeBubble`) →
`showNames` → `layoutBubbles` → door-sign pulse → `drawRain` (if on) → mist → extra rain (`stepWeather`, then
draw at the rain step rate).

`loop(t)` wraps `frame` in try/catch, so an exception never stops the screen. A `setInterval` (40 ms) drives
`frame` when rAF stalls for more than 150 ms (throttled or background tabs, headless screenshots).

### Walker plans

Each walker has `w.plan`, a list of steps that `stepPlan` runs one per frame (up to 8 instant steps per frame):

| Step | Meaning |
|---|---|
| `{ to: [u, v], slow? }` | walk in a straight line (no pathfinding; routes are hand-placed waypoints) |
| `{ wait: s, start?, end? }` | wait, with optional callbacks |
| `{ until: () => bool }` | hold until true |
| `{ alpha: a }` | wait until the fade (`w.alphaT`) reaches `a` |
| `{ call: fn }` | run `fn(w)`; it may replace or prepend to `w.plan` |

Speed: 2.0 tiles/s × `pace`, 0.9 for `slow`, 3.0 when `hurry`. `pace` eases between 0.75 and 1.0 as the live
count goes from 70% to 85% of `CAP` (`stepPace`). `blockedAhead` makes a walker wait behind someone on screen
for up to 1.5 s, then they pass anyway.

---

## 2. URL options

The header comment lists only some of these. This table is from the actual `q.get` / `q.has` calls in
`lobby.html`, `shared/core.js`, `shared/cinema.js` and `shared/live.js`.

### lobby.html

| Option | Default | Effect | Where |
|---|---|---|---|
| `artdir=<name>` | `out10` | Art pack folder under `roxy3d/` (non `[a-z0-9_-]` stripped), e.g. `out8b` | `ART`, :202 |
| `art=flat` | off | Skip the art; flat canvas blockout | `loadArt`, :3461 |
| `layout=<n>` | manifest `layout`, else 1 | Force a queue/staff layout (1, 2, 3). Layout 3 setup (`setupLayout3`) still only runs when the manifest says `layout: 3` | :3718 |
| `loop=0` | on | No light loop: a lit still (`lit_bg_dry` > `lit_bg` > `full`) + procedural rain | `setupArt` |
| `loop2x=0` | on | Keep the 1080p light loop even over 4K art | `setupArt` |
| `wet2x=1` | off | Load @2x `wet_*` prop-loop sheets too (heavy, see section 8) | `applyArtRes` |
| `maxres=<height>` | off (no cap) | Cap art sharpness to this output height (e.g. 1080: never @2x art or the 4K loop). Clamped 540-4320 | `MAXK`, :321 |
| `fit=cover` | off (letterbox) | Fill a non-16:9 source to its larger side and crop; the camera and bubbles stay inside the visible part | `FIT_COVER`, :315 |
| `fitx=<stage x>` | 960, or 1040 with `fit=cover` | Wide-shot centre x | `WIDE_X`, :316 |
| `director=0` / `director=<s>` | on, 150 s | Off, or seconds between automatic follow shots (30-1800) | `DIRECTOR_ON`, `director.every` |
| `zoom=<x>` | 1.85 | Follow-shot zoom (1.2-3). Also sets how much art headroom `dpr()` asks for | `ZOOM`, :312 |
| `bubbles=<n>` | 8 | Max speech bubbles on screen (2-14); the oldest fades for a new one | `MAX_BUB`, :1056 |
| `crowd=<n>` | 14 | People outside/in line before new chatters are thinned out (4-60); `crowd=0` = never | `CROWD`, :1497 |
| `quit=<p>` | 0.06 | Chance someone in the ticket line gives up and goes home (0-1; `quit=1` for testing) | `QUIT_P`, :1289 |
| `janitor=always` / `janitor=3d` | none | Old unnamed cpMOP penguin always present / the rendered 3D janitor. Default: only mods' jannies | `setupArt`, :3635 |
| `janidle=<s>` | 600 | Seconds without a message before a janny clocks off (20-3600) | `JAN_IDLE`, :2124 |
| `mist=1-4` | 0 (off) | Splash-mist sample style: 1 sparkle, 2 edge spray, 3 lamp-lit mist, 4 wind sheets | `MIST`, :2546 |
| `mistgain=<x>` | 1 | Mist brightness (0.1-4) | `MIST_GAIN` |
| `mistdir=<name>` | `out10mist` | Folder with the surface passes (`catch`, `rim`, `light`, `height` .png). Also used by the extra rain | `MIST_DIR`, :2548 |
| `morerain=0-4` | weather (internal 5) | 0 = no extra rain; 1 steady, 2 downpour, 3 curtains, 4 deluge (fixed) | `RAIN2`, :2732 |
| `moreraingain=<x>` | 1 | Extra-rain brightness (0.1-4) | `RAIN2_GAIN` |
| `weather=<x>` | 1 | Weather clock speed-up (0.1-100), for testing | `WEATHER_SPEED` |
| `rainfps=<n>` | 24 | Extra-rain steps per second (0-120); 0 = every display frame | `RAIN2_FPS` |
| `rainspeed=<x>` | follows weather | Fix the streak fall speed (0.1-2) | `rainSpeedFixed`, :2739 |
| `raintune=1` | off | On-screen slider for the rain speed (debug) | :2741 |
| `ctl=0` | on | Don't connect to the control panel | :3365 |

### shared scripts (used by the lobby)

| Option | Default | Effect | Where |
|---|---|---|---|
| `everyone=1` | off | Every chatter walks in | `shared/cinema.js:35` |
| `tag=<nick>` | the host's nick (default in `cinema.js:36`) | Only messages mentioning this nick (or from it) walk in | `cinema.js:36-38` |
| `demo=1` | off | Fake chat traffic. Not allowed for showing or QA (`AGENTS.md`) | `core.js:20` |
| `relay=<host:port>` | local relay, port 18765 | Chat relay WebSocket | `core.js:22` |
| `live=1` | off | Reload when the page or a shared file changes | `shared/live.js` |
| `cmds=off` | on | Ignore `!commands` (the lobby registers none) | `core.js:31` |
| `green=off\|<hex>` | `#00ff00` | Parsed into `Cinema.green`, **not used by the lobby** | `cinema.js:180` |

`f`, `chat`, `chatbar`, `chatcrop`, `title`, `sub` and `until` are read by `core.js` but have no effect in the
lobby (it mounts no chat panel and shows no timer).

---

## 3. Coordinates and compositing

### Stage

The stage is a fixed 1920×1080 px world. `SB.mountStage` (`core.js:50`) scales `#stage` to the window: letterbox
(`Math.min`) or `cover` (`Math.max`, sides cropped). `SB.view` is the visible part in stage px
`[x0, y0, x1, y1]`. `lobby.html` reads it through `view()`.

### Iso projection (`lobby.html:204-211`)

```js
const P = (u, v, z = 0) => [900 + (u - v) * 60, 350 + (u + v) * 30 - z];
const depth = (u, v) => 1000 + Math.round((u + v) * 100);
```

- `u` runs down-right, `v` runs down-left (1 tile = 60 px across, 30 px down), `z` is height in px.
- Screen x grows with `u - v`. That is why facing uses `du - dv`.
- Floor plan (tiles): building `u 0-13, v 0-9`. Glass front at `v ≈ 9`, sidewalk `v 9.15-10.5`, curb `10.5-10.6`,
  road `10.6-13.5` (centre line `v 12`). Near lane `v 11`, far lane `v 12.75` (`LANES`).
- Named points: `G = [3.7, 3.7]` (usher gate), `J = [1.4, 1.4]` (corridor junction), `GATE_OUT = [3.75, 2.45]`
  (the way round the restroom corner), `HUB = [8.6, 6.6]` (NPC routing hub), `ARCADE = [12.95, 7.85]`.
- `DOORS` (`:219`): wall `u` (left wing, `at` = v) or wall `v` (right wing, `at` = u). Layout 3 removes the
  left-wing ones (`setupLayout3`).

### Depth sorting

`#cam` has a transform, so it is the stacking context for everything in the world. `#world` has no z-index of its
own, so its children's `z-index` values compete directly with the `#cam` layers.

| z-index | What |
|---|---|
| (none) | `#bg`, `#bgimg` (DOM order, bottom) |
| 1 | `#glow` |
| 2 | `#loop` (light loop, plus-lighter) |
| 3 | `.doorglow`, arcade flash; prop loops without their own `z_index` |
| 4 | vehicle wake |
| 500 / 600+ | flat posters / door title signs |
| 900 / 901 / 902 | door animations (default) / LED signs / restroom light |
| ~1000-4500 | `depth(u, v)`: occluders (manifest `z_index`), walkers, vehicle slices, NPCs; wet prints `depth-2`, splashes `depth-1` |
| 69990 / 70000 / 70001 / 70002 | `#mist` / `#rain` / `#rainfg` / `#rain2` |
| 80000 / 85000 | `#hang` / `#fx` |
| 86000 | `#bubbles` (outside `#cam`, screen space) |

- **Occluders** (manifest `occluders`): each is an `<img>` at its `x, y, w, h` with its `z_index`. With
  `depth_slices`, every slice is its own `<img>` with its own z-index. The whole unsliced file goes underneath at
  the lowest slice depth to fill the antialiased seams between slices (`setupArt`, `:3554-3576`). There is one
  special-case clip for `occ_restroom_side_wall_01.png` (`:3572`).
- **Walkers** use `depth(u, frontV(u, v))`. `frontV` (`:2282`) cheats near the glass front (u 2.9-13.1): outside
  always in front of the glass slices, inside always behind them.
- **Vehicles** are drawn as depth slices along their length (`slices[].du`), each with its own z-index (`place`,
  `:1854`). Roof-rain loops sit just above their slice; tyre spray goes above the whole body; the wake goes at z 4.
- **Flat fallback**: `addProp` cuts every prop into ≤1×1 tile chunks, each a clipped canvas with its own depth.

### Camera

`#cam` gets `translate(960 - x·z, 540 - y·z) scale(z)` (`stepCamera`). `toScreen(x, y)` converts world px to
screen px; bubbles and on-screen checks use it.

### Art resolution (`dpr()`, `:322`)

`dpr() = min(MAXK, stageScale × devicePixelRatio × (director on ? ZOOM : 1))`. @2x art is used when
`dpr() > 1.3` and the manifest has `scale2x`. Canvases (flat bg/props) are sized to `dpr()` too.

---

## 4. Art loading

### manifest.json, as the page uses it

`loadArt` accepts a manifest when it has `bg` or `base` **and** an `occluders` array. Otherwise the page falls back
to the flat canvas art. Optional subsystems switch on only when their entries are complete (`validSheet` checks
`file`, `anchor[2]`, `frames`, `columns`, `frame_width`, `frame_height`).

| Field | Used for |
|---|---|
| `layout` | `useLayout`; `3` also runs `setupLayout3` |
| `scale2x` | allows @2x files (`name.png` → `name@2x.png`, or `file_2x` fields) |
| `bg`, `base`, `full`, `lit_bg`, `lit_bg_dry`, `glow` | background still: `base`/`bg` under the light loop, else `lit_bg_dry` > `lit_bg` > `full` |
| `light_loop`, `light_loop_2x` | `#loop` video (1080p / 4K) |
| `rain_fg` (`file`, `fps`) | foreground rain video |
| `occluders[]` (`file`, `x,y,w,h`, `z_index`, `depth_slices[]`) | depth-sorted scenery |
| `led_signs[]` (`door`, `wall` u0/v0, `along`, `z_px`, `offset`, `cols`, `rows_px`, `dot_pitch_px`) | LED door signs |
| `poster_frames[]` (`screen`, `wall`, `along`, `z_px`, `offset`) | poster placement on the wall plane |
| `marquees[]` (`screen`, `bottom_center`, `inner_size`) | older art: title boxes |
| `wc_indicator` (`vacant`, `occupied`) | restroom light |
| `prop_loops[]` (`name`, `file`, `x,y,w,h`, `frames`, `columns`, `fps`, `z_index`, `blend`) | popcorn, menu boards, arcade screens, poster bulbs, `wet_*` highlights, water on the glass |
| `door_anims[]` (`door`, `x`, `y`, sheet fields) | screen doors (keys `1`, `2`, ...) |
| `restroom` (`door`, `outside`, `inside`, `stalls[].spot/route_points/door_anim`, `sinks`, `dryer`, `door_anim`) | layout 3 restroom |
| `vehicles.{bus,taxi,sedan_a,sedan_b}.{+u,-u}` | traffic sprites, slices, lights, `roof_rain`, `spray`, `wake`, `length_tiles`, `width_tiles`, `door_open` |
| `lanes`, `arrival_stops` | lanes and bus/taxi stop points (far lane forced to 12.75 when ≤ 12.05) |
| `tyre_spray` | one-shot spray when a vehicle has no rendered spray loop |
| `cat`, `janitor` | NPC sprite sheets |
| `umbrella` (`colors`, `open`, `fold`, `wet`) | umbrellas |
| `items` (`popcorn`, `soda`, `stub`, `ticket`, `cap_cashier`, `cap_usher`, `wet_print`) | carried items and caps |

Fields in `out10/manifest.json` that the page does **not** read: `staff_positions`, `customer_positions`,
`queue`, `doors`, `bus_shelter`, `ad_surfaces`, `baked_signs`, `render_layers`, `projection` and the various
`*_contract` notes. Staff, queue and door positions are hard-coded in `LAYOUTS` / `DOORS` and must be kept in
step with the art by hand.

### @2x selection

- `applyArtRes` (`:3696`): background and occluders swap `.png` for `@2x.png` when `scale2x && dpr() > 1.3`, and
  fall back to 1x on error. Prop loops use `file_2x`, except `wet_*` sheets unless `wet2x=1`.
- `setImg(im, file, file_2x, two, fail)` (`:1600`): the same @2x→1x fallback for items, vehicles, umbrellas and
  lights. `fail` runs when even 1x fails (a vehicle that can't load is removed).
- `sheetStyle` probes a @2x sheet and falls back to 1x.
- It is re-applied on every `resize` (OBS source size change).

### Video loops (`playLoop`, `:3472`)

- First frame within 6 s, or the loop is dropped. A stall while visible is nudged every 3rd check (2 s interval)
  and dropped after 9 stuck checks (~18 s). A dropped video is detached (`removeAttribute('src')`, `load()`).
- The light loop is 4K when the window-derived scale × DPR × zoom is > 1.3 (the 4K base needs the 4K loop as its
  exact complement). `loopSwap` switches it on resize.
- Light loop dead → background becomes the lit still, `rain_fg` is dropped, procedural rain turns on.
- `rain_fg` dead → procedural rain over the still-running light loop.
- `setRain(!(baseOk && (fgOk || !hasFg)))`: the 2D `#rain` canvas only draws when the video rain isn't fully
  running. It also draws during loading and in flat mode.

### Rain and mist layers

| Layer | Default | Source | Notes |
|---|---|---|---|
| Baked rain in `light_loop` | on | Blender | downpour, splashes, gutters, reflections |
| `rain_fg` video | on | Blender | in front of people and cars; fed into `#rain2` as a texture when that runs |
| `#rain` 2D canvas | only as fallback | `drawRain` | 520 drops at 960×540, clipped to outside the building |
| `#rain2` extra rain | on (weather) | `RAIN2_FS` + `out10mist/light,catch,height.png` | streaks lit by the light pass; a mask keeps it off the roof area and the dry strip at u 13-15.6 |
| `#mist` splash mist | off | `MIST_FS` + `out10mist/catch,rim,light,height.png` | samples only (`mist=1-4`) |

The extra-rain mask is built once on load (`:2760-2826`): red = extra rain may fall, green = baked `rain_fg` shows.
"Air" light is filled in under the glass and walls from a blurred light pass divided by blurred coverage.

### Weather (`WEATHER`, `stepWeather`, `:2724-2909`)

| State | fine | near drops | gust curtains | crowns | streak speed | odds |
|---|---|---|---|---|---|---|
| light | 0.35 | 0 | 0 | 0 | 0.20 | 2 |
| steady | 1 | 0 | 0 | 0 | 0.26 | 3 |
| downpour | 1 | 1 | 0 | 0 | 0.34 | 2 |
| curtains | 1 | 0.7 | 1 | 0 | 0.30 | 1.5 |
| deluge | 1.15 | 1.1 | 0 | 1 | 0.40 | 1 |

- Starts at `steady`. Each state holds 40-120 s, then a weighted pick of another state crossfades in over 12-20 s
  (smoothstep). `weather=<x>` scales both clocks.
- The first four numbers go to the shader as `uW` (intensity mix). The fifth is the streak fall speed:
  `rainClock += dt × rainSpeed`, sent as `uS`. `rainspeed=` or the `raintune` slider override it.
- `morerain=1-4` pins steady/downpour/curtains/deluge with no drift.
- The extra rain is redrawn at `rainfps` steps per second (24 by default, like the baked loops). When `rain_fg` is
  in the pass, new video frames (via `requestVideoFrameCallback` when available) are the steps. If the video
  stalls for >120 ms, the page clock takes over.
- WebGL context lost → `#rain2` is hidden and `rain_fg` shows on its own again.

### Fallback art

With `art=flat`, no or invalid manifest, or a fetch over 5 s: `buildProps()` + `redrawBg()` draw the
pass-1 blockout (sky, street, building, five doors, flat signs), with the procedural rain. Layout 1 is used.

---

## 5. Chatters

### Who walks in

`shared/cinema.js` decides (`SB.on('msg')`, `:144`):

- Default: only messages that mention the host nick (with or without `@`), plus the host's own messages.
- `tag=<nick>` changes the nick. `everyone=1` lets everyone in. `demo=1` also lets everyone in unless `tag=` is
  set.
- Moderators (`features` has `moderator`) never walk in as customers. They become jannies (see below)
  (`spawn`, `:1422`).
- Crowd control (`crowdSkip`, `:1494`): with `CROWD` (14) or more people outside or in line, only every 2nd new
  chatter walks in; every 3rd from 1.5× `CROWD`; every 5th from 2× `CROWD` or at `CAP`. The tag nick always walks
  in. Chatters already on screen are never skipped.
- Someone already on screen who talks again keeps walking: their emote updates and the line is queued. Their room
  can still change until the door is locked at the usher. Someone already going through a door gets a new walker.
- MUTE/BAN → `Cinema.onPurge` removes that nick at once.

Caps: `CAP` 40 (above it, someone is hurried past the line), `HARD_CAP` 55 (above it, someone fades out), and at
most 80 figures in the DOM (the oldest go).

### Emote choice and size

- `cinema.js`: the first emote in the message that works as a body, else their last used one, else
  `Cinema.defaultEmote(nick)` (stable hash into a pool). Square "picture" emotes (border-pixel check through
  `/dgg/emote-img`) and `JARVIS` are kept off bodies.
- `setEmote` (`:909`): height `EH` 50 px, width capped at 74 px. Contact shadow sized to the footprint.
- `checkEmote` (`:889`): if the emote image fails, show `?` and retry after 5/15/30/60/120/300 s. Chrome
  otherwise keeps a failed CSS background broken.
- **Facing**: `shared/emote-facing.json` maps emote → `left` / `right` / `front`. `SB.faceEmote(el, name, dirX)`
  mirrors with `scaleX(-1)` so the emote looks the way it walks (`dirX = du - dv`). `front` and unknown emotes are
  never mirrored. Staff face their customers (`faceStaff`).
- Tier-5 subs get the moving rainbow name (`.rbt`). Name colors come from `core.js` `flairColor`.
- Combos: everyone wearing the combo emote jumps for 2.6 s (`Cinema.onCombo`).

### Arrival (`spawn`, `:1421`)

| Way | Chance | Details |
|---|---|---|
| Bus | 65% while a bus is coming or stopped with time left, max 6 riders | Hidden until the bus stops, step out at `STOPS.bus.door_ground` 0.3 + 0.9 × n s apart. 40% chance of "thanks driver!" |
| Taxi | 10% of the rest, if no taxi is already coming | Spawns a `+u` taxi that stops at `STOPS.taxi.vehicle_centre` |
| On foot | otherwise | From the left (u −6) or right (u 16.5), staggered by 1.1 tiles per arrival within 1.5 s |
| Jaywalk | 6% of walkers (`JAYWALK`), only with vehicle art | Walk along the road lane; traffic doesn't stop (`runOver` → "BONK", fade out) |

Everyone gets an umbrella outside (rendered sprite, a wet 24 fps loop when available, else a CSS shape). It folds
with a one-shot when they step under the roof (`drawFigure`). Coming in from the rain leaves 4 wet footprints that
dry in 7 s (max 30).

Then: a sidewalk lane `v 9.78-10.05` → maybe a talk group outside (`hangOutside`) → the entrance (`u ≈ 9.5`,
`v 9.45` → `8.6`) → `joinQueue`.

### Route through the lobby (layout 3)

1. **Bench** (`tryBench`): 10% chance, only if the bench is free, the line is ≤3 and they aren't in a hurry. They
   wait for the next person to come in (a "friend") or 16 s, then join the line.
2. **Ticket line** (`joinQueue`, `serveQueue`): rope lane entered at its far end `queueEntry [9.3, 7.4]`. Slots
   `L.slot(i)`: 7 in the lane, then a second row at `v 8.25`. `qmax` 14. If the line is full, they're in a hurry,
   or the house is at `CAP`, they skip it with a stub in hand. Window 1 always serves; window 2 opens while ≥3 wait.
   Service time is `max(0.8, 2.6 − 0.3 × line)` s. A ticket flies from the cashier; the chatter gets a stub.
3. **Quitting** (`giveUp`): `quit` chance (6%) per person in line, after 2.5-7 s. They leave by the lane's open
   end, wait at the bus stop, and board the next bus (one is called early if none is due). Without bus art they
   walk off along the sidewalk.
4. **Detour** (`afterTicket`): `popcorn` (12% from `cinema.js`) → the shortest snack line (max 3 per register,
   2.2 s, "+1 POPCORN", popcorn or soda in hand). `arcade` (~7%, if free) → 3-6 s on the cabinet; 15% "NEW HIGH
   SCORE" (hi-score screen for 3.5 s), 35% "GAME OVER". `bathroom`: ~16% with the layout-3 restroom (`cinema.js`
   sends another ~5%).
5. **Lobby talk group** (`hangOut`).
6. **Usher gate** (`joinGate`, `serveGate`): the head of the line steps up to `G`, the others hold at
   `L.gateSlots`. The usher hops, the stub flies to the usher, and a ◀ / ▶ arrow shows the wing (0.7 s, 0.2 s
   when hurried). The door is locked here (`lockDoor`).
7. **Past the gate**: `GATE_OUT` → `J` → corridor talk group (`hangHall`) → restroom if their detour says so →
   their door (`doorSteps`).
8. **Restroom** (layout 3, `tryRestroom`): door → a free stall (hidden 3-6 s, stall door animates) → sink (always,
   if sinks exist) → dryer (50%) → out ("much better"). If all stalls are taken, they skip it. The light shows
   OCCUPIED only when every stall is taken. Without `restroom` data, the older one-person WC (`tryWC`) is used.
9. **Door** (`doorSteps`, `startEnter`, `finishEnter`): walk to `0.55` tiles from the wall, the door animation
   plays (held open while more people arrive), fade out at `0.1`. The sign's count goes up by 1 and flashes, a
   warm glow spills out, and the poster bulbs chase for 4 s. Then the walker is removed.

Room choice: `cinema.js` picks a room index 0-4 (regulars keep theirs 70% of the time). The lobby maps it to a door
with `room % DOORS.length`.

### Talk spots and speech

Speech only happens in talk groups or, outside a group, on its own after a delay (owner, 02 Nov).

`SPOTS` (`:3030`, replaced in `setupLayout3`, `:3181-3186`):

| Kind | Centers (u, v) | Radius | Stop chance (has lines / quiet) |
|---|---|---|---|
| `lobby` | [10.8, 7.2], [11.0, 5.35], [5.9, 8.35] (layout 3) | 0.42 | 1 / 0.5 |
| `outside` | [6.8, 9.5], [11.9, 9.5] (layout 3 only) | 0.34 | 0.5 / 0.35 |
| `hall` | [6.3, 0.85], [9.7, 0.85] (layout 3 only) | 0.28 | 0.7 / 0.4 |

- Each kind is visited once per walker. A group has at most 4 members, placed on `RING` (left, right, back,
  front × radius).
- Turns: someone with a saved line speaks every 2.2-3.4 s when ≥2 members are there. The same speaker doesn't
  go twice in a row if others have lines.
- Leaving: nothing left to say and past `stayT` (9-16 s), alone for 10 s (lobby) / 7 s (outside, hall), 45 s max,
  or hurried.
- Alone in a lobby group with something to say for 7 s → they go and talk to a mopping janny (one listener each).
  The janny stops mopping while listened to.
- `queueLine`: every message is said once, in order. A backlog over 4 says the oldest at once.
  `soloSpeech`: outside a group, 1.2 s after arrival or after their last bubble has been read.
- `say`: a bubble only for someone on screen (else it waits in `w.pending`). Bubbles last 5.5 s and fade in over
  0.25 s; the name heads the bubble. At most `MAX_BUB`.

### Bubble placement (`placeBubble`, `layoutBubbles`, `:2396-2501`)

- Anchor: 13 px above the head at standing height (hops don't bob it). Kept inside `SB.view` (the cropped area
  with `fit=cover`).
- Overlaps stack upwards (the lower one stays next to its speaker). If that leaves the view or hits a protected
  rect, try beside the speaker; if nothing fits, it waits hidden and its time doesn't run.
- `HARD_RECTS` (never cover) is empty. `softRects` (avoid if possible): door-title boxes from `marquees`, plus a
  gate-sign rect `[812, 328, 988, 370]`.
- Moves glide on a critically damped spring (~0.2 s). Upward pushes are capped at 900 px/s. The tail points at
  the speaker.
- Floor names (`showNames`): shown while `nameT > 0` (5 s for new arrivals, 7 after a ride, 8 for jannies),
  always for the followed chatter and jannies, never while they have a bubble. Names that would overlap show one
  at a time (followed > jannies > newest).

### Staff

| Role | Layout 2/3 spot | Notes |
|---|---|---|
| `cashier`, `cashier2` | [3.45, 7.4], [3.45, 6.0] | windows at [4.85, 7.4] / [4.85, 6.0]; window 2 `opensAt: 3` |
| `clerk1-3` | v 3.75 at u 6.6 / 8.2 / 9.8 | registers at v 5.05 |
| `usher` | [5.3, 3.8] | faces `gateIn [4.5, 4.6]` |

- Staff emotes are `Cinema.defaultEmote('roxy-<role>')`. They're placed on every `emotes` event (`placeStaff`).
- Counter staff stand 18 px higher (`STAFF_STEP`), plus `STAFF_CHAIR` extras (BINGQILIN +14).
- Rendered caps (`cap_cashier`, `cap_usher`) or CSS hats. Staff names are hidden. Staff "talk" with hops and arrows.

### Jannies, janitor, cat

- **Jannies** (default, `:2119-2190`): a DGG moderator's message (any, tagged or not) brings in a cpMOP penguin
  (`assets/cpMOP.webp`) wearing their name. It enters at `J`, says their messages, mops a free spot from
  `JAN_SPOTS` (4 spots; layout 3 moves spot 3 to [6.7, 8.35]) for 10-18 s, then moves on. After `janidle` (600 s)
  without a message it clocks off back past the usher. Max 4 (one per spot).
- `janitor=always`: one unnamed cpMOP penguin, always mopping (`initMopper`). `janitor=3d`: the rendered janitor
  sheets (sweep / idle / walk).
- **Cat** (`stepCat`, `:2017`): sleeps (20-50 s, later 30-80 s) at one of 4 `CAT_SPOTS` → stretch → walks via
  `HUB` → sits 8-20 s → sleeps. A walker moving within 0.7 tiles can wake it (it sits for 6-12 s). It needs
  `cat.sleep`, `cat.sit` and all four walk sheets.

---

## 6. Camera, vehicles, doors, screens

### Director (`:3217-3314`)

- Wide shot (zoom 1, centred on `WIDE_X`, 540) most of the time.
- Every `director.every` s (150, × 0.85-1.2; the first one after 45-75 s), the next arrival is followed
  (`directorArrival`). Hurried arrivals are never taken.
- Follow: while riding, follow the vehicle (`P(veh.u, veh.lane, 40)`); after that, the chatter at head height,
  with a small lead in the walking direction (±60 px x, ±40 px y). Zoom `director.zoom`.
- Ends 1.6 s after they go through the door, at once if they're removed, or after 150 s. Then back to wide.
- Smoothing: critically damped `damp()`; zoom 1.5 s, position 0.75 s while following, 1.4 s back to wide.
- Clamping: the centre is clamped so the view never leaves the stage, using the visible size from `SB.view`
  (`fit=cover` crops). A non-finite camera resets to the wide shot.
- Keys (page focused; OBS: Interact): `F` follow the next arrival, `R` follow someone now, `W`/`Esc` wide, `D`
  director on/off.

### Vehicles (`:1588-1877`)

- Types `sedan_a`, `sedan_b`, `taxi`, `bus`; directions `+u` (near lane, from u −9) and `-u` (far lane, from
  u 21). Removed past u 22 / −10.
- A passing car every 6-16 s (first after 2.5 s). A bus every 50-100 s (first after 8-20 s, `+u`, stops at the
  shelter, dwell 4.5 s). Taxis also come by from `pickRide`.
- A stopped vehicle waits for riders to clear the door (dwell + up to 10 s) and for boarders and waiting people
  (dwell + up to 12 s). Riders still inside when it has to go get off at the shelter (`releaseRiders`).
- Spacing: never inside the vehicle ahead in the same lane; enters only when the spawn area is clear
  (`laneClear`).
- Lights: brake while decelerating (held 0.3 s) or stopped. Bus and taxi blink the indicator (400 ms) within
  7 tiles of their stop, while stopped (`light_indicator_only` art), and for 1.8 s after leaving. All light variants
  are preloaded.
- Rain: roof loops always run; spray and wake fade in with speed (full at ~half of `full_speed`).
- The `door_open` sprite set is used while stopped. New sprite sets are decoded before the old ones are removed.

### Doors and animations

`playDoor(key)` plays a door sprite sheet once (open ≈ first 35% → hold → close). Re-triggering while it plays
winds it back to the start of the hold, so nobody walks through a closing door. Keys: screen numbers from
`door_anims`, `wc` and `stall<n>` from `restroom`.

### Screens and dinkdonk.mov films

- `Cinema.onRooms` (`cinema.js`): `/dd/data.json` is fetched at start and every 120 s. Rooms are the last five
  distinct films (TV only if there aren't enough), with title, year, DinkDonk rating and poster. Placeholders
  until data arrives.
- `applyRooms` (`:792`): title, a second line `★ <rating>` (else the year) + `<n> in`, and the poster. A new film
  on a screen resets its count. A failed poster is retried on the next refresh.
- Layout 3: only the right-wing doors remain, renumbered SCREEN 1-3 and showing rooms 0-2 (the three newest).
- LED signs (`makeLed`, `stepLeds`): a 5×7 dot font (accents stripped, unknown characters → `?`, `*` → `★`). Line 1
  in amber, line 2 in red. A row that doesn't fit scrolls one column per 75 ms with an 18-column pause. Each
  canvas is redrawn only when its text or offset changes. When LED signs exist, the DOM title boxes are hidden.
- Poster bulbs: `poster_bulbs_<n>_idle` / `_chase` prop loops. They chase for 4 s when someone enters, and one
  random screen chases for 3.5 s every 20-45 s.
- Arcade screen prop loops: `attract`, `play` while someone stands at `ARCADE`, `hiscore` for 3.5 s after a high
  score.

### Poll billboard / green screen

**The lobby has none.** The header says so ("no HUD, no green screen", owner, 02 Nov), `HARD_RECTS` is empty, and
nothing reads `Cinema.green`. Leftovers: `drawSky` (flat fallback only) still draws a billboard frame on the tower
at about x 1280-1888, y 26-382, with a comment about a green DOM rect that no longer exists. `README.txt` still
documents a lobby green screen at x1296 y40 576x324. How the DinkDonk poll is shown now, if at all, is unknown
from this file.

---

## 7. Control panel and live reload

The page opens `EventSource('/ctl/events')` (no `page` or `id` query; the server treats it as a lobby screen) and
posts its state to `/ctl/state` every 1.5 s (one post at a time, 3.5 s timeout). A 404 means an older server, so
the link shuts down. Off with `ctl=0` or when not served over http.

`control(c)` (`:3331`):

| `cmd` | Fields | Effect |
|---|---|---|
| `follow` | `nick` | follow that chatter (random if not found) |
| `random` | | follow a random visible chatter |
| `next` | | follow the next arrival |
| `wide` | | back to the wide shot, cancel `next` |
| `director` | `on` | automatic director on/off (when turned on, the next shot is within 20 s) |
| `every` | `value` | seconds between follow shots (30-1800) |
| `zoom` | `value` | follow zoom (1.2-3) |
| `remove` | `nick` | take them out of every line and fade them out |
| `add` | `nick`, `text`, `detour?` | walk a new chatter in (emote = first emote in `text`, else default; random room) |
| `say` | `nick`, `text` | an existing walker says `text` at once; otherwise like `add` |

`control.html` sends `say` for its form (there's no separate `add` button). The auditorium-only commands
(`phase`, `movie`, `outro`, `lights`, `houseOut`, `reset`, `phaseAuto`) are ignored by the lobby.

State posted: `id`, `size`, `obs` (running inside OBS), director state (`on`, `every`, `zoom`, `wantNext`,
`following`, `nextIn`), and `chatters[]` with `nick`, `emote`, `status` (`statusOf`: going in, on the bus, in a
taxi, street, ticket line, buying a ticket, snack bar, usher gate, restroom, arcade, bench, talking to the janitor,
chatting, corridor, lobby) and `followed`.

**Live reload** (`?live=1`, `shared/live.js`): every 1.5 s it fetches the page itself, `shared/core.js`,
`shared/cinema.js` and `shared/base.css`. It reloads when a file's new content is seen twice in a row (not
half-written). Error responses are ignored. It does not watch `emote-facing.json` or the art manifest.

---

## 8. Performance notes and debugging

From comments in the code:

| Topic | Note | Where |
|---|---|---|
| Wet highlight sheets | The 58 `wet_*` sheets stay 1x: at @2x they decode to ~590 MB, more than Chrome's image cache, so it re-decoded every frame (~10 fps vs ~53 fps). `wet2x=1` restores @2x | `applyArtRes` |
| Foreground rain | `rain_fg` is drawn inside the `#rain2` WebGL pass, not as a blended `<video>`: the blended video held Edge at ~52 fps (QA 04 Nov: 105 fps headless without it) | `fgToRain2` |
| Rain step rate | Extra rain redraws at 24 steps per second like the baked loops (`rainfps`) | `frame` |
| DOM writes | Figures, camera, LEDs, names and bubble tails write styles only when the value changes | `drawFigure`, `stepCamera`, `stepLeds` |
| Throttled sources | Door-sign flash is driven by the frame loop, not CSS animations; a 40 ms timer runs `frame` when rAF stalls | `frame`, `:3452` |
| Never freeze | Every frame is wrapped in try/catch; a NaN camera resets to wide | `loop`, `stepCamera` |
| Bounded counts | ≤80 figures, ≤30 wet prints, ≤16 sprite shots, ≤256 emote checks, ≤8 bubbles | various |
| Loop resolution | The 4K light loop must match the 4K base (exact complement); chosen from the window size before the stage scale is known | `setupArt` |
| Memory/decode | `maxres=1080` keeps 1080p art and loops even at 1440p/zoom | `MAXK` |
| Vehicle swaps | A new sprite set is decoded before the old one goes (no blank frame); light variants are preloaded | `vehSprites` |
| Control posts | One state post at a time with a 3.5 s timeout | `postState` |

Note `AGENTS.md`: performance fixes must not lower the full render resolution.

**Debug helpers**

| Helper | Use |
|---|---|
| `raintune=1` | slider for the extra-rain fall speed (shows "(weather)" while following the weather) |
| `weather=<x>` | run the weather clock faster |
| `morerain=1-4`, `rainspeed=`, `rainfps=0` | fix the rain style, speed, step rate |
| `mist=1-4`, `mistgain=` | splash-mist samples |
| `quit=1` | everyone in line gives up (tests the bus-home path) |
| `janidle=<s>` | shorter janny idle time |
| `layout=<n>`, `art=flat`, `artdir=`, `loop=0`, `loop2x=0` | art and layout fallbacks |
| `director=0`, keys F/R/W/D | camera |
| Console messages | `[lobby] frame`, `[lobby] control`, `[lobby] mist passes missing`, `[lobby] extra rain: passes missing`, `[lobby] <canvas>: no WebGL`; `[cinema] N square emotes kept off chatters` |
| `SB.say(nick, text, features)` | injects a fake chat message from the console (`core.js:576`). Synthetic chat is not allowed for showing or QA (`AGENTS.md`); use real chat with `everyone=1` |

---

## 9. How to change common things

Make the change in `lobby-qa.html` first, check it with real chat (`?everyone=1`), then bring it to
`lobby.html` (back that up first).

### Add or move a talk spot

1. Edit `SPOTS` in `setupLayout3` (`lobby.html:3181-3186`) for layout 3, or `HANGOUTS` (`:3025`) for the base
   lobby spots. Each entry is `{ c: [u, v], r }`.
2. Walkers walk in **straight lines** from wherever they are to `c + RING × r` and back. Nothing avoids props.
   Keep the spot and the lines to it clear of counters, the rope lane (`L.lane = [5.2, 7.15, 9.25, 7.65]`), the
   bench, the arcade and the snack partition.
3. Corridor spots must stay in front of the walking line (`v < ~1.6`). Behind it, the snack bar's back wall hides
   the floor and people look like they stand on the wall (owner, 05 Nov).
4. The stop chance per kind is `HANG_P`. A new *kind* also needs a `hangOut(w, '<kind>')` call in a route.
5. If a janny spot is affected, check `JAN_SPOTS` (routes go via `HUB [8.6, 6.6]`).

### Add a URL option

1. Read it once near the code it controls, clamped:
   `const FOO = clamp(Number(q.get('foo')) || DEFAULT, MIN, MAX);` (`q` is the page's `URLSearchParams`).
   For on/off flags use `q.get('foo') === '1'` or `q.has('foo')`, as the existing ones do.
2. Add it to the header comment at the top of the page and to the table in section 2 of this doc.
3. Options read in `shared/*.js` affect every page that loads them. Check with whoever is working on the
   auditorium before adding one there.

### Swap the art pack (`artdir`)

- Try a pack with `?artdir=<folder>` (under `roxy3d/`). It needs `manifest.json` with `bg` or `base` and an
  `occluders` array. Missing optional parts just switch features off.
- The manifest's `layout` picks `LAYOUTS[n]`. Staff, queue, door and talk-spot positions are in the page, not the
  manifest, so a pack with a different floor plan needs matching `LAYOUTS` / `DOORS` / `SPOTS` edits.
- Mist and extra-rain passes come from `mistdir` (default `out10mist`), separately from `artdir`.
- To make a new pack the default, change the `'out10'` fallback in `ART` (`:202`) and update the file list in
  `package/art.js`. The promote steps (stage, verify, back up) are in [art-pipeline.md](art-pipeline.md). Art files
  are byte-exact; don't re-save them.

### Adjust the rain

| Want | Change |
|---|---|
| Heavier/lighter overall | `moreraingain=` (URL), or `RAIN2_GAIN` default |
| A state's mix or speed | the `WEATHER` table (`:2724`): `[fine, near, curtains, crowns, speed]` |
| How often states come up | `WEATHER_ODDS` |
| Hold / crossfade times | `w.hold = rand(40, 120)`, `w.fadeT = rand(12, 20)` in `stepWeather` |
| Streak look (width, length, density, base speed) | `streaks(...)` calls in `RAIN2_FS` `main()` |
| Where the extra rain may fall | the mask build in the `RAIN2` loader (`:2760-2793`): roof polygon, dry strip u 13-15.6 |
| The baked rain itself | it's in `light_loop` / `rain_fg`; that needs a re-render (see art-pipeline.md) |
| The fallback 2D rain | `drops` and `drawRain` (`:2507-2537`) |

### Move staff, counters or the queue

Edit `LAYOUTS[3]` (it extends `LAYOUTS[2]`, `:240-261`): `windows`, `slot(i)`, `queueEntry`, `lane`, `qmax`,
`snack`, `staff`, `toSnack`, `fromSnack`, `toGate`, `gateIn`, `gateSlots`, `bench`. Keep them in step with the
render, since the manifest's `staff_positions` / `queue` are not read.
