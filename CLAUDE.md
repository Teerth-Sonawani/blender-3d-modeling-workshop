# Claude Code entry point

This folder is a **Blender 3D modeling workshop**. Read `AGENTS.md` in full before doing
anything — it is the authoritative operating manual.

Short version:

- One job only: build 3D models in Blender through the `blender` MCP server (official
  Blender MCP extension + `blender-mcp` stdio client).
- Run `python scripts/preflight.py`, then confirm MCP with `get_objects_summary`.
- For each request, create `models/<subject-slug>/` with `python scripts/new_model.py <slug>`.
- Read `.claude/skills/blender-director/SKILL.md` plus the discipline/style skills in
  `.claude/skills/` before modeling.
- Build **one sub-part at a time**: the parts manifest in `NOTES.md` fixes the order, and a
  part passes its own gate (measured dims, verified detail counts, inspected close-up
  render) before the next one starts. Never interleave two parts.
- Deliver `<slug>.blend`, `exports/<slug>.glb`, `exports/<slug>.fbx`, and `renders/`.
- Never report a model that was not actually built and saved in Blender.
