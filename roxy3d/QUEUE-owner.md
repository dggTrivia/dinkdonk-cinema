# Owner's queued changes (do NOT start yet)

Collected 02 Nov 2026 ~10:15, after the fresh GPT-6 Astra (xhigh) feedback (reviews/fresh-xhigh-feedback.md).
The owner will look at the final out8b pass first and then add more changes; do all of these together
with those, not before.

1. **Billboard panel better integrated** (fresh feedback #1, owner agrees): today it reads as a heavy,
   layered frame pasted on, crowding the Screen 3/4 signs. Make it part of the venue/tower (slimmer, physical
   billboard construction, maybe a cinema-style label like "Coming Attractions"). Open question for the owner
   when we do it: the green aperture x1296 y40 576x324 is used by OBS - keep it exactly, or may it move/resize?
2. **Movie signs in the walls' isometric perspective** (owner): the five screen title signs (and their DOM
   text) are flat, screen-aligned rectangles; they should sit on the wall planes like the posters do (skewed
   to the u = 0 / v = 0 walls). Needs Codex (rendered marquee boxes) + page (text transformed onto the plane).
3. **Remove the top-left HUD text** (owner): no "INTERMISSION"/standby wording, no schedule bar (clock +
   next movie night). Fresh feedback #3 (return message) and #4 (schedule bar) are rejected. Check with the
   owner whether the "The Roxy" neon logo goes too.
