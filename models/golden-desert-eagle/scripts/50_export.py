"""Export GLB + FBX from a duplicate and run a GLB round-trip check.

Exports only model meshes (no studio, lights or cameras), duplicated and shifted
so the origin sits at the grip hand-contact centre. The working scene is never
translated.
"""

import importlib
import os
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import EXPORTS, ROOT, bbox, col, save, tri_count  # noqa: E402

PIVOT = (0.0580, 0.0, 0.0600)

# ---------------------------------------------------------------- duplicate
for ob in list(bpy.data.collections.get("COL_Export").objects):
    bpy.data.objects.remove(ob, do_unlink=True)

src = []
for c in bpy.data.collections:
    if c.name.startswith("COL_Part_"):
        src.extend([o for o in c.objects if o.type == "MESH"])

dups = []
for ob in src:
    nd = ob.copy()
    nd.data = ob.data.copy()
    nd.name = ob.name + "_EXP"
    col("COL_Export").objects.link(nd)
    # shift in world space: mark objects carry their own object offsets
    from mathutils import Matrix
    nd.matrix_world = Matrix.Translation(
        (-PIVOT[0], -PIVOT[1], -PIVOT[2])) @ ob.matrix_world
    dups.append(nd)
    ob.select_set(False)

# --- flatten procedural materials to representative PBR values for export ------
FLAT = {
    "MAT_Gold_TitaniumGold": ((0.930, 0.635, 0.235, 1.0), 1.00, 0.16),
    "MAT_Rubber_Grip":       ((0.030, 0.031, 0.034, 1.0), 0.00, 0.56),
    "MAT_Sight_Black":       ((0.016, 0.016, 0.018, 1.0), 0.65, 0.34),
    "MAT_Black_Metal":       ((0.016, 0.016, 0.018, 1.0), 0.55, 0.40),
    "MAT_Mark_Etch":         ((0.020, 0.014, 0.008, 1.0), 0.35, 0.42),
    "MAT_Steel_Bore":        ((0.012, 0.012, 0.013, 1.0), 1.00, 0.38),
}
used = {m for nd in dups for m in nd.data.materials if m}
for mat in used:
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for sock in ("Base Color", "Roughness", "Normal", "Metallic", "Emission Color"):
        if sock in b.inputs:
            for lk in list(b.inputs[sock].links):
                nt.links.remove(lk)
    base, met, rough = FLAT.get(mat.name, ((0.5, 0.5, 0.5, 1.0), 0.0, 0.5))
    b.inputs["Base Color"].default_value = base
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
print("flattened materials:", sorted(m.name for m in used))

total_tris = sum(tri_count(o) for o in dups)
print("export objects:", len(dups), "tris:", total_tris)

for ob in bpy.context.selected_objects:
    ob.select_set(False)
for nd in dups:
    nd.select_set(True)
bpy.context.view_layer.objects.active = dups[0]

# ---------------------------------------------------------------- GLB
glb = os.path.join(EXPORTS, "golden-desert-eagle.glb")
bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
    export_normals=True,
)
print("GLB:", glb, os.path.getsize(glb), "bytes")

# ---------------------------------------------------------------- FBX
fbx = os.path.join(EXPORTS, "golden-desert-eagle.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx,
    use_selection=True,
    apply_scale_options="FBX_SCALE_NONE",
    axis_forward="-Z",
    axis_up="Y",
    object_types={"MESH"},
    mesh_smooth_type="FACE",
    bake_space_transform=False,
    path_mode="COPY",
    embed_textures=False,
)
print("FBX:", fbx, os.path.getsize(fbx), "bytes")

for nd in dups:
    data = nd.data
    bpy.data.objects.remove(nd, do_unlink=True)
    bpy.data.meshes.remove(data)

# ---------------------------------------------------------------- round trip
before = bpy.data.filepath
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.ops.import_scene.gltf(filepath=glb)
imported = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("re-imported meshes:", len(imported))
xs, ys, zs = [], [], []
tris = 0
for ob in imported:
    (x0, x1), _, _ = bbox(ob)
    _, (y0, y1), _ = bbox(ob)
    _, _, (z0, z1) = bbox(ob)
    xs += [x0, x1]; ys += [y0, y1]; zs += [z0, z1]
    tris += tri_count(ob)
print(f"round-trip tris: {tris}")
print(f"round-trip bbox mm: x {min(xs)*1000:.1f}..{max(xs)*1000:.1f} "
      f"y {min(ys)*1000:.1f}..{max(ys)*1000:.1f} "
      f"z {min(zs)*1000:.1f}..{max(zs)*1000:.1f}")
print("round-trip size mm:", round((max(xs)-min(xs))*1000, 1), "x",
      round((max(ys)-min(ys))*1000, 1), "x", round((max(zs)-min(zs))*1000, 1))
print("materials:", sorted({m.name for ob in imported for m in ob.data.materials if m}))

# comparison frame of the imported asset
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 800
scene.render.resolution_y = 500
scene.view_settings.view_transform = "AgX"

wd = bpy.data.worlds.new("W")
scene.world = wd
wd.use_nodes = True
bg = next(n for n in wd.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.3, 0.3, 0.32, 1.0)
bg.inputs[1].default_value = 1.0

cd = bpy.data.cameras.new("CAM_RT")
cd.lens = 85.0
cam = bpy.data.objects.new("CAM_RT", cd)
scene.collection.objects.link(cam)
scene.camera = cam
from mathutils import Vector  # noqa: E402

centre = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
                 (min(zs) + max(zs)) / 2))
cam.location = centre + Vector((0.55, 1.0, 0.32)).normalized() * 0.72
cam.rotation_euler = (centre - cam.location).normalized().to_track_quat(
    "-Z", "Y").to_euler()

ld = bpy.data.lights.new("K", "SUN")
ld.energy = 2.2
ld.angle = 0.09
sun = bpy.data.objects.new("K", ld)
scene.collection.objects.link(sun)
sun.rotation_euler = Vector((0.7, 1.0, -0.9)).normalized().to_track_quat(
    "-Z", "Y").to_euler()

out = os.path.join(ROOT, "renders", "roundtrip_glb.png")
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("ROUND-TRIP RENDER:", out)

# restore the working file so the live session matches disk again
bpy.ops.wm.open_mainfile(filepath=de_lib.BLEND)
print("RESTORED WORKING FILE:", bpy.data.filepath)
