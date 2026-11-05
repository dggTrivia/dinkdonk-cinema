# Brief 42 (RENDER): auditorium "house lights down" state, final quality, both scales

The page will dim the house lights near the end of the film download (phase `dim`), then the film starts on the screen.
A CSS darkening is only the fallback; render the real lights-down state from the final draft 11 scene
(`roxy_cinema_draft11.blend`, `build_cinema_draft11.py`, `qa11/cinema_layout_11.json`). Only write inside roxy3d/;
no page edits (another Codex session is editing the page). Local GPU only.

## The look
A real cinema seconds before the feature: house lights (overhead pools, broad fills, most sconce light) down to a
low glow; the wall sconces barely lit; aisle/step lights, the tunnel-mouth spill, EXIT signs (green at the tunnel,
red emergency) and the wheelchair plaques' faint reflections stay; the room reads as dark but the tiers, rows and
stairs are still readable (seat backs must still separate from the floor so seated chatters read). The SCREEN: no
light from the projector in this render (the page/OBS puts the pre-show or film there), and keep it unlit and
unchanged in shape; a very faint cool bounce from the screen onto the first rows is allowed ONLY if it never touches
the screen quad itself. Same camera, same geometry, no other change.

## Deliverables
- `qa11/cinema_draft_11_dim.png` (1920x1080) and `qa11/cinema_draft_11_dim@2x.png` (3840x2160), same pipeline as
  draft 11 (say native 4K + 2x2 area or how).
- `qa11/draft11_dim/` - the depth slices cut from the dim images with EXACTLY the same names, x/y/w/h, z_index and
  alpha masks as `qa11/draft11/slices` (only the RGB comes from the dim render), both scales; the entrance door sheet
  in the dim state, both scales (same cells/frames/cutout as draft 11).
- `qa11/cinema_layout_11.json` gets `page_layers.dim = { image, image_2x, slices_dir, slices_dir_2x (or per-slice
  file/file_2x lists in the same order), door_file, door_file_2x }` - add the key, change nothing else in the file.
- Checks: dim bg + dim slices = dim bg exactly (both scales); slice masks identical to draft 11's; screen quad pixels
  unchanged in shape and unlit; a short note on how readable the seats/rows are (luminance numbers like draft 7/8).
- Report `qa11/CINEMA-DRAFT-11-DIM.md`, STATUS, stop.
