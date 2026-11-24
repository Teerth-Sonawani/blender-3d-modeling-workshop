"""Mosin M91/30 — re-frame the hero camera.

The delivered CAM_Hero sat at (-0.02, -2.45, 0.34) with a 52 mm lens: a nearly
orthographic side elevation of a 1.235 m rifle, which is why the hero render
read flat.  This frames it as a low three-quarter from the front right, the
angle that shows the bolt handle, ejection port, sights and the stock shape
together.
"""
import bpy
import math
from mathutils import Vector

CAM = "CAM_Hero"
TARGET = Vector((0.0, 0.0, 0.072))
POSITION = Vector((0.55, -1.32, 0.34))
LENS = 42.0

cam = bpy.data.objects[CAM]
cam.data.lens = LENS
cam.location = POSITION
cam.rotation_euler = (TARGET - POSITION).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()

dist = (TARGET - POSITION).length
result = {
    "camera": CAM,
    "location": [round(v, 3) for v in cam.location],
    "rotation": [round(v, 4) for v in cam.rotation_euler],
    "lens": LENS,
    "distance_m": round(dist, 3),
    "frame_width_m": round(36.0 / LENS * dist, 3),
    "elevation_deg": round(math.degrees(math.atan2(
        POSITION.z - TARGET.z,
        Vector((POSITION.x, POSITION.y, 0.0)).length)), 1),
}
print("HERO CAMERA:", result)
