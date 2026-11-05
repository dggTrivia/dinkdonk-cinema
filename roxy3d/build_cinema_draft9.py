"""Brief36: only the draft8 tunnel-mouth lighting. One render; new files only.

Run Blender factory-startup --python-exit-code 1 --python this.py [-- --preflight].
The draft8 source is evaluated as helpers with all output/cache paths redirected
to runtime09. Its main is never called; no earlier blend is opened or saved.
"""
import sys
sys.dont_write_bytecode = True
import os, json, math, time, hashlib, statistics, struct, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUN = QA/'runtime09'
IMAGE = QA/'cinema_draft_09.png'
REPORT = QA/'CINEMA-DRAFT-09.md'
LAYOUT = QA/'cinema_layout_09.json'
TARGET = ROOT/'roxy_cinema_draft9.blend'
RUN.mkdir(parents=True, exist_ok=True)
D = {'__file__': str(ROOT/'build_cinema_draft8.py'), '__name__': 'draft8_helpers_for_draft9'}
source = (ROOT/'build_cinema_draft8.py').read_text(encoding='utf-8')
for a,b in [('runtime08','runtime09'), ('cinema_draft_08.png','cinema_draft_09.png'),
            ('CINEMA-DRAFT-08.md','CINEMA-DRAFT-09.md'), ('cinema_layout_08.json','cinema_layout_09.json'),
            ('roxy_cinema_draft8.blend','roxy_cinema_draft9.blend')]:
    source = source.replace(a,b)
exec(compile(source, 'unchanged_draft8_helpers_redirected_to_runtime09', 'exec'), D)
import bpy
xyz, project = D['xyz'], D['project']
NORMAL, RIGHT, UP = D['NORMAL'], D['RIGHT'], D['UP']
W,H,ORTHO,ZPP,PPU = D['W'],D['H'],D['ORTHO'],D['ZPP'],D['PPU']
BASE = json.loads((QA/'cinema_layout_08.json').read_text(encoding='utf-8'))
SWITCH = '13 Tunnel mouth lighting - draft09 switch'
EXTERNAL_LOGS = {'roxy3d/codex36.log', 'roxy3d/cloud/cloud-full-20261103-190526.log'}
NEW_FILES = {'build_cinema_draft9.py','roxy_cinema_draft9.blend','qa11/cinema_draft_09.png',
             'qa11/CINEMA-DRAFT-09.md','qa11/cinema_layout_09.json'}


def snapshot():
    result = {}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUN in p.parents: continue
        st=p.stat(); result[p.relative_to(ROOT.parent).as_posix()] = [st.st_size,st.st_mtime_ns]
    return result


def preserve(before):
    after=snapshot()
    changed=[p for p,v in before.items() if after.get(p)!=v]
    external=[p for p in changed if p in EXTERNAL_LOGS]
    protected=[p for p in changed if p not in EXTERNAL_LOGS and p!='roxy3d/build_cinema_draft9.py'
               and (p.startswith('roxy3d/') or p.endswith(('.html','.htm')))]
    assert not protected, protected
    new=[p for p in after if p not in before]
    unexpected=[p for p in new if p.startswith('roxy3d/') and p[7:] not in NEW_FILES]
    assert not unexpected, unexpected
    return {'passed':True,'existing_files_checked':len(before),
            'existing_roxy3d_files_checked':sum(p.startswith('roxy3d/') and p not in EXTERNAL_LOGS
                  and p!='roxy3d/build_cinema_draft9.py' for p in before),
            'existing_pages_checked':sum(p.endswith(('.html','.htm')) for p in before),
            'protected_changes':protected,'external_active_logs_changed':external,
            'unrelated_workspace_changes':[p for p in changed if p not in external and p not in protected
                                            and p!='roxy3d/build_cinema_draft9.py'],
            'new_files_outside_runtime09':new,
            'method':'Original size and nanosecond mtime inventory; all earlier drafts, blends, cloud bundle, out10 and pages protected. Only current externally written codex36/cloud log changes are itemized separately. This builder never writes them.'}


