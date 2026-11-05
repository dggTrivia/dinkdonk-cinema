# Brief 56: PRODUCTION of draft 23 (DINK DONK "CINEMAS" + bell at half speed) for the live page

Owner (05 Nov) on qa10/draft23-dinkdonk-cinemas.png: "Yes, render it". So: the full production pass in exactly the
draft-23 look (out10h/ + NOTES-55.md are the reference; no new look decisions), with ONE fix from your read-only
critique (codex-55-critique.txt point 7): re-aim / shield the moved central floodlight so it gives the sign and roof
the same restrained warm wash under O/M as before the move, with no stray white glint above the O (around
(1077,294) in the comparison) and a clean bulb rhythm. Bell: A12/B12 (0.50 s per state), seamless in the unchanged
6 s / 144-frame / 24 fps loop. Local GPU only, no cloud. Source scene read-only; production edits go into a new
saved copy, never over cloud/bundle/scene.blend.

## Render
Everything NOTES-54/55 list as affected, at production settings and with the same pipeline/contracts as the live
out10 pack: base/bg/lit_bg(+dry)/full (1x and @2x), light_loop (all its sizes/codecs the manifest lists), rain_fg if
the new sign geometry changes its holdout, every occluder / depth slice / prop loop / static glow whose pixels change,
the out10mist passes if the sign changes them (catch/height/light/rim), and the derived ad-frame crops. Anything not
affected stays byte-identical (say which and how you checked). Check the loop wrap (frame 143 -> 0) for the bell and
every other loop you re-render.

## Package
New staging pack roxy3d/out10i/ = full copy of live out10 + the re-rendered files, manifest/checksums.json/
validation.json refreshed (same keys and contracts as out10, so the page needs no code change). Plus
roxy3d/out10i-copy-list.txt: every file that differs from live out10 (NEW / CHG) - Claude copies only those into
out10 after testing with ?artdir=out10i. Live out10/, out10mist/ and standby/roxy.html stay untouched.

## Deliver
NOTES-56.md (files changed, sizes, decoded VRAM 1x/@2x if it changes, render time per output, validation incl. loop
wraps and byte-identical checks), and one check image qa10/draft24-dinkdonk-production.png (1280x720: live out10
lit frame crop | out10i lit frame crop of the sign, state A, plus the same for state B) - no owner sign-off needed on
it, Claude checks it in the page. STATUS line, stop. If the laptop sleeps or a render dies, resume from what's done
(don't restart finished outputs) and say so in the notes.
