"""Export the C96 to GLB + FBX with the pivot at the grip (runs via MCP)."""
import bpy
import os
from mathutils import Matrix, Vector

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\mauser-c96-original"
EXP = os.path.join(ROOT, "exports")
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")
os.makedirs(EXP, exist_ok=True)

GEO = bpy.data.collections["COL_Geo"]
EXPC = bpy.data.collections["COL_Export"]
PIVOT = Vector((0.040, 0.0, -0.075))   # web of the hand on the grip

meshes = [o for o in GEO.objects if o.type == "MESH" and not o.name.startswith("SM_Ground")]
for o in meshes:
    if o.name not in EXPC.objects:
        EXPC.objects.link(o)


def bounds():
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for v in o.data.vertices:
            for i in range(3):
                lo[i] = min(lo[i], v.co[i])
                hi[i] = max(hi[i], v.co[i])
    return lo, hi


lo, hi = bounds()
print(f"AUTHOR BBOX  x {lo.x*1000:.1f}..{hi.x*1000:.1f}  y {lo.y*1000:.1f}..{hi.y*1000:.1f}"
      f"  z {lo.z*1000:.1f}..{hi.z*1000:.1f}")

for o in meshes:
    o.data.transform(Matrix.Translation(-PIVOT))
    o.data.update()

lo, hi = bounds()
print(f"EXPORT BBOX  x {lo.x*1000:.1f}..{hi.x*1000:.1f}  y {lo.y*1000:.1f}..{hi.y*1000:.1f}"
      f"  z {lo.z*1000:.1f}..{hi.z*1000:.1f}   (pivot at grip)")

bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]

glb = os.path.join(EXP, "mauser-c96-original.glb")
bpy.ops.export_scene.gltf(
    filepath=glb, export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_materials="EXPORT",
    export_cameras=False, export_lights=False,
)
print("GLB", os.path.exists(glb), os.path.getsize(glb) if os.path.exists(glb) else 0)

fbx = os.path.join(EXP, "mauser-c96-original.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx, use_selection=True, object_types={"MESH"},
    apply_unit_scale=True, global_scale=1.0, apply_scale_options="FBX_SCALE_NONE",
    axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", bake_anim=False,
)
print("FBX", os.path.exists(fbx), os.path.getsize(fbx) if os.path.exists(fbx) else 0)

for o in meshes:
    o.data.transform(Matrix.Translation(PIVOT))
    o.data.update()

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("restored authoring space; SAVED", BLEND)
