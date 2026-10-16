# Structural Documentation Skill System

Phases 1-3 done, Phase 4 partly done (see table). Phases 5-8 are not built.

## Layout
```
.claude/skills/            6 skills (SKILL.md + references/)
  ├── structural-calculation-report/
  ├── structural-document-qa/
  ├── structural-documentation/
  ├── structural-drawing/
  ├── structural-specification/
  └── pt-slab-structural-design/     ← NEW (Eurocode 2 PT slab package)
Structural-Drawing-Standards/   company standards (existing 05; 01-04 approved 14-OCT-2026; gap register)
design-basis/              PROJECT_TEMPLATE.yaml, examples/PRJ-2026-003/
tools/design_basis/        validate_design_basis.py
tools/doc_control/         check_register.py
tools/docgen/              build_document.py (spec / calc report -> DOCX + PDF)
tools/cadgen/              build_sheets.py, validate_dxf.py, probe_cad.py, restandardise.py (DXF sheets, preview PDF, validation, move an existing DXF set onto the standards)
tools/xlsxgen/             build_anchorage_workbook.py, verify_workbook.py (XLSX + recalculation + checks)
tools/qa/                  package_qa.py (whole-package QA -> issue-register.csv + qa_report.md)
tools/etabs/               etabs_import.py (table export XLSX/CSV), etabs_db_import.py (SQLite .db model export) (ETABS/SAFE table export -> normalised CSV + checks + provenance)
calc_lib/                  reusable calculation logic + run scripts (separate from formatting)
skills-to-install/         copy into .claude/skills/ (see INSTALL.txt)
docs/                      PRODUCT_ROADMAP_PT_PLATFORM.md  ← long-term vision link
tests/                     unittest suite
```
## Setup
On the user's PC: double-click `setup_on_this_pc.bat` (installs the skills into `.claude\skills` and writes `probe_result.json`).

Python 3.9+, `pip install pyyaml python-docx openpyxl ezdxf matplotlib pillow numpy`; LibreOffice (`soffice`) for PDF/XLSX recalculation. Run `python tools/cadgen/probe_cad.py` on the PC that has AutoCAD/ETABS to record what is installed. Run tests: `python -m unittest discover -s tests -v` (147 tests; 13 need LibreOffice, 24 need the 05_Drafting-Styles folder).

## Use
1. New project: copy `design-basis/PROJECT_TEMPLATE.yaml`; fill known values only; validate it.
2. Ask Claude Code to use `structural-documentation` for a package, or a production skill directly. Finish with `structural-document-qa`.
3. For a full PT slab drawing package: use the skill `pt-slab-structural-design` with the prompt in `.claude/skills/pt-slab-structural-design/references/user-prompt.md`.
4. Register check: `python tools/doc_control/check_register.py <register.csv> --design-basis <db.yaml>`.

## Status of phases
| Phase | State |
|---|---|
| 1 Audit | done (see gap register) |
| 2 Skills + reference maps | done (instruction level; no generators) |
| 3 Design basis + document control | done, 10 tests passing |
| 4 Spec/report generation | DOCX+PDF generator built and tested on PRJ-2026-003 examples; one calculation implemented (EN 1992-1-1 anchorage); spec text is SEED from drawings, unverified |
| 5 Excel workflows | built and tested for the anchorage check (live formulas, Inputs/Calc/Outputs/Checks/Log, verifier, 13 tests); other calculations still need workbooks |
| 6 DXF/DWG/PDF | DXF + preview PDF built for cover (001) and drawing list (002), with validator and 24 tests. NO DWG (no AutoCAD/ODA here). PDF is a script-rendered preview, not an AutoCAD plot with the company CTB. Sheets 003-204 not generated |
| 7 ETABS/SAFE import | importer built (XLSX/CSV table exports, unit normalisation, completeness/mapping/superposition/equilibrium checks, SHA-256 provenance) and tested with 20 tests on a SYNTHETIC fixture. The export layout is ASSUMED and NOT verified against a real ETABS/SAFE export; no ETABS here. Not run on any real model |
| 8 Cross-document QA automation | `tools/qa/package_qa.py` built: 13 check groups across design basis, register, DOCX/XLSX/DXF/PDF, results tie-out, ETABS import; 35 acceptance tests incl. deliberately incomplete, inconsistent and unsupported-claim packages. Consistency gate only; engineering correctness not judged; DWG, AutoCAD plots, and any sheet without a file are NOT checked |

## Long-term Product Vision
See `docs/PRODUCT_ROADMAP_PT_PLATFORM.md` for the relationship between the current skill system and the future full bonded-PT design platform.

## Known limitations
- PRJ-2026-003 design basis is transcribed from drawings; unverified, editions/generations blank, 8 open items.
- Sheets 101-204 of the example set were not supplied.
- Standards 01-04 and layers 05-04a/05-04b were approved by the user in chat on 14-OCT-2026; 06, 07, 10 absent; report/spec formats still PROPOSED. No engineering approval has been given to anything here.
