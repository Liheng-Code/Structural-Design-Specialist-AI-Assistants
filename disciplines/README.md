# Disciplines

The project covers three structural disciplines. They share one core and differ only in their design knowledge, calculation modules and examples.

| # | Discipline | Folder | Entry skill | Design code family | State (17-OCT-2026) |
|---|---|---|---|---|---|
| 1 | Post-tensioned floors (bonded PT slab + band beam) | [pt-floor/](pt-floor/README.md) | `pt-floor-design` | EN 1992-1-1 (incl. prestressed concrete), EN 1990, EN 1991 | Most developed: PT drawings, screening checks, 2F PT example |
| 2 | Steel structures | [steel/](steel/README.md) | `steel-design` | EN 1993 series, EN 1090-2, EN 1990, EN 1991 | Skeleton: scope and workflow only (gap G27) |
| 3 | Reinforced concrete works | [rc-works/](rc-works/README.md) | `rc-design` | EN 1992-1-1, EN 206, EN 13670, EN 1990, EN 1991 | Anchorage/lap check only (gap G28) |

## Shared core (used by all three)

| What | Where |
|---|---|
| Company drawing standards (authoritative) | `Structural-Drawing-Standards/` |
| Project design basis (single source for code, revision, loads, materials) | `design-basis/` |
| Code-dependent parameters (partial factors etc.) | `config/code_registry/` |
| Drawing, report, spec, workbook, ETABS/SAFE import, QA tools | `tools/` |
| Engineering core (units, check status, schemas) | `calc_lib/core/` |
| Production skills (drawing, spec, calc report, QA, coordinator) | `.claude/skills/structural-*` |

## Layout of each discipline folder

```
<discipline>/
  README.md        scope, what exists, what is missing
  knowledge/       design workflow and rules for AI assistants (Markdown; goes into the NotebookLM knowledge pack)
  examples/        worked project examples (project-specific scripts and outputs)
```

Calculation code lives in `calc_lib/<pt|steel|rc>/` so every discipline uses the same units, status and registry from `calc_lib/core/`.

## Rules for every discipline
- Never invent engineering values, clauses, standards or PASS results. A value that is not in the design basis, the code registry or the engineer's input is reported as missing.
- Nothing is marked APPROVED. Engineer sign-off is human.
- Eurocodes with CEN recommended values unless the design basis records a National Annex.
