import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runtime import Renderer,log
from fast_pipeline import combined
import numpy as np
r=Renderer(1280,720)
a,path,uv=combined(r,'fast27_combined_720')
with np.load(path) as masks:
    log('mask_probe',shape=list(a.shape),groups={n:{'max':float(masks[n].max()),'pixels':int((masks[n]>0).sum())} for n in masks.files})
