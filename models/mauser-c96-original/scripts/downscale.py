"""Downscale renders for inspection (runs inside Blender via MCP)."""
import bpy
import os
import numpy as np

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\mauser-c96-original"
REND = os.path.join(ROOT, "renders")

WIDTH = 1200
for name in ("side.png", "hero.png", "front.png", "top.png"):
    src = os.path.join(REND, name)
    if not os.path.exists(src):
        continue
    img = bpy.data.images.load(src, check_existing=False)
    w, h = img.size
    k = WIDTH / w
    nw, nh = WIDTH, max(1, int(h * k))
    img.scale(nw, nh)
    out = bpy.data.images.new(name + "_prev", width=nw, height=nh, alpha=True)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(nh, nw, 4)
    out.pixels = px.ravel().tolist()
    out.filepath_raw = os.path.join(REND, "prev_" + name.replace(".png", ".jpg"))
    out.file_format = "JPEG"
    bpy.context.scene.render.image_settings.quality = 90
    out.save()
    print("wrote", out.filepath_raw, nw, nh)
    bpy.data.images.remove(img)
    bpy.data.images.remove(out)
