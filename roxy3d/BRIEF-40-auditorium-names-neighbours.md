# Brief 40 (PAGE): auditorium - names never hidden, neighbours turn to the speaker

Page work in `standby/auditorium.html` only (you ported the director/control in BRIEF-38; same rules: read
`standby/roxy.html` for conventions, keep the page working, no shared/*.js changes, test with
`?everyone=1&relay=127.0.0.1:1` + `SB.say(...)`, the server on 18770 stays up). Report `roxy3d/qa11/PAGE-40.md`, STATUS.

1. **Name labels are covered by the depth slices.** The `.nm` label lives inside each walker element, so it shares
   the walker's depth z-index and seat backs / rails / tiers in front of the walker hide it (seen live while zoomed:
   "FatHead...tball", "Nekr...", "con...ut"). Names must always be fully readable: draw them in their own layer above
   all world art (inside the camera so they zoom/pan with the world, or in the screen overlay like the bubbles -
   choose what matches the lobby best and keeps them crisp), anchored under their emote as now. Keep the lobby's
   rules for when names show (new arrivals / followed / while not talking; hidden while their bubble is up).
   Names of chatters hidden in the tunnel stay hidden.
2. **Seated neighbours react to talk.** When a seated chatter says something, the seated chatters next to them
   (same row within ~2 seats, and the seat directly in front/behind) turn to face the speaker for ~4-6 s
   (`SB.faceEmote(el, name, dirX)` with dirX = sign of the screen-x offset to the speaker), then turn back to the
   screen. Front-facing emotes don't turn (faceEmote already ignores them). No other new behaviour.

Do not change anything else. STATUS line, stop.
