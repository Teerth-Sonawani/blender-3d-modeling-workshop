"""Assembly phase — studio set for the render.

Seamless light-grey cyclorama swept along X, product-photography light rig with
long strip sources for the gold reflections, and the camera set
(CAM_Hero_34, CAM_Side, CAM_Hero_Rear34, CAM_Top, detail cameras).
"""

import importlib
import math
import sys

import bmesh
import bpy
from mathutils import Vector

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import col, clear_collection, mat, save  # noqa: E402

# ---------------------------------------------------------------- backdrop
C = "COL_Studio"
clear_collection(C)

prof = [
    (1.00, -0.0030),
    (0.50, -0.0030),
    (0.20, -0.0030),
    (-0.02, -0.0028),
    (-0.10, -0.0018),
    (-0.20, 0.0020),
    (-0.28, 0.0100),
    (-0.34, 0.0300),
    (-0.385, 0.0650),
    (-0.415, 0.1100),
    (-0.432, 0.2000),
    (-0.442, 0.4000),
    (-0.448, 1.6000),
]
x0, x1 = -1.00, 1.40
bm = bmesh.new()
rows = []
for x in (x0, x1):
    rows.append([bm.verts.new((x, y, z)) for y, z in prof])
n = len(prof)
for i in range(n - 1):
    bm.faces.new([rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]])
me = bpy.data.meshes.new("SM_Studio_Cyclorama")
bm.normal_update()
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
backdrop = bpy.data.objects.new("SM_Studio_Cyclorama", me)
col(C).objects.link(backdrop)

bm = bpy.data.materials.get("MAT_Studio_Backdrop")
if bm is None:
    bm = bpy.data.materials.new("MAT_Studio_Backdrop")
    bm.use_nodes = True
    b = next(n for n in bm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.34, 0.336, 0.328, 1.0)
    b.inputs["Roughness"].default_value = 0.68
    b.inputs["Metallic"].default_value = 0.0
me.materials.append(bm)
print("backdrop verts:", len(me.vertices))

# ---------------------------------------------------------------- lights
L = "COL_Lights"
for ob in list(col(L).objects):
    d = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if d.users == 0:
        bpy.data.lights.remove(d)

TARGET = Vector((0.1365, 0.0, 0.080))


def area(name, loc, power, size, size_y, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = power
    d.shape = "RECTANGLE"
    d.size = size
    d.size_y = size_y
    d.color = color
    ob = bpy.data.objects.new(name, d)
    col(L).objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = (TARGET - ob.location).normalized().to_track_quat(
        "-Z", "Y").to_euler()
    return ob


# key: large soft source front-left high
area("LGT_Key", (-0.42, 0.54, 0.46), 7.2, 0.38, 0.85, (1.0, 0.965, 0.925))
# narrow strip in front: a tight, continuous highlight along the slide
area("LGT_Strip_L", (0.10, 0.34, 0.30), 3.0, 0.055, 0.85, (1.0, 0.98, 0.95))
# back strip: edge separation on the far side
area("LGT_Strip_R", (0.22, -0.30, 0.26), 1.8, 0.07, 0.80, (0.96, 0.98, 1.0))
# rim from behind to separate the slide from the backdrop
area("LGT_Rim", (0.10, -0.44, 0.44), 5.5, 0.35, 0.26, (1.0, 0.99, 0.96))
# broad top light for the rail and beavertail
area("LGT_Top", (0.13, 0.02, 0.72), 2.8, 0.55, 0.55, (1.0, 1.0, 1.0))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.035, 0.037, 0.042, 1.0)
bg.inputs[1].default_value = 1.0
print("lights:", [o.name for o in col(L).objects])

# ---------------------------------------------------------------- cameras
CC = "COL_Cameras"
clear_collection(CC)


def camera(name, direction, dist, lens, aim=TARGET):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.005
    cd.clip_end = 20.0
    ob = bpy.data.objects.new(name, cd)
    col(CC).objects.link(ob)
    ob.location = aim + Vector(direction).normalized() * dist
    ob.rotation_euler = (aim - ob.location).normalized().to_track_quat(
        "-Z", "Y").to_euler()
    return ob


camera("CAM_Hero_34", (0.58, 1.0, 0.30), 0.70, 85.0)
camera("CAM_Side", (0.0, 1.0, 0.0), 0.86, 105.0, Vector((0.1365, 0.0, 0.080)))
camera("CAM_Hero_Rear34", (-0.62, 1.0, 0.36), 0.66, 85.0)
camera("CAM_Top", (0.12, 0.55, 1.0), 0.62, 90.0)
camera("CAM_Detail_Port", (0.15, 1.0, 0.18), 0.30, 100.0, Vector((0.158, 0.0, 0.128)))
camera("CAM_Detail_Grip", (0.35, -1.0, 0.18), 0.30, 100.0, Vector((0.058, 0.0, 0.060)))
camera("CAM_Detail_Marks", (0.10, -1.0, 0.06), 0.26, 100.0, Vector((0.148, 0.0, 0.118)))
camera("CAM_Detail_Muzzle", (0.75, -1.0, 0.30), 0.26, 100.0, Vector((0.258, 0.0, 0.122)))
camera("CAM_Detail_Safety", (0.55, -1.0, 0.40), 0.26, 100.0, Vector((0.052, 0.0, 0.134)))

scene = bpy.context.scene
scene.camera = bpy.data.objects["CAM_Hero_34"]
print("cameras:", [o.name for o in col(CC).objects])
save()
