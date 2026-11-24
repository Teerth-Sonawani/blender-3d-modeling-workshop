#!/usr/bin/env python3
"""Verify a delivered model against its NOTES.md claims and the files on disk.

This is the workshop's claims auditor. It opens the exports, measures them, and
compares the numbers to the machine-readable block in NOTES.md, so a delivery
record cannot drift away from the files it describes.

Checks, per model:

  structure   required folders/files from AGENTS.md section 3
  blend       .blend present, non-empty, valid Blender container magic
  glb         parses as glTF 2.0; triangles, world bbox, meshes, materials, textures
  fbx         present; whether UCX_/COL_ collision geometry actually exists
  renders     every .png is a valid image, not blank, not a viewport screenshot;
              every render named in NOTES exists, and renders on disk are declared
  claims      the <!-- verify:begin --> block in NOTES.md vs the measured export

Usage:
    python scripts/verify_model.py --all
    python scripts/verify_model.py mosin-nagant-m91-30
    python scripts/verify_model.py --all --strict     # warnings also fail

Exit: 0 if every check passes, 1 if any FAIL.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"

OK = "  [ OK ]"
FAIL = "  [FAIL]"
WARN = "  [warn]"

REQUIRED_DIRS = ("refs", "renders", "versions", "textures", "exports", "scripts")
REQUIRED_FILES = ("NOTES.md",)

# A delivery record may differ from the export by this much before it is a lie.
DIM_TOLERANCE_M = 0.002
PREVIEW_SUFFIXES = ("_prev.png", "_prev.jpg", "_prev.jpeg")


class Report:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.fails: list[str] = []
        self.warns: list[str] = []

    def ok(self, label: str, detail: str = "") -> None:
        print(f"{OK} {label}" + (f" — {detail}" if detail else ""))

    def fail(self, label: str, detail: str = "") -> None:
        print(f"{FAIL} {label}" + (f" — {detail}" if detail else ""))
        self.fails.append(f"{label}: {detail}" if detail else label)

    def warn(self, label: str, detail: str = "") -> None:
        print(f"{WARN} {label}" + (f" — {detail}" if detail else ""))
        self.warns.append(f"{label}: {detail}" if detail else label)


# ---------------------------------------------------------------- notes / claims


def parse_notes(path: Path) -> tuple[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    block: dict[str, str] = {}
    match = re.search(r"<!--\s*verify:begin\s*-->(.*?)<!--\s*verify:end\s*-->", text, re.S)
    if match:
        for raw in match.group(1).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                block[key.strip().lower()] = value.strip()
    return text, block


def parse_dims(value: str) -> list[float] | None:
    nums = re.findall(r"\d+(?:\.\d+)?", value.replace(",", "."))
    if len(nums) < 3:
        return None
    try:
        return [float(n) for n in nums[:3]]
    except ValueError:
        return None


def declared_pngs(text: str, folder: Path) -> tuple[dict[str, set[str]], set[str]]:
    """Return (exact name -> relative path, glob patterns) of renders named in NOTES.

    Reference and texture images are cited by path and are not render evidence, and
    shorthand like `lighttest_A/B/C.png` or `T_..._MR.png` is not a filename.
    """
    tokens = set(re.findall(r"[A-Za-z0-9_.\-/*]+\.png", text))
    exact: dict[str, set[str]] = {}
    patterns: set[str] = set()
    for token in tokens:
        if "..." in token or "…" in token:
            continue
        if "/" in token and not token.startswith("renders/"):
            continue  # refs/, textures/ and A/B/C shorthand are not renders
        name = token.rsplit("/", 1)[-1]
        if (folder / "refs" / name).is_file() or (folder / "textures" / name).is_file():
            continue
        if "*" in name:
            patterns.add(name)
        else:
            # The same image may be cited bare and by path; accept either.
            rel = token if token.startswith("renders/") else f"renders/{name}"
            exact.setdefault(name, set()).add(rel)
    return exact, patterns


# ------------------------------------------------------------------------ blend


def blend_report(path: Path) -> str | None:
    head = path.read_bytes()[:8]
    if head.startswith(b"BLENDER"):
        return "uncompressed"
    if head.startswith(b"\x28\xb5\x2f\xfd"):
        return "zstd"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    return None


# -------------------------------------------------------------------------- glb


def _ident() -> list[float]:
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def _mul(a: list[float], b: list[float]) -> list[float]:
    return [
        sum(a[i * 4 + k] * b[k * 4 + j] for k in range(4))
        for i in range(4)
        for j in range(4)
    ]


def _node_matrix(node: dict) -> list[float]:
    if "matrix" in node:
        m = node["matrix"]
        return [m[0], m[4], m[8], m[12], m[1], m[5], m[9], m[13],
                m[2], m[6], m[10], m[14], m[3], m[7], m[11], m[15]]
    t = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    rot = [
        1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
        2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
        2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y),
    ]
    m = [0.0] * 16
    for i in range(3):
        for j in range(3):
            m[i * 4 + j] = rot[i * 3 + j] * s[j]
    m[3], m[7], m[11], m[15] = t[0], t[1], t[2], 1.0
    return m


def _apply(m: list[float], p: list[float]) -> list[float]:
    return [
        m[0] * p[0] + m[1] * p[1] + m[2] * p[2] + m[3],
        m[4] * p[0] + m[5] * p[1] + m[6] * p[2] + m[7],
        m[8] * p[0] + m[9] * p[1] + m[10] * p[2] + m[11],
    ]


def glb_report(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError("file shorter than a GLB header")
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        raise ValueError("missing glTF magic")
    if version != 2:
        raise ValueError(f"glTF version {version}, expected 2")

    offset, doc = 12, None
    while offset + 8 <= min(length, len(data)):
        chunk_len, chunk_type = struct.unpack("<II", data[offset:offset + 8])
        chunk = data[offset + 8:offset + 8 + chunk_len]
        if chunk_type == 0x4E4F534A:
            doc = json.loads(chunk)
        offset += 8 + chunk_len
    if doc is None:
        raise ValueError("no JSON chunk")

    triangles = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if "indices" in prim:
                triangles += doc["accessors"][prim["indices"]]["count"] // 3
            else:
                triangles += doc["accessors"][prim["attributes"]["POSITION"]]["count"] // 3

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    with_mesh = 0
    scene = doc.get("scenes", [{}])[doc.get("scene", 0)]

    def walk(index: int, parent: list[float]) -> None:
        nonlocal with_mesh
        node = doc["nodes"][index]
        matrix = _mul(parent, _node_matrix(node))
        if "mesh" in node:
            with_mesh += 1
            for prim in doc["meshes"][node["mesh"]].get("primitives", []):
                acc = doc["accessors"][prim["attributes"]["POSITION"]]
                if "min" not in acc or "max" not in acc:
                    continue
                for corner in range(8):
                    point = [
                        acc["min"][i] if (corner >> i) & 1 else acc["max"][i]
                        for i in range(3)
                    ]
                    world = _apply(matrix, point)
                    for i in range(3):
                        lo[i] = min(lo[i], world[i])
                        hi[i] = max(hi[i], world[i])
        for child in node.get("children", []):
            walk(child, matrix)

    for root_index in scene.get("nodes", []):
        walk(root_index, _ident())

    dims = [hi[i] - lo[i] for i in range(3)] if with_mesh else None
    return {
        "bytes": len(data),
        "triangles": triangles,
        "meshes": with_mesh,
        "materials": len(doc.get("materials", [])),
        "textures": len(doc.get("images", [])),
        "animations": len(doc.get("animations", [])),
        "dims": dims,
        "dims_sorted": sorted(dims) if dims else None,
        "generator": doc.get("asset", {}).get("generator", "?"),
    }


# -------------------------------------------------------------------------- fbx


def fbx_report(path: Path) -> dict:
    data = path.read_bytes()
    binary = data[:18] == b"Kaydara FBX Binary"
    return {
        "bytes": len(data),
        "binary": binary,
        "ucx": data.count(b"UCX_"),
        "col": data.count(b"COL_"),
        "sm": len(set(re.findall(rb"SM_[A-Za-z0-9_]+", data))),
    }


# ---------------------------------------------------------------------- renders


def render_info(path: Path) -> dict:
    info = {"w": None, "h": None, "std": None, "colors": None, "viewport": None}
    try:
        from PIL import Image, ImageStat
    except ImportError:  # Pillow is optional; dimensions still come from the header
        try:
            with path.open("rb") as fh:
                head = fh.read(33)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                info["w"], info["h"] = struct.unpack(">II", head[16:24])
        except OSError:
            pass
        return info

    try:
        with Image.open(path) as image:
            info["w"], info["h"] = image.size
            info["std"] = ImageStat.Stat(image.convert("L")).stddev[0]
            raw = image.convert("RGB").resize((160, 160)).tobytes()
    except Exception:
        return info

    pixels = [raw[i:i + 3] for i in range(0, len(raw), 3)]
    total = len(pixels)
    info["colors"] = len(set(pixels))
    red = sum(1 for p in pixels if p[0] > 90 and p[0] > p[1] + 15 and p[0] > p[2] + 15)
    green = sum(1 for p in pixels if p[1] > 90 and p[1] > p[0] + 15 and p[1] > p[2] + 15)
    # A flat, low-contrast frame carrying both axis colours at once is a Blender
    # viewport screenshot (X red / Y green grid lines), not a rendered frame.
    info["viewport"] = (
        info["std"] < 10.0
        and red > 0.002 * total
        and green > 0.002 * total
    )
    return info


# ----------------------------------------------------------------------- checks


def check_structure(folder: Path, slug: str, rep: Report) -> None:
    for name in REQUIRED_FILES:
        path = folder / name
        if path.is_file():
            rep.ok(name, f"{path.stat().st_size:,} B")
        else:
            rep.fail(name, "missing")
    for name in REQUIRED_DIRS:
        if (folder / name).is_dir():
            continue
        if name in ("textures",) :
            rep.warn(f"{name}/", "missing (create it and state 'procedural-only' if unused)")
        else:
            rep.warn(f"{name}/", "missing from the standard model tree")

    blend = folder / f"{slug}.blend"
    if not blend.is_file():
        rep.fail(f"{slug}.blend", "missing")
    else:
        size = blend.stat().st_size
        kind = blend_report(blend)
        if kind is None:
            rep.fail(f"{slug}.blend", f"{size:,} B — not a Blender container")
        elif size < 20_000:
            rep.warn(f"{slug}.blend", f"{size:,} B — suspiciously small ({kind})")
        else:
            rep.ok(f"{slug}.blend", f"{size:,} B ({kind})")


def check_exports(folder: Path, slug: str, rep: Report) -> tuple[dict | None, dict | None]:
    glb_path = folder / "exports" / f"{slug}.glb"
    fbx_path = folder / "exports" / f"{slug}.fbx"

    glb = None
    if not glb_path.is_file():
        rep.fail("exports/<slug>.glb", "missing")
    else:
        try:
            glb = glb_report(glb_path)
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            rep.fail("exports/<slug>.glb", f"unreadable: {exc}")
        else:
            dims = " x ".join(f"{d:.4f}" for d in glb["dims"]) if glb["dims"] else "?"
            rep.ok(
                "exports/<slug>.glb",
                f"{glb['bytes'] / 1048576:.2f} MiB — {glb['triangles']:,} tris, "
                f"{glb['meshes']} meshes, {glb['materials']} materials, "
                f"{glb['textures']} textures, {dims} m",
            )
            if glb["meshes"] > 60:
                rep.warn(
                    "draw calls",
                    f"{glb['meshes']} separate meshes in the GLB — merge static parts "
                    "unless the brief needs them separate",
                )

    fbx = None
    if not fbx_path.is_file():
        rep.fail("exports/<slug>.fbx", "missing")
    else:
        fbx = fbx_report(fbx_path)
        rep.ok(
            "exports/<slug>.fbx",
            f"{fbx['bytes'] / 1048576:.2f} MiB — {fbx['sm']} SM_ meshes, "
            f"UCX_={fbx['ucx']}, COL_={fbx['col']}",
        )
    return glb, fbx


def check_renders(folder: Path, notes_text: str, rep: Report) -> None:
    render_dir = folder / "renders"
    if not render_dir.is_dir():
        return

    exact, patterns = declared_pngs(notes_text, folder)
    on_disk = sorted(p for p in render_dir.iterdir() if p.suffix.lower() == ".png")

    for name, rels in sorted(exact.items()):
        if not any((folder / rel).is_file() for rel in rels):
            rep.fail(
                "declared render missing",
                f"{sorted(rels)[0]} is named in NOTES but absent",
            )

    undeclared: list[str] = []
    blank: list[str] = []
    viewport: list[str] = []
    flat: list[str] = []
    junk: list[str] = []

    for path in sorted(render_dir.iterdir()):
        if path.is_dir():
            continue
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            junk.append(path.name)
            continue
        if path.suffix.lower() != ".png":
            continue
        info = render_info(path)
        if info["std"] is not None and info["std"] < 2.0:
            blank.append(path.name)
        elif info["colors"] is not None and info["colors"] < 24:
            blank.append(path.name)
        elif info["viewport"]:
            viewport.append(path.name)
        elif info["std"] is not None and info["std"] < 8.0:
            flat.append(f"{path.name} (std {info['std']:.1f})")

        name = path.name
        if any(name.endswith(s) for s in PREVIEW_SUFFIXES):
            continue
        declared = name in exact or any(fnmatch.fnmatch(name, pat) for pat in patterns)
        if not declared:
            undeclared.append(name)

    if on_disk:
        rep.ok("renders", f"{len(on_disk)} PNGs on disk")
    else:
        rep.warn("renders", "no PNG renders in renders/")

    if blank:
        rep.fail("blank render", ", ".join(blank[:4]) + " — gate evidence cannot be empty")
    if viewport:
        rep.fail(
            "viewport screenshot",
            ", ".join(viewport[:4])
            + " — a Blender viewport grab with grid axes, not a render; gate evidence must "
            "come from a render",
        )
    if flat:
        rep.warn(
            "flat render",
            ", ".join(flat[:4]) + " — very low contrast; check exposure and key/fill ratio",
        )
    if undeclared:
        rep.warn(
            "undeclared renders",
            f"{len(undeclared)} render(s) not named in NOTES (e.g. {undeclared[0]})",
        )
    if junk:
        rep.warn("non-image files in renders/", ", ".join(junk[:4]))

    quarantined = [p for p in render_dir.rglob("*.png") if p.parent != render_dir]
    if quarantined:
        rep.warn(
            "quarantined evidence",
            f"{len(quarantined)} image(s) in renders/ subfolders, not counted as gate "
            f"evidence (e.g. {quarantined[0].parent.name}/{quarantined[0].name})",
        )


def check_claims(notes_block: dict[str, str], glb: dict | None, fbx: dict | None,
                 rep: Report) -> None:
    if not notes_block:
        rep.warn(
            "verification block",
            "no <!-- verify:begin --> block in NOTES.md — claims cannot be checked",
        )
        return
    if glb is None:
        return

    def compare_int(key: str, actual: int) -> None:
        if key not in notes_block:
            return
        try:
            claimed = int(notes_block[key].replace(",", "").strip())
        except ValueError:
            rep.fail(key, f"unparseable claim {notes_block[key]!r}")
            return
        if claimed == actual:
            rep.ok(key, f"{actual:,}")
        else:
            rep.fail(key, f"NOTES {claimed:,} vs export {actual:,}")

    compare_int("triangles", glb["triangles"])
    compare_int("meshes", glb["meshes"])
    compare_int("materials", glb["materials"])
    compare_int("textures", glb["textures"])
    compare_int("animations", glb["animations"])

    if "dimensions_m" in notes_block and glb["dims_sorted"]:
        claimed = parse_dims(notes_block["dimensions_m"])
        if claimed is None:
            rep.fail("dimensions_m", f"unparseable claim {notes_block['dimensions_m']!r}")
        else:
            actual = glb["dims_sorted"]
            deltas = [abs(a - c) for a, c in zip(sorted(claimed), actual)]
            if max(deltas) <= DIM_TOLERANCE_M:
                rep.ok(
                    "dimensions_m",
                    " x ".join(f"{d:.4f}" for d in actual)
                    + f" (max delta {max(deltas) * 1000:.1f} mm)",
                )
            else:
                rep.fail(
                    "dimensions_m",
                    "NOTES " + " x ".join(f"{c:.4f}" for c in sorted(claimed))
                    + " vs export " + " x ".join(f"{d:.4f}" for d in actual)
                    + f" (max delta {max(deltas) * 1000:.1f} mm)",
                )

    if "collision" in notes_block:
        claim = notes_block["collision"].strip().lower()
        has_collision = bool(fbx and (fbx["ucx"] or fbx["col"]))
        claims_collision = claim not in ("none", "n/a", "no", "false", "")
        if claims_collision and not has_collision:
            rep.fail(
                "collision",
                f"NOTES claims {notes_block['collision']!r} but no UCX_/COL_ geometry "
                "exists in the FBX",
            )
        elif not claims_collision and has_collision:
            rep.fail(
                "collision",
                "NOTES says none but the FBX contains UCX_/COL_ geometry",
            )
        elif claims_collision:
            rep.ok("collision", f"{notes_block['collision']} (UCX_={fbx['ucx']}, COL_={fbx['col']})")
        else:
            rep.ok("collision", "none claimed, none present")


def verify(slug: str, strict: bool) -> bool:
    folder = MODELS / slug
    rep = Report(slug)
    print(f"\n{'=' * 72}\nModel: {slug}\n{'=' * 72}")

    if not folder.is_dir():
        rep.fail("model folder", f"{folder} does not exist")
        return False

    check_structure(folder, slug, rep)
    glb, fbx = check_exports(folder, slug, rep)

    notes = folder / "NOTES.md"
    if notes.is_file():
        text, block = parse_notes(notes)
        check_renders(folder, text, rep)
        check_claims(block, glb, fbx, rep)

    if rep.fails:
        print(f"\nRESULT: FAIL — {len(rep.fails)} blocking issue(s)")
        for item in rep.fails:
            print(f"  - {item}")
        return False
    if strict and rep.warns:
        print(f"\nRESULT: FAIL (strict) — {len(rep.warns)} warning(s)")
        return False
    if rep.warns:
        print(f"\nRESULT: PASS with {len(rep.warns)} warning(s)")
    else:
        print("\nRESULT: PASS")
    return True


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(description="Verify delivered models against NOTES.md.")
    parser.add_argument("slugs", nargs="*", help="model slugs (folder names under models/)")
    parser.add_argument("--all", action="store_true", help="verify every model folder")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv[1:])

    if args.all:
        slugs = sorted(p.name for p in MODELS.iterdir() if p.is_dir())
    else:
        slugs = args.slugs
    if not slugs:
        parser.print_help()
        return 2

    results = {slug: verify(slug, args.strict) for slug in slugs}
    failed = [slug for slug, ok in results.items() if not ok]
    print(f"\n{'=' * 72}")
    print(f"SUMMARY: {len(results) - len(failed)}/{len(results)} model(s) PASS")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
