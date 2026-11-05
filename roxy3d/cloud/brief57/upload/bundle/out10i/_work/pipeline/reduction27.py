import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from runtime import Renderer,WORK,pixels,diff,within,atomic_json,log
from fast_pipeline import area2
from common import ROOT
r=Renderer(3840,2160)
print('PIXEL_FILTER',r.sc.cycles.pixel_filter_type,r.sc.cycles.filter_width,flush=True)
low=pixels(WORK/'buffers/fast27_native1080_a.exr');baseline=diff(low,pixels(WORK/'buffers/fast27_native1080_b.exr'))
rows=[]
for width in [3.0,2.5]:
    r.sc.cycles.filter_width=width
    high,seconds=r.capture('fast27_filter_'+str(width).replace('.','_'),part='background',rect=[660,230,660,390],state={'pixel_filter_width':width},adaptive=True,threshold=.01)
    d=diff(low,area2(high));row=dict(filter_width=width,difference=d,noise=baseline,passed=within(d,baseline),seconds=seconds);rows.append(row);log('reduction_filter',**row)
    atomic_json(ROOT/'smoke/filter27.json',rows)
