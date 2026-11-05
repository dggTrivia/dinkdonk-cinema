# Rain realism: techniques for roxy3d

Research only (2 Nov 2026); nothing rendered or tested. **[U]** = unverified (my inference, or a source not read in full). Loop terms: T = 48 frames, φ = (frame mod 48)/48. Source numbers [n] refer to the list at the end.

## Ranked shortlist

| # | Technique | Gain | Effort | Cost / VRAM | Loops by |
|---|---|---|---|---|---|
| 1 | Wet-layer shader: porosity darkening plus Coat water film, in zones | Very high | Low | ~0 | Static |
| 2 | Reflection catchers placed off-frame | Very high | Low | ~0 | Static |
| 3 | Standing water from a water-level mask (roofs, road dips) | High | Low–med | ~0 | Existing ripples |
| 4 | Stateless Geometry Nodes drips, pours and splashes | High | Medium | Low | Period divides 48 |
| 5 | Gutter and curb flow strips (two-phase) | Med–high | Medium | Low | Two-phase, T=48 |
| 6 | Tyre spray and mist sprites lit by the scene | High (cars) | Medium | Med (sprite only) | 12-frame stateless |
| 7 | Tyre tracks via a "squeegeed" second plate | Medium | Low–med | 1 extra still | Page |
| 8 | Fake headlight cone plus rain-layer mask | Medium | Low | ~0 | Page |
| 9 | Puddle wakes from Dynamic Paint sheets | Medium | High | Med (bake) | One-shot |
| 10 | Facade run-down streaks | Medium | Low | ~0 | Static |

## 1. Wet-layer shader

**Look.** Porous surfaces go darker and more saturated, with a sharp water film reflecting over a base that keeps its own roughness.

**Build.** One node group `WetLayer(wet, porosity)` before every outdoor Principled BSDF [1]:
- Darken: `factor = lerp(1, 0.2, porosity·(1−metallic))`, then `albedo *= lerp(1, factor, wet)`. Asphalt goes from about 0.12 to about 0.08.
- Lower roughness only partly: `rough = lerp(rough, rough·factor, 0.5·wet)`.
- Model the water as **Coat**: Weight = wet, Roughness 0.02–0.05, IOR 1.33 [9]. A rough base under a mirror coat is the wet-asphalt look.
- Zones from one depth value: **wet** (darken only) → **drenched** (Coat on, damped normal) → **pool** (normal blended to the geometric normal, Coat roughness about 0.005, ripples on). Lagarde blends the normal toward the vertex normal in proportion to depth [1].
- Metals and signs: Coat and beads only, no darkening. Darken albedo rather than tinting it blue [3].

**Cost and bpy.** Coat adds one glossy lobe; this is the cheapest gain on the list. Simple to build and insert from a script.

## 2. Reflection catchers (key for an orthographic camera)

**Why.** An orthographic puddle mirrors what lies further along the view direction, rising at the camera elevation e. At e ≈ 35° a puddle shows objects at distance D *behind* it and height ≈ 0.7·D, mostly outside the frame. Water Fresnel at that angle is only about 4% (about 6% at e = 30°; computed for n = 1.33) **[U]**. Only bright emitters over dark bottoms read as reflections.

**Build.**
- Put emissive cards beyond the far frame edge: back-facing signs, lit window grids, a sky-glow gradient.
- Ray visibility on the cards: Camera off, Diffuse off, Glossy on [10].
- Pool bottom albedo ≤ 0.04.
- Raise emitter strength rather than faking reflectivity; HDR glare does the rest.
- Keep Light Tree on.

**bpy.** `obj.visible_camera = False`, `obj.visible_diffuse = False`.

## 3. Standing water: ponds, sheets, shorelines

**Build (mask, no new geometry).**
- In Geometry Nodes, `depth = waterLevel − height`: displaced Z plus low-frequency noise, smoothed with **Blur Attribute**.
- Gate with `normal.z > 0.9` so water only ponds on surfaces facing up [4].
- Store depth as an attribute. In the shader, Map Range it into zones: depth > 0 pool; −1–0 cm drenched; −3 to −1 cm wet.
- Set the water level per region: road dips, roof ponds behind parapets, the curb line.
- Commercial puddle shaders use the same height input. Their docs give a calm-water roughness of about 0.005 and 64–128 samples with OIDN [5]. The same mask can also drive bump strength [6].

**Deep, clear roof ponds.**
- Add a flat plane at the water level: Transmission 1, IOR 1.33, roughness 0.
- Shadow visibility off, so it casts no glass shadows; transmission bounces ≥ 4.
- Only worth it where a visible bottom matters; refraction is slower **[U]**.

## 4. Drips, pours and splashes: stateless, so they loop exactly

