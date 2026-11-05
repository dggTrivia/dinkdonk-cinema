import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from render_draft5 import setup,frame
from draft5_common import *
sc=setup();sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=96/1280;sc.render.border_max_x=448/1280;sc.render.border_min_y=80/720;sc.render.border_max_y=336/720
films=[m.node_tree.nodes.get('D5 directional water film') for m in bpy.data.materials if m.node_tree];films=[q for q in films if q]
for name,tangent,rough in [('linked_depth30',(-.707106,.707106,0),.22),('linked_cross30',(.707106,.707106,0),.22)]:
    for q in films:
        vec=q.id_data.nodes.new('ShaderNodeCombineXYZ')
        for i,v in enumerate(tangent):vec.inputs[i].default_value=v
        q.id_data.links.new(vec.outputs[0],q.inputs['Tangent'])
        for link in list(q.inputs['Roughness'].links):q.id_data.links.remove(link)
        q.inputs['Roughness'].default_value=rough
        out=next(n for n in q.id_data.nodes if n.type=='OUTPUT_MATERIAL');mix=out.inputs['Surface'].links[0].from_node
        for link in list(mix.inputs[0].links):q.id_data.links.remove(link)
        mix.inputs[0].default_value=int(name[-2:])/100
        if name=='mirror99':
            q.inputs['Anisotropy'].default_value=0
            for link in list(q.inputs['Normal'].links):q.id_data.links.remove(link)
    frame(sc,WORK/('probe_'+name+'.png'))
    print('FILM_PROBE',name,flush=True)
