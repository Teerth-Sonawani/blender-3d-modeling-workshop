#!/usr/bin/env python3
"""Scaffold a new model folder under models/.

Usage:
    python scripts/new_model.py ww2-rifle --title "Realistic WW2 Rifle"

Creates:
    models/<slug>/NOTES.md
    models/<slug>/refs/
    models/<slug>/renders/
    models/<slug>/exports/
    models/<slug>/versions/
    models/<slug>/textures/

Refuses to overwrite an existing folder unless --force is given (which only
fills in missing pieces; it never deletes files).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

NOTES = """# {title}

- **Slug:** `{slug}`
- **Created:** {date}
- **Status:** planned

## Request

> {title}

## Production brief

- **Type:** <!-- prop / hard-surface / vehicle / character / environment -->
- **Target:** <!-- game / cinematic / portfolio / print -->
- **Style:** <!-- realistic / stylized / lowpoly / ... -->
- **Dimensions (m):** <!-- real-world width x height x depth -->
- **Poly budget (tris):**
- **Texture delivery:** <!-- baked BC/N/R/M for game targets; procedural-only needs a reason -->
- **Pivot:**
- **Export:** GLB + FBX
- **Animation:** <!-- none / rigged / animated -->
- **LOD / collision:** <!-- LOD0-LODn + UCX_ proxy, or "none — reason" -->
- **Reference canon:** <!-- one image/measurement set; variant and deviations -->
- **Identity features:** <!-- 5-10 features that make this object recognizable -->

## Active skills

1. <!-- e.g. hard-surface -->
2.

## Parts manifest

Build order, one job per part. Only one row may read `in progress`; each part passes its
own gate before the next one starts (AGENTS.md §5.1).

| # | Part | Collection | Dim spec (m) | Budget (tris) | Detail spec | Status |
|---|---|---|---|---|---|---|
| 01 | | `COL_Part_` | | | | pending |
| 02 | | `COL_Part_` | | | | pending |

Part gate: measured dims in tolerance, counted details verified programmatically, mesh health
clean, `renders/part_<name>.png` inspected. Status: `pending` / `in progress` / `PASS` /
`PASS WITH NOTES` / `FAIL`.

## Measured detail spec

Fill from the canon reference before modeling. Counts and pitches are exact numbers.

| Feature | Real spec | Modeled as | Tolerance | Verified |
|---|---|---|---|---|
| | | | | |

## Pipeline

- [ ] Preflight (`python scripts/preflight.py`)
- [ ] Brief + dimensions + reference canon + identity features
- [ ] Parts manifest written (one job per part, in build order)
- [ ] Scene scaffold (`COL_` collections)
- [ ] Each part gated in isolation before the next part starts
- [ ] Blockout vs measured landmarks, canon-camera screenshot
- [ ] Secondary forms
- [ ] Detail tier + identity features (before UVs)
- [ ] Cleanup (must PASS before export)
- [ ] UVs (hand seams for hero; packing + texel density recorded)
- [ ] Materials + bake for game targets
- [ ] Low-res look-dev, then lights + hero renders + detail close-ups
- [ ] Optimization (tris vs budget, LODs, collision proxy)
- [ ] Export GLB + FBX from a duplicate scene
- [ ] GLB re-import round-trip check
- [ ] Validation + visual match + QA verdict
- [ ] Claims verified (`python scripts/verify_model.py {slug}` → PASS)

## Verification (machine-checked)

Fill this block with the measured values of the **exported** file, then run
`python scripts/verify_model.py {slug}`. The verifier re-measures the GLB/FBX and fails when
these numbers, the render set, or the collision claim stop matching the files on disk.

<!-- verify:begin -->
triangles:
meshes:
materials:
textures:
dimensions_m: 0.000 x 0.000 x 0.000
collision: none
animations: 0
<!-- verify:end -->

## Phase gate evidence

| Gate | Evidence | Result |
|---|---|---|
| Part (each) | manifest row, verified counts, `renders/part_<name>.png` | |
| Blockout | canon-camera screenshot, landmark deltas | |
| Detail | identity features, counts/pitch, close-up render | |
| UV | seam plan, packing %, texel density variance | |
| Material | look-dev crop, baked map list | |
| Export | GLB round-trip render, dimensions, pivot | |
| Delivery | QA verdict SHIP / SHIP WITH NOTES / NO-SHIP | |

## QA verdict

- **Mechanical validation:** <!-- tris, non-manifold, UVs, transforms -->
- **Visual match:** <!-- x/10 Match or Close -->
- **Round-trip:** <!-- GLB re-import dimensions, pivot, materials -->
- **Verdict:** <!-- SHIP / SHIP WITH NOTES / NO-SHIP -->

## Files

- `{slug}.blend` — current working scene
- `versions/` — gate snapshots (`_v01_blockout` … `_v04_export`)
- `refs/` — reference images, dimension notes
- `renders/` — hero + orthographic views + `part_*.png` + `detail_*.png`
- `textures/` — baked maps used by the exports
- `exports/` — GLB / FBX (+ textures)

## Execution deviations

<!-- none, or: what ran outside MCP, why, and what it leaves unverified -->

## Known gaps

<!-- identity features not built, approximations, unverified engine import -->
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a model folder.")
    parser.add_argument("slug", help="kebab-case subject slug, e.g. ww2-rifle")
    parser.add_argument("--title", help="human title (defaults to the slug, title-cased)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="fill missing subfolders in an existing model folder",
    )
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    if not SLUG_RE.match(slug):
        print(
            f"error: invalid slug {slug!r}. Use lowercase kebab-case: "
            "letters, digits and single hyphens (e.g. ww2-rifle).",
            file=sys.stderr,
        )
        return 2

    title = (args.title or slug.replace("-", " ")).strip()
    folder = MODELS / slug

    if folder.exists() and not args.force:
        print(
            f"error: {folder} already exists.\n"
            "Continue that model, or choose a new slug (e.g. "
            f"{slug}-v2) for a deliberate second take.",
            file=sys.stderr,
        )
        return 1

    for sub in ("refs", "renders", "exports", "versions", "textures", "scripts"):
        (folder / sub).mkdir(parents=True, exist_ok=True)

    notes = folder / "NOTES.md"
    if not notes.exists():
        notes.write_text(
            NOTES.format(title=title, slug=slug, date=dt.date.today().isoformat()),
            encoding="utf-8",
        )

    print(f"model folder ready: {folder}")
    print(f"  brief:  {notes}")
    print()
    print("Next:")
    print(f"  1. fill in the production brief in {notes.name}")
    print("  2. run python scripts/preflight.py and confirm get_objects_summary over MCP")
    print(f"  3. save the scene as models/{slug}/{slug}.blend before modeling")
    print(f"  4. before delivery: python scripts/verify_model.py {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
