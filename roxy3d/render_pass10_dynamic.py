"""Native 2x source crops for eight doors, two bell poses and WC states."""
import sys,json,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,numpy as np
from mathutils import Matrix,Vector
import build_scene as b
from common import xyz,ZPP,project,render
from pass10_common import ROOT,QA,OUT,status
from render_pass10_scene import load,crop

def matrix(a):return Matrix([a[j:j+4] for j in range(0,16,4)])
def door_pose(objects,amount):
    for o in objects:
        pivot=Vector(o['anim_pivot']);angle=math.radians(o['anim_angle'])*amount
        o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-pivot)@matrix(list(o['closed_matrix']))
    bpy.context.view_layer.update()
def bell_pose(objects,info,state):
    pivot=Vector(info['pivot']);angle=math.radians(info['angles_deg'][state])
    for o in objects:o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Y')@Matrix.Translation(-pivot)@matrix(list(o['bell_original_matrix']))
    bpy.context.view_layer.update()
def projected_bounds(objects):
    return [project(p.x,-p.y,p.z*ZPP) for o in objects for c in o.bound_box for p in [o.matrix_world@Vector(c)]]
def rect(points,pad=12):
    x=max(0,math.floor(min(q[0] for q in points))-pad);y=max(0,math.floor(min(q[1] for q in points))-pad)
    x1=min(1920,math.ceil(max(q[0] for q in points))+pad);y1=min(1080,math.ceil(max(q[1] for q in points))+pad)
    return [x,y,x1-x,y1-y]

def doors():
    meta=json.loads((QA/'scene_metadata_final.json').read_text());sc=load();b.set_visibility();sc.cycles.samples=40;sc.cycles.adaptive_threshold=.018
    sc.render.use_compositing=False;sc.render.film_transparent=False
    records=json.loads((QA/'doors_metadata_final.json').read_text()) if (QA/'doors_metadata_final.json').exists() else []
    done={e['id'] for e in records}
    for info in meta['animations']:
        if info['id'] in done:continue
        leaves=[o for o in sc.objects if o.get('anim_id')==info['id']];assert leaves,info
        points=[project(*p) for p in info['opening_world']]
        for f in np.linspace(0,1,6):door_pose(leaves,float(f));points+=projected_bounds(leaves)
        door_pose(leaves,0);r=rect(points,18);assert r[2]<240 and r[3]<240,(info['id'],r)
        crop(sc,r,2);folder=QA/'doors_raw_final'/info['id'];folder.mkdir(parents=True,exist_ok=True)
        for i in range(6):
            path=folder/('f'+str(i).zfill(3)+'.png')
            door_pose(leaves,.5-.5*math.cos(math.pi*i/5))
            if not path.exists():render(path)
        for i in range(6,16):shutil.copyfile(folder/('f'+str(min(i,15-i,5)).zfill(3)+'.png'),folder/('f'+str(i).zfill(3)+'.png'))
        door_pose(leaves,0)
        e=dict(info,x=r[0],y=r[1],frame_width=r[2],frame_height=r[3],w=r[2],h=r[3],frames=16,columns=4,rows=4,fps=18,seconds=16/18,loop=False,alpha='straight',blend='source-over',frame_order='row-major')
        records.append(e);(QA/'doors_metadata_final.json').write_text(json.dumps(records,indent=2))
        status('Native 2x open/hold/close source sequence rendered: '+info['id'])

def bells_wc():
    meta=json.loads((QA/'scene_metadata_final.json').read_text());sc=load();sc.cycles.samples=48;sc.cycles.adaptive_threshold=.015;sc.render.use_compositing=False;records=[]
    for name,info in meta['bells'].items():
        leaves=[o for o in sc.objects if o.get('bell_id')==name];assert leaves
        points=[]
        for f in [0,1]:bell_pose(leaves,info,f);points+=projected_bounds(leaves)
        r=rect(points,8);assert r[2]<130 and r[3]<130,(name,r)
        for o in sc.objects:
            if o.type in ['MESH','CURVE','FONT']:o.visible_camera=True;o.is_holdout=o not in leaves
        sc.render.film_transparent=True;crop(sc,r,2)
        folder=QA/'bells_raw'/name;folder.mkdir(parents=True,exist_ok=True)
        for state in [0,1]:bell_pose(leaves,info,state);render(folder/('f'+str(state).zfill(3)+'.png'))
        bell_pose(leaves,info,0)
        records.append(dict(name='bell_'+name,x=r[0],y=r[1],w=r[2],h=r[3],frames=2,columns=2,rows=1,fps=20,z_index=101 if name.startswith('rooftop') else 1882,blend='source-over',alpha='straight',frame_order='row-major',loop_seconds=.1,source_emote_delay_seconds=.05,period_endpoint_transform_error=0))
        status('Two-frame native bell ring rendered for '+name+'; 20 fps matches the reference APNG timing')
    (QA/'bells_metadata.json').write_text(json.dumps(records,indent=2))
    sc=load();b.set_visibility('wc_dynamic');sc.cycles.samples=48;b.layer('wc_dynamic')
    cover=b.material('P10 occupancy face black',(.005,.009,.008),.5)
    b.box('P10 dynamic occupancy face',1.919,3.122,2.191,3.125,95,103,cover,.001)
    labels=[o for o in b.GROUPS['wc_dynamic'] if o.type=='FONT'];state_mat=bpy.data.materials['P10 independent WC state']
    bpy.context.view_layer.update();points=projected_bounds(b.GROUPS['wc_dynamic']);r=rect(points,5)
    parent=next(e for e in meta['production_occluders'] if e['name']=='restroom_entry_wall')
    from package_layers import tile_clips
    z=max(e['z_index'] for e in tile_clips(parent))+1
    states={};crop(sc,r,2);sc.render.use_compositing=False
    for name,text,color in [('vacant','VACANT',(.1,1,.25)),('occupied','OCCUPIED',(1,.035,.025))]:
        for ob in labels:ob.data.body=text;ob.data.size=.058 if name=='vacant' else .0435
        p=state_mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=2
        render(QA/('wc_'+name+'@2x.png'));states[name]=dict(file='wc_'+name+'.png',file_2x='wc_'+name+'@2x.png',x=r[0],y=r[1],w=r[2],h=r[3],z_index=z,alpha='straight',blend='source-over')
    (QA/'wc_indicator.json').write_text(json.dumps(states,indent=2));status('Vacant/occupied indicator states rendered on the new restroom wall with a shared native crop')

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
    if mode in ['all','doors']:doors()
    if mode in ['all','props']:bells_wc()
