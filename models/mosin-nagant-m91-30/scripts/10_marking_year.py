"""Mosin M91/30 — move the receiver date stamp out from behind the cut-off.

The delivered SM_Marking_Year sat at x -253.2..-238.2, z 59.9..65.8 mm, which
is exactly where SM_MagazineCutoff sits (x -259.2..-228.8, z 57.0..67.0 mm,
protruding to y +21.5 mm).  The date was therefore fully occluded, which is why
the delivered record could only ever report "ТК" and no year.

SM_Marking_Model ("ТК") occupies z 78.9..87.6.  The date is moved into the
clear band between the lever top (z 67.0) and the model stamp (z 78.9), giving
a two-line stamp:
    ТК      z 78.9 .. 87.6
    1938    z 71.5 .. 77.4
"""
import bpy
from mathutils import Vector

YEAR = "SM_Marking_Year"
TARGET_Z_MIN = 0.0715

ob = bpy.data.objects[YEAR]
before = [round(v * 1000, 1) for v in ob.dimensions]
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
z_min = min(v.z for v in bb)
ob.location.z += TARGET_Z_MIN - z_min
bpy.context.view_layer.update()

bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
result = {
    "object": YEAR,
    "dims_mm": before,
    "new_z_mm": [round(min(v.z for v in bb) * 1000, 1),
                 round(max(v.z for v in bb) * 1000, 1)],
    "new_x_mm": [round(min(v.x for v in bb) * 1000, 1),
                 round(max(v.x for v in bb) * 1000, 1)],
    "location": [round(v, 4) for v in ob.location],
}
print("MARKING YEAR:", result)
