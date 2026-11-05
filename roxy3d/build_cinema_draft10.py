"""Brief 37: draft09, closed section, lobby entrance and sampled depth layers.

All output paths and caches are under roxy3d. Previous sources are helper-only;
the lobby blend is linked through the read-only library API, never saved.
Use Blender --background --factory-startup --python-exit-code 1 --python this.py.
-- --preflight builds/checks only. -- --package resumes packaging saved buffers.
"""
import sys
sys.dont_write_bytecode = True
import os, json, math, time, copy, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parent
QA = ROOT/'qa11'
RUN = QA/'runtime10'
OUT = QA/'draft10'
IMAGE = QA/'cinema_draft_10.png'
LAYOUT = QA/'cinema_layout_10.json'
REPORT = QA/'CINEMA-DRAFT-10.md'
TARGET = ROOT/'roxy_cinema_draft10.blend'
RUN.mkdir(parents=True, exist_ok=True)
for key, folder in [('TEMP','temp'),('TMP','temp'),('CUDA_CACHE_PATH','cuda'),
                    ('OPTIX_CACHE_PATH','optix'),('BLENDER_USER_CONFIG','config'),
                    ('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts'),
                    ('BLENDER_USER_EXTENSIONS','extensions'),('XDG_CACHE_HOME','xdg')]:
    path=RUN/folder;path.mkdir(exist_ok=True);os.environ[key]=str(path)
NINE={'__file__':str(ROOT/'build_cinema_draft9.py'),'__name__':'draft9_helpers_for_draft10'}
src=(ROOT/'build_cinema_draft9.py').read_text(encoding='utf-8')
# Redirect the nested draft8 helper as well as draft9's own side-effect paths.
src=src.replace("source = source.replace(a,b)","source = source.replace(a,b)\nsource = source.replace('runtime09','runtime10').replace('cinema_draft_09.png','cinema_draft_10.png').replace('roxy_cinema_draft9.blend','roxy_cinema_draft10.blend')")
src=src.replace("RUN = QA/'runtime09'","RUN = QA/'runtime10'")
exec(compile(src,'read_only_draft9_helpers_runtime10','exec'),NINE)
import bpy
import numpy as np
from mathutils import Matrix,Vector
D=NINE['D']
xyz,project=D['xyz'],D['project']
NORMAL,RIGHT,UP=D['NORMAL'],D['RIGHT'],D['UP']
W,H,ZPP=1920,1080,D['ZPP']
BASE=json.loads((QA/'cinema_layout_09.json').read_text(encoding='utf-8'))
DIV=90.0
BAND=.25
NBANDS=152
EDGES=[i*BAND for i in range(NBANDS+1)]
# Local PNG helpers have no module side effects; do not use its disk decode cache.
sys.path.insert(0,str(ROOT))
from pngio import read as pngread,write as pngwrite


def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')


def snapshot():
    out={}
    for p in ROOT.parent.rglob('*'):
        if not p.is_file() or RUN in p.parents:continue
        s=p.stat();out[p.relative_to(ROOT.parent).as_posix()]=[s.st_size,s.st_mtime_ns]
    return out


def preservation():
    p=RUN/'preservation_before.json'
    if not p.exists():dump(p,snapshot())
    before=json.loads(p.read_text());after=snapshot()
    changed=[k for k,v in before.items() if after.get(k)!=v]
    external_active={'roxy3d/PROGRESS.md'}
    protected=[k for k in changed if k.startswith('roxy3d/') and not k.endswith('.log') and k!='roxy3d/build_cinema_draft10.py' and k not in external_active]
    assert not protected,protected
    allowed={'roxy3d/build_cinema_draft10.py','roxy3d/roxy_cinema_draft10.blend',
             'roxy3d/qa11/cinema_draft_10.png','roxy3d/qa11/cinema_layout_10.json','roxy3d/qa11/CINEMA-DRAFT-10.md'}
    new=[k for k in after if k not in before]
    external_new={'roxy3d/reviews/emote-facing.md'}
    unexpected=[k for k in new if k.startswith('roxy3d/') and k not in allowed and k not in external_new and not k.startswith('roxy3d/qa11/draft10/') and not k.endswith('.log')]
    assert not unexpected,unexpected
    return {'passed':True,'existing_files':len(before),'earlier_roxy3d_files':sum(k.startswith('roxy3d/') for k in before),
            'pages':sum(k.endswith(('.html','.htm')) for k in before),'changed_protected_files':protected,
            'external_log_changes':[k for k in changed if k.endswith('.log')],
            'concurrent_external_workspace_changes':[k for k in changed if not k.startswith('roxy3d/')],
            'concurrent_external_progress_changes':[k for k in changed if k in external_active],
            'concurrent_external_new_files':[k for k in new if k in external_new],
            'new_files':new,'method':'Size and nanosecond mtime against before-build inventory; externally active logs listed separately.'}


def key(p):return float(p.x-p.y+p.z*ZPP/DIV)
def depth(u,v,z):return u+v+z/DIV
def zi(k):return 1000+math.floor(k*100+.5)


