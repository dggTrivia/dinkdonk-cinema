"""Native video, sprite, geometry, contract and protected-pack acceptance."""
import json,hashlib,math,struct,time
import numpy as np
from pass9_common import ROOT,QA,OUT,LIVE,status
from pngio import read,write,predecode
from finalize_pass8 import vp9_format,webm_metadata
from compose_pass9 import compose
from package_vehicles import blend,project
from package_pass2 import grain
import package_pass6 as doors

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def video(kind,meta,period):
    p=OUT/(kind+'.webm');container=webm_metadata(p);fmt=vp9_format(p);s=2 if kind.endswith('_2x') else 1
    assert container['codec_id']=='V_VP9' and container['width']==1920*s and container['height']==1080*s
    assert abs(container['seconds']-6)<.01 and abs(container['fps']-24)<.001
    assert sha(p)==meta['sha256'];predecode(list((QA/('decoded_'+kind)).glob('*.png')))
    rows=[];decoded={}
    for i in [0,1,36,72,108,142,143]:
        name='f'+str(i).zfill(3)+'.png';src=read(QA/(kind+'_frames')/name)[:,:,:3];out=read(QA/('decoded_'+kind)/name)[:,:,:3];decoded[i]=out
        delta=np.abs(src.astype(np.int16)-out.astype(np.int16));active=src.max(2)>8
        interior=int(out[440*s:480*s,910*s:960*s].max());assert interior==0,(kind,i,interior)
        mae=float(delta.mean());active_mae=float(delta[active].mean());assert mae<2 and active_mae<6,(kind,i,mae,active_mae)
        rows.append(dict(frame=i,mean_abs_error=mae,active_mean_abs_error=active_mae,interior_black_max=interior))
    diff=lambda a,b:float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean())
    seam=diff(decoded[143],decoded[0]);adj=max(diff(decoded[0],decoded[1]),diff(decoded[142],decoded[143]),period['adjacent_max_mean_abs']);assert seam<=adj*1.6+.02
    return dict(container=container,vp9=fmt,decoded_samples=rows,seam_mean_abs=seam,adjacent_max_mean_abs=adj)

