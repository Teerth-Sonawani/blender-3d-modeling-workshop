"""Write mm-gridded zoom crops of the reference photos (runs inside Blender via MCP)."""
import bpy
import numpy as np
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
SRC = os.path.join(ROOT, "refs", "ref_04.jpg")
OUT = os.path.join(ROOT, "refs")
os.makedirs(OUT, exist_ok=True)

img = bpy.data.images.load(SRC, check_existing=False)
w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
px = px[::-1]
lum = px[:, :, 0] * 0.2126 + px[:, :, 1] * 0.7152 + px[:, :, 2] * 0.0722
bg = np.median(lum[:60, :], axis=0)
mask = lum < (bg[None, :] - 0.13)
cols = np.where(mask.sum(axis=0) > 20)[0]
rows = np.where(mask.sum(axis=1) > 6)[0]
x0, y0 = cols.min(), rows.min()
S = 288.0 / (cols.max() - cols.min() + 1)   # mm per px
mmpp = S


def save(arr, name):
    ih, iw = arr.shape[0], arr.shape[1]
    out = bpy.data.images.new(name, width=iw, height=ih, alpha=True)
    out.pixels = arr[::-1].ravel().tolist()
    path = os.path.join(OUT, name + ".jpg")
    out.filepath_raw = path
    out.file_format = "JPEG"
    bpy.context.scene.render.image_settings.quality = 88
    out.save()
    print("saved", path, iw, "x", ih)


def crop_mm(ax, bx, ay, by, zoom, name):
    """x range in mm (a<b), y in mm, zoom factor."""
    xa = x0 + int(ax / mmpp)
    xb = x0 + int(bx / mmpp)
    ya = y0 + int(ay / mmpp)
    yb = y0 + int(by / mmpp)
    crop = px[ya:yb, xa:xb]
    big = np.repeat(np.repeat(crop, zoom, axis=0), zoom, axis=1)
    cell = mmpp * zoom  # px per mm after zoom
    # grid every 5mm light, every 10mm magenta-ish, every 50mm bright
    for mm in range(0, int(bx - ax) + 1, 5):
        c = int(mm * cell)
        if c >= big.shape[1]:
            break
        major = (mm % 50 == 0)
        mid = (mm % 10 == 0)
        if major:
            big[:, c] = [0.0, 1.0, 1.0, 1.0]
        elif mid:
            big[:, c] = [0.9, 0.1, 0.9, 1.0]
        else:
            big[:, c] = big[:, c] * 0.55 + np.array([0.5, 1.0, 0.5, 1.0]) * 0.45
    for mm in range(0, int(by - ay) + 1, 5):
        c = int(mm * cell)
        if c >= big.shape[0]:
            break
        major = (mm % 50 == 0)
        mid = (mm % 10 == 0)
        if major:
            big[c, :] = [0.0, 1.0, 1.0, 1.0]
        elif mid:
            big[c, :] = [0.9, 0.1, 0.9, 1.0]
        else:
            big[c, :] = big[c, :] * 0.55 + np.array([0.5, 1.0, 0.5, 1.0]) * 0.45
    save(big, name)
    print(f"  crop x{ax}-{bx}mm y{ay}-{by}mm zoom{zoom}")


crop_mm(0, 70, 0, 62, 5, "crop_mech")
crop_mm(40, 160, 38, 105, 5, "crop_guard")
