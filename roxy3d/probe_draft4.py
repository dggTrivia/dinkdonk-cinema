import sys,json,hashlib,shutil,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from common import ROOT
from build_pass10_draft import bounds
from pass8_common import gpu
QA=ROOT/'qa10';TEST=QA/'draft4_probe';TEST.mkdir(exist_ok=True)
backup=QA/'source_before_draft4.blend'
if not backup.exists():shutil.copy2(ROOT/'roxy_pass10_draft.blend',backup)
baseline=QA/'draft4_protected_before.json'
if not baseline.exists():
    files={}
    for folder in ROOT.glob('out*'):
        if folder.is_dir():
            for p in folder.rglob('*'):
                if p.is_file():files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for n in ['roxy_pass9.blend','roxy_pass10.blend']:
        files[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    baseline.write_text(json.dumps(files,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(backup));sc=bpy.context.scene;gpu(sc);bpy.context.view_layer.update()
rows=[]
for o in sc.objects:
    rows.append(dict(name=o.name,type=o.type,layer=o.get('layer'),bounds=[round(x,4) for x in bounds(o)],materials=[m.name for m in getattr(o.data,'materials',[]) if m],energy=o.data.energy if o.type=='LIGHT' else None))
(QA/'draft4_source_inventory.json').write_text(json.dumps(rows,indent=2))
print('DISK',shutil.disk_usage(ROOT),flush=True)
print('CYCLES_DENOISE_PROPS',[(p.identifier,str(getattr(sc.cycles,p.identifier,None))) for p in sc.cycles.bl_rna.properties if 'denois' in p.identifier or 'seed' in p.identifier],flush=True)
print('LAYER_DENOISE',[(p.identifier,str(getattr(sc.view_layers[0].cycles,p.identifier,None))) for p in sc.view_layers[0].cycles.bl_rna.properties if 'denois' in p.identifier],flush=True)
sc.render.resolution_x=160;sc.render.resolution_y=90;sc.render.resolution_percentage=100;sc.cycles.samples=8;sc.cycles.use_denoising=False;sc.cycles.denoiser='OPTIX';sc.cycles.seed=1701;sc.cycles.use_animated_seed=False
sc.render.use_compositing=False;sc.view_layers[0].cycles.denoising_store_passes=True;sc.view_layers[0].use_pass_vector=True
print('FORMAT_PROPS',[(p.identifier,str(getattr(sc.render.image_settings,p.identifier,None))) for p in sc.render.image_settings.bl_rna.properties],flush=True)
sc.render.image_settings.media_type='MULTI_LAYER_IMAGE';sc.render.image_settings.file_format='OPEN_EXR_MULTILAYER';sc.render.image_settings.color_depth='32';sc.render.image_settings.exr_codec='ZIP'
sc.render.filepath=str(TEST/'raw_');sc.frame_start=1;sc.frame_end=3
sc.frame_set(1);sc.render.filepath=str(TEST/'raw_0001.exr');bpy.ops.render.render(write_still=True)
for i in [2,3]:shutil.copy2(TEST/'raw_0001.exr',TEST/('raw_%04d.exr'%i))
sc.render.filepath=str(TEST/'raw_');sc.cycles.use_denoising=True
t=time.perf_counter();result=bpy.ops.cycles.denoise_animation(output_filepath=str(TEST/'td_'));print('TEMPORAL_RESULT',result,time.perf_counter()-t,flush=True)
result=bpy.ops.cycles.denoise_animation(input_filepath=str(TEST/'raw_0001.exr'),output_filepath=str(TEST/'single.exr'));print('SINGLE_RESULT',result,flush=True)
im=bpy.data.images.load(str(TEST/'td_0001.exr'));tree=bpy.data.node_groups.new('D4 probe','CompositorNodeTree');node=tree.nodes.new('CompositorNodeImage');node.image=im
print('IMAGE_OUTPUTS',[(s.name,s.identifier) for s in node.outputs],flush=True)
gl=tree.nodes.new('CompositorNodeGlare');print('GLARE_TYPE_ENUM',[(e.name,e.value) for e in gl.inputs['Type'].bl_rna.properties['default_value'].enum_items] if hasattr(gl.inputs['Type'].bl_rna.properties['default_value'],'enum_items') else str(gl.inputs['Type'].default_value),flush=True)
print('GLARE_OUTPUTS',[s.name for s in gl.outputs],flush=True)
(QA/'draft4_probe_report.json').write_text(json.dumps({'temporal_output_exists':(TEST/'td_0001.exr').exists(),'single_output_exists':(TEST/'single.exr').exists(),'raw_bytes':(TEST/'raw_0001.exr').stat().st_size,'td_bytes':(TEST/'td_0001.exr').stat().st_size,'td_seconds':time.perf_counter()-t,'image_outputs':[s.name for s in node.outputs]},indent=2))
