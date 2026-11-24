"""Gate 03 — Barrel.

Fixed barrel: rectangular chamber block exposed through the ejection port, round
muzzle section, crowned muzzle with a .50 AE bore, and the recoil-spring guide
rod visible at the front bottom.

Measured: breech x 0.121, muzzle 0.273 (152 mm barrel), bore Ø 12.6 mm,
bore axis z 0.1305. Tube OD 21.6 mm, chamber block 25 mm wide.
"""

import importlib
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (boolean, box, clear_collection, col, cylinder, join, mat,  # noqa: E402
                    mesh_health, report, save)

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False

C = "COL_Part_Barrel"
CUT = "COL_Cutters"
clear_collection(C)
clear_collection(CUT)
GOLD = mat("MAT_Gold_TitaniumGold")
BORE_Z = 0.1305

parts = []

# chamber block, fills the ejection port on the right side
parts.append(box("SM_Barrel_Chamber", 0.1340, 0.1820, -0.0128, 0.0112,
                 0.1158, 0.1416, C, GOLD, bevel=0.0007, bevel_segments=2))

# round muzzle section
parts.append(cylinder("SM_Barrel_Tube", 0.0108, 0.1390, (0.2010, 0.0, BORE_Z), "X",
                      C, GOLD, segments=64, bevel=0.0004, bevel_segments=1))

# crown ring
parts.append(cylinder("SM_Barrel_Crown", 0.0114, 0.0075, (0.2668, 0.0, BORE_Z), "X",
                      C, GOLD, segments=64, bevel=0.0005, bevel_segments=2))

# recoil spring guide rod, visible through the muzzle relief notch
parts.append(cylinder("SM_Barrel_GuideRod", 0.0034, 0.0300, (0.2590, 0.0, 0.1138),
                      "X", C, GOLD, segments=32, bevel=0.0004, bevel_segments=2))

barrel = join(parts, "SM_Barrel_A")

# bore + crown chamfer
cut = cylinder("SM_Cutter_Bore50", 0.0063, 0.1300, (0.2110, 0.0, BORE_Z), "X",
               CUT, segments=64, bevel=0.0)
boolean(barrel, cut)

cut = cylinder("SM_Cutter_CrownChamfer", 0.0082, 0.0030, (0.2697, 0.0, BORE_Z), "X",
               CUT, segments=64, bevel=0.0, radius2=0.0066)
boolean(barrel, cut)

report(barrel)
mesh_health(barrel)
print("barrel materials:", [m.name for m in barrel.data.materials])
save()
