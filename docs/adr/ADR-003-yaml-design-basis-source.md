# ADR-003 - YAML design basis is the source of truth until M6

Status: ACCEPTED (user, 16-OCT-2026)

## Context
`design-basis/<PROJECT-CODE>.yaml` and the PT basis (`design-basis/PT_BASIS_TEMPLATE.yaml`) are already the single source for code, revision, date, stage, codes, loads and materials, with validators. v1 assumed a database from the start.

## Decision
- Until M6, project data lives in YAML under Git, validated by `tools/design_basis/validate_design_basis.py` and `tools/cadgen/validate_pt_basis.py`.
- At M6 the database imports and exports the same schema, field for field. Any schema change is made in both, with a migration and a version number.
- Unknown values stay null and print as TBC; the database must keep null rather than substitute defaults.

## Consequences
- Every input change is reviewable as a Git diff before M6.
- The M6 database needs round-trip tests (YAML to database to YAML gives the same file).
