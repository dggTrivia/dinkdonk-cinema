STANDBY SCREENS FOR OBS

LOBBY - lobby.html (current, main screen; the old roxy.html URL redirects here)
A late-90s pre-rendered isometric cinema on a rainy night, in the middle of a
city block (apartments, a video rental, shops across the street, the billboard
tower). The art is rendered in Blender (roxy3d/, built by Codex): a still + a
6 s seamless light loop (downpour, splashes, gutter water, wet reflections,
neon) + a foreground rain loop in front of people and cars, water running down
the cinema glass, depth-sliced props, vehicles, a cat, a janitor, door/prop
animations. The page adds everything live on top.

  Street: cars both ways, a bus stopping at the shelter, taxis to the door;
          chatters walk in, or arrive by bus/taxi and step out.
  Lobby:  box office counter (2 windows), snack bar (3 registers), usher gate
          with a short line (tears the stub, points to the wing), arcade (attract /
          game / hi-score screen), bench (someone waits for a friend), cat,
          janitor, wet footprints behind people coming in from the rain.
  Wings:  left = screens 1-2 + restroom, right = screens 3-5 (last 5 films on
          dinkdonk.mov, with rating and "n in" counts); doors swing open.
  Who walks in: only chatters who tag arealhumanbean (everyone=1 for all).
  No chat panel: speech bubbles with the speaker's name.

GREEN SCREEN (DinkDonk poll): billboard on the tower, x1296 y40 576x324
(x2 at 3840x2160). OBS: keep hardware acceleration for browser sources on.
URL options: demo=1, green=off|<hex>, everyone=1, tag=Nick, loop=0 (no video
loop, lit still), art=flat (old blockout), artdir=out..out8b (art versions),
live=1 (reloads itself when a file changes).
The rain/neon loops are .webm videos: restart start-standby.bat after updating
(older versions of standby-server.js could not serve video, the page then
falls back to a still with drawn rain).
Re-render the art: roxy3d/NOTES*.md (Blender 5.2.3 in tools/).

CINEMA HALL - 5 ISOMETRIC DESIGNS (hall-1..5, newest)
Same behaviour as cinema-1..5 below (ticket booth queue, hallway with 5
doors = last 5 dinkdonk.mov films, popcorn/restroom detours, no commands),
drawn in a smooth pre-rendered isometric style instead of pixel art.

  hall-1-monastery.html  Monastery Picture House  green screen x1256 y36  640x360
  hall-2-deco.html       The Grand Palace         green screen x1262 y18  640x360
  hall-3-bazaar.html     Desert Rose Cinema       green screen x1184 y32  704x396
  hall-4-noir.html       The Roxy, 90s (chosen)   green screen x48   y36  576x324
  hall-5-lodge.html      Highlands Lodge Cinema   green screen x340  y20  560x315
(1920x1080 layout; x2 at 3840x2160.) Same options: demo=1, green=off|<hex>,
chat=off, f=. OBS: keep "hardware acceleration" for browser sources on.

WHO WALKS IN (all hall-* and cinema-* pages)
Only chatters whose message tags arealhumanbean (with or without @), plus
arealhumanbean's own messages. The DSA chat panel still shows everyone.
  everyone=1          every chatter walks in again
  tag=OtherNick       require a different nick
With demo=1 everyone walks in (fake chat never tags you) unless tag= is set.

CINEMA STANDBY - 5 DESIGNS (cinema-1..5)
Every chat message walks that chatter in as their emote (first emote of the
message, else the last one they used, else a fixed default), hopping, and
they go into one of 5 screening rooms = the last 5 films shown on
dinkdonk.mov. Talking again walks them in again. No chat commands.
Now and then someone stops at the popcorn machine or visits the restroom.
Shared logic: shared/cinema.js.

  cinema-1-iso.html     Isometric Multiplex     green screen x1388 y24  512x288
  cinema-2-rpg.html     16-bit RPG Cinema       green screen x888  y606 528x297
  cinema-3-gothic.html  Gothic Picture Palace   green screen x483  y42  576x324
  cinema-4-tower.html   Tiny Tower Cinema       green screen x1344 y64  544x306
  cinema-5-pocket.html  Pocket Cinema (GB)      green screen x1296 y20  608x342
