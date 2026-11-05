DINKDONK CINEMA FOR OBS

Two animated screens for DinkDonk movie nights, filled live from Destiny.gg chat:

  The lobby       a rainy late-90s cinema on a city block. Chatters walk in off the street (or arrive by
                  bus or taxi), queue at the box office and snack bar, and go into the screens.
  The auditorium  Screen 1. Chatters come in through the tunnel, climb the stairs and take a seat. The
                  lights go down and the film plays on the cinema screen itself.

Film titles and ratings come from dinkdonk.mov. Everything runs on your own PC; nothing needs an account.

WHAT YOU NEED (once)
1. Windows, OBS Studio 30 or newer.
2. Node.js 22 or newer (LTS): https://nodejs.org/
3. For the film on the auditorium screen only:
   - the obs-shaderfilter plugin: https://github.com/exeldro/obs-shaderfilter/releases
   - OBS > Tools > WebSocket Server Settings > Enable WebSocket server (keep port 4455; the password is
     read from OBS's own settings on this PC, you don't have to type it anywhere).
   - VLC to play the film.
   Without these the auditorium still works; its screen just stays green (handy for your own chroma key).

FIRST TIME IN OBS
1. Unzip this folder somewhere permanent (e.g. Documents\DinkDonk-Cinema). Don't run it from inside the zip.
2. Double-click START.bat. Three windows open (chat relay, screens server, OBS bridge) plus the control
   panel in your browser. Windows may ask about network access: Node only listens on this PC (127.0.0.1).
3. OBS > Scene Collection > Import > pick the file in obs\ that matches your canvas
   (Settings > Video > Base Resolution): DinkDonk Cinema 1080p / 1440p / 2160p.json. Then switch to it under
   Scene Collection. Your own collections are not touched.
4. You get these scenes:
     DinkDonk Cinema       the auditorium, with the film pinned onto the cinema screen
     Lobby + Poll setup    the lobby, with dinkdonk.mov beside it for building the poll
     Lobby (src), Film screen (src)   building blocks, used by the two above
   Add your own scenes (camera, the movie itself, ...) to this collection, or copy these into yours.
5. Open the film in VLC. If the cinema screen stays black: right-click "Film screen (src)" > Game Capture >
   Properties and pick the VLC window, or replace it with a Window Capture of VLC.

EVERY STREAM
1. Double-click START.bat (before or after OBS, either works).
2. Use the control panel (http://127.0.0.1:18770/control.html) to follow a chatter, go back to the wide
   shot, switch the automatic camera director on or off, or move the auditorium through its phases
   (seating, lights down, film, lights up).
3. Close the three windows when you're done.

WHO WALKS IN
By default everyone who chats walks in (the OBS URLs end in ?everyone=1). To let in only chatters who
tag you, edit the Browser source URL in OBS: replace everyone=1 with tag=YourNick.

USEFUL URL OPTIONS (Browser source URL, joined with &)
  demo=1          fake chat, for trying it out off-stream
  everyone=1      every chatter walks in            tag=Nick   only chatters who mention Nick
  director=0      no automatic camera moves         zoom=1.5   closer camera
  maxres=1080     smaller art (for slower PCs)      green=off  no green screen on the lobby billboard
Auditorium only: phase=seating|dim|film|up (start in that phase), screen=green (always a green film
screen, for keying the film yourself), bridge=0 (don't move the film screen in OBS).
The auditorium's pre-show slide shows download progress if qBittorrent's Web UI runs on port 8080.

IF SOMETHING'S OFF
  No one walks in             Is the "Chat relay" window open and saying it is connected?
  Screen stays green          Is the "OBS bridge" window saying OBS is connected? Is obs-shaderfilter installed?
  Film is in the wrong place  Leave the auditorium on screen for a second; the bridge follows every camera move.
  Old film titles             dinkdonk.mov was unreachable; the last good copy is shown until it's back.
  Slow / dropped frames       Settings > Advanced: keep "Browser Source Hardware Acceleration" on; try maxres=1080.
  Port already in use         Something else uses 18765, 18770 or 18790. Close it, or the old window of this.

WHAT'S INSIDE
  START.bat     starts everything below
  screens\      the lobby and auditorium pages, their art, the screens server and the OBS bridge
  chat-relay\   the Destiny.gg chat relay with the DSA script (see chat-relay\README.txt)
  obs\          scene collections to import, and the corner-pin shader (obs-shaderfilter, GPL-2.0, SkeletonBow)
