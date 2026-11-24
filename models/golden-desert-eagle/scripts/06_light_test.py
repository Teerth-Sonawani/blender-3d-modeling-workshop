"""Lighting calibration: render the frame+slide under three rigs at low res."""

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
from de_lib import RENDERS, bbox, col  # noqa: E402

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_"):
        c.hide_render = c.name not in ("COL_Part_Frame", "COL_Part_Slide")
        c.hide_viewport = c.name not in ("COL_Part_Frame", "COL_Part_Slide")

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
xs, ys, zs = [], [], []
for o in objs:
    (x0, x1), _, _ = bbox(o)
    _, (y0, y1), _ = bbox(o)
    _, _, (z0, z1) = bbox(o)
    xs += [x0, x1]; ys += [y0, y1]; zs += [z0, z1]
center = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
size = max(max(xs) - min(xs), max(zs) - min(zs))

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 560
scene.render.resolution_y = 380
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.0

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")

cam_data = bpy.data.cameras.new("CAM_Test")
cam = bpy.data.objects.new("CAM_Test", cam_data)
col("COL_Cameras").objects.link(cam)
scene.camera = cam
cam_data.lens = 70.0
cam.location = center + Vector((0.35, -1.0, 0.30)).normalized() * size * 2.6
cam.rotation_euler = (center - cam.location).normalized().to_track_quat("-Z", "Y").to_euler()

lights = col("COL_Lights")


def clear_lights():
    for ob in list(lights.objects):
        d = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if d.users == 0:
            bpy.data.lights.remove(d)


def sun(name, strength, direction, angle_deg=6.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = strength
    d.angle = math.radians(angle_deg)
    ob = bpy.data.objects.new(name, d)
    lights.objects.link(ob)
    ob.rotation_euler = (-Vector(direction)).normalized().to_track_quat("-Z", "Y").to_euler()
    return ob


def area(name, energy, direction, size_m, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.shape = "RECTANGLE"
    d.size = size_m
    d.size_y = size_m * 1.6
    d.color = color
    ob = bpy.data.objects.new(name, d)
    lights.objects.link(ob)
    ob.location = center + Vector(direction).normalized() * size * 2.0
    ob.rotation_euler = (center - ob.location).normalized().to_track_quat("-Z", "Y").to_euler()
    return ob


rigs = {
    "A": dict(world=0.30),
    "B": dict(world=0.18),
    "C": dict(world=0.09),
}
for tag, cfg in rigs.items():
    clear_lights()
    bg.inputs[0].default_value = (cfg["world"], cfg["world"], cfg["world"] * 1.05, 1.0)
    bg.inputs[1].default_value = 1.0
    if tag == "A":
        sun("LGT_Key", 2.5, (-0.7, -1.0, 0.9), 5.0)
        sun("LGT_Rim", 1.2, (0.4, 1.0, 0.5), 12.0)
    elif tag == "B":
        sun("LGT_Key", 1.6, (-0.7, -1.0, 0.9), 4.0)
        area("LGT_Fill", 1.5, (1.0, -0.7, 0.2), size * 0.8, (0.93, 0.96, 1.0))
        area("LGT_Rim", 2.0, (-0.2, 1.0, 0.7), size * 0.6)
    else:
        area("LGT_Key", 4.0, (-0.7, -1.0, 0.9), size * 0.55, (1.0, 0.97, 0.92))
        area("LGT_Fill", 1.2, (1.0, -0.7, 0.2), size * 0.9, (0.93, 0.96, 1.0))
        area("LGT_Rim", 2.5, (-0.2, 1.0, 0.7), size * 0.5)
    out = os.path.join(RENDERS, f"lighttest_{tag}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("RENDERED", tag, out)