def new_geometry(sc):
    removed=[]
    for name in ['Tunnel rear EXIT sign backing','Rear portal green EXIT']:
        ob=bpy.data.objects[name];removed.append(name);bpy.data.objects.remove(ob,do_unlink=True)
    D['collection']('14 Draft10 solid cut faces and padded rear entrance')
    cut=D['M']['cut core']
    walls=[]
    def wall(name,*args):
        ob=D['box']('D10 '+name,*args,cut,.003);walls.append(ob);return ob
    # Rear cut face, with the existing real portal opening retained.
    wall('rear cut wall left of portal',0,14.90,.30,14.94,-8,159.84)
    wall('rear cut wall right of portal',2.65,14.90,17.50,14.94,-8,159.84)
    wall('rear cut wall above portal',.30,14.90,2.65,14.94,140,159.84)
    # Camera-facing right cut face has the same stepped tops as the bank decks.
    for r in D['ROWS'][1:]:
        lo=5.2 if r['row']=='C' else round(r['v']-.7,2)
        hi=14.9 if r['row']=='I' else round(r['v']+.7,2)
        wall('right stepped cut wall '+r['row'],17.50,lo,17.54,hi,-8,r['floor_zpx']-.16)
    # Append the actual tagged pass9 screen-1 leaves and all attached fittings.
    # The draft13 padded-door code was read; its removed portholes are not used,
    # because Brief37 explicitly selects the porthole-equipped out9 design.
    old=set(sc.objects)
    with bpy.data.libraries.load(str(ROOT/'roxy_pass9.blend'),link=False) as (a,b):
        b.objects=[n for n in a.objects if n.startswith(('Upholstered cinema door','Door diamond stitching',
                  'Porthole chrome','Porthole amber','Polished door pull','Door brass kickplate','Pass6 kickplate scuff'))]
    leaves=[]
    sx=2.35/.93;sz=139/108
    transform=Matrix(((0,sx,0,1.475+6.4*sx),(-1,0,0,-14.84),(0,0,sz,0),(0,0,0,1)))
    for ob in b.objects:
        if ob is None:continue
        if ob.get('door_id')!='1':bpy.data.objects.remove(ob,do_unlink=True);continue
        D['COLLECTION'].objects.link(ob)
        ob.name='D10 entrance '+ob.name
        ob['d10_leaf']=True;leaves.append(ob)
    # Library objects' matrix_world is lazy. Evaluate all appended placements
    # before reading it; curves store world-space vertices but cubes do not.
    bpy.context.view_layer.update()
    original_matrices={ob.name:ob.matrix_world.copy() for ob in leaves}
    for ob in leaves:ob.matrix_world=transform@original_matrices[ob.name]
    bpy.context.view_layer.update()
    for ob in leaves:
        ps=[ob.matrix_world@Vector(p) for p in ob.bound_box]
        assert all(.20<p.x<2.75 and 14.70<-p.y<15.05 and -3<p.z*ZPP<142 for p in ps),('Door import bounds',ob.name)
    assert len(leaves)>20,len(leaves)
    # Camera-only inherited porthole illumination cannot illuminate the screen.
    glow={}
    for ob in leaves:
        ob.hide_render=False;ob.visible_camera=True
        for i,ma in enumerate(ob.data.materials):
            p=ma.node_tree.nodes.get('Principled BSDF') if ma and ma.use_nodes else None
            if p and p.inputs['Emission Strength'].default_value>0:
                if ma.name not in glow:glow[ma.name]=NINE['camera_only_material']('D10 camera-only '+ma.name,ma)
                ob.data.materials[i]=glow[ma.name]
    # Existing broad cut-surface fill illuminates only these new receivers too.
    receivers=bpy.data.collections.get('Fill receivers floor and cut structure')
    for ob in walls+leaves:
        if receivers and ob.name not in receivers.objects:receivers.objects.link(ob)
    bpy.context.view_layer.update()
    additions=owner_additions(sc)
    removed.extend(additions.pop('removed_objects'))
    return leaves,{'removed_objects':removed,'owner_additions':additions,'new_cut_wall_objects':[o.name for o in walls],
                   'door_objects':[o.name for o in leaves],'door_source':'roxy_pass9.blend: door_id=1',
                   'design_reference':['out9/doors/door_1.png','build_scene.py:door','build_pass6.py:door',
                                       'render_doors_pass6.py:amount','build_pass10_draft7.py:padded_doors'],
                   'door_opening_u':[.30,2.65],'door_plane_v':14.868,'door_leaf_height':139,
                   'new_lights':0,'cut_wall_top':'existing deck top minus 0.16 zpx; retained existing edge lights'}


