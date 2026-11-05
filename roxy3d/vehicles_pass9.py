"""Rebuild every branded vehicle state, retaining published sprite canvases."""
import sys,json,types,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from pass9_common import ROOT,QA,OUT,LIVE,status
import build_vehicles as v
import render_vehicle_pass5 as rv
from pass8_common import gpu

# Reuse the established geometry with explicit source-level brand substitutions.
src=(ROOT/'build_vehicles.py').read_text().replace('ROXY TRANSIT','d.gg TRANSIT').replace('95 ROXY','95 d.gg').replace('RXY 95','DGG 95').replace('roxy_vehicles.blend','roxy_vehicles_pass9.blend')
src=src.replace("'Roxy pink reflection'","'d.gg blue reflection'").replace("100,(1,.09,.37)","100,(.15,.52,1)")
src=src.replace("(-.05,side*.409,25),.066","(-.05,side*.409,31),.040")
exec(compile(src,str(ROOT/'build_vehicles.py'),'exec'),v.__dict__)
v.QA=QA/'vehicles';rv.QA=v.QA
original_bus=v.bus
def bus(opened=False):
    original_bus(opened)
    for side in [-1,1]:
        vv=side*.414
        v.box('d.gg bus ad panel frame',-.65,vv-.009,.65,vv+.009,19.5,29.2,'black',.003)
        v.box('d.gg bus blank advertisement',-.61,vv+side*.012-.002,.61,vv+side*.012+.002,20.5,28.2,'cream',.001)
v.bus=bus
original_scene=rv.scene
def scene(*args):
    sc,model,t=original_scene(*args);gpu(sc);return sc,model,t
rv.scene=scene

def main():
    v.QA.mkdir(exist_ok=True);rows=[]
    for kind in v.SPECS:
        for direction in ['plus','minus']:
            for opened in ([False,True] if kind in ['bus','taxi'] else [False]):
                name=kind+'_'+direction+('_open' if opened else '')
                for scale in [1,2]:rows.append(v.make(kind,direction,opened,64,scale))
                rv.positions(kind,direction,opened,name)
                rv.lights(kind,direction,opened,name,48)
                (v.QA/'render_vehicles.json').write_text(json.dumps({'renders':rows},indent=2))
                status('Rebranded vehicle body, ownership and lamp states rendered at both resolutions: '+name)
    assert not [o for o in bpy.context.scene.objects if o.type=='FONT' and any(s in o.data.body.upper() for s in ['ROXY','RXY'])]
if __name__=='__main__':main()
