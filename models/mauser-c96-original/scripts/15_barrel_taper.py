"""Mauser C96 — rebuild the barrel as a tapered lathe (scene units = metres).

Delivered barrel: a uniform 20.2 mm tube from x 0.1465 to x 0.288, which is why
the side view reads as blockout-grade.  The record already measured the real
thing:

    coaxial barrel, diameter ~20 at the breech collar tapering to ~13.1 at the
    muzzle, with a raised muzzle collar under the front sight

The profile is written in millimetres for readability and converted to metres on
build, because this scene's geometry is authored in metres (the pistol is
0.288 m long) even though the record quotes millimetres.
"""
import bpy
import bmesh
import math
from mathutils import Vector

NAME = "SM_Weapon_C96_Barrel"
SEG = 32
MAT_OUT = "MAT_Metal_Blued_Steel"
MAT_BORE = "MAT_Metal_Bore_Shadow"
MM = 0.001

# (x_mm, radius_mm) — breech collar, shoulder, taper, stepped muzzle collar.
PROFILE_MM = [
    (146.5, 10.10),
    (147.5, 10.10),
    (147.5, 9.40),
    (150.0, 9.40),
    (151.0, 8.90),
    (160.0, 8.55),
    (250.0, 7.05),
    (266.0, 6.60),
    (266.0, 7.35),
    (275.0, 7.35),
    (275.0, 6.60),
    (284.0, 6.55),
    (288.0, 6.55),
]
BORE_R_MM = 3.10
BORE_END_MM = 245.0
MUZZLE_MM = 288.0

PROFILE = [(x * MM, r * MM) for x, r in PROFILE_MM]
BORE_R = BORE_R_MM * MM
BORE_END = BORE_END_MM * MM
MUZZLE_X = MUZZLE_MM * MM


def ring(bm, x, r):
    return [bm.verts.new((x, r * math.cos(a), r * math.sin(a)))
            for a in (2.0 * math.pi * i / SEG for i in range(SEG))]


def bridge(bm, a, b, faces):
    for j in range(SEG):
        k = (j + 1) % SEG
        faces.append(bm.faces.new((a[j], a[k], b[k], b[j])))


def build():
    old = bpy.data.objects.get(NAME)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    me = bpy.data.meshes.new(NAME)
    bm = bmesh.new()
    outer_faces, bore_faces = [], []

    rings = [ring(bm, x, r) for x, r in PROFILE]
    for i in range(len(rings) - 1):
        bridge(bm, rings[i], rings[i + 1], outer_faces)
    outer_faces.append(bm.faces.new(list(reversed(rings[0]))))

    last = rings[-1]
    inner = ring(bm, MUZZLE_X, BORE_R)
    for j in range(SEG):
        k = (j + 1) % SEG
        bore_faces.append(bm.faces.new((last[j], last[k], inner[k], inner[j])))

    bore_rings = [inner, ring(bm, BORE_END, BORE_R)]
    for i in range(len(bore_rings) - 1):
        bridge(bm, bore_rings[i], bore_rings[i + 1], bore_faces)
    bore_faces.append(bm.faces.new(list(bore_rings[-1])))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bore_faces:
        f.material_index = 1
    for f in outer_faces:
        f.material_index = 0

    bm.to_mesh(me)
    bm.free()
    me.validate()

    ob = bpy.data.objects.new(NAME, me)
    coll = bpy.data.collections.get("COL_Geo")
    if coll:
        coll.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)
    for name in (MAT_OUT, MAT_BORE):
        mat = bpy.data.materials.get(name)
        if mat:
            ob.data.materials.append(mat)

    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
    except Exception:
        pass
    ob.select_set(False)
    return ob


ob = build()
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
result = {
    "object": ob.name,
    "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons),
    "verts": len(ob.data.vertices),
    "x_m": [round(min(v.x for v in bb), 4), round(max(v.x for v in bb), 4)],
    "dims_mm": [round(d * 1000, 2) for d in ob.dimensions],
    "materials": [m.name for m in ob.data.materials],
}
print("BARREL:", result)
