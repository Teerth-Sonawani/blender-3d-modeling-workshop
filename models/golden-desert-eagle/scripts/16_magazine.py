"""Gate 07 — Magazine.

Black magazine floorplate / baseplate visible at the bottom rear of the grip,
proud of the gold flare by ~2 mm.

Measured: black plate x 0.032..0.080, z 0.0024..0.0057; the baseplate protrudes
rearward past the gold grip lip.
"""

import importlib
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (box, clear_collection, join, mat, mesh_health, profile,  # noqa: E402
                    report, save)

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False

C = "COL_Part_Magazine"
clear_collection(C)
BLACK = mat("MAT_Black_Metal")
parts = []

# floorplate across the grip bottom
parts.append(box("SM_Mag_Floorplate", 0.0286, 0.0800, -0.0161, 0.0161,
                 0.0004, 0.0046, C, BLACK, bevel=0.0008, bevel_segments=2))

# rear baseplate tab, a small step behind the gold lip
parts.append(profile("SM_Mag_BaseplateTab", [
    (0.0266, 0.0012),
    (0.0286, 0.0012),
    (0.0286, 0.0050),
    (0.0272, 0.0058),
    (0.0262, 0.0050),
], 0.0290, C, BLACK, bevel=0.0005, bevel_segments=2))

mag = join(parts, "SM_Magazine_A")
report(mag)
mesh_health(mag)
print("mag materials:", [m.name for m in mag.data.materials])
save()
