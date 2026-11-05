import json
from pass9_common import QA,status
from pngio import write
from compose_pass9 import compose
m=json.loads((QA/'manifest_vehicles.json').read_text());a=compose(m,60,2)
write(QA/'native_weather_f060@2x.png',a)
for name,rect in [('native_glass_detail',(540,645,1140,975)),('native_poster_detail',(480,350,785,545)),('native_blade_detail',(285,300,360,535)),('native_ad_detail',(200,490,295,590))]:
    x,y,x1,y1=rect;write(QA/(name+'.png'),a[y*2:y1*2,x*2:x1*2])
status('Native 4K source composition and unscaled glass, poster, neon and shutter details prepared for visual inspection')
