import json,math
import numpy as np
from pass9_common import ROOT,QA,OUT,LIVE,status
from pngio import read,write,predecode
import package_layers as layers

def main():
    m=json.loads((LIVE/'manifest.json').read_text());meta=json.loads((QA/'scene_metadata.json').read_text())
    rows=json.loads((QA/'rendered_occluders.json').read_text());parents=[e for e in rows if 'footprint' in e]
    predecode([OUT/(e['file'][:-4]+s+'.png') for e in rows for s in ['', '@2x']])
    layers.OUT=OUT;layers.QA=QA
    for e in parents:e['tile_clips']=layers.tile_clips(e)
    changed={e['name'] for e in parents};slices=layers.depth_slices(parents)
    for e in slices:
        if e['parent']=='paste_wall':e['z_index']=99
    m['occluders']=[e for e in m['occluders'] if e['name'] not in changed]+parents
    m['render_layers']=sorted([e for e in m['render_layers'] if e['parent'] not in changed]+slices,key=lambda e:e['z_index'])
    m['marquees']=[];m.pop('billboard_rect',None)
    m['led_signs']=meta['led_signs'];m['poster_frames']=meta['poster_frames'];m['wc_indicator']=json.loads((QA/'wc_indicator.json').read_text())
    m['ad_surfaces']=[]
    for ad in meta['ad_surfaces']:
        e=next(e for e in rows if e['name']==ad['layer']);d={k:v for k,v in ad.items() if k!='layer'}
        d['overlay']={k:e[k] for k in ['file','x','y','w','h']};d['overlay'].update(file_2x=e['file'][:-4]+'@2x.png',alpha='straight',blend='source-over')
        m['ad_surfaces'].append(d)
    # Empty obsolete global glow prevents the former screen-facing boxes returning.
    for scale,s in [(1,''),(2,'@2x')]:write(OUT/('glow'+s+'.png'),np.zeros((1080*scale,1920*scale,3),np.uint8))
    m['static_glow_enabled']=False
    (QA/'manifest_scene.json').write_text(json.dumps(m,indent=2))
    status('Storefront and changed prop depth slices packaged; wall LED, one-sheet, WC and advertising contracts assembled')
if __name__=='__main__':main()
