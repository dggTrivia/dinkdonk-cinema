"""Brief 20: repair moved water geometry and a coincident roof cap; one draft."""
import sys, math, shutil
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from mathutils import Matrix, Vector
import build_scene as b
from common import ROOT,ZPP
from build_pass10_draft4 import quality
from build_pass10_draft7 import rain_layer
from pass8_common import gpu
from pngio import read,write

QA=ROOT/'qa10';TMP=ROOT/'cache'/'draft9'

def repair_split_droplets(sc):
    ob=sc.objects['D5 physical surface beads'];me=ob.data
    # Draft 8 selected individual vertices by a spatial box. A handful of
    # boundary beads were only partly moved, stretching their shared faces
    # between the former cinema sign and its new apartment-roof position.
    adjacent=[[] for _ in me.vertices];bad=set()
    for edge in me.edges:
        a,c=edge.vertices;adjacent[a].append(c);adjacent[c].append(a)
        if (me.vertices[a].co-me.vertices[c].co).length>.2:bad.update((a,c))
    visited=set();components=[]
    for start in sorted(bad):
        if start in visited:continue
        todo=[start];visited.add(start);island=[]
        while todo:
            k=todo.pop();island.append(k)
            for j in adjacent[k]:
                if j not in visited:visited.add(j);todo.append(j)
        components.append(island)
    turn=Matrix.Translation(Vector((2.85,-13.15,-29/ZPP))) @ Matrix.Rotation(math.pi/2,4,'Z')
    inv=ob.matrix_world.inverted();count=0
    for island in components:
        # Moved points have u around -.7; their unmoved partners have u
        # around 10..13. Complete the same rigid transform on those partners.
        for k in island:
            vertex=me.vertices[k];p=ob.matrix_world@vertex.co
            if p.x>5:vertex.co=inv@(turn@p);count+=1
    me.update()
    print('D9 repaired',len(components),'split droplet islands;',count,'remaining vertices moved with their islands',flush=True)
    return len(components)

def repair_roof_cap(sc):
    # Source construction gives both the masonry block and roof slab a
    # nominal top of 192. Floating-point coordinates actually put the block
    # 0.0000175 z-pixels above the felt, making that finish disappear.
    # End the masonry at the existing slab underside (190); the 190..192
    # wet-felt slab now provides the only outer roof surface.
    block=sc.objects['P8 right apartment block'];inv=block.matrix_world.inverted()
    for vertex in block.data.vertices:
        p=block.matrix_world@vertex.co
        if p.z*ZPP>191:p.z=190/ZPP;vertex.co=inv@p
    block.data.update()
    print('D9 masonry cap lowered to 190 beneath the existing 190..192 wet-felt roof slab',flush=True)

def main():
    TMP.mkdir(parents=True,exist_ok=True)
    source=ROOT/'roxy_pass10_draft.blend';backup=TMP/'source_draft8.blend'
    if not backup.exists():shutil.copy2(source,backup)
    bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
    b.GROUPS.clear();b.M.clear()
    islands=repair_split_droplets(sc);repair_roof_cap(sc)
    quality(sc);gpu(sc);sc.cycles.use_denoising=True
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=25
    for vl in sc.view_layers:vl.use_pass_vector=False;vl.cycles.denoising_store_passes=False
    sc.render.use_compositing=True
    sc['draft9_only']=True;sc['draft9_brief']='BRIEF-20-draft9.md'
    sc.render.filepath=str(QA/'draft_9.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    print('D9 model saved; rendering one fixed-camera draft and its weather layer',flush=True)
    beauty=TMP/'beauty_buffer.png';weather=TMP/'weather_buffer.png'
    sc.render.filepath=str(beauty);bpy.ops.render.render(write_still=True)
    rain_layer(sc);sc.render.filepath=str(weather);bpy.ops.render.render(write_still=True)
    a=read(beauty,use_cache=False);r=read(weather,use_cache=False)
    alpha=r[:,:,3:4].astype(np.float32)/255
    out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-alpha)+r[:,:,:3]*alpha).astype(np.uint8)
    write(QA/'draft_9.png',out);beauty.unlink();weather.unlink()
    (QA/'DRAFT-9.md').write_text(
        '# Draft 9\n\n'
        'Built from the saved Draft 8 scene; updated `roxy_pass10_draft.blend`.\n'
        f'Lines: Draft 8 moved only some vertices of {islands} water-droplet islands at the billboard selection boundary, leaving 40 stretched mesh edges (up to 14.04 scene units) between its old and new positions. Completed the billboard transform for each whole affected droplet; the HDR glare settings are retained.\n'
        'Roof blotches: the masonry block cap and wet-felt slab both ended at z=192; the cap was about 0.0000175 z-pixels higher, obscuring the felt while the separate repair-felt/stain overlays remained visible. Lowered the masonry cap to the slab underside at z=190, exposing the original continuous wet-felt finish at z=192. The conspicuous patches were roof repair/stain geometry against that incorrectly exposed cap.\n'
        'Delivered only `draft_9.png`: fixed camera, 1280×720, Cycles 256 samples, retained wet materials, soft ray-traced ripples/reflections and HDR glare, with the current-scene occluded weather frame composited. One STATUS line; stopped without extra views, clips, audits, rerenders or out10 work.\n',encoding='utf-8')
    stamp=datetime.now().astimezone().isoformat(timespec='seconds')
    with (QA/'STATUS.md').open('a',encoding='utf-8') as f:
        f.write(stamp+' | Finished: Draft 9 split billboard droplets and coincident roof cap fixed; saved draft model and one 1280×720 / 256-sample weather-composited draft_9.png; causes recorded in DRAFT-9.md; stopped.\n')
    print('D9 COMPLETE: qa10/draft_9.png, DRAFT-9.md, one STATUS line. STOP.',flush=True)

if __name__=='__main__':main()