4. **Gate sign as a physical directional sign** (fresh feedback #5, owner agrees): the "◀ 1-2 · 3-5 ▶" box
   looks like a UI pagination control; make it a real cinema wayfinding sign with distinct left/right groups
   (Codex re-renders the baked sign).
5. **More restrained ambient animation** (fresh feedback #6, owner agrees): gentle puddle ripples, occasional
   single-tube neon flicker, popcorn machines, janitor idle (most exist - extend and make them more visible),
   rain softer around text; never everything moving at once.

## Round 2 feedback (02 Nov ~11:00) - for the NEXT pass (after out9 lands), do not start yet
6. **Speech only in conversations.** Chatters no longer spawn with a bubble. They come in and do their thing
   (tickets, popcorn); then, instead of going straight to the screen, they hang around, walk up to another
   chatter (or a group of 3+) and chat - bubbles appear only then, for everyone in that conversation.
7. **Only three screens, all on the right.** Scrap screens 1-2 on the left (they would sit in the neighbour's
   building). Keep screens 3-5 (right wing) -> they become screens 1-3. The background buildings top-right are
   replaced by the exterior of those three auditoriums (their roofs/walls as a continuation of the cinema,
   not fully built).
8. **Left wing becomes the restroom.** The left side keeps only the restroom: its own rectangular room
   (reaching to where the ticket area ends), built in 3D and cut away like the lobby: toilet stalls, sinks,
   mirrors, etc. Walkers use it for real (stall doors).
   Owner's answers (11:05): messages sent while not in a conversation are SAVED and said at the next chat (a
   new message makes them go find a group); restroom = the left wing strip from the back corner to where the
   ticket counter ends (3-4 stalls, sinks + mirrors, hand dryer), the front-left corner stays lobby; the three
   screens show the last 3 films from dinkdonk.mov, newest on screen 1. Items 1-5 above were already sent to
   Codex in BRIEF-11-pass9 (out9) - re-check them in out9.
   Item 7 detail (owner, 11:30, with screenshot): right now the three doors look like "portal doors" with an
   apartment block directly behind them. Behind the right-wing wall there must be the three big auditorium
   boxes themselves (taller than the corridor wall, roofs with HVAC/projection booths, plain exterior walls),
   so the doors obviously lead into large halls. The apartment/tower block behind goes; the rooftop billboard
   (ad surface) moves onto the auditorium roof or another spot that stays clear of the walkers.

## Round 3 feedback (02 Nov ~12:15, after seeing out9) - next pass
9. Ticket queue marked with stanchions + red velvet ropes (the page queue slots follow the rope lane).
10. Snack counter populated: cash registers, napkin/straw dispensers, cup stacks, candy display case, tip jar,
    nacho cheese pump etc. - looks alive.
11. Doors open into a dark space (black vestibule / curtain), not a brick wall.
12. Corridors less empty: cardboard standees of other films, etc. (Claude to suggest a set).
13. Janitor = a DGG emote (inside joke) instead of the 3D janitor - owner pastes the emote name/image.
14. The cinema is called DINK DONK (as in dinkdonk.mov), with a neon of the DinkDonk emote. Placement open:
    over the entrance would block the view into the lobby - Claude to propose options.
15. The front wall beside the bus stop (next to the restroom, front of the left wing) is still the low
    half-height wall - make it full height like the rest of the front.
16. WORKFLOW: Codex does a quick DRAFT first (fast still render, no loops/sprites) for owner feedback, and only
    then the full render - shorter time between feedback rounds.
   Owner's answers (12:20): DINK DONK = big rooftop neon on the new auditorium block ("DINK DONK" letters + the
   DinkDonk emote in tubes), the entrance blade gets a small DinkDonk emote neon; d.gg stays as a small nod
   elsewhere (bus line "d.gg transit", a shop or street sign); the left-wing front wall = solid full-height
   wall (brick/plaster, maybe a small high window) - the restroom inside is mostly hidden from the camera.
   Corridor ideas from Claude (to confirm in the draft): cardboard standees of other films, a "coming soon"
   lightbox, a bench, a drinking fountain, an exit sign, a fire extinguisher, carpet runners, a trash can.
   Item 13 detail (12:25): the janitor emote is 7TV "cpMOP" (Club Penguin penguin mopping, animated,
   https://cdn.7tv.app/emote/01HVYG5N680004JB4FF7766GF8/4x.webp; local copy roxy3d/ref/janitor-emote/4x.webp).
   Page-side: the janitor NPC becomes this emote (same spots/routes, mops at each spot, waddles between them,
   mirrored by direction, contact shadow) - no Codex render needed; the 3D janitor sheets stay unused.

## Later (owner, 02 Nov ~12:55, after draft 2)
17. The big back-building roof is liked as is. Later: add decay/wear to it and the rain effects on it
    (puddle ripples, splashes, run-off) - not in pass 10.

## Round 4 feedback on draft 2 (02 Nov ~13:15) - collecting, do not start yet
18. Top-left neighbour: the low annex between the brick apartment block and the restroom covers the apartment
    block's windows - makes no sense. Instead the apartment block itself extends all the way to the restroom
    wall (one continuous building), and that part has NO windows facing the cinema (a blank party wall).
19. The corridor walls (the corner junction by the WC / 1-3 signs and the back walls) look empty - dress them:
    framed one-sheets of classic/fictional films, a "NOW SHOWING / COMING SOON" board, a wall clock, fire alarm
    + extinguisher cabinet, a framed cinema-history photo or two, a vending machine or payphone in the corner,
    more sconces / a neon accent - things attached to the walls, without blocking walker routes.
20. Roofs (the big theatre roof and the other roofs): more decay and imperfection now, not later - stains,
    patched felt, rust streaks, pooled water, debris, a tarp, a bent vent, moss/grime in corners, uneven
    parapet caps. Small charming flaws in the animation too: e.g. the AC fans spin in the loop, but one of
    them is dead (not spinning), another one wobbles; one sign tube flickers. (Supersedes item 17's "later".)
21. (owner sent 3 crops, no text - Claude's reading, to confirm) Surface details look fake/drawn:
    a) roof puddles are flat dark ovals (stickers) - make irregular, soft-edged, reflective (sky/neon), shallow;
    b) the thin ellipse rings on the street/sidewalk read as drawn outlines, not ripples - remove the static
       rings; ripples only as faint animated rings in the loop;
    c) road cracks are black scribble lines - make them subtle sealed asphalt cracks/tar snakes, lower contrast,
       broken, catching a little wet light.
    Owner confirmed (13:25): "most puddles and lines don't look natural, they look artificial" - rework all
    puddles, rings and crack lines across the scene (roofs, street, sidewalk), not just the cropped spots.
22. The back alley (right of the lobby, between the cinema and RECORDS & REPAIR / the apartments): make it a
    real back alley - dumpster(s), trash bags, a recycling bin, the cinema's emergency exit door (with a lit
    EXIT sign, maybe propped open with a brick), loading door, pallets, crates, a puddle with neon reflection,
    steam from a vent, graffiti/tags, a fire escape. Floor: not neat tiles - cracked, patched, uneven asphalt/
    concrete with potholes and grime, wet. (Owner: more things will come here later.)
