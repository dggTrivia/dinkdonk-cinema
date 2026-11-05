import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from common import ROOT
from runtime import WORK,pixels,rgba8,log
checks=json.loads((ROOT/'smoke/group-comparison.json').read_text())['groups']
for name in ['partition_left','restroom_side_wall']:
    a=pixels(WORK/'buffers'/('fast27_ref_'+name+'.exr'));uv=np.load(WORK/'positions'/('fast27_ref_'+name+'.npz'))['uv']
    rect=next(g['rect'] for g in checks if g['name']==name)
    yy,xx=np.indices(a.shape[:2]);z=350+30*(uv[:,:,0]+uv[:,:,1])-(rect[1]+(yy+.5)*1.5)
    solid=a[:,:,3]>.95;edge=(a[:,:,3]>.01)&(a[:,:,3]<.95)
    log('depth_diagnostic',name=name,solid_uv_bounds=[np.percentile(uv[solid],q,axis=0).tolist() for q in [0,1,50,99,100]],edge_uv_bounds=[np.percentile(uv[edge],q,axis=0).tolist() for q in [0,1,50,99,100]],z_solid=[float(np.percentile(z[solid],q)) for q in [0,1,50,99,100]])
