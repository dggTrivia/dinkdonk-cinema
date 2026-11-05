"""Bounded, non-rendering integration checks on the smoke sprite and bus model."""
import sys,json,ast,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'bundle';sys.path.insert(0,str(ROOT))
import bpy,numpy as np
from runtime import rgba8,png,WORK,atomic_json
import package_layers as layers
import production,vehicles,video,validation
for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=p.name)
a=rgba8(WORK/'draft_cut_queue_front.png');a[a[:,:,3]==0,:3]=0;uv=np.load(WORK/'positions/fast27_ref_queue_front.npz')['uv'];out=WORK/'contract_fixture';out.mkdir(exist_ok=True);qa=out/'qa';(qa/'positions').mkdir(parents=True,exist_ok=True)
for scale,suffix in [(1,''),(2,'@2x')]:
    aa=np.repeat(np.repeat(a,scale,axis=0),scale,axis=1);vv=np.repeat(np.repeat(uv,scale,axis=0),scale,axis=1);png(out/('occ_fixture'+suffix+'.png'),aa);np.savez_compressed(qa/'positions'/('fixture'+suffix+'.npz'),uv=vv)
    assert np.array_equal(rgba8(out/('occ_fixture'+suffix+'.png')),aa),'PNG roundtrip changed pixels'
spec=next(e for e in json.loads((ROOT/'production.json').read_text())['groups'] if e['name']=='queue_front')
e=dict(name='fixture',x=0,y=0,w=a.shape[1],h=a.shape[0],file='occ_fixture.png',footprint=spec['footprint'],height_px=spec['height_px']);layers.OUT=out;layers.QA=qa;slices=layers.depth_slices([e]);errors=[]
for scale,suffix in [(1,''),(2,'@2x')]:
    source=rgba8(out/('occ_fixture'+suffix+'.png'));recon=np.zeros_like(source,np.uint16)
    for piece in slices:
        b=rgba8(out/(piece['file'][:-4]+suffix+'.png'));x=piece['x']*scale;y=piece['y']*scale;recon[y:y+b.shape[0],x:x+b.shape[1]]+=b
    error=int(np.abs(source.astype(np.int32)-recon).max());assert error==0;errors.append(error)
# Exercise the production geometry builder, without any render call.
from common import setup
import build_scene as b
import build_vehicles as v
bus=[]
for opened in [False,True]:
    sc=setup();b.GROUPS.clear();b.META.clear();b.layer('vehicle');b.FONT=bpy.data.fonts.load(str(ROOT/'assets/fonts/arialbd.ttf'));v.palette('bus');vehicles.build_model(opened)
    labels=[o.data.body for o in sc.objects if o.type=='FONT'];assert labels.count('05 DINK DONK')==2 and labels.count('d.gg TRANSIT')==2 and 'DGG 05' in labels
    assert sum(o.name.startswith('Bus side advertisement frame') for o in sc.objects)==2
    arts=[o for o in sc.objects if o.get('approved_meme') in ['boxing','courier']]
    assert len(arts)==4 and all(len(o.data.uv_layers)==1 for o in arts)
    for o in arts:assert any(n.type=='TEX_IMAGE' and n.image and n.image.size[0]>0 for n in o.data.materials[0].node_tree.nodes)
    # Exercise the production helper setup without capturing a frame.
    from runtime import Renderer,sha
    r=Renderer.__new__(Renderer);r.sc=sc;r.original={o.name:list(o.data.materials) for o in sc.objects if o.type in ['MESH','CURVE','FONT']};r.visible={o.name:(o.visible_camera,o.hide_render,o.is_holdout) for o in sc.objects if o.name in r.original};r.masks={};r.wet=set();r.rain=[]
    for o in sc.objects:
        if o.name in r.original:o['cloud_group']='vehicle'
    r.visibility('vehicle');assert all(o.visible_camera for o in arts)
    bus.append({'open':opened,'labels':labels,'objects':len(sc.objects),'approved_bus_art_panels':len(arts)})
report={'passed':True,'python_modules_parsed':len(list(ROOT.glob('*.py'))),'smoke_sprite_png_roundtrip':'exact','depth_slice_fixture_max_error':errors,'depth_slice_fixture_pieces':len(slices),'fixture_2x_note':'Repeated smoke pixels test packaging only; not a native 4K render claim.','bus_geometry':bus,'additional_3d_renders':0}
atomic_json(ROOT/'contract_checks.json',report);print(json.dumps(report),flush=True)
