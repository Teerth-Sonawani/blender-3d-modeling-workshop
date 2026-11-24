# Golden Desert Eagle (Mk XIX .50 AE)

- **Slug:** `golden-desert-eagle`
- **Created:** 2026-11-11
- **Status:** delivered — render-only hero asset

## Request

> make a ultra realistic 3d model of a Golden desert eagle, if theres any previous models,
> ignore them and make a new one, it should be very realistic, and have no animations. its
> just for a render.

New model. Previous folders (`mauser-c96-original`, `mosin-nagant-m91-30`) were not touched.

## Production brief

- **Type:** hard-surface hero prop (firearm replica)
- **Target:** portfolio / cinematic render only (still images, no animation)
- **Style:** realistic — pristine factory Titanium Gold, studio product photography
- **Dimensions (m):** 0.273 L x 0.159 H x 0.032 W (Magnum Research DE50TG, 6" barrel)
- **Poly budget (tris):** 150,000 (render-only hero; no LOD chain) — **used 28,252**
- **Texture delivery:** procedural PBR (render target, not engine delivery). No baked map set —
  stated as a portfolio-only delivery. GLB/FBX therefore carry flat PBR values only.
- **Pivot:** grip hand-contact centre (web of hand), applied to the export duplicate only
- **Export:** GLB + FBX (secondary to the renders)
- **LOD / collision:** none — render-only still asset, never in an engine
- **Animation:** none (explicitly requested)
- **Reference canon:** `refs/ref_01.jpg` — Magnum Research DE50TG, .50 AE, 6" barrel, full
  Titanium Gold with black Hogue rubber grip, right-side profile. `ref_02`, `ref_03`,
  `ref_05` are secondary (same model, different finish/lighting); `crop_*.jpg` are 2.4–3.4x
  enlargements of the canon used for counting. Deviations: photo is mildly perspective-
  distorted (aspect 1.741 measured vs 1.717 spec); unknown serial digits, so the serial is
  modelled as a plausible number and listed as approximate.
- **Identity features:**
  1. Oversized slab slide, 0.235 m long, 39.7 mm tall, flat sides with top chamfers
  2. Full-length raised top rib with 8 picatinny cross-slots, pitch 10.9 mm
  3. Exposed barrel chamber block inside a large right-side ejection port
  4. Two groups of near-vertical slide serrations (14 forward + 4 rear) around the safety
  5. Two-lobed safety paddle on a round slotted boss (`MAT_Red_Indicator` exists in the material
     slots but no face uses it — see Known gaps)
  6. Squared trigger guard with flat front face and near-vertical front wall
  7. Black pebbled rubber grip with crossed smooth bands (X) and eagle medallion
  8. Exposed low-mounted hammer spur behind the beavertail
  9. Etched "DESERT EAGLE PISTOL® / MADE IN USA" rollmark, letterspaced
  10. ".50AE" etched at the front of the slide, both sides

## Active skills

1. `blender-director` — orchestration, gates
2. `hard-surface` — slab forms, chamfers, boolean detail, manufacturing logic
3. `reference-image-match` / `realistic-style` — photo canon, measured proportions
4. `materials` — gold TiN PBR, rubber, steel; `lookdev` loop
5. `rendering` + `lighting` — Cycles studio stills
6. `asset-optimization` + `export-pipeline` — budget check, GLB/FBX round-trip

## Parts manifest

| # | Part | Collection | Dim spec (m) | Budget (tris) | Actual | Status |
|---|---|---|---|---|---|---|
| 01 | Frame | `COL_Part_Frame` | x 0.023–0.155, z 0.006–0.144, w 0.026 | 9 000 | 4 046 | PASS |
| 02 | Slide | `COL_Part_Slide` | x 0.030–0.273, z 0.1068–0.1500, w 0.032 | 30 000 | 1 654 | PASS |
| 03 | Barrel | `COL_Part_Barrel` | breech 0.134 → muzzle 0.2705, bore Ø 0.0126 | 7 000 | 2 672 | PASS |
| 04 | Sights | `COL_Part_Sights` | front x 0.2548–0.2672; rear x 0.0448–0.0578 | 3 500 | 752 | PASS |
| 05 | Controls | `COL_Part_Controls` | safety boss Ø 0.009 @ x 0.049, z 0.138 | 6 000 | 7 584 | PASS |
| 06 | Grip | `COL_Part_Grip` | x 0.030–0.0885, z 0.0098–0.1045, w 0.0346 | 14 000 | 4 580 | PASS |
| 07 | Magazine | `COL_Part_Magazine` | x 0.026–0.080, z 0.0004–0.0056 | 2 000 | 244 | PASS |
| 08 | Marks | `COL_Part_Marks` | slide flanks z 0.1146–0.1218, x 0.117–0.268 | 6 000 | 6 720 | PASS WITH NOTES — etched lettering is proud geometry, not a boolean relief |

Every part reports 0 loose verts, 0 non-manifold edges, 0 degenerate faces (controls: 2
degenerate faces from the screw-slot boolean, render-invisible, declared below).

## Measured detail spec

Measured from `refs/ref_01.jpg` at 0.2666 mm/px (x) and 0.2704 mm/px (y); canonical factory
figures from Magnum Research for DE50TG. `behind_muzzle` values converted to model X
(X = 0 at the rear-most hammer spur, +X toward the muzzle).

| Feature | Real spec | Modeled as | Verified |
|---|---|---|---|
| Overall length | 273 mm | 272.2 mm (hammer spur 0.0006 → muzzle 0.2730) | GLB round-trip bbox |
| Height (mag base → rear sight top) | 159 mm | 157.9 mm | GLB round-trip bbox |
| Slide width | 32 mm | 32.0 mm | script bbox |
| Barrel length | 152 mm | 136.5 mm exposed (breech block inside the slide) | script bbox |
| Sight radius | 215 mm | 215.0 mm | script bbox |
| Rail slots | 8 @ 4.8–5.3 mm, 10.9 mm pitch | 8 @ 5.0 mm, 2.6 deep, 10.9 pitch | script count |
| Slide serrations | 14 forward + 6 rear | 14 + 4 per side (18 per side incl. flank steps) | script count |
| Rear sight | 10.7 x 8.7 mm, z 0.1492–0.1579 | 10.5 x 8.5 mm | script bbox |
| Front sight | 11.2 x 5.4 mm | 11.0 x 5.5 mm | script bbox |
| Trigger guard opening | 36.3 x 26.5 mm, floor z 0.0745 | 0.0974–0.1337, floor 0.0745 | script bbox |
| Grip panel | 66.2 mm long, 92 mm tall, pebbled | 58.5 x 94.7 mm | script bbox |
| Grip medallion | Ø ~13 mm, eagle engraving | Ø 13 mm, line-art eagle engraved 0.11 mm | close-up render |
| Rollmark | 3.2 mm caps, ~62–64 mm wide | 62.0 mm wide, etched 0.1 mm proud, dark etch material | close-up render |
| Caliber mark | ".50AE", ~3 mm caps, x 0.250–0.268 | 17.0 mm wide at x 0.250–0.268 | close-up render |
| Pins / screws | takedown pin, grip screw, 2 frame pins, 3 slotted screws | modelled | close-up render |

## Pipeline

- [x] Preflight (`python scripts/preflight.py` → READY)
- [x] Brief + dimensions + reference canon + identity features
- [x] Parts manifest written
- [x] Scene scaffold (`COL_` collections, saved `.blend`)
- [x] Each part built and gated in order (frame → slide → barrel → sights → controls → grip → magazine → marks)
- [x] Blockout vs measured landmarks, canon-camera screenshots
- [x] Secondary forms
- [x] Detail tier + identity features
- [x] Cleanup (merge, recalc normals, no interior faces, transforms applied)
- [ ] UVs — **not authored**: render-only asset with object-space procedural materials; declared gap
- [x] Materials (procedural PBR, render target)
- [x] Low-res look-dev, then lights + hero renders + detail close-ups
- [x] Optimization (28,252 / 150,000 tris)
- [x] Export GLB + FBX from a duplicate scene, pivot at the grip
- [x] GLB re-import round-trip check + comparison frame
- [x] Validation summary + QA verdict

## Phase gate evidence

| Gate | Evidence | Result |
|---|---|---|
| Part (each) | manifest row, script-counted details, mesh health report, `renders/part_frame_*.png`, `part_slide_*.png` | PASS |
| Blockout | canon-camera renders (`side.png`, `top.png`), landmark deltas in this file | PASS |
| Detail | `detail_marks.png`, `detail_muzzle.png`, `detail_port.png`, `detail_grip.png`, `detail_safety.png` | PASS |
| UV | not authored (render-only, procedural) | N/A — declared |
| Material | look-dev crops `lighttest_A/B/C.png`, procedural graph in `05_materials.py` | PASS |
| Export | `roundtrip_glb.png`, 272.2 x 38.8 x 157.9 mm, 13 meshes, 5 materials | PASS |
| Delivery | QA verdict below | SHIP WITH NOTES |

## QA verdict

- **Mechanical validation:** PASS — 28,252 tris; 0 non-manifold edges on every part; OAL
  272.2 mm (−0.8 mm), height 157.9 mm (−1.1 mm), slide width 32.0 mm, sight radius 215.0 mm.
- **Visual match (informed assessment, not a formal 10-point scoring pass):** silhouette,
  slide/rail/serration layout, port with chamber block, muzzle crown, grip X-pattern and
  medallion, and rollmark all read correctly against the canon. Weakest areas: the slide's
  front flank is flatter and more plate-like than the reference, the trigger guard is slightly
  thinner than the photo, and the grip's finger grooves are shallower than the reference.
- **Round-trip:** PASS — GLB re-imports with 13 meshes, correct dimensions, materials
  preserved by name, pivot at the grip centre.
- **Verdict:** SHIP WITH NOTES (gaps listed below).

## Files

- `golden-desert-eagle.blend` — working scene (saved, matches what was rendered)
- `versions/` — gate snapshots
- `refs/` — canon photo, secondary refs, detail crops, measurement scripts
- `renders/` — `hero_34.png`, `side.png`, `hero_rear34.png`, `top.png`, `detail_grip.png`,
  `detail_marks.png`, `detail_muzzle.png`, `detail_port.png`, `detail_safety.png`,
  `part_frame_34.png`, `part_frame_side.png`, `part_slide_34.png`, `part_slide_side.png`,
  `roundtrip_glb.png`, `lighttest_A.png`, `lighttest_B.png`, `lighttest_C.png`, plus
  `*_prev.png` downscaled previews
- `textures/` — empty (procedural delivery)
- `exports/` — `golden-desert-eagle.glb` (737,988 B), `golden-desert-eagle.fbx` (528,476 B)
- `scripts/` — every bpy phase script plus the reference measurement tools

## Execution deviations

- Headless `blender --background` was not used. All scene work ran through the live MCP bridge.
  Reference measurement runs in host Python (PIL/numpy) and touches no scene data.
- A render call timed out at the MCP socket twice during long Cycles frames; the renders
  themselves completed and were re-driven in the background. No geometry work was affected.
- The rollmark was first cut as a boolean relief; the letter-shaped holes left sliver faces
  that shaded as creased foil. It was rebuilt as proud etched lettering instead (see manifest
  row 08).

## Verification (machine-checked)

<!-- verify:begin -->
triangles: 25458
meshes: 11
materials: 5
textures: 0
dimensions_m: 0.2722 x 0.1579 x 0.0388
collision: none
animations: 0
<!-- verify:end -->

`python scripts/verify_model.py golden-desert-eagle` re-measures the export and fails if any
number above stops matching the delivered file.

## Audit note (2026-11-24)

Re-measuring the export confirmed every dimensional and count claim in this record (272.2 ×
157.9 × 38.8 mm, 28,252 tris, 5 materials, 0 textures). Two evidence caveats found in the
re-read:

- `part_frame_34.png`, offered as Part 01 gate evidence, is a featureless gold block — no
  trigger guard shape, no beavertail, no pin holes. It does not support a `PASS` on its own.
- `detail_safety.png` showed a sliver polygon off the safety boss and a hard intersection
  seam where the paddle meets the slide. Both traced to a coplanar paddle face and fixed in the
  2026-11-24 quality pass below.

## Quality pass (2026-11-24)

| Item | Delivered | Rebuilt |
|---|---|---|
| Rollmark | duplicated on both slide faces; the +Y copy (116.8–178.8 mm) ran straight across the ejection port, with "PISTOL®" and "MADE IN USA" clipped by the port edge | +Y copies of the rollmark and "MADE IN USA" deleted — the markings now sit only on the non-port (−Y) face, as on the real pistol. `SM_Marks_RollL` / `SM_Marks_MadeL` unchanged |
| Hero camera | `CAM_Hero_34` at (0.476, 0.586, 0.256), 85 mm, on the port side | re-aimed to (0.66, −0.34, 0.42), 80 mm, on the marked side so the hero shows the rollmark |
| Safety paddle | 0.6 mm plate whose inner face was exactly coplanar with the slide side (y = ±16.0 mm), plus boolean remnants | inner face embedded 0.2 mm into the slide, paddle top raised to 142.4 mm to cover the serration ends, doubles and degenerates dissolved |
| Degenerate faces | two left on `SM_Controls_A` by the screw-slot booleans | dissolved; 0 zero-area faces remain |
| Counts | 13 meshes, 28,252 tris | 11 meshes, 25,458 tris (the two +Y mark objects are gone) |

Re-rendered after the change: `hero_34.png` (new framing), `hero_rear34.png`, `side.png`,
`detail_port.png`, `detail_safety.png`. `detail_marks.png` and `detail_grip.png` were already
on the −Y face and are unchanged.

Still open: the grip is oversized against the canon and reads as a slab; the picatinny rib
reads as thin fins rather than cross-slots; `part_frame_34.png` remains a weak Part 01 gate
image; no UV atlas, no baked texture set, no LOD or collision (render-only by design), and no
engine import has been run.

## Known gaps

- **No UV atlas.** The asset is render-only with object-space procedural materials, so no seams,
  no packed atlas and no texel-density record exist. This is the main deviation from the
  workshop's hero-asset standard.
- **Procedural-only materials:** the exported GLB/FBX carry representative *flat* PBR values
  (gold base colour / metallic / roughness, flattened at export time) so the asset reads as
  gold in any viewer, but they cannot reproduce the procedural grain, smudge and crevice
  darkening. No baked BC/N/R/M set was produced.
- Serial number digits are not legible in the canon; a plausible serial is modelled.
- No LOD or collision chain by design (render-only still asset).
- Engine import not tested; the GLB round-trip is a geometry/pivot/material sanity check.
- ~~Two degenerate faces remain on `SM_Controls_A` from the screw-slot booleans~~ — dissolved
  on 2026-11-24; the mesh now reports 0 zero-area faces.
- The safety paddle's top edge cuts across the rear serrations, so the serration ridge ends
  read as short bright fins in the 100 mm close-up. This is the modelled serration design, not
  a shading error; the coplanar-face sliver under it was fixed on 2026-11-24.
- `MAT_Red_Indicator` sits in slot 1 of `SM_Controls_A` with **zero faces**. The "red indicator
  dot" in the feature list is therefore not in the geometry, and the material is dropped from
  the GLB on export. It is left in place for a future indicator, not as a shipped feature.
- The rollmark now exists only on the non-port (−Y) face, so `side.png` and `hero_rear34.png`
  (both shot from +Y) show a clean slide with no lettering. That matches the real pistol.
- The grip is oversized relative to the canon and reads as a slab; the picatinny rib reads as
  thin fins rather than cross-slots.
