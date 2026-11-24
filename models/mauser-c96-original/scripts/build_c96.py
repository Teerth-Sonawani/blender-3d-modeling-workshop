"""Build the Mauser C96 Original (M1896 cone hammer) in Blender via MCP.

Coordinates: +X = muzzle, +Z = up, bore axis at Z = 0, X = 0 = rearmost point.
Metres. Dimensions come from the measured reference (see NOTES.md).
"""
import bpy
import bmesh
import math
import os
from math import cos, sin, pi, radians
from mathutils import Matrix

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")
GEO = bpy.data.collections["COL_Geo"]

# ---------------------------------------------------------------- helpers


def purge():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def get_mat(name, color, metallic, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = rough
    return m


def to_object(name, bm, mats, smooth_angle=32.0, weld=1e-6):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    lim = radians(smooth_angle)
    sharp = set()
    for e in bm.edges:
        if len(e.link_faces) != 2:
            sharp.add(tuple(sorted(v.index for v in e.verts)))
            continue
        try:
            ang = e.calc_face_angle(0.0)
        except ValueError:
            ang = 0.0
        a, b = e.link_faces
        if ang > lim or a.material_index != b.material_index:
            sharp.add(tuple(sorted(v.index for v in e.verts)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    for e in me.edges:
        if tuple(sorted(e.vertices)) in sharp:
            e.use_edge_sharp = True
    ob = bpy.data.objects.new(name, me)
    GEO.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    return ob


def bevel(bm, width, segments=2, angle=25.0):
    if width <= 0:
        return
    lim = radians(angle)
    sel = []
    for e in bm.edges:
        if len(e.link_faces) == 2:
            try:
                if e.calc_face_angle(0.0) > lim:
                    sel.append(e)
            except ValueError:
                pass
    if sel:
        bmesh.ops.bevel(bm, geom=sel, offset=width, segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)


def loft(rings, close=True):
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    for a, b in zip(vr, vr[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(len(b)):
                bm.faces.new((a[0], b[i], b[(i + 1) % len(b)]))
        elif len(b) == 1:
            for i in range(len(a)):
                bm.faces.new((a[i], a[(i + 1) % len(a)], b[0]))
        else:
            m = len(a)
            for i in range(m if close else m - 1):
                j = (i + 1) % m
                bm.faces.new((a[i], a[j], b[j], b[i]))
    return bm


def lathe(profile, segs=48, cz=0.0, ribs=0, amp=0.0):
    """profile [(x, r)] revolved about X. ribs/amp add flute knurling."""
    rings = []
    for x, r in profile:
        if r <= 1e-7:
            rings.append([(x, 0.0, cz)])
            continue
        row = []
        for i in range(segs):
            a = 2 * pi * i / segs
            rr = r * (1.0 + amp * cos(ribs * a)) if ribs else r
            row.append((x, rr * cos(a), cz + rr * sin(a)))
        rings.append(row)
    return loft(rings)


def prism(poly, width, bevel_w=0.0008, segments=2, angle=25.0, y_center=0.0):
    bm = bmesh.new()
    vs = [bm.verts.new((x, y_center - width / 2, z)) for x, z in poly]
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(0, width, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bevel(bm, bevel_w, segments, angle)
    return bm


def rounded_box(cx, cy, cz, sx, sy, sz, r=0.0006, segments=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    bevel(bm, r, segments, 20.0)
    return bm


def merge_bm(dst, src):
    me = bpy.data.meshes.new("_m")
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


def rotated_into(bm, parts):
    pass


def subtract(target, cutter):
    me_t = bpy.data.meshes.new("_t")
    target.to_mesh(me_t)
    ob_t = bpy.data.objects.new("_t", me_t)
    bpy.context.scene.collection.objects.link(ob_t)
    me_c = bpy.data.meshes.new("_c")
    cutter.to_mesh(me_c)
    ob_c = bpy.data.objects.new("_c", me_c)
    bpy.context.scene.collection.objects.link(ob_c)
    md = ob_t.modifiers.new("bool", "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.solver = "EXACT"
    md.object = ob_c
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me_out = bpy.data.meshes.new_from_object(ob_t.evaluated_get(dg))
    out = bmesh.new()
    out.from_mesh(me_out)
    for ob in (ob_t, ob_c):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in (me_t, me_c, me_out):
        bpy.data.meshes.remove(me)
    cutter.free()
    target.free()
    return out


def arc2(center, a, b, t0, t1, steps):
    cx, cz = center
    return [(cx + a * cos(radians(t0 + (t1 - t0) * i / steps)),
             cz + b * sin(radians(t0 + (t1 - t0) * i / steps)))
            for i in range(steps + 1)]


def rot90_z(bm, sign=90.0):
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(radians(sign), 3, "Z"))


# ---------------------------------------------------------------- materials
MAT_STEEL = get_mat("MAT_Metal_Blued_Steel", (0.047, 0.050, 0.060), 1.0, 0.32)
MAT_BRIGHT = get_mat("MAT_Metal_Polished_Highlights", (0.26, 0.26, 0.28), 1.0, 0.20)
MAT_WOOD = get_mat("MAT_Wood_Walnut_Grip", (0.036, 0.0145, 0.0062), 0.0, 0.48)
MAT_BORE = get_mat("MAT_Metal_Bore_Shadow", (0.010, 0.010, 0.011), 0.35, 0.72)

purge()

# ---------------------------------------------------------------- barrel
bar_prof = [
    (0.1465, 0.0), (0.1465, 0.0088), (0.1490, 0.0101), (0.1550, 0.00985),
    (0.1650, 0.00915), (0.1750, 0.00825), (0.1800, 0.00780),
    (0.1810, 0.00725), (0.2200, 0.00698), (0.2560, 0.00678),
    (0.2700, 0.00670), (0.2790, 0.00708), (0.2856, 0.00708),
    (0.2874, 0.00655), (0.2880, 0.0050),
]
bm = lathe(bar_prof, segs=56)
bm = subtract(bm, lathe([(0.2880, 0.0), (0.2880, 0.0039), (0.2380, 0.0039),
                         (0.2380, 0.0)], segs=32))
for f in bm.faces:
    c = f.calc_center_median()
    if c.x > 0.2360 and math.hypot(c.y, c.z) < 0.0045:
        f.material_index = 1
barrel = to_object("SM_Weapon_C96_Barrel", bm, [MAT_STEEL, MAT_BORE])

# ---------------------------------------------------------------- receiver / barrel extension
RX0, RX1 = 0.0415, 0.1480
TOP = 0.0096
REC_BOT = -0.0136
rec_poly = [(RX0, REC_BOT), (RX1, REC_BOT), (RX1, 0.0042), (0.1452, 0.0028),
            (0.1432, 0.0036)]
for i in range(1, 11):
    t = i / 10.0
    rec_poly.append((0.1432 - 0.0132 * t,
                     0.0036 + (TOP - 0.0036) * (math.sin(t * pi / 2) ** 0.62)))
rec_poly += [(0.1300, TOP), (0.0450, TOP), (RX0 + 0.0018, TOP - 0.0014)]
bm = prism(rec_poly, 0.0258, bevel_w=0.0006, segments=2, angle=18.0)
# side milled pocket + oval lock-bolt recess, both sides
for sgn in (-1, 1):
    bm = subtract(bm, rounded_box(0.0620, sgn * 0.0137, -0.0026, 0.0480, 0.0040,
                                  0.0130, r=0.0018, segments=3))
    bm = subtract(bm, rounded_box(0.0700, sgn * 0.0137, -0.0102, 0.0330, 0.0040,
                                  0.0038, r=0.0016, segments=3))
# top slot for the hammer head
bm = subtract(bm, rounded_box(0.0492, 0.0, 0.0060, 0.0250, 0.0600, 0.0120,
                              r=0.0015, segments=3))
receiver = to_object("SM_Weapon_C96_Receiver", bm, [MAT_STEEL])

# ---------------------------------------------------------------- frame
FR_BOT = -0.0722
frame_poly = [
    (0.1480, -0.0136), (0.1480, -0.0670), (0.1425, FR_BOT), (0.0935, FR_BOT),
    (0.0900, -0.0445), (0.0600, -0.0445), (0.0550, -0.0462), (0.0180, -0.0505),
    (0.0125, -0.0430), (0.0125, -0.0180), (0.0160, -0.0136),
]
bm = prism(frame_poly, 0.0242, bevel_w=0.0006, segments=2, angle=18.0)
for sgn in (-1, 1):
    bm = subtract(bm, rounded_box(0.0515, sgn * 0.0128, -0.0250, 0.0355, 0.0040,
                                  0.0145, r=0.0017, segments=3))
    bm = subtract(bm, rounded_box(0.1060, sgn * 0.0128, -0.0260, 0.0470, 0.0040,
                                  0.0155, r=0.0017, segments=3))
frame = to_object("SM_Weapon_C96_Frame", bm, [MAT_STEEL])

# ---------------------------------------------------------------- trigger guard
guard = arc2((0.0725, -0.0557), 0.0198, 0.0166, 0.0, 360.0, 48)[:-1]
guard += arc2((0.0725, -0.0557), 0.0132, 0.0100, 0.0, 360.0, 48)[:-1][::-1]
bm = prism(guard, 0.0086, bevel_w=0.0007, segments=2, angle=20.0)
tguard = to_object("SM_Weapon_C96_TriggerGuard", bm, [MAT_STEEL])

# ---------------------------------------------------------------- grip
G_TOP, G_BOT = -0.0470, -0.1352
stations = [
    (-0.0470, 0.0330, 0.0378, 0.0330),
    (-0.0560, 0.0318, 0.0392, 0.0338),
    (-0.0680, 0.0300, 0.0402, 0.0343),
    (-0.0820, 0.0282, 0.0412, 0.0348),
    (-0.0960, 0.0264, 0.0420, 0.0353),
    (-0.1080, 0.0248, 0.0426, 0.0357),
    (-0.1180, 0.0236, 0.0431, 0.0360),
    (-0.1260, 0.0226, 0.0422, 0.0351),
    (-0.1310, 0.0220, 0.0385, 0.0318),
    (-0.1340, 0.0216, 0.0300, 0.0244),
    (-0.1352, 0.0214, 0.0172, 0.0134),
]
N = 72
EXP = 2.55
GP = 0.0018          # groove pitch
BAND = (-0.0555, -0.1285)


def station_at(z):
    if z >= stations[0][0]:
        return stations[0]
    for a, b in zip(stations, stations[1:]):
        if b[0] <= z <= a[0]:
            t = (a[0] - z) / (a[0] - b[0])
            t = t * t * (3 - 2 * t)
            return (z,
                    a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t,
                    a[3] + (b[3] - a[3]) * t)
    return stations[-1]


def superell(th):
    c, s = cos(th), sin(th)
    return (math.copysign(abs(c) ** (2 / EXP), c),
            math.copysign(abs(s) ** (2 / EXP), s))


zs = []
z = G_TOP
while z > BAND[0]:
    zs.append(z)
    z -= 0.0024
n_g = int((BAND[0] - BAND[1]) / (GP / 4))
for i in range(n_g + 1):
    zs.append(BAND[0] - i * GP / 4)
for zz in (-0.1305, -0.1325, -0.1340, -0.1352):
    zs.append(zz)
zs = sorted({round(v, 6) for v in zs}, reverse=True)

rings = [[(stations[0][1], 0.0, G_TOP)]]
for z in zs:
    zz, cx, d, w = station_at(z)
    ring = []
    for i in range(N):
        th = 2 * pi * i / N
        ux, uy = superell(th)
        side = abs(sin(th))            # 1 at the flat panels (+/-Y)
        wood = 0.0
        if BAND[1] + 0.0018 < z < BAND[0] - 0.0018 and side > 0.50:
            wood = min((side - 0.50) / 0.08, 1.0)
        groove = 0.0
        if side > 0.62 and wood > 0.9:
            groove = 0.5 * (1 - cos(2 * pi * (z - BAND[1]) / GP))
        shrink = (0.00030 + 0.00030 * groove) * wood
        kx = 1.0 - (0.00055 if wood > 0.0 else 0.0) / max(d / 2, 1e-6) - shrink / max(d / 2, 1e-6)
        ky = 1.0 - (0.00055 if wood > 0.0 else 0.0) / max(w / 2, 1e-6) - shrink / max(w / 2, 1e-6)
        ring.append((cx + (d / 2) * ux * kx, (w / 2) * uy * ky, z))
    rings.append(ring)
rings.append([(0.0214, 0.0, G_BOT)])

bm = loft(rings, close=True)
for f in bm.faces:
    c = f.calc_center_median()
    if BAND[1] + 0.0010 < c.z < BAND[0] - 0.0010 and abs(c.y) > 0.0090:
        f.material_index = 1
grip = to_object("SM_Weapon_C96_Grip", bm, [MAT_STEEL, MAT_WOOD], smooth_angle=34.0)

# ---------------------------------------------------------------- hammer
bm = prism([(0.0400, -0.0060), (0.0572, -0.0060), (0.0572, 0.0046),
            (0.0512, 0.0146), (0.0438, 0.0142), (0.0400, 0.0034)],
           0.0052, bevel_w=0.0006, segments=2, angle=20.0)
for sgn in (-1, 1):
    cone = lathe([(0.0, 0.0), (0.0, 0.0086), (0.0026, 0.0083), (0.0042, 0.0059),
                  (0.0042, 0.0)], segs=42, ribs=20, amp=0.055)
    rot90_z(cone, 90)
    bmesh.ops.translate(cone, verts=cone.verts, vec=(0.0486, sgn * 0.0024, 0.0032))
    merge_bm(bm, cone)
hammer = to_object("SM_Weapon_C96_Hammer", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- bolt rear disc
bm = lathe([(0.0340, 0.0), (0.0340, 0.0100), (0.0388, 0.0104),
            (0.0442, 0.0099), (0.0454, 0.0086), (0.0458, 0.0064),
            (0.0458, 0.0034), (0.0430, 0.0032), (0.0430, 0.0)],
           segs=56, cz=-0.0024, ribs=34, amp=0.05)
bolt = to_object("SM_Weapon_C96_Bolt", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- rear sight
bm = rounded_box(0.0885, 0.0, 0.0112, 0.0520, 0.0092, 0.0034, r=0.0006, segments=2)
merge_bm(bm, rounded_box(0.0672, 0.0, 0.0131, 0.0108, 0.0080, 0.0042, r=0.0005, segments=2))
merge_bm(bm, rounded_box(0.0895, 0.0, 0.0137, 0.0118, 0.0108, 0.0028, r=0.0005, segments=2))
sight = to_object("SM_Weapon_C96_RearSight", bm, [MAT_STEEL])

# ---------------------------------------------------------------- extractor
bm = rounded_box(0.0900, 0.0061, 0.0105, 0.0640, 0.0052, 0.0024, r=0.0004, segments=2)
extractor = to_object("SM_Weapon_C96_Extractor", bm, [MAT_STEEL])

# ---------------------------------------------------------------- safety (left flank)
bm = prism([(0.0438, -0.0118), (0.0578, -0.0118), (0.0580, -0.0038),
            (0.0512, -0.0006), (0.0440, -0.0022)], 0.0034, bevel_w=0.0004,
           segments=2, y_center=-0.0119)
safety = to_object("SM_Weapon_C96_Safety", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- front sight
bm = rounded_box(0.2757, 0.0, 0.0050, 0.0225, 0.0074, 0.0074, r=0.0006, segments=2)
merge_bm(bm, prism([(0.2732, 0.0084), (0.2778, 0.0084), (0.2772, 0.0144),
                    (0.2726, 0.0144)], 0.0017, bevel_w=0.0002, segments=1))
fsight = to_object("SM_Weapon_C96_FrontSight", bm, [MAT_STEEL])

# ---------------------------------------------------------------- trigger
bm = prism([(0.0652, -0.0505), (0.0704, -0.0498), (0.0728, -0.0556),
            (0.0716, -0.0622), (0.0674, -0.0644), (0.0650, -0.0578)],
           0.0050, bevel_w=0.0006, segments=2)
trigger = to_object("SM_Weapon_C96_Trigger", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- magazine floorplate
bm = rounded_box(0.1180, 0.0, -0.0727, 0.0530, 0.0234, 0.0032, r=0.0008, segments=2)
plate = to_object("SM_Weapon_C96_MagFloorplate", bm, [MAT_STEEL])

# ---------------------------------------------------------------- stock lugs
bm = prism([(0.0412, -0.0030), (0.0412, -0.0385), (0.0290, -0.0475),
            (0.0120, -0.0450), (0.0060, -0.0290), (0.0060, -0.0060),
            (0.0125, 0.0005), (0.0300, 0.0055)],
           0.0170, bevel_w=0.0006, segments=2, angle=18.0)
for (bx, bz, br) in ((0.0205, 0.0008, 0.0058), (0.0148, -0.0300, 0.0062)):
    boss = lathe([(-0.0088, br * 0.44), (-0.0088, br), (0.0088, br),
                  (0.0088, br * 0.44), (-0.0088, br * 0.44)], segs=40)
    rot90_z(boss, 90)
    bmesh.ops.translate(boss, verts=boss.verts, vec=(bx, 0.0, bz))
    merge_bm(bm, boss)
lugs = to_object("SM_Weapon_C96_StockLugs", bm, [MAT_STEEL])

# ---------------------------------------------------------------- lanyard ring
bm = bmesh.new()
R1, R2 = 0.0052, 0.00115
seg, tub = 36, 10
rows = []
for i in range(seg):
    a = 2 * pi * i / seg
    row = []
    for j in range(tub):
        b = 2 * pi * j / tub
        rr = R1 + R2 * cos(b)
        row.append(bm.verts.new((0.0126 + rr * cos(a), R2 * sin(b),
                                 -0.1322 + rr * sin(a))))
    rows.append(row)
for i in range(seg):
    i2 = (i + 1) % seg
    for j in range(tub):
        j2 = (j + 1) % tub
        bm.faces.new((rows[i][j], rows[i2][j], rows[i2][j2], rows[i][j2]))
lanyard = to_object("SM_Weapon_C96_LanyardRing", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- grip screw + escutcheon
bm = lathe([(0.0, 0.0), (0.0, 0.0043), (0.0011, 0.0043), (0.0013, 0.0030),
            (0.0020, 0.0029), (0.0022, 0.0)], segs=32)
rot90_z(bm, -90)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0288, -0.0172, -0.0962))
screw = to_object("SM_Weapon_C96_GripScrew", bm, [MAT_BRIGHT])

# ---------------------------------------------------------------- pins
bm = bmesh.new()
for (px, pz, pr) in ((0.0242, -0.0086, 0.0022), (0.0396, -0.0172, 0.0018),
                     (0.0900, -0.0190, 0.0016)):
    for side in (-1, 1):
        pin = lathe([(side * 0.0119, 0.0), (side * 0.0119, pr),
                     (side * 0.0131, pr), (side * 0.0134, pr * 0.8),
                     (side * 0.0134, 0.0)], segs=22)
        rot90_z(pin, 90)
        bmesh.ops.translate(pin, verts=pin.verts, vec=(px, 0.0, pz))
        merge_bm(bm, pin)
pins = to_object("SM_Weapon_C96_Pins", bm, [MAT_STEEL])

# ---------------------------------------------------------------- report
total = 0
for ob in GEO.objects:
    if ob.type == "MESH":
        t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        total += t
        print(f"{ob.name:34s} tris {t:6d} verts {len(ob.data.vertices):6d}")
print("TOTAL TRIS", total)

xs, ys, zs2 = [], [], []
for ob in GEO.objects:
    for v in ob.bound_box:
        w = ob.matrix_world @ __import__("mathutils").Vector(v)
        xs.append(w.x); ys.append(w.y); zs2.append(w.z)
print(f"BBOX X {min(xs)*1000:.1f}..{max(xs)*1000:.1f} mm  "
      f"Y {min(ys)*1000:.1f}..{max(ys)*1000:.1f}  Z {min(zs2)*1000:.1f}..{max(zs2)*1000:.1f}")
print(f"LENGTH {(max(xs)-min(xs))*1000:.1f} mm  HEIGHT {(max(zs2)-min(zs2))*1000:.1f} mm")

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
