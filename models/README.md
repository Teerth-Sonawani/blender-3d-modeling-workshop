# models

One folder per model request. Slug = the **subject**, lowercase kebab-case, 2–5 words.

| Folder | Subject | Tris | Collision |
|---|---|---|---|
| [`mosin-nagant-m91-30/`](mosin-nagant-m91-30/) | WW2 bolt-action rifle | 25,940 | 4 `UCX_` (FBX) |
| [`mauser-c96-original/`](mauser-c96-original/) | 1896 semi-automatic pistol | 33,277 | 4 `UCX_` (FBX) |
| [`golden-desert-eagle/`](golden-desert-eagle/) | .50 AE pistol, gold titanium | 25,458 | none — render-only |

```
models/ww2-rifle/
├── NOTES.md          # brief, detail spec, gate evidence, QA verdict
├── ww2-rifle.blend   # current Blender scene
├── versions/         # gate snapshots (_v01_blockout … _v04_export)
├── refs/             # reference images, dimension notes
├── renders/          # hero + front/side/top + detail close-ups
├── textures/         # baked maps used by the exports
├── scripts/          # bpy snippets used per phase
└── exports/          # ww2-rifle.glb, ww2-rifle.fbx
```

Create a new one with:

```bash
python scripts/new_model.py ww2-rifle --title "Realistic WW2 Rifle"
```

Each model's `scripts/` holds the exact `bpy` code that was executed to build and revise it,
including the author's absolute folder paths. It is kept as a provenance record of what
actually ran, not as portable tooling — re-running it assumes those paths.

Rules:

- Never overwrite an existing folder. Continue it, or use `-v2` for a deliberate new take.
- Keep the `.blend` saved at every phase gate; snapshot versions instead of overwriting one file.
- Identity features and counted details are built before UVs, and close-up renders prove them.
- Game targets get baked maps in `textures/` and a GLB re-import check before delivery.
- Only `exports/` and `renders/` are deliverables; everything else is working material.
- A model is not done until `NOTES.md` carries the gate table, visual-match result and QA verdict.
