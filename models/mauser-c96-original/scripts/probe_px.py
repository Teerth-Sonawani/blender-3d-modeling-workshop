"""Probe reference luminance down columns (runs inside Blender via MCP)."""
import bpy
import numpy as np
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
img = bpy.data.images.load(os.path.join(ROOT, "refs", "ref_04.jpg"), check_existing=False)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
lum = px[:, :, 0] * 0.2126 + px[:, :, 1] * 0.7152 + px[:, :, 2] * 0.0722
x0, y0 = 205, 229
S = 0.1844


def col(mm_x, y_from, y_to):
    c = x0 + int(mm_x / S)
    print(f"--- column x={mm_x}mm (px {c})")
    prev = None
    for ymm in range(y_from, y_to, 1):
        r = y0 + int(ymm / S)
        v = float(lum[r, c])
        rgb = tuple(round(float(px[r, c, k]), 3) for k in range(3))
        mark = ""
        if prev is not None and abs(v - prev) > 0.05:
            mark = "  <<<"
        print(f"  y={ymm:6.1f}mm lum={v:.3f} rgb={rgb}{mark}")
        prev = v


col(120, 40, 100)
col(75, 40, 100)
col(15, 120, 158)
