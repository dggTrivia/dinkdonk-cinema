# Brief 8: pass 7 - carried items and staff caps in the rendered style, indicator-only lights

out6 is live and the reviewer's verdict is good. The remaining visual gap: small DOM-drawn items on the
chatters look flatter than the render. Same rules; **outputs to `roxy3d/out7/`** (complete set, layout 2,
keep every manifest key/contract, only add).

## A. Small attachable sprites (same camera, lighting, wear and palette; tiny, crisp; 1x + @2x)
Each with `w`, `h` and an `anchor` = the attach point described below, as `"items": { "<name>": {...} }`:
- `popcorn` - striped red/white tub with popcorn heaped on top, ~16 x 20 px at 1x; anchor = bottom
  centre of the tub (the page puts it at the emote's lower right).
- `soda` - waxed paper cup with lid and straw, ~12 x 18 px; anchor = bottom centre.
- `stub` - a torn cinema ticket stub, ~12 x 8 px, slightly tilted; anchor = its centre.
- `ticket` - a whole ticket (flies from the cashier), ~18 x 11 px; anchor = centre.
- `cap_cashier` - small red staff cap with gold band, ~28 x 12 px, seen from this camera; anchor =
  bottom centre (sits on top of a ~50 px emote).
- `cap_usher` - maroon pillbox cap with gold band and button, same size/anchor.

## B. Indicator-only light sprites
For the bus and taxi, both directions, closed and door-open: `light_indicator_only` (+ `_2x`): ONLY the
amber indicator glow and its wet-road reflection (indicator-on minus normal), on black, same size and
anchor as the other light sprites, so the page can add it on top of the brake or normal light.

Report as before.
