"""Make a local H.264 QA movie from the delivered PNG sheets and depth stack.

Run with bundled Python to composite frames, then Blender with --encode.
The ambient layer is held at the fallback frame to isolate prop motion.
"""
from pathlib import Path
import sys,json,warnings
sys.path.insert(0,str(Path(__file__).resolve().parent))
warnings.filterwarnings('ignore',category=DeprecationWarning)
import numpy as np
from pngio import read,write
from package_vehicles import blend

ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa4';OUT=ROOT/'out4';FRAMES=QA/'preview_frames'

def composite():
    m=json.loads((OUT/'manifest.json').read_text());base=read(OUT/'lit_bg.png')
    layers=[(e,read(OUT/e['file'])) for e in m['render_layers']]
    sheets=[(e,read(OUT/e['file'])) for e in m['prop_loops']]
    enlarge=lambda a,n:np.repeat(np.repeat(a,n,axis=0),n,axis=1)
    for f in range(72):
        a=base.copy();draw=[(e['z_index'],e['x'],e['y'],im,False) for e,im in layers]
        for e,sheet in sheets:
            x=f%6*e['w'];y=f//6*e['h'];cell=sheet[y:y+e['h'],x:x+e['w']]
            draw.append((e['z_index'],e['x'],e['y'],cell,True))
        for z,x,y,im,add in sorted(draw,key=lambda q:q[0]):blend(a,im,x,y,add)
        panel=np.full((720,1280,4),255,np.uint8);panel[:,:,:3]=(20,21,30)
        blend(panel,enlarge(a[510:740,1025:1465],2),0,0)
        blend(panel,enlarge(a[530:650,580:805],2),0,480)
        blend(panel,enlarge(a[880:950,1160:1225],4),950,25)
        blend(panel,a[::3,::3],640,360)
        write(FRAMES/('f'+str(f).zfill(3)+'.png'),panel)
    print('PREVIEW_FRAMES_READY',flush=True)

def encode():
    import bpy
    sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
    sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
    sc.render.fps=24;sc.render.fps_base=1;sc.frame_start=1;sc.frame_end=216
    sc.render.use_sequencer=True;sc.render.use_compositing=False
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
    sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.sequencer_colorspace_settings.name='sRGB'
    ed=sc.sequence_editor_create();strip=ed.strips.new_image('Delivered prop loops - three cycles',str(FRAMES/'f000.png'),1,1)
    for i in range(1,216):strip.elements.append('f'+str(i%72).zfill(3)+'.png')
    strip.frame_final_duration=216
    sc.render.image_settings.media_type='VIDEO';sc.render.image_settings.file_format='FFMPEG'
    sc.render.image_settings.color_mode='RGB';ff=sc.render.ffmpeg
    ff.format='MPEG4';ff.codec='H264';ff.audio_codec='NONE';ff.constant_rate_factor='HIGH';ff.ffmpeg_preset='GOOD'
    sc.render.use_file_extension=False;sc.render.filepath=str(QA/'prop_preview.mp4')
    bpy.ops.render.render(animation=True)
    ed.strips.remove(strip)
    movie=ed.strips.new_movie('Actual preview decode',str(QA/'prop_preview.mp4'),1,1)
    assert movie.frame_duration==216
    assert (movie.elements[0].orig_width,movie.elements[0].orig_height)==(1280,720)
    sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
    for f in [0,15,45]:
        sc.frame_set(f+1);sc.render.filepath=str(QA/('preview_decoded_f'+str(f).zfill(3)+'.png'))
        bpy.ops.render.render(write_still=True)
    (QA/'preview_metadata.json').write_text(json.dumps({'format':'H264/MP4','frames':216,'fps':24,
        'seconds':9,'size':[1280,720],'prop_cycles':3,'ambient':'Held at fallback frame 60',
        'decoded_samples':[0,15,45],'bytes':(QA/'prop_preview.mp4').stat().st_size},indent=2))
    print('PREVIEW_MOVIE_READY',flush=True)

if __name__=='__main__':
    if '--encode' in sys.argv:encode()
    else:composite()