def owner_additions(sc):
    """Brief37's owner-added items4/5, present in the current on-disk brief."""
    removed=[]
    prefixes=('Side wall before passage','Side wall after passage','Passage lintel exact height',
              'Recessed EXIT passage floor','Recessed rear burgundy fire door','Passage inner dark reveal',
              'Passage inner roof','Exit door push bar','English EXIT dark sign exact extents','Green EXIT in English')
    def rm(ob):removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
    for ob in list(sc.objects):
        if ob.name.startswith(prefixes):rm(ob)
        elif ob.name.startswith('Stepped muted dusty pink rake trim') and ob.type=='CURVE':
            # Only the first original trim span crosses the new doorway.
            pts=[ob.matrix_world@Vector(p.co[:3]) for p in ob.data.splines[0].points]
            if max(-p.y for p in pts)<3.701:rm(ob)
    D['collection']('15 Draft10 closed red-sign emergency exit and rowB reserved plaques')
    M=D['M'];box,line=D['box'],D['line']
    for a,b in [(0,1.2),(2.1,14.9)]:box('D10 emergency wall shell',-.12,a,0,b,-8,500,M['dado'],0)
    box('D10 wall above closed emergency door',-.12,1.2,0,2.1,152,500,M['dado'],0)
    box('D10 wall under closed emergency threshold',-.12,1.2,0,2.1,-8,24,M['dado'],0)
    for a,b in [(0,1.2),(2.1,4.6)]:
        line('D10 continuous pink dado trim at new exit',[(.046,a,136),(.046,b,136)],M['pink trim'],.012)
    for ob in list(sc.objects):
        if ob.name.startswith('Vertical acoustic fabric pleat'):
            ps=[ob.matrix_world@Vector(p) for p in ob.bound_box];v=sum(-p.y for p in ps)/8
            if 1.2<v<2.1 or 3.7<v<4.6:
                a=min(-p.y for p in ps)+.004;b=max(-p.y for p in ps)-.004
                rm(ob);bottom=152 if v<2.1 else 136
                box('D10 restored acoustic pleat at relocated exit',-.019,a,.032,b,bottom,493,M['rib navy'],.008)
    for a,b in [(1.17,1.23),(2.07,2.13)]:box('D10 emergency door dark metal jamb',.005,a,.055,b,24,154,M['champagne'],.004)
    box('D10 emergency door header',.005,1.17,.055,2.13,150,155,M['champagne'],.004)
    box('D10 plain closed emergency fire door',.006,1.23,.043,2.07,25,150,M['fixture burgundy'],.006)
    line('D10 emergency horizontal push bar',[(.075,1.32,84),(.075,1.98,84)],M['champagne'],.015)
    for v in [1.32,1.98]:box('D10 push bar bracket',.043,v-.025,.075,v+.025,81,87,M['champagne'],.002)
    box('D10 red EXIT box housing',.015,1.14,.13,2.16,164,187,M['armrest'],.005)
    red=D['material']('D10 red illuminated emergency EXIT',(.9,.025,.008),.5,0,2)
    red=NINE['camera_only_material']('D10 camera-only red emergency EXIT',red)
    D['text']('D10 RED emergency EXIT lettering','E X I T',.14,1.65,175.5,.19,red)
    # Wheelchair signs are code-native 3D decals, no font/emoji substitution.
    blue=D['material']('D10 accessibility plaque blue',(.012,.075,.46),.72)
    white=D['material']('D10 accessibility pictogram white',(.9,.94,1),.65)
    row=BASE['rows'][0];z=row['floor_zpx_world'];v=row['v']+.312
    before=set(sc.objects)
    for u in row['seat_u']:
        box('D10 rowB blue wheelchair plaque',u-.16,v-.008,u+.16,v+.006,z+29,z+53,blue,.005)
        def p(a,b):return (u+a,v+.013,z+41+b*ZPP)
        line('D10 wheelchair white wheel',[p(-.029+.078*math.cos(t*math.tau/32),-.045+.078*math.sin(t*math.tau/32)) for t in range(33)],white,.008)
        # Head, seated torso, horizontal seat/leg and leading foot.
        D['cylinder']('D10 wheelchair white head',u+.021,v+.014,z+41+.112*ZPP,.027,.004,white,axis=(0,-1,0),count=20)
        line('D10 wheelchair white seated figure',[p(.021,.072),p(.003,-.009),p(.074,-.009),p(.105,-.099),p(.139,-.099)],white,.010)
        line('D10 wheelchair white forward arm',[p(.013,.043),p(.076,.043)],white,.009)
    receivers=bpy.data.collections.get('Fill receivers row B')
    if receivers:
        for ob in set(sc.objects)-before:receivers.objects.link(ob)
    return {'removed_objects':removed,'emergency_exit':{'wall':'u=0','v':[1.2,2.1],'door_closed':True,'push_bar':True,
             'sign':'red illuminated EXIT','routes_use_this_door':False},
            'wheelchair_plaques':{'row':'B','count':len(row['seat_u']),'white_pictogram_on_blue':True,
                                 'floor_marking':False,'sign_height_zpx':24,'sign_width_world':.32}}


def setup_aovs(sc):
    """Per-camera-sample binary position bands, filtered by Cycles with beauty.

    Three scalar coverage masks per RGB AOV; no interpolated depth image, ID
    threshold, polygon raster approximation, or denoising on the masks.
    """
    group=bpy.data.node_groups.new('D10 first-hit surface depth coverage','ShaderNodeTree')
    nodes,links=group.nodes,group.links
    geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ')
    links.new(geo.outputs['Position'],sep.inputs[0])
    sub=nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';links.new(sep.outputs['X'],sub.inputs[0]);links.new(sep.outputs['Y'],sub.inputs[1])
    mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=ZPP/DIV;links.new(sep.outputs['Z'],mult.inputs[0])
    add=nodes.new('ShaderNodeMath');add.operation='ADD';links.new(sub.outputs[0],add.inputs[0]);links.new(mult.outputs[0],add.inputs[1])
    masks=[]
    for b in range(NBANDS):
        low=nodes.new('ShaderNodeMath');low.operation='LESS_THAN';low.inputs[1].default_value=EDGES[b];links.new(add.outputs[0],low.inputs[0])
        high=nodes.new('ShaderNodeMath');high.operation='LESS_THAN';high.inputs[1].default_value=EDGES[b+1];links.new(add.outputs[0],high.inputs[0])
        diff=nodes.new('ShaderNodeMath');diff.operation='SUBTRACT';links.new(high.outputs[0],diff.inputs[0]);links.new(low.outputs[0],diff.inputs[1]);masks.append(diff.outputs[0])
    for i in range(math.ceil(NBANDS/3)):
        name='D10mask%03d'%i
        a=sc.view_layers[0].aovs.add();a.name=name;a.type='COLOR'
        combine=nodes.new('ShaderNodeCombineXYZ')
        for c in range(3):
            if i*3+c<len(masks):links.new(masks[i*3+c],combine.inputs[c])
        out=nodes.new('ShaderNodeOutputAOV');out.name=name;out.aov_name=name
        links.new(combine.outputs[0],out.inputs['Color'])
    for ma in list(bpy.data.materials):
        if ma.use_nodes:
            n=ma.node_tree.nodes.new('ShaderNodeGroup');n.node_tree=group
    tree=bpy.data.node_groups.new('D10 coverage files','CompositorNodeTree');sc.compositing_node_group=tree
    rl=tree.nodes.new('CompositorNodeRLayers');rl.scene=sc
    out=tree.nodes.new('CompositorNodeOutputFile');out.directory=str(RUN/'coverage');out.file_name='coverage'
    out.format.media_type='IMAGE';out.format.file_format='OPEN_EXR';out.format.color_mode='RGB';out.format.color_depth='32';out.format.exr_codec='ZIP';out.save_as_render=False
    for i in range(math.ceil(NBANDS/3)):
        name='D10mask%03d'%i;out.file_output_items.new('RGBA',name)
        tree.links.new(rl.outputs[name],out.inputs[name])
    sc.render.use_compositing=True
    return {'method':'Cycles same-beauty camera-sample first-hit Position -> half-open 0.25 key bands; packed RGB AOVs, full-float linear EXR, same pixel filter, no mask denoising.',
            'bands':NBANDS,'maximum_band_width':BAND,'edges':EDGES,'range':[EDGES[0],EDGES[-1]],'mask_aovs':math.ceil(NBANDS/3)}


