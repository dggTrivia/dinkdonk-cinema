# Standing goal: scene 2, the DINK DONK auditorium (overnight 03-04 Nov 2026)

Owner (21:35): keep working until it is good enough or Claude weekly usage reaches 55 % (43 % at the start). Includes
the final 4K render on the owner's own GPU (no cloud), more draft -> review -> fix rounds, chatter animations learned
from the lobby. No images sent overnight; summarise in the morning.

## Pieces
- Page: `standby/auditorium.html` (?draft=NN reads `qa11/cinema_draft_NN.png` + `qa11/cinema_layout_NN.json`).
- Art: Codex drafts in `roxy3d/qa11/` (BRIEF-28 .. 39). Draft 10 = current approved look + page layers.
- Phone/LAN: `standby/lan-proxy.js` (192.168.2.150:18780), chat relay `customchat/destinygg-obs-overlay`.

## Done 03 Nov evening
Tunnel arrival, seats, diagonal backrest cut -> depth slices (draft 10), entrance door anim, speech while walking,
DGG flair colours 1:1 with the DSA script (both scenes), square-emote filter (both), emote facing table
(`shared/emote-facing.json`, both scenes), lobby walk animation (hop/waddle/squash, seated talk bounce), taller
sitters, YEE = wheelchair front row, red emergency exit, wheelchair plaques.

## Running / next
1. Codex BRIEF-38 (page): zoom director + control panel for the auditorium -> review, restart server if needed.
2. Codex BRIEF-39 (render): fresh review + draft 11 polish + final 4K set -> review, switch page default to 11.
3. Then, if budget allows: lights-down state for the film start, pre-show slides on the screen, lobby -> auditorium
   transition, OBS copy of "Moobies 1440p" with the corner-pin shader (ask owner before touching OBS).

## Status at stop (03 Nov ~23:30, weekly usage 44 %)
Done overnight: director + control panel (BRIEF-38/40), draft 11 polish + FINAL 4K set on the local GPU (BRIEF-39),
pre-show slides + qBittorrent progress + phases seating/dim/film/up (BRIEF-41), rendered lights-down state + crossfade
(BRIEF-42/43), QA/code review + crowd spacing + full-house queue (BRIEF-44).
Waiting on the owner:
1. Enable qBittorrent's Web UI (127.0.0.1:8080, bypass auth for localhost) -> real download % in the pre-show.
2. OK to make the OBS copy of "Moobies 1440p" with the corner-pin shader (screen corners in cinema_layout_11.json).
3. How the stream should get from the lobby to the auditorium (OBS scene switch when the poll ends? a walk-in?).
4. Review the 27 square emotes kept off chatter bodies (console line "[cinema] ... square emotes").
5. Small: wheelchair plaques look self-lit in the dim state; crowd look in huge bursts.
