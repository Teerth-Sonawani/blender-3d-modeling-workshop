"""Gate 08 — Marks (slide).

The slide carries an etched, dark-filled rollmark:

  both sides: "DESERT EAGLE PISTOL®" / "MADE IN USA", and ".50AE" at the front.

These are real letter meshes extruded 0.10 mm and set 0.06 mm proud of the flank
with the dark etch material. The earlier boolean pocket was abandoned: the
letter-shaped holes left long sliver faces on the flat flank that shaded as
creased foil even after weighted normals, and the reference marks read as dark
etching against gold far more than as a deep relief.

The frame serial is engraved in 10_frame.py (the joined frame is multi-volume
and must not be booleaned).
"""

import importlib
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import col, place_engraving, report, save, text_to_mesh  # noqa: E402

C = "COL_Part_Marks"
for ob in list(col(C).objects):
    bpy.data.objects.remove(ob, do_unlink=True)

MARK = bpy.data.materials.get("MAT_Mark_Etch")
if MARK is None:
    MARK = bpy.data.materials.new("MAT_Mark_Etch")
    MARK.use_nodes = True
    b = next(n for n in MARK.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.02, 0.014, 0.008, 1.0)
    b.inputs["Metallic"].default_value = 0.35
    b.inputs["Roughness"].default_value = 0.42

slide = bpy.data.objects["SM_Slide_A"]
print("slide tris:", de_lib.tri_count(slide))

ROLL_Z, MADE_Z, CAL_X = 0.1198, 0.1146, 0.2590
FLANK = 0.0160          # slide flank plane, half-width
PROUD = 0.00006         # 60 um of letter stands above the flank
DEPTH = PROUD + 0.00004  # buried portion, so no coplanar faces

marks = []
for side, sgn in (("R", 1.0), ("L", -1.0)):
    rot = (1.5707963, 0.0, 0.0 if sgn < 0 else 3.14159265)
    y0 = sgn * FLANK
    specs = (
        ("Roll", "DESERT EAGLE PISTOL\u00ae", 0.0032, 0.1480, ROLL_Z, 0.062, 1.30),
        ("Made", "MADE IN USA", 0.0028, 0.1480, MADE_Z, 0.036, 1.36),
        ("Cal", ".50AE", 0.0030, CAL_X, 0.1218, 0.017, 1.08),
    )
    for nm, txt, size, x, z, width, track in specs:
        ob = text_to_mesh(f"SM_Marks_{nm}{side}", txt, size, (x, y0, z), rot,
                          0.00010, track, C, width)
        place_engraving(ob, y0, DEPTH, 1 if sgn > 0 else -1)
        ob.data.materials.clear()
        ob.data.materials.append(MARK)
        marks.append(ob)

for ob in marks:
    print(f"  {ob.name}: width {ob.dimensions.x*1000:.1f}mm "
          f"height {ob.dimensions.z*1000:.1f}mm "
          f"y {min((ob.matrix_world @ v.co).y for v in ob.data.vertices)*1000:.3f}"
          f"..{max((ob.matrix_world @ v.co).y for v in ob.data.vertices)*1000:.3f}mm")

print("mark objects:", len(marks))
report(slide)
save()
