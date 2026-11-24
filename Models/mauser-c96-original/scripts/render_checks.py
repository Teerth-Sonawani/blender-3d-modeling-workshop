"""Lights, cameras and render passes for the C96 (runs inside Blender via MCP).

  python scripts/mcp_call.py exec Models/mauser-c96-original/scripts/render_checks.py
Optional argv-like flag via env CHECK_ONLY=1 renders just the side view.
"""
import bpy
import os
import math

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")
REND = os.path.join(ROOT, "renders")
os.makedirs(REND, exist_ok=True)
CHECK_ONLY = os.environ.get("C96_CHECK_ONLY") == "1"

scene = bpy.context.scene
GEO = bpy.data.collections["COL_Geo"]
CAMS = bpy.data.collections["COL_Cameras"]
LIGHTS = bpy.data.collections["COL_Lights"]


def clear(col, types):
    for ob in list(col.objects):
        if ob.type in types:
            bpy.data.objects.remove(ob, do_unlink=True)


clear(CAMS, {"CAMERA"})
clear(LIGHTS, {"LIGHT"})

# ------------------------------------------------------------------ engine
try:
    scene.render.engine = "BLENDER_EEVEE"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
ee = scene.eevee
for attr, val in (("taa_render_samples", 64), ("use_gtao", True), ("gtao_distance", 0.05),
                  ("use_raytracing", True), ("use_soft_shadows", True)):
    if hasattr(ee, attr):
        try:
            setattr(ee, attr, val)
        except Exception:
            pass
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = -1.15

# ------------------------------------------------------------------ world
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
grad = nt.nodes.new("ShaderNodeTexGradient")
mapn = nt.nodes.new("ShaderNodeMapping")
texco = nt.nodes.new("ShaderNodeTexCoord")
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.20, 0.205, 0.215, 1)
ramp.color_ramp.elements[1].color = (0.56, 0.57, 0.585, 1)
mapn.inputs["Rotation"].default_value = (0, math.radians(90), 0)
nt.links.new(texco.outputs["Generated"], mapn.inputs["Vector"])
nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# ------------------------------------------------------------------ lights


def area(name, loc, rot, size, power, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = "RECTANGLE"
    d.size = size[0]
    d.size_y = size[1]
    d.energy = power
    d.color = color
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    ob.rotation_euler = rot
    LIGHTS.objects.link(ob)
    return ob


def aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


key = area("LGT_Key_Softbox", (0.34, -0.50, 0.44), (0, 0, 0), (0.50, 0.50), 45,
           (1.0, 0.96, 0.90))
aim(key, (0.14, 0, -0.03))
fill = area("LGT_Fill_Bounce", (-0.44, -0.34, 0.04), (0, 0, 0), (0.9, 0.5), 13,
            (0.82, 0.88, 1.0))
aim(fill, (0.14, 0, -0.05))
rim = area("LGT_Rim_Edge", (0.00, 0.44, 0.34), (0, 0, 0), (0.6, 0.22), 24,
           (0.92, 0.95, 1.0))
aim(rim, (0.15, 0, 0.0))
top = area("LGT_Top_Scrim", (0.14, 0.0, 0.52), (0, 0, 0), (0.48, 0.30), 16)
aim(top, (0.14, 0, -0.02))

# ------------------------------------------------------------------ cameras


def cam(name, loc, target, ortho=None, lens=85.0):
    d = bpy.data.cameras.new(name)
    if ortho:
        d.type = "ORTHO"
        d.ortho_scale = ortho
    else:
        d.lens = lens
    d.clip_start = 0.01
    d.clip_end = 10.0
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    CAMS.objects.link(ob)
    aim(ob, target)
    return ob


cam_side = cam("CAM_Side_Ortho", (0.146, 0.75, -0.062), (0.146, 0, -0.062), ortho=0.345)
cam_hero = cam("CAM_Hero", (0.520, 0.345, 0.115), (0.145, 0.0, -0.052), lens=72)
cam_front = cam("CAM_Front_Ortho", (0.58, 0.0, -0.062), (0.146, 0.0, -0.062), ortho=0.30)
cam_top = cam("CAM_Top_Ortho", (0.146, 0.0, 0.45), (0.146, 0.0, -0.062), ortho=0.345)

# ------------------------------------------------------------------ ground
for ob in list(bpy.data.objects):
    if ob.name.startswith("SM_Ground"):
        bpy.data.objects.remove(ob, do_unlink=True)

if not CHECK_ONLY:
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3.0)
    me = bpy.data.meshes.new("SM_Ground_Plane")
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("SM_Ground_Plane", me)
    g.location = (0.15, 0.0, -0.142)
    g.data.materials.append(bpy.data.materials.get("MAT_Surface_Studio_Floor")
                            or bpy.data.materials.new("MAT_Surface_Studio_Floor"))
    m = bpy.data.materials["MAT_Surface_Studio_Floor"]
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.30, 0.295, 0.285, 1)
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Metallic"].default_value = 0.0
    bpy.data.collections["COL_Geo"].objects.link(g)


def render(camera, path, res=(1920, 1080), samples=64):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = res
    if hasattr(ee, "taa_render_samples"):
        ee.taa_render_samples = samples
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path, os.path.exists(path))


render(cam_side, os.path.join(REND, "side.png"), (1920, 1080), 96)
render(cam_hero, os.path.join(REND, "hero.png"), (1920, 1080), 192)
render(cam_front, os.path.join(REND, "front.png"), (1920, 1080), 96)
render(cam_top, os.path.join(REND, "top.png"), (1920, 1080), 96)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
