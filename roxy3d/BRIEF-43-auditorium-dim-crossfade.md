# Brief 43 (PAGE): use the rendered lights-down state in the `dim` / `film` phases

Page work in `standby/auditorium.html` only (same rules as BRIEF-38/40/41; report `roxy3d/qa11/PAGE-43.md`, STATUS).

`qa11/cinema_layout_11.json` now has `page_layers.dim` (see `qa11/CINEMA-DRAFT-11-DIM.md`): a rendered house-lights-
down background (`image`, `image_2x`), depth slices with EXACTLY the same names / x / y / w / h / z_index / masks as the
lit ones (`slices[]` with `file` / `file_2x`), and the dim entrance door sheet (+ 2x).

- In `dim` and `film`, crossfade (~6 s, ease in-out) from the lit art to the dim art: background, every slice (pair
  each lit slice with its dim twin of the same name and stack the twin directly above it with the same z_index,
  fading its opacity), and the door sheet (play the dim sheet while dim). Back to lit in `up` / `seating`.
- Remove the CSS brightness darkening for the art when the dim set is present (keep it only as the fallback when
  `page_layers.dim` is missing). Emotes may still dim slightly (as now); names/bubbles unchanged.
- Use the same 1x / 2x selection as the lit art; preload the dim set (both images it will need at the current scale)
  well before the fade so nothing pops.
- Keep the pre-show / green quad and everything else unchanged.
STATUS line, stop.
