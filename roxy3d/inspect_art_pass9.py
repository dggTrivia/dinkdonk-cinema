import json
import numpy as np
from pass9_common import QA,OUT,status
from pngio import read,write,predecode
from package_vehicles import blend

predecode([QA/'steady_bg@2x.png',OUT/'wc_vacant@2x.png',OUT/'wc_occupied@2x.png'])
a=read(QA/'steady_bg@2x.png')
write(QA/'wall_sign_detail.png',a[580:1130,850:1530])
canvas=np.zeros((300,500,4),np.uint8);canvas[:,:,:3]=[34,39,46];canvas[:,:,3]=255
for j,name in enumerate(['vacant','occupied']):
    p=read(OUT/('wc_'+name+'@2x.png'));p=np.repeat(np.repeat(p,3,0),3,1);blend(canvas,p,j*250+20,30)
write(QA/'wc_state_detail.png',canvas)
status('Native wall-sign detail and both delivered WC states prepared for visual inspection')
