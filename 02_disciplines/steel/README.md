# Discipline 2 - Steel structures

Scope: structural steelwork (frames, beams, columns, bracing, connections, base plates) designed to the EN 1993 series and executed to EN 1090-2.

Status: **SKELETON (17-OCT-2026).** Scope, workflow and check list only. No calculation module, code-registry file, steel drawing standard or example exists yet (gap G27); a few steel CAD template blocks exist.

## What exists

| Capability | Location | State |
|---|---|---|
| Entry skill | `.claude/skills/steel-design/` | Workflow guidance; no automated checks |
| Design knowledge | [knowledge/steel-design-workflow.md](knowledge/steel-design-workflow.md) | DRAFT |
| Shared tools usable now | `04_tools/cadgen` (sheets, title block), `04_tools/docgen` (calc report, spec), `04_tools/xlsxgen`, `04_tools/etabs` (analysis results import), `04_tools/qa` | Built for the shared core |
| Steel CAD blocks (bolt spacing table, weld symbols, stiffener / fin plate schematic) | `01_standards/06-templates/` (`BLK_EC3_*`), listed in `06-01-templates-library.md` | Drafted; check the file's status header before use |
| Calculation modules | `04_tools/calc_lib/steel/` | Empty |

## Build order (proposed)
1. Steel section of the design basis (steel grade, execution class, corrosion protection, fire resistance) agreed with the engineer.
2. `04_tools/code_registry/EN1993-1-1_<edition>_CEN.yaml` skeleton; values entered and verified by an engineer.
3. Member checks in `04_tools/calc_lib/steel/` one at a time, each with hand-value tests: cross-section classification, resistance, member buckling.
4. Connection checks to EN 1993-1-8 (bolts, welds, base plates).
5. Steel general notes and layers in `01_standards/` (PROPOSED until approved), then drawing generators.
6. A worked example in `03_projects/<PROJECT-CODE>/`.
