"""Mosin M91/30 — re-aim the rear-sight detail camera, flatten the graduations.

The delivered CAM_detail_rearsight sat at (0.030, -0.190, 0.165) with an 85 mm
lens: a ~20 deg grazing view along the leaf's Y axis.  At that angle each
graduation tick projects as a long streak and the leaf top is a sliver, so the
shot could never show the sight.  A rear sight has to be shot from above and
behind, looking down the leaf.

Also drops the ticks to 0.5 mm proud (they were 0.8 mm) so they read as
graduations rather than as a raised fence.
"""
import bpy
import math
from mathutils import Vector

CAM = "CAM_detail_rearsight"
TARGET = Vector((0.024, 0.0, 0.0915))     # leaf centre, top face
POSITION = Vector((-0.045, -0.115, 0.170))
LENS = 50.0
TICK_Z = 0.0937


def aim(cam, position, target):
    cam.location = position
    direction = target - position
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


cam = bpy.data.objects[CAM]
cam.data.lens = LENS
aim(cam, POSITION, TARGET)

for i in range(1, 21):
    ob = bpy.data.objects.get("SM_RearSight_Tick_%02d" % i)
    if ob:
        ob.location.z = TICK_Z

# Slider sits at the leaf's rear so it does not cover the numerals.
slider = bpy.data.objects.get("SM_RearSight_Slider")
if slider:
    slider.location.x = 0.0008

bpy.context.view_layer.update()
result = {
    "camera": CAM,
    "location": [round(v, 4) for v in cam.location],
    "rotation": [round(v, 4) for v in cam.rotation_euler],
    "lens": cam.data.lens,
    "elevation_deg": round(math.degrees(math.atan2(
        POSITION.z - TARGET.z,
        (Vector((POSITION.x, POSITION.y, 0)) - Vector((TARGET.x, TARGET.y, 0))).length)), 1),
}
print("SIGHT CAMERA:", result)
