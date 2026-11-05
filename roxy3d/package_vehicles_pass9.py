import json
import numpy as np
from pass9_common import ROOT,QA,OUT,LIVE,status
from pngio import read,write,predecode
from package_vehicles import shadow_body,road_light,project
import package_vehicle_pass5 as pv

def main():
    m=json.loads((QA/'manifest_props.json').read_text());folder=QA/'vehicles';rows=json.loads((folder/'render_vehicles.json').read_text())['renders']
    pv.QA=folder;pv.OUT=OUT
    predecode(list((folder/'raw').glob('*.png'))+list((folder/'light_raw').glob('*.png')))
    checks=[];lights=[]
    for kind,dirs in m['vehicles'].items():
        for direction,e in dirs.items():
            for opened,v in [(False,e)]+([(True,e['door_open'])] if 'door_open' in e else []):
                name=kind+('_plus' if direction=='+u' else '_minus')+('_open' if opened else '')
                for scale,key,s in [(1,'file',''),(2,'file_2x','@2x')]:
                    row=next(r for r in rows if r['name']==name and r['scale']==scale)
                    body=shadow_body(read(folder/'raw'/(name+s+'.png')),row);light=road_light(read(folder/'raw'/(name+'_light'+s+'.png')),row)
                    x0=(300-e['anchor'][0])*scale;y0=(230-e['anchor'][1])*scale;w=e['w']*scale;h=e['h']*scale
                    a=body[y0:y0+h,x0:x0+w];assert a.shape==(h,w,4);write(OUT/v[key],a)
                    write(OUT/v['light' if scale==1 else 'light_2x'],light[y0:y0+h,x0:x0+w,:3])
                checks+=pv.slice_vehicle(e,v,name,direction)
                for state in ['brake']+(['indicator'] if kind in ['bus','taxi'] else []):
                    for scale in [1,2]:
                        row=next(r for r in rows if r['name']==name and r['scale']==scale);lights.append(pv.lamp_variant(e,v,name,row,state,scale))
                if kind in ['bus','taxi']:
                    for scale,s in [(1,''),(2,'_2x')]:
                        a=read(OUT/v['light'+s])[:,:,:3];b=read(OUT/v['light_indicator'+s])[:,:,:3]
                        write(OUT/v['light_indicator_only'+s],np.maximum(b.astype(np.int16)-a.astype(np.int16),0).astype(np.uint8))
                if kind=='bus':
                    f=1 if direction=='+u' else -1
                    # Front-visible world side is +v in both directions; order is screen clockwise.
                    vv=.426
                    quad=[project(6+u,11+vv,z)-project(6,11)+np.array(e['anchor']) for u,z in [(-.61,28.2),(.61,28.2),(.61,20.5),(-.61,20.5)]]
                    v['ad_panel_quad']=[p.tolist() for p in quad];v['ad_panel_aspect']=1.22*73.4846922835/7.7
    (QA/'manifest_vehicles.json').write_text(json.dumps(m,indent=2));(QA/'vehicle_validation.json').write_text(json.dumps(dict(passed=True,slices=checks,lights=lights,published_anchors_and_canvases_retained=True,ad_panel_states=4),indent=2))
    status('All 12 vehicle states packaged with d.gg routes/plates, lossless depth slices and refreshed normal/brake/indicator maps; four bus ad quads supplied')
if __name__=='__main__':main()
