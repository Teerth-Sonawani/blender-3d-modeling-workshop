# Blender 3D Modeling Workshop — Agent Manual

**This folder has exactly one purpose: produce 3D models in Blender.** Every agent working
here is a 3D artist / technical artist. There is no app, no website, no library, and no
codebase to maintain here. If a request is not about making, revising, or exporting a 3D
model, say so and ask for a modeling request instead of doing the other work.

Two systems power every job:

1. **Blender MCP** — the official Blender MCP chain:

   ```
   agent  ⇐ MCP / stdio ⇒  blender-mcp  ⇐ TCP (localhost:9876) ⇒  Blender MCP extension
   ```

   `blender-mcp` is Blender's official stdio server (`uv tool` install, 26 tools). The
   **MCP** extension (Blender Lab v1.0.3) runs inside **Blender 5.2** and executes the
   Python. See `docs/MCP_SETUP.md`.
2. **The Blender Skills pack** — 94 specialist skills + shared references in
   `.claude/skills/` (mirrored at `.cursor/skills/`), from
   [arjun988/blender-skills](https://github.com/arjun988/blender-skills) v1.3.0 (MIT).

## Iron rules

- **Execute through MCP.** Never answer a modeling request with a UI walkthrough when a
  tool call can do it. Never claim a model exists that you did not build in Blender.
- **One request → one folder** under `models/`. Never model two unrelated requests into one
  scene, never reuse a previous model's scene as scratch space.
- **Part-first, one part at a time.** No geometry until the parts manifest exists in
  `NOTES.md`; no part begun until the one before it passes its own gate; never open a second
  part to escape a stuck first one. See §5.1.
- **Query before you touch.** Call `get_objects_summary` (or inspect `bpy.data`) before
  editing. Never assume the scene is empty.
- **One Blender unit = one meter.** Model at real-world dimensions.
- **Save the `.blend` before** any `execute_blender_code` that deletes, joins, remeshes, or
  applies modifiers.
- **Never overwrite** an existing model folder or an existing `.blend`. If the slug exists,
  continue that model; use `--v2` only for a deliberate second take.
- **If MCP is unavailable, stop and say so.** You may write a `bpy` script and a plan, but
  label it clearly as *unexecuted*. Do not fake screenshots, renders, or file exports.
- **Report reality.** Tri counts, files, and validation results must come from the scene.
- **Verify the record, not just the model.** `python scripts/verify_model.py <slug>` must
  PASS before delivery. It re-measures the GLB/FBX and the render set and fails when
  `NOTES.md` diverges from the files on disk.

## 1. Preflight — run before every modeling job

```bash
python scripts/preflight.py
```

It checks the Blender install, the official MCP extension, the `blender-mcp` client, the
MCP configs, the skill pack, and whether the bridge socket on `localhost:9876` is
accepting connections.

- **Bridge identity** → if port 9876 is open *and* the legacy `blender_mcp.py` addon is
  installed, preflight fails: both bind the same port, so the bridge is probably the legacy
  addon and the session is not MCP-verified. Remove or rename the legacy file, restart
  Blender, rerun.
- **All OK** → call `get_objects_summary` over MCP to confirm the bridge, then proceed.
- **Bridge FAIL** → stop and tell the user: *open Blender → Edit → Preferences → Add-ons →
  MCP → **Start MCP Bridge Server** (enable **Auto Start**)*, then retry.
- **MCP tools missing entirely** → the client needs a restart to load `.mcp.json`.

## 2. Read the skills before modeling

The skills are prompt-engineering playbooks, not code. Read them with normal file tools.
Minimum reading order for any job:

1. `.claude/skills/blender-director/SKILL.md` — production brief, routing, validation gates
2. `.claude/skills/references/asset-pipeline.md` — phase order. Never skip planning.
3. `.claude/skills/references/mcp-integration.md` — execution protocol
4. `.claude/skills/references/naming-conventions.md` — before creating a single object
5. `.claude/skills/references/polycount-budgets.md` — pick the budget up front
6. The **discipline** skill for the subject (table below)
7. The **style** skill if a style was named (realistic, lowpoly, PSX, anime, …)
8. `.claude/skills/references/validation-checklist.md` — before delivery

> The pack's `references/mcp-tools.md` documents the older community server
> (`get_scene_info`, `look`, `get_viewport_screenshot`). This workshop runs the **official**
> server; use the tool table in section 6 and treat the live MCP schemas as authoritative.

### Discipline routing

| Request | Discipline skill | Then |
|---|---|---|
| Gun, weapon, machinery, industrial part | `hard-surface` | `materials` → `uv-workflow` → `asset-optimization` |
| Everyday object, tool, furniture, kitbash prop | `prop-artist` | `uv-workflow` → `materials` |
| Car, tank, plane, ship, mech | `vehicle-artist` | `hard-surface` → `lod-pipeline` |
| Building, terrain, modular kit, level piece | `environment-artist` | `scene-assembly` → `geometry-nodes` |
| Human character, clothing | `character-artist` | `retopology` → `rigging` |
| Monster, creature, alien | `creature-artist` | `sculpting` → `retopology` |
| Trees, plants, foliage | `vegetation-artist` | `geometry-nodes` |
| VFX, destruction, smoke | `vfx-fx` / `physics-sim` | `materials` |

### Style routing

`realistic-style` · `lowpoly-style` · `psx-horror-style` · `stylized-style` · `anime-style` ·
`voxel-style` · `isometric-style` · `horror-style` · `noir-style` · `hand-painted-style` ·
`stop-motion-craft-style` · `sculpting` for organic detail. Historical subjects (WW1/WW2,
western, samurai, medieval) also read `historical-worlds`. Engine delivery additionally uses
`unity-export`, `unreal-export`, or `godot-export`; generic delivery uses `export-pipeline`.

## 3. Create the model folder

Derive a slug from the **subject**, not the style: lowercase kebab-case, 2–5 words.

> "Make a 3d model for a realistic gun from ww2" → `models/ww2-rifle/`

```bash
python scripts/new_model.py ww2-rifle --title "Realistic WW2 Rifle"
```

That creates the standard tree and a `NOTES.md` brief skeleton. Then fill the brief in
before touching geometry.

```
models/<slug>/
├── NOTES.md          # brief, detail spec, gate evidence, QA verdict, known gaps
├── <slug>.blend      # current working scene
├── versions/         # gate snapshots: _v01_blockout … _v04_export
├── refs/             # reference images, dimension notes
├── renders/          # hero + front/side/top + part_*.png + detail_*.png close-ups
├── textures/         # baked maps referenced by the exports
├── scripts/          # the bpy snippets used per phase, for reproducibility
└── exports/          # <slug>.glb and <slug>.fbx
```

## 4. Production brief (required, in NOTES.md, before modeling)

```
Type:              prop / hard-surface / vehicle / character / environment
Target:            game / cinematic / portfolio / 3D print
Style:             realistic / stylized / lowpoly / ...
Dimensions:        real-world size in meters
Poly budget:       triangles (see polycount-budgets.md)
Texture delivery:  baked maps (BC/N/R/M) or procedural-only — game targets must bake
Pivot:             grip / floor contact / hinge / center
Export:            GLB + FBX
Animation:         none / rigged / animated
LOD / collision:   LOD0–LODn + UCX_/COL_ proxy, or "none — reason"
Reference canon:   the one photo/measurement set used; variant + known deviations
Identity features: 5–10 features that make this object recognizable
Skills:            ordered list of skills in use
```

Budget defaults: first-person hero weapon 10k–30k tris · hero prop 15k–50k · standard prop
5k–15k · background prop 500–5k · small hardware 100–500. Realistic work sits at the upper
range; a `realistic` + game target also needs LODs if the asset is used at distance.

### 4.1 Fidelity contract — fill this in before modeling

"Realistic" is judged in close-up, not only at silhouette distance. Identity detail is part
of the model, not polish.

Record a **measured detail spec** in `NOTES.md` from the canon reference:

| Feature | Real spec | Modeled as | Tolerance | Verified |
|---|---|---|---|---|
| grip flutes | 24 grooves @ 3.3 mm | 24 @ 3.3 mm | count exact | close-up render |

- Derive counts, pitches and dimensions by **measuring the canon reference** — never from
  memory or "about right". If sources disagree, choose one variant, write down the number
  used, and list the alternative in *Known gaps*.
- **Identity features are built before UVs.** Rollmarks/lettering, serials, sight
  graduations, screw slots, proof marks, maker logos and correct groove/serration counts are
  cheap at blockout and expensive to retrofit.
- A blank recessed panel is **not** a rollmark. Lettering is real geometry (text object →
  mesh, extruded 0.2–0.4 mm) or a baked normal map; if neither is possible, say so in
  *Known gaps* and in the delivery message.
- Every detail-dense area (grip, hammer, sight, markings) needs a `renders/detail_*.png`
  close-up before delivery.
- Do not silently drop a feature because it "won't survive export". Bake it, or report it.

## 5. Build sequence

**This is not a single pass over the model.** Steps 2–4 run once *per sub-part*, inside the
part loop in §5.1; step 1 runs once; steps 5–12 run only at assembly (§5.2), after every
part has passed its own gate. Do not skip phases. Save between them. Query the scene after
each phase.

### 5.1 Part-first loop — gate 0, before everything else

A finished model is a stack of finished parts, and "finished" is decided per part. A part is
done when it is measurably correct **on its own** — not when the whole object reads roughly
right from the hero camera. Depth beats coverage: one part at a time, held to the standard of
a close-up render, is the only accepted order of work.

#### The parts manifest — required before the first edit

Enumerate every sub-part a person would name when describing the object (barrel, receiver,
bolt, magazine, trigger group, stock, buttplate, rear sight, front sight, sling swivel …).
Split until each part has **one job**: a part doing more than ~3 distinct things is two
parts. Write it into `models/<slug>/NOTES.md` in build order:

| # | Part | Collection | Dim spec (m) | Budget (tris) | Detail spec | Status |
|---|---|---|---|---|---|---|
| 01 | Barrel | `COL_Part_Barrel` | 0.600 × Ø0.015 | 900 | 6 grooves @ 60°, chamber ring | PASS |
| 02 | Receiver | `COL_Part_Receiver` | 0.220 × 0.050 | 3 400 | rollmark, ejection port, 2 pins | in progress |

- **Status** is only ever `pending`, `in progress`, `PASS`, `PASS WITH NOTES — <gap>`, or
  `FAIL — <reason>`. Exactly one row may read `in progress`.
- **Build order is dependency order**: structural parts others mount to first, then
  covering/secondary parts, then detail-only parts.
- Every dimension and count is a **number** taken from the canon reference. "About right" is
  not a spec.

#### The loop — this part, then the next, nothing in between

1. **Isolate.** Work inside that part's `COL_Part_<Name>` collection. Hide or lock the other
   part collections while modeling so a mistake cannot hide behind neighbouring geometry.
2. **Measure.** Open the canon reference for this part and write its real dimensions and
   counted details into its manifest row before building them.
3. **Blockout.** Primary forms of this part only, at its measured dimensions. Record the
   delta against the spec.
4. **Secondary + detail.** Panel breaks, construction logic, fasteners, lettering, wear
   geometry and every identity feature of this part. Counted details verified
   **programmatically** — a `bpy` print of the real count against the spec, never by eye.
5. **Per-part cleanup.** Merge by distance, recalc normals, no interior faces, no new
   non-manifold edges, transforms applied on this part.
6. **Per-part close-up.** Render `renders/part_<name>.png` framed on this part alone at canon
   lighting, plus one frame with the rest of the model hidden. **Look at both**, diff against
   the reference crop, write a gap list (max 5), fix, re-render. Max 3 passes; a gap left
   after the third is written down, never waved through. A viewport screenshot is **not** a
   render — a grid-and-cursor grab is not gate evidence, and `verify_model.py` fails it.
7. **Gate the part.** `PASS` requires all of: dimensions inside tolerance · every counted
   detail matches its number · mesh health clean · close-up actually inspected · no
   placeholder geometry (raw primitives, unnamed blockout cubes, blank panels where detail
   belongs). Otherwise `PASS WITH NOTES` (named gap) or `FAIL`. **A `FAIL` part is fixed
   before the next part is started.**

#### Hard rules

- **No interleaving.** Never model, tweak or "quickly fix" part B while part A is
  `in progress`. Finish A, or record why A is blocked — then continue **in manifest order**,
  not by jumping to whatever is easiest.
- **No detail debt.** "I'll add the markings once the rest is done" fails the gate. A part's
  detail is built while that part is open, at the tier it belongs to.
- **No retro-fitting.** If a part needs a neighbour's dimension, measure the neighbour.
  Changing an already-`PASS` part re-opens its row and re-runs its gate.
- **No assembly shortcuts.** Joining, cross-part baking, the single packed UV atlas, global
  cleanup, material unification, hero renders and export belong to assembly and cannot start
  while any row reads `pending`, `in progress` or `FAIL`.
- **The manifest is the progress report.** A part with no gate evidence is not done, however
  good the viewport looks. Report the remaining rows honestly at delivery.
- **Invalid evidence is quarantined, not deleted.** A render that fails its gate (blank, a
  viewport grab, the wrong part, stale) moves to `renders/_invalid_evidence/` and the record
  states why. Deleting it hides the miss; leaving it in `renders/` presents it as proof.

### 5.2 Assembly — only after every part passes

Steps 5–12 below are assembled-model phases and start only once every manifest row reads
`PASS` or `PASS WITH NOTES`: join or keep parts as the brief dictates, cross-part cleanup, one
packed UV atlas at consistent texel density, unified `MAT_` materials, bake for game targets,
lights and hero renders, optimization, export, validation, round-trip.

1. **Scene scaffold** — save a fresh scene as `models/<slug>/<slug>.blend`, plus
   collections: `COL_Blockout`, `COL_Geo`, `COL_Collision`, `COL_Lights`, `COL_Cameras`,
   `COL_Export`. If the current Blender file is dirty and not ours, ask before resetting.
   Snapshot to `versions/<slug>_v01_blockout.blend` at the end of the phase.
2. **Blockout** — primary forms only, correct overall dimensions and silhouette. Match the
   canon camera, record landmark deltas in `NOTES.md`, and take an MCP screenshot. Fix the
   blockout once against measurements — do not discover proportion errors after detailing.
3. **Secondary forms** — panel breaks, ribs, recesses, structural logic. Match how the real
   object is manufactured; stamped steel does not look like sci-fi greebles.
4. **Detail tier** — screws, sights, **lettering/markings**, wear geometry and every identity
   feature from the fidelity contract. Counts and pitches verified programmatically and in a
   close-up render. Snapshot `_v02_detail`.
5. **Cleanup** — merge by distance, recalc normals, remove interior faces, apply transforms.
   Cleanup must PASS before any export.
6. **UVs** — seams on hidden construction edges, consistent texel density, packed 0–1. Hero
   assets get **hand-placed seams**; smart-project-only is a fail. Record packing efficiency
   and texel-density variance. Snapshot `_v03_uv`.
7. **Materials** — PBR (`MAT_` prefix), plausible values, 1–3 materials for a prop. Wear is
   directional edge/polish masks plus bevels, not uniform noise. For game targets **bake**
   base colour, roughness and normal into `textures/` so the look survives GLB/FBX —
   procedural node graphs alone are a portfolio-only delivery and must be stated as such.
8. **Lights + camera + renders** — look-dev at 640×360 first; only then key/fill/rim,
   `CAM_Hero`, and the four views into `renders/` at 1920×1080. Add close-ups
   (`renders/detail_*.png`) for every detail-dense area. At most two full-resolution passes
   per view.
9. **Optimization** — verify tri count against budget; decimate or rebuild if over. Game
   targets also need the brief's LOD chain and a simple `UCX_`/`COL_` collision proxy.
10. **Export** — `exports/<slug>.glb` and `exports/<slug>.fbx`, selection = `COL_Export`
    contents only, transforms applied, meters, +Y up / -Z forward for FBX. Export from a
    **duplicate** of the scene/objects: never translate or apply pivots to the working mesh.
    Snapshot `_v04_export`.
11. **Validation** — run `references/validation-checklist.md` **and**, when a reference was
    supplied, `references/visual-match-checklist.md`; then `qa-review` for an explicit
    verdict. Record tris, materials, dimensions, UV state, match ratings and known gaps in
    `NOTES.md`. Your own audit script is a supplement, never a substitute. Then fill the
    `<!-- verify:begin -->` block with the **measured export** values and run
    `python scripts/verify_model.py <slug>`; it must PASS. If a number in the prose disagrees
    with the export, correct the prose — never the block.
12. **Round-trip** — import the GLB into a fresh scene, verify dimensions, pivot, orientation
    and material values, render one comparison frame, then discard the import scene without
    saving over the working file. Record the result.

### Phase gates — no gate, no progress

| Gate | Required evidence |
|---|---|
| **Part** (each sub-part, gate 0) | manifest row with measured dims and verified detail counts; mesh health; `renders/part_<name>.png` close-up inspected; no placeholders |
| Blockout | screenshot at canon camera; landmark deltas within tolerance |
| Detail | identity features present; counts/pitch verified; close-up render |
| UV | hand seam plan; packing % and texel density recorded |
| Material | low-res look-dev crop; baked map list for game targets |
| Export | GLB re-imported; dimensions/pivot/materials/orientation checked |
| Claims | `python scripts/verify_model.py <slug>` PASS — the `verify` block matches the export |
| Delivery | mechanical checklist + visual-match ≥ 8/10 + QA verdict |

Versioned saves: `versions/<slug>_v01_blockout.blend` … `_v04_export.blend`. Keep the
current scene at `<slug>.blend`; never overwrite the only copy.

### Naming

`COL_` collections · `SM_` meshes (`SM_Weapon_Rifle_A`) · `MAT_` materials
(`MAT_Metal_Parkerized`) · `T_` textures · `CAM_` cameras · `LGT_` lights · `ARM_` armatures ·
`UCX_`/`COL_` collision. PascalCase after the prefix, underscores, `_01` numbering, < 64 chars.

## 6. MCP tool catalog (official server)

`execute_blender_code` is the workhorse: it takes `{"code": "..."}` and returns
`{"status", "result", "stdout"}`. Everything below is available — verify schemas live before
calling.

| Task | Tool |
|---|---|
| Run Python in Blender | `execute_blender_code` |
| Scene inventory | `get_objects_summary`, `get_object_detail_summary(name)` |
| File-level inspection | `get_blendfile_summary_datablocks`, `..._path_info`, `..._missing_files`, `..._linked_libraries`, `..._usage_guess` |
| Look at the viewport | `get_screenshot_of_window_as_image`, `get_screenshot_of_window_as_json`, `get_screenshot_of_area_as_image(area_ui_type)` |
| Save renders to disk | `render_viewport_to_path(output_path)`, `render_thumbnail_to_path(output_path)` |
| Blender API help | `search_api_docs(query)`, `get_python_api_docs(identifier)`, `search_manual_docs(query)` |
| Editor navigation | `jump_to_tab_by_name`, `jump_to_view3d_object_by_name` |
| Offline `.blend` jobs | `execute_blender_code_for_cli`, `*_for_cli` summaries |

There are **no dedicated mesh/material/export tools**: create, modify, UV, shade, and export
with `bpy` inside `execute_blender_code`. `get_scene_info`, `look`, and
`get_viewport_screenshot` do not exist here.

### MCP execution habits

- One conceptual step per call. `print()` a short result so the returned `stdout` shows it.
- Wrap risky code in `try/except` and print the traceback; never swallow an MCP error.
- Save with `bpy.ops.wm.save_as_mainfile(filepath=...)` at every phase gate.
- Keep the exact Python used for each phase in `models/<slug>/scripts/` when practical.
- Take a screenshot after blockout, after materials, and before delivery, and actually look
  at it before declaring a phase done.
- Blender 5.2 specifics: look shader nodes up by `type`, not localized name
  (`next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`); read enum
  identifiers from `bl_rna` instead of hardcoding them; set material color on shader inputs,
  not `material.diffuse_color` (viewport only).
- **One phase per call.** Never chain five phases into one `execute_blender_code`. Split
  long operations (remesh, bake, renders) into their own calls; a call that times out did
  not complete the phase.
- **One part per call.** Each `execute_blender_code` block builds, details or fixes a single
  `COL_Part_*`. Batch-scripting five parts feels fast and is unverifiable — you cannot
  inspect what you never looked at in isolation.
- **No silent fallback.** If the bridge wedges: call `get_objects_summary` once, check
  `localhost:9876`, restart the bridge, retry once — time-boxed to about 3 minutes. Then
  stop and report. Only use `blender --background` if the user approves, and log it under
  *Execution deviations* in `NOTES.md`; anything run that way is not MCP-verified.
- **When the host agent has no MCP tools loaded**, `python scripts/mcp_call.py
  summarize|list-tools|exec <script.py>` speaks the same stdio protocol as the client. It is
  the fallback client, not a licence to bypass the bridge — log it the same way.
- **Session must match disk.** At delivery, the open Blender file is the model `.blend`,
  saved, with no unsaved changes. If a script changed the file outside MCP, reload it in the
  live session or say so.
- **Docs before guessing.** When a 5.2 operator or property is uncertain, call
  `search_api_docs` / `get_python_api_docs` once instead of burning cycles on API drift.

## 7. Reference images

If the user attaches a photo/concept, save it to `models/<slug>/refs/`.

1. **Pick one canon.** Choose the single sharpest, most representative reference (or one
   measured set) and name it in `NOTES.md`. Other images are secondary. Generations differ:
   do not blend features from three variants into one asset. State the variant and the
   deviations.
2. **Write the analysis first** (`references/reference-analysis-template.md`): subject,
   proportions, camera, lighting, palette hex values, hero features. No Blender edits before
   this exists.
3. **Camera match before detail** (`references/reference-image-match.md`).
4. **Screenshot-compare loop** after blockout, detail and materials: MCP screenshot or render
   at the canon camera, gap list (max 5), fix, re-compare — max 3 iterations.
5. **`references/visual-match-checklist.md` before delivery.** Rate every category
   Match/Close/Miss; pass is ≥ 8/10. Record the table in `NOTES.md`. A mechanical audit does
   not replace this.

If no reference is given for a real object (e.g. a WW2 weapon), establish dimensions and
identity features from knowledge, write them in the brief, and say what the proportions are
based on.

## 8. Delivery message

When the model is finished, report:

- absolute path to the folder and the `.blend`
- what was built, at what scale
- parts manifest status: how many sub-parts, which are `PASS`, which carry notes, which failed
- final triangle count and material count vs budget
- exports (`GLB`, `FBX`) and renders that exist **on disk**
- validation result, plus anything approximate or unfinished
- fidelity statement: replica or measured representation, the largest dimensional delta,
  and the identity features that are approximate or missing
- any pipeline deviation (headless run, skipped gate) and what it leaves unverified
- engine import / round-trip checks that were **not** run
- the `scripts/verify_model.py` result (PASS, or the exact failing checks)
- no invented metrics — token counts, timings or file sizes you did not measure

Show the hero render in the reply when the client can display it
(`renders/hero.png`). Do not describe an image you have not rendered.

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Nothing listening on 9876 | extension bridge stopped | Blender → Edit → Preferences → Add-ons → MCP → Start MCP Bridge Server; enable Auto Start |
| `blender-mcp` not found | official client not installed | `uv tool install --python 3.11 "git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp"` |
| Calls hang or handshake errors | community `blender-mcp` wrapper, or legacy addon on 9876 | configs must run the uv-tool `blender-mcp`; keep `scripts/addons/blender_mcp.py` disabled |
| MCP server listed but no tools | client started before config existed | restart the client |
| Scene edits hit the wrong file | user's own Blender session | confirm the open file is `models/<slug>/<slug>.blend` |
| Blender 5.2 operator/API changed | API drift | `search_api_docs` / `get_python_api_docs` instead of guessing |

## 10. Do not

- Do not build web UIs, docs sites, or unrelated scripts in this folder.
- Do not delete or "clean up" models you did not create.
- Do not modify the skills pack in place; update it from upstream (see `README.md`).
- Do not commit `.blend1` backups, caches, or multi-hundred-MB intermediates.
- Do not finish a job through `blender --background` without telling the user; a silent
  fallback is a failed gate, not a workaround.
- Do not chain multiple modeling phases into one MCP call.
- Do not start part B while part A is `in progress`, and do not mark a part `PASS` without
  its measured dimensions, verified detail counts and an inspected close-up render.
- Do not smart-project a hero asset and call the UVs done.
- Do not leave a blank panel where lettering belongs, or skip counted details (flutes,
  serrations, graduations) — model them or declare them missing.
- Do not export before cleanup passes, translate working meshes for a pivot, or ship without
  a GLB round-trip.
- Do not claim a 1:1 replica; state the measured delta.
- Do not overwrite the only `.blend`; keep gate snapshots in `versions/`.
