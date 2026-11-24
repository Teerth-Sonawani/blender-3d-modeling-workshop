"""Remove duplicate verts and zero-area faces, then save (from the saved .blend)."""
import bpy, bmesh, os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")
GEO = bpy.data.collections["COL_Geo"]

print("=== CLEANUP ===")
removed_total = 0
for o in sorted(GEO.objects, key=lambda x: x.name):
    if o.type != "MESH" or o.name.startswith("SM_Ground"):
        continue
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    f0, v0 = len(bm.faces), len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-9, edges=bm.edges)
    bad = [f for f in bm.faces if f.calc_area() < 1e-10]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
        removed_total += len(bad)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    if (len(me.polygons), len(me.vertices)) != (f0, v0):
        print(f"  {o.name:34s} faces {f0}->{len(me.polygons)}  verts {v0}->{len(me.vertices)}")
print("degenerate faces removed:", removed_total)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
