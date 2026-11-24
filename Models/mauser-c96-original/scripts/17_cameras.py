"""Mauser C96 — restore the four cameras to their authored transforms.

These cameras were re-positioned during the quality pass on a misreading of the
scene units: the geometry is authored in metres (the pistol is 0.288 m long),
not millimetres, so the original transforms were already correct.  This puts
back the delivered values exactly, with one deliberate change:

  CAM_Hero lens 90 mm -> 62 mm.  At 90 mm the delivered hero cropped the muzzle
  and the top of the receiver; 62 mm fits the whole pistol at 3/4.

All other values are as found in `mauser-c96-original.blend` before the pass.
"""
import bpy

CAMERAS = {
    "CAM_Side_Ortho": {"type": 'ORTHO', "ortho": 0.345, "lens": 50.0,
                       "loc": (0.15, 0.75, -0.06),
                       "rot": (-1.571, 3.142, 0.0)},
    "CAM_Top_Ortho": {"type": 'ORTHO', "ortho": 0.345, "lens": 50.0,
                      "loc": (0.15, 0.0, 0.45),
                      "rot": (0.0, 0.0, 0.0)},
    "CAM_Front_Ortho": {"type": 'ORTHO', "ortho": 0.3, "lens": 50.0,
                        "loc": (0.58, 0.0, -0.06),
                        "rot": (1.571, 0.0, 1.571)},
    "CAM_Hero": {"type": 'PERSP', "ortho": 6.0, "lens": 62.0,
                 "loc": (0.44, 0.4, 0.17),
                 "rot": (1.186, 0.0, 2.514)},
}

for name, spec in CAMERAS.items():
    cam = bpy.data.objects[name]
    cam.data.type = spec["type"]
    cam.data.ortho_scale = spec["ortho"]
    cam.data.lens = spec["lens"]
    cam.location = spec["loc"]
    cam.rotation_euler = spec["rot"]

bpy.context.view_layer.update()
result = {n: {"loc": [round(v, 3) for v in bpy.data.objects[n].location],
              "ortho": bpy.data.objects[n].data.ortho_scale,
              "lens": bpy.data.objects[n].data.lens} for n in CAMERAS}
print("CAMERAS RESTORED:", result)