23. The short white dashes all over the front glass are the "static rain traces" Codex baked into the panes in
    draft 1/2 - they read as random white rectangles. Remove them from the still; water on the glass only comes
    from the animated glass-water overlays (soft runnels/beads), and those must not look like dashes either.
24. Living windows on EVERY apartment/neighbour building (not just the video-rental block): lights switching
    on/off, a flickering bulb, TV glow changing colour, a silhouette walking past behind the curtain, a curtain
    moving, a cat on a sill, someone at a window smoking (ember), a party window with coloured light...
    Plan: these must not repeat every 6 s, so Codex delivers per-window data (`windows: [{quad_px, z_index,
    lit, building}]` for every visible window) + a small kit of additive/straight-alpha sprite sheets for each
    event type in window perspective; the page schedules random events per window over minutes (a few at a
    time, never everywhere at once), lights change state and stay changed.
25. Far top-left (left of the video-rental block, the cropped "REPAIR" building at the frame edge): doesn't make
    sense as a cut-off building - replace it with a small cafe: shopfront facing the street, a lit sign, and a
    little outdoor seating area on the sidewalk (tables, chairs, closed or open umbrellas/parasols, a menu
    A-board, string lights), wet from the rain, keeping the walker spawn lane (u ~ -6, v 9.78-10.05) clear.
26. The end of the back alley (right of screen 3, below the theatre building) is a flat black wall/void. It must be
    the cinema's own exterior side/back wall (same masonry as the theatre building), lit by the alley, with
    graffiti/tags, drainpipe, the emergency exit (item 22), a grimy service light - no black surfaces.