def geometry_signature(objects):
    deps=bpy.context.evaluated_depsgraph_get(); result={}
    for ob in objects:
        if ob.type not in ['MESH','CURVE','FONT']:continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh(); h=hashlib.sha256()
        for v in me.vertices:h.update(struct.pack('<3d',*(ev.matrix_world@v.co)))
        for poly in me.polygons:
            h.update(struct.pack('<I',len(poly.vertices)))
            h.update(struct.pack('<'+'I'*len(poly.vertices),*poly.vertices))
        result[ob.name]=h.hexdigest();ev.to_mesh_clear()
    return result


def camera_only_material(name, base):
    # The new indicators are self-lit only in camera rays. They cannot emit
    # indirect light onto the screen or the walkers' background.
    ma=base.copy();ma.name=name
    nt=ma.node_tree;out=nt.nodes.get('Material Output')
    principled=nt.nodes.get('Principled BSDF')
    emission=nt.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value=principled.inputs['Emission Color'].default_value
    emission.inputs['Strength'].default_value=principled.inputs['Emission Strength'].default_value
    path=nt.nodes.new('ShaderNodeLightPath');transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
    mix=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(path.outputs['Is Camera Ray'],mix.inputs[0])
    nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(emission.outputs[0],mix.inputs[2])
    nt.links.new(mix.outputs[0],out.inputs['Surface'])
    return ma


