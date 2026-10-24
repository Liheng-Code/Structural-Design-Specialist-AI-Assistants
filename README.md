# Structural Design Specialist AI Assistants

A local, AI-assisted structural design and documentation system with three disciplines on one shared core:

| # | Discipline | Folder | Entry skill | State |
|---|---|---|---|---|
| 1 | Post-tensioned floors (PT slabs, band beams; bonded default, unbonded allowed) | [02_disciplines/pt-floor/](02_disciplines/pt-floor/README.md) | `pt-floor-design` | PT drawings, screening checks, 2F PT example |
| 2 | Steel structures | [02_disciplines/steel/](02_disciplines/steel/README.md) | `steel-design` | Skeleton (gap G27) |
| 3 | Reinforced concrete works | [02_disciplines/rc-works/](02_disciplines/rc-works/README.md) | `rc-design` | Anchorage/lap check only (gap G28) |

AI access (Claude, local Ollama, other assistants), GitHub and NotebookLM: [05_docs/ai-access.md](05_docs/ai-access.md). Rules for every AI: [AGENTS.md](AGENTS.md).

## Start here - folder map
Folders are numbered in reading order. Names are lowercase with hyphens; Python files use underscores.

| Folder | What is in it | Open first |
|---|---|---|
| [01_standards/](01_standards/00-overview.md) | Company drawing standards (title block, cover, drawing index, general notes, drafting styles, CAD templates) and the gap register | `00-overview.md`, `00-gap-register.md` |
| [02_disciplines/](02_disciplines/README.md) | Design knowledge for the three disciplines (`pt-floor/`, `steel/`, `rc-works/`) and `manifest.yaml` (which files belong to each) | `README.md` |
| [03_projects/](03_projects/) | One folder per project with everything about it: design basis, register, inputs, outputs, project scripts. `_template/` holds the blank design basis and PT basis | `<PROJECT-CODE>/design-basis.yaml` |
| [04_tools/](04_tools/) | All Python code: `cadgen/` drawings, `docgen/` reports and specs, `xlsxgen/` workbooks, `etabs/` analysis import, `qa/` package checks, `doc_control/`, `design_basis/` validators, `calc_lib/` calculations, `code_registry/` code parameters, `ai/` MCP server and Ollama helper, `knowledge/` NotebookLM pack builder, `paths.py` folder locations | `paths.py` |
| [05_docs/](05_docs/) | Development plan, architecture, PT roadmap, AI access guide, decision records (`adr/`), `images/` | `ai-access.md` |
| [06_knowledge-pack/](06_knowledge-pack/README.md) | Generated NotebookLM sources, committed to git. Rebuild with `python 04_tools/knowledge/build_knowledge_pack.py` after changing standards, skills or knowledge files, then commit | `README.md` |
| [tests/](tests/) | Automated checks (`python -m unittest discover -s tests`) | - |
| [.claude/skills/](.claude/skills/) | Claude skills: entry skills `pt-floor-design`, `steel-design`, `rc-design`; production skills `structural-*`; PT skills `pt-drawings`, `pt-slab-package` | `structural-documentation` |

Root files: `README.md` (this), `AGENTS.md` (rules for any AI), `CLAUDE.md` (Claude Code), `setup.bat` (first-time setup), `pyproject.toml` (lint/type settings), `.mcp.json` (local MCP server).

## Setup
On the user's PC: double-click `setup.bat` (installs Python libraries, builds the knowledge pack and writes `probe_result.json`). Skills are already in `.claude\skills`.

Python 3.9+, `pip install pyyaml python-docx openpyxl ezdxf matplotlib pillow numpy pint pydantic mcp` (2F PT example scripts also need `shapely`, `pymupdf`) (plus `mypy ruff types-PyYAML` for checks: `python -m mypy`, `python -m ruff check 04_tools/calc_lib/core tests/test_core.py`); LibreOffice (`soffice`) for PDF/XLSX recalculation. Run `python 04_tools/cadgen/probe_cad.py` on the PC that has AutoCAD/ETABS to record what is installed. Run tests: `python -m unittest discover -s tests -v` (222 tests; 13 need LibreOffice, 24 need the 05-drafting-styles folder).

## Use
1. New project: create `03_projects/<PROJECT-CODE>/` and copy `03_projects/_template/design-basis.yaml` into it (and `pt-basis.yaml` for PT); fill known values only; validate it.
2. Ask Claude Code to use `structural-documentation` for a package, or a production skill directly. Finish with `structural-document-qa`.
3. For a full PT slab drawing package: use the skill `pt-slab-package` with the prompt in `.claude/skills/pt-slab-package/references/user-prompt.md`.
4. Register check: `python 04_tools/doc_control/check_register.py <register.csv> --design-basis <db.yaml>`.

## Status of phases
| Phase | State |
|---|---|
| 1 Audit | done (see gap register) |
| 2 Skills + reference maps | done (instruction level; no generators) |
| 3 Design basis + document control | done, 10 tests passing |
| 4 Spec/report generation | DOCX+PDF generator built and tested on PJR-2026-003 examples; one calculation implemented (EN 1992-1-1 anchorage); spec text is SEED from drawings, unverified |
| 5 Excel workflows | built and tested for the anchorage check (live formulas, Inputs/Calc/Outputs/Checks/Log, verifier, 13 tests); other calculations still need workbooks |
| 6 DXF/DWG/PDF | DXF + preview PDF built for cover (001) and drawing list (002), with validator and 24 tests. NO DWG (no AutoCAD/ODA here). PDF is a script-rendered preview, not an AutoCAD plot with the company CTB. Sheets 003-204 not generated |
| 7 ETABS/SAFE import | importer built (XLSX/CSV table exports, unit normalisation, completeness/mapping/superposition/equilibrium checks, SHA-256 provenance) and tested with 20 tests on a SYNTHETIC fixture. The export layout is ASSUMED and NOT verified against a real ETABS/SAFE export; no ETABS here. Not run on any real model |
| 8 Cross-document QA automation | `04_tools/qa/package_qa.py` built: 13 check groups across design basis, register, DOCX/XLSX/DXF/PDF, results tie-out, ETABS import; 35 acceptance tests incl. deliberately incomplete, inconsistent and unsupported-claim packages. Consistency gate only; engineering correctness not judged; DWG, AutoCAD plots, and any sheet without a file are NOT checked |
| PT designer M0 (Dev Plan v2) | Built 16-OCT-2026, awaiting engineer review gate: `04_tools/calc_lib/core` units/status/registry/schemas, registry skeleton, 34 tests, mypy strict + ruff clean. Internal base units provisional (ADR-007 open). No engineering values entered |

## Long-term Product Vision
See `05_docs/product-roadmap-pt.md` for the relationship between the current skill system and the future full bonded-PT design platform.

## Known limitations
- PJR-2026-003 design basis is transcribed from drawings; unverified, editions/generations blank, 8 open items.
- Sheets 101-204 of the example set were not supplied.
- Standards 01-04 and layers 05-04a/05-04b were approved by the user in chat on 14-OCT-2026; 06, 07, 10 absent; report/spec formats still PROPOSED. No engineering approval has been given to anything here.
