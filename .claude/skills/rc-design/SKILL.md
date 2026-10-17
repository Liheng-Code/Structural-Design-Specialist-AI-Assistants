---
name: rc-design
description: Entry point for discipline 3, reinforced concrete works (slabs, beams, columns, walls, foundations, ground slabs) to EN 1992-1-1, EN 206 and EN 13670. Use for any RC request - design workflow, anchorage and lap lengths, member checks, reinforcement drawings, bar schedules, concrete specification or calculation report. Not for post-tensioned floors (use pt-floor-design).
---

# Reinforced concrete design (discipline 3)

Read first: `disciplines/rc-works/README.md` and `disciplines/rc-works/knowledge/rc-design-workflow.md`, plus the repo `CLAUDE.md` / `AGENTS.md` rules.

## State
EARLY. Only the anchorage/lap check is built (`calc_lib/rc/ec2_anchorage.py`). Member checks, bar-schedule format and registry values are missing (gap G28).

## Route the request
| Request | Do this |
|---|---|
| Design approach / what to check | Follow `disciplines/rc-works/knowledge/rc-design-workflow.md` |
| Anchorage and lap lengths | `calc_lib/rc/ec2_anchorage.py`; run script `calc_lib/runs/anchorage_check.py`; workbook `tools/xlsxgen/build_anchorage_workbook.py` |
| General notes (concrete, reinforcement) | Skill `structural-drawing`; notes library `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml` |
| Member checks (flexure, shear, punching, columns) | No module yet. Engineer-supplied calculation, or build one in `calc_lib/rc/` with hand-value tests |
| Analysis results | `tools/etabs/` via skill `structural-calculation-report` |
| Concrete / reinforcement specification | Skill `structural-specification` |
| Package check | Skill `structural-document-qa` |

## Rules
- Concrete class, exposure class, cover, steel grade and loads come from the design basis only.
- Registry values that are null/UNVERIFIED make the dependent check NOT EVALUATED.
- Never mark anything APPROVED. Missing inputs are listed, not assumed.
