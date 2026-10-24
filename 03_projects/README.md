# Projects

One folder per project, named by its project code (as recorded in its design basis). Everything about the project stays inside its folder.

| File / folder | Content |
|---|---|
| `design-basis.yaml` | Single source for project code, revision, date, stage, codes, loads, materials. Validate: `python 04_tools/design_basis/validate_design_basis.py 03_projects/<CODE>/design-basis.yaml` |
| `pt-basis.yaml` | PT projects only: PT basis (`system.type` bonded = default, or unbonded). Validate: `python 04_tools/cadgen/validate_pt_basis.py <file> --design-basis <design-basis.yaml>` |
| `document-register.csv` | Drawing and document register |
| inputs (`*-inputs.yaml`, `*-data.json`), `content/` | Project inputs for the tools |
| `output/` | Generated deliverables (DXF, PDF, DOCX, XLSX) |
| `runs/`, `redraft/`, `verification/` | Project-specific scripts and their results |

| Project | Discipline | Notes |
|---|---|---|
| [_template/](_template/) | - | Blank `design-basis.yaml` and `pt-basis.yaml` to copy |
| [PJR-2F-PT/](PJR-2F-PT/) | 1 PT floor | 2F PT slab: redraft, screening runs, verification reports (gaps G24-G26) |
| [PJR-2026-003/](PJR-2026-003/) | Steel + RC | Warehouse drawing set WH-STR-SD R00: design basis transcribed from drawings, restandardised DXF, calc report, spec, workbook. Issued R00 drawings still show `PRJ-2026-003` (gap G07) |
