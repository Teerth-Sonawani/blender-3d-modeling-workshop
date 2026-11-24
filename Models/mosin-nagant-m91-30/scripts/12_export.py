"""Mosin M91/30 — export GLB (visual) and FBX (visual + UCX collision).

The delivered FBX contained no UCX_/COL_ objects even though the scene had four
UCX meshes: the export ran from a selection that excluded them.  This exports
explicitly:

  GLB  visual meshes only, so the collision boxes cannot clad the rifle
  FBX  visual meshes *and* UCX_ proxies, which is the Unreal convention

Both are written from the same scene without touching the working mesh.
"""
import bpy
import os

BASE = bpy.path.abspath("//")
SLUG = "mosin-nagant-m91-30"
OUT = os.path.join(BASE, "exports")
os.makedirs(OUT, exist_ok=True)

col = bpy.data.collections["COL_Export"]
meshes = [o for o in col.objects if o.type == 'MESH']
visual = [o for o in meshes if not o.name.startswith("UCX_")]
collision = [o for o in meshes if o.name.startswith("UCX_")]


def select(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]


# --- GLB: visual only -------------------------------------------------------
select(visual)
glb = os.path.join(OUT, SLUG + ".glb")
bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False,
)

# --- FBX: visual + collision ------------------------------------------------
select(visual + collision)
fbx = os.path.join(OUT, SLUG + ".fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx,
    use_selection=True,
    object_types={'MESH'},
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    mesh_smooth_type='FACE',
    use_mesh_modifiers=True,
    path_mode='COPY',
    embed_textures=True,
)

bpy.ops.object.select_all(action='DESELECT')

result = {
    "glb": {"path": glb, "bytes": os.path.getsize(glb), "meshes": len(visual)},
    "fbx": {"path": fbx, "bytes": os.path.getsize(fbx),
            "meshes": len(visual), "collision": len(collision),
            "collision_names": sorted(o.name for o in collision)},
}
print("EXPORT:", result)
