"""Gate 06 — Grip.

Black rubber wrap-around grip sleeve: pebbled panels (material bump), three
finger grooves on the front strap, crossed smooth X bands, eagle medallion and a
slotted grip screw. Gold backstrap stays exposed behind the panel.

Measured: panel x 0.030..0.089, z 0.010..0.105, sleeve width 34.6 mm,
medallion Ø 13 mm at panel centre, panel rear edge 7 mm forward of the backstrap.
"""

import importlib
import math
import sys

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import (boolean, box, clear_collection, cylinder, join, mat,  # noqa: E402
                    mesh_health, profile, report, save)

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name == "COL_Cutters":
        c.hide_viewport = False
        c.hide_render = False

C = "COL_Part_Grip"
CUT = "COL_Cutters"
clear_collection(C)
clear_collection(CUT)
RUBBER = mat("MAT_Rubber_Grip")
BLACK = mat("MAT_Black_Metal")
W = 0.0346
HALF = W / 2.0

# panel outline: back edge, bottom, front strap with three finger grooves, top
panel = [
    (0.0316, 0.1045),
    (0.0294, 0.0920),
    (0.0284, 0.0720),
    (0.0288, 0.0500),
    (0.0302, 0.0300),
    (0.0322, 0.0130),
    (0.0330, 0.0098),
    (0.0768, 0.0098),
    (0.0792, 0.0180),
    (0.0762, 0.0242),
    (0.0802, 0.0306),
    (0.0832, 0.0402),
    (0.0844, 0.0462),
    (0.0813, 0.0524),
    (0.0852, 0.0584),
    (0.0872, 0.0682),
    (0.0882, 0.0762),
    (0.0847, 0.0822),
    (0.0882, 0.0882),
    (0.0886, 0.0980),
    (0.0880, 0.1045),
]

sleeve = profile("SM_Grip_Sleeve", panel, W, C, RUBBER, bevel=0.0022,
                 bevel_segments=3)
parts = [sleeve]

# --- crossed smooth X bands, clipped to the panel outline ---------------------
cx, cz = 0.0585, 0.0570
for side, sgn in (("R", 1.0), ("L", -1.0)):
    for i, ang in enumerate((33.0, -33.0)):
        clip = profile(f"SM_Cutter_GripClip{side}{i}", panel, 0.0030, CUT,
                       y_center=sgn * 0.0180)
        h, w = 0.056, 0.0048
        a = math.radians(ang)
        pts = []
        for u, v in ((-h, -w), (h, -w), (h, w), (-h, w)):
            pts.append((cx + u * math.cos(a) - v * math.sin(a),
                        cz + u * math.sin(a) + v * math.cos(a)))
        band = profile(f"SM_Grip_Band{side}{i}", pts, 0.0007, CUT,
                       y_center=sgn * 0.01730)
        boolean(band, clip, operation="INTERSECT")
        # clear a circle around the medallion so the X meets the disc rim
        hole = cylinder(f"SM_Cutter_BandHole{side}{i}", 0.0092, 0.0060,
                        (0.0585, sgn * 0.0175, 0.0570), "Y", CUT, segments=40)
        boolean(band, hole)
        # re-link the clipped band into the part collection
        for coll in list(band.users_collection):
            coll.objects.unlink(band)
        de_lib.col(C).objects.link(band)
        band.name = f"SM_Grip_Band{side}{i}"
        parts.append(band)

# --- medallion + engraved eagle ----------------------------------------------
for side, sgn in (("R", 1.0), ("L", -1.0)):
    med = cylinder(f"SM_Grip_Medallion{side}", 0.0065, 0.0014,
                   (0.0585, sgn * 0.01750, 0.0570), "Y", C, RUBBER,
                   segments=48, bevel=0.0005, bevel_segments=2)
    parts.append(med)

    # engraved eagle glyph: body diamond + two swept wings + head.
    # Cutters are placed 0.16 mm into the medallion face, not through it.
    face = sgn * 0.01820
    glyphs = []
    # thin line-art eagle: 0.22 mm engraved strokes, not solid shapes
    glyphs.append(profile(f"SM_Grip_EagleBody{side}", [
        (0.05839, 0.0544), (0.05861, 0.0544),
        (0.05861, 0.0596), (0.05839, 0.0596),
    ], 0.0008, CUT, y_center=sgn * 0.0180))
    wing_pts = [
        (0.0586, 0.0579), (0.0623, 0.0599), (0.0628, 0.0593),
        (0.0591, 0.0571), (0.0586, 0.0571),
    ]
    for i, ang in enumerate((0.0, 180.0)):
        a = math.radians(ang)
        pts = [(0.0585 + (x - 0.0585) * math.cos(a) - (z - 0.0570) * math.sin(a),
                0.0570 + (x - 0.0585) * math.sin(a) + (z - 0.0570) * math.cos(a))
               for x, z in wing_pts]
        glyphs.append(profile(f"SM_Grip_EagleWing{side}{i}", pts, 0.0008, CUT,
                              y_center=sgn * 0.0180))
    glyphs.append(cylinder(f"SM_Grip_EagleHead{side}", 0.00055, 0.0010,
                           (0.0585, sgn * 0.0180, 0.0604), "Y", CUT, segments=16))
    glyphs.append(profile(f"SM_Grip_EagleTail{side}", [
        (0.05839, 0.0528), (0.05861, 0.0528),
        (0.05876, 0.0546), (0.05824, 0.0546),
    ], 0.0008, CUT, y_center=sgn * 0.0180))
    for g in glyphs:
        eng = de_lib.join([g], g.name + "_eng")
        de_lib.place_engraving(eng, face, 0.00011, 1 if sgn > 0 else -1)
        boolean(med, eng)

# --- slotted grip screw -------------------------------------------------------
for side, sgn in (("R", 1.0), ("L", -1.0)):
    screw = cylinder(f"SM_Grip_Screw{side}", 0.0019, 0.0016,
                     (0.0400, sgn * 0.0177, 0.0312), "Y", C, BLACK,
                     segments=24, bevel=0.00015, bevel_segments=1)
    parts.append(screw)
    cut = box(f"SM_Cutter_ScrewSlot{side}", 0.0386, 0.0414,
              sgn * 0.0172, sgn * 0.0192, 0.03106, 0.03134, CUT,
              bevel=0.00008, bevel_segments=1)
    boolean(screw, cut)

grip = join(parts, "SM_Grip_A")
report(grip)
mesh_health(grip)
print("grip materials:", [m.name for m in grip.data.materials])
save()
