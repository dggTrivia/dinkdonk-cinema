"""Sequential GPU stages; all logs/cache/output stay under roxy3d."""
import sys,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BLENDER=ROOT.parent/'tools/blender-5.2.3-windows-x64/blender.exe'
for key in ['TEMP','TMP']:os.environ[key]=str(ROOT/'cache/temp')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
stages=[('audit','audit_draft5_source.py',[]),('preview','render_draft5.py',['--','preview']),('details','render_draft5.py',['--','details','--only','alley,service_art,billboard,cabge']),('weather','weather_draft5.py',[]),('sparkle_off','render_draft5.py',['--','sparkle_off']),('loop','render_draft5.py',['--','loop']),('encode','encode_draft5.py',[])]
for name,script,args in stages:
    print('START',name,flush=True)
    with (ROOT/'qa10'/('draft5_'+name+'.log')).open('w',encoding='utf-8') as log:
        subprocess.run([str(BLENDER),'-b','-t','6','--python-exit-code','1','--python',str(ROOT/script)]+args,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT.parent)
    print('DONE',name,flush=True)
