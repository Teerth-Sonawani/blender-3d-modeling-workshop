"""Mosin M91/30 — restore clean names after the quality pass.

Parts rebuilt in this pass (rear sight leaf, guard bow, 20 ticks, 4 numerals)
came back with ".001" suffixes because the originals were still holding the
names when the replacements were created, and the numerals kept their
temporary "TMP_" curve names through the text-to-mesh conversion.

Naming rule for this project: SM_ prefix, PascalCase, underscores, no suffixes.
"""
import bpy

renames = {}

# TMP_Num5 -> SM_RearSight_Num5
for o in list(bpy.data.objects):
    if o.name.startswith("TMP_Num"):
        renames[o.name] = "SM_RearSight_Num" + o.name[len("TMP_Num"):]

# SM_Foo.001 -> SM_Foo
for o in list(bpy.data.objects):
    if o.name.startswith("SM_") and o.name.endswith(".001"):
        renames[o.name] = o.name[:-4]

applied, skipped = [], []
for old, new in renames.items():
    ob = bpy.data.objects.get(old)
    if not ob:
        skipped.append((old, "missing"))
        continue
    if bpy.data.objects.get(new):
        skipped.append((old, "target exists"))
        continue
    ob.name = new
    if ob.data is not None and ob.data.name != new:
        ob.data.name = new
    applied.append((old, new))

bpy.context.view_layer.update()

names = sorted(o.name for o in bpy.data.objects
               if o.type == 'MESH' and o.name.startswith(("SM_", "UCX_")))
result = {
    "renamed": applied,
    "skipped": skipped,
    "dirty_names": [n for n in names if n.endswith(".001") or n.startswith("TMP_")],
    "n_meshes": len(names),
}
print("NAMES:", result)
