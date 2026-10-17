# Discipline 3 - Reinforced concrete works

Knowledge pack generated 2026-10-17 from commit `6cba6d9`.

> Generated from the project repository. This is reference material for search and recall, not an approved standard or a calculation result. Each section names its source file; check that file's status header (APPROVED / PROPOSED / DRAFT / SKELETON). Nothing here is engineer-approved unless the source file says so. NotebookLM answers are AI summaries of this text (gap G29).

## Contents

- `disciplines/rc-works/README.md`
- `.claude/skills/rc-design/SKILL.md`
- `disciplines/rc-works/knowledge/rc-design-workflow.md`

---

## Source: `disciplines/rc-works/README.md`

### Discipline 3 - Reinforced concrete works

Scope: conventionally reinforced concrete members (slabs, beams, columns, walls, foundations, ground slabs) designed to EN 1992-1-1, with concrete to EN 206 and execution to EN 13670. Post-tensioned floors are discipline 1.

Status: **EARLY (17-OCT-2026).** One tested check exists; member design is not built (gap G28).

#### What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/rc-design/` | Workflow guidance |
| Anchorage and lap length check (EN 1992-1-1) | `calc_lib/rc/ec2_anchorage.py`, `calc_lib/runs/anchorage_check.py`, tests in `tests/test_phase4.py`, `tests/test_phase5.py` | Built and tested; used live on general-notes sheet 004 |
| Anchorage workbook | `tools/xlsxgen/build_anchorage_workbook.py` | Built |
| Concrete and reinforcement general notes | `Structural-Drawing-Standards/04_General-Notes-and-Details/` | APPROVED (user, 14-OCT-2026) |
| Design knowledge | [knowledge/rc-design-workflow.md](knowledge/rc-design-workflow.md) | DRAFT |
| Worked example (drawing set) | `design-basis/examples/PRJ-2026-003/` | Transcribed from drawings; unverified |

#### Build order (proposed)
1. Engineer enters and verifies the EN 1992-1-1 registry values (`config/code_registry/EN1992-1-1_2004_CEN.yaml`, currently all null).
2. Member checks in `calc_lib/rc/`, one at a time with hand-value benchmarks: beam/slab flexure, shear, crack control, deflection by span/depth, column axial + bending, punching.
3. Bar-schedule format approved, then a schedule generator.
4. Reinforcement detail sheets.

---

## Source: `.claude/skills/rc-design/SKILL.md`

---
name: rc-design
description: Entry point for discipline 3, reinforced concrete works (slabs, beams, columns, walls, foundations, ground slabs) to EN 1992-1-1, EN 206 and EN 13670. Use for any RC request - design workflow, anchorage and lap lengths, member checks, reinforcement drawings, bar schedules, concrete specification or calculation report. Not for post-tensioned floors (use pt-floor-design).
---

### Reinforced concrete design (discipline 3)

Read first: `disciplines/rc-works/README.md` and `disciplines/rc-works/knowledge/rc-design-workflow.md`, plus the repo `CLAUDE.md` / `AGENTS.md` rules.

#### State
EARLY. Only the anchorage/lap check is built (`calc_lib/rc/ec2_anchorage.py`). Member checks, bar-schedule format and registry values are missing (gap G28).

#### Route the request
| Request | Do this |
|---|---|
| Design approach / what to check | Follow `disciplines/rc-works/knowledge/rc-design-workflow.md` |
| Anchorage and lap lengths | `calc_lib/rc/ec2_anchorage.py`; run script `calc_lib/runs/anchorage_check.py`; workbook `tools/xlsxgen/build_anchorage_workbook.py` |
| General notes (concrete, reinforcement) | Skill `structural-drawing`; notes library `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml` |
| Member checks (flexure, shear, punching, columns) | No module yet. Engineer-supplied calculation, or build one in `calc_lib/rc/` with hand-value tests |
| Analysis results | `tools/etabs/` via skill `structural-calculation-report` |
| Concrete / reinforcement specification | Skill `structural-specification` |
| Package check | Skill `structural-document-qa` |

#### Rules
- Concrete class, exposure class, cover, steel grade and loads come from the design basis only.
- Registry values that are null/UNVERIFIED make the dependent check NOT EVALUATED.
- Never mark anything APPROVED. Missing inputs are listed, not assumed.

---

## Source: `disciplines/rc-works/knowledge/rc-design-workflow.md`

### Reinforced concrete works - design workflow

Status: DRAFT (17-OCT-2026), written by Claude as a working outline. Not an approved standard. Contains no design values: every number comes from the project design basis, the code registry or the engineer.

#### 1. Standards family
The design basis (`standards[]`) records the editions and National Annex actually used. The usual family is:

| Topic | Standard |
|---|---|
| Basis of design, combinations | EN 1990 |
| Actions | EN 1991 parts |
| Concrete structures - general rules and rules for buildings | EN 1992-1-1 |
| Structural fire design | EN 1992-1-2 |
| Foundations / geotechnical | EN 1997-1 |
| Seismic (if required) | EN 1998-1 |
| Concrete specification, performance, production, conformity | EN 206 |
| Execution of concrete structures | EN 13670 |
| Weldable reinforcing steel | EN 10080 |

Do not quote clause numbers, factors or limits from memory. Cite only what the code registry or the engineer supplies.

#### 2. Inputs needed before any check
1. Design basis: project code, stage, revision, standards and National Annex stance, design working life, consequence class.
2. Concrete strength class and exposure class per element; nominal cover basis; reinforcement grade and ductility class.
3. Loads and combinations, or an analysis export (ETABS/SAFE) with units and sign convention.
4. Fire resistance period; crack width limits; deflection limits.
5. Geotechnical data for foundations (from the geotechnical report, never assumed).

If any of these is missing, list it and stop; do not assume.

#### 3. Design sequence
1. Durability and cover from exposure class (values from the basis/registry).
2. Analysis results import (`tools/etabs/`), checked for completeness and equilibrium.
3. ULS: flexure, shear, torsion, punching, axial + bending for columns and walls.
4. SLS: stress limits, crack control, deflection.
5. Detailing: anchorage and laps (`calc_lib/rc/ec2_anchorage.py`), minimum and maximum reinforcement, spacing, curtailment.
6. Documentation: general notes, layouts, reinforcement details, bar schedules, calculation report.

#### 4. Deliverables and which shared skill produces them
| Deliverable | Skill |
|---|---|
| General notes, layouts, reinforcement details | `structural-drawing` |
| Concrete and reinforcement specification | `structural-specification` |
| Calculation report and workbook | `structural-calculation-report` |
| Package consistency check | `structural-document-qa` |

#### 5. Open items (gap G28)
- Only the anchorage/lap check is built.
- EN 1992-1-1 registry values are all null and UNVERIFIED.
- No approved bar-schedule format.
