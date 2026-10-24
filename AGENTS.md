# AGENTS.md - instructions for any AI assistant

This file is read by Claude Code (via `CLAUDE.md`), GitHub Copilot, OpenAI Codex, Gemini CLI, Cursor, Continue, Cline and other coding agents. Local models reach the project through the MCP server or `tools/ai/ask_local.py` (see `docs/AI_ACCESS.md`).

## What this project is
A structural design specialist assistant with **three disciplines** on one shared core:

| # | Discipline | Folder | Entry skill | State |
|---|---|---|---|---|
| 1 | Post-tensioned floors (bonded PT slabs, band beams) | `disciplines/pt-floor/` | `.claude/skills/pt-floor-design/` | Most developed |
| 2 | Steel structures | `disciplines/steel/` | `.claude/skills/steel-design/` | Skeleton (gap G27) |
| 3 | Reinforced concrete works | `disciplines/rc-works/` | `.claude/skills/rc-design/` | Early (gap G28) |

Shared core: `Structural-Drawing-Standards/` (company standards, authoritative), `design-basis/` (project data), `config/code_registry/` (code parameters), `tools/` (drawings, documents, workbooks, ETABS/SAFE import, QA), `calc_lib/core/` (units, status, schemas), `.claude/skills/structural-*` (production skills). Map: `disciplines/README.md`; file lists per discipline: `disciplines/manifest.yaml`.

## Non-negotiable rules
1. Never invent engineering values, clauses, standards or PASS results. If a value is not in the design basis, the code registry or the engineer's input, report it missing.
2. Never mark anything APPROVED. Engineer sign-off is human. Prepare "FOR REVIEW" at most.
3. Eurocodes with CEN recommended values unless a National Annex is recorded in the design basis.
4. `design-basis/<PROJECT-CODE>.yaml` is the single source for project code, revision, date, stage, codes, loads and materials.
5. Read `Structural-Drawing-Standards/00_Company_Standards_Overview.md` and `00_Standards_Gap_Register.md` first; check each standard's status header (APPROVED / PROPOSED). Log new gaps in the gap register instead of inventing a standard.
6. Results built on ASSUMED inputs are INDICATIVE; checks that need an UNVERIFIED registry value are NOT EVALUATED.
7. Bonded PT only in discipline 1. Stop if a document says unbonded.

## How to work
- Pick the discipline, read its `README.md` and entry skill `SKILL.md`, then the shared production skill for the deliverable (`structural-drawing`, `structural-specification`, `structural-calculation-report`, `structural-document-qa`, coordinator `structural-documentation`).
- Calculation code: `calc_lib/<pt|steel|rc>/`, pure functions, units through `calc_lib/core/units.py`, every check with hand-value tests in `tests/`.
- Never commit secrets or uploads (`.env`, local `webapp/data/` from the removed web app mockup).

## Commands
```
python -m unittest discover -s tests                       # full test suite
python tools/design_basis/validate_design_basis.py <file>  # design basis check
python tools/knowledge/build_knowledge_pack.py             # rebuild NotebookLM pack after changing knowledge/skills/standards
python tools/ai/mcp_server.py                              # local read-only MCP server (clients start it themselves)
python tools/ai/ask_local.py --discipline steel "question" # ask local Ollama (qwen3:14b)
```
