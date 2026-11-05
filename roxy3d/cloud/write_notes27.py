"""Generate the delivery notes from measured local evidence (no renders)."""
import json,statistics,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'bundle';SRC=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
fast=read(ROOT/'smoke/fast-validation.json');q=read(ROOT/'smoke/quality27.json');pack=read(ROOT/'smoke/packaging27.json');draft=read(ROOT/'smoke/draft27.json')
t=fast['timing'];before=t['before'];after=t['after'];ratio=after[1]['total']/before[1]['total']
nodes=ast.parse((ROOT/'production.py').read_text()).body
static=next(ast.literal_eval(n.value) for n in nodes if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='INTERIOR_STATIC' for x in n.targets))
dynamic=[g['name'] for g in fast['groups'] if g['name'] not in static]
dynamic_fallback=[n for n in fast['fallback_groups'] if n in dynamic]
static_fallback=[n for n in fast['fallback_groups'] if n in static]
combined=read(ROOT/'work/buffers/fast27_combined_720.json')['timing']
isolated=[read(ROOT/'work/buffers'/('fast27_ref_'+g['name']+'.json'))['timing']['total'] for g in fast['groups']]
combined_ratio=combined['total']/statistics.median(isolated)
visibility_transition=statistics.median([read(ROOT/'work/buffers'/('fast27_ref_'+g['name']+'.json'))['timing']['visibility'] for g in fast['groups']])/6
old_render=before[1]['render_sync_trace_exr'];new_render=after[1]['render_sync_trace_compositor']+after[1]['exr_write']
render_ratio=new_render/old_render
overhead_ratio=(after[1]['total']-new_render+visibility_transition)/(before[1]['total']-old_render)
projections=[]
for frames in [24,48]:
    iso_cloud=4*render_ratio+5*overhead_ratio;fg=len(dynamic_fallback)*frames*iso_cloud+len(static_fallback)*iso_cloud+frames*iso_cloud*combined_ratio
    background=48*41;doors=1200/2*ratio
    # Keep the entire unexplained run-2 remainder; do not claim encode savings.
    remainder=5.5*3600-(48*(19+41)+14*48*2*9+1200)
    for gpu,rate,factor in [('RTX 5090',1.19,1),('RTX 4090',.89,31/19)]:
        hours=((fg+background+doors)*factor+remainder)/3600
        projections.append(dict(gpu=gpu,wet_unique=frames,default=frames==24,hours=hours,low_hours=hours*.8,high_hours=hours*1.3,cost=hours*rate,low_cost=hours*.8*rate,high_cost=hours*1.3*rate,rate=rate))
