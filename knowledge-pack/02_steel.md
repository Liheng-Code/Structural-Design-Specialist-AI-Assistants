# Discipline 2 - Steel structures

Knowledge pack generated 2026-10-17 from commit `b41e123`.

> Generated from the project repository. This is reference material for search and recall, not an approved standard or a calculation result. Each section names its source file; check that file's status header (APPROVED / PROPOSED / DRAFT / SKELETON). Nothing here is engineer-approved unless the source file says so. NotebookLM answers are AI summaries of this text (gap G29).

## Contents

- `disciplines/steel/README.md`
- `.claude/skills/steel-design/SKILL.md`
- `disciplines/steel/knowledge/steel-design-workflow.md`

---

## Source: `disciplines/steel/README.md`

### Discipline 2 - Steel structures

Scope: structural steelwork (frames, beams, columns, bracing, connections, base plates) designed to the EN 1993 series and executed to EN 1090-2.

Status: **SKELETON (17-OCT-2026).** Scope, workflow and check list only. No calculation module, code-registry file, steel drawing standard or example exists yet (gap G27); a few steel CAD template blocks exist.

#### What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/steel-design/` | Workflow guidance; no automated checks |
| Design knowledge | [knowledge/steel-design-workflow.md](knowledge/steel-design-workflow.md) | DRAFT |
| Shared tools usable now | `tools/cadgen` (sheets, title block), `tools/docgen` (calc report, spec), `tools/xlsxgen`, `tools/etabs` (analysis results import), `tools/qa` | Built for the shared core |
| Steel CAD blocks (bolt spacing table, weld symbols, stiffener / fin plate schematic) | `Structural-Drawing-Standards/06_Templates/` (`BLK_EC3_*`), listed in `06-01_Templates_and_Standard_Details_Library.md` | Drafted; check the file's status header before use |
| Calculation modules | `calc_lib/steel/` | Empty |

#### Build order (proposed)
1. Steel section of the design basis (steel grade, execution class, corrosion protection, fire resistance) agreed with the engineer.
2. `config/code_registry/EN1993-1-1_<edition>_CEN.yaml` skeleton; values entered and verified by an engineer.
3. Member checks in `calc_lib/steel/` one at a time, each with hand-value tests: cross-section classification, resistance, member buckling.
4. Connection checks to EN 1993-1-8 (bolts, welds, base plates).
5. Steel general notes and layers in `Structural-Drawing-Standards/` (PROPOSED until approved), then drawing generators.
6. A worked example in `examples/`.

---

## Source: `.claude/skills/steel-design/SKILL.md`

---
name: steel-design
description: Entry point for discipline 2, structural steelwork (frames, beams, columns, bracing, connections, base plates) to the EN 1993 series and EN 1090-2. Use for any steel structure request - design workflow, member or connection checks, steel drawings, steelwork specification or calculation report. Guidance only; no automated steel checks exist yet.
---

### Steel structure design (discipline 2)

Read first: `disciplines/steel/README.md` and `disciplines/steel/knowledge/steel-design-workflow.md`, plus the repo `CLAUDE.md` / `AGENTS.md` rules.

#### State
SKELETON. No steel calculation module, code-registry file, steel drawing standard or example exists (gap G27). Say so in every answer that relies on automation.

#### Route the request
| Request | Do this |
|---|---|
| Design approach / what to check | Follow `disciplines/steel/knowledge/steel-design-workflow.md` |
| Analysis results (ETABS/SAFE export) | `tools/etabs/etabs_import.py` via skill `structural-calculation-report` |
| Member or connection check | No module yet. Either the engineer supplies a verified calculation, or build a new module in `calc_lib/steel/` with hand-value tests (see below) |
| GA / connection drawings | Skill `structural-drawing` (no steel layers or notes standard yet: propose them, mark PROPOSED, log a gap) |
| Steelwork specification | Skill `structural-specification` |
| Package check | Skill `structural-document-qa` |

#### Building a steel check
1. Parameters (partial factors, imperfection factors, limits) go in `config/code_registry/EN1993-<part>_<edition>_CEN.yaml` with `value: null`, `status: UNVERIFIED`. An engineer enters and verifies them.
2. Code in `calc_lib/steel/<check>.py`: pure functions, units via `calc_lib/core/units.py`, status via `calc_lib/core/status.py`.
3. Tests in `tests/test_steel_<check>.py` against hand calculations the engineer supplies or checks.

#### Rules
- Never quote EN 1993 clauses, factors or section properties from memory. Section properties come from a supplier table or the engineer.
- Never mark anything APPROVED. Missing inputs are listed, not assumed.

---

## Source: `disciplines/steel/knowledge/steel-design-workflow.md`

### Steel structures - design workflow

Status: DRAFT (17-OCT-2026), written by Claude as a working outline. Not an approved standard. Contains no design values: every number comes from the project design basis, the code registry or the engineer.

#### 1. Standards family
The design basis (`standards[]`) records the editions and National Annex actually used. The usual family is:

| Topic | Standard |
|---|---|
| Basis of design, combinations | EN 1990 |
| Actions (self-weight, imposed, wind, snow, thermal, execution) | EN 1991 parts |
| General rules and rules for buildings | EN 1993-1-1 |
| Fire design | EN 1993-1-2 |
| Cold-formed members and sheeting | EN 1993-1-3 |
| Plated structural elements | EN 1993-1-5 |
| Design of joints | EN 1993-1-8 |
| Fatigue | EN 1993-1-9 |
| Material toughness and through-thickness properties | EN 1993-1-10 |
| Composite steel-concrete (if used) | EN 1994-1-1 |
| Execution of steel structures | EN 1090-2 |
| Hot-rolled structural steel products | EN 10025 parts |
| Seismic (if required) | EN 1998-1 |

Do not quote clause numbers, factors or limits from memory. Cite only what the code registry or the engineer supplies.

#### 2. Inputs needed before any check
1. Design basis: project code, stage, revision, standards and National Annex stance, consequence class, design working life.
2. Steel grade and product standard per member type; execution class (EN 1090-2); bolt and weld specifications.
3. Loads and load combinations, or an analysis model export (ETABS/SAFE/other) with its units and sign convention.
4. Restraint and bracing arrangement, effective lengths basis, frame stability approach (sway / non-sway, imperfections).
5. Fire resistance period, corrosion protection system and durability requirements.

If any of these is missing, list it and stop; do not assume.

#### 3. Design sequence
1. Stability system: identify bracing, moment frames, diaphragms.
2. Analysis: global analysis method and imperfections per the design basis; import results with `tools/etabs/`.
3. Members: cross-section classification, cross-section resistance, member buckling (flexural, lateral-torsional), combined actions.
4. Serviceability: deflections and vibration against limits recorded in the design basis.
5. Connections: bolts, welds, end plates, splices, base plates and holding-down bolts.
6. Fire and corrosion: protection system consistent with the basis.
7. Documentation: general arrangement, member schedules, connection details, steel general notes, calculation report.

#### 4. Deliverables and which shared skill produces them
| Deliverable | Skill |
|---|---|
| GA plans, elevations, connection details | `structural-drawing` |
| Steelwork specification (materials, fabrication, erection, inspection) | `structural-specification` |
| Calculation report and workbook | `structural-calculation-report` |
| Package consistency check | `structural-document-qa` |

#### 5. Open items (gap G27)
- No steel drawing standard (layers, member marks, connection detail library, general notes).
- No EN 1993 code-registry file.
- No calculation modules in `calc_lib/steel/`.
- No worked example.
