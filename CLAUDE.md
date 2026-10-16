# Structural documentation project

- Company standards: `Structural-Drawing-Standards/` (authoritative). Check each file's status header; read `00_Company_Standards_Overview.md` and `00_Standards_Gap_Register.md` first.
- Skills: `.claude/skills/` - start with `structural-documentation`.
- Project data: `design-basis/<PROJECT-CODE>.yaml` is the single source for code, revision, date, stage, codes, loads, materials.
- Never invent engineering values, clauses, standards or PASS results. Flag gaps. Never mark anything APPROVED; engineer sign-off is human.
- Design to Eurocodes (CEN recommended values unless a National Annex is recorded in the design basis).
- Checks: `python -m unittest discover -s tests`; `python tools/design_basis/validate_design_basis.py <file>`.
