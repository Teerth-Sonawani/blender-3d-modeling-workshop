# Blender MCP connection

This workshop uses **Blender's official MCP chain**, not the community
`blender-mcp` add-on:

```
agent  ⇐ MCP / stdio ⇒  blender-mcp  ⇐ TCP socket (localhost:9876) ⇒  Blender MCP extension
```

| Component | What it is | Where |
|---|---|---|
| Blender | 5.2.3 LTS | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| MCP extension | Official Blender Lab add-on v1.0.3 (`lab_blender_org/mcp`) | Blender user extensions dir |
| `blender-mcp` | Official stdio MCP server (Python 3.11) | `C:\Users\<user>\.local\bin\blender-mcp.exe` |
| Client configs | Claude Code / Cursor / VS Code | `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` |

## Install (already done on this machine)

1. **Blender 5.1+** and the **MCP extension**
   (Blender → Edit → Preferences → Get Extensions → search “MCP”, or the zip from
   <https://www.blender.org/lab/mcp-server/>). Enable it; Auto Start is on by default.
2. **MCP server** (separate Python process, launched by the agent):

   ```bash
   uv tool install --python 3.11 \
     "git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp"
   ```

   Verify: `blender-mcp --help` prints `MCP server for Blender`.

## Start

1. Open Blender and confirm the bridge is running:
   Edit → Preferences → Add-ons → **MCP** → “Server is running” (or press
   **Start MCP Bridge Server**). Keep Blender open.
2. Restart your agent client once after opening this folder so it loads the
   `blender` server.
3. `python scripts/preflight.py` → expect `RESULT: READY`.
4. Ask the agent to run `get_objects_summary`; if it returns JSON, the chain is live.

## Available tools (official server, 26)

| Purpose | Tool |
|---|---|
| Run Python in Blender | `execute_blender_code` |
| Scene inventory | `get_objects_summary`, `get_object_detail_summary` |
| File summaries | `get_blendfile_summary_*` |
| Visual check | `get_screenshot_of_window_as_image`, `get_screenshot_of_window_as_json`, `get_screenshot_of_area_as_image` |
| Save renders to disk | `render_viewport_to_path`, `render_thumbnail_to_path` |
| Blender docs | `search_api_docs`, `get_python_api_docs`, `search_manual_docs` |
| Editor navigation | `jump_to_*` |
| Open a .blend and run code | `execute_blender_code_for_cli` (+ `*_for_cli` summaries) |

`execute_blender_code` returns `{"status", "result", "stdout"}`. Print values inside
the snippet to get data back.

## Notes

- The community `blender-mcp` add-on (`scripts/addons/blender_mcp.py`) is also present
  on this machine but is **not** used: it speaks a different protocol and binds the same
  port. Leave it disabled.
- The skill pack's `references/mcp-tools.md` describes the community tool names
  (`get_scene_info`, `look`, `get_viewport_screenshot`). Use the table above — the live
  MCP tool schemas are authoritative.
- `execute_blender_code` runs arbitrary Python in the open Blender file. Save first.
