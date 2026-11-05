# Brief: pre-rendered isometric art for "The Roxy" (Blender)

You are making the background art for an OBS standby screen, `standby/roxy.html` (read it fully first).
The page already works as a **blockout**: a 1920x1080 isometric scene drawn with flat canvas shapes,
where every Destiny.gg chatter is a hopping emote (DOM element) that walks from the street, queues at the
box office, maybe gets popcorn, passes the usher gate and walks through one of 5 screen doors.
The streamer likes the layout and flow but the look is too cheap. They want the look of **late-90s /
early-2000s games with a fixed camera and pre-rendered 3D backgrounds shown as 2D**: Diablo 2,
Fallout 1/2, Baldur's Gate, The Sims 1, Commandos. 3D-rendered, lit, textured, with soft GI shadows,
then used as a flat image.

Your job: build the scene in **Blender 5.2.3** (scripted, reproducible) and render it into image layers that
`roxy.html` can use in place of its flat canvas art. **I (another agent) will do the HTML integration.**
Do NOT edit `roxy.html`, `shared/*`, `index.html`, `README.txt` or any other existing file.
Work only inside `standby/roxy3d/`.

- Blender: `standby/tools/blender-5.2.3-windows-x64/blender.exe`, run headless:
  `blender.exe -b -P roxy3d/build_scene.py -- <args>`. Everything is built from Python (no manual
  editing); keep the scripts readable and re-runnable. Saving a `.blend` too is fine.
- No internet, no downloaded assets: procedural geometry, procedural materials/shader nodes, text
  objects for signage. GPU: NVIDIA RTX 3050 Laptop 6 GB (try Cycles OPTIX/CUDA, fall back to CPU).
- Reference images in `roxy3d/ref/`: `layout-blockout.png` (the current working page; positions of
  everything), `layout-sketch.png` (the approved floor plan), `style-90s-roxy.png` (an earlier canvas
  version whose mood the streamer liked: rainy night city, 90s neon pink/cyan/purple, wet reflections,
  cozy warm interior).

## 1. The camera MUST match the page's projection exactly

The page places everything with this projection (tile units u, v on the floor; z in screen pixels up):

```
P(u, v, zpx) = [ 900 + (u - v) * 60 ,  350 + (u + v) * 30 - zpx ]     (pixels on a 1920x1080 frame)
```

u runs screen down-right, v runs screen down-left, z up. Walkers are DOM elements placed with P(), so
the rendered floor/walls must land on the same pixels. That means a 2:1 dimetric orthographic camera:
- Use 1 Blender unit = 1 tile. Floor point (u, v) <-> Blender (x, y) with whatever axis signs make the
  projection above come out (e.g. x = u, y = -v, depending on camera yaw) - work it out and verify.
- Camera: orthographic, elevation 30 deg (rotation X = 60 deg), yaw 45 deg. Then 1 tile projects to
  (60, 30) px when the ortho scale gives 84.853 px per Blender unit -> ortho_scale = 1920/84.853 = 22.627.
- Vertical: 1 Blender unit in z projects to 84.853 * cos(30 deg) = 73.48 px. So a height given in the
  page as zpx is zpx / 73.48 Blender units (e.g. the back walls are 170 px = 2.314 BU high).
- Position/shift the camera so that P(0,0,0) = (900, 350).
- **Calibration is required:** render small marker spheres at several known (u, v, zpx) points
  (e.g. (0,0,0), (13,0,0), (0,9,0), (13,9,0), (0,0,170)), find their pixel centres in the PNG and
  confirm they match P() within +-1 px at 1920x1080. Keep the check as a script
  (`roxy3d/calibrate.py`) and report the measured errors.

## 2. The scene (keep the floor plan and footprints)

Same layout as `roxy.html` (read its constants: DOORS, WC_V, SNACK, QSLOT, G, J and `buildProps()`).
Footprints of walkable areas and of every prop must stay where they are (walk paths depend on them).
You may make props prettier and add detail, but not move them; if one must change, report its new
footprint in the manifest.

- Building: back-left wall at u = 0 (v 0..9), back-right wall at v = 0 (u 0..13), 170 px high. The front
  and right side are cut away (dollhouse view, like The Sims): show the floor slab edge, no front walls
  except the low pieces listed below.
- Lobby (u 3..13, v 3..9): 90s cinema carpet (confetti / geometric pattern), purple/teal palette.
- Corridors: left wing (u 0..3, v 0..9) and right wing (u 3..13, v 0..3), darker carpet.
- Screen doors in the outer walls: screens 1-2 on the u = 0 wall at v = 6.4 and 4.0; screens 3-5 on
  the v = 0 wall at u = 4.8, 8.2, 11.2. Door 1.1 tiles wide, 114 px high, padded double doors with
  portholes, warm light leaking under them.
- Restroom door on the u = 0 wall at v = 8.3 (0.8 wide, 104 px).
- Above each screen door: a lit **blank** marquee box (the page overlays the film title as DOM text).
  Box: camera-facing, about 176 x 92 px, its bottom-centre at P(door, zpx = 124) - i.e. for the
  u = 0 wall at P(0, v_door, 124), for the v = 0 wall at P(u_door, 0, 124).
