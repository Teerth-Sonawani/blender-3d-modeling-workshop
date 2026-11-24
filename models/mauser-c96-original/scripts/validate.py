"""Validation report for the C96 (runs inside Blender via MCP)."""
import bpy
import bmesh
from mathutils import Vector

GEO = bpy.data.collections["COL_Geo"]

meshes = sorted([o for o in GEO.objects if o.type == "MESH"
                 and not o.name.startswith("SM_Ground")], key=lambda o: o.name)

total_tris = 0
total_verts = 0
non_manifold = 0
loose = 0
degenerate = 0
bad_transform = []
no_uv = []
mats = set()

print("=== VALIDATION ===")
for o in meshes:
    me = o.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    total_tris += tris
    total_verts += len(me.vertices)
    for m in me.materials:
        if m:
            mats.add(m.name)
    if not me.uv_layers:
        no_uv.append(o.name)
    if (tuple(round(v, 6) for v in o.location) != (0, 0, 0)
            or tuple(round(v, 6) for v in o.scale) != (1, 1, 1)):
        bad_transform.append(o.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    lv = sum(1 for v in bm.verts if not v.link_faces)
    dg = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    non_manifold += nm
    loose += lv
    degenerate += dg
    bm.free()
    print(f"  {o.name:34s} tris {tris:6d}  mats {len(me.materials)}  uv {len(me.uv_layers)}"
          f"  open edges {nm:4d}  loose {lv}  degenerate {dg}")

lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for o in meshes:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])

print("\nTOTAL TRIS", total_tris)
print("TOTAL VERTS", total_verts)
print("OBJECTS", len(meshes))
print("MATERIALS", sorted(mats))
print(f"DIMENSIONS length {((hi.x-lo.x)*1000):.1f} mm  width {((hi.y-lo.y)*1000):.1f} mm  "
      f"height {((hi.z-lo.z)*1000):.1f} mm")
print(f"Z RANGE {lo.z*1000:.1f}..{hi.z*1000:.1f} mm (bore axis at 0)")
print("OPEN/NON-MANIFOLD EDGES", non_manifold, " LOOSE VERTS", loose, " DEGENERATE", degenerate)
print("NO UV", no_uv if no_uv else "none")
print("BAD TRANSFORMS", bad_transform if bad_transform else "none")
print("VERDICT", "PASS" if (not no_uv and not bad_transform and degenerate == 0) else "REVIEW")