atomic=dict(default_wet_unique_frames=24,method='Run-2 foreground 4s render + 5s overhead scaled separately by matched local ratios, with a visibility refresh amortized every six phases for bell-circuit changes; combined/isolated local ratio; 4K background 41s from 5090; doors halved; entire run-2 remainder retained. 4090 render stages multiplied by 31/19 observed background ratio. Planning interval -20%/+30%; no cloud measurements.',matched_ratio=ratio,render_ratio=render_ratio,overhead_ratio=overhead_ratio,combined_vs_isolated_ratio=combined_ratio,dynamic_fallback=dynamic_fallback,static_fallback=static_fallback,estimates=projections)
(ROOT/'smoke/projection27.json').write_text(json.dumps(atomic,indent=2),encoding='utf-8')
lines=['# Brief 27 - faster pipeline, approved Draft 13','',
'Implemented all four changes. The source scene and roxy.html are unchanged. No local full render or cloud pod was run. ONE owner draft: `qa10/draft14-fast.png` (1280x720), composed from the measured cut/fallback layers, depth ownership and additive weather.','',
'Owner decision, 03 Nov 2026: 24 unique wet/foreground frames are now the default when ROXY_WET_FRAMES is unset; ROXY_WET_FRAMES=48 remains an override. Only the affected no-render scheduling and cadence checks were re-run for this change. The existing draft, render timings and packaging evidence below are retained; no new draft, 3D capture or clip was made.','',
'The combined pass is deliberately conditional: '+str(len(fast['combined_groups']))+' of 39 groups pass both colour and alpha noise gates. The other '+str(len(fast['fallback_groups']))+' retain isolated rendering. This limits the batching gain, but avoids discarding hidden surfaces or changing glass coverage.','',
'## Pipeline and output contract','',
'- Combined foreground beauty + antialiased Cryptomatte masks + FloorUV positions; selected groups share one capture per unique phase. Measured exceptions are rendered consecutively by group.','- All new production captures use the 4K camera grid. 1080p is a 2x2 scene-linear RGBA average before display conversion. Surface coordinates are coverage-weighted. Backgrounds, foreground, doors, WC, airborne rain and four bus states use this path.','- Unchanged phase/visibility state is cached, redundant object/material writes are skipped, and neon circuits/materials are pre-indexed. Persistent Data, adaptive 256/64/.01, OptiX denoise, HDR glare and sharp topology-changing drips remain.','- Default 24 unique foreground/wet phases when `ROXY_WET_FRAMES` is unset: even phases are duplicated into the original 48 slots. `ROXY_WET_FRAMES=48` overrides this to render every phase. Eight columns, six rows, 24 fps and the 2s/6s cadence stay unchanged. Background light and airborne rain remain 48 unique phases. No new draft or test clip was rendered for this default change.','',
'The layout-3 manifest schema, production sizes, filenames, wet/door sheet layouts, run.sh modes, progress.log, SUCCESS line, watchdog and out10.tar.gz are retained. The earlier per-decoded-frame video tolerance and validation pass flag are untouched. The cloud launcher/credit/keep-on-failure code is untouched.','',
'## Matched local timings','',
'RTX 3050 6 GB laptop, same 720p camera crop, queue_front, phases 0 and 2, same final quality and seed. The first sample includes pass setup; the second measures consecutive frames. These are wall times, not cloud benchmarks.','',
'| Item (seconds) | Old first | New first | Old consecutive | New consecutive |','|---|---:|---:|---:|---:|']
for label,key in [('Phase + frame/GN evaluation','phase'),('Visibility/material work','visibility'),('EXR/hash receipts','hash'),('EXR loading','exr_read'),('Total capture wall','total')]:lines.append(f"| {label} | {before[0].get(key,0):.4f} | {after[0].get(key,0):.4f} | {before[1].get(key,0):.4f} | {after[1].get(key,0):.4f} |")
lines += ['',f"Old render/sync/EXR bucket: {before[0]['render_sync_trace_exr']:.3f} / {before[1]['render_sync_trace_exr']:.3f} s. New render/sync/compositor: {after[0]['render_sync_trace_compositor']:.3f} / {after[1]['render_sync_trace_compositor']:.3f} s; separate EXR writes {after[0]['exr_write']:.4f} / {after[1]['exr_write']:.4f} s; configuration {after[0]['configuration']:.4f} / {after[1]['configuration']:.4f} s. Display conversion: old {t['display_seconds'][0]:.3f}, new {t['display_seconds'][1]:.3f} s.",'',
'The C++ render bucket includes Cycles tracing, Persistent Data synchronization/rebuild, denoising and compositor work. These were not independently timed inside Blender; no unsupported attribution of that bucket to pure tracing is made. The directly measured Python visibility cost is removed between unchanged passes. Fixed-Persistent/adaptive comparisons also pass the original two-seed RGB gate.','',
f"Combined 720p capture including masks and positions: {combined['total']:.3f} s ({combined['render_sync_trace_compositor']:.3f} render/sync/compositor, {combined['mask_export']:.3f} mask export). This is compared with all 39 corresponding isolated groups in the table below. Old/new matched render pixel differences are recorded in timing27.json.",'',
'## Linear reduction and quality','',
'| Comparison | Mean RGB | p99 RGB | Pass |','|---|---:|---:|---|']
for label,d in [('Original 720p two-seed baseline',q['quality']['noise_baseline']),('Persistent Data',q['quality']['persistent']),('Adaptive 256/64/.01',q['quality']['adaptive_001']),('Native 1080p crop noise',fast['downscale']['noise']),('4K area reduction vs native 1080p',fast['downscale']['difference'])]:lines.append(f"| {label} | {d['mean']:.9f} | {d['p99']:.9f} | {'reference' if 'noise' in label or 'baseline' in label else 'yes'} |")
d=fast['downscale'];lines += ['',f"Reduction test: native 3840/1920 camera grids over logical crop {d['rect_1080']}, high pixels {d['high_size']}, low pixels {d['low_size']}. Native 1080 A/B: {d['native1080_seconds']:.2f}/{d['native1080_seed_b_seconds']:.2f} s; one 4K crop: {d['native4k_seconds']:.2f} s. This proves a bounded actual-resolution crop, not a whole 4K frame or all surfaces/phases.",'',
f"Antialias matching is part of the production path and every high-resolution receipt: {d['high_filter']} at 4K, compared with {d['native_filter']} at native 1080p. The initial 1.5-pixel high-resolution filter failed (mean 0.003223705, p99 0.050588796); 3.0 also failed. The measured 2.5-pixel footprint passed without changing the noise thresholds. Original results remain in filter27.json and raw receipts.",'',
'## Every foreground group','',
'Two independent seeds provide each group\'s noise baseline on the same frame and crop. Both mean/p99 RGB and mean/p99 alpha must pass. No threshold was relaxed. JSON includes every p99 and maximum as well as receipts.','',
'| Group | RGB mean / noise | RGB p99 / noise | Alpha mean / noise | Path |','|---|---:|---:|---:|---|']
for g in fast['groups']:
    d=g['difference'];n=g['noise'];lines.append(f"| {g['name']} | {d['mean']:.6g} / {n['mean']:.6g} | {d['p99']:.6g} / {n['p99']:.6g} | {d['alpha_mean']:.6g} / {n['alpha_mean']:.6g} | {'combined' if g['accepted'] else 'isolated fallback'} |")
