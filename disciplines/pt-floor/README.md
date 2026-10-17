# Discipline 1 - Post-tensioned floors

Scope: **bonded** post-tensioned concrete slabs and band beams to EN 1992-1-1. Unbonded / mono-strand systems are out of scope; stop and tell the user if a document says otherwise.

## What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/pt-floor-design/` | Routes PT work to the tools below |
| PT drawings (notes PT-001, tendon plan PT-101, profiles PT-102, schedule) | `.claude/skills/structural-pt-drawing/`, `tools/cadgen/pt_notes.py`, `pt_plan.py`, `pt_profiles.py` | Built; DXF + preview PDF; draws data, computes nothing |
| PT basis template and validator | `design-basis/PT_BASIS_TEMPLATE.yaml`, `tools/cadgen/validate_pt_basis.py` | Built |
| PT screening checks (stress, balanced load, strip solver) | `calc_lib/pt/ec2_pt_screen.py`, tests in `tests/test_ec2_pt_screen.py` | Indicative screening only, not a design |
| PT designer roadmap | `docs/Development Plan v2.md`, `docs/Architecture v2.md`, `docs/adr/` | M0 built, awaiting engineer review gate |
| Design knowledge | `knowledge/` | See [knowledge/README.md](knowledge/README.md) |
| Worked example: 2F PT slab | `examples/2F-PT/` (`redraft/`, `runs/`, `verification/`) and `design-basis/examples/PJR-2F-PT/` | Redraft + screening; gaps G24-G26 open |

## What is missing
- Loss calculation, ULS flexure, punching shear and deflection modules (Development Plan v2, M2 onward).
- Anchorage, band-beam section and summary sheets.
- Real SAFE/ETABS export to validate the importer (ADR-002).

## Running the 2F example scripts
```
python disciplines/pt-floor/examples/2F-PT/runs/pt_2f_screening.py <redraft_data_dir> <out.json>
python disciplines/pt-floor/examples/2F-PT/runs/pt_2f_stress_map.py <redraft_data_dir> <out_dir>
```
They need `shapely` and `numpy` (and `pymupdf` for `check_vs_calc_note.py`). Results are INDICATIVE (gap G25).
