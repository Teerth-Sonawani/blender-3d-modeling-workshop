"""Mosin M91/30 — rebuild the trigger as one curved solid blade.

Replaces SM_Trigger_Top / SM_Trigger_Mid / SM_Trigger_Bot (three disconnected
8-vertex boxes that read as floating plates) with a single swept blade.

Canon: M91/30 trigger is a flat ~3 mm steel blade, 5 mm wide, dropping ~25 mm
from the sear housing and sweeping rearward, with a curled tip.  Coordinates
are taken from the existing receiver / guard measurements in this scene:
  receiver slab bottom   z 0.046
  guard bow              x -0.2026 .. -0.1067,  z 0.013 .. 0.0323
Blade therefore runs z 0.049 (3 mm into the receiver) down to z 0.024 (inside
the guard bow opening), front edge x -0.161 -> -0.173.

Run from Blender (MCP execute_blender_code: exec(open(path).read())).
"""
import bpy
import bmesh

OLD = ["SM_Trigger_Top", "SM_Trigger_Mid", "SM_Trigger_Bot"]
NEW = "SM_Trigger_Blade"

# Silhouette in XZ. Front edge runs down from the receiver, then the rear
# edge climbs back up: one closed loop, so the blade is a single solid.
FRONT = [(-0.1612, 0.0490), (-0.1622, 0.0440), (-0.1642, 0.0380),
         (-0.1668, 0.0320), (-0.1698, 0.0270), (-0.1726, 0.0240)]
REAR = [(-0.1760, 0.0245), (-0.1724, 0.0290), (-0.1696, 0.0340),
        (-0.1674, 0.0400), (-0.1652, 0.0460), (-0.1640, 0.0490)]
OUTLINE = FRONT + REAR
WIDTH = 0.0050          # blade width across the bore axis (5 mm, matches spec)
BEVEL = 0.00035         # edge break so the blade catches a highlight


def remove_old():
    removed = []
    for name in OLD:
        ob = bpy.data.objects.get(name)
        if ob:
            removed.append(name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return removed


def build_blade():
    me = bpy.data.meshes.new(NEW)
    bm = bmesh.new()
    verts = [bm.verts.new((x, 0.0, z)) for x, z in OUTLINE]
    face = bm.faces.new(verts)
    face.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.validate()

    ob = bpy.data.objects.new(NEW, me)
    for coll in ("COL_Geo", "COL_Export"):
        c = bpy.data.collections.get(coll)
        if c and ob.name not in c.objects:
            c.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)

    # 5 mm wide solid: solidify symmetrically around the profile plane.
    solid = ob.modifiers.new("Solidify", 'SOLIDIFY')
    solid.thickness = WIDTH
    solid.offset = 0.0
    solid.use_even_offset = True

    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=solid.name)

    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = BEVEL
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = 0.52
    bpy.ops.object.modifier_apply(modifier=bev.name)

    mat = bpy.data.materials.get("MAT_Steel_Blued")
    if mat:
        ob.data.materials.append(mat)

    try:
        bpy.ops.object.shade_smooth_by_angle(angle=0.61)
    except Exception:
        pass

    root = bpy.data.objects.get("SM_MosinNagant_Root")
    if root:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    ob.select_set(False)
    return ob


removed = remove_old()
blade = build_blade()

tris = sum(len(p.vertices) - 2 for p in blade.data.polygons)
result = {
    "removed": removed,
    "object": blade.name,
    "tris": tris,
    "verts": len(blade.data.vertices),
    "dims_mm": [round(d * 1000, 2) for d in blade.dimensions],
    "location": [round(v, 4) for v in blade.location],
    "materials": [m.name for m in blade.data.materials],
    "collections": [c.name for c in blade.users_collection],
}
print("TRIGGER BLADE:", result)
