"""Gate 05 — Controls.

Ambidextrous two-lobe safety on a slotted round boss with red indicator dot,
low exposed hammer spur, curved trigger blade, takedown pin and frame pin.

Measured: safety plate x 0.0415..0.0625, z 0.1265..0.1420, boss Ø 9.4 mm at
(0.0545, 0.1360); hammer spur reaches x 0.000, z 0.1015..0.1135; trigger face
x ~0.100 inside the guard opening.
"""

import importlib
import math
import sys

import bpy
from mathutils import Matrix, Vector

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (boolean, box, clear_collection, cylinder, join, mat,  # noqa: E402
                    mesh_health, profile, report, rounded_rect, save)

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False

C = "COL_Part_Controls"
CUT = "COL_Cutters"
clear_collection(C)
clear_collection(CUT)
GOLD = mat("MAT_Gold_TitaniumGold")
BLACK = mat("MAT_Black_Metal")
RED = mat("MAT_Red_Indicator")

parts = []

# --- safety plate + boss + lever, both sides ----------------------------------
for side, sgn in (("R", 1.0), ("L", -1.0)):
    y_face = sgn * 0.0160
    plate = profile(f"SM_Ctrl_SafetyPlate{side}",
                    rounded_rect(0.0432, 0.0608, 0.1274, 0.1410, 0.0026, 6),
                    0.0006, C, GOLD, y_center=y_face + sgn * 0.00030,
                    bevel=0.00020, bevel_segments=1)
    parts.append(plate)

    boss = cylinder(f"SM_Ctrl_SafetyBoss{side}", 0.0042, 0.0013,
                    (0.0545, y_face + sgn * 0.0013, 0.1360), "Y", C, GOLD,
                    segments=36, bevel=0.00035, bevel_segments=2)
    parts.append(boss)

    lever = profile(f"SM_Ctrl_SafetyLever{side}", [
        (0.0622, 0.1342),
        (0.0598, 0.1372),
        (0.0538, 0.1394),
        (0.0432, 0.1414),
        (0.0358, 0.1418),
        (0.0332, 0.1392),
        (0.0362, 0.1368),
        (0.0482, 0.1348),
        (0.0558, 0.1328),
    ], 0.0011, C, GOLD, y_center=y_face + sgn * 0.0012,
        bevel=0.00025, bevel_segments=2)
    parts.append(lever)

    pad = cylinder(f"SM_Ctrl_SafetyPad{side}", 0.0015, 0.0007,
                   (0.0384, y_face + sgn * 0.0018, 0.1398), "Y", C, GOLD,
                   segments=24, bevel=0.0002, bevel_segments=1)
    parts.append(pad)

    dot = cylinder(f"SM_Ctrl_RedDot{side}", 0.0008, 0.0006,
                   (0.0450, y_face + sgn * 0.0015, 0.1286), "Y", C, RED,
                   segments=20, bevel=0.0001, bevel_segments=1)
    parts.append(dot)

# --- hammer spur ---------------------------------------------------------------
hammer = profile("SM_Ctrl_Hammer", [
    (0.0210, 0.1055),
    (0.0130, 0.1024),
    (0.0042, 0.1024),
    (0.0006, 0.1046),
    (0.0016, 0.1088),
    (0.0090, 0.1122),
    (0.0168, 0.1128),
    (0.0205, 0.1102),
], 0.0066, C, GOLD, bevel=0.0007, bevel_segments=2)
parts.append(hammer)

# --- trigger blade -------------------------------------------------------------
trigger = profile("SM_Ctrl_Trigger", [
    (0.0998, 0.0994),
    (0.1052, 0.0972),
    (0.1062, 0.0880),
    (0.1038, 0.0802),
    (0.0996, 0.0794),
    (0.0968, 0.0852),
    (0.0972, 0.0952),
], 0.0062, C, GOLD, bevel=0.0005, bevel_segments=2)
parts.append(trigger)

# --- takedown pin + frame pin (both sides) ------------------------------------
for side, sgn in (("R", 1.0), ("L", -1.0)):
    parts.append(cylinder(f"SM_Ctrl_TakedownPin{side}", 0.0040, 0.0018,
                          (0.1292, sgn * 0.0129, 0.1062), "Y", C, GOLD,
                          segments=32, bevel=0.0003, bevel_segments=2))
    parts.append(cylinder(f"SM_Ctrl_FramePin{side}", 0.0022, 0.0014,
                          (0.1168, sgn * 0.0129, 0.1046), "Y", C, GOLD,
                          segments=24, bevel=0.0002, bevel_segments=1))

# --- magazine release (left side) ---------------------------------------------
parts.append(cylinder("SM_Ctrl_MagRelease", 0.0028, 0.0020,
                      (0.0948, -0.0134, 0.0872), "Y", C, GOLD,
                      segments=28, bevel=0.0003, bevel_segments=2))

controls = join(parts, "SM_Controls_A")

# safety boss screw slot (both sides) + trigger guard clearance
for side, sgn in (("R", 1.0), ("L", -1.0)):
    cut = box(f"SM_Cutter_BossSlot{side}", 0.0508, 0.0582,
              sgn * 0.0170, sgn * 0.0186, 0.13578, 0.13622, CUT,
              bevel=0.00012, bevel_segments=1)
    boolean(controls, cut)

report(controls)
mesh_health(controls)
print("control materials:", [m.name for m in controls.data.materials])
save()
