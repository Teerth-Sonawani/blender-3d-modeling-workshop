# Mauser C96 "Original" — M1896 Cone Hammer

**Request:** "Make a realistic 3d model of a mauser c96 original"

## Production Brief

```
Type:        hard-surface hero weapon (semi-automatic pistol)
Target:      game / cinematic / portfolio hybrid — hero prop, unreal/unity ready
Style:       realistic (AAA PBR, worn blued steel + oiled walnut)
Dimensions:  overall 288 mm, height 152 mm, barrel 140 mm, bore axis 152 mm above
             the butt, grip width 36 mm (matches 7.63x25mm C96 "pre-Bolo" figures)
Poly budget: 15k-50k tris hero prop (polycount-budgets.md), realistic = upper range
Texture:     procedural PBR in-scene; no image textures on disk (documented as such)
Pivot:       grip / hand-contact centre of the frame
Export:      GLB + FBX (selection = COL_Export contents, transforms applied, metres)
Animation:   none (mechanically separable parts kept as separate objects)
```

### Skills in use (ordered)
1. `blender-director` — brief, routing, validation gates
2. `hard-surface` — primary/secondary form logic, bevel + weighted-normal workflow
3. `historical-worlds` — 1896 Mauser Oberndorf manufacturing logic, period finish
4. `realistic-style` — real-world scale, plausible PBR, micro-detail via shader
5. `materials` — blued steel, polished wear, walnut with grain
6. `uv-workflow` — production UVs, seams on construction edges
7. `asset-optimization` — tri budget, no interior/dead geometry in export parts
8. `export-pipeline` — GLB/FBX axis + scale + pivot

## Reference analysis (measured, not guessed)

Reference photos downloaded from Wikimedia Commons into `refs/`:

| file | subject | use |
|---|---|---|
| `ref_04.jpg` | early commercial C96, right side, clean background | **primary: measured** |
| `ref_03.jpg` | C96, left side | left-side panel layout, hammer/safety |
| `ref_01.jpg` | C96 in museum case (reblued) | finish/value reference |
| `ref_02.jpg` | C96 with shoulder stock | stock lug geometry |

Silhouette extracted numerically from `ref_04.jpg` (`scripts/measure_ref.py`,
background-relative threshold + morphological cleanup). The measured bounding box is
1566 px wide; scaling so overall length = 288 mm gives **0.1844 mm/px**, and the
resulting height is **152.1 mm** — independently matching the documented 152 mm, so the
pixel scale is trustworthy. All model coordinates below are read off that measurement
(`scripts/crop_ref.py` writes mm-gridded crops used to read the small parts).

Orientation: **+X = muzzle, +Z = up, bore axis = Z 0**, X 0 = rear face of the receiver.

### Measured landmarks (mm)
- overall length 288, height 152, barrel 140 (x 148 → 288)
- barrel is coaxial, diameter ≈ 20 at the breech collar tapering to ≈ 13.1 at the muzzle
- receiver/barrel-extension top line at z +9.6 (x 25 → 118), dipping concave to z +3.2
  at the barrel collar (x 143) — the characteristic C96 "scoop"
- magazine housing bottom at z −72.2 (x 66 → 148); trigger guard bottom ≈ z −55
- grip: top at z −53, butt at z −135, raked back, flared butt, 36 mm wide
- rear sight leaf lies flat on the receiver top (x 58 → 105) with a knurled slider
- hammer (knurled cone) breaks the top line by ≈ 7 mm at x ≈ 45–58
- two bored bosses on the rear frame tail (x 0–20) = shoulder-stock lugs
- lanyard ring at the butt (x ≈ 0–6)

### Identifying features that must read
1. Broomhandle grip with ~24 horizontal walnut grooves, brass escutcheon screw
2. Long flat-sided barrel extension with a milled panel and the Oberndorf rollmark area
3. S-curve shoulder where the extension dives into the barrel
4. Stepped barrel with a muzzle collar, tall blade front sight on a raised base
5. Cone hammer with knurled side rings, bowtie safety paddle in a pocket
6. Knurled bolt rear protruding behind the receiver; extractor rib along the top
7. Tangent rear sight folded flat, graduations + slider
8. Trigger guard with crescent trigger, integral 10-round magazine box
9. Steel frontstrap/backstrap with walnut panels inset
10. Shoulder-stock lugs and lanyard ring

### Approximations to state honestly
- Rollmark text ("WAFFENFABRIK MAUSER / OBERNDORF A. NECKAR") is modelled as a recessed
  panel only; no lettering geometry or texture exists.
- Sight graduations are represented by a ribbed slider area, not 1–10 numerals.
- Internal mechanism (lock frame, firing pin, spring) is not modelled — only what is
  visible with the pistol assembled.
- The 312 mm "pre-Bolo" figure quoted by some sources is not used; 288 mm matches the
  measured photograph, which is the M1896 Original configuration.

## Pipeline phases
- [x] Reference & planning
- [x] Blockout & silhouette
- [x] Modelling
- [x] Cleanup & topology
- [x] UVs
- [x] Materials
- [x] Optimization
- [x] Lights, cameras, renders
- [x] Export & validation

## Validation report (final, read from the scene)

`scripts/validate.py` on `mauser-c96-original.blend`, after `scripts/cleanup.py`
(merge-by-distance, degenerate-face removal) and `scripts/export_assets.py`.

