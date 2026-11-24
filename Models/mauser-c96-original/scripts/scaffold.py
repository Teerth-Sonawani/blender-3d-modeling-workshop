"""Scene scaffold for the C96 model: collections, units, saved file."""
import bpy
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.unit_settings.length_unit = "MILLIMETERS"

# clear the default startup objects (Cube / Camera / Light) - not user work
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

root = bpy.data.collections.get("Collection")
if root:
    bpy.data.collections.remove(root)

base = bpy.context.scene.collection
names = ["COL_Blockout", "COL_Geo", "COL_Collision", "COL_Lights", "COL_Cameras", "COL_Export"]
for n in names:
    col = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if col.name not in [c.name for c in base.children]:
        base.children.link(col)

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
print("COLLECTIONS", [c.name for c in base.children])