**Build.** Everything is a function of the frame number; no simulation:
- **Emitters:** the agent tags edges `drip_edge` (awnings, gutters, sign bottoms, AC units). Resample every 3–8 cm with jitter.
- **Timing per drop:** period `P ∈ {12, 16, 24, 48}`, `τ = (frame + hash(id)·P) mod P`.
- **Motion:** bead swells while `τ < τh`, then falls `z = z0 − ½g((τ−τh)/24)²`.
- **Landing:** a static **Raycast** downward gives the landing point. A 3 m fall takes about 0.78 s (≈19 frames), so it fits a 24- or 48-frame period.
- **Splash:** after impact, instance the existing crown scaled over 4–6 frames, plus a 12-frame ring ripple.
- **Pours** (downspouts, AC drains): ballistic curve → Curve to Mesh, transmission shader. Scroll the normal noise along the curve by `φ·k·L` with k an integer, add 4D-noise wobble, and put a foam patch at the base.
- Motion blur, shutter 0.5.

**Cost and bpy.** Instances are cheap; thousands fit easily in 6 GB. Author once in an asset .blend and append from scripts.

**Prior art.** Geometry Nodes rain with drops, splashes and ripples [11]; a Reddit post of Geometry Nodes rain on a puddle [12] (no write-up, method **[U]**); CG Cookie's 5.2 drip-and-splat chapter [13].

## 5. Gutter, curb and run-off flow

**Build.**
- Author curves along curbs, valleys and gutters → flat strips 15–30 cm wide. Store U = spline parameter × length.
- Two-phase flow [7][8]:
  - `pA = φ`, `pB = frac(φ + 0.5)`.
  - Sample the ripple normal at `U − pA·L` and `U − pB·L + offset`.
  - Blend with `w = |1 − 2·pA|`.
  - Each phase resets only while its weight is zero, so the period is exactly 48.
- Narrow the strip toward drains. Roof-edge sheets use the same strip and feed the pours in item 4.
- Full road flow maps from the height gradient are possible but fiddly **[U]**.

## 6. Tyre spray and trailing mist sprites

**Build.**
- **Scene:** a sprite scene with the same orthographic camera shifted to the lane, Film Transparent. Set the linked city collection to **Indirect Only** [14]: the spray is lit by and reflects the real neon, but the road doesn't render.
- **Droplets:** Geometry Nodes points (rendered natively as a point cloud). Emit from the rear of the contact patch at 2–6 m/s back and up plus car velocity, with gravity and drag; life 6–12 frames; radius 1–3 mm; glossy/transmission shader; motion blur.
- **Mist:** Points to Volume from the older points → Principled Volume, low density, anisotropy 0.5–0.7 so it glows when backlit **[U values]**.
- **Light linking** [9]: a headlight spot that lights only the spray and mist.
- **Add a looping 12-frame "trail" sheet** (`t = frac(frame/12 + hash(id))`) beside the existing one-shot burst.
- **In the page:** droplets as premultiplied alpha over, mist as screen/additive.
- **Lighting by position:** render 2–3 lane positions, or render grey and tint per area **[design choice]**.
- **Cost:** the volume exists only at sprite size, so it's fine on 6 GB.
- **bpy:** `layer_collection.indirect_only = True`; light linking through `obj.light_linking`.
- **Prior art:** Auto Car Driver (paid wet-road spray add-on, method not shown) [15]; a Houdini approach that emits spray only from puddle areas of a wet map [16].

## 7. Fading wet tyre tracks

Tyres squeeze the film away, leaving darker, less mirror-like stripes that re-wet within about 1–3 s **[U, observational]**.

**Build.**
- Render **plate B**: the same road still with Coat 0 and ripples off.
- The page paints wheel stripes into an offscreen mask that fades exponentially (about 0.5 s half-life **[U]**), then composites B over the background through it.
- Reflections stay physically consistent.
- Fallback: a multiply decal (−10–20%), which can't remove reflections correctly.
- In-Blender equivalent: Dynamic Paint wet tracks [17].

## 8. Headlight beams catching rain

- **Beam:** add a fake cone to the vehicle sprite — a truncated cone with its axis along local Z, emission × tip-to-base gradient × facing falloff, composited additively [18][19].
- **Rain in the beam:** the rain is already 2D, so the page multiplies rain brightness by the beam mask. Streaks light up inside the beam at no render cost.
- Avoid true volumetric cones in the background: slow and noisy.

## 9. Puddle wakes

- For each puddle on a fixed lane, add a Dynamic Paint **Waves** canvas.
- Animate wheel brushes at lane speed. A negative brush factor gives a wake, and waves only form while the brush intersection changes [20].
- Bake, then render 16–24 frames over the Indirect Only city with the existing ripples off. The page plays the sheet when a car crosses and crossfades back to the loop.
- Headless baking needs an operator context override **[U]**.

## 10. Facade streaks and more reflections

- Noise stretched about 20× in Z, masked below sills and ledges, drives `wet` → darker, glossier vertical streaks.
- Glossy bounces 4–6 so wet walls reflect the wet road; Filter Glossy ≤ 0.3 for mirror pools.
- Check denoised pools at 1:1; they may smear **[U]**.
- Layer rain correctly and don't overdo gloss [21].

## Loop toolbox

