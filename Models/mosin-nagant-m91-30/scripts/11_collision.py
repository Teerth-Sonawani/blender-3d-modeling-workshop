"""Mosin M91/30 — rebuild the UCX collision proxies.

The delivered UCX_Stock_Butt / UCX_Receiver / UCX_Forend_Barrel / UCX_Barrel_Front
were all clustered within x -0.22..0.22, z +-0.0625 around the origin: a 0.44 m
envelope for a 1.235 m rifle, so they enclosed almost nothing.  The FBX also
shipped without them, so the exports carried no collision at all.

These are hand-authored boxes, not vertex fits: fitting to every vertex in an
x window pulls the hulls out to the sling rings and the bolt knob and produces
82 mm-wide "receiver" boxes.  Collision proxies are authored, so each box is
sized from the measured part layout and kept tight:

  UCX_Stock_Butt     x -0.619 .. -0.291   y +-0.020   z -0.004 .. 0.128
  UCX_Receiver       x -0.331 .. -0.039   y -0.062 .. 0.022 (incl. bolt knob)
                                             z  0.042 .. 0.099
  UCX_Forend_Barrel  x -0.039 ..  0.472   y +-0.025   z  0.023 .. 0.093
  UCX_Barrel_Front   x  0.472 ..  0.619   y +-0.013   z  0.058 .. 0.088

Naming follows the Unreal convention: UCX_<Part> for one hull per part.
"""
import bpy
import bmesh
from mathutils import Vector

# name, x_min, x_max, y_min, y_max, z_min, z_max   (metres)
BOXES = [
    ("UCX_Stock_Butt", -0.619, -0.291, -0.020, 0.020, -0.004, 0.128),
    ("UCX_Receiver", -0.331, -0.039, -0.062, 0.022, 0.042, 0.099),
    ("UCX_Forend_Barrel", -0.039, 0.472, -0.025, 0.025, 0.023, 0.093),
    ("UCX_Barrel_Front", 0.472, 0.619, -0.013, 0.013, 0.058, 0.088),
]
INFLATE = 0.0010


def make_box(name, x0, x1, y0, y1, z0, z1):
    lo = Vector((x0, y0, z0)) - Vector((INFLATE, INFLATE, INFLATE))
    hi = Vector((x1, y1, z1)) + Vector((INFLATE, INFLATE, INFLATE))
    centre = (lo + hi) / 2.0
    size = hi - lo
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * size.x + centre.x
        v.co.y = v.co.y * size.y + centre.y
        v.co.z = v.co.z * size.z + centre.z
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


for name, *_ in BOXES:
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

built = []
for spec in BOXES:
    ob = make_box(*spec)
    built.append({"name": spec[0],
                  "dims_mm": [round(d * 1000, 1) for d in ob.dimensions]})

proxies = [o for o in bpy.data.objects if o.name.startswith("UCX_") and o.type == 'MESH']
print("COLLISION:", {"proxies": built,
                     "total_tris": sum(len(p.vertices) - 2 for o in proxies
                                       for p in o.data.polygons)})
