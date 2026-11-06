"""Add seat-back screen anchors to the F10 camera data from the matching Blender file."""
import json
import sys
from pathlib import Path

import bpy

layout_path, camera_path = map(Path, sys.argv[sys.argv.index("--") + 1:])
layout = json.loads(layout_path.read_text(encoding="utf-8"))
camera_data = json.loads(camera_path.read_text(encoding="utf-8"))
scene = bpy.data.scenes["Screen 1 - Seated POV"]
bpy.context.window.scene = scene
bpy.context.view_layer.update()
camera = scene.camera
matrix = camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=1920, y=1080) @ camera.matrix_world.inverted()
assert all(abs(a - b) < .0001 for row_a, row_b in zip(matrix, camera_data["matrix"]) for a, b in zip(row_a, row_b)), "Camera does not match the POV plate"

seat_backs = {}
for row in layout["rows"]:
    name = row["row"]
    back = scene.objects[f"Row {name} purple backs - future occluder"]
    vertices = [back.matrix_world @ vertex.co for vertex in back.data.vertices]
    for seats in row["seat_u_by_block"].values():
        for u in seats:
            points = []
            for vertex in vertices:
                if abs(vertex.x - u) >= .36:
                    continue
                point = matrix @ vertex.to_4d()
                if point.w > .35:
                    points.append(((1 + point.x / point.w) * 960, (1 - point.y / point.w) * 540, point.w))
            if not points:
                continue
            left, right = min(p[0] for p in points), max(p[0] for p in points)
            width = right - left
            center = (left + right) / 2
            crest = min((p for p in points if abs(p[0] - center) < width * .24), key=lambda p: p[1], default=None)
            if crest is None:
                continue
            # Place the head on the screen side of the chair, behind its rear-facing silhouette.
            seat_backs[f"{name}:{u:.3f}"] = [round(value, 2) for value in (center, crest[1], width, crest[2] + .12)]

assert sum(key.startswith("B:") for key in seat_backs) == sum(map(len, layout["rows"][0]["seat_u_by_block"].values()))
camera_data["seatBacks"] = seat_backs
camera_path.write_text(json.dumps(camera_data, separators=(",", ":")), encoding="utf-8")
print(f"Exported {len(seat_backs)} seat-back anchors")
