"""Local packaging only. Run in Blender; never renders or changes the draft."""
import sys,json,shutil,hashlib,re
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent;SRC=HERE.parent;DEST=HERE/'bundle'
DEST.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(DEST))
def copy(name):shutil.copy2(SRC/name,DEST/name)
for name in ['build_scene.py','build_vehicles.py','package_layers.py','depth_pass.py','package_vehicles.py','package_vehicle_pass5.py']:
    text=(SRC/name).read_text(encoding='utf-8')
    text=text.replace("bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')","bpy.data.fonts.load(str(ROOT/'assets/fonts/arialbd.ttf'))")
    if name=='build_vehicles.py':
        text=text.replace('ROXY TRANSIT','d.gg TRANSIT').replace('95 ROXY','05 DINK DONK').replace('RXY 95','DGG 05')
        text=text.replace("'95'","'05'").replace("'Roxy pink reflection'","'Current warm script reflection'").replace('100,(1,.09,.37)','100,(1,.27,.39)')
    (DEST/name).write_text(text,encoding='utf-8')
shutil.copytree(SRC/'out9',DEST/'reuse',dirs_exist_ok=True)
(DEST/'assets/fonts').mkdir(parents=True,exist_ok=True)
shutil.copy2(Path(bpy.utils.system_resource('DATAFILES')).parent.parent/'unused',DEST/'unused') if False else None
source=SRC/'roxy_pass10_draft.blend'
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
assert len([o for o in sc.objects if o.name.startswith('D13 marquee bulb ')])==74
assert len([o for o in sc.objects if o.name.startswith('D13 truss reflector flood ')])==3
for name in ['D10 stateless edge drips and impact crowns','D10 stateless gutter and AC pours']:
    sc.objects[name].cycles.use_motion_blur=False
fonts=[];images=[]
for font in bpy.data.fonts:
    if font.filepath=='<builtin>':continue
    p=Path(bpy.path.abspath(font.filepath));name=p.name
    dst=DEST/'assets/fonts'/name
    if font.packed_file:dst.write_bytes(font.packed_file.data)
    elif p.is_file():shutil.copy2(p,dst)
    else:raise RuntimeError('Missing font '+font.name)
    font.filepath=str(dst);fonts.append(name)
if not (DEST/'assets/fonts/arialbd.ttf').exists():raise RuntimeError('Required vehicle font missing')
for index,im in enumerate(bpy.data.images):
    if im.type in ['RENDER_RESULT','COMPOSITING'] or im.source in ['GENERATED','VIEWER']:continue
    original=Path(bpy.path.abspath(im.filepath));ext=original.suffix or '.png'
    name=str(index)+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',im.name)+ext
    dst=DEST/'assets/textures'/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if im.packed_file:dst.write_bytes(im.packed_file.data)
    elif original.is_file():shutil.copy2(original,dst)
    else:raise RuntimeError('Missing image '+im.name)
    im.filepath=str(dst);images.append(name)
for text in list(bpy.data.texts):bpy.data.texts.remove(text)
for lib in bpy.data.libraries:raise RuntimeError('Unpacked linked library '+lib.filepath)
# Current saved micro-impact vertices include the billboard moves and fixes.
# Derive canonical landing points from the equatorial vertices, instead of
# restoring obsolete coordinates from the original Draft 5 JSON.
sites=json.loads((SRC/'qa10/draft5/impact_sites.json').read_text(encoding='utf-8'))
ob=sc.objects['D5 periodic wet micro impacts']
if len(ob.data.vertices)!=len(sites)*6:raise RuntimeError('Impact topology mismatch')
for i,s in enumerate(sites):s['point']=list(sum((ob.matrix_world@ob.data.vertices[i*6+j].co for j in [1,2,3,4]),__import__('mathutils').Vector())/4)
(DEST/'assets/impact_sites.json').write_text(json.dumps(sites),encoding='utf-8')
old=json.loads((SRC/'out9/manifest.json').read_text(encoding='utf-8'))
meta=json.loads((SRC/'qa10/scene_metadata_final.json').read_text(encoding='utf-8'))
from prepare_scene import prepare
manifest,production=prepare(sc,old,meta)
(DEST/'manifest.template.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(DEST/'production.json').write_text(json.dumps(production,indent=2),encoding='utf-8')
bpy.ops.file.pack_all()
for font in bpy.data.fonts:
    if font.filepath!='<builtin>':font.filepath='//assets/fonts/'+Path(font.filepath).name
for im in bpy.data.images:
    if im.filepath and im.source not in ['GENERATED','VIEWER']:im.filepath='//assets/textures/'+Path(im.filepath).name
for im in bpy.data.images:
    if im.filepath and not im.filepath.startswith('//') and im.source not in ['GENERATED','VIEWER']:raise RuntimeError('Absolute image path '+im.name)
sc.render.filepath='//work/render.png'
for scene in bpy.data.scenes:
    if scene.compositing_node_group:
        for node in scene.compositing_node_group.nodes:
            if node.type=='OUTPUT_FILE':node.directory='//work/compositor'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'scene.blend'),relative_remap=False)
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
shutil.copy2(SRC.parent/'tools/blender-5.2.3.sha256',DEST/'blender-5.2.3.sha256')
(DEST/'bundle.json').write_text(json.dumps({'schema':1,'scene_source':'approved Draft 13','source_sha256':source_sha,'scene_sha256':hashlib.sha256((DEST/'scene.blend').read_bytes()).hexdigest(),'blender_version':'5.2.3','fonts':fonts,'images':images,'source_scene_unchanged':True},indent=2),encoding='utf-8')
print('BUNDLE PACKED',len(fonts),'fonts',len(images),'images;',len(production['groups']),'foreground groups',flush=True)
