#!/usr/bin/env python3
"""Preflight checks for the Blender modeling workshop.

Verifies Blender, the official Blender MCP extension, the `blender-mcp`
stdio client, the per-client MCP configs, the skill pack, and the live
bridge socket on localhost:9876.

Usage:  python scripts/preflight.py
Exit:   0 if every required check passes, 1 otherwise.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = os.environ.get("BLENDER_HOST", "localhost")
PORT = int(os.environ.get("BLENDER_PORT", "9876"))

OK = "  [ OK ]"
FAIL = "  [FAIL]"
WARN = "  [warn]"

failures: list[str] = []
warnings: list[str] = []


def pass_(label: str, detail: str = "") -> None:
    print(f"{OK} {label}" + (f" — {detail}" if detail else ""))


def fail(label: str, detail: str = "", hint: str = "") -> None:
    print(f"{FAIL} {label}" + (f" — {detail}" if detail else ""))
    if hint:
        print(f"         → {hint}")
    failures.append(label)


def warn(label: str, detail: str = "", hint: str = "") -> None:
    print(f"{WARN} {label}" + (f" — {detail}" if detail else ""))
    if hint:
        print(f"         → {hint}")
    warnings.append(label)


def find_blender() -> Path | None:
    env = os.environ.get("BLENDER_EXE")
    if env and Path(env).is_file():
        return Path(env)
    bases = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation",
        Path(r"C:\Program Files\Blender Foundation"),
    ]
    found: list[Path] = []
    for base in bases:
        if not base.is_dir():
            continue
        for child in base.glob("Blender *"):
            exe = child / "blender.exe"
            if exe.is_file():
                found.append(exe)
    mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if mac.is_file():
        found.append(mac)
    return max(found, key=lambda p: p.parent.name) if found else None


def blender_config_roots() -> list[Path]:
    roots: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(Path(appdata) / "Blender Foundation" / "Blender")
    home = Path.home()
    roots.append(home / "Library" / "Application Support" / "Blender")
    roots.append(home / ".config" / "blender")
    return [r for r in roots if r.is_dir()]


def find_extension() -> tuple[Path, str] | None:
    """Return (manifest path, version) for the official MCP extension."""
    hits: list[tuple[Path, str]] = []
    for root in blender_config_roots():
        for manifest in root.glob("*/extensions/*/*/blender_manifest.toml"):
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r'^id\s*=\s*"mcp"\s*$', text, re.MULTILINE):
                ver = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
                hits.append((manifest, ver.group(1) if ver else "?"))
    return hits[-1] if hits else None


def find_legacy_addon() -> Path | None:
    for root in blender_config_roots():
        hits = sorted(root.glob("*/scripts/addons/blender_mcp.py"))
        if hits:
            return hits[-1]
    return None


def port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.5)
        return sock.connect_ex((HOST, PORT)) == 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    print("\nBlender 3D Modeling Workshop — preflight\n" + "=" * 46)

    blender = find_blender()
    if blender:
        version = "unknown"
        try:
            out = subprocess.run(
                [str(blender), "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            version = (out.stdout or "").splitlines()[0].strip() or version
        except Exception as exc:  # noqa: BLE001 - report any probe failure
            version = f"version probe failed: {exc}"
        pass_("Blender", f"{version} ({blender})")
    else:
        fail(
            "Blender",
            "executable not found",
            "install Blender 5.1+, or set BLENDER_EXE to blender.exe",
        )

    extension = find_extension()
    if extension:
        manifest, version = extension
        pass_("Blender MCP extension", f"v{version} ({manifest.parent})")
    else:
        fail(
            "Blender MCP extension",
            "official 'MCP' extension not installed",
            "Blender → Edit → Preferences → Get Extensions → search 'MCP' → install, "
            "or grab mcp-1.0.3.zip from blender.org/lab/mcp-server",
        )

    bridge_up = port_open()

    legacy = find_legacy_addon()
    if legacy and bridge_up:
        fail(
            "bridge identity",
            f"port {PORT} is open while the legacy community addon is installed",
            "both bind port 9876, so this bridge is probably the legacy addon, not the "
            "official extension. Remove or rename scripts/addons/blender_mcp.py, restart "
            "Blender, then rerun. A session served by the legacy addon is not MCP-verified",
        )
    elif legacy:
        warn(
            "legacy community addon present",
            str(legacy),
            "not listening right now, but never enable it — it binds port 9876 and speaks "
            "a different protocol from the official extension",
        )

    client = shutil.which("blender-mcp")
    if not client:
        fallback = Path.home() / ".local" / "bin" / ("blender-mcp.exe" if os.name == "nt" else "blender-mcp")
        client = str(fallback) if fallback.is_file() else None
    if client:
        try:
            out = subprocess.run([client, "--help"], capture_output=True, text=True, timeout=25)
            if "MCP server for Blender" not in (out.stdout or ""):
                raise RuntimeError("unexpected --help output (wrong package?)")
        except Exception as exc:  # noqa: BLE001
            warn("blender-mcp client", f"{client} — verification failed: {exc}")
        else:
            pass_("blender-mcp client", f"official stdio server ({client})")
    else:
        fail(
            "blender-mcp client",
            "not installed",
            'uv tool install --python 3.11 "git+https://projects.blender.org/lab/'
            'blender_mcp.git#subdirectory=mcp"',
        )

    configs = [".mcp.json", ".cursor/mcp.json", ".vscode/mcp.json"]
    present = [name for name in configs if (ROOT / name).is_file()]
    if present:
        pass_("MCP client configs", ", ".join(present))
    else:
        fail("MCP client configs", "none found", "restore .mcp.json from this repo")

    skills = list((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    if len(skills) >= 90:
        pass_("Skill pack", f"{len(skills)} skills in .claude/skills")
    else:
        fail(
            "Skill pack",
            f"only {len(skills)} SKILL.md files found",
            "re-copy the pack from github.com/arjun988/blender-skills",
        )

    if bridge_up:
        pass_("Blender MCP bridge", f"{HOST}:{PORT} reachable")
    else:
        fail(
            "Blender MCP bridge",
            f"nothing listening on {HOST}:{PORT}",
            "open Blender → Edit → Preferences → Add-ons → MCP → Start MCP Bridge "
            "Server (enable Auto Start), then rerun this script",
        )

    print("=" * 46)
    if failures:
        print(f"RESULT: BLOCKED — {len(failures)} required check(s) failed.")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("RESULT: READY — Blender MCP bridge is available." + (
        f" ({len(warnings)} warning(s))" if warnings else ""
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