27. Wall tops / cutaway: the purple band running along the top of the corridor walls (above the doors, under
    the theatre building's brick) is ambiguous. Make it read like a Sims cutaway: the walls are cut, and the cut
    shows the wall's cross-section - a clean cap showing the wall's thickness (plaster/brick core, the inner
    purple finish on the inside face, the outer brick/stucco on the outside), consistently on every cut wall
    (corridor walls, restroom walls, partitions, the left wing), so it's obvious we look into the building.

## Memes (02 Nov ~13:40)
28. Owner approved the whole Top 12 of memes/SHORTLIST.md (alley graffiti, inside posters/boards, billboard,
    shelter, bus side, poster wall, shop sign). Not implemented yet.

## Round 5 feedback on draft 3 (02 Nov ~13:50)
29. Top-left apartment block roof (the part extended to the restroom wall): it reads as an extra piece added
    on - the seam line between old and new roof is visible. Make it one continuous roof (same felt, no join
    line, one parapet all round). The rooftop kit (AC units, vents, skylights, hatch, pipes) is bunched
    together - spread it out across the whole roof in a believable layout.
30. WORKFLOW: drafts must show the real wet look (reflections, puddles, water on roofs/street) - render drafts as
    one final-quality frame with the wet materials and one composited weather frame, as long as that stays
    a few minutes (not ~30 min per frame).
    Owner (13:55): resolution doesn't matter for drafts - 720p is fine if it saves time. Draft standard from now
    on: ONE 1280x720 frame at final quality (final samples, wet materials, reflections) + one composited weather
    frame (rain, splashes, puddle reflections) = the real look, target ~1-2 min per draft.
31. The street reflection of the entrance blade sign doesn't match the sign: the big green smear on the road is
    left over from the old d.gg neon colours; the reflection must come from the current DinkDonk blade (yellow hood,
    green face, gold bell, "DD") - colours and shape - and likewise every reflection must match its real source
    (rooftop DINK DONK neon, cafe, shops). The new 720p final-quality drafts with one weather frame exist to check
    exactly this: rain, splashes on the ground, puddle reflections, wet roofs.

## Round 6 feedback on draft 4 (02 Nov ~14:35)
32. Reflections are real (Cycles ray-traced from the current scene, no proxy lights) but read as fake: under the
    DD blade the wet asphalt acts as a near-perfect mirror, so the reflection is a crisp copy of the emote ("looks
    like the image of the emote"); elsewhere small lights become round red/green blobs (isotropic roughness).
    Fix in the material, not with fakes: rough asphalt base with varied/micro roughness and grain, a thin water
    film of varying thickness on top (true puddles only in low spots, sharp-ish edges), fine rain-impact
    micro-ripple normals everywhere, so neon reflections stretch into long broken vertical streaks with roughly
    the source colour/shape, like a real rainy street (also sidewalk and roofs).
33. KEEP the ray-traced periodic ripples (owner loved the first 16 frames). Scene-wide water audit: draft 4 put
    ripples only on materials matched by name (puddle water, asphalt, paving, roof felt, wet stone/concrete) -
    everything else stayed dry-looking (e.g. the bus-shelter roof, AC unit tops). Every upward-facing outdoor
    surface gets the right rain response by material: water/puddles -> ripple rings; roof felt/asphalt/paving ->
    wet sheen + rings in puddles; metal (AC tops, shelter roof, dumpster lids, sign boxes, railings, fire
    escapes) -> beading, small splash crowns, drips falling off edges; glass (skylights, shelter roof) -> beads
    and runnels; fabric (awnings, cafe parasols) -> soaked darker look, drips off the hems; ledges/sills/parapet
    caps -> sheen, splashes, run-off streaks down the walls. Codex delivers a coverage map (which surfaces get
    which response) so nothing is missed.
34. Owner (14:50): the leftover noise in the ripple clip may actually read as tiny raindrops hitting the
    water ("rain drops come in all sizes; the small ones just make this noise effect"). Plan: keep the render
    itself clean (render noise is random everywhere - walls, dry interiors - and VP9 turns it into blocks), and
    add that effect on purpose: a fine micro-impact layer on WET surfaces only (tiny short-lived specular
    glints/pinpricks of many sizes, density following the rain), so it looks like small drops, stays seamless
    and compresses cleanly. Show it next to the noisy version in a draft so the owner can pick.

## Round 7 feedback on draft 5 (02 Nov ~16:15) - collecting
35. Move the YEE vs PEPE turf-war graffiti from the alley into the RESTROOM: vandalism on the stall partitions,
    stall doors, tiles or mirror - Sharpie/marker scrawl and a bit of scratched etching, the way public restrooms
    get tagged (YEE NEVA LOSE crossed out by PEPE WINS, the tiny dino re-tag), small and messy, readable at a glance
    when zoomed. The alley keeps ABSOLUTE CINEMA on the back wall.
Claude's own notes on draft 5 (to fix in the same round): the bus destination still says "95 ROXY" (make it the
d.gg transit line); the CABGE sign overlaps the NOODLES sign (give the greengrocer its own frontage); the
LOOKALIKE / RE-ELECT posters and the PEPE graffiti are on free-standing boards in the alley - paste/spray them
onto real walls; ripples read as ring outlines in a still - check they stay soft.
36. Rooftop DinkDonk emote neon = classic 2-state neon animation: two separate tube sets that switch on/off
    alternately - state A arm + bell DOWN, state B arm raised with the bell UP (Pepe ringing the bell). The off
    set stays visible as dark unlit glass. In the final it runs as part of the loop (state change ~2-3x/s, or a
    ring rhythm: up-down-up-down-pause); in the draft show both states.
37. New ad with the DGG emote "EatFresh" (ref: roxy3d/ref/eatfresh-emote/EatFresh.png + EatFresh-x12.png: a blue
    chibi character with rosy cheeks biting a sub sandwich): the emote + slogan "EAT OUR FRESH NOTHING BURGERS"
    (or close), 90s fast-food ad style, parody only - no real sandwich-chain logo, name, colours or typeface.
    Placement: a good free ad surface (second billboard, a bus side, the poster wall, a shop window poster).
38. The small DinkDonk emote neon on the entrance blade by the bus stop duplicates the big rooftop one: reimagine
    it as a different DGG meme neon, or remove it. Claude's proposal: the shortlist alternate #25 "Anything
    else?" as a small script neon (owner to confirm).
    Owner (16:25): yes - the entrance blade neon becomes "Anything else?" (small script neon, shortlist #25).
39. Back alley still too clean: really rough pavement (broken, heaved and patched asphalt/concrete, potholes with
    water, crumbling edges, oil stains, weeds in cracks, grime gradients along the walls) and loose litter ON the
    ground - flattened/unfolded soggy cardboard, scattered papers and flyers, a wet newspaper, crushed cups and cans,
    cigarette butts, a takeaway box - not trash bags. Wet and stuck to the ground, catching a bit of light; keep
    the walker/route areas readable.
40. Bus stop too simple: a proper 90s bus shelter - steel frame with scratched/etched glass or perspex side and
    back panels, a curved or flat roof with a lit route header ("95 / d.gg transit"), a bench (slatted or perch
    seat), the ad lightbox (keep the travel ad + PICK ONE call box), a route map/timetable case, a stop pole with
    its sign, a litter bin, maybe some stickers, a bit of graffiti and gum. Riders still step out of the bus at the
    stop and walk off along the sidewalk - keep that path clear; people may sit on the bench (page can use it).
41. Bus route number (owner: "keep a two-digit number related to DGG, you choose"): Claude picked 05 from the
    meme session's candidates (memes/SHORTLIST.md "Bus route number"): "Movie in 5". Destination "05  DINK DONK",
    plates "DGG 05", shelter timetable "Route 05 - every 5 min". Alternatives if the owner prefers: 13, 11.

## Round 8 feedback on draft 6 (02 Nov ~17:05) - collecting
42. Close-ups in drafts: use the same isometric camera, just zoomed (smaller ortho scale centred on the spot) -
    never extra angled "review" cameras (owner noticed the different perspectives).
43. The WCAT billboard (liked) moves from the theatre roof (top right) to the roof of the top-left apartment block,
    as a rooftop billboard facing the other way (northwest-pointing / the other iso axis, readable from this
    camera). Picture = the actual DGG emote "wcat" (ref roxy3d/ref/wcat-emote/wcat.png + wcat-x12.png: a beige cat
    in a dark suit, white shirt, red tie, holding a brown briefcase), painted large in billboard style. Copy is
    about business, e.g. "WCAT & ASSOCIATES - for all your bidness needs" / "let's do bidness." The theatre-roof
    billboard spot becomes free for another ad (EatFresh or a later meme).
    Style (owner, 17:10): the billboard matches the emote's serious-business tone - not mostly white: dark,
    rich ground (deep navy/charcoal or oxblood, maybe a subtle pinstripe or marble), gold serif lettering with a
    slight bevel/foil look, a thin gold rule/frame, small "EST." or "ATTORNEYS & ADVISORS"-style secondary line;
    lit by gooseneck lamps; weathered like everything else.
44. Wayfinding signs at the junction ("WC ◀" and "▶ 1-3" hanging sign) and the restroom sign read as floating.
    Either attach them clearly (flat on a wall, or a projecting blade on a visible bracket/ceiling rod) or drop
    them - owner is fine with not showing them at all.
    Copy (owner, 17:20): the billboard shows ONLY the wcat emote and the slogan "IT'S JUST BUSINESS." - no
    "WCAT & ASSOCIATES", no secondary lines. Same serious style (dark rich ground, gold serif lettering, gold rule).
45. Walls: the cutaway approach is fine (owner keeps the low cuts) - but make cut heights continuous: the
    tickets wall (box-office back, half height) and the restroom walls next to it (cut lower, showing a sink) must
    follow one rule - neighbouring/connected wall runs share the same cut height, with the wall-thickness cap.
46. Theatre doors: classic padded doors (diamond-button upholstered leather/vinyl, brass push and kick plates), no
    lit porthole windows (owner agreed, 17:30).

## Round 9 feedback on draft 7 (02 Nov ~17:55) - collecting
47. Move the EatFresh "nothing burgers" billboard from the theatre roof to the top-left apartment roof, to the
    right of the wcat billboard (same facing, a pair of rooftop billboards side by side); the theatre roof then has
    only the DINK DONK neon (and its kit).

## Ideas (05 Nov)
48. Frame-rate test: show how the whole lobby (and auditorium) would look with everything at 24 fps and at 48 fps -
    walking, hops, vehicles, camera, bubbles, the baked loops (now 24 fps) and the extra rain. Idea only, not started.
