"""Rebuild only scene-dependent assets, carry every other pass-5 asset forward."""
import json
from pathlib import Path
import compose_pass4 as c
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa6';OUT=ROOT/'out6'

def preserve_billboard():
    # The page replaces this exact rectangle with video. Preserve its inherited
    # placeholder pixels as well as its bounds, independent of new indirect GI.
    import numpy as np
    from pngio import read,write,predecode
    for scale,suffix in [(1,''),(2,'@2x')]:
        source=ROOT/'out5'/('base'+suffix+'.png');predecode([source]);old=read(source)
        region=(slice(40*scale,364*scale),slice(1296*scale,1872*scale))
        for stem in ['base','bg','lit_bg','full']:
            path=OUT/(stem+suffix+'.png');a=read(path)
            if not np.array_equal(a[region],old[region]):a[region]=old[region];write(path,a)

def surface_metadata(m):
    measured=json.loads((QA/'geometry_bounds.json').read_text());old=json.loads((ROOT/'out5/manifest.json').read_text())
    byname={e['name']:e for e in old['occluders']};changes=[]
    for e in m['occluders']:
        previous=byname[e['name']];actual=measured[e['name']]
        assert actual['geometry_footprint']==previous['geometry_footprint']
        if actual['geometry_z_px']!=previous['geometry_z_px']:
            changes.append({'name':e['name'],'old_geometry_z_px':previous['geometry_z_px'],'new_geometry_z_px':actual['geometry_z_px'],
                'reason':'Raised hairline countertop scratch relief; original sorting height, footprint, crop and slice rectangles retained.'})
        e.update(actual)
    m['pass6_art']['surface_height_changes']=changes

def main():
    co=json.loads((QA/'coordinates.json').read_text())
    # The analytic exterior rain mask must follow the relocated title boxes.
    c.motion.OUTSIDE=(~c.motion.BUILDING).copy()
    for e in co['marquees']:
        x,y=e['bottom_center'];w,h=e['inner_size']
        c.motion.OUTSIDE[max(0,int(y-h-7)):int(y+7),int(x-w/2-7):int(x+w/2+7)]=False
    c.motion.OUTSIDE[40:364,1296:1872]=False
    c.QA=QA;c.OUT=OUT;c.SOURCE=ROOT/'out5';c.main();preserve_billboard()
    m=json.loads((QA/'manifest_art.json').read_text());old=json.loads((ROOT/'out5/manifest.json').read_text())
    m['pass4_art']=old['pass4_art'];m['pass']=6;m['status']='stills_ready'
    m['marquees']=co['marquees'];m['poster_frames']=co['poster_frames']
    m['pass6_art']={'coordinate_changes':co['changes'],'carpet':'Unmodified pass4 geometry and material node trees.',
        'wear':'Counter chips and scratches, scuffed kickplates and thresholds, corner grime, pavement burns/gum, dirty glass; furniture trim emission reduced to 30 percent of pass4.',
        'door_positions':'All five screen doors and the restroom stay fixed; hinges now reveal shallow warm vestibules.'}
    surface_metadata(m)
    (QA/'manifest_stills_ready.json').write_text(json.dumps(m,indent=2));(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print('PASS6_STILL_MANIFEST_READY',flush=True)

if __name__=='__main__':main()
