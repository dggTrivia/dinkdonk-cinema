"""No-render scheduling/contract checks for both allowed wet cadences."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import production as p
from runtime import WORK,atomic_json,png,rgba8
from fast_pipeline import area2,position2,wet_frames

def run():
    old={n:getattr(p,n) for n in ['WORK','QA','policy','combined','display_cached']};env=os.environ.get('ROXY_WET_FRAMES');cases=[]
    try:
        for setting in [None,24,48]:
            if setting is None:os.environ.pop('ROXY_WET_FRAMES',None)
            else:os.environ['ROXY_WET_FRAMES']=str(setting)
            count=wet_frames();assert count==(24 if setting is None else setting)
            root=WORK/f'schedule_fixture_{count}';root.mkdir(exist_ok=True)
            p.WORK=root;p.QA=root/'qa';p.QA.mkdir(exist_ok=True);(root/'positions').mkdir(exist_ok=True)
            p.policy=lambda:{'fallback_groups':['glass_left']}
            names=['entrance_neon','standee_1','glass_left'];calls=[]
            high=np.ones((8,8,4),np.float32);uv=np.full((8,8,2),2,np.float32)
            class Fake:
                width=3840;height=2160;wet=set(names)
                meta={'groups':[{'name':n,'objects':[n]} for n in names]}
                class Scene:objects={n:n for n in names}
                sc=Scene()
                def rect(self,objects,pad):return [0,0,4,4]
                def capture(self,tag,**kw):
                    assert (self.width,self.height)==(3840,2160)
                    calls.append(('isolated',kw['frame']))
                    if kw['aov']:np.savez_compressed(root/'positions'/(tag+'.npz'),uv=uv)
                    return high*(1+kw['frame']/100),0
            def combined(r,tag,f):
                assert (r.width,r.height)==(3840,2160);calls.append(('combined',f))
                path=root/'masks.npz';np.savez_compressed(path,**{n:np.ones((8,8),np.float32) for n in names})
                return high*(1+f/100),path,uv
            def display(r,a,path,glare=False):
                result=np.rint(np.clip(a*.5,0,1)*255).astype(np.uint8);png(path,result);return result
            p.combined=combined;p.display_cached=display;p.prepare_foreground(Fake())
            expected=list(range(0,48,48//count))
            assert [f for k,f in calls if k=='combined']==expected
            assert [f for k,f in calls if k=='isolated']==expected
            for name in names:
                for scale in [1,2]:
                    folder=root/f'foreground_{name}_{scale}';files=sorted(folder.glob('f*.png'))
                    assert len(files)==(1 if name=='standee_1' else 48)
                    assert rgba8(files[0]).shape==(4*scale,4*scale,4)
                    if count==24 and name!='standee_1':
                        for f in range(0,48,2):assert (folder/f'f{f:03d}.png').read_bytes()==(folder/f'f{f+1:03d}.png').read_bytes()
            cases.append(dict(environment=setting,unique_frames=count,combined_captures=count,isolated_captures=count,static_frames=1,output_slots=48,scale_shapes_exact=True,duplicated_pairs_exact=count==24))
        a=np.arange(4*4*4,dtype=np.float32).reshape(4,4,4)
        assert np.array_equal(area2(a),np.array([[a[y:y+2,x:x+2].mean(axis=(0,1)) for x in [0,2]] for y in [0,2]]))
        alpha=np.zeros((2,2),np.float32);alpha[0,0]=1;uv=np.zeros((2,2,2),np.float32);uv[0,0]=[7,9];uv[1,1]=[100,100]
        assert np.array_equal(position2(uv,alpha),[[[7,9]]])
        import package_layers as layers
        specs=json.loads((p.ROOT/'production.json').read_text())['groups']
        wall=next(e for e in specs if e['name']=='partition_left');cap=next(e for e in specs if e['name']=='restroom_side_wall')
        wall_tiles=layers.tile_clips(wall);cap_tiles=layers.tile_clips(cap)
        assert len(wall_tiles)==5 and len(cap_tiles)==6
        for w,c in zip(wall_tiles,cap_tiles[1:]):
            assert c['footprint'][1]==w['footprint'][1] and c['z_index']==w['z_index']+1
    finally:
        for n,value in old.items():setattr(p,n,value)
        if env is None:os.environ.pop('ROXY_WET_FRAMES',None)
        else:os.environ['ROXY_WET_FRAMES']=env
    report=dict(passed=True,default=24,override=48,cases=cases,linear_area_exact=True,transparent_positions_do_not_bleed=True,continuous_wall_cap_depth_aligned=True,scope='Synthetic scheduling/packing assertions only; no 3D render or motion clip')
    atomic_json(p.ROOT/'fast_contracts.json',report);print(json.dumps(report))

if __name__=='__main__':run()
