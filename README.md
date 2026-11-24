# Blender 3D Modeling Workshop

A prompt-driven 3D modeling workspace. Any coding agent opened in this folder becomes a
Blender artist: it takes a request like *"Make a 3d model for a realistic gun from ww2"*,
creates `Models/ww2-rifle/`, and builds the model in Blender through **Blender MCP** using
the **[blender-skills](https://github.com/arjun988/blender-skills)** pack (94 specialist
skills + references).

![Golden Desert Eagle — hero render](Models/golden-desert-eagle/renders/hero_34.png)

Every asset is built to measured real-world dimensions, documented in a `NOTES.md` that
records what was actually delivered, and audited by a script that re-measures the exported
files and fails when the record and the geometry disagree.

```
Blender 5.2  ⇐  MCP extension (localhost:9876)  ⇐  blender-mcp (stdio)  ⇐  your agent
```

## Requirements

| Piece | What you need |
|---|---|
| Blender | 5.2 LTS — built and tested on 5.2.3 |
| MCP extension | Official Blender Lab **MCP** add-on v1.0.3, enabled with Auto Start |
| MCP client | Official `blender-mcp` 1.30.0, installed as a `uv tool` (26 tools) |
| Skill pack | 94 skill files + 9 shared references in `.claude/skills/` (mirror in `.cursor/skills/`). About 15 are full playbooks; the rest are short routing/art-direction notes with their own `references/` files — read the substantive ones, don't assume all 94 carry equal weight |
| MCP configs | `.mcp.json` (Claude Code), `.cursor/mcp.json` (Cursor), `.vscode/mcp.json` |

## Start a session

1. **Open Blender.** The MCP extension starts its bridge automatically. To check:
   Edit → Preferences → Add-ons → **MCP** → “Server is running” (otherwise press
   **Start MCP Bridge Server**). Leave Blender open.
2. **Open this folder in your agent** (Claude Code, Cursor, VS Code, …). The MCP configs are
   already in place — restart the client once after the first open so it loads the
   `blender` server.
3. **Verify:**

   ```bash
   python scripts/preflight.py
   ```

   Expect `RESULT: READY`. Then ask the agent to run `get_objects_summary` — if it returns
   JSON, the bridge is live.

If the client or extension is missing on another machine:

```bash
uv tool install --python 3.11 \
  "git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp"
```

…and install the MCP extension from <https://www.blender.org/lab/mcp-server/>. Details in
`docs/MCP_SETUP.md`.

## Request a model

Just describe the object, the style, and the intended use:

> Make a 3d model for a realistic gun from ww2

> Model a low-poly PSX-style abandoned gas station, game-ready for Godot

> Build a rigged stylized treasure chest with an opening lid animation

The agent will:

1. Derive a slug and scaffold `Models/<slug>/` with `NOTES.md`, `refs/`, `renders/`,
   `textures/`, `versions/`, `exports/`.
2. Read `blender-director` plus the relevant discipline/style skills.
3. Block out in Blender over MCP, then detail, UV, material, light, and render.
4. Save `<slug>.blend`, export `GLB` + `FBX`, write the validation report into `NOTES.md`,
   and show you the hero render.
5. Run `python scripts/verify_model.py <slug>` and report PASS — the measured export must
   match the record before the model counts as delivered.

Deliverables per model:

```
Models/<slug>/
├── NOTES.md          # brief, detail spec, gate evidence, QA verdict
├── <slug>.blend      # editable Blender scene
├── versions/         # gate snapshots (_v01_blockout … _v04_export)
├── refs/             # reference images / dimensions
├── renders/          # hero + front/side/top + detail close-ups
├── textures/         # baked maps used by the exports
└── exports/          # <slug>.glb, <slug>.fbx
```

## Models in this repository

Three finished assets, each with an editable `.blend`, `GLB` + `FBX` exports, a full render
set and a record that `verify_model.py` checks against the files on disk.

| Model | Subject | Tris | Materials | Export | Record |
|---|---|---|---|---|---|
| **[Mosin-Nagant M91/30](Models/mosin-nagant-m91-30/NOTES.md)** | WW2 bolt-action rifle | 25,940 | 5 (3 baked textures) | GLB 5.1 MB · FBX 4.8 MB | [hero](Models/mosin-nagant-m91-30/renders/hero.png) |
| **[Mauser C96](Models/mauser-c96-original/NOTES.md)** | 1896 semi-automatic pistol | 33,277 | 4 | GLB 1.0 MB · FBX 0.9 MB | [hero](Models/mauser-c96-original/renders/hero.png) |
| **[Golden Desert Eagle](Models/golden-desert-eagle/NOTES.md)** | .50 AE pistol, gold titanium | 25,458 | 5 | GLB 0.7 MB · FBX 0.5 MB | [hero](Models/golden-desert-eagle/renders/hero_34.png) |

