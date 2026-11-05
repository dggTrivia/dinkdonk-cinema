"""Inspect a completed source frame while the higher-resolution job continues."""
import json
from pass9_common import QA,OUT,status
from pngio import read,write,predecode
from package_pass2 import grain
from compose_pass9 import compose
predecode([QA/'steady_bg.png']);raw=grain(read(QA/'steady_bg.png'));rects=json.loads((QA/'poster_patch_rects.json').read_text())
for kind in ['base','bg','lit_bg','lit_bg_dry']:
    a=read(OUT/(kind+'.png'))
    for x,y,x1,y1 in rects:a[y:y1,x:x1]=raw[y:y1,x:x1]
    write(OUT/(kind+'.png'),a)
m=json.loads((QA/'manifest_props.json').read_text());write(QA/'preview_weather_f024.png',compose(m,24))
status('Completed 1080p source frame composited with the final poster correction, tall wet glass, bulb frames and local d.gg halo for visual QA')
