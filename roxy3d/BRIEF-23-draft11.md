# Brief 23: DRAFT 11 - a really dark night, one image, then stop

Strict draft rule: exactly ONE image - the fixed isometric camera, 1280x720 at final quality with the weather frame
-> `qa10/draft_11.png`. Nothing else. One STATUS line, a few lines in `qa10/DRAFT-11.md`, then STOP. Work from the
draft 10 scene. Only write inside roxy3d/.

Owner on draft 10 (only feedback): the whole map is too bright. On a really dark night the only bright places are
actual light sources and what they light: neon signs (DINK DONK, Anything else?, shop signs), lit windows, street
lamps, car headlights (page sprites), the cinema itself (its interior, entrance, storefront glow). Everything else -
roofs, streets, sidewalks, alley, building walls far from lights, the sky - should fall into deep darkness, lit by
practically nothing.
- Cut the ambient/world light and the generic fill lights drastically (sky dome, city fill, any "readability"
  fills from earlier passes); darken the sky to a near-black night with only a faint low glow.
- Let practical lights do the work with real falloff: pools of light under lamps, spill from windows and the
  cinema, neon colour bleeding onto nearby wet surfaces; strong contrast between lit pools and dark areas.
- Wet surfaces stay readable mostly through REFLECTIONS of the light sources (and the hidden catchers, which may need
  to be dimmer and more localised so roofs don't glow), not through diffuse brightness.
- Keep the lobby/cinema interior as bright as now (it's the focus) and keep walker areas on the street/sidewalk
  just readable (lamp pools, storefront spill), since chatters walk there.
- Keep everything else exactly as in draft 10.
Report the light changes (old/new values) in DRAFT-11.md.