The Mosin and the Mauser ship `UCX_` collision proxies in their FBX files; the Desert Eagle
is a render-only still asset and declares no collision. All three are checked with:

```bash
python scripts/verify_model.py --all     # 3/3 PASS
```

Each `NOTES.md` carries its production brief, parts manifest, measured detail spec, gate
evidence, an audit-corrections table where an earlier claim was wrong, and a known-gaps
section. Those gaps are the honest part: no engine import has been run on any of the three,
none ships an LOD chain, and the Desert Eagle's materials are procedural and flatten on
export rather than shipping a baked texture set.

## Files that drive the workshop

| File | Purpose |
|---|---|
| `AGENTS.md` | **The manual.** Scope, preflight, routing, pipeline, deliverables, rules |
| `CLAUDE.md` | Claude Code entry point → `AGENTS.md` |
| `.cursor/rules/blender-workshop.mdc` | Always-on Cursor rule → `AGENTS.md` |
| `.claude/skills/` | 94 skills (`*/SKILL.md`) + `references/` (pipeline, naming, budgets) |
| `.cursor/skills/` | Mirror of the pack for Cursor |
| `scripts/preflight.py` | Checks Blender, extension, `blender-mcp`, configs, bridge identity, live socket |
| `scripts/new_model.py` | Creates a standard model folder + brief skeleton |
| `scripts/verify_model.py` | Audits a delivery: re-measures the GLB/FBX, checks the render set, compares both to the `NOTES.md` claims. `--all` audits every model |
| `scripts/mcp_call.py` | Fallback MCP stdio client (`summarize`, `list-tools`, `exec <script>`) for hosts with no MCP tools loaded |
| `Models/` | All output, one folder per model |
| `docs/MCP_SETUP.md` | Official MCP chain, tool catalog, install commands |
| `docs/SKILLS_GUIDE.md` | Upstream skill index and workflows |

## Ground rules

- One request → one folder. Existing models are never overwritten.
- Real-world scale: 1 Blender unit = 1 meter.
- Execute in Blender; don't hand back UI instructions or unexecuted code as if it ran.
- Save the `.blend` at every phase gate — versioned snapshots, not one overwritten file.
- Identity detail (lettering, marks, counted grooves/serrations) is modeled before UVs —
  never a blank panel where a rollmark belongs.
- Game-target looks are baked into `textures/`, and exports are round-tripped through a GLB
  re-import before delivery.
- One phase per MCP call. If the bridge wedges, the agent stops and reports instead of
  silently switching to `blender --background`.
- If Blender isn't connected, the agent stops and tells you, rather than inventing a model.
- Every delivery is machine-checked: `python scripts/verify_model.py --all` re-measures the
  exports and fails on any claim that no longer matches the file on disk.

## Verify a delivery

```bash
python scripts/verify_model.py --all          # audit every model
python scripts/verify_model.py ww2-rifle      # audit one
```

It parses the GLB (triangles, world-space bbox, meshes, materials, embedded textures), scans
the FBX for `UCX_`/`COL_` collision, checks every render is a real non-blank image, and
compares all of it to the `<!-- verify:begin -->` block in `NOTES.md`. Exit code 1 means the
record and the files disagree.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RESULT: BLOCKED` / nothing on 9876 | Enable the MCP extension and press **Start MCP Bridge Server** |
| MCP server missing in the client | Restart the client; check your client's config file |
| `blender-mcp` not found | `uv tool install --python 3.11 "git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp"` |
| Handshake errors / hanging calls | Wrong server package or the legacy `blender_mcp.py` addon enabled — see `docs/MCP_SETUP.md` |
| Blender renders look wrong | Ask the agent to re-check camera/engine and re-render; renders come from the scene, not the agent's imagination |

## Updating the skill pack

The pack is vendored (MIT). To refresh it:

```bash
git clone --depth 1 https://github.com/arjun988/blender-skills.git .upstream
cp -r .upstream/.claude/skills/. .claude/skills/
cp -r .upstream/.claude/skills/. .cursor/skills/
cp .upstream/SKILLS_GUIDE.md docs/
cp .upstream/LICENSE docs/blender-skills-LICENSE.md
rm -rf .upstream
python scripts/preflight.py
```

## License

The workshop tooling, documentation and 3D assets in this repository are MIT licensed — see
[`LICENSE`](LICENSE).

The vendored skill pack in `.claude/skills/` and `.cursor/skills/` is MIT ©
[arjun988](https://github.com/arjun988) — see
[`docs/blender-skills-LICENSE.md`](docs/blender-skills-LICENSE.md). Blender MCP is the
official Blender Lab project (<https://projects.blender.org/lab/blender_mcp>).
