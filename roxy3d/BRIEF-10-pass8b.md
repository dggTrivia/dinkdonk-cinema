# Brief 10: pass 8b - polish out8 (outputs to roxy3d/out8b/, complete pack, same contracts)

out8 is live and reads as one rainy city block (your review-9). Fix these, nothing else changes:
1. Your review-9 #7: upper-centre backdrop x890-1280 y0-250 - break the straight transition around y175 with
   distant roof geometry, uneven cloud light and rain haze.
2. Review-9 #8: denser fine/medium rain between the big streaks (base loop and rain_fg), stronger impact spray
   under lamps and along curbs; keep the nearest streaks sparse. The owner asked for MUCH heavier rain: it
   should read as a downpour at stream size, without turning into a white veil.
3. Review-9 #9: glass water reads as clean blue railing - faint water films across each pane, a few readable
   runnels, brighter sill accumulation; same depth slices.
4. Review-9 #10: road reflections less smooth - rough asphalt breaks, interrupted puddles, local impact
   distortion, still recognisable light sources.
5. Claude: the right-hand alley/forecourt paving (about x1150-1700, y720-1080) and the roof right of it are a
   flat, uniform light grey - give them material (wet concrete/asphalt, joints, grime, puddles, reflections of
   the annex/records sign and windows), darker so they don't outshine the lobby.
6. Claude: the lobby carpet has faint screen-aligned rectangle outlines (dozens of them, e.g. base@2x around
   x1500-2300 y1300-1800; already in out6/out7). They read as debug boxes at 4K - remove them (or make any intended
   wear patches follow the carpet, soft, no outlines).
7. Review-9 #6: provide a weather-free lit still for the no-video fallback (`lit_bg_dry` + `_2x`: lit like
   lit_bg but without baked rain streaks/impacts; wet surfaces stay wet). The page draws procedural rain on it.
Same validations (occlusion 0, aperture, seams, black level, protected files), NOTES-PASS8B.md, STATUS lines in
qa8/STATUS.md.