- Beside each door: an empty lit **poster frame** on the wall plane (the page maps the poster image onto
  it). Frame inner area: 0.8 tiles wide, from zpx 23 to 128. Left wall (u = 0): spans v from
  (door - 0.75) down to (door - 1.55). Right wall (v = 0): spans u from (door + 0.75) to (door + 1.55).
- Low partition walls (34 px high) between lobby and corridors: along u = 3 for v 4.4..9 and along
  v = 3 for u 4.4..13; the opening at the lobby's back corner (u, v 3..4.4) is the usher gate.
- Front: low wall u 0..3 at v = 9; glass storefront (30 px, low) at v = 9 for u 3..8.4 and 10.6..13
  with the entrance gap 8.4..10.6 and two door posts at u = 8.4 and 10.6.
- Box office counter u 4..7, v 7..7.8 (42 px) with a glass cashier screen on top (to 84 px) and two
  ticket windows; the cashier (a DOM emote) stands behind it at (5.5, 6.55). Queue stands at v = 8.38.
- Snack island u 8.2..11.8, v 4.6..6.0 (42 px), with a glowing popcorn machine (u 9.6..10.4,
  v 4.9..5.5, to ~108 px), soda fountain, candy case. Clerk stands behind at (10.0, 4.15).
- Usher podium u 4.6..5.1, v 3.5..4.0 (40 px) with a little lamp; usher stands at (5.5, 3.75).
- Bench u 6.4..7.9, v 3.25..3.75. Arcade cabinet u 12.0..12.7, v 7.5..8.2 (82 px), screen glowing.
  Two cardboard movie standees: u 12.2..12.62 at v 5.0, and u 6.0..6.42 at v 6.3 (92 px).
- Outside: sidewalk v 9.15..10.5, curb, wet street v 10.6..13.5 with lane dashes; bus stop shelter
  u 0.4..2.0, v 9.3..9.55; street lamp at (5.07, 10.37); vertical neon "ROXY" blade sign on the front
  corner (u -0.75..-0.05, v 9.1..9.3, from 110 to 300 px). Night skyline behind; a tower behind the
  cinema on the right carrying a big video billboard.
- **Billboard / green screen**: the page draws a pure green rectangle at x 1296, y 40, 576 x 324 on top
  of everything. Render the billboard's frame around exactly that rectangle (neon pink/cyan trim on a
  dark tower). Nothing important may be inside the rectangle (it is covered).
- Static signage can be baked into the render: "TICKETS" neon over the box office, a backlit "SNACK
  BAR" menu (Popcorn $4.50, Soda $2.75, Nachos $3.25), the gate sign "◀ 1-2 · 3-5 ▶" hanging over the
  usher gate, a "RESTROOM" sign over the WC door, the ROXY blade. Tell me which ones you baked so I can
  remove the DOM versions.
- Mood: rainy night, 90s neon (pink #ff5fb0, cyan #7ff7f0, purple), warm interior pools of light,
  wet glossy street and sidewalk with neon reflections, slight haze. Cozy, readable, not too dark:
  emotes (about 50 px tall) must read well on the floor.

## 3. Render outputs (in `roxy3d/out/`)

Render at **1920x1080 and 3840x2160** (same framing, 2x) with Cycles + denoise. Outputs:
1. `bg.png` - the full scene **without** the occluder objects below (everything that is always behind
   walkers: sky, skyline, tower, street, sidewalk, floors, back walls, doors, frames, wall signs).
   Shadows and light from the occluders should still fall on the floor (use holdout / indirect-only /
   render-visibility tricks so the floor looks right).
2. One RGBA sprite per occluder object (`occ_<name>.png`, cropped to its bounding box, premultiplied
   alpha handled correctly, clean edges): partition walls, front low wall, glass panes, door posts, box
   office, snack island (+ machine), podium, bench, arcade, standees, bus stop, street lamp, ROXY blade.
   They must line up pixel-perfectly when drawn over `bg.png` at their offsets.
3. `full.png` - everything together (for checking).
4. Optional `glow.png` - additive light/haze layer (neon halos) the page can put over the walkers with
   `mix-blend-mode: screen`.
5. `manifest.json`:
   ```json
   { "size": [1920, 1080], "scale2x": true,
     "bg": "bg.png", "glow": "glow.png or null",
     "occluders": [ { "name": "boxoffice", "file": "occ_boxoffice.png", "x": 0, "y": 0, "w": 0, "h": 0,
                      "footprint": [u0, v0, u1, v1], "height_px": 84 } ],
     "baked_signs": ["tickets", "snackbar", "gate", "restroom", "roxy"] }
   ```
   x/y/w/h in 1920x1080 pixels; the 2x files are the same names with `@2x` before `.png`.

## 4. Process and quality

- Build in steps and LOOK at your renders (open the PNGs) after each step. Do low-sample previews
  while iterating; final renders with enough samples + denoise.
- Compare against the references. The bar: it should look like a pre-rendered background from a late
  90s PC game, not like flat vector shapes.
- Keep render times reasonable (6 GB GPU). Write `roxy3d/NOTES.md`: how to re-render, render times,
  calibration errors, anything you changed or could not do.
- Final message: what you produced, calibration result, which signs are baked, footprints that
  changed, known issues.
