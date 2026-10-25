# Discipline 1 - Post-tensioned floors

Scope: post-tensioned concrete slabs and band beams to EN 1992-1-1. **Bonded is the company default; unbonded is also allowed** (user decision 24-OCT-2026). The PT basis `system.type` decides; if empty, bonded is assumed and flagged. Unbonded gaps: ULS tendon stress for unbonded tendons is not implemented and the unbonded note wording is not reviewed (gap G32).

## What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/pt-floor-design/` | Routes PT work to the tools below |
| PT drawings (notes PT-001, tendon plan PT-101, profiles PT-102, schedule) | `.claude/skills/pt-drawings/`, `04_tools/cadgen/pt_notes.py`, `pt_plan.py`, `pt_profiles.py` | Built; DXF + preview PDF; draws data, computes nothing |
| Full PT slab package skill (10 sheets from a draft layout) | `.claude/skills/pt-slab-package/` | Instruction level; its numeric defaults are not design-basis values (gap G30) |
| PT basis template and validator | `03_projects/_template/pt-basis.yaml`, `04_tools/cadgen/validate_pt_basis.py` | Built |
| PT screening checks (stress, balanced load, strip solver) | `04_tools/calc_lib/pt/ec2_pt_screen.py`, tests in `tests/test_ec2_pt_screen.py` | Indicative screening only, not a design |
| PT designer roadmap | `05_docs/development-plan-v2.md`, `05_docs/architecture-v2.md`, `05_docs/adr/` | M0 gate closed by the user 25-OCT-2026; M1 next |
| Design knowledge | `knowledge/` | See [knowledge/README.md](knowledge/README.md) |
| Worked example: 2F PT slab | `03_projects/PJR-2F-PT/` (PT basis, plan/profile data, `redraft/`, `runs/`, `verification/`) | Redraft + screening; gaps G24-G26 open |

## What is missing
- Loss calculation, ULS flexure, punching shear and deflection modules (Development Plan v2, M2 onward).
- Anchorage, band-beam section and summary sheets.
- Real SAFE/ETABS export to validate the importer (ADR-002).

## Running the 2F example scripts
```
python 03_projects/PJR-2F-PT/runs/pt_2f_screening.py <redraft_data_dir> <out.json>
python 03_projects/PJR-2F-PT/runs/pt_2f_stress_map.py <redraft_data_dir> <out_dir>
```
They need `shapely` and `numpy` (and `pymupdf` for `check_vs_calc_note.py`). Results are INDICATIVE (gap G25).
