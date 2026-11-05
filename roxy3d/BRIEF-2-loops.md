# Brief 2: pre-rendered ambient LOOPS for The Roxy

Follow-up to BRIEF.md (same rules: work only in `roxy3d/`, scripts re-runnable, keep the camera and
calibration exactly as they are, don't touch the page or shared files).

The streamer loved the direction and wants the static world to feel alive the way late-90s games did
it: **pre-rendered animation loops** (think Diablo 2 torches, Fallout neon, rain in Commandos), not
stills. Chatters, posters and texts stay dynamic in the page; everything ambient should be a seamless
pre-rendered loop: rain falling, splashes on the pavement and in puddles, ripples in the wet street
reflections, neon tubes buzzing / flickering / slowly shifting colour, the billboard frame's chase
lights, the light leaking under the screen doors flickering (projector light), the arcade screen,
the street lamp, maybe a passing car's headlight sweep across the wet street.

## How it plugs into the page (please produce exactly this)

The page stacks: `bg` still -> **light loop video** (CSS `mix-blend-mode: plus-lighter`, i.e. purely
additive) -> walkers + occluder sprites (z-sorted) -> UI. So:

1. `out/base.png` (+ `base@2x.png`): the static background, rendered with every animated light at its
   **minimum** (neon tubes dim/unlit glass, no rain, no splashes, reflections of those lights absent,
   door light at its lowest). Same framing/calibration as before. Occluder sprites must still match it
   (re-cut them from the same base render if lighting changed; same manifest format).
2. `out/light_loop.webm`: 1920x1080, VP9 (Blender's FFmpeg output can write WebM/VP9 directly;
   there is no separate ffmpeg on this PC), seamless loop, 24 fps, 4-6 s. Each frame =
   **animated frame minus base** (clamped at 0), i.e. only the light the animation ADDS on top of the
   base, on black. Added together with base.png it must reproduce the fully lit, animated scene.
   Keep the bitrate sane (target < 15 MB for the loop) and avoid banding/compression mush on the dark
   gradients (some film grain or dithering in the render helps and fits the 90s look).
3. Seamless: frame N+1 == frame 0. Use periodic drivers (sin/cos of 2*pi*frame/N), 4D noise sampled
   on a circle for ripples, rain/splashes whose spawn times wrap around the loop, flicker patterns
   that repeat with the loop length. Verify by comparing the last frame against the first.
4. Keep the animated stuff on the environment (street, sidewalk, puddles, walls, signs, billboard,
   doors, sky). The occluder props (counters, glass, low walls, bus stop, lamp, blade sign...) are
   static sprites drawn ABOVE the loop, so light animating on top of them would be covered: either keep
   their own lights static (baked into base and their sprites) or tell me which regions get covered.
5. Also produce `out/loop_preview.mp4` or a few still frames `qa/loop_f000.png`... of base + loop added
   together, so the result can be checked without the page.
6. Render budget: the laptop GPU did a full 1080p frame in ~27 s. Pick samples/denoise settings so the
   loop renders in well under an hour, and watch for denoiser flicker between frames (temporal
   stability matters more than per-frame detail; consider rendering the rain/splashes as separate
   simple emission passes and compositing them).

## Look notes from the streamer and me

- Push the late-90s pre-rendered feel further: richer surface texture and grime (worn carpet, scuffed
  floor edges, dirty wet asphalt with oil sheen, water stains on walls), less clean "modern low-poly"
  plastic. Slight film grain. Keep it cozy and readable.
- The blank marquee boxes above the doors and the empty poster frames stay (the page fills them).

Update NOTES.md and the manifest (add `"base"`, `"light_loop"`, loop length/fps) and end with the same
kind of report as before.
