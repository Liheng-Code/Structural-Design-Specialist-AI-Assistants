# Discipline 3 - Reinforced concrete works

Scope: conventionally reinforced concrete members (slabs, beams, columns, walls, foundations, ground slabs) designed to EN 1992-1-1, with concrete to EN 206 and execution to EN 13670. Post-tensioned floors are discipline 1.

Status: **EARLY (17-OCT-2026).** One tested check exists; member design is not built (gap G28).

## What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/rc-design/` | Workflow guidance |
| Anchorage and lap length check (EN 1992-1-1) | `04_tools/calc_lib/rc/ec2_anchorage.py`, `04_tools/calc_lib/runs/anchorage_check.py`, tests in `tests/test_calc_report_docgen.py`, `tests/test_xlsx_workbook.py` | Built and tested; used live on general-notes sheet 004 |
| Anchorage workbook | `04_tools/xlsxgen/build_anchorage_workbook.py` | Built |
| Concrete and reinforcement general notes | `01_standards/04-general-notes/` | APPROVED (user, 14-OCT-2026) |
| Design knowledge | [knowledge/rc-design-workflow.md](knowledge/rc-design-workflow.md) | DRAFT |
| Worked example (drawing set) | `03_projects/PJR-2026-003/` | Transcribed from drawings; unverified |

## Build order (proposed)
1. Engineer enters and verifies the EN 1992-1-1 registry values (`04_tools/code_registry/EN1992-1-1_2004_CEN.yaml`, currently all null).
2. Member checks in `04_tools/calc_lib/rc/`, one at a time with hand-value benchmarks: beam/slab flexure, shear, crack control, deflection by span/depth, column axial + bending, punching.
3. Bar-schedule format approved, then a schedule generator.
4. Reinforcement detail sheets.
