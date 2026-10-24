# Structural design specialist project

Three disciplines on one shared core: **1 post-tensioned floors** (`02_disciplines/pt-floor/`), **2 steel structures** (`02_disciplines/steel/`), **3 RC works** (`02_disciplines/rc-works/`). Cross-tool rules and commands: `AGENTS.md` (applies here too).

- Company standards: `01_standards/` (authoritative). Check each file's status header; read `00-overview.md` and `00-gap-register.md` first.
- Skills: `.claude/skills/` - discipline entry skills `pt-floor-design`, `steel-design`, `rc-design`; coordinator `structural-documentation` for packages.
- Project data: `03_projects/<PROJECT-CODE>/design-basis.yaml` is the single source for code, revision, date, stage, codes, loads, materials.
- Never invent engineering values, clauses, standards or PASS results. Flag gaps. Never mark anything APPROVED; engineer sign-off is human.
- Design to Eurocodes (CEN recommended values unless a National Annex is recorded in the design basis).
- Checks: `python -m unittest discover -s tests`; `python 04_tools/design_basis/validate_design_basis.py <file>`.
- After changing standards, skills or `02_disciplines/*/knowledge/`: `python 04_tools/knowledge/build_knowledge_pack.py` (NotebookLM pack, tracked in git - commit it with the change).
