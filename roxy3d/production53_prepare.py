"""Adapt only local copies of the approved draft-21 render functions."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent;W=ROOT/'out10g/_work'
p=W/'draft21.py';s=p.read_text()
s=s.replace("{'umbrella':5201,'taxi':5202,'bus':5203}[kind]","{'umbrella':5201,'taxi':5202,'bus':5203,'sedan_a':5202,'sedan_b':5202}[kind]")
s=s.replace("{'umbrella':[40],'taxi':[20,14,10],'bus':[76]}[kind]","{'umbrella':[40],'taxi':[20,14,10],'bus':[76],'sedan_a':[20,14,10],'sedan_b':[20,14,10]}[kind]")
s=s.replace("5210+zone+len(kind)","5210+zone+len('taxi' if kind.startswith('sedan') else kind)")
s=s.replace("elif kind=='taxi':", "elif kind in ['taxi','sedan_a','sedan_b']:")
s=s.replace("if not (-.12<x<.10 and abs(y)<.21):break", "if kind!='taxi' or not (-.12<x<.10 and abs(y)<.21):break")
s=s.replace("z=32.8/r.ZPP+.004", "z=(30.8 if kind=='sedan_b' else 32.8)/r.ZPP+.004")
s=s.replace("x=rng.uniform(.45,.81) if zone==1 else rng.uniform(-.81,-.47)", "end=min(.81,r.v.SPECS[kind]['length']/2-.05)\n                x=rng.uniform(.45,end) if zone==1 else rng.uniform(-end,-.47)")
s=s.replace("        life=rng.choice([2,3,3,4]);", "        m.landing_u=x\n        life=rng.choice([2,3,3,4]);")
s=s.replace("                y=rng.uniform(-.30,.30);z=20/r.ZPP+.004", "                y=rng.uniform(-.30,.30);z=20/r.ZPP+.004\n                if kind=='sedan_b' and zone==1:\n                    headx=r.v.SPECS[kind]['length']/2-.11\n                    side=r.v.SPECS[kind]['width']*.30\n                    if headx-.17<x<headx+.005 and abs(abs(y)-side)<.082:\n                        z=max(20,19+6*(x-(headx-.17))/.175)/r.ZPP+.004")
s=s.replace("32.8/r.ZPP+.003", "(30.8 if kind=='sedan_b' else 32.8)/r.ZPP+.003")
s=s.replace("(.445,-.32,.81,.32,20/r.ZPP+.003),(-.81,-.32,-.465,.32,20/r.ZPP+.003)","(.445,-.32,min(.81,r.v.SPECS[kind]['length']/2-.05),.32,20/r.ZPP+.003),(-min(.81,r.v.SPECS[kind]['length']/2-.05),-.32,-.465,.32,20/r.ZPP+.003)")
p.write_text(s)
print('Prepared copied draft-21 geometry functions')
