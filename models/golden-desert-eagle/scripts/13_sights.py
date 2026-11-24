"""Gate 04 — Sights.

Front: 11.0 x 5.5 mm black fin on the rail, slanted rear face, x 0.2554..0.2666.
Rear: 10.5 mm long x 8.5 mm tall black squared notch sight, x 0.0455..0.0570,
notch 3.4 mm wide x 4.6 mm deep. Sight radius 0.215 m.
"""

import importlib
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (boolean, box, clear_collection, join, mat, mesh_health,  # noqa: E402
                    profile, report, save)

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False

C = "COL_Part_Sights"
CUT = "COL_Cutters"
clear_collection(C)
clear_collection(CUT)
BLACK = mat("MAT_Sight_Black")
RAIL_TOP = 0.1500

parts = []

# front sight: fin with a slanted rear and a dovetail base
front = profile("SM_Sight_Front", [
    (0.2554, 0.1494),
    (0.2666, 0.1494),
    (0.2666, 0.1554),
    (0.2604, 0.1554),
    (0.2554, 0.1518),
], 0.0034, C, BLACK, bevel=0.0011, bevel_segments=3)
parts.append(front)
parts.append(box("SM_Sight_FrontBase", 0.2548, 0.2672, -0.0042, 0.0042,
                 0.1478, 0.1496, C, BLACK, bevel=0.0008, bevel_segments=2))

# rear sight: squared block, slanted rear top, notch cut after joining
rear = profile("SM_Sight_Rear", [
    (0.0455, 0.1494),
    (0.0570, 0.1494),
    (0.0570, 0.1560),
    (0.0538, 0.1579),
    (0.0455, 0.1579),
], 0.0128, C, BLACK, bevel=0.0011, bevel_segments=3)
parts.append(rear)
parts.append(box("SM_Sight_RearBase", 0.0448, 0.0578, -0.0072, 0.0072,
                 0.1478, 0.1496, C, BLACK, bevel=0.0008, bevel_segments=2))

sights = join(parts, "SM_Sights_A")

cut = box("SM_Cutter_RearNotch", 0.0430, 0.0600, -0.0017, 0.0017,
          0.1524, 0.1600, CUT, bevel=0.0002, bevel_segments=1)
boolean(sights, cut)

report(sights)
mesh_health(sights)
print("sight materials:", [m.name for m in sights.data.materials])
print("sight radius mm:", round((0.2655 - 0.0505) * 1000, 1))
save()
