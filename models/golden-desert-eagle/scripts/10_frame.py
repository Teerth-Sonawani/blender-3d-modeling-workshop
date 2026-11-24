"""Gate 01 — Frame.

Six machined gold solids joined into SM_Frame_A:
  grip core, frame rail strip, dust cover, beavertail tang, U trigger guard,
  ported butt lip.

Measured targets (m): grip back 0.023, front strap 0.090, guard opening
0.0958..0.1368 x z 0.0745..0.1010, dust cover front 0.1545, beavertail top
0.1442, frame width 0.026.
"""

import importlib
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (col, clear_collection, join, mat, profile, box, report,  # noqa: E402
                    mesh_health, save, text_to_mesh, place_engraving, boolean)

for junk in [o for o in bpy.data.objects if o.name.startswith("DIAG_")]:
    bpy.data.objects.remove(junk, do_unlink=True)

C = "COL_Part_Frame"
clear_collection(C)
for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False
GOLD = mat("MAT_Gold_TitaniumGold")
print("gold material:", GOLD.name if GOLD else None)

parts = []

# 1. grip core -----------------------------------------------------------------
grip_pts = [
    (0.0900, 0.1060),
    (0.0900, 0.0980),
    (0.0888, 0.0860),
    (0.0862, 0.0690),
    (0.0822, 0.0490),
    (0.0772, 0.0280),
    (0.0742, 0.0140),
    (0.0730, 0.0060),
    (0.0310, 0.0060),
    (0.0282, 0.0210),
    (0.0258, 0.0450),
    (0.0242, 0.0700),
    (0.0232, 0.0900),
    (0.0230, 0.1060),
]
parts.append(profile("SM_Frame_GripCore", grip_pts, 0.0260, C, GOLD,
                     bevel=0.0018, bevel_segments=3))

# 2. frame rail strip under the slide -------------------------------------------
strip_pts = [
    (0.0215, 0.0995),
    (0.1550, 0.0995),
    (0.1550, 0.1120),
    (0.0215, 0.1120),
]
parts.append(profile("SM_Frame_RailStrip", strip_pts, 0.0260, C, GOLD,
                     bevel=0.0012, bevel_segments=2))

# 3. dust cover (slanted nose) --------------------------------------------------
dust_pts = [
    (0.1368, 0.1120),
    (0.1545, 0.1120),
    (0.1545, 0.1042),
    (0.1490, 0.0972),
    (0.1395, 0.0965),
    (0.1368, 0.0985),
]
dust = profile("SM_Frame_DustCover", dust_pts, 0.0240, C, GOLD,
               bevel=0.0016, bevel_segments=3)

# Serial number engraved here, while the dust cover is still a single manifold
# solid: the joined frame is a multi-volume mesh and EXACT booleans on it clip
# whole shells (verified: a serial cut removed the beavertail).
CUT = "COL_Cutters"
clear_collection(CUT)
serial = text_to_mesh("SM_Frame_SerialCut", "DE50TG0142", 0.0017,
                      (0.1456, 0.0126, 0.1008), (1.5707963, 0.0, 3.14159265),
                      0.0006, 0.95, CUT)
place_engraving(serial, 0.0120, 0.00020, 1)
boolean(dust, serial)
parts.append(dust)

# 4. beavertail tang ------------------------------------------------------------
tang_pts = [
    (0.0310, 0.0970),
    (0.0240, 0.1010),
    (0.0182, 0.1110),
    (0.0132, 0.1205),
    (0.0102, 0.1288),
    (0.0108, 0.1352),
    (0.0158, 0.1402),
    (0.0228, 0.1424),
    (0.0302, 0.1428),
    (0.0352, 0.1406),
    (0.0386, 0.1342),
    (0.0402, 0.1230),
    (0.0425, 0.1128),
    (0.0392, 0.1034),
]
parts.append(profile("SM_Frame_Beavertail", tang_pts, 0.0225, C, GOLD,
                     bevel=0.0013, bevel_segments=3))

# 5. U trigger guard ------------------------------------------------------------
guard_pts = [
    (0.0900, 0.1000),
    (0.0912, 0.0900),
    (0.0940, 0.0800),
    (0.0990, 0.0722),
    (0.1060, 0.0695),
    (0.1200, 0.0693),
    (0.1290, 0.0710),
    (0.1345, 0.0770),
    (0.1368, 0.0870),
    (0.1370, 0.1000),
    (0.1337, 0.1000),
    (0.1335, 0.0870),
    (0.1300, 0.0790),
    (0.1245, 0.0755),
    (0.1060, 0.0750),
    (0.1005, 0.0772),
    (0.0970, 0.0850),
    (0.0974, 0.1000),
]
parts.append(profile("SM_Frame_TriggerGuard", guard_pts, 0.0190, C, GOLD,
                     bevel=0.0011, bevel_segments=3))

# 6. butt lip / magwell flare ---------------------------------------------------
parts.append(box("SM_Frame_ButtLip", 0.0295, 0.0745, -0.0152, 0.0152,
                 0.0000, 0.0076, C, GOLD, bevel=0.0016, bevel_segments=3))

frame = join(parts, "SM_Frame_A")
report(frame)
print("frame materials:", [m.name for m in frame.data.materials])
mesh_health(frame)
print("FRAME OBJECTS:", [o.name for o in col(C).objects])
save()