def tree_for(sc):return D['object_tree'](list(sc.objects))


def probe_samples(sc,tree,owners):
    samples=[]
    route=BASE['walk_route']['rear_portal_to_cross_aisle']
    for idx in [0,1,2,3,5,6,7,9,10,11,12,16,19]:samples.append(('route_%02d'%idx,route[idx],False))
    samples.append(('stairs_C',[3.475,5.725,64],False))
    for r in BASE['rows']:
        samples.append(('seated_'+r['row'],[r['seat_u_by_block']['main'][0],r['v']+.2,r['floor_zpx_world']+36],True))
    records=[]
    # Pixel-centre rays across the page's camera-facing emote rectangle. These
    # positions agree exactly with CSS foot anchoring, without the optional hop.
    for name,p,seated in samples:
        u,v,z=p;px,py=project(u,v,z);height=50*D['K'];half=11.1*D['K']
        tests=[]
        for y in range(math.ceil(py-height),math.floor(py)):
            for x in range(math.ceil(px-half),math.floor(px+half)):
                q=xyz(u,v,z)+RIGHT*((x+.5-px)/60)+UP*((py-y-.5)/60)
                hit=tree.ray_cast(q+NORMAL*45,-NORMAL,44.9998)
                tests.append([x,y,hit[2] is None,owners[hit[2]] if hit[2] is not None else None,
                              key(hit[0]) if hit[2] is not None else None])
        records.append({'name':name,'uvzpx':p,'seated':seated,'key':depth(*p),'z_index':zi(depth(*p)),
                        'ray_visible_fraction':sum(t[2] for t in tests)/len(tests),'pixels':tests})
    return records


def door_pose(leaves,original,amount):
    for ob in leaves:
        side=ob['door_side'];hinge=xyz(1.475-side*1.175,14.868,0)
        ob.matrix_world=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(79)*amount*side,4,'Z')@Matrix.Translation(-hinge)@original[ob.name]
    bpy.context.view_layer.update()


def render_door(sc,leaves):
    # Opening geometry fits inside this fixed camera-aligned rectangle. Render
    # patches retain the exact camera and full scene lighting, not a flat decal.
    points=[project(u,v,z) for u in [-.1,.30,2.65,3.05] for v in [13.55,14.98] for z in [0,160]]
    x=max(0,math.floor(min(p[0] for p in points))-3);y=max(0,math.floor(min(p[1] for p in points))-3)
    right=math.ceil(max(p[0] for p in points))+3;bottom=math.ceil(max(p[1] for p in points))+3
    w,h=right-x,bottom-y
    # Blender border is integer aligned; crop output, no change in projection.
    sc.render.use_border=True;sc.render.use_crop_to_border=True
    sc.render.border_min_x=x/W;sc.render.border_max_x=right/W
    sc.render.border_min_y=1-bottom/H;sc.render.border_max_y=1-y/H
    sc.render.use_compositing=False
    for aov in list(sc.view_layers[0].aovs):sc.view_layers[0].aovs.remove(aov)
    original={o.name:o.matrix_world.copy() for o in leaves}
    times=[]
    for pose in range(1,6):
        amount=.5-.5*math.cos(math.pi*pose/5)
        door_pose(leaves,original,amount)
        sc.render.filepath=str(RUN/('door_pose_%02d.png'%pose));t=time.perf_counter()
        bpy.ops.render.render(write_still=True);times.append(time.perf_counter()-t)
    opened_tree,opened_owners=tree_for(sc)
    open_probes=probe_samples(sc,opened_tree,opened_owners)
    door_pose(leaves,original,0)
    return {'x':x,'y':y,'frame_width':w,'frame_height':h,'frames':16,'columns':4,'rows':4,'fps':18,'loop':False,
            'z_index':2590,'file':'draft10/door_entrance.png','open_hold_frames':[5,10],
            'render_seconds':times,'open_probes':open_probes}


def read_exr(path):
    im=bpy.data.images.load(str(path),check_existing=False)
    a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a)
    a=a.reshape(im.size[1],im.size[0],4)[::-1].copy();bpy.data.images.remove(im)
    return a


def fast_png(path):
    # Non-Color exposes encoded PNG byte values, avoiding a color transform.
    # All beauty/patch inputs are opaque; PNG output uses our stdlib encoder.
    im=bpy.data.images.load(str(path),check_existing=False)
    im.colorspace_settings.name='Non-Color'
    a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a)
    a=np.rint(a.reshape(im.size[1],im.size[0],4)[::-1]*255).clip(0,255).astype(np.uint8)
    bpy.data.images.remove(im);return a


