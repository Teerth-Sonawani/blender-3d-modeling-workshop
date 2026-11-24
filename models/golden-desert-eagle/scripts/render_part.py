"""Part gate renderer.

Reads a comma-separated part list from scripts/_part.txt and, for each part,
hides every other COL_Part_* collection, frames the part alone from a 3/4 and a
side view, and writes renders/part_<name>_<view>.png.

Lighting is the calibrated rig from the light test: sun key + soft area fill and
rim, mid-grey world.
"""

import importlib
import math
import os
import sys

import bpy
from mathutils import Vector

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import RENDERS, bbox, col, mesh_health, tri_count  # noqa: E402

parts = [p.strip() for p in
         open(os.path.join(SCRIPTS, "_part.txt"), encoding="utf-8").read().split(",")
         if p.strip()]

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 44
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.render.resolution_x = 860
scene.render.resolution_y = 860
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.0

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.175, 0.180, 0.190, 1.0)
bg.inputs[1].default_value = 1.0

lights = col("COL_Lights")
cam_data = bpy.data.cameras.new("CAM_Part")
cam = bpy.data.objects.new("CAM_Part", cam_data)
col("COL_Cameras").objects.link(cam)
scene.camera = cam
cam_data.lens = 70.0
cam_data.sensor_width = 36.0
fov = 2 * math.atan(0.5 * cam_data.sensor_width / cam_data.lens)


def clear_lights():
    for ob in list(lights.objects):
        d = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if d.users == 0:
            bpy.data.lights.remove(d)


def add_area(name, direction, center, energy, size_m, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.shape = "RECTANGLE"
    d.size = size_m
    d.size_y = size_m * 1.6
    d.color = color
    ob = bpy.data.objects.new(name, d)
    lights.objects.link(ob)
    ob.location = center + Vector(direction).normalized() * max(size_m * 2.4, 0.25)
    ob.rotation_euler = (center - ob.location).normalized().to_track_quat("-Z", "Y").to_euler()


for part in parts:
    target_col = "COL_Part_" + part
    for c in bpy.data.collections:
        if c.name.startswith("COL_Part_"):
            c.hide_render = c.name != target_col
            c.hide_viewport = c.name != target_col
    if "COL_Studio" in bpy.data.collections:
        bpy.data.collections["COL_Studio"].hide_render = True

    objs = [o for o in col(target_col).objects if o.type == "MESH"]
    print(f"=== PART {part}: {[(o.name, tri_count(o)) for o in objs]}")
    for o in objs:
        mesh_health(o)
    xs, ys, zs = [], [], []
    for o in objs:
        (x0, x1), _, _ = bbox(o)
        _, (y0, y1), _ = bbox(o)
        _, _, (z0, z1) = bbox(o)
        xs += [x0, x1]; ys += [y0, y1]; zs += [z0, z1]
    center = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                     (min(zs) + max(zs)) / 2))
    sx, sy, sz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
    print(f"  bbox mm x {min(xs)*1000:.1f}..{max(xs)*1000:.1f} "
          f"y {min(ys)*1000:.1f}..{max(ys)*1000:.1f} "
          f"z {min(zs)*1000:.1f}..{max(zs)*1000:.1f}")
    span = max(sx, sy, sz)

    clear_lights()
    d = bpy.data.lights.new("LGT_Key", "SUN")
    d.energy = 1.7
    d.angle = math.radians(4.0)
    d.color = (1.0, 0.97, 0.92)
    sob = bpy.data.objects.new("LGT_Key", d)
    lights.objects.link(sob)
    sob.rotation_euler = Vector((0.7, 1.0, -0.9)).normalized().to_track_quat(
        "-Z", "Y").to_euler()
    add_area("LGT_Fill", (1.0, -0.8, 0.2), center, 1.6, span * 0.9, (0.93, 0.96, 1.0))
    add_area("LGT_Rim", (-0.25, 1.0, 0.7), center, 2.2, span * 0.6)

    dist = (span * 0.5) / math.tan(fov / 2) * 1.30
    for tag, direction in (("34", Vector((0.55, -1.0, 0.45))),
                           ("side", Vector((0.02, -1.0, 0.02)))):
        cam.location = center + direction.normalized() * dist
        cam.rotation_euler = (center - cam.location).normalized().to_track_quat(
            "-Z", "Y").to_euler()
        out = os.path.join(RENDERS, f"part_{part.lower()}_{tag}.png")
        scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print("  RENDERED:", out)

# restore visibility so later build scripts can select objects
for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name in ("COL_Studio", "COL_Cutters"):
        c.hide_render = False
        c.hide_viewport = False
