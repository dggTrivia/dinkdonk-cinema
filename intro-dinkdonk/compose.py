# Lays the rendered DINK DONK logo card (dd_NNNNN.png from build_logo.py) over the original
# National Amusements snipe and writes an H.264/AAC MP4 with the original audio untouched.
#
#   blender -b --factory-startup --python compose.py -- <source.mp4> <frames_dir> <out.mp4> <height> <start> <end> [signs_dir]
import bpy, sys, os

A = sys.argv[sys.argv.index('--') + 1:]
SRC, FRAMES, OUT, H, START, END = A[0], A[1], A[2], int(A[3]), int(A[4]), int(A[5])
SIGNS = A[6] if len(A) > 6 else None
W = H * 16 // 9
# no fade in: the render opens on the original's own frame 1108 (cut before the slats at 1112)
FADE_OUT = (1359, 1372)    # same fade as the original (measured)

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps, sc.render.fps_base = 24, 1.0
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
se = sc.sequence_editor_create()

mv = se.strips.new_movie('original', SRC, 1, 1)
mv.transform.scale_x = mv.transform.scale_y = W / mv.elements[0].orig_width
se.strips.new_sound('audio', SRC, 2, 1)

files = sorted(f for f in os.listdir(FRAMES) if f.startswith('dd_') and f.endswith('.png'))
first = int(files[0][3:8])
img = se.strips.new_image('dinkdonk', os.path.join(FRAMES, files[0]), 3, first)
for f in files[1:]:
    img.elements.append(f)
probe = bpy.data.images.load(os.path.join(FRAMES, files[0]))
img.transform.scale_x = img.transform.scale_y = H / probe.size[1]
img.blend_type = 'ALPHA_OVER'
for f, v in ((FADE_OUT[0], 1.0), (FADE_OUT[1], 0.0)):
    img.color_multiply = v; img.keyframe_insert('color_multiply', frame=f)

# the neon dome shot with its N panels replaced (sg_NNNNN.png full frames from sign_replace.py)
if SIGNS:
    files = sorted(f for f in os.listdir(SIGNS) if f.startswith('sg_') and f.endswith('.png'))
    sg = se.strips.new_image('dome_signs', os.path.join(SIGNS, files[0]), 4, int(files[0][3:8]))
    for f in files[1:]:
        sg.elements.append(f)
    sg.transform.scale_x = sg.transform.scale_y = H / bpy.data.images.load(os.path.join(SIGNS, files[0])).size[1]

sc.frame_start, sc.frame_end = START, END
r = sc.render
r.image_settings.media_type = 'VIDEO'  # Blender 5: pick video output before the format
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'
r.ffmpeg.codec = 'H264'
r.ffmpeg.constant_rate_factor = 'HIGH'
r.ffmpeg.ffmpeg_preset = 'GOOD'
r.ffmpeg.gopsize = 24
r.ffmpeg.audio_codec = 'AAC'
r.ffmpeg.audio_bitrate = 192
r.ffmpeg.audio_channels = 'STEREO'
r.filepath = OUT
r.use_file_extension = False
bpy.ops.render.render(animation=True)
