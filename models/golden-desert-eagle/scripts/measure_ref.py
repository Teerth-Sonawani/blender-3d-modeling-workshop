"""Measure the canon reference photo (refs/ref_01.jpg) to derive proportions.

Run inside Blender (bpy image API + numpy) or with system python if PIL exists.

Outputs, for the largest connected silhouette:
  - bounding box and aspect ratio (must match 273 x 159 mm = 1.717)
  - top/bottom silhouette profile sampled across the width (normalised)
  - rail cross-slot count in the front region
  - slide serration count in the rear region
  - an ASCII silhouette map so the shape can be read as text

All output is plain text so it can be pasted into NOTES.md as measured evidence.
"""

from __future__ import annotations

import sys
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "refs" / "ref_01.jpg"

# Real-world spec for the canon object (Magnum Research DE50TG, 6" barrel).
REAL_LENGTH_M = 0.273
REAL_HEIGHT_M = 0.159


def load_gray(path: Path):
    """Return (2-D float array of luminance 0..255, height, width)."""
    try:
        import numpy as np
        from PIL import Image  # type: ignore

        img = Image.open(path).convert("L")
        return np.asarray(img, dtype=float), img.height, img.width
    except Exception:
        import numpy as np
        import bpy  # type: ignore

        bpy_img = bpy.data.images.load(str(path))
        w, h = bpy_img.size
        px = np.array(bpy_img.pixels[:], dtype=float).reshape(h, w, 4)
        # Blender images are bottom-up; flip to top-down like PIL
        rgb = px[::-1, :, :3]
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
        bpy.data.images.remove(bpy_img)
        return lum * 255.0, h, w


def main() -> int:
    import numpy as np

    lum, h, w = load_gray(REF)
    subject = lum < 245.0

    # Largest connected component via simple row/col flood (image is one object).
    rows = np.where(subject.any(axis=1))[0]
    cols = np.where(subject.any(axis=0))[0]
    y0, y1 = int(rows.min()), int(rows.max())
    x0, x1 = int(cols.min()), int(cols.max())
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    print(f"image        : {w} x {h}")
    print(f"bbox px      : x {x0}..{x1} (w={bw})  y {y0}..{y1} (h={bh})")
    print(f"aspect W/H   : {bw / bh:.3f}   (spec {REAL_LENGTH_M / REAL_HEIGHT_M:.3f})")
    print(f"scale        : {REAL_LENGTH_M / bw * 1000:.4f} mm per px (x)")
    print(f"               {REAL_HEIGHT_M / bh * 1000:.4f} mm per px (y)")
    print()

    crop = subject[y0 : y1 + 1, x0 : x1 + 1]

    # Silhouette profile: first/last subject row per column.
    tops = np.full(bw, -1)
    bots = np.full(bw, -1)
    for x in range(bw):
        col = np.where(crop[:, x])[0]
        if col.size:
            tops[x] = col.min()
            bots[x] = col.max()

    def z_of(row: int) -> float:
        """Convert an image row to height above the bottom of the gun, in mm."""
        return (bh - 1 - row) * (REAL_HEIGHT_M / bh) * 1000.0

    def x_of(col: int) -> float:
        """Convert an image column to distance behind the muzzle, in mm."""
        return col * (REAL_LENGTH_M / bw) * 1000.0

    print("profile (x = mm behind muzzle, top/bottom = mm above grip-base plane)")
    print(f"{'x_mm':>7} {'top_mm':>7} {'bot_mm':>7} {'height':>7}")
    for frac in [i / 40 for i in range(41)]:
        c = min(bw - 1, int(round(frac * (bw - 1))))
        if tops[c] < 0:
            continue
        print(
            f"{x_of(c):7.1f} {z_of(int(tops[c])):7.1f} "
            f"{z_of(int(bots[c])):7.1f} {z_of(int(tops[c])) - z_of(int(bots[c])):7.1f}"
        )
    print()

    # Rail cross slots: along the top edge of the front half, a slot is a local
    # downward notch in the top profile.
    front = slice(int(bw * 0.05), int(bw * 0.45))
    tt = tops[front].astype(float)
    notch = tt > (np.median(tt[tt > 0]) + 2.0)
    runs = []
    in_run = False
    for i, v in enumerate(notch):
        if v and not in_run:
            start = i
            in_run = True
        elif not v and in_run:
            runs.append((start + int(bw * 0.05), i + int(bw * 0.05)))
            in_run = False
    print(f"rail slots detected in front region: {len(runs)}")
    for a, b in runs:
        print(f"   slot {x_of(a):6.1f} .. {x_of(b):6.1f} mm  (width {x_of(b) - x_of(a):4.1f} mm)")
    print()

    # Serrations: count dark vertical lines in a band across the rear slide side.
    band_y0 = y0 + int(bh * 0.10)
    band_y1 = y0 + int(bh * 0.30)
    band_x0 = x0 + int(bw * 0.68)
    band_x1 = x0 + int(bw * 0.92)
    band = lum[band_y0:band_y1, band_x0:band_x1]
    colmin = band.min(axis=0)
    thr = colmin.mean() - 0.6 * colmin.std()
    dark = colmin < thr
    groups = 0
    prev = False
    for v in dark:
        if v and not prev:
            groups += 1
        prev = bool(v)
    print(f"serration-ish dark column groups in rear slide band: {groups}")
    print(f"   band x {x_of(band_x0 - x0):6.1f} .. {x_of(band_x1 - x0):6.1f} mm, "
          f"z {z_of(band_y1 - y0):5.1f} .. {z_of(band_y0 - y0):5.1f} mm")
    print()

    # ASCII silhouette map (100 x 34).
    aw, ah = 100, 34
    print("silhouette map (left = muzzle, bottom = grip base):")
    for r in range(ah):
        line = []
        for c in range(aw):
            yy = int(round((r / (ah - 1)) * (bh - 1)))
            xx = int(round((c / (aw - 1)) * (bw - 1)))
            line.append("#" if crop[yy, xx] else ".")
        print("   " + "".join(line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
