# Structural design specialist project

Three disciplines on one shared core: **1 post-tensioned floors** (`disciplines/pt-floor/`), **2 steel structures** (`disciplines/steel/`), **3 RC works** (`disciplines/rc-works/`). Cross-tool rules and commands: `AGENTS.md` (applies here too).

- Company standards: `Structural-Drawing-Standards/` (authoritative). Check each file's status header; read `00_Company_Standards_Overview.md` and `00_Standards_Gap_Register.md` first.
- Skills: `.claude/skills/` - discipline entry skills `pt-floor-design`, `steel-design`, `rc-design`; coordinator `structural-documentation` for packages.
- Project data: `design-basis/<PROJECT-CODE>.yaml` is the single source for code, revision, date, stage, codes, loads, materials.
- Never invent engineering values, clauses, standards or PASS results. Flag gaps. Never mark anything APPROVED; engineer sign-off is human.
- Design to Eurocodes (CEN recommended values unless a National Annex is recorded in the design basis).
- Checks: `python -m unittest discover -s tests`; `python tools/design_basis/validate_design_basis.py <file>`.
- After changing standards, skills or `disciplines/*/knowledge/`: `python tools/knowledge/build_knowledge_pack.py` (NotebookLM pack).
