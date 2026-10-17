---
name: pt-floor-design
description: Entry point for discipline 1, bonded post-tensioned floors (PT slabs and band beams) to EN 1992-1-1. Use for any PT floor request - scheme design, tendon layout, PT screening checks, PT drawings, PT calculation notes, or checking a PT design or drawing set. Routes to the PT tools and the shared production skills.
---

# PT floor design (discipline 1)

Read first: `disciplines/pt-floor/README.md` (what exists and what is missing) and the repo `CLAUDE.md` / `AGENTS.md` rules.

## Scope
- **Bonded** PT only. If a document says unbonded or mono-strand, stop and tell the user.
- Eurocodes, CEN recommended values unless the design basis records a National Annex.
- Tendon forces, strand counts, profiles and losses come from a PT analysis or the engineer. Never fill them in.

## Route the request
| Request | Do this |
|---|---|
| Preliminary scheme from a plan | Follow `disciplines/pt-floor/knowledge/PT-Design-Assistant-SKILL.md` |
| Tendon arrangement / profile rules | `disciplines/pt-floor/knowledge/PT-Detailing-Arrangement-Profile-SKILL.md` |
| PT drawings (PT-001 notes, PT-101 plan, PT-102 profiles, schedule) | Skill `structural-pt-drawing` |
| Full 10-sheet PT slab package from a draft layout (body layout, beam / drop-panel / slab reinforcement, tendon plan and profiles) | Skill `pt-slab-structural-design`. Its "defaults" section lists numbers (materials, partial factors, friction, wobble): treat every one as ASSUMED / TBC unless the design basis records it (gap G30). Bonded only |
| Screening checks (stresses at transfer/service, balanced load) | `calc_lib/pt/ec2_pt_screen.py`; pattern in `disciplines/pt-floor/examples/2F-PT/runs/`. Label every result INDICATIVE |
| Calculation note / workbook | Skill `structural-calculation-report` |
| Specification | Skill `structural-specification` |
| Package check before issue | Skill `structural-document-qa` |
| More than one deliverable | Skill `structural-documentation` (coordinator) |

## Before any work
1. Locate `design-basis/<PROJECT-CODE>.yaml` and the PT basis `design-basis/<PROJECT-CODE>.pt.yaml`. Validate both (`tools/design_basis/validate_design_basis.py`, `tools/cadgen/validate_pt_basis.py`).
2. List missing inputs in plain language and stop on anything that drives a result.

## Rules
- A check whose inputs are ASSUMED reports INDICATIVE; a check whose registry value is UNVERIFIED reports NOT EVALUATED.
- Never mark anything APPROVED. Log new gaps in `Structural-Drawing-Standards/00_Standards_Gap_Register.md`.
- Run `python -m unittest discover -s tests` after changing any code.
