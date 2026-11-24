"""Mauser C96 — collision proxies, grip pivot, and export (scene units = metres).

The brief calls the asset "unreal/unity ready", but the delivered exports carry
no collision geometry: COL_Collision and COL_Export were both empty and neither
file contained a UCX_ object.

Four hand-authored boxes are fitted to the measured part layout (written in mm
for readability, converted to metres on build).  The export then follows
`export_assets.py`: translate the mesh data so the origin sits at the grip web,
export, and restore the authoring space.

  GLB  visual meshes only, so the proxies cannot clad the pistol
  FBX  visual meshes plus the UCX_ proxies
"""
import bpy
import bmesh
import os
from mathutils import Matrix, Vector

BASE = bpy.path.abspath("//")
SLUG = "mauser-c96-original"
OUT = os.path.join(BASE, "exports")
os.makedirs(OUT, exist_ok=True)

MM = 0.001
PIVOT = Vector((0.040, 0.0, -0.075))     # web of the hand on the grip

# name, x0, x1, y0, y1, z0, z1   (mm)
BOXES_MM = [
    ("UCX_Grip", 1.5, 52.0, -17.4, 17.4, -138.5, -47.0),
    ("UCX_Frame", 12.5, 148.0, -12.9, 12.9, -74.3, -13.6),
    ("UCX_Receiver", 34.0, 148.0, -13.6, 13.6, -13.6, 15.2),
    ("UCX_Barrel", 146.5, 288.0, -10.2, 10.2, -10.2, 10.2),
]
INFLATE = 0.0006


def make_box(name, x0, x1, y0, y1, z0, z1):
    lo = Vector((x0, y0, z0)) * MM - Vector((INFLATE,) * 3)
    hi = Vector((x1, y1, z1)) * MM + Vector((INFLATE,) * 3)
    centre, size = (lo + hi) / 2.0, hi - lo
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size.x + centre.x,
                       v.co.y * size.y + centre.y,
                       v.co.z * size.z + centre.z))
    bm.to_mesh(me)
    bm.free()
    me.validate()
    ob = bpy.data.objects.new(name, me)
    for coll in ("COL_Collision", "COL_Export"):
        c = bpy.data.collections.get(coll)
        if c:
            c.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = True
    ob.display_type = 'WIRE'
    return ob


for name, *_ in BOXES_MM:
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

built = [{"name": spec[0],
          "dims_mm": [round(d * 1000, 1) for d in make_box(*spec).dimensions]}
         for spec in BOXES_MM]

visual = [o for o in bpy.data.objects
          if o.type == 'MESH' and o.name.startswith("SM_")
          and not o.name.startswith("SM_Ground")]
collision = [o for o in bpy.data.objects
             if o.type == 'MESH' and o.name.startswith("UCX_")]

export_coll = bpy.data.collections.get("COL_Export")
if export_coll is not None:
    for o in visual + collision:
        if o.name not in export_coll.objects:
            export_coll.objects.link(o)


def shift(meshes, delta):
    seen = set()
    for o in meshes:
        if o.data.name in seen:
            continue
        seen.add(o.data.name)
        o.data.transform(Matrix.Translation(delta))
        o.data.update()


def select(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]


shift(visual + collision, -PIVOT)

select(visual)
glb = os.path.join(OUT, SLUG + ".glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True,
                          export_apply=True, export_yup=True,
                          export_materials='EXPORT', export_cameras=False,
                          export_lights=False)

select(visual + collision)
fbx = os.path.join(OUT, SLUG + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH'},
                         apply_unit_scale=True, global_scale=1.0,
                         apply_scale_options='FBX_SCALE_NONE',
                         axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                         mesh_smooth_type='FACE', bake_anim=False)

shift(visual + collision, PIVOT)

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, SLUG + ".blend"))

result = {
    "collision": built,
    "pivot": list(PIVOT),
    "glb": {"bytes": os.path.getsize(glb), "meshes": len(visual)},
    "fbx": {"bytes": os.path.getsize(fbx), "meshes": len(visual),
            "collision": len(collision)},
}
print("EXPORT:", result)