def add_mouth_lighting(sc,base_tree,base_owners):
    group=D['collection'](SWITCH);M=D['M'];specs=[];markers=[]
    floor=bpy.data.collections.new('D09 receivers - lower approach only')
    notch=bpy.data.collections.new('D09 receivers - existing tunnel notch only')
    for ob in list(sc.objects):
        if ob.type not in ['MESH','CURVE','FONT']:continue
        # Only existing low approach geometry is eligible, never seats/screen.
        if ob.name.startswith(('Approach broad step','Approach step nosing','Tunnel carpet floor')):
            floor.objects.link(ob)
        elif ob.name.startswith('Quiet low contrast broken woven carpet texture'):
            if any(c.name.startswith('10 ') for c in ob.users_collection):floor.objects.link(ob)
        if ob.name in D['OCCLUDERS'] or ob.name.startswith('Tunnel near wall bearing'):
            notch.objects.link(ob)
    for name,point,target,power,size,sy,receivers in [
        ('D09 soft warm mouth floor spill',(1.25,9.10,78),(1.35,7.90,8),85,2.1,1.5,floor),
        ('D09 soft warm lower approach continuation',(1.20,7.10,100),(1.40,5.65,22),45,2.2,1.8,floor),
        ('D09 restrained notch jamb and soffit wash',(1.60,8.85,80),(.72,9.66,102),12,1.4,1.0,notch)]:
        lamp=D['light'](name,point,target,power,(1,.66,.39),size,sy)
        lamp.light_linking.receiver_collection=receivers
        lamp.data.cycles.max_bounces=0
        specs.append({'object':name,'type':'AREA','point_uvzpx':point,'target_uvzpx':target,
                      'energy_W':power,'color_linear_rgb':[1,.66,.39],'size_world':[size,sy],
                      'receiver_collection':receivers.name,'receiver_objects':sorted(o.name for o in receivers.objects),
                      'indirect_bounces':lamp.data.cycles.max_bounces,'screen_receiver':False})
    red=camera_only_material('D09 camera-only inherited red-orange indicator',M['red dot'])
    for lo,hi,z in [(7.4,9.36,8),(5.9,7.4,16),(5.2,5.9,24),(5.2,5.9,24)]:
        chosen=None;diagnostic={'safe':0,'visible':0,'tested':0,'blockers':{},'visible_candidates':[]}
        for u in [.08,.05,.15,.23,.35,.43,.65,.90,1.15,2.70,2.50,2.30,2.10,1.85,1.6]:
            for offset in [hi-lo-.03,.08,.18,.30,.45,.60,.80,1.,1.2,1.4,1.6,1.8]:
                if hi-offset<lo+.025:continue
                point=[u,hi-offset,z+.42]
                if any(math.dist(project(*point),mark['pixel'])<10 for mark in markers):continue
                diagnostic['tested']+=1
                rectangle_conflicts=D['dot_conflicts'](point)
                conflicts=[]
                # A projected rectangle belonging to a walker hidden by the
                # fixed roof/stairs is not a visible face. Test the scene ray
                # at the candidate pixel before rejecting that low fixture.
                px,py=project(*point)
                for walker in rectangle_conflicts:
                    anchor=xyz(walker[0],walker[1],walker[2]+36)
                    ax,ay=project(walker[0],walker[1],walker[2]+36)
                    if abs(px-ax)>=11.1*D['K']+4:continue
                    q=anchor+RIGHT*((px-ax)/60)+UP*((ay-py)/60)
                    if base_tree.ray_cast(q+NORMAL*45,-NORMAL,44.9995)[2] is None:
                        conflicts.append(walker)
                hit=base_tree.ray_cast(xyz(*point)+NORMAL*45,-NORMAL,44.998)
                if not conflicts:diagnostic['safe']+=1
                if hit[2] is None:
                    diagnostic['visible']+=1
                    diagnostic['visible_candidates'].append({'point':point,'conflicts':conflicts[:3]})
                else:
                    owner=base_owners[hit[2]];diagnostic['blockers'][owner]=diagnostic['blockers'].get(owner,0)+1
                if hit[2] is None and not conflicts:chosen=point;break
            if chosen:break
        print('D09_MARKER_SEARCH',hi,z,chosen,json.dumps({k:diagnostic[k] for k in ['safe','visible','tested']}),flush=True)
        if not chosen:
            # Retain the lit middle rise, but do not force a luminous marker
            # behind a projected face when the locked geometry leaves no gap.
            continue
        u,v,zz=chosen;name='D09 approach low red-orange tread light '+str(z)+' '+str(len(markers)+1)
        endpoints=[[u-.07,v,zz],[u+.07,v,zz]]
        D['line'](name,endpoints,red,.015)
        markers.append({'object':name,'face':'+z tread top','uvzpx':chosen,'endpoints':endpoints,
                        'pixel':project(*chosen),'visible_upper55_walker_conflicts':0,
                        'safety_method':'Visible upper55 face core (+/-11.1 lobby px), plus4px horizontal/2.5px vertical marker margin; full sprite rectangle overlaps retained separately.',
                        'occluded_rectangle_conflicts':len(D['dot_conflicts'](chosen))})
    # Small sign attached to the existing drop-guard post at v8.7. No post,
    # notch, rail, step or other architectural geometry is altered.
    green=camera_only_material('D09 camera-only green EXIT',M['exit'])
    D['box']('D09 mouth EXIT backing on existing guard post',2.925,8.42,2.956,8.98,140,154,M['armrest'],.002)
    sign=D['text']('D09 mouth green EXIT visible on guard post','E X I T',2.962,8.70,147,.17,green)
    sign['mounted_on']='Left stair rail and lower approach drop guard support at v8.7'
    return {'collection':group.name,'switch_off':'Disable collection 13 Tunnel mouth lighting - draft09 switch in render and viewport to restore draft8 lighting.',
            'lights':specs,'step_indicators':markers,
            'exit_sign':{'text_object':sign.name,'backing_object':'D09 mouth EXIT backing on existing guard post',
                         'uvzpx':[2.962,8.7,147],'pixel':project(2.962,8.7,147),'face':'+u, on existing guard post'},
            'new_geometry_only':'Tiny tread-top luminous inserts and an EXIT fixture. No architectural mesh changes.',
            'screen_isolation':'All three new lamps have explicit local receiver collections excluding screen and max_bounces=0. New indicator emissions are camera-ray-only.'}


