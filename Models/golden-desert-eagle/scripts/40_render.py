"""Render named views.

Reads scripts/_render.json:
    {"views": ["CAM_Hero_34", "CAM_Side"], "scale": 100, "samples": 160}

Writes renders/<view>.png (CAM_ prefix stripped, lowercased).
"""

import importlib
import json
import os
import sys
import time

import bpy

SCRIPTS = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts"
sys.path.insert(0, SCRIPTS)
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import RENDERS  # noqa: E402

cfg = json.load(open(os.path.join(SCRIPTS, "_render.json"), encoding="utf-8"))
cams = cfg.get("views", ["CAM_Hero_34"])
scale = int(cfg.get("scale", 100))
samples = int(cfg.get("samples", 160))
exposure = float(cfg.get("exposure", 0.0))

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 10
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 6
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = scale
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = exposure

for c in bpy.data.collections:
    if c.name.startswith("COL_Part_") or c.name in ("COL_Studio", "COL_Lights"):
        c.hide_render = False
        c.hide_viewport = False

for name in cams:
    cam = bpy.data.objects.get(name)
    if cam is None:
        print("!! missing camera", name)
        continue
    scene.camera = cam
    out = os.path.join(RENDERS, name.replace("CAM_", "").lower() + ".png")
    scene.render.filepath = out
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {name} -> {out} in {time.time() - t0:.0f}s")