(green-screen rectangles on the 1920x1080 layout; x2 at 3840x2160. Each
file's header comment has the details.)

Options for all five: demo=1, green=off (info panel instead) or green=<hex>,
chat=off, f=<DSA chat size>. Pocket Cinema is all green, so key it with
?green=ff00ff (magenta) or lower OBS chroma similarity - see its header.

STANDBY: lobby.html  (http://127.0.0.1:18770/lobby.html)
A cozy cinema lobby. Every chatter who talks walks in as a cinema-goer:
their sprite is the first emote of their latest message (or a default
emote until they use one). They queue at the ticket booth, wander around
with speech bubbles, grab popcorn and eventually go into Screen 1-3; when
they talk again they come back out. Quiet for 20 minutes = gone.
  !popcorn       go get popcorn          !enter 1-3   go into that screen
  !hop           happy hopping           !ticket      join the ticket queue
Combos make everyone wearing that emote jump.

GREEN SCREEN for an OBS insert: pure #00FF00 at x 730, y 128, 600x338
(on the 1920x1080 layout; at 2560x1440 multiply by 1.333, at 3840x2160 by 2).
Either add a Chroma Key filter to the Browser Source and put your source
underneath, or put your source on top of that rectangle.
  green=00b140   other key colour        green=off   plain black screen
  screens=Title A|Title B|Title C        door titles (default: last 3 watched
                                         on dinkdonk.mov)
  clerk=EMOTE    who sells the tickets (default DinkDonk)
  chat=off       no lobby chat monitor   f=2         its text size

DINKDONK INTERMISSION: dinkdonk.html  (http://127.0.0.1:18770/dinkdonk.html)
A cinema "intermission" built from dinkdonk.mov, cycling through:
  Just watched     poster, DinkDonk score, vote histogram, how it was picked,
                   DinkDonk vs TMDB
  Recent           the last 8 screenings with scores and pick method
  Poll replay      recent polls; instant-runoff polls replay round by round
  Fame & shame     all-time best and worst rated (10+ votes)
  Numbers          watch-log stats: picks by method, busiest conductors, ...
  Chat's pick      straw poll of runners-up you haven't watched lately
  Next night       countdown + upcoming sessions from /schedule
Chat commands:
  !rate 0-5        chat's own rating of the last movie (kept per movie)
  !pick 1-3        vote in the straw poll
  !watched TITLE   searches the DinkDonk watch log ("have we seen X?")
  !skip            next segment (20 s cooldown)
Options: seg=poll (stay on one segment), dur=1.5 (slower rotation), plus the
URL options below.

dinkdonk.js reads the site's public pages (about 15 requests every 5
minutes while the screen is open) and keeps the last good copy in
cache\dinkdonk.json. If dinkdonk.mov is unreachable - e.g. Spanish ISPs block
Cloudflare during LaLiga matches - the screen keeps showing the cached data
with a small "showing data from ..." note.

EARLIER DRAFTS (no dinkdonk data)

Each draft is a full-screen 16:9 page with Destiny.gg chat from the DSA OBS
overlay relay (Desktop\customchat\destinygg-obs-overlay, 127.0.0.1:18765) and
things chat can do to the screen.

  01-testcard.html    SMPTE bars + CRT.  !dvd EMOTE  !channel  !static
  02-aquarium.html    every chatter is a fish.  !feed  !shark  !bubbles
  03-claw.html        emote physics pile + claw machine.  !claw  !shake
  04-pulse.html       live dashboard + PEPE vs YEE.  !pepe  !yee
  05-nightdrive.html  synthwave drive, chat speed = car speed.  !boost  !honk  !radio

All drafts also react to emotes and combos (C-C-COMBO) on their own.

START
1. Start the DSA overlay as usual (customchat\...\start-windows.bat).
2. Double-click start-standby.bat in this folder (needs Node.js 18+).
3. Gallery with fake chat: http://127.0.0.1:18770/

OBS
Browser Source, URL e.g. http://127.0.0.1:18770/03-claw.html
Width/height: any 16:9 size - 1920x1080, 2560x1440 or 3840x2160. The page
scales itself; canvases render at the real pixel size.

URL OPTIONS (add with ? and &)
  title=BE%20RIGHT%20BACK   headline        sub=...   subline
  until=21:30               count down to a local time instead of "away for"
  f=4                       DSA chat text size (1..10), same as the overlay
  chat=native               our own simple chat list instead of the DSA iframe
  chat=off                  no chat panel
  chatbar=1                 show the DSA toolbar (crop is 40px by default,
                            chatcrop=NN to change)
  cmds=off                  ignore chat !commands
  demo=1                    fake chat traffic for previewing

WHY A SECOND SERVER
The pages read raw chat from the relay's WebSocket (/__dgg_chat_ws) for the
interactions, and show the real DSA chat in an iframe. cdn.destiny.gg only lets
www.destiny.gg read the emote list, so standby-server.js relays
emotes.json/emotes.css (cached 10 min). It binds to 127.0.0.1 only.

Commands have a global cooldown per command and 8 s per user. Banned/muted
users' bubbles, fish, signs and prizes are removed on MUTE/BAN.
