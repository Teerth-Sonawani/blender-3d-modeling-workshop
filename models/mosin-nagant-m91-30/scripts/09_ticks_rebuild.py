"""Mosin M91/30 — rebuild the 20 rear-sight graduation ticks.

The delivered SM_RearSight_Tick_01..20 carried an un-applied object scale
(mesh 1.0 m long, object scale ~0.0116).  Setting scale.y to shorten them
instead stretched each tick to 400 mm, which is what put 20 long rods across
the detail render.

They are rebuilt here as 12-triangle boxes with the geometry in world space and
the object transform left at identity, so nothing can rescale them later:
  tick     1.1 x 4.6 x 1.2 mm
  pitch    3.9 mm, 20 ticks spanning x -0.0221 .. 0.0520
  proud    0.5 mm above the leaf top face (z 0.0938)
  offset   y -0.0033 (near side); the numerals sit on the far (+Y) side
"""
import bpy
import bmesh

COUNT = 20
X_START = -0.0221
X_END = 0.0520
Y_CENTER = -0.0033
Z_CENTER = 0.0937
SIZE = (0.0011, 0.0046, 0.0012)
MAT = "MAT_Steel_Marked"


def remove_ticks():
    gone = []
    for i in range(1, COUNT + 1):
        ob = bpy.data.objects.get("SM_RearSight_Tick_%02d" % i)
        if ob:
            gone.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return gone


def make_tick(name, cx, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = SIZE
    for v in bm.verts:
        v.co.x = v.co.x * sx + cx
        v.co.y = v.co.y * sy + Y_CENTER
        v.co.z = v.co.z * sz + Z_CENTER
    bm.to_mesh(me)
    bm.free()
    me.validate()

    ob = bpy.data.objects.new(name, me)
    for coll in ("COL_Geo", "COL_Export"):
        c = bpy.data.collections.get(coll)
        if c:
            c.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    root = bpy.data.objects.get("SM_MosinNagant_Root")
    if root:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
    return ob


gone = remove_ticks()
mat = bpy.data.materials.get(MAT)
step = (X_END - X_START) / (COUNT - 1)
made = []
for i in range(COUNT):
    ob = make_tick("SM_RearSight_Tick_%02d" % (i + 1), X_START + i * step, mat)
    made.append(ob)

dims = [round(d * 1000, 2) for d in made[0].dimensions]
result = {
    "removed": len(gone),
    "rebuilt": len(made),
    "tick_dims_mm": dims,
    "first_x_mm": round(made[0].location.x, 5),
    "last_x_mm": round(made[-1].location.x, 5),
    "pitch_mm": round(step * 1000, 2),
    "total_tris": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in made),
}
print("TICKS:", result)
