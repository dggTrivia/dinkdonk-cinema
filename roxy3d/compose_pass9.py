import json,math
import numpy as np
from pass9_common import ROOT,QA,OUT
from pngio import read,write,predecode
from package_vehicles import blend,upscale2

def cell(e,frame,scale):
    a=read(OUT/e['file_2x' if scale==2 else 'file']);w=e['w']*scale;h=e['h']*scale;f=frame%e['frames'];x=f%e['columns']*w;y=f//e['columns']*h
    return a[y:y+h,x:x+w]

def compose(m,frame=60,scale=1,decoded=False,dry=False,chase=False,wc='vacant',test_ads=False):
    suffix='@2x' if scale==2 else '';a=read(OUT/(('lit_bg_dry' if dry else 'base')+suffix+'.png'))
    if not dry:
        kind='light_loop_2x' if scale==2 else 'light_loop';folder=QA/(('decoded_' if decoded else '')+kind+('' if decoded else '_frames'))
        light=read(folder/('f'+str(frame).zfill(3)+'.png'));blend(a,light,0,0,True)
    draws=[]
    for e in m['render_layers']:draws.append((e['z_index'],False,e['x'],e['y'],read(OUT/(e['file'][:-4]+suffix+'.png'))))
    for e in m['prop_loops']:
        if e['name'].startswith('arcade_') and e['name']!='arcade_attract':continue
        if e['name'].startswith('poster_bulbs_') and e['name'].endswith('_chase' if not chase else '_idle'):continue
        if dry and e['name'].startswith(('water_','film_','awning_rain','shelter_drip')):continue
        f=int(frame/24*e['fps'])%e['frames'];draws.append((e['z_index'],e.get('blend','plus-lighter')=='plus-lighter',e['x'],e['y'],cell(e,f,scale)))
    for ad in m['ad_surfaces']:
        if test_ads:
            from interfaces_pass9 import quad_art
            x,y,src=quad_art(ad['quad_px'],scale)
            draws.append((ad['z_index']-.01,False,x,y,src))
        e=ad['overlay'];draws.append((ad['z_index'],False,e['x'],e['y'],read(OUT/e['file_2x' if scale==2 else 'file'])))
    e=m['wc_indicator'][wc];draws.append((e['z_index'],False,e['x'],e['y'],read(OUT/e['file_2x' if scale==2 else 'file'])))
    for z,add,x,y,src in sorted(draws,key=lambda e:e[0]):blend(a,src,x*scale,y*scale,add)
    if not dry:
        fg=read(QA/(('decoded_rain_fg' if decoded else 'rain_fg_frames'))/('f'+str(frame).zfill(3)+'.png'))
        blend(a,upscale2(fg) if scale==2 else fg,0,0,True)
    return a

if __name__=='__main__':
    m=json.loads((QA/'manifest_props.json').read_text());predecode([OUT/(e['file'][:-4]+s+'.png') for e in m['render_layers'] for s in ['', '@2x']])
    for f in [0,60,143]:write(QA/('assembled_f'+str(f).zfill(3)+'.png'),compose(m,f))