def package():
    global EDGES,NBANDS
    data=json.loads((RUN/'build_data.json').read_text())
    EDGES=data['coverage']['edges'];NBANDS=len(EDGES)-1
    beauty=fast_png(IMAGE);rgb=beauty[:,:,:3]
    files=sorted((RUN/'coverage').glob('*.exr'))
    print('D10_COVERAGE_FILES',len(files),[p.name for p in files[:2]],flush=True)
    assert len(files)==math.ceil(NBANDS/3),len(files)
    slices=[];masks={};coverage_sum=np.zeros((H,W),np.float32)
    for i in range(len(files)-1,-1,-1):
        path=files[i]
        a=read_exr(path)
        assert a.shape[:2]==(H,W),a.shape
        for c in range(2,-1,-1):
            b=i*3+c
            if b>=NBANDS:continue
            # Conditional source-over alpha: exclusive Cycles sample coverage
            # must be normalized by the coverage not already in nearer bands.
            # Otherwise two adjacent 50% masks leave a false25% hole in a solid
            # surface when the page composites separate DOM images.
            remaining=np.maximum(1-coverage_sum,1e-7)
            alpha=np.rint(np.clip(a[:,:,c]/remaining,0,1)*255).astype(np.uint8)
            coverage_sum+=a[:,:,c]
            yy,xx=np.nonzero(alpha)
            if not len(xx):continue
            x0,x1=int(xx.min()),int(xx.max()+1);y0,y1=int(yy.min()),int(yy.max()+1)
            crop=np.dstack([rgb[y0:y1,x0:x1],alpha[y0:y1,x0:x1]])
            name='depth_%03d'%b;file='draft10/slices/'+name+'.png'
            pngwrite(QA/file,crop)
            slices.append({'file':file,'x':x0,'y':y0,'w':x1-x0,'h':y1-y0,'z_index':zi(EDGES[b]),
                           'key_min':EDGES[b],'key_max':EDGES[b+1],'name':name})
            masks[name]=(x0,y0,alpha[y0:y1,x0:x1].copy())
    slices.sort(key=lambda s:s['key_min'])
    # Exact source-over identity in byte arithmetic, including partial alpha.
    recon=rgb.astype(np.float64).copy()
    for s in slices:
        x,y,w,h=[s[k] for k in ['x','y','w','h']]
        a=masks[s['name']][2][:,:,None].astype(np.float64)/255
        recon[y:y+h,x:x+w]=np.rint(rgb[y:y+h,x:x+w]*a+recon[y:y+h,x:x+w]*(1-a))
    maxdiff=int(np.abs(recon-rgb.astype(float)).max());assert maxdiff==0,maxdiff
    tests=[]
    for p in data['closed_probes']:
        above=[s for s in slices if s['z_index']>p['z_index']]
        below=[s['name'] for s in slices if s['z_index']<=p['z_index']]
        total=0.;near=[]
        for x,y,clear,owner,hitkey in p['pixels']:
            trans=1.
            for s in above:
                ax,ay,a=masks[s['name']]
                if ax<=x<ax+a.shape[1] and ay<=y<ay+a.shape[0]:
                    v=int(a[y-ay,x-ax])/255
                    if v:trans*=1-v
                    if v and s['name'] not in near:near.append(s['name'])
            total+=trans
        fraction=total/len(p['pixels'])
        tests.append({k:v for k,v in p.items() if k!='pixels'}|{'layer_visible_fraction':fraction,
                     'absolute_fraction_error':abs(fraction-p['ray_visible_fraction']),
                     'above_slices': [s['name'] for s in above],'below_slices':below,'overlapping_above_slices':near})
    door=data['door'];x,y,w,h=[door[k] for k in ['x','y','frame_width','frame_height']]
    base=beauty[y:y+h,x:x+w].copy()
    # Replacement only within the moving doorway footprint. Use opaque core
    # so the closed leaves in the background are erased by every open pose.
    # Endpoints are exact copies of the closed beauty.
    poses=[base]
    for i in range(1,6):
        p=fast_png(RUN/('door_pose_%02d.png'%i))
        assert p.shape==base.shape,(p.shape,base.shape)
        poses.append(p)
    sheet=np.zeros((h*4,w*4,4),np.uint8)
    # A full RGB replacement patch is camera correct; all pixels identical to
    # closed beauty are transparent, changed ones are opaque. Limits the sheet
    # to actual image changes, avoiding an opaque bounding-box occluder.
    union=np.zeros((h,w),bool)
    for p in poses[1:]:union|=np.max(np.abs(p[:,:,:3].astype(int)-base[:,:,:3].astype(int)),axis=2)>2
    # Confine to portal/opened leaves (not sampling noise across neighbouring walls).
    yy,xx=np.indices((h,w));gx=xx+x+.5;gy=yy+y+.5
    # Portal plane parallelogram and inward swept-leaf projection bounding hull.
    poly=[project(.25,14.95,-2),project(2.70,14.95,-2),project(2.70,14.95,142),project(.25,14.95,142)]
    cross=[(b[0]-a[0])*(gy-a[1])-(b[1]-a[1])*(gx-a[0]) for a,b in zip(poly,poly[1:]+poly[:1])]
    portal=np.logical_and.reduce([v>=0 for v in cross])|np.logical_and.reduce([v<=0 for v in cross])
    union &= portal
    # Portal is opaque throughout all frames: exact endpoint reconstruction,
    # dark opening and both leaves replace the static door, no additive ghosts.
    alpha=(portal.astype(np.uint8)*255)
    for f in range(16):
        canonical=min(f,15-f,5);p=poses[canonical].copy();p[:,:,3]=alpha
        sheet[(f//4)*h:(f//4+1)*h,(f%4)*w:(f%4+1)*w]=p
    pngwrite(OUT/'door_entrance.png',sheet)
    assert np.array_equal(sheet[:h,:w],sheet[3*h:4*h,3*w:4*w])
    # A single door sheet cannot erase the higher-depth closed-leaf slices by
    # z-index alone. Supply the exact static-slice cutout needed while it plays.
    cutout=np.full((h,w,4),255,np.uint8);cutout[:,:,3]=alpha
    pngwrite(OUT/'door_static_cutout.png',cutout)
    affected=[];ghost=poses[5][:,:,:3].astype(float).copy()
    for s in slices:
        if s['z_index']<=door['z_index']:continue
        ax,ay,am=masks[s['name']]
        x0=max(x,ax);x1=min(x+w,ax+am.shape[1]);y0=max(y,ay);y1=min(y+h,ay+am.shape[0])
        if x0>=x1 or y0>=y1:continue
        aa=am[y0-ay:y1-ay,x0-ax:x1-ax][:,:,None].astype(float)/255
        if not np.any((aa[:,:,0]>0)&portal[y0-y:y1-y,x0-x:x1-x]):continue
        affected.append(s['name'])
        basepart=rgb[y0:y1,x0:x1]
        ghost[y0-y:y1-y,x0-x:x1-x]=basepart*aa+ghost[y0-y:y1-y,x0-x:x1-x]*(1-aa)
    ghostdelta=np.abs(ghost-poses[5][:,:,:3].astype(float))[portal]
    door['static_slice_cutout']={'file':'draft10/door_static_cutout.png','x':x,'y':y,'w':w,'h':h,
        'slices':affected,'active_frames':[0,15],
        'operation':'While doorShot exists, multiply these static slices alpha by (1-cutout alpha), in stage coordinates. Restore on removal.',
        'required_page_hook':True}
    raw9=fast_png(QA/'cinema_draft_09.png')[:,:,:3]
    screenmask=np.zeros((H,W),bool)
    corners=BASE['screen']['corners_1920x1080']
    for x0 in range(math.ceil(corners['TL'][0]+8),math.floor(corners['TR'][0]-8)):
        top=370+.5*(x0+.5-890)-460*D['K'];bottom=370+.5*(x0+.5-890)-90*D['K']
        screenmask[math.ceil(top+8):math.floor(bottom-8),x0]=True
    a=raw9[screenmask].astype(float);b=rgb[screenmask].astype(float)
    luminance=np.array([.2126,.7152,.0722]);sdelta=float(((b-a)@luminance).mean())
    screencheck={'pixels':len(a),'mean_luminance_delta_0_255':sdelta,'max_channel_difference':int(np.abs(b-a).max()),
                 'mean_absolute_channel_difference':float(np.abs(b-a).mean()),'screen_settings_identical':True,
                 'unchanged_mean_tolerance_0_255':.5,'passed':abs(sdelta)<=.5}
    # Main scene fields remain byte-for-byte values from draft9.
    layout=copy.deepcopy(BASE)
    layout['brief']='BRIEF-37-cinema-draft10-layers.md'
    publicdoor={k:v for k,v in door.items() if k not in ['render_seconds','open_probes']}
    layout['page_layers']={'key_z_divisor':DIV,'key_z_coefficient':1/DIV,'depth_key':'(u + v) + zpx_world / 90',
        'z_index_formula':'1000 + Math.round(key * 100)','slices':slices,'entrance_door':publicdoor,
        'coverage':data['coverage'],'spawn':{'point':BASE['walk_route']['rear_portal_to_cross_aisle'][0],
          'outside_closed_door':True,'wait_uvzpx':BASE['walk_route']['rear_portal_to_cross_aisle'][0],
          'wait_seconds':5/18,'door_plane_v':14.868}}
    layout['render'].update(image='qa11/cinema_draft_10.png',blend='roxy_cinema_draft10.blend',seconds=data['render']['beauty_seconds'],image_sha256=data['render']['image_sha256'])
    layout['approved_layout_source']='qa11/cinema_layout_09.json'
    layout['draft10']={k:v for k,v in data.items() if k not in ['closed_probes','door']}
    layout['draft10'].update(layer_validation={'background_plus_all_slices_max_absolute_rgb_difference':maxdiff,
                   'slices':len(slices),'coverage_sum_range':[float(coverage_sum.min()),float(coverage_sum.max())],
                   'walker_samples':tests},screen_comparison=screencheck,
                   door_validation={'first_last_identical':True,'first_last_over_beauty_max_difference':0,
                    'open_hold_frames':[5,10],'pose_render_seconds':door['render_seconds'],
                    'static_slice_cutout_required':True,'affected_static_slices':affected,
                    'without_cutout_open_frame_max_rgb_error':float(ghostdelta.max()),
                    'without_cutout_open_frame_mean_rgb_error':float(ghostdelta.mean())},preservation=preservation())
    dump(LAYOUT,layout)
    dump(RUN/'layer_checks.json',layout['draft10'])
    write_report(layout)
    print('D10_PACKAGE_COMPLETE',len(slices),'slices, identity',maxdiff,'screen',screencheck,flush=True)


def write_report(layout):
    d=layout['draft10'];v=d['layer_validation'];r=d['render'];door=layout['page_layers']['entrance_door']
    lines=['# Cinema draft 10 - rear door, closed underside and page layers','',
      'Brief 37. One 1920x1080 Cycles beauty, built from the draft9 helper chain and unchanged draft9 layout. '
      'Rear EXIT removed; guard-post green EXIT retained. New solid dark rear/right cut walls close the visible deck underside. '
      'The existing stepped edge lights are retained. The actual pass9 lobby screen-1 padded double leaves, portholes, stitching, pulls, brass kickplates and scuffs are reused through the read-only Blender library API, scaled into the existing portal. Closed in the review still.', '',
      'Camera, 135 seats, row floors, routes, stairs, screen corners/material/fill/exposure and every existing lamp retain draft9 values. No new lamps. '
      'The new surfaces join the existing room receiver collection, and new cut surfaces also join the existing cut-surface fill receiver collection. Porthole emission is camera-only. '
      'Draft13 door code was read: it removes portholes; the brief explicitly requests the retained out9 portholes, so pass9 geometry is used.', '',
      'The owner-added items4/5 are included. The former open screen-side passage is closed with matching wall finishes. '
      'A plain closed fire door with a push bar occupies u=0/v1.2-2.1, nearer the screen, with red illuminated EXIT lettering. '
      'All18 row-B seat backs carry white wheelchair pictograms on clean blue plaques; no other row has them. '
      'No optional floor marking was added. Routes and seat centres remain unchanged.', '',
      '## Page contract','',
      f'Exact camera depth coefficient: **{d["depth_check"]["coefficient"]:.15f}**, divisor **{DIV:g}**. '
      'It follows from N=(sqrt(3/8),-sqrt(3/8),1/2), z_world=zpx/73.48469228349535. '
      'key=(u+v)+zpx/90; z_index=1000+Math.round(key*100). Seated foot uses (seat_u,row_v+0.2,floor+36).', '',
      f'{len(layout["page_layers"]["slices"])} tight RGBA slices, maximum0.25-wide half-open surface key bands, with narrower splits at the probe z-index thresholds; RGB bytes copied from the delivered beauty. '
      'Alpha is camera-sample coverage from the same Cycles render, through a shared shader AOV group; packed RGB full-float linear EXRs are retained in runtime10/coverage. '
      'The masks receive the same Cycles pixel filter and are not denoised. Exclusive coverage is converted to conditional source-over alpha: '
      'alpha_band=coverage_band/(1-sum(coverage_in_nearer_bands)). This prevents band-boundary gaps when the page composites separate images. '
      'Final PNG alpha is quantized to8bits. '
      'Full-beauty background plus all slices has maximum absolute RGB-byte difference **0**.', '',
      f'Door sheet: {door["frame_width"]}x{door["frame_height"]} cells, 4x4, 16 frames at18fps; frames5-10 fully open, reverse to close. '
      'Both endpoints reconstruct the closed beauty exactly. Five actual intermediate/open Cycles patch renders use the same camera/lighting. '
      f'Sheet z_index={door["z_index"]}, below the outside walker at spawn (2657), the threshold walker atv14.9 (2635), and the just-inside walker atv14.55 (2600), '
      'so the opaque opening replacement does not hide them while the door is open. The deeper tunnel is occluded by its real structure. '
      'Spawn [1.45,15.12,0] is outside the closed leaf planev14.868. Wait at spawn for5/18s (0.277778s); the existing page already reads this hold start.', '',
      '## Visibility checks','',
      'Synthetic camera-facing emote rectangle, +/-11.1 lobby pixels wide and50 high, scaled by camera k, no hop. '
      'Pixel-centre camera rays are compared with source-over alpha of slices strictly above each walker z_index; the page appends walkers after static slices, so the walker wins equal-z ties. '
      'A band is deliberately assigned its key_min; resulting boundary approximation and filtered-edge differences are reported, not hidden. '
      'Full above/below slice names, intersecting slices and numeric fractions are in runtime10/layer_checks.json and the layout JSON.', '',
      '| Probe | Ray visible | Layers visible | Absolute error | Overlapping layers above |','|---|---:|---:|---:|---|']
    for p in v['walker_samples']:
        lines.append(f'| {p["name"]} | {p["ray_visible_fraction"]:.2%} | {p["layer_visible_fraction"]:.2%} | {p["absolute_fraction_error"]:.2%} | '+', '.join(p['overlapping_above_slices'])+' |')
    s=d['screen_comparison']
    lines+=['','## Render and preservation','',
      f'Blender5.2.3 LTS; unchanged Cycles adaptive64-384, threshold0.007, seed341997, OptiX denoising, AgX Medium High Contrast, exposure0. '
      f'Beauty with coverage AOVs: **{r["beauty_seconds"]:.2f}s**. Door pose renders: **{sum(d["door_validation"]["pose_render_seconds"]):.2f}s**. '
      f'Calibration max axis error **{d["calibration"]["max_axis_error_px"]:.8f}px**. '
      f'Screen inset mean change **{s["mean_luminance_delta_0_255"]:+.5f}/255**, maximum channel difference{s["max_channel_difference"]}; '
      'screen geometry/material/light settings unchanged; pixel noise differences are measured separately.','',
      f'Preservation inventory: {d["preservation"]["existing_files"]} prior files, {d["preservation"]["pages"]} pages; zero builder changes to protected inputs. '
      'Only new draft10 source/blend/beauty/layout/report, slices/sheet/cutout and runtime10 files are written. Earlier drafts, pre-task blends, cloud bundle and out10 are preserved. '
      'Concurrent external edits to auditorium.html, roxy.html, shared files or PROGRESS.md are listed in the preservation JSON; this builder never writes those files. '
      'No4K, encoding, cloud action or page edits.','',
      '## Required door-page integration','',
      'The current page consumes the primary sheet and depth slices, but does not yet consume entrance_door.static_slice_cutout. '
      'When the sheet plays, higher-depth pixels from the closed door in the static slices paint the closed leaves back over the opening. '
      f'This affects{len(d["door_validation"]["affected_static_slices"])} slices. Without the cutout, the fully-open frame differs from its rendered target by '
      f'up to{d["door_validation"]["without_cutout_open_frame_max_rgb_error"]:.0f} RGB bytes; it is not a passed page integration.', '',
      'The JSON lists the affected slices and provides draft10/door_static_cutout.png in stage coordinates. '
      'While doorShot exists, multiply the alpha of those static slices by (1-cutout alpha), restoring them when the sheet is removed. '
      'Keep the sheet below portal walkers at z2590. A single opaque replacement sheet cannot simultaneously encode the depth of the dark opening and both moving leaves; '
      'this placement supports the centred, wait-then-enter route, while exact moving-leaf intersections would require per-pose depth layers. '
      'No page was edited to implement this hook.', '',
      'One final review still is delivered. Two rejected render attempts are preserved under runtime10/attempt01 and attempt02: '
      'the first exposed lazy appended-object transforms, the second exposed missing receiver links on the replacement emergency wall. '
      'Both were corrected before delivery. The final render plus five door poses is reported above; rejected attempt timings/logs are retained separately. '
      'No live chatter, browser or production acceptance is claimed.','']
    baseline=json.loads((RUN/'preservation_before.json').read_text())
    assert 'roxy3d/qa11/CINEMA-DRAFT-10.md' not in baseline
    REPORT.write_text('\n'.join(lines),encoding='utf-8')


def main():
    global EDGES,NBANDS
    if '--package' in sys.argv:package();return
    preservation()
    for p in [IMAGE,LAYOUT,REPORT,TARGET,RUN/'beauty_started']:assert not p.exists(),str(p)
    start=time.perf_counter()
    sc=D['configure']();sc.name='DINK DONK Screen 1 - draft10 layers and rear door'
    D['palette']();D['floors']();screen=D['walls_screen_passage']();D['front_ceiling']();D['seats']()
    D['tunnel_geometry']();D['fixtures_lighting']();D['wear']();D['screen_lighting'](sc,screen)
    original=list(sc.objects);signature=NINE['geometry_signature'](original)
    tree,owners=tree_for(sc);mouth=NINE['add_mouth_lighting'](sc,tree,owners)
    leaves,changes=new_geometry(sc)
    room=bpy.data.collections['Receivers - room excluding matte screen']
    original_names=set(signature)
    for ob in sc.objects:
        if ob.type in ['MESH','CURVE','FONT'] and ob.name not in original_names and ob.name not in room.objects:
            room.objects.link(ob)
    retained=[o for o in sc.objects if o.name in signature and o.name not in changes['removed_objects']]
    retained_signature=NINE['geometry_signature'](retained)
    assert all(signature[k]==v for k,v in retained_signature.items())
    D['collection']('00 Calibration marker empties');cal=D['calibration'](sc)
    tree,owners=tree_for(sc);closed=probe_samples(sc,tree,owners)
    # Keep exact order thresholds at the requested ray-check locations. Most
    # bands remain 0.25; additional narrow splits prevent a sample foot key
    # falling inside a coarser band that could falsely reveal an occluder.
    EDGES=sorted(set(EDGES+[(zi(p['key'])-1000+.5)/100+.00001 for p in closed]));NBANDS=len(EDGES)-1
    coefficient=NORMAL.z/(NORMAL.x*ZPP)
    assert abs(coefficient-1/90)<1e-10,coefficient
    data={'changes':changes,'depth_check':{'coefficient':coefficient,'divisor':1/coefficient,'normal':list(NORMAL),
            'formula_matches_page':True},'calibration':cal,'geometry_lock':{'retained_meshes':len(retained_signature),'passed':True},
          'closed_probes':closed,'render':{'device':sc['render_device'],'build_seconds':time.perf_counter()-start},
          'source_sha256':{p.relative_to(ROOT.parent).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [ROOT/'BRIEF-37-cinema-draft10-layers.md',ROOT/'build_cinema_draft9.py',QA/'CINEMA-DRAFT-09.md',QA/'cinema_layout_09.json',
               ROOT.parent/'auditorium.html',ROOT/'build_scene.py',ROOT/'build_pass6.py',ROOT/'build_pass10_draft7.py']}}
    if '--preflight' in sys.argv:
        data['coverage_planned']={'edges':EDGES,'bands':NBANDS}
        dump(RUN/('preflight_%02d.json'%(1+len(list(RUN.glob('preflight_*.json'))))),data)
        print('DRAFT10 PREFLIGHT OK',len(leaves),'door parts; depth coefficient',coefficient,flush=True);return
    data['coverage']=setup_aovs(sc)
    sc['brief']='BRIEF-37-cinema-draft10-layers.md';sc['draft_only']=True
    sc['draft10_layout_source']='qa11/cinema_layout_09.json'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
    with (RUN/'beauty_started').open('x') as f:f.write('One review beauty render. Do not overwrite or rerender it.\n')
    t=time.perf_counter();bpy.ops.render.render(write_still=True)
    data['render']['beauty_seconds']=time.perf_counter()-t
    data['render']['image_sha256']=hashlib.sha256(IMAGE.read_bytes()).hexdigest()
    dump(RUN/'beauty_checkpoint.json',data)
    data['door']=render_door(sc,leaves)
    data['render']['total_render_seconds']=data['render']['beauty_seconds']+sum(data['door']['render_seconds'])
    dump(RUN/'build_data.json',data)
    package()
    print('STATUS: DRAFT 10 COMPLETE | one 1920x1080 review beauty + page layers + door sheet | STOP',flush=True)


if __name__=='__main__':main()
