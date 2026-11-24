"""ASCII silhouette + extents of the C96 reference (runs inside Blender via MCP)."""
import bpy
import numpy as np
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
PATH = os.path.join(ROOT, "refs", "ref_04.jpg")

img = bpy.data.images.load(PATH, check_existing=False)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
px = px[::-1]
lum = px[:, :, 0] * 0.2126 + px[:, :, 1] * 0.7152 + px[:, :, 2] * 0.0722
bg = np.median(lum[:60, :], axis=0)
mask = lum < (bg[None, :] - 0.13)


def erode(m, n=1):
    for _ in range(n):
        o = m.copy()
        o[1:, :] &= m[:-1, :]; o[:-1, :] &= m[1:, :]
        o[:, 1:] &= m[:, :-1]; o[:, :-1] &= m[:, 1:]
        m = o
    return m


def dilate(m, n=1):
    for _ in range(n):
        o = m.copy()
        o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        m = o
    return m


mask = dilate(erode(mask, 3), 3)
cy = mask.sum(axis=0)
cols = np.where(cy > 20)[0]
rows = np.where(mask.sum(axis=1) > 6)[0]
x0, x1, y0, y1 = cols.min(), cols.max(), rows.min(), rows.max()
W = x1 - x0 + 1
H = y1 - y0 + 1
s = 288.0 / W
print(f"bbox px x{x0}-{x1} y{y0}-{y1}  scale {s:.4f} mm/px  height {(y1-y0+1)*s:.1f}mm")

# ASCII: 2.5 mm per cell, x = 0 at rear
CELL = 2.5
nx = int(288 / CELL)
ny = int((y1 - y0) * s / CELL) + 1
print(f"\nsilhouette ({CELL}mm/cell), x=0 rear .. 288 muzzle, y=0 top")
hdr = "".join(str((i * 5 // 2) // 50 % 10) for i in range(nx))
print("     " + hdr)
for j in range(ny):
    ya = y0 + int(j * CELL / s)
    yb = y0 + int((j + 1) * CELL / s)
    line = []
    for i in range(nx):
        xa = x0 + int(i * CELL / s)
        xb = x0 + int((i + 1) * CELL / s)
        blk = mask[ya:max(yb, ya + 1), xa:max(xb, xa + 1)]
        line.append("#" if blk.mean() > 0.45 else ("." if blk.mean() > 0.12 else " "))
    print(f"{j * CELL:5.0f}" + "".join(line))

print("\ncolumn extents (mm from rear | top .. bottom mm from bbox top)")
for mm in range(0, 289, 6):
    c = x0 + int(round(mm / s))
    if c > x1:
        break
    col = np.where(mask[:, c])[0]
    if len(col) == 0:
        print(f"  x={mm:3d} -")
        continue
    print(f"  x={mm:3d}  {(col.min()-y0)*s:6.1f} .. {(col.max()-y0)*s:6.1f}")
