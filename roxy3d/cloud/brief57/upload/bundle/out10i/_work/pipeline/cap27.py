import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from runtime import Renderer,WORK,pixels,rgba8,log,atomic_json
from common import ROOT
import package_layers as layers
r=Renderer();r.display(pixels(WORK/'buffers/adaptive_threshold_001.exr'),WORK/'independent_reference27.png')
ref=rgba8(WORK/'independent_reference27.png');final=rgba8(ROOT.parent.parent/'qa10/draft14-fast.png')
yy,xx=np.indices(final.shape[:2]);mask=(xx>360)&(xx<548)&(abs(yy+xx*.5-593.33)<4)
delta=np.mean(ref[:,:,:3].astype(float)-final[:,:,:3],axis=2);bad=mask&(delta>35)
points=list(zip(*np.where(bad)));chosen=sorted(points,key=lambda p:delta[p],reverse=True)[:8]
checks=json.loads((ROOT/'smoke/group-comparison.json').read_text())['groups'];sources=[]
for g in checks:
    n=g['name'];p=rgba8(WORK/('draft_cut_'+n+'.png'));uv=np.load(WORK/'positions'/('fast27_ref_'+n+'.npz'))['uv']
    spec=next(s for s in r.meta['groups'] if s['name']==n);tiles=layers.tile_clips(spec);u0,v0,u1,v1=spec['footprint'];nu=max(1,__import__('math').ceil(u1-u0-.01));nv=max(1,__import__('math').ceil(v1-v0-.01))
    own=layers.owners(spec,uv)
    sources.append((g,p,uv,own,tiles))
for y,x in chosen:
    stack=[]
    for g,p,uv,own,tiles in sources:
        lx=x-round(g['rect'][0]*2/3);ly=y-round(g['rect'][1]*2/3)
        if 0<=lx<p.shape[1] and 0<=ly<p.shape[0] and p[ly,lx,3]>0:stack.append(dict(name=g['name'],rgba=p[ly,lx].tolist(),uv=uv[ly,lx].tolist(),z=tiles[own[ly,lx]]['z_index']))
    log('cap_pixel',xy=[int(x),int(y)],reference=ref[y,x].tolist(),final=final[y,x].tolist(),stack=sorted(stack,key=lambda s:s['z']))
log('cap_error_count',count=len(points))
holes=int((mask&(ref[:,:,:3].min(axis=2)>100)&(final[:,:,:3].max(axis=2)<10)).sum())
atomic_json(ROOT/'smoke/visual27.json',dict(wall_cap_black_holes=holes,large_differences_in_cap_band=int(bad.sum()),passed=holes==0,scope='Bright cap pixels must not become black holes in the layer-composed still; independent already-rendered physical reference'))
assert holes==0,holes
