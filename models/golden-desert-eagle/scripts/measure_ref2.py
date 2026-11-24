"""Second measurement pass: segment the black parts and interior holes.

Gold frame/slide are bright; the Hogue grip, sights and magazine baseplate are
near-black. Interior white regions (holes) are the trigger-guard opening and the
gap between guard and grip. Both give exact part boxes in millimetres.

Coordinates printed as:
  behind_muzzle_mm  - distance rearward from the muzzle face
  z_mm              - height above the bottom of the magazine baseplate
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

REF = Path(__file__).resolve().parent.parent / "refs" / "ref_01.jpg"
BBOX = (0, 218, 1023, 805)  # x0, y0, x1, y1 measured in pass 1
REAL_LEN, REAL_HGT = 0.273, 0.159


def label(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """4-connected components on a small boolean array. Returns (x0,y0,x1,y1,area)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            x0 = x1 = sx
            y0 = y1 = sy
            area = 0
            while q:
                y, x = q.popleft()
                area += 1
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append((x0, y0, x1, y1, area))
    return out


def main() -> int:
    img = Image.open(REF).convert("L")
    # Downsample 2x for fast component labelling (0.5 mm precision).
    small = img.resize((img.width // 2, img.height // 2), Image.BILINEAR)
    a = np.asarray(small, dtype=float)

    x0, y0, x1, y1 = [v / 2 for v in BBOX]
    bw, bh = x1 - x0, y1 - y0
    sx = REAL_LEN * 1000.0 / bw
    sy = REAL_HGT * 1000.0 / bh

    def box(c):
        cx0, cy0, cx1, cy1, area = c
        return (
            (cx0 - x0) * sx,
            (cx1 - x0) * sx,
            (y1 - cy1) * sy,
            (y1 - cy0) * sy,
            area,
        )

    print("scale: %.4f mm/px (x)   %.4f mm/px (y)" % (sx, sy))
    print()

    for name, mask, min_area in (
        ("BLACK PARTS (grip, sights, mag plate)", a < 80.0, 40),
        ("WHITE HOLES (guard opening etc)", a > 250.0, 40),
    ):
        m = mask.copy()
        comps = [c for c in label(m) if c[4] >= min_area]
        comps.sort(key=lambda c: -c[4])
        print(name)
        print(f"  {'behind_mm':>18} {'z_mm':>16} {'size_mm':>14} {'area_px':>8}")
        for c in comps[:10]:
            bx0, bx1, bz0, bz1, area = box(c)
            print(
                f"  {bx0:7.1f}..{bx1:6.1f} {bz0:7.1f}..{bz1:6.1f} "
                f"{bx1 - bx0:6.1f}x{bz1 - bz0:5.1f} {area:8d}"
            )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