def main():
    m=json.loads((QA/'manifest_vehicles.json').read_text());old=json.loads((LIVE/'manifest.json').read_text())
    periods=json.loads((QA/'weather_validation.json').read_text());videos=json.loads((QA/'video_metadata.json').read_text());prop=json.loads((QA/'prop_validation.json').read_text());veh=json.loads((QA/'vehicle_validation.json').read_text());cal=json.loads((QA/'calibration.json').read_text())
    assert all(e['passed'] for e in [periods,prop,veh,cal])
    interfaces=json.loads((QA/'interface_validation.json').read_text());assert interfaces['passed'] and len(interfaces['composited_ad_visibility'])==3
    # Poster corrections are wholly indoors, where the additive weather is zero.
    # Restore native final static pixels even if a loop started before refinement.
    rects=json.loads((QA/'poster_patch_rects.json').read_text())
    for s,suffix in [(1,''),(2,'@2x')]:
        protected=np.load(QA/('weather_masks'+suffix+'.npz'))['outside']
        for x,y,x1,y1 in rects:assert not protected[y*s:y1*s,x*s:x1*s].any(),'Poster patch must be fully rain-protected'
        predecode([QA/('steady_bg'+suffix+'.png')]);raw=grain(read(QA/('steady_bg'+suffix+'.png')))
        for kind in ['base','bg','lit_bg','lit_bg_dry']:
            a=read(OUT/(kind+suffix+'.png'))
            for x,y,x1,y1 in rects:a[y*s:y1*s,x*s:x1*s]=raw[y*s:y1*s,x*s:x1*s]
            write(OUT/(kind+suffix+'.png'),a)
    holds=[json.loads((QA/('surroundings_occlusion'+s+'.json')).read_text()) for s in ['', '@2x']];assert all(e['covered_action_pixels']==0 for e in holds)
    reports={k:video(k,v,periods['streams'][k]) for k,v in videos.items()};assert set(reports)=={'light_loop','rain_fg','light_loop_2x'}
    lo=read(QA/'light_loop_frames/f072.png')[:,:,:3];hi=read(QA/'light_loop_2x_frames/f072.png')[:,:,:3]
    from package_vehicles import upscale2
    native_error=float(np.abs(hi.astype(np.int16)-upscale2(lo).astype(np.int16)).mean());assert native_error>.01
    assert int(lo[40:364,1296:1872].max())>0,'Retired billboard aperture still masked'
    (QA/'video_validation.json').write_text(json.dumps(dict(passed=True,streams=reports),indent=2));status('Three encoded VP9 streams passed native dimensions, six-second timing, decoded zero-black interior, detail error and seam checks')
    predecode([OUT/(e['file'][:-4]+s+'.png') for e in m['render_layers'] for s in ['', '@2x']]+[OUT/'lit_bg@2x.png'])
    doors.QA=QA;doors.OUT=OUT;doors.doors(m)
    door_checks=json.loads((QA/'doors_validation.json').read_text());assert all(e['max_source_over_rounding_error']<2 for e in door_checks['checks'])
    status('Fresh door animation atlases packaged and source-over reconstruction verified')
    # Geometry and placement contracts preserved, including vehicles and arrivals.
    for key in ['layout','size','scale2x','projection','staff_positions','customer_positions','lanes','arrival_stops','cat','janitor','umbrella','items','tyre_spray']:
        assert m[key]==old[key],key
    for kind,dirs in old['vehicles'].items():
        for direction,e in dirs.items():
            n=m['vehicles'][kind][direction]
            for key in ['anchor','w','h','length_tiles','width_tiles','geometry_local_footprint','door_ground_offset_tiles']:
                if key in e:assert n[key]==e[key],(kind,direction,key)
    for e in m['poster_frames']:
        aspect=(e['along'][1]-e['along'][0])*73.4846922835/(e['z_px'][1]-e['z_px'][0]);assert abs(aspect-27/40)<1e-9
    for e in m['led_signs']:e['column_direction']=-1 if e['wall']=='u0' else 1
    assert len(m['led_signs'])==5 and len(m['ad_surfaces'])==3
    # Exact disjoint RGBA reconstruction of the newly changed occluders.
    changed=set(json.loads((QA/'scene_metadata.json').read_text())['changed_groups']+['entrance_header']);slice_checks=[]
    for e in m['occluders']:
        if e['name'] not in changed:continue
        for s,suffix in [(1,''),(2,'@2x')]:
            src=read(OUT/(e['file'][:-4]+suffix+'.png'));recon=np.zeros_like(src,dtype=np.uint16)
            for p in e['depth_slices']:
                a=read(OUT/(p['file'][:-4]+suffix+'.png'));x=(p['x']-e['x'])*s;y=(p['y']-e['y'])*s;recon[y:y+a.shape[0],x:x+a.shape[1]]+=a
            # Zero-alpha RGB is deliberately cleaned in disjoint slices.
            src[src[:,:,3]==0,:3]=0;err=int(np.abs(recon.astype(np.int16)-src.astype(np.int16)).max());assert err==0,(e['name'],s,err)
            slice_checks.append(dict(name=e['name'],scale=s,max_error=err))
    status('Camera, arrival, actor and vehicle placement contracts retained; poster proportions and changed occluder reconstruction validated')
    m.update(asset_pack_pass=9,asset_pack_revision='9',status='complete',light_loop_2x='light_loop_2x.webm',light_loop_bytes=videos['light_loop']['bytes'],light_loop_sha256=videos['light_loop']['sha256'],light_loop_2x_bytes=videos['light_loop_2x']['bytes'],light_loop_2x_sha256=videos['light_loop_2x']['sha256'],loop_seam_validation='../qa9/weather_validation.json',static_glow=False)
    m['rain_fg'].update(bytes=videos['rain_fg']['bytes'],sha256=videos['rain_fg']['sha256'])
    m['light_loop_2x_size']=[3840,2160]
    m['baked_signs']=[s.replace('roxy','d.gg') for s in m['baked_signs']]
    m['vehicle_baked_signs']=['95 d.gg','d.gg TRANSIT','DGG 95','TAXI']
    m['full_composition']='Native base + matching-resolution light_loop frame 60; render_layers, selected prop loops, ad overlays and vacant WC depth-sorted; rain_fg last. No old billboard aperture or marquee boxes.'
    m['loop_note']='Native nonnegative light/reflection/rain difference above its matching temporal-minimum base and below actors/occluders. Indoor and shelter rain protection remains; the old billboard/marquee protection masks are removed. Foreground rain is a separate additive stream. Use full.png as the flattened still fallback.'
    m['notes']='Pass 9 complete pack. Current geometry, native loops and page integration contracts are documented in ../NOTES-PASS9.md and pass9_integration.'
    m['pass9_art']={'scene':'../roxy_pass9.blend','source_pack':'out8b','preview':'../qa9/preview_1.png','no_screen_facing_signs':True,'old_billboard_aperture_removed':True,'world_units_per_tile_z_px':73.4846922835,'neon':'Bent glass d.gg, blue d / pink dot / mint gg, backer, brackets, rounded ends, local additive halo and physically lit sidewalk reflections. One neighbour tube flickers per six seconds.','decode_measurement':videos,'live_obs_benchmark_performed':False,'historical_metadata':'pass4 through pass8b fields describe earlier packs; pass9_art and pass9_checks govern current art.'}
    m['pass9_integration']={'led_signs':'Two rows of seven dots. Row top/bottom and along are world coordinates; dot pitch is in z_px units. Columns run column_direction along the wall for readable text. 108 columns allow 18 six-column glyphs. Amber title and red score supplied by page.','poster_bulbs':'Select idle OR chase per numbered variant_group. Idle is a single steady frame; chase is 72 frames at 12 fps. Both plus-lighter at z_index 902.','ads':'quad_px is logical 1080p TL/TR/BR/BL, clockwise in screen coordinates. Project content into that quad, then draw straight-RGBA overlay at its supplied x/y/w/h at the same depth. Blank surfaces are in the background/parent. Bus ad_panel_quad is local to the shared sprite canvas for each state.','wc':'Choose vacant OR occupied; same rectangle, straight RGBA source-over at z_index 901.','storefront':'Use new render_layers. Water and film share their owning glass-slice depth. Entrance header has three overhead slices; no door leaf obstructs the entry route.','4k':'At 2x use native base@2x.png plus light_loop_2x.webm. It is rendered from native 4K surface positions and textures; rain, impacts and steam are evaluated at native resolution. rain_fg remains 1080p.','retired':'marquees is empty; billboard_rect is absent. Stop drawing the former HUD/title boxes and green-screen rectangle.'}
    m['prop_loop_contract'].update(format='Use each entry blend and alpha: RGB on black for plus-lighter, straight RGBA for source-over.',phase='Use per-entry fps/frames, including one-cell steady entries and six-second 12fps water/bulbs; do not assume a common sheet length.')
    m['pass8_prop_loop_contract']['glass_atlas_decoded_bytes_both_scales']=prop['glass_decoded_bytes_both_scales']
    m['validation'].update(calibration='../qa9/calibration.json',layout='../qa9/final_validation.json',loop_period='../qa9/weather_validation.json',encoded_video='../qa9/video_validation.json',interfaces='../qa9/interface_validation.json')
    # Actual delivered composites at both resolutions; no synthetic green aperture.
    for s,suffix in [(1,''),(2,'@2x')]:
        write(OUT/('full'+suffix+'.png'),compose(m,60,s));write(QA/('final_decoded_f072'+suffix+'.png'),compose(m,72,s,True));write(QA/('fallback_dry_full'+suffix+'.png'),compose(m,60,s,dry=True))
    for f in [0,36,108,143]:write(QA/('final_decoded_f'+str(f).zfill(3)+'.png'),compose(m,f,1,True))
    write(QA/'poster_chase_and_occupied.png',compose(m,72,1,True,chase=True,wc='occupied'))
    # Vehicle contact sheet uses exact delivered 2x cells over a neutral ground.
    canvas=np.zeros((1200,1800,4),np.uint8);canvas[:,:,:3]=[29,35,43];canvas[:,:,3]=255
    y=10
    for kind,dirs in m['vehicles'].items():
        for j,(direction,e) in enumerate(dirs.items()):
            a=read(OUT/e['file_2x']);blend(canvas,a,j*900+10,y)
        y+=280
    write(QA/'vehicle_branding_contact.png',canvas)
    status('Final native stills, decoded rainy compositions, alternate poster/WC state and vehicle contact sheet assembled for inspection')
    before=json.loads((QA/'live_before.json').read_text());assert len(before)==2625,len(before)
    for e in before:
        p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='manifest.json':files.append(dict(file=p.relative_to(OUT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    # Verify referenced files, atlas dimensions, transparent color hygiene, ad winding.
    def refs(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if isinstance(v,str) and k in ['file','file_2x','light','light_2x','light_brake','light_brake_2x','light_indicator','light_indicator_2x','light_indicator_only','light_indicator_only_2x']:assert (OUT/v).is_file(),v
                refs(v)
        elif isinstance(o,list):
            for v in o:refs(v)
    refs(m)
    for e in m['prop_loops']:
        for s,key in [(1,'file'),(2,'file_2x')]:
            p=OUT/e[key];w,h=struct.unpack_from('>II',p.read_bytes(),16);assert [w,h]==[e['w']*e['columns']*s,e['h']*e['rows']*s],e['name']
            if e.get('alpha')=='straight':
                a=read(p);assert not a[a[:,:,3]==0,:3].any(),e['name']
    for ad in m['ad_surfaces']:
        p=ad['quad_px'];area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))/2;assert area>0
    report=dict(passed=True,protected_live_files=len(before),protected_live_packs=9,protected_sha256_unchanged=True,holdouts=holds,camera=cal,changed_occluder_slices=slice_checks,vehicle=veh,props=prop,doors=door_checks,video=reports,interfaces=interfaces,native_4k_vs_upscaled_1080p_mean_abs=native_error,no_screen_facing_text=json.loads((QA/'scene_metadata.json').read_text())['no_camera_facing_text'],old_green_aperture='Retired by brief 11; replaced by facade billboard in perspective',files=len(files)+1,bytes_without_manifest=sum(e['bytes'] for e in files))
    m['pass9_checks']={'report':'../qa9/final_validation.json','passed':True,'protected_live_files':len(before),'occlusion_pixels':[0,0],'native_loop_2x':True}
    (QA/'asset_inventory.json').write_text(json.dumps(files,indent=2));(QA/'final_validation.json').write_text(json.dumps(report,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2));status('Complete pass-9 manifest published after validation; all 2625 files in nine live packs remain byte-identical')
if __name__=='__main__':main()