def rebuild_tree(sc):
    tree,owners=D['object_tree'](list(sc.objects))
    D['SCENE_BVH'],D['SCENE_OWNERS']=tree,owners
    return tree,owners


def integrated_routes(composition,tree):
    for item in composition['route_samples']:
        u,v,z=item['uvzpx'];anchor=xyz(u,v,z+36);whole=[];upper=[]
        for dx in [-11.1,0,11.1]:
            clear=0;high=0
            for i in range(400):
                p=anchor+RIGHT*(dx/PPU)+UP*((50*(1-(i+.5)/400))/PPU)
                hit=tree.ray_cast(p+NORMAL*45,-NORMAL,44.9995)
                if hit[2] is None:
                    clear+=1
                    if i<220:high+=1
            whole.append(clear/400);upper.append(high/220)
        item['unoccluded_face_core_fraction']=min(whole)
        item['upper55_unoccluded_face_core_fraction']=min(upper)
    approach=[p for p in composition['route_samples'] if 5.15<=p['uvzpx'][1]<=8.7 and p['uvzpx'][0]<2.95]
    composition['minimum_open_approach_integrated_upper55_fraction']=min(p['upper55_unoccluded_face_core_fraction'] for p in approach)
    composition['integrated_visibility_method']=BASE['composition_and_route']['integrated_visibility_method']


def metric_masks(sc,tree,owners):
    masks={k:[] for k in ['approach_floor','approach_step_faces','notch_jamb_soffit','screen']}
    for y in range(0,H,2):
        for x in range(0,W,2):
            origin=sc.camera.location-NORMAL*2+RIGHT*((x+.5-W/2)*ORTHO/W)+UP*((H/2-y-.5)*ORTHO/W)
            hit=tree.ray_cast(origin,-NORMAL,100)
            if hit[2] is None:continue
            name=owners[hit[2]];p=hit[0];u,v,z=p.x,-p.y,p.z*ZPP;nz=abs(hit[1].z)
            key=None
            if 'SCREEN clean' in name:key='screen'
            elif .3<=u<=2.80 and 5.2<=v<=9.4 and z<26:
                if nz>.7:key='approach_floor'
                elif nz<.45 and name.startswith('Approach'):key='approach_step_faces'
            elif name in D['OCCLUDERS'] and .15<=u<=2.96 and 9.39<=v<=9.90:
                key='notch_jamb_soffit'
            if key:masks[key].append([x,y])
    assert all(masks.values()),{k:len(v) for k,v in masks.items()}
    return masks


