import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pass9_common import ROOT,QA,status
import render_doors_pass6 as d
src=(ROOT/'render_doors_pass6.py').read_text().replace('roxy_pass6.blend','roxy_pass9.blend').replace("QA=ROOT/'qa6'","QA=ROOT/'qa9'")
src=src.replace("sc=bpy.context.scene\n","sc=bpy.context.scene\n    from pass8_common import gpu\n    gpu(sc)\n")
exec(compile(src,str(ROOT/'render_doors_pass6.py'),'exec'),d.__dict__)
d.main();status('Six door animations rerendered under the pass-9 wall lighting; original pivots and timings retained')
