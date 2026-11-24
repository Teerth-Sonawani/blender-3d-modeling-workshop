"""Phase 0 — scene scaffold for golden-desert-eagle.

Creates a fresh scene (only if the open file is the untouched factory startup),
metric units, the part collections and studio collections, then saves the
working .blend. Prints scene state and Cycles devices for render planning.

Run through: python scripts/mcp_call.py exec Models/golden-desert-eagle/scripts/00_scaffold.py
"""

import bpy
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle"
BLEND = os.path.join(ROOT, "golden-desert-eagle.blend")

objects = sorted(o.name for o in bpy.data.objects)
filepath = bpy.data.filepath
print("OPEN FILE:", filepath if filepath else "<unsaved>")
print("OBJECTS:", objects)

factory_names = {"Cube", "Camera", "Light"}
if filepath and not filepath.lower().endswith("golden-desert-eagle.blend"):
    raise RuntimeError(
        "Refusing to reset: a different saved file is open (%s). "
        "Open the model file first." % filepath
    )
if set(objects) - factory_names:
    raise RuntimeError("Refusing to reset: scene has non-default objects: %s" % objects)

bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.unit_settings.length_unit = "MILLIMETERS"

PARTS = [
    "Frame",
    "Slide",
    "Barrel",
    "Sights",
    "Controls",
    "Grip",
    "Magazine",
    "Marks",
]
root = bpy.data.collections.new("COL_DesertEagle")
scene.collection.children.link(root)

for name in PARTS:
    col = bpy.data.collections.new("COL_Part_" + name)
    root.children.link(col)

for name in ("COL_Lights", "COL_Cameras", "COL_Studio", "COL_Export"):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)

scene.render.engine = "CYCLES"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.cycles.samples = 64
scene.cycles.use_denoising = True

# Render device report.
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    print("DEVICES:", [(d.name, d.type) for d in prefs.devices])
    print("COMPUTE:", prefs.compute_device_type)
except Exception as exc:
    print("DEVICE ERROR:", exc)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED:", bpy.data.filepath)
print("COLLECTIONS:", [c.name for c in bpy.data.collections])