| check | result |
|---|---|
| triangles | **33,277** (re-measured after the 2026-11-24 barrel rebuild; was 33,954) |
| vertices | 17,063 |
| objects | 17 `SM_` meshes |
| materials | 4 — `MAT_Metal_Blued_Steel`, `MAT_Metal_Polished_Highlights`, `MAT_Wood_Walnut_Grip`, `MAT_Metal_Bore_Shadow` |
| dimensions | **286.5 × 36.8 × 153.8 mm** (target 288 × 36 × 152) |
| pivot | grip web `(0.040, 0, -0.075)` m, translated into the mesh data for export and restored afterwards |
| collision | 4 `UCX_` proxies — `UCX_Grip`, `UCX_Frame`, `UCX_Receiver`, `UCX_Barrel` — in the FBX, none in the GLB |
| UVs | 17/17 meshes, smart-projected, packed into 0–1 |
| transforms | applied — every object at location 0, scale 1 |
| degenerate faces | 0 (6 removed from the receiver in cleanup) |
| open edges | 60 — 56 are the hollow bore (muzzle + chamber, intentional), 4 are receiver cut-outs |
| loose vertices | 0 |
| verdict | **PASS** |

Budget note: the grip carries 24,624 tris of the total — 74% of the asset (24 real flutes plus
the stippled panels, modelled as geometry because the project has no image textures). The
remaining 16 objects share 8,653 tris. The barrel was rebuilt in the 2026-11-24 quality pass
(tapered, with a stepped muzzle collar and a real bore); the receiver is still a slab, which is
the next geometry fix if this asset is revisited. Baking the grip flutes to a normal map would
free ~20k tris.
That keeps the asset inside the 15k–50k hero-prop range, but there is **no LOD chain** —
it is a single hero asset. A decimated distance LOD is the first optimisation if it
ships in a scene where it is seen far away.

## Files on disk

```
Models/mauser-c96-original/
├── mauser-c96-original.blend        working scene, authoring space (+X muzzle, bore Z 0)
├── refs/                            Commons photos + mm-gridded measurement crops
├── renders/hero.png                 1920×1080, 3/4 view, key/fill/rim
├── renders/side.png                 1920×1080, orthographic right side
├── renders/front.png                1920×1080, orthographic muzzle-on
├── renders/top.png                  1920×1080, orthographic top
├── renders/prev_*.jpg               1200 px previews of the four views
├── exports/mauser-c96-original.glb  1,057,404 bytes
├── exports/mauser-c96-original.fbx  932,348 bytes
└── scripts/                         build, uv, materials, render, cleanup, export, validate
```

## Execution note

Geometry, UVs and the first look-dev/render pass were driven through the workshop's
MCP chain (`scripts/mcp_call.py` → `blender-mcp` → bridge on 9876). The bridge's
`execute_blender_code` path stopped responding partway through the final pass (the socket
accepted connections but never serviced a call), so the final materials, renders, cleanup,
export and validation were run with Blender's own background interpreter on the same
`.blend` with the same scripts. Nothing was simulated: every number above and every file
listed was produced by Blender from this scene.

## Verification (machine-checked)

<!-- verify:begin -->
triangles: 33277
meshes: 17
materials: 4
textures: 0
dimensions_m: 0.2865 x 0.1538 x 0.0368
collision: 4 UCX proxies (FBX)
animations: 0
<!-- verify:end -->

`python scripts/verify_model.py mauser-c96-original` re-measures the export and fails if any
number above stops matching the delivered file.

## Audit note (2026-11-24)

The export re-measures exactly as recorded: 33,954 tris, 17 `SM_` meshes, 4 materials, 0
textures, 0.2865 × 0.1538 × 0.0368 m. Structural gaps found against the standard model tree:

- No `versions/` — no `_v01_blockout` … `_v04_export` gate snapshots exist, so the phase
  claims in this record cannot be checked against a saved state.
- No `textures/` — correct for a procedural-only delivery, but the folder is part of the tree
  and should exist with a note rather than be absent.
- ~~No collision proxy, although the brief says "unreal/unity ready".~~ Fixed 2026-11-24: four
  `UCX_` boxes are in the FBX and `COL_Collision` / `COL_Export` are populated.
- No LOD chain, although the brief says "unreal/unity ready".

## Quality pass (2026-11-24)

| Item | Delivered | Rebuilt |
|---|---|---|
| Barrel | uniform 20.2 mm tube, x 146.5–288, 1640 tris | lathed taper 20.2 → 13.1 mm with a stepped muzzle collar and a 3.1 mm-radius bore, 956 tris |
| Collision | none — `COL_Collision` and `COL_Export` empty, no `UCX_` in either export | 4 boxes (`UCX_Grip`, `UCX_Frame`, `UCX_Receiver`, `UCX_Barrel`) in the FBX |
| Hero camera | 90 mm — cropped the muzzle and the receiver top | 62 mm, whole pistol in frame |
| Camera units | authored in metres, geometry also in metres — verified correct | restored to the delivered transforms after a wrong metre/millimetre reading mid-pass |
| Names | — | the barrel and the four proxies had `.001`/`.002` object *and* mesh datablock names; both namespaces re-aligned |

The export now runs from an explicit selection (visual `SM_` meshes without the studio floor,
plus the `UCX_` set) and translates the mesh data by the grip pivot `(0.040, 0, -0.075)` m for
the export, restoring the authoring space afterwards — the same intent as `export_assets.py`,
with collision included.

Still open: no LOD chain, the receiver is still a slab without the C96 top scoop, the grip's 24
flutes cost 24,624 tris (74% of the asset) and read as a coarse washboard rather than fine
checkering, and no engine import (Unity/Unreal/Godot) has been run.

## Export limitation

The GLB/FBX carry geometry, UVs and flat PBR values (base colour, metallic, roughness).
The procedural walnut grain, blued-steel noise variation and bump detail live only in the
Blender node graphs; with no image textures in the project they cannot survive glTF/FBX.

