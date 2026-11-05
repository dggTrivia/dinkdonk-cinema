import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Vector
from render_draft5 import setup,frame
from common import xyz
from draft5_common import *
sc=setup();sc.render.resolution_x=1000;sc.render.resolution_y=750
target=xyz(14.95,-.1,104);offset=Vector((2,-6,8)).normalized()*30
sc.camera.location=target+offset;sc.camera.rotation_mode='QUATERNION';sc.camera.rotation_quaternion=(-offset).to_track_quat('-Z','Y');sc.camera.data.ortho_scale=4.8
sec=frame(sc,WORK/'service_art_front.png');status('additional high-angle service-wall review rendered at 256 samples, exposing the complete turf-war panel behind the foreground building (%.1f seconds)'%sec)
