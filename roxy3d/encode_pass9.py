import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pass9_common import ROOT,QA
import json
import encode_pass8 as e
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['light_loop','rain_fg','light_loop_2x']
assert all(k in ['light_loop','rain_fg','light_loop_2x'] for k in requested)
previous=json.loads((QA/'video_metadata.json').read_text()) if (QA/'video_metadata.json').exists() else {}
requested=[k for k in requested if k not in previous]
src=(ROOT/'encode_pass8.py').read_text().replace('from pass8_common import','from pass9_common import')
src=src.replace("assert json.loads((QA/'weather_validation.json').read_text())['passed']","assert all(k in json.loads((QA/'weather_validation.json').read_text())['streams'] for k in "+repr(requested)+")")
src=src.replace('reports={}',"reports=json.loads((QA/'video_metadata.json').read_text()) if (QA/'video_metadata.json').exists() else {}")
src=src.replace("for kind in ['light_loop','rain_fg']:","for kind in "+repr(requested)+":\n        width,height=(3840,2160) if kind=='light_loop_2x' else (1920,1080)\n        sc.render.resolution_x=width;sc.render.resolution_y=height")
src=src.replace('orig_width==1920 and movie.elements[0].orig_height==1080','orig_width==width and movie.elements[0].orig_height==height').replace("'size':[1920,1080]","'size':[width,height]")
exec(compile(src,str(ROOT/'encode_pass8.py'),'exec'),e.__dict__)
e.main()
