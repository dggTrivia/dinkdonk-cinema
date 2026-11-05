"""Layout-3 foreground slices and all page placement interfaces."""
import json
import numpy as np
from pass10_common import ROOT,QA,OUT,LIVE,status
from pngio import read,write,predecode
import package_layers as layers

def main():
    m=json.loads((LIVE/'manifest.json').read_text());meta=json.loads((QA/'scene_metadata_final.json').read_text());rows=json.loads((QA/'rendered_occluders_final.json').read_text())
    parents=[dict(e) for e in rows if 'footprint' in e]
    assert len(parents)==len(meta['production_occluders'])
    predecode([OUT/e[k] for e in rows for k in ['file','file_2x']]);layers.OUT=OUT;layers.QA=QA
    for e in parents:e['tile_clips']=layers.tile_clips(e)
    slices=layers.depth_slices(parents)
    for e in slices:
        if e['parent']=='paste_wall':e['z_index']=99
    m['occluders']=parents;m['render_layers']=sorted(slices,key=lambda e:e['z_index'])
    m.update(layout=3,status='stills_ready',asset_pack_pass=10,asset_pack_revision='10',marquees=[],led_signs=meta['led_signs'],poster_frames=meta['poster_frames'])
    m['doors']=[dict(screen=i,wall='v0',at=u,approach=[[u,1.4],[u,.55]]) for i,u in enumerate([4.8,8.2,11.2],1)]
    stalls=[]
    for v in [4.4,5.4,6.4,7.4]:stalls.append(dict(spot=[1.5,v],route_points=[[1.4,3.5],[1.6,4.1],[1.6,v],[1.5,v]]))
    m['restroom']=dict(door=[1.4,3.0],outside=[1.4,2.6],inside=[1.4,3.5],stalls=stalls,sinks=[[2.12,4.1],[2.63,4.1]],dryer=[.55,3.55],route_points={'stalls':[e['route_points'] for e in stalls],'sinks':[[[1.4,3.5],[1.6,4.1],[2.12,4.1]],[[1.4,3.5],[1.6,4.1],[2.63,4.1]]],'dryer':[[1.4,3.5],[.55,3.55]]},room_footprint=[0,3,2.9,8.4])
    m['queue']=dict(slots=[[round(4.85+.62*i,2),7.4] for i in range(7)],entry=[9.3,7.4],window2_gap=[4.4,5.79])
    m['ad_surfaces']=[]
    for ad in meta['ad_surfaces']:
        e=next(e for e in rows if e['name']==ad['layer'])
        d={k:v for k,v in ad.items() if k not in ['layer','overlay']};d['overlay']={k:e[k] for k in ['file','file_2x','x','y','w','h']};d['overlay'].update(alpha='straight',blend='source-over');m['ad_surfaces'].append(d)
    # Changed pane depth owners match the existing nine logical water divisions.
    m['prop_loops']=[e for e in m['prop_loops'] if not e['name'].startswith(('water_glass_','film_glass_','poster_bulbs_','dgg_neon_halo'))]
    for e in m['prop_loops']:
        if e.get('parent_slices'):
            known={p['name'] for p in slices};e['parent_slices']=[n for n in e['parent_slices'] if n in known]
    m['baked_signs']=[x for x in m['baked_signs'] if x not in ['d.gg','roxy']]+['DINK DONK','DinkDonk hooded frog with bell']
    m['door_anims']=[];m['wc_indicator']={}
    for scale,suffix in [(1,''),(2,'@2x')]:write(OUT/('glow'+suffix+'.png'),np.zeros((1080*scale,1920*scale,3),np.uint8))
    m['static_glow_enabled']=False;m['static_glow']=False
    (QA/'manifest_scene.json').write_text(json.dumps(m,indent=2));status('All 39 foreground parents depth-sliced; layout-3 door, restroom routes, queue, LED/poster and ad interfaces assembled')
if __name__=='__main__':main()
