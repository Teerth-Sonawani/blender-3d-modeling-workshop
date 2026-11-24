"""UV unwrap + pack for every mesh in COL_Geo (runs inside Blender via MCP)."""
import bpy
import bmesh
import math
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")
GEO = bpy.data.collections["COL_Geo"]

if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

report = []
for ob in sorted(GEO.objects, key=lambda o: o.name):
    if ob.type != "MESH":
        continue
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    ok = True
    try:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66.0),
                                 island_margin=0.0035,
                                 correct_aspect=True,
                                 scale_to_bounds=False)
        bpy.ops.uv.pack_islands(margin=0.0035, rotate=True)
        bpy.ops.object.mode_set(mode="OBJECT")
    except Exception as exc:
        ok = False
        print("SMART PROJECT FAILED", ob.name, exc)
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        # fallback: per-face planar projection on the dominant axis
        me = ob.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uvl = me.uv_layers[0]
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        uvlayer = bm.loops.layers.uv.verify()
        s = 1.0 / 0.30
        for f in bm.faces:
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            for loop in f.loops:
                co = loop.vert.co
                if ax == 0:
                    u, v = co.y, co.z
                elif ax == 1:
                    u, v = co.x, co.z
                else:
                    u, v = co.x, co.y
                loop[uvlayer].uv = (u * s + 0.5, v * s + 0.5)
        bm.to_mesh(me)
        bm.free()
    me = ob.data
    area = 0.0
    if me.uv_layers:
        uvl = me.uv_layers[0].data
        for poly in me.polygons:
            pts = [uvl[li].uv for li in poly.loop_indices]
            a = 0.0
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                a += x1 * y2 - x2 * y1
            area += abs(a) * 0.5
    report.append((ob.name, len(me.uv_layers), area, ok))

print("UV REPORT  (uv_layers, uv area used, smart_project ok)")
for name, nlayer, area, ok in report:
    print(f"  {name:34s} layers={nlayer} coverage={area*100:5.1f}%  {'smart' if ok else 'fallback'}")

bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
