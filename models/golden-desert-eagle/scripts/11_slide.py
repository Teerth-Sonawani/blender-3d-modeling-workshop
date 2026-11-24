"""Gate 02 — Slide.

One lofted, manifold solid swept along X from the measured cross-section, then
machined with booleans: rear-top chamfer, front-bottom chamfer, 8 picatinny
slots, 14 + 4 slide serrations per side, long side relief grooves, ejection
port pocket, muzzle relief notch and the barrel counterbore.

Measured targets (m): x 0.030..0.273, z 0.1068..0.1500, width 0.032,
rail 0.021 wide, 8 slots @ 5.0 mm with 10.9 mm pitch from x 0.158..0.240.
"""

import importlib
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (bevel_edges, boolean, box, col, clear_collection, comb,  # noqa: E402
                    cylinder, make_object, mat, mesh_health, profile, report, save,
                    _finish)
importlib.reload(de_lib)

C = "COL_Part_Slide"
CUT = "COL_Cutters"
clear_collection(C)
clear_collection(CUT)
GOLD = mat("MAT_Gold_TitaniumGold")

X0, X1 = 0.0300, 0.2730
W2 = 0.0160
BOT, TOP = 0.1068, 0.1465
BORE_Z = 0.1305

# Cross-section, CCW in (y, z): bottom, sides, 4 mm top chamfer, 21 mm rail.
section = [
    (-0.0152, BOT),
    (0.0152, BOT),
    (W2, BOT + 0.0008),
    (W2, 0.1425),
    (0.0120, TOP),
    (0.0105, TOP),
    (0.0105, 0.1491),
    (0.0096, 0.1500),
    (-0.0096, 0.1500),
    (-0.0105, 0.1491),
    (-0.0105, TOP),
    (-0.0120, TOP),
    (-W2, 0.1425),
    (-W2, BOT + 0.0008),
]

bm = bmesh.new()
a = [bm.verts.new((X0, y, z)) for y, z in section]
b = [bm.verts.new((X1, y, z)) for y, z in section]
bm.faces.new(a)
bm.faces.new(list(reversed(b)))
n = len(section)
for i in range(n):
    j = (i + 1) % n
    bm.faces.new([a[i], a[j], b[j], b[i]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# Break the long edges so the slab catches light, then clean the end corners.
bevel_edges(bm, list(bm.edges), 0.00035, segments=1)
_finish(bm, 32.0)
me = bpy.data.meshes.new("SM_Slide_A")
bm.to_mesh(me)
bm.free()
slide = bpy.data.objects.new("SM_Slide_A", me)
col(C).objects.link(slide)
me.materials.append(GOLD)
print("loft tris:", sum(len(p.vertices) - 2 for p in me.polygons))

# 1. rear-top chamfer -----------------------------------------------------------
cut = profile("SM_Cutter_RearTop", [
    (0.0200, 0.1335), (0.0600, 0.1540), (0.0200, 0.1600),
], 0.045, CUT, bevel=0.0)
boolean(slide, cut)

# 2. front-bottom chamfer -------------------------------------------------------
cut = profile("SM_Cutter_FrontBottom", [
    (0.2570, 0.1044), (0.2760, 0.1126), (0.2760, 0.0940), (0.2570, 0.0940),
], 0.045, CUT, bevel=0.0)
boolean(slide, cut)

# 3. picatinny slots ------------------------------------------------------------
centres = [0.2375 - i * 0.01093 for i in range(8)]
cut = comb("SM_Cutter_RailSlots", centres, 0.0050, 0.1472, 0.1560,
           -0.0120, 0.0120, CUT)
boolean(slide, cut)
print("rail slots:", len(centres), [round(c * 1000, 1) for c in centres])

# 4. slide serrations: 14 forward + 4 rear, both sides --------------------------
front = [0.0985 - i * 0.00260 for i in range(16)]
rear = [0.0438 - i * 0.00280 for i in range(4)]
for side, (y0, y1) in (("R", (0.0146, 0.0190)), ("L", (-0.0190, -0.0146))):
    for group, xs in (("Front", front), ("Rear", rear)):
        cut = comb(f"SM_Cutter_Serr{group}{side}", xs, 0.0010, 0.1114, 0.1428,
                   y0, y1, CUT, slant_deg=9.0, cx=0.070, cz=0.1265)
        boolean(slide, cut)
print("serrations per side:", len(front) + len(rear))

# 5. long side relief grooves ---------------------------------------------------
for side, (y0, y1) in (("R", (0.0153, 0.0185)), ("L", (-0.0185, -0.0153))):
    cut = box(f"SM_Cutter_SideGroove{side}", 0.1462, 0.2652, y0, y1,
              0.1318, 0.1346, CUT, bevel=0.0007, bevel_segments=2)
    boolean(slide, cut)

# 6. ejection port pocket (right side only; barrel block fills it) -------------
cut = box("SM_Cutter_Port", 0.1380, 0.1790, 0.0090, 0.0195,
          0.1165, 0.1408, CUT, bevel=0.0008, bevel_segments=2)
boolean(slide, cut)

# 7. muzzle relief notch --------------------------------------------------------
cut = box("SM_Cutter_MuzzleNotch", 0.2560, 0.2665, -0.0063, 0.0063,
          0.1060, 0.1132, CUT, bevel=0.0008, bevel_segments=2)
boolean(slide, cut)

# 8. barrel counterbore ---------------------------------------------------------
cut = cylinder("SM_Cutter_Bore", 0.0117, 0.026, (0.2620, 0.0, BORE_Z), "X",
               CUT, segments=64, bevel=0.0)
boolean(slide, cut)

report(slide)
mesh_health(slide)
print("slide objects:", [o.name for o in col(C).objects])
save()
