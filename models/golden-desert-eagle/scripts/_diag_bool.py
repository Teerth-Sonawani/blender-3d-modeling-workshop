"""Diagnostic: which boolean path actually applies in this Blender/sandbox?"""

import bmesh
import bpy


def cube(name, size, loc):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


target = cube("DIAG_target", 0.1, (0, 0, 0))
cutter = cube("DIAG_cutter", 0.1, (0.05, 0, 0))

mod = target.modifiers.new("b", "BOOLEAN")
mod.operation = "DIFFERENCE"
mod.object = cutter
mod.solver = "EXACT"
print("operand_type:", getattr(mod, "operand_type", "n/a"))
print("object set:", mod.object.name if mod.object else None)
print("target verts before:", len(target.data.vertices))

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = target.evaluated_get(dg)
print("ev is target:", ev == target)
print("ev modifiers:", [(m.name, m.type) for m in ev.modifiers])

try:
    tmp = ev.to_mesh()
    print("path1 ev.to_mesh verts:", len(tmp.vertices))
    ev.to_mesh_clear()
except Exception as exc:
    print("path1 failed:", exc)

try:
    me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    print("path2 new_from_object(depsgraph) verts:", len(me.vertices))
except Exception as exc:
    print("path2 failed:", exc)

try:
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print("path3 operator ok, verts:", len(target.data.vertices))
except Exception as exc:
    print("path3 failed:", type(exc).__name__, exc)

print("final verts:", len(target.data.vertices))
print("final dims:", tuple(round(v, 4) for v in target.dimensions))
