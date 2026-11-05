import json
from pass9_common import ROOT,QA,OUT,status

def main():
    m=json.loads((OUT/'manifest.json').read_text());r=json.loads((QA/'final_validation.json').read_text());v=json.loads((QA/'video_metadata.json').read_text());p=json.loads((QA/'prop_validation.json').read_text())
    table='\n'.join('| '+k+' | '+str(e['size'][0])+' x '+str(e['size'][1])+' | '+f"{e['bytes']:,}"+' | '+f"{e['average_mbps']:.3f}"+' | '+f"{e['decode_vse_ms_per_frame']:.2f}"+' |' for k,e in v.items())
    text=f'''# Pass 9 — d.gg inside the world

Complete pack: `out9/`, derived from `out8b/`. Main scene: `roxy_pass9.blend`.
The lit still was saved to `qa9/preview_1.png` before expensive weather loops.
`qa9/STATUS.md` records completed stages with timestamps, including refinements and rechecks.

## Delivered art

- Full-height storefront glass, wet sills, mullions, transoms and a header; opening hours, NO SMOKING, a small one-sheet and a d.gg sticker. The entrance remains an open route. The header has its own three depth slices.
- Five physical two-row LED housings and dark dot fields, sized for 18 six-column characters. Their title and score content belongs to the page.
- RESTROOM is a wall plaque; the same-rectangle green VACANT/red OCCUPIED sprites are straight RGBA. Bus route lettering and the two hanging screen-direction signs follow actual world planes.
- Five true 27:40 one-sheet apertures with small bulb sockets, individual steady idle and six-second chase sheets. The page selects one state for each poster.
- Bent glass lowercase d.gg blade: blue d, pink dot and mint gg, bright cores, visible glass bodies, rounded ends, standoffs, brackets, raceway, thin outline, local halo, wall illumination and wet-street reflection. The old `roxy_blade` file/layer identifier is retained solely for compatibility.
- All vehicle states were rebuilt with d.gg destination/transit lettering and DGG 95 plates. Normal, brake, indicator and indicator-only lights and all vehicle depth slices were rebuilt. Existing anchors, canvases, lanes, stops and door offsets are retained.
- A west infill block and repair shop fill the top-left edge. The records shop now continues to the street-side sidewalk, with an alley curb cut/drainage strip, dumpster and planter. The left roof felt was refined after inspection so it remains readable in the night lighting.
- Three real blank ad surfaces: tower facade billboard, bus shelter lightbox and the exposed shutter below NOODLES. Frame/glass overlays are separate straight RGBA. The shutter backing is background dressing at depth 99; its content/frame use 100, all below street walkers. Four bus direction/state records include a blank-panel quad in sprite-local coordinates.
- Heavy rain, native wet-street texture displacement, more legible local puddle rings, curb spray/runoff, roof steam and TV windows. One physical green neighbour tube has a short dropout pair each six seconds. Existing popcorn, actor, umbrella, cat, item and arcade states are retained.

## Integration changes

Use `out9/manifest.json` as the authoritative contract.

1. Retire the screen-facing marquee renderer and old green billboard rectangle. `marquees` is empty and `billboard_rect` is absent. The former 186,624-pixel green aperture test is intentionally retired by Brief 11; that region contains real architecture and rain now.
2. For `led_signs`, use the unchanged projection `x=900+60(u-v)`, `y=350+30(u+v)-z_px`. For wall u0, put u=offset and vary v; for v0, put v=offset and vary u. Dot pitch is in world z-pixel units, with 73.4846922835 z-pixels per tile. There are 108 columns and seven dots per row. `column_direction=-1` on u0 and +1 on v0 makes text read left to right. Row bounds and clockwise `quad_px` are included. The page supplies scrolling amber titles and red scores.
3. `poster_frames` now describes the enlarged true-proportion aperture. Select `poster_bulbs_n_idle` OR `poster_bulbs_n_chase`, never both. Both use plus-lighter. Idle has one steady frame; chase has 72 frames at 12 fps.
4. `ad_surfaces[].quad_px` is TL, TR, BR, BL clockwise in logical 1920x1080 pixels. Warp content into the quad, then draw the overlay at its x/y/w/h and z_index using source-over. The overlay object includes native `file_2x`. `aspect` is the physical surface ratio, before projection. A bus quad is local to the published vehicle canvas and valid for that direction/state; it moves with the sprite.
5. Use the supplied new storefront slices. Each water/film entry shares its owning slice depth and is source-over; do not move it to a global foreground layer. Glass atlases use {p['glass_decoded_bytes_both_scales']:,} decoded bytes ({p['glass_decoded_bytes_both_scales']/1024**2:.3f} MiB) at both scales combined, below the inherited 16 MiB budget.
6. Choose `wc_indicator.vacant` OR `.occupied`. Both have the same rectangle and depth. Fresh door animation atlases use pass-9 lighting and the existing open/hold/close timing.
7. At 1x, draw `base.png` plus `light_loop.webm`; at 2x, draw `base@2x.png` plus `light_loop_2x.webm`. The 4K source uses native Cycles surface positions, native texture sampling and weather evaluation. It is not an enlargement of the 1080p frames. Both are 144 frames / 24 fps / six seconds and share phase zero. `rain_fg.webm` remains 1080p and may scale with the stage.
8. `lit_bg_dry.png` and `lit_bg_dry@2x.png` provide the fully lit wet scene without animated rain, impacts or steam baked in. Add the sprite layers. The old global glow is disabled/zero; the d.gg halo is a local depth-sorted prop.

Every loop entry owns its own timing/blend fields. Historical pass4–pass8b fields remain for provenance; `pass9_art`, `pass9_integration` and `pass9_checks` describe this pack.

## Video size and measured decode cost

All videos are VP9 profile 0, 8-bit 4:2:0, constant quality CRF 18, with bitrate setting zero.

| Stream | Native pixels | Bytes | Average Mbit/s | VSE ms/frame |
| --- | --- | ---: | ---: | ---: |
{table}

Decode measurements cover all 144 sequential decoded frames through Blender VSE, including color conversion, render overhead and seven PNG writes. They are a reproducible local pipeline measurement, not an isolated decoder benchmark or a live OBS/CEF performance result. At 24 fps the frame interval is 41.67 ms; actual browser/GPU decoding costs require the live page.

## Validation and inspection

- Both independent surroundings/action-volume renders: **0 occluded pixels**, against {r['holdouts'][0]['protected_action_pixels']:,} protected pixels at 1080p and {r['holdouts'][1]['protected_action_pixels']:,} at native 4K. See `qa9/surroundings_occlusion.json` and `qa9/surroundings_occlusion@2x.json` for exact counts.
- Camera calibration: 11 markers, maximum axis error {r['camera']['max_axis_error_px']:.6f} px. Walker routes, staff/customer anchors, vehicle lanes/stops and sprite canvases match out8b.
- Exact periodic endpoint regeneration and last-to-first source seams passed for all three videos and new dynamic prop loops. All three encoded videos were decoded; sampled indoor black level is RGB 0, and decoded seam/detail checks pass.
- Newly changed static sprites and all vehicle slices reconstruct their parent RGBA exactly. Poster physical aspect is 27:40. Ad quads have clockwise winding. All referenced assets and sheet sizes resolve.
- The Blender scene has no camera-facing text and no visible ROXY/RXY brand text. Vehicle source labeling was rebuilt too.
- All **{r['protected_live_files']:,} files in nine live packs** remain SHA-256 identical. All task writes are inside roxy3d.

Visual evidence: `qa9/preview_1.png`, `qa9/final_decoded_f072.png`, `qa9/final_decoded_f072@2x.png`, `qa9/poster_chase_and_occupied.png`, `qa9/vehicle_branding_contact.png`, and the dry fallback composites. `qa9/final_validation.json`, `qa9/video_validation.json`, `qa9/asset_inventory.json` and the source scripts retain the reproducible checks.

The page/server was not edited. Dynamic LED text, poster/ad content, WC state switching and zoom integration are consumer-side work using these new contracts.
'''
    (ROOT/'NOTES-PASS9.md').write_text(text,encoding='utf-8');status('NOTES-PASS9.md written with complete integration changes, native-video sizes and measured decode costs')
if __name__=='__main__':main()