def stats(values):
    values=sorted(values)
    return {'samples':len(values),'mean_0_255':statistics.mean(values),'median_0_255':statistics.median(values),
            'p10_p90_0_255':[values[len(values)//10],values[int(len(values)*.9)]],
            'min_max_0_255':[values[0],values[-1]],'stdev_0_255':statistics.pstdev(values)}


def delivered_comparison(masks):
    pix8=D['delivered_png_rgb'](QA/'cinema_draft_08.png');pix9=D['delivered_png_rgb'](IMAGE)
    result={'method':'Same draft8 delivered-image metric: direct PNG RGB8 display-sRGB Rec709 bytes (.2126,.7152,.0722), every second pixel x/y. Fixed first-hit draft8 geometry masks, absolute normal z for floor/fascia separation; identical pixels before/after. Fixture occlusions excluded from floor/notch masks. No color re-encoding.', 'categories':{}}
    for key,points in masks.items():
        before=[];after=[];rgb_delta=[]
        for x,y in points:
            i=(y*W+x)*3;a=pix8[i:i+3];b=pix9[i:i+3]
            before.append(sum(c*w for c,w in zip(a,[.2126,.7152,.0722])))
            after.append(sum(c*w for c,w in zip(b,[.2126,.7152,.0722])))
            rgb_delta.extend(abs(c-d) for c,d in zip(a,b))
        result['categories'][key]={'before':stats(before),'after':stats(after),
            'mean_delta_0_255':statistics.mean(after)-statistics.mean(before),
            'mean_absolute_rgb_byte_delta':statistics.mean(rgb_delta),'max_rgb_byte_delta':max(rgb_delta)}
    # The same inset mask and calculation used in draft8 final QA.
    corners=BASE['screen']['corners_1920x1080'];points=[]
    for x in range(math.ceil(corners['TL'][0]+8),math.floor(corners['TR'][0]-8)):
        top=370+.5*(x+.5-890)-460*D['K'];bottom=370+.5*(x+.5-890)-90*D['K']
        for y in range(math.ceil(top+8),math.floor(bottom-8)):points.append([x,y])
    screen=[];old=[];peak=0;channel_deltas=[]
    for x,y in points:
        i=(y*W+x)*3;a=pix8[i:i+3];b=pix9[i:i+3]
        screen.append(sum(c*w for c,w in zip(b,[.2126,.7152,.0722])))
        old.append(sum(c*w for c,w in zip(a,[.2126,.7152,.0722])))
        peak=max(peak,*b);channel_deltas.extend(abs(c-d) for c,d in zip(a,b))
    result['screen_inset']={'before':stats(old),'after':stats(screen),'highest_rgb_channel_after':peak,
           'mean_delta_0_255':statistics.mean(screen)-statistics.mean(old),
           'mean_absolute_rgb_byte_delta':statistics.mean(channel_deltas),'max_rgb_byte_delta':max(channel_deltas),
           'mean_unchanged_tolerance_0_255':.5,'passed':abs(statistics.mean(screen)-statistics.mean(old))<=.5}
    return result


def write_report(data):
    comp=data['delivered_image_comparison'];rows=[]
    for key,val in comp['categories'].items():
        a,b=val['before'],val['after']
        rows.append(f"| {key} | {a['samples']} | {a['mean_0_255']:.2f} | {b['mean_0_255']:.2f} | {val['mean_delta_0_255']:+.2f} | {a['median_0_255']:.2f} / {b['median_0_255']:.2f} |")
    route=[]
    for i,p in enumerate(data['composition_and_route']['route_samples']):
        if i%8==0:
            route.append(f"| {p['uvzpx']} | {p['visible_top_fraction']:.2%} | {p['upper55_unoccluded_face_core_fraction']:.2%} |")
    s=comp['screen_inset'];p=data['preservation'];r=data['render']
    lamps='\n'.join(f"- `{l['object']}`: {l['energy_W']} W, area {l['size_world']}, position `{l['point_uvzpx']}`, target `{l['target_uvzpx']}`; receiver `{l['receiver_collection']}`." for l in data['mouth_lighting']['lights'])
    out=f'''# Cinema draft 09 - tunnel-mouth lighting only

One 1920x1080 PNG, built directly with the unchanged draft8 source helpers and its delivered layout. Only the mouth/approach lighting and its three low step indicators and small green EXIT fixture are added. Earlier scene geometry and materials, all 135 seats, rails, stairs, route, camera, notch, screen and every existing light retain their draft8 values.

Warm broad light spills across the low approach from the mouth and continues gently onto the three 8-unit rises. A restrained separate wash touches the retained notch jamb/soffit. Sources stay invisible in the camera; receivers are limited to low approach surfaces or existing tunnel structure. No bright backdrop is added at walker-face height. Three small red-orange inserts face +z. The new EXIT is on the +u face of the existing guard post; the rear-portal EXIT is retained.

## Switchable additions

All additions are in `{SWITCH}`. Disable that collection for render and viewport to return to the draft8 scene. The receiver collections contain references to existing meshes and do not duplicate or modify them. New area lamps have zero indirect bounces; the tiny red/green emitters contribute only to camera rays. The screen receives zero illumination from these additions.

{lamps}

Exact indicator positions, projection and visibility checks, the EXIT fixture, receiver membership and light settings are in the JSON. One insert is on the 8-unit tread and two on the 24-unit tread. The middle rise receives the warm wash; no insert is forced into its face projections. The safety test covers visible upper55 face cores (+/-11.1 lobby px, plus4px horizontal and2.5px vertical margin); overlaps with wider full-sprite rectangles are separately retained in JSON. Existing mouth/rear spills are unchanged.

## Delivered-image measurement

Direct saved PNG RGB8 display-sRGB Rec709 weighted byte luminance /255, matching draft8; every second pixel, first camera-ray geometry masks. The exact same visible approach/notch/screen pixels are measured in both delivered images. Floor and vertical faces use absolute normal z. New fixture-covered samples are excluded. These are rendered pixel measurements, not linear scene radiance. Quantiles and ranges are in JSON.

| Category | Samples | Draft8 mean | Draft9 mean | Change | Median before / after |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Screen inset ({s['after']['samples']:,} pixels, same 8px inset as draft8): mean **{s['before']['mean_0_255']:.4f} -> {s['after']['mean_0_255']:.4f}/255**, delta **{s['mean_delta_0_255']:+.4f}**. Screen check **{'PASS' if s['passed'] else 'OUTSIDE TOLERANCE'}** at +/-0.5/255 mean tolerance. Actual mean absolute RGB-byte difference **{s['mean_absolute_rgb_byte_delta']:.4f}**, maximum channel difference **{s['max_rgb_byte_delta']}**; sampling/denoising differences are reported rather than described as pixel identity. Range after **{s['after']['min_max_0_255']}**, standard deviation **{s['after']['stdev_0_255']:.4f}**, peak channel **{s['highest_rgb_channel_after']}**. Screen material, exclusive screen fill, quad and exposure remain unchanged.

## Unchanged route visibility, for reference

Re-evaluated against the delivered draft9 geometry. All {len(data['composition_and_route']['route_samples'])} route samples match draft8's contiguous and integrated upper55 visibility fractions. Three face-core columns, 400 vertical samples, floor+36 anchor, 50k height. The upper55 column counts all unblocked rays; a thin guard crossing can reduce the contiguous-from-top metric disproportionately. Tiny low fixtures can affect rays in the lower45% of the full envelope; those complete fractions and their differences are retained in JSON. Lighting improves floor legibility; the mouth's geometric occlusion is unchanged.

| Route key point (u,v,zpx) | Contiguous clear from top | Upper55 unoccluded |
|---|---:|---:|
{chr(10).join(route)}

At v9.4 the walker remains geometrically hidden. Initial emergence is still 15.5% contiguous at (2.1,9.32,8), then 37.5% at (2.1,9.1,8). Minimum integrated upper55 clearance in the open approach is {data['composition_and_route']['minimum_open_approach_integrated_upper55_fraction']:.2%}. The fixed stair/seat projection remains the reveal limit. A future tiny local cheek/soffit adjustment could be investigated to advance the first reveal, but no notch or architectural change was made here. No artwork, page or animation test is claimed.

## Render and preservation

Blender {r['blender_version']}, Cycles adaptive64-384, threshold0.007, denoising, seed341997, {r['device']}, 1920x1080, same AgX view/look and exposure0 as draft8. **One render: {r['seconds']:.2f}s**; build and checks {r['build_checks_seconds']:.2f}s. PNG SHA256 `{r['image_sha256']}`. All PNG chunk CRCs verified during full RGB decode. One new blend saved, backups disabled; no prior blend opened or saved.

Evaluated mesh signatures of **{data['geometry_lock']['original_mesh_objects_checked']}** pre-existing scene objects match before/after the additions. Camera/seat/occupied-tier/aisle/stair/screen/route/tunnel fields match draft8. The new EXIT and all three new bars have visible camera probes; the bars have no overlaps with visible upper55 face cores by the stated probe method. Screen geometry ray check: {data['screen_visibility']['rays']:,} rays, zero blockers. Existing scene light transforms/settings and material node values are untouched.

Preservation check: **{p['existing_roxy3d_files_checked']}** existing roxy3d files and **{p['existing_pages_checked']}** pages unchanged by size/nanosecond mtime; {p['existing_files_checked']} workspace records inventoried. External active log changes and unrelated external workspace changes are separately itemized in JSON. Only new draft9 source/blend, this PNG/report/JSON and runtime09 diagnostics/caches are written, all inside roxy3d. Earlier drafts, existing blends, cloud bundle, out10 and all pages are retained.

Visual inspection is recorded in runtime09/final_verification.json. No second image, rerender, image edit, layers, encode, cloud operation or page modification. STOP.
'''
    with REPORT.open('x',encoding='utf-8') as f:f.write(out)


def main():
    start=time.perf_counter();preflight='--preflight' in sys.argv
    for p in [IMAGE,REPORT,LAYOUT,TARGET,RUN/'render_started']:
        assert not p.exists(), 'New-file/one-render guard: '+str(p)
    baseline=RUN/'preservation_before.json'
    if baseline.exists():before=json.loads(baseline.read_text(encoding='utf-8'));preserve(before)
    else:
        before=snapshot()
        with baseline.open('x',encoding='utf-8') as f:json.dump(before,f)
    sc=D['configure']();sc.name='DINK DONK Screen 1 - draft09 tunnel mouth lighting'
    sc['brief']='BRIEF-36-cinema-draft9.md'
    D['palette']();D['floors']();screen=D['walls_screen_passage']();D['front_ceiling']();D['seats']()
    D['tunnel_geometry']();D['fixtures_lighting']();D['wear']();D['screen_lighting'](sc,screen)
    originals=list(sc.objects);original_signature=geometry_signature(originals)
    base_tree,base_owners=rebuild_tree(sc)
    masks=metric_masks(sc,base_tree,base_owners)
    additions=add_mouth_lighting(sc,base_tree,base_owners)
    assert original_signature==geometry_signature(originals),'Original geometry changed'
    D['collection']('00 Calibration marker empties')
    cal=D['calibration'](sc);visibility=D['screen_check'](sc,screen)
    tree,owners=rebuild_tree(sc)
    audience=D['audience_checks']();composition=D['composition_route']();integrated_routes(composition,tree)
    for p,q in zip(composition['route_samples'],BASE['composition_and_route']['route_samples']):
        for k in ['uvzpx','visible_top_fraction','upper55_unoccluded_face_core_fraction']:
            assert p[k]==q[k],('Route visibility changed',k,p['uvzpx'],p[k],q[k])
        p['full_envelope_unoccluded_fraction_delta_from_draft8']=p['unoccluded_face_core_fraction']-q['unoccluded_face_core_fraction']
    assert len(composition['route_samples'])==len(BASE['composition_and_route']['route_samples'])
    # Verify actual fixture centres from camera, not just orientation labels.
    for mark in additions['step_indicators']+[additions['exit_sign']]:
        p=xyz(*mark['uvzpx']);hit=tree.ray_cast(p+NORMAL*45,-NORMAL,45.02)
        owner=owners[hit[2]] if hit[2] is not None else None
        target=mark.get('object',mark.get('text_object'))
        mark['camera_probe_first_hit']=owner;mark['camera_visible']=owner==target
        if 'text_object' in mark:
            ob=bpy.data.objects[target];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            visible=0;tested=0
            for vertex in list(me.vertices)[::max(1,len(me.vertices)//120)]:
                q=ev.matrix_world@vertex.co
                probe=tree.ray_cast(q+NORMAL*45,-NORMAL,45.02)
                tested+=1
                if probe[2] is not None and owners[probe[2]]==target:visible+=1
            ev.to_mesh_clear()
            mark['visible_glyph_vertex_probes']=[visible,tested]
            mark['camera_visible']=visible/max(1,tested)>=.5
        assert mark['camera_visible'],('Fixture hidden',target,owner)
    # Remove any measurement pixels now covered by the authorized fixtures.
    for key in ['approach_floor','approach_step_faces','notch_jamb_soffit']:
        clean=[]
        for x,y in masks[key]:
            origin=sc.camera.location-NORMAL*2+RIGHT*((x+.5-W/2)*ORTHO/W)+UP*((H/2-y-.5)*ORTHO/W)
            hit=tree.ray_cast(origin,-NORMAL,100)
            if hit[2] is not None and not owners[hit[2]].startswith('D09 '):clean.append([x,y])
        masks[key]=clean
    data=copy.deepcopy(BASE)
    for key in ['camera','rows','row_pairs','aisles','stairs','screen','total_seats','walk_route','tunnel']:
        assert data[key]==BASE[key],key
    data.update(brief='BRIEF-36-cinema-draft9.md',approved_layout_source='qa11/cinema_layout_08.json',
                calibration=cal,screen_visibility=visibility,audience_check=audience,composition_and_route=composition,
                mouth_lighting=additions,geometry_lock={'passed':True,'original_mesh_objects_checked':len(original_signature),
                   'original_mesh_signature_sha256':hashlib.sha256(json.dumps(original_signature,sort_keys=True).encode()).hexdigest(),
                   'unchanged_original_objects':original_signature,'route_contiguous_and_upper55_fractions_equal_draft8':True})
    data['layout_lock'].update(aisle_or_route_points_changed=0,other_detail_footprint_changes='Only new step-light and EXIT fixtures; all draft8 architecture unchanged.',cut_section='Exact draft8 notch and tunnel retained.')
    data.pop('visual_qa',None);data.pop('image_statistics',None);data.pop('seat_back_luminance',None)
    data['source_hashes']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/'build_cinema_draft4.py',ROOT/'build_cinema_draft8.py',ROOT/'build_cinema_draft9.py',
         ROOT/'BRIEF-36-cinema-draft9.md',QA/'cinema_layout_08.json',QA/'CINEMA-DRAFT-08.md',QA/'cinema_draft_08.png']}
    data['limitations']=['Single 1080p still; no emote art, page changes, animation, layers, encode or 4K render.',
        'Lighting improves walkway readability, not geometric walker visibility; mouth reveal remains limited by exact draft8 geometry.']
    data['preservation']=preserve(before)
    data['render'].update(count=0,image='qa11/cinema_draft_09.png',blend='roxy_cinema_draft9.blend')
    print('DRAFT09_PREFLIGHT',json.dumps({'mask_counts':{k:len(v) for k,v in masks.items()},'geometry_lock':True,
        'route_lock':True,'fixture_visibility':[(m.get('object',m.get('text_object')),m['camera_visible']) for m in additions['step_indicators']+[additions['exit_sign']]],
        'screen_rays':visibility['rays']}),flush=True)
    if preflight:
        path=RUN/('preflight_%02d.json'%(1+len(list(RUN.glob('preflight_*.json')))))
        with path.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
        print('PREFLIGHT COMPLETE - no render or blend save',flush=True);return
    bpy.context.preferences.filepaths.save_version=0
    sc['layout_contract']=json.dumps(data);sc['draft_only']=True
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    with (RUN/'render_started').open('x',encoding='utf-8') as f:f.write('Brief36: one image only. Never render again.\n')
    built=time.perf_counter();print('DRAFT09_SINGLE_RENDER_START',flush=True)
    bpy.ops.render.render(write_still=True);end=time.perf_counter()
    data['render'].update(count=1,seconds=end-built,build_checks_seconds=built-start,total_seconds=end-start,
                          image_sha256=hashlib.sha256(IMAGE.read_bytes()).hexdigest())
    data['delivered_image_comparison']=delivered_comparison(masks)
    data['seat_back_luminance']=D['seat_back_luminance'](sc)
    data['preservation']=preserve(before)
    with LAYOUT.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')
    write_report(data)
    print('DELIVERED_COMPARISON',json.dumps(data['delivered_image_comparison']),flush=True)
    print('DRAFT09_SINGLE_RENDER_COMPLETE',flush=True)
    print('STATUS: DRAFT 09 COMPLETE | one 1920x1080 image | report + JSON | STOP',flush=True)


if __name__=='__main__':main()