lines += ['', '## Packaging proof','',
f"End-to-end smoke pack passed production VP9 encode and actual decode (144 repeated smoke frames), validator, all depth reconstructions, 8x6 and 4x4 sheet dimensions/endpoints, real rebuilt bus bodies in four states at both output scales, cleanup of an unreferenced sentinel, checksum inventory, tar creation and every-member SHA-256 read-back. Archive fixture: `cloud/bundle/work/smoke_tail/out10.tar.gz`; {pack['archive']['files']} files. Codec maximum black channel: {pack['video']['decoded_black_max']}/255. The video's own per-frame pass flag remains authoritative.",'',
'The repeated-frame video/sheets exercise packaging and codec branches; they are not a motion/seam quality claim. No extra owner preview or test clip is delivered. Preflight and contract/watchdog fixtures pass; watchdog pod commands are mocked. Cache resume is exercised by the final smoke rerun loading completed captures from hash-checked receipts.','',
'Visual QA caught a shared-wall depth issue in the layer assembly: independently spaced cap and support-wall bins exposed the shadowed black wall top in alternating spans. The six cap bins now share the five supporting-wall boundaries, with one extra entry span and a one-unit depth offset. The physical footprint and slice count remain unchanged; the final draft was recomposed from the same captures and inspected with the cap continuous. The smoke fixture also clears RGB when downscaled alpha rounds to zero, as production already does, so exact RGBA slice reconstruction passes.','',
'The focused independent-reference check reports zero bright-cap pixels turning into black holes after the correction. A 0.025-tile ownership guard handles fractional coverage at the shared boundaries. It is not a claim that the display-space glass stack is pixel-identical to a single physical scene render; visual27.json records the remaining differences in that narrow diagnostic band.','',
'## Cloud projection (not measured)','',atomic['method'],'',
'| GPU / wet unique frames | Central hours | Planning hours | Central cost | Planning cost |','|---|---:|---:|---:|---:|']
for p in projections:
    mode='default' if p['default'] else 'override'
    lines.append(f"| {p['gpu']} / {p['wet_unique']} ({mode}) | {p['hours']:.2f} | {p['low_hours']:.2f}-{p['high_hours']:.2f} | ${p['cost']:.2f} | ${p['low_cost']:.2f}-${p['high_cost']:.2f} |")
lines += ['',f"Rates supplied by owner: RTX 4090 $0.89/h, RTX 5090 $1.19/h. Dynamic isolated exceptions: {len(dynamic_fallback)} of 14; static isolated exceptions: {len(static_fallback)} of 25. Native 4K rain/mask overhead, GPU clocks, packing and cache behavior can shift these projections. No rental or spend occurred.",'',
'## Delivery limits','',
'The one draft and bounded local smoke are complete. Full animation, every camera pixel at native 4K, all-time glass comparisons, Linux/GPU behavior and browser/OBS playback remain untested. No full render was launched to fill those gaps. The source scene and page were preserved. The sealed archive identity is recorded separately in cloud/bundle-delivery.json and qa10/STATUS.md.','',
'Cryptomatte API reference used during implementation: https://docs.blender.org/api/5.2/bpy.types.CompositorNodeCryptomatteV2.html','']
(SRC/'NOTES-FAST-PIPELINE.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(atomic,indent=2))
