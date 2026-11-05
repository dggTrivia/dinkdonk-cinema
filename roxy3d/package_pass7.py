"""Self-contained additive pass-7 pack. All inherited files are copied verbatim."""
from pathlib import Path
import json, shutil, time
import numpy as np
from pngio import read, write, predecode
from package_cat_pass5 import down_rgba

ROOT=Path(__file__).resolve().parent
QA=ROOT/'qa7'; OUT=ROOT/'out7'; LIVE=ROOT/'out6'

def vehicle_variants(m):
    for kind in ['bus','taxi']:
        for direction,e in m['vehicles'][kind].items():
            stem=kind+('_plus' if direction=='+u' else '_minus')
            yield stem,e,e
            yield stem+'_open',e,e['door_open']

def main():
    start=time.perf_counter();OUT.mkdir(exist_ok=True)
    for p in LIVE.rglob('*'):
        if p.is_file() and p.name!='manifest.json':
            target=OUT/p.relative_to(LIVE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    m=json.loads((LIVE/'manifest.json').read_text())
    meta=json.loads((QA/'items_metadata.json').read_text());predecode(list((QA/'items_raw').glob('*.png')))
    items={}
    for name,e in meta['items'].items():
        hi=down_rgba(read(QA/'items_raw'/(name+'@4x.png')));lo=down_rgba(hi)
        e2={'file':'items/'+name+'.png','file_2x':'items/'+name+'@2x.png',
            'w':e['w'],'h':e['h'],'anchor':e['anchor'],'attach_point':e['attach_point']}
        write(OUT/e2['file'],lo);write(OUT/e2['file_2x'],hi);items[name]=e2
    # Subtract the delivered, quantized maps at each resolution independently.
    # This also retains the exact Cycles wet-road reflection in the old variant.
    paths=[OUT/e[k] for _,_,e in vehicle_variants(m) for k in ['light','light_2x','light_indicator','light_indicator_2x']]
    predecode(paths);rows=[]
    for name,parent,e in vehicle_variants(m):
        for scale,suffix,key in [(1,'',''),(2,'@2x','_2x')]:
            normal=read(OUT/e['light'+key])[:,:,:3].astype(np.int16)
            indicator=read(OUT/e['light_indicator'+key])[:,:,:3].astype(np.int16)
            delta=np.maximum(indicator-normal,0).astype(np.uint8)
            filename='vehicles/'+name+'_light_indicator_only'+suffix+'.png'
            write(OUT/filename,delta);e['light_indicator_only'+key]=filename
            rows.append({'name':name,'scale':scale,'w':parent['w']*scale,'h':parent['h']*scale,
                         'anchor':parent['anchor'],'added_rgb_sum':delta.sum(axis=(0,1)).tolist(),
                         'nonblack_pixels':int((delta.max(axis=2)>0).sum()),'max_added':int(delta.max())})
    assert 'items' not in m
    m['items']=items
    m['item_contract']={
        'placement':'Top-left = attachment screen point - item.anchor. w/h/anchor are logical 1x pixels, also when file_2x is displayed at w by h.',
        'alpha':'Straight RGBA; ordinary source-over. Transparent pixels have zero RGB. Internal shadows and highlights are baked; no ground shadow.',
        'carried':'Popcorn and soda attach at the visible bottom centre. Suggested attachment for a 50px emote: its lower right, chosen by the page.',
        'staff':'Both caps attach at their visible bottom centre; place this at the top centre of the roughly 50px emote.',
        'paper':'Stub and ticket attach at their image centre. The whole ticket has a half-pixel vertical anchor because its canvas is 11px high. Rotate/translate around this point for a flying ticket.',
        'depth':'Keep an attached item with its owner and draw it immediately above the emote. These sprites introduce no new floor footprints.',
        'render':'Original procedural 3D, unchanged layout-2 orthographic camera and pass-6 lighting at P(8,7,50). Cycles 4x supersampling filtered to 2x then 1x with premultiplied area averaging.'}
    m['vehicle_indicator_only_contract']={
        'definition':'light_indicator_only = max(light_indicator - light, 0), applied per sRGB RGB channel to the delivered maps independently at 1x and 2x.',
        'composition':'Draw one normal OR brake light map, then add light_indicator_only only while the amber signal is on. Use plus-lighter / additive RGB clamped to 255, below all vehicle bodies.',
        'placement':'Use the same top-left P(u,v)-direction.anchor, width and height as the selected closed/open light and body. Door-open indicator fields are nested under door_open.',
        'off':'Hide the indicator-only layer. No new light or vehicle animation timing is imposed.',
        'compatibility':'Inherited light_indicator remains a complete replacement light map; all existing fields and contracts are unchanged. The new additive-only files contain no normal headlights or tail lights.'}
    # "Only add" is literal: preserve every inherited leaf, including legacy pass.
    m['asset_pack_pass']=7
    m['pass7_art']={'base_scene_pass':6,'additions':['six carried/staff items at 1x and 2x','eight indicator-only vehicle states at 1x and 2x'],
                    'legacy_pass_field':'Inherited pass=6 is retained under the additive-only contract; asset_pack_pass=7 identifies this complete pack.',
                    'changed_existing_coordinates':[],'changed_existing_assets':[]}
    m['pass7_validation']='../qa7/final_validation.json'
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    (QA/'packaging.json').write_text(json.dumps({'items':len(items),'indicator_variants':rows,'seconds':round(time.perf_counter()-start,3)},indent=2))
    print('PASS7_PACKAGED',len(items),'items;',len(rows),'indicator PNGs',flush=True)

if __name__=='__main__':main()
