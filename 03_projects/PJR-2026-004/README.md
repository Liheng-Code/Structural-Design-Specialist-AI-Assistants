# PJR-2026-004 - 3F PT floor (mock-up project)

Mock-up project for the structural-layout DXF to SAFE 22 workflow (Development Plan v2, M1-M4; ADR-012). It is the benchmark for M1 and the example later projects copy. Nothing here is engineer-approved.

**Input is a structural layout, not an architect plan** (user decision 25-OCT-2026): the engineer places the vertical elements (columns, walls) and gives sizes. The system reads them, checks them, and proposes only what the drawing does not give.

## Folders

| Folder | What goes in it | Who writes it | Milestone / gate |
|---|---|---|---|
| `design-basis.yaml` | Project data, codes, materials, loads, combinations (single source) | Engineer | all |
| `pt-basis.yaml` | PT system, strand, losses data, cover | Engineer | M3 |
| `document-register.csv` | Drawing and document register | Engineer / system | M6 |
| `inputs/str-layout/` | Structural layout DXF (`3F Floor.dxf`) and `layer-map.yaml` | Engineer | M1 |
| `inputs/supplier/` | PT system data sheet / ETA (mu, k, draw-in, relaxation, anchorages) | Engineer | M3 |
| `inputs/references/` | Architect, MEP or other drawings, for information only (not read by the tools) | Engineer | - |
| `model/01-geometry/` | Geometry read from the DXF, labelled preview, review record | System | M1, Gate A |
| `model/02-sizing-loading/` | Size check, loads, load cases, patterns, combinations | System | M2, Gate B |
| `model/03-strips-tendons/` | Support lines, design strips, tendon layout, profiles and forces | System | M3, Gate C |
| `model/04-safe/` | Generated SAFE 22 model, API log, analysis results | System | M4, Gate D |
| `checks/` | Design check results (SLS, ULS, punching, deflection) | System | M5 |
| `output/` | Drawings, calculation report, specification, workbooks (all DRAFT) | System | M6 |

Rule for the `model/` folders: the system writes there and never edits `inputs/`. Each gate leaves a review record in its folder; the next step starts only after the engineer accepts it.

## Status (25-OCT-2026)

- Building: 22 floors and a top roof; this layout is the 3F floor (user, 25-OCT-2026).
- `inputs/str-layout/3F Floor.dxf` received and read (units mm): 22 columns, 11 walls (incl. one core wall drawn as two nested rectangles, ~350 mm), 2 pour strips 2.0 m wide, 18 cast-later squares on the slab edge, grid 1-4 / A-G. The legend holds sample shapes on the structural layers, so raw layer counts overstate beams, band beams, drop panels, openings and slab edges; exact counts come from the M1 reader. Layer map drafted. The DXF is ignored by git (public repo).
- `design-basis.yaml`: project code only; validator reports 8 missing required fields (NOT READY), expected at this stage.
- `pt-basis.yaml`: project code and floor only.
- Open items OI-01 to OI-07 are listed in `design-basis.yaml` (OI-04 closed).
