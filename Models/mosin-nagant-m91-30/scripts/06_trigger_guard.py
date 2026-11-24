"""Mosin M91/30 — rebuild the trigger guard bow as flat stamped steel.

The delivered SM_TriggerGuard_Bow was a swept *round tube* (8.4 mm diameter),
which reads as a bent pipe in close-up.  A real M91/30 guard is a flat strap
(~2.8 mm thick radially, ~13 mm wide) bent into a U and riveted to the front
and rear tangs.

This rebuilds the bow as a flat band swept along the centreline the old tube
followed, so the silhouette, the tang joints and the rivet positions are
unchanged:
  bow extent   x -0.2026 .. -0.1067,  z 0.013 .. 0.0323
  front tang   x -0.1433 .. -0.0688,  z 0.025 .. 0.035   (bow end sits inside)
  rear  tang   x -0.2064 .. -0.1945,  z 0.026 .. 0.038   (bow end sits inside)

Run from Blender (MCP execute_blender_code: exec(open(path).read())).
"""
import bpy
import bmesh
from mathutils import Vector

OLD = "SM_TriggerGuard_Bow"
NEW = "SM_TriggerGuard_Bow"

# Centreline of the bow, front (muzzle side) to rear, in XZ.
PATH = [(-0.1067, 0.0323), (-0.1072, 0.0290), (-0.1100, 0.0235),
        (-0.1160, 0.0185), (-0.1250, 0.0150), (-0.1350, 0.0132),
        (-0.1450, 0.0128), (-0.1550, 0.0130), (-0.1650, 0.0140),
        (-0.1750, 0.0165), (-0.1840, 0.0205), (-0.1920, 0.0255),
        (-0.1990, 0.0300), (-0.2026, 0.0323)]
RADIAL = 0.0028         # strap thickness, radially (stamped steel)
WIDTH = 0.0130          # strap width across the bore axis
BEVEL = 0.00035


def band_outline():
    """Offset the centreline to both sides; returns one closed loop."""
    half = RADIAL / 2.0
    outer, inner = [], []
    n = len(PATH)
    for i, (x, z) in enumerate(PATH):
        px, pz = PATH[max(i - 1, 0)]
        nx, nz = PATH[min(i + 1, n - 1)]
        tx, tz = nx - px, nz - pz
        length = (tx * tx + tz * tz) ** 0.5 or 1.0
        tx, tz = tx / length, tz / length
        ox, oz = -tz, tx          # outward normal in XZ
        outer.append((x + ox * half, z + oz * half))
        inner.append((x - ox * half, z - oz * half))
    return outer + list(reversed(inner))


def build():
    old = bpy.data.objects.get(OLD)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    me = bpy.data.meshes.new(NEW)
    bm = bmesh.new()
    verts = [bm.verts.new((x, 0.0, z)) for x, z in band_outline()]
    bm.faces.new(verts)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.validate()

    ob = bpy.data.objects.new(NEW, me)
    for coll in ("COL_Geo", "COL_Export"):
        c = bpy.data.collections.get(coll)
        if c:
            c.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)

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

    mat = bpy.data.materials.get("MAT_Steel_Parkerized")
    if mat:
        ob.data.materials.append(mat)

    root = bpy.data.objects.get("SM_MosinNagant_Root")
    if root:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    ob.select_set(False)
    return ob


bow = build()
bb = [bow.matrix_world @ Vector(c) for c in bow.bound_box]
result = {
    "object": bow.name,
    "tris": sum(len(p.vertices) - 2 for p in bow.data.polygons),
    "verts": len(bow.data.vertices),
    "dims_mm": [round(d * 1000, 2) for d in bow.dimensions],
    "bbox_mm": [[round(min(v[i] for v in bb) * 1000, 1) for i in range(3)],
                [round(max(v[i] for v in bb) * 1000, 1) for i in range(3)]],
    "materials": [m.name for m in bow.data.materials],
}
print("GUARD BOW:", result)