- **Moving noise:** set noise to 4D. On ground: Vector = (x, y, R·cos 2πφ), W = R·sin 2πφ gives constant speed and an exact loop. A sine into W alone eases in and out [22].
- **Stateless particles:** seed from the id, `t = frac(frame/P + hash(id))`, with P dividing 48.
- **Stateful effects** (Dynamic Paint, simulation zones): bake 144 + N frames and crossfade the tail into the head, or ship as one-shot sprites [23].

## First draft test (one 720p still on the 3050)

1. WetLayer (darkening plus Coat) on asphalt, sidewalk and one roof, with depth zones.
2. 3–4 reflection catchers beyond the far frame edge.
3. One road-dip sheet and one roof pond from the water-level mask.
4. One awning drip line plus one gutter pour with splash, motion blur on.

Settings: 256 samples, OptiX denoise, Glossy bounces 6, Light Tree on, clamp indirect 10. A/B against the current still; inspect the pools at 200%.

## Research notes

- reddit.com fetches were blocked. Arctic Shift answered one query, then returned HTTP 422, so Reddit coverage is thin.
- No technical breakdown of *Blade Runner 2049* or *Cyberpunk 2077* wet roads was found; only press coverage of Cyberpunk patch 1.31 (14 Sep 2021).

## Sources

1. Lagarde, "Water drop 3b – Physically based wet surfaces", 14 Apr 2013 – https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/
2. eviltak, Unity wet shader after Lagarde (gist, n.d.) – https://gist.github.com/eviltak/e04b83ffdb91aa3d477bbfe0ca370da7
3. Axton, "Procedural PBR Wetness/Puddle Shader – UE4" – https://axton.artstation.com/projects/nYeAJe
4. Mochie, Splat Mapping Shader wiki (puddle height blend) – https://github.com/MochiesCode/Mochies-Unity-Shaders/wiki/Splat-Mapping-Shader
5. Procedural Wet Puddles Master docs (Blender 4.0–5.1) – https://superhivemarket.com/products/procedural-wet-puddles-master/docs
6. BlenderArtists, "Cycles puddle material" – https://blenderartists.org/t/cycles-puddle-material-shader-now-with-example/544715
7. Vlachos, "Water Flow in Portal 2", SIGGRAPH 2010 – https://www.advances.realtimerendering.com/s2010/Vlachos-Waterflow(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
8. Grimes, GDC 2011 Portal 2 shading – https://www.hlportal.de/files/GDC2011_BronwenGrimes_NonstandardTextures.pdf
9. Blender manual, Principled BSDF (Coat) – https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html ; Blender 4.0 Cycles notes (light linking, Nov 2023) – https://developer.blender.org/docs/release_notes/4.0/cycles/
10. Blender manual, Cycles object visibility – https://docs.blender.org/manual/en/dev/render/cycles/object_settings/object_data.html
11. Kuldeep Singh, "Procedural Rain effect with Geometry Nodes in Blender – Detailed Tutorial", 9 Jun 2022 – https://blenderartists.org/t/procedural-rain-effect-with-geometry-nodes-in-blender-detailed-tutorial/1384620
12. r/blender, "Tried to create rain on puddle with geometry nodes", 7 Oct 2022 – https://www.reddit.com/r/blender/comments/xy7grk/
13. CG Cookie, Core 5.2 Fundamentals of Geometry Nodes – https://cgcookie.com/courses/core-5-2-fundamentals-of-geometry-nodes
14. Blender manual, Collections (Indirect Only) – https://docs.blender.org/manual/en/dev/scene_layout/collections/collections.html
15. Auto Car Driver – https://superhivemarket.com/products/auto-driver
16. SideFX forum, wet-map spray – https://www.sidefx.com/ja/forum/post/228719/
17. Sardi Pax, wet tyre track with Dynamic Paint (via Lester Banks, date [U]) – https://lesterbanks.com/tag/blender-dynamic-paint-waves-tutorial/
18. BlenderNation, "How to fake volumetric light cones", 29 Mar 2020 – https://www.blendernation.com/2020/03/29/how-to-fake-volumetric-light-cones-60-second-tutorial-3/
19. BlenderNation, "Caminandes: Creating a simple Volumetric Light Beam", 22 Feb 2016 – https://www.blendernation.com/2016/02/22/caminandes-creating-a-simple-volumetric-light-beam/
20. Blender manual Dynamic Paint commit (wake tip), Sep 2020 – https://lists.blender.org/pipermail/bf-docboard-svn/2020-September/000962.html
21. 80.lv, "How Rain Works in Video Games", 10 Nov 2023 – https://80.lv/articles/how-rain-works-in-video-games
22. BlenderArtists, "How to loop procedural noise seamlessly" – https://blenderartists.org/t/how-to-loop-procedural-noise-seamlessly/1337153
23. BlenderNation, "The ultimate guide to seamless looping animations in Blender 4.2", 8 Aug 2024 – https://www.blendernation.com/2024/08/08/the-ultimate-guide-to-seamless-looping-animations-in-blender-4-2/
