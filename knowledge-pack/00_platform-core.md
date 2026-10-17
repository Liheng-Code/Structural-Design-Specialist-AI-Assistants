# Platform core (shared by all disciplines)

Knowledge pack generated 2026-10-17 from commit `6cba6d9`.

> Generated from the project repository. This is reference material for search and recall, not an approved standard or a calculation result. Each section names its source file; check that file's status header (APPROVED / PROPOSED / DRAFT / SKELETON). Nothing here is engineer-approved unless the source file says so. NotebookLM answers are AI summaries of this text (gap G29).

## Contents

- `AGENTS.md`
- `disciplines/README.md`
- `Structural-Drawing-Standards/00_Company_Standards_Overview.md`
- `Structural-Drawing-Standards/00_Standards_Gap_Register.md`
- `Structural-Drawing-Standards/01_Title-Block/01-01_Title_Block.md`
- `Structural-Drawing-Standards/02_Cover-Page/02-01_Cover_Page.md`
- `Structural-Drawing-Standards/03_Drawing-Index/03-01_Drawing_Index.md`
- `Structural-Drawing-Standards/04_General-Notes-and-Details/04-01_General_Notes_Format.md`
- `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_PT_General_Notes.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-01_Text_Styles.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-02_Annotation_Styles.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-03_Line_Types_and_Thickness.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-04a_README_PROPOSED.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-04b_README_PROPOSED.md`
- `Structural-Drawing-Standards/05_Drafting-Styles/05-05_Style_Reference.md`
- `Structural-Drawing-Standards/06_Templates/06-01_Templates_and_Standard_Details_Library.md`
- `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml`
- `design-basis/PROJECT_TEMPLATE.yaml`
- `config/code_registry/README.md`
- `.claude/skills/structural-documentation/SKILL.md`
- `.claude/skills/structural-documentation/references/deliverable-matrix.md`
- `.claude/skills/structural-documentation/references/document-control.md`
- `.claude/skills/structural-drawing/SKILL.md`
- `.claude/skills/structural-drawing/references/cad-workflow.md`
- `.claude/skills/structural-drawing/references/drawing-package-format.md`
- `.claude/skills/structural-specification/SKILL.md`
- `.claude/skills/structural-specification/references/spec-format.md`
- `.claude/skills/structural-calculation-report/SKILL.md`
- `.claude/skills/structural-calculation-report/references/data-contracts.md`
- `.claude/skills/structural-calculation-report/references/etabs-safe-import.md`
- `.claude/skills/structural-calculation-report/references/report-format.md`
- `.claude/skills/structural-document-qa/SKILL.md`
- `.claude/skills/structural-document-qa/references/qa-checklist.md`
- `docs/adr/README.md`

---

## Source: `AGENTS.md`

### AGENTS.md - instructions for any AI assistant

This file is read by Claude Code (via `CLAUDE.md`), GitHub Copilot, OpenAI Codex, Gemini CLI, Cursor, Continue, Cline and other coding agents. Local models reach the project through the MCP server or `tools/ai/ask_local.py` (see `docs/AI_ACCESS.md`).

#### What this project is
A structural design specialist assistant with **three disciplines** on one shared core:

| # | Discipline | Folder | Entry skill | State |
|---|---|---|---|---|
| 1 | Post-tensioned floors (bonded PT slabs, band beams) | `disciplines/pt-floor/` | `.claude/skills/pt-floor-design/` | Most developed |
| 2 | Steel structures | `disciplines/steel/` | `.claude/skills/steel-design/` | Skeleton (gap G27) |
| 3 | Reinforced concrete works | `disciplines/rc-works/` | `.claude/skills/rc-design/` | Early (gap G28) |

Shared core: `Structural-Drawing-Standards/` (company standards, authoritative), `design-basis/` (project data), `config/code_registry/` (code parameters), `tools/` (drawings, documents, workbooks, ETABS/SAFE import, QA), `calc_lib/core/` (units, status, schemas), `.claude/skills/structural-*` (production skills). Map: `disciplines/README.md`; file lists per discipline: `disciplines/manifest.yaml`.

#### Non-negotiable rules
1. Never invent engineering values, clauses, standards or PASS results. If a value is not in the design basis, the code registry or the engineer's input, report it missing.
2. Never mark anything APPROVED. Engineer sign-off is human. Prepare "FOR REVIEW" at most.
3. Eurocodes with CEN recommended values unless a National Annex is recorded in the design basis.
4. `design-basis/<PROJECT-CODE>.yaml` is the single source for project code, revision, date, stage, codes, loads and materials.
5. Read `Structural-Drawing-Standards/00_Company_Standards_Overview.md` and `00_Standards_Gap_Register.md` first; check each standard's status header (APPROVED / PROPOSED). Log new gaps in the gap register instead of inventing a standard.
6. Results built on ASSUMED inputs are INDICATIVE; checks that need an UNVERIFIED registry value are NOT EVALUATED.
7. Bonded PT only in discipline 1. Stop if a document says unbonded.

#### How to work
- Pick the discipline, read its `README.md` and entry skill `SKILL.md`, then the shared production skill for the deliverable (`structural-drawing`, `structural-specification`, `structural-calculation-report`, `structural-document-qa`, coordinator `structural-documentation`).
- Calculation code: `calc_lib/<pt|steel|rc>/`, pure functions, units through `calc_lib/core/units.py`, every check with hand-value tests in `tests/`.
- Do not commit `webapp/data/` (holds the API key and uploads).

#### Commands
```
python -m unittest discover -s tests                       # full test suite
python tools/design_basis/validate_design_basis.py <file>  # design basis check
python tools/knowledge/build_knowledge_pack.py             # rebuild NotebookLM pack after changing knowledge/skills/standards
python tools/ai/mcp_server.py                              # local read-only MCP server (clients start it themselves)
python tools/ai/ask_local.py --discipline steel "question" # ask local Ollama (qwen3:14b)
```

---

## Source: `disciplines/README.md`

### Disciplines

The project covers three structural disciplines. They share one core and differ only in their design knowledge, calculation modules and examples.

| # | Discipline | Folder | Entry skill | Design code family | State (17-OCT-2026) |
|---|---|---|---|---|---|
| 1 | Post-tensioned floors (bonded PT slab + band beam) | [pt-floor/](pt-floor/README.md) | `pt-floor-design` | EN 1992-1-1 (incl. prestressed concrete), EN 1990, EN 1991 | Most developed: PT drawings, screening checks, 2F PT example |
| 2 | Steel structures | [steel/](steel/README.md) | `steel-design` | EN 1993 series, EN 1090-2, EN 1990, EN 1991 | Skeleton: scope and workflow only (gap G27) |
| 3 | Reinforced concrete works | [rc-works/](rc-works/README.md) | `rc-design` | EN 1992-1-1, EN 206, EN 13670, EN 1990, EN 1991 | Anchorage/lap check only (gap G28) |

#### Shared core (used by all three)

| What | Where |
|---|---|
| Company drawing standards (authoritative) | `Structural-Drawing-Standards/` |
| Project design basis (single source for code, revision, loads, materials) | `design-basis/` |
| Code-dependent parameters (partial factors etc.) | `config/code_registry/` |
| Drawing, report, spec, workbook, ETABS/SAFE import, QA tools | `tools/` |
| Engineering core (units, check status, schemas) | `calc_lib/core/` |
| Production skills (drawing, spec, calc report, QA, coordinator) | `.claude/skills/structural-*` |

#### Layout of each discipline folder

```
<discipline>/
  README.md        scope, what exists, what is missing
  knowledge/       design workflow and rules for AI assistants (Markdown; goes into the NotebookLM knowledge pack)
  examples/        worked project examples (project-specific scripts and outputs)
```

Calculation code lives in `calc_lib/<pt|steel|rc>/` so every discipline uses the same units, status and registry from `calc_lib/core/`.

#### Rules for every discipline
- Never invent engineering values, clauses, standards or PASS results. A value that is not in the design basis, the code registry or the engineer's input is reported as missing.
- Nothing is marked APPROVED. Engineer sign-off is human.
- Eurocodes with CEN recommended values unless the design basis records a National Annex.

---

## Source: `Structural-Drawing-Standards/00_Company_Standards_Overview.md`

### Company Standards Overview

Authoritative company reference for structural documentation. Skills in `.claude/skills/` point here; they do not copy it.

#### Status map (14-Oct-2026)
| Folder | Status | Notes |
|---|---|---|
| 01_Title-Block | APPROVED (user, 14-OCT-2026) | derived from WH-STR-SD R00 |
| 02_Cover-Page | APPROVED (user, 14-OCT-2026) | derived from WH-STR-SD-001 |
| 03_Drawing-Index | APPROVED (user, 14-OCT-2026) | derived from WH-STR-SD-002 |
| 04_General-Notes-and-Details | APPROVED (user, 14-OCT-2026) | derived from WH-STR-SD-003..007 |
| 04-02_PT_General_Notes (in 04) | PROPOSED, not approved (16-OCT-2026) | bonded PT notes, Eurocode; see gap G26 |
| 05_Drafting-Styles | Company standard R00 | `05-05` is an unfinished draft; `05-04a` (5 layers) and `05-04b` (6 layers) approved 14-OCT-2026; `05-04c` (2 PT layers) PROPOSED, not approved |
| 06_Templates | NOT AUTHORED | need DWT, CTB/STB, title-block block |
| 07_Structural-Specification | NOT AUTHORED | |
| 10_Structural-Calculation-Reports | NOT AUTHORED | |
| 20_Other-Document-Types, 99_Archive | reserved | |

"APPROVED (user, ...)" means the user (P.Liheng) approved the Claude-drafted standard in chat on that date; recorded by Claude on that statement. Anything still marked PROPOSED (report/spec formats) has not been approved. An authorised engineer approves by changing the header status and adding a revision-history entry.

See `00_Standards_Gap_Register.md` for open gaps.

---

## Source: `Structural-Drawing-Standards/00_Standards_Gap_Register.md`

### Standards Gap Register

| ID | Gap | Impact | Proposed resolution | Status |
|---|---|---|---|---|
| G01 | No approved template files (DWT, CTB/STB plot style, title-block block, fonts list) | Cannot claim company-template DWG output | Supply files into `06_Templates/` | Open |
| G02 | `07_Structural-Specification` and `10_Structural-Calculation-Reports` not authored | Spec/report formats are only proposals | Author or approve proposals in skill references | Open |
| G03 | `05-04` layer list has 10 layers; none for members, rebar, grid bubbles, symbols, title block, viewports, xrefs, revision clouds | Drawings need unapproved layers | 5 sheet/title-block/table/view layers drafted in `05-04a_Layer_Extensions_PROPOSED.csv` (needs approval); member, rebar, grid-bubble, symbol, viewport, xref layers still missing | Partly addressed (proposed) |
| G04 | Text heights defined for A3 only | A1/A0 sheets undefined | State scaling rule | Open |
| G05 | `05-03` gives weight ranges; `05-04` gives single values | Ambiguity | Treat CSV as authoritative for CAD unless told otherwise | Open |
| G06 | `05-05_Style_Reference.md` is draft notes, no visual sheet | No visual reference | Produce style reference sheet | Open |
| G07 | Prefix: user confirmed project codes use `PJR-` (14-Oct-2026). Issued R00 set shows `PRJ-2026-003`; the 2-letter site code rule (`WH`, `OF`) is not documented | R00 drawings need correcting at next revision | Correct title blocks to `PJR-2026-003`; state site-code rule | Partly resolved |
| G08 | Revision scheme: `R00` (issued) vs `P01` (PT preliminary) | Rules for P/R/C undocumented | Confirm scheme | Open |
| G09 | Eurocode edition/generation not recorded on drawings. National Annex stance RESOLVED 14-Oct-2026: user confirmed CEN recommended values (no NA for Cambodia), local requirements where more onerous | Editions/generation still blank in design basis | Record editions and 1st/2nd generation per part (user allows combining 1st and 2nd generation, 14-Oct-2026; justification recorded in design basis) | Partly resolved |
| G10 | Drawings 101-108 and 201-204 are listed in SD-002 but were not in the supplied PDF | Cannot audit them | Supply sheets | Open |
| G11 | Revision history files absent for all folders | Document control gaps | Add `Revision_History.md` per folder | Open |
| G12 | ETABS/SAFE and AutoCAD versions on user's PC not verified | Phases 6-7 tooling unproven | Run environment check when PC command access is available | Open |
| G13 | Two-letter site code rule | Prefix for new projects | RESOLVED by user 14-OCT-2026: site code = first two letters of the drawing prefix (WH = warehouse), chosen per site/building type and recorded once in design basis `drawing_prefix` | Closed (user decision) |
| G14 | Title-block geometry was measured from a PDF of the issued set (page aspect 1.429, not A3 1.414); margins 7 mm sides / 5 mm top-bottom, label text set at 2.0 mm (PDF labels look ~1.7 mm) to respect the 2.0 mm minimum | Dimensions are measured, not from the company DWG title-block | Supply the company title-block DWG/DXF or confirm the measurements | Open |
| G15 | Dimension style, hatch and annotative text scaling (05-01/05-02) are not applied by the generator yet | Only cover/list sheets built so far | Implement when layout sheets (101+) are built | Open |
| G16 | ETABS/SAFE importer (tools/etabs) was written to the documented "Export Tables" layout (TABLE: row, header row, units row) and tested only on a SYNTHETIC fixture | Real exports may differ in table/column names, units row, sheet layout or ETABS/SAFE version; SAFE tables not covered | User supplies a real ETABS and/or SAFE table export (XLSX/CSV) and the version; adjust REGISTRY and re-test | Partly addressed 14-OCT-2026: user will export as SQLite `.db`; one real file (GDT_CleanV3.db, ETABS 22.1.0, ExporterVersion 2) was received and `tools/etabs/etabs_db_import.py` reads it. That file has IncludesResults = No, so NO result-table layout has been seen. SAFE .db not seen. Table-export importer (etabs_import.py) still unverified |
| G17 | Package QA (tools/qa) is tested on the PRJ-2026-003 example and mutations of it, not on a real multi-discipline package; numeric tie-out covers only the anchorage check; drawing notes sheets 003-204 do not exist as files so drawing-vs-report values are not compared | Cross-document consistency is only as broad as the files and checks present | Extend tie-out per calculation as new checks are added; supply sheets 003-204 | Open |
| G18 | Existing company DXF set `WH-STR-SD_DXF_R00.zip` (19 sheets 001-007, 101-108, 201-204; found on the user's Desktop\Soil Test, 14-OCT-2026) does NOT follow standard 05: layers are FRAME/TITLE/TEXT/DIM/RC/STEEL/REBAR... not S-xxxx from 05-04; all lineweights are ByLayer default (-3), not 0.18/0.25/0.50; text style ARIAL with heights 1.5-2.8 mm (hundreds of items below the 2.0 mm minimum; 1.7/1.8 most common); no title-block INSERT/attributes (lines + text only); dimension style not checked | The set is usable as GEOMETRY/CONTENT source for sheets 003-204, but would fail validate_dxf and QA as it stands | User decides: (a) restandardise the set (needs a layer map old->S-xxxx and a text-height rule) or (b) revise 05-04 to match the existing layers | User chose to RESTANDARDISE (14-OCT-2026). Done as copies in `design-basis/examples/PRJ-2026-003/restandardised_dxf/` by `tools/cadgen/restandardise.py` using PROPOSED 05-04b layers. 15 of 19 sheets pass validate_dxf. Remaining: 002 drawing list names for 003 and 202 differ from the register; 102, 104, 105, 204 have source geometry 1-10 mm outside the border. Text grew to the 2.0 mm minimum: estimated new text overlaps on 004 (5), 005 (9), 103 (3) need manual review. Not seen in AutoCAD; DXF only |
| G19 | SD-004 (user DXF, text at section C) states "MANDRELS: 4 phi (phi <= 16), 7 phi (phi > 16)" yet its mandrel row prints 40/48/64/80/100 mm = 4 phi for 20 mm and 25 mm bars; 7 phi would give 140/175 mm | Internal inconsistency on the sheet itself (not only against EN 1992-1-1) | Engineer confirms and corrects at next revision | Confirmed by user (P.Liheng) 14-OCT-2026 as a correction item: 20 mm -> 140 mm, 25 mm -> 175 mm. APPLIED 14-OCT-2026 to the restandardised SD-004 DXF (texts 80->140, 100->175; user's original source file untouched), to anchorage_inputs.yaml (as-issued values kept in anchorage_inputs_SD004_R00_as_issued.yaml for the tests) and the calc report, workbook and results JSON were regenerated. Sheet 004 DWG needs re-conversion. Engineer must confirm which revision carries it |
| G20 | Software found by directory listing on the user's PC (not executed, licences not tested): AutoCAD 2018 and 2023, ETABS 21 and 22, SAFE 21 and 22, Revit 2019/2023, Navisworks 2023. Probe 14-OCT-2026 (executed): AutoCAD 2018/2023 with acad.exe and accoreconsole.exe, ETABS 22, SAFE 22, Excel found; ODA File Converter and LibreOffice NOT found. DWG output remains untested. No ETABS/SAFE TABLE EXPORT (xlsx/csv) found in Documents, Downloads or Desktop; only .EDB models of other projects | AutoCAD 2023 could produce DWG via a script or accoreconsole run on the PC; importer still unverified against a real export | User exports tables from a model of this project (Display > Show Tables > Export to Excel) and says the version | Open |
| G21 | Closed 14-OCT-2026: ezdxf, matplotlib, openpyxl, python-docx, PyYAML, numpy, Pillow installed (probe_result.json). comtypes and pywin32 not installed and not needed yet | None | None | Closed |
| G22 | `iso-7200-title-block-print-test-v5.pdf` (received 14-OCT-2026) is a generic ISO 7200 print-calibration sheet with dummy data (GLOBAL ENGINEERING PARTNERS, J. DOE, M. SMITH, PRJ20..., margins 20 mm left / 10 mm others), not the company title block: its layout and margins differ from the issued set and from `Office Title Block .pdf` (7 mm margins, PJR-2026-003 fields). Not adopted. Its lineweight ladder (0.70/0.50/0.35/0.25/0.18) and text ladder (7/5/3.5/2.5/2.0) agree with 05-01/05-03 | Risk of two competing title blocks | User states which governs; if v5 does, 01-01 and common.py must change | Closed: user decided Office Title Block.pdf governs (14-OCT-2026); v5 not used |
| G23 | 2F PT layout redraft (16-OCT-2026) needs layers not in 05-04/05-04a/05-04b: tendons and drop panels/thickened bands. Drafted in `05-04c_Layer_Extensions_PROPOSED.csv`: S-PT-TENDON (colour 3, 0.25) and S-CONC-DROP (colour 4, 0.25). Member, rebar, symbol and tendon-profile layers still missing (see G03) | Redraft DXF uses two layers not yet approved; validate_redraft.py flags them as warnings | User/authorised engineer approves, changes or rejects 05-04c | Open (proposed, NOT approved) |
| G24 | 2F PT tendon profiles redrafted from source sheet 16 (16-OCT-2026, DXF only). For 19 of 32 marks the sheet-16 profile length differs from the plan label length - 0.5 m (e.g. Y1: profile 21.20 m, plan 9.45 m; X4: profile 10.52 m, plan 48.25 m). Cause not established: mark names may differ between sheets, one profile may serve several tendons, or a plan label was mis-read | Cannot rely on a profile for a plan tendon of the same mark until checked | Designer (Success Design & Build) or P.Liheng to confirm the profile-to-tendon mapping from the original drawings | Open (observation, not a conclusion) |
| G25 | 2F PT verification screening (16-OCT-2026) has no design-basis file. PT grade (A416 Gr.270 typical), jacking 0.75 fpk, 18 % losses, psi factors, exposure class, d and creep are ASSUMED; mild reinforcement schedule, stressing records, pour sequence, wall/core supports and the designer's calculation are MISSING | Results are indicative only; ULS flexure and punching cannot be closed (NOT CHECKED) | Engineer of record supplies the items; then create design-basis/<PROJECT-CODE>.yaml and rerun disciplines/pt-floor/examples/2F-PT/runs/pt_2f_screening.py | Open |
| G26 | 2F PT calculation report (ADAPT, ACI 318-99, 15 runs, Oct 2019) vs drawing (Rev 01, 2023): frames mapped by span/column pattern. B-line span 19-28 m has 8 strands (86 T) vs 125 T in note; Y strip C-B span 14/16 strands vs 201 T; D-line end spans fit runs 4/12 only if walls at x=5.6/41.4 exist (run 8 needs 266 T vs 130 T drawn); columns D 80/90 and C 60/70 in note vs C4 1100 and C3 800 drawn; CGS lows 4 cm vs 5.6 cm; f'c 31.4 vs 32 MPa; 0.63 T/m edge load not on drawing; punching ratio >1.0 in 8 of 15 runs with no shear reinforcement; required mild steel not on PT sheets; F-line 19 m spans not covered; runs 1/9/5/6/13/14/15 not mapped. | Calculation does not demonstrably cover the drawn PT in 3 spans; basis run and revision unconfirmed | Designer to confirm basis runs, walls, column sizes, B-line stopping of X5-X8, punching steel and mild steel; see 2F_PT_CalcNote_vs_Drawing_Check (v2) | Open |
| G27 | Steel structure discipline added 17-OCT-2026 (`disciplines/steel/`). No company standard for steel drawings (member and connection layers, steel general notes, member marks, connection detail library), no EN 1993 / EN 1090 code-registry file, no steel calculation modules, no example project | Steel work can only follow the skill workflow manually; every value comes from the design basis or the engineer | Author steel notes and layers in `04_`/`05_` (PROPOSED until approved); add `config/code_registry/EN1993-1-1_*_CEN.yaml` skeleton; build checks in `calc_lib/steel/` with hand-value tests | Open |
| G28 | RC works discipline added 17-OCT-2026 (`disciplines/rc-works/`). Only the EN 1992-1-1 anchorage/lap check exists (`calc_lib/rc/ec2_anchorage.py`). No member checks (beam, slab, column, wall, footing), no bar-schedule format standard, EN 1992 registry values all null | RC member design cannot be automated; bar schedules have no company format | Approve a bar-schedule format; add member checks in `calc_lib/rc/` one at a time with benchmarks; engineer enters registry values | Open |
| G29 | NotebookLM knowledge base (17-OCT-2026): `knowledge-pack/` is generated from this repo by `tools/knowledge/build_knowledge_pack.py`. NotebookLM answers are AI summaries of the pack, not a verified source | An answer from NotebookLM could be quoted as if it were a standard or a check result | Treat NotebookLM as search/recall only; cite the repo file it points to; rebuild and re-upload the pack after each change to standards or skills | Open |
| G30 | Skill `pt-slab-structural-design` (added 16-OCT-2026) lists 'locked' numeric defaults (concrete class, fyk, partial factors, strand properties, friction and wobble, draw-in, cover) and mentions unbonded values. Project rules take values only from the design basis / code registry, and PT is bonded only | Values could reach drawings without a source | Treat the defaults as ASSUMED / TBC until the design basis records them; engineer to confirm or remove them from the skill | Open |

Decision log 14-OCT-2026 (user, in chat): site-code rule (G13); reconciliation tolerance "larger of 5 mm or 1 %" accepted; mandrel correction confirmed (G19); restandardise the existing DXF set (G18). Approval of PROPOSED standards 01-04 and 05-04a/05-04b is still pending and can only be given by the user.
Decision log 14-OCT-2026 (later): Office Title Block.pdf governs the title block; standards 01-04 and layer files 05-04a/05-04b approved by the user in chat. Approval was stated by the user and recorded by Claude; it is not an independent engineering review.
- 14-OCT-2026 (decision log): User replied "your recommendation" to the open items. Recorded as the user's acceptance of Claude's recommended defaults, NOT an engineering review: (a) 05-04b layer names and lineweights kept as proposed; (b) mandrel correction 140/175 mm approved for SD-004 and the design basis (NOT yet applied to those files); (c) the drawing register governs sheet names, so sheets 003 and 202 titles follow the register; (d) sheets 102/104/105/204 stay flagged until their source geometry is corrected inside the border; (e) sheets 004, 005, 103 stay flagged for visual overlap review. DWG conversion test via AutoCAD 2023 accoreconsole requested; result pending.

- 14-OCT-2026: AutoCAD 2023 accoreconsole converted WH-STR-SD-001_R00.dxf to a 25,903-byte file with header AC1032 (AutoCAD 2018 DWG format). Opening it in AutoCAD and a visual comparison with the DXF are NOT yet done; text-style substitution (simplex.shx for TrueType fonts) was logged. One sheet only.
- 14-OCT-2026: User opened WH-STR-SD-001_R00.dwg in AutoCAD and sent a screenshot: title block, cover text and isometric all display. Client field still reads the placeholder 'Mr. XXX'. This confirms sheet 001 only; the other 18 sheets are untested and no engineer has reviewed any sheet.
- 14-OCT-2026: DXF-to-DWG by AutoCAD 2023 accoreconsole: all 19 restandardised sheets produced files with header AC1032 (AutoCAD 2018 DWG format). Sheet 102 first failed (undefined HIDDEN linetype in DXF); restandardise.py now falls back to BYLAYER and 102 re-converted OK. Opened visually in AutoCAD: sheet 001 only. Output is a conversion of the DXF, not drawings drafted in AutoCAD; no engineer review.

- 14-OCT-2026: User confirmed 'yes' to applying the mandrel correction; client name left as the placeholder 'Mr. XXX' (user said to hold the client name, wording unclear - confirm). User saw no problems on sheets 004, 102 and 204 in AutoCAD, so those three are logged as visually checked by the user; this is not an engineering review.

---

## Source: `Structural-Drawing-Standards/01_Title-Block/01-01_Title_Block.md`

### 01-01 Title Block - APPROVED (user, 14-OCT-2026)

Source: WH-STR-SD Drawing Set R00 (sheets 001-007) and user's earlier title-block description. Not yet an approved company standard.

- Sheet: A3 landscape, single outer border.
- Title block: strip across the TOP of the sheet, two rows, plus a right-hand box with north arrow and discipline label `STRUCTURAL (BIM)`. No company logo is reproduced.
- Labels: small, grey, upper case. Values: larger, black (text styles per `05-01`).

| | Col 1 | Col 2 | Col 3 | Col 4 | Col 5 |
|---|---|---|---|---|---|
| Row 1 | PROJ. REFERENCE | DRAWING NAME | REVISION | (blank cell) | DRAWN BY |
| Row 2 | DRAWING NUMBER | DRAWING STAGE | CLIENT | SCALE | ISSUE DATE |

Formats: project reference `PJR-YYYY-NNN`; drawing number `<prefix>-STR-<TYPE>-<NNN>`; revision `R00`; scale `AS-SHOWN` / `N.T.S.` / ratio; date `DD-MMM-YYYY` upper case; stage e.g. `FOR APPROVAL`, `SHOP DRAWING`, `PRELIMINARY PT DESIGN`.
Fields are filled from the project design basis and document register only.

#### Revision History
| Rev | Date | Description | By |
|---|---|---|---|
| R00 | 14-Oct-2026 | Proposed from WH-STR-SD R00 | Claude (draft) - awaiting approval |
| R01 | 14-Oct-2026 | Approved; Office Title Block.pdf governs by P.Liheng (stated in chat; recorded by Claude) | P.LIHENG |

Governing source (user decision 14-OCT-2026): `Office Title Block.pdf`. The generic ISO 7200 sheet `iso-7200-title-block-print-test-v5.pdf` (20/10 mm margins, dummy data) is NOT the company title block and is not used.

---

## Source: `Structural-Drawing-Standards/02_Cover-Page/02-01_Cover_Page.md`

### 02-01 Cover Page - APPROVED (user, 14-OCT-2026)

Source: WH-STR-SD-001 (R00). Sheet number `<prefix>-STR-SD-001`, standard title block.

Centred content, top to bottom:
1. `<PROJECT CODE>_<PROJECT NAME>` - largest text, with a thin rule below
2. `STRUCTURAL CONSTRUCTION DRAWING`
3. One line: size/system description | design codes (from design basis)
4. Isometric view of the structure (line drawing)
5. `ISSUE DATE: DD-MMM-YYYY`
6. `REVISION: Rxx`

Values come from the design basis. Text heights from `05-01` (5.0 mm title; 7.0 mm optional).

| Rev | Date | Description | By |
|---|---|---|---|
| R00 | 14-Oct-2026 | Proposed from WH-STR-SD-001 | Claude (draft) |
| R01 | 14-Oct-2026 | Approved by P.Liheng (stated in chat; recorded by Claude) | P.LIHENG |

---

## Source: `Structural-Drawing-Standards/03_Drawing-Index/03-01_Drawing_Index.md`

### 03-01 Drawing Index - APPROVED (user, 14-OCT-2026)

Source: WH-STR-SD-002 (R00). Sheet `<prefix>-STR-SD-002`, heading `STRUCTURAL DRAWING LIST`.

Table columns: Sheet Number | Sheet Name | Paper | Current Revision | Sheet Issue Date. All sheets in numeric order, including 001 and 002.

#### Number series
001 cover; 002 drawing list; 003-007 general notes (parts 01-05); 101-199 layouts, sections, elevations, steel details; 201-299 reinforcement details.

Machine-readable twin: `design-basis/<code>/document_register.csv` (check with `tools/doc_control/check_register.py`). The drawing list sheet and the register must always match.

| Rev | Date | Description | By |
|---|---|---|---|
| R00 | 14-Oct-2026 | Proposed from WH-STR-SD-002 | Claude (draft) |
| R01 | 14-Oct-2026 | Approved by P.Liheng (stated in chat; recorded by Claude) | P.LIHENG |

---

## Source: `Structural-Drawing-Standards/04_General-Notes-and-Details/04-01_General_Notes_Format.md`

### 04-01 General Notes and Details Format - APPROVED (user, 14-OCT-2026)

Source: WH-STR-SD-003 to 007 (R00).

#### Layout
Two text columns on A3. Lettered section headings (`A. GENERAL`, `B. DESIGN CODES` ...) in TEXT_2.5/3.5; numbered notes in TEXT_2.0; small bordered tables for codes, materials, cover, laps, sections, bolts.

#### Sheet split
| Sheet | Part | Sections |
|---|---|---|
| 003 | 01 General, design basis & loading | General; Design codes; Design basis & actions; Load combinations; Design results summary; Assumptions to be confirmed |
| 004 | 02 Concrete & reinforcement | Materials; Cover; Anchorage & laps; Reinforcement notes; Concreting & curing; Earthworks & ground slab; Brickwork |
| 005 | 03 Structural steelwork | Materials; Sections adopted; Fabrication & welding; Corrosion protection; Erection; Connection design basis |
| 006 | 04 RC standard details | Bends & hooks; Lap/anchorage; Corner detail; Reinforcement notation |
| 007 | 05 Steel standard details | Bolt hole/spacing table; Weld symbols; Stiffener/fin plate; Abbreviations |

#### Rules
- Codes, materials, loads, results shown must equal the design basis / calculation report. Notes that are project assumptions appear under "Assumptions to be confirmed" and match design-basis `open_items`.
- No clause reference or value without a source. Unknowns are marked TBC.

| Rev | Date | Description | By |
|---|---|---|---|
| R00 | 14-Oct-2026 | Proposed from WH-STR-SD-003..007 | Claude (draft) |
| R01 | 14-Oct-2026 | Approved by P.Liheng (stated in chat; recorded by Claude) | P.LIHENG |

---

## Source: `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_PT_General_Notes.md`

### 04-02 PT General Notes (bonded post-tensioning, Eurocode) - PROPOSED, NOT APPROVED

Source: notes and legends block of the 2F PT drawing (Success Design & Build, sheet 15, Rev 01, 22-AUG-2023), two images supplied 16-OCT-2026. Design codes changed from BS to Eurocode as instructed; PT system stated as bonded as instructed. Everything else keeps the source wording and values.

#### Where the text lives
- Wording and layout: `.claude/skills/structural-pt-drawing/assets/pt_general_notes.yaml`.
- Project values: `design-basis/<PROJECT-CODE>.pt.yaml` (template `design-basis/PT_BASIS_TEMPLATE.yaml`).
- Sheet: `python tools/cadgen/pt_notes.py` writes the A3 sheet (sheet no. `<PREFIX>-PT-001`), a text copy and a preview PDF.

#### Sections (lettered, two text columns, per 04-01)
A Design codes | B Concrete | C Reinforcement | D Strand properties | E Tendon design parameters | F Rebar arrangement | G Slab step typical details | H Tendon symbol - high / low point | I Tendon symbol - stressing ends and strands | J Tendon symbol details | K Assumptions to be confirmed

#### Rules
- Codes: EN 1990, EN 1991-1-1, EN 1992-1-1 (parts as listed in the PT basis). CEN recommended values unless the design basis records a National Annex.
- A value that is not in the PT basis prints TBC and is listed in section K. The builder never fills values.
- Source values that do not carry straight across to Eurocode stay as the source value or TBC and have an open item (see `.claude/skills/structural-pt-drawing/references/source-conversion-log.md`).
- Only a bonded system is accepted by the builder and the validator.
- The symbol graphics of source legends VI to X (rebar layers, slab step detail, duct and chair, stressing arrows, strand symbols) are written as notes, not drawn. Drawing them is open (gap G26).

| Rev | Date | Description | By |
|---|---|---|---|
| R00 | 16-Oct-2026 | Proposed from the 2F PT notes images; Eurocode, bonded | Claude (draft) |

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-01_Text_Styles.md`

### 05-01 Text Styles – Company Standard (A3)

**Font**: Arial (TrueType)  
**Language**: English  
**Case**: UPPER CASE preferred for titles and notes (mixed case allowed for long paragraphs if clarity improves)

#### 1. Standard Text Heights (Paper Size – A3)

| Style Name          | Height (mm) | Width Factor | Colour | Usage |
|---------------------|-------------|--------------|--------|-------|
| TEXT_2.0            | 2.0         | 1.0          | Black  | General notes, dimensions, labels, call-outs, table body |
| TEXT_2.5            | 2.5         | 1.0          | Black  | Table headers, secondary titles, section names |
| TEXT_3.5            | 3.5         | 1.0          | Black  | Drawing titles, primary titles inside sheets |
| TEXT_5.0            | 5.0         | 1.0          | Black  | Cover page main title, project name |
| TEXT_7.0            | 7.0         | 1.0          | Black  | Large cover titles only (optional) |

#### 2. AutoCAD / CAD Settings

- Annotative: **Yes** (recommended)
- Paper text height: as table above
- Font style: Regular (Bold only for major titles if required)
- Oblique angle: 0° (vertical)
- Justification: Left for notes, Centre for titles

#### 3. Rules

1. Never use text smaller than 2.0 mm on A3.
2. Maintain consistent hierarchy on every sheet.
3. All text must remain legible when printed at 50% (A3 → A4).
4. Avoid special characters that may not print correctly.

#### 4. Revision History

| Rev | Date       | Description              | By |
|-----|------------|--------------------------|----|
| R00 | 14-Oct-2026| Initial company standard | —  |

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-02_Annotation_Styles.md`

### 05-02 Annotation Styles – Company Standard

#### 1. Dimension Style

- Text style: TEXT_2.0 (Arial 2.0 mm)
- Text colour: Black
- Arrow head: Closed filled, size 2.5 mm
- Extension line offset: 1.0 mm
- Extension line extension: 1.5 mm
- Dimension line spacing: 7–8 mm (typical)
- Precision: 0 (or 1 decimal as required by project)
- Zero suppression: Leading zeros suppressed for metric
- Units: Decimal, mm

#### 2. Leader / Multileader

- Text style: TEXT_2.0
- Arrow head: Closed filled, 2.5 mm
- Landing distance: 2–3 mm
- Max leader segments: 2 preferred
- Text colour: Black

#### 3. Hatch Patterns

| Element              | Pattern     | Scale   | Angle | Colour |
|----------------------|-------------|---------|-------|--------|
| Concrete             | AR-CONC     | 25–50   | 0°    | Grey   |
| Structural Steel     | ANSI31      | 10–15   | 45°   | Black  |
| Earth / Fill         | EARTH       | 25      | 0°    | Grey   |
| Insulation / Other   | As required | —       | —     | —      |

#### 4. Section / Detail Call-outs

- Circle / bubble diameter: 8–10 mm
- Text height inside bubble: 2.5 mm or 3.5 mm
- Style: Consistent across the whole set

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-03_Line_Types_and_Thickness.md`

### 05-03 Line Types and Thickness – Company Standard

**Reference**: ISO 128-20 / ISO 128-21 + common structural practice

#### 1. Recommended Line Weights (A3)

| Line Type                  | Thickness (mm) | Colour (ACI) | Typical Use |
|---------------------------|----------------|--------------|-------------|
| Continuous thick          | 0.50 – 0.70    | Black        | Outlines of main structural members, section cuts |
| Continuous medium         | 0.35           | Black        | Secondary outlines, hidden edges (if not dashed) |
| Continuous thin           | 0.18 – 0.25    | Black        | Dimension lines, extension lines, leaders, hatching |
| Dashed                    | 0.25 – 0.35    | Black        | Hidden lines |
| Centre line               | 0.18 – 0.25    | Black / Red  | Grid lines, centre lines |
| Phantom / Cutting plane   | 0.35 – 0.50    | Black / Red  | Section cutting planes |

#### 2. Standard Linetypes

- Continuous
- Dashed (ISO or ACAD_ISO02W100)
- Centre (ISO or ACAD_ISO04W100)
- Phantom (for cutting planes)

#### 3. Rules

1. Never use line weight thinner than 0.18 mm on A3.
2. Maintain clear visual hierarchy: thick = primary structure, thin = annotation.
3. All line weights must remain distinguishable when printed at 50%.

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-04a_README_PROPOSED.md`

### 05-04a Layer Extensions - APPROVED (user, 14-OCT-2026)

`05-04_Layer_Standards.csv` (approved, 10 layers) has no layers for the sheet border, title block, tables or schematic views.
`05-04a_Layer_Extensions_PROPOSED.csv` adds the five layers needed to generate the cover page and drawing list.
Weights follow `05-03` (border 0.50 = thick; title block lines 0.25 = thin; text/table 0.18). Colour 7 (black), Continuous.
Nothing in `05-04` was changed. Approve, edit or reject this file; the CAD generator reads both files and reports any layer outside them.
Linetype names: the company CSV says `Centre` / `Phantom`; the DXF generator maps these to the standard `CENTER` / `PHANTOM` linetypes.

Approved by P.Liheng (stated in chat) 14-OCT-2026. File name keeps the `_PROPOSED` suffix so existing references still resolve.

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-04b_README_PROPOSED.md`

### 05-04b Layer extensions - APPROVED with 05-04a (user, 14-OCT-2026)

Derived 14-OCT-2026 from the layers actually used in the existing set `WH-STR-SD_DXF_R00.zip`
(REBAR, BRACE, BRICK, SOIL, THIN, HIDDEN) which have no counterpart in the approved 05-04 or in 05-04a.
Colours are the existing set's colours; lineweights and the names are Claude's PROPOSALS.
The user chose on 14-OCT-2026 to restandardise the existing set; this file only exists so that restandardised sheets validate.
Status: approved together with 05-04a on the user's 'yes' of 14-OCT-2026. The colours come from the existing set; the names and lineweights were Claude's proposals - confirm or edit them. File name keeps the `_PROPOSED` suffix.
Old -> new map: FRAME->(sheet border, redrawn by title block), TITLE->S-TBLK-* (strip) / S-ANNO-TABLE / S-ANNO-TEXT, TEXT->S-ANNO-TEXT, DIM->S-ANNO-DIMS,
NOTE->S-ANNO-TEXT, GRID->S-GRID, STEEL->S-STEEL-OUTLINE, RC->S-CONC-OUTLINE, HATCH->S-HATCH-CONC, REBAR->S-REBAR, BRACE->S-STEEL-BRACE,
BRICK->S-MASONRY, SOIL->S-SOIL, THIN->S-DETAIL-THIN, HIDDEN->S-HIDDEN.

---

## Source: `Structural-Drawing-Standards/05_Drafting-Styles/05-05_Style_Reference.md`

This can be a one-page visual summary showing:

Sample text at 2.0 / 2.5 / 3.5 / 5.0 mm in Arial
Sample dimension style
Sample leader
Line weight examples
Colour legend


Summary of decisions made for you

Normal text = 2.0 mm (as requested)
Titles follow ISO 3098 progression (2.5 → 3.5 → 5.0 mm)
Font = Arial throughout
Width factor = 1.0
Colour = Black for maximum print reliability

---

## Source: `Structural-Drawing-Standards/06_Templates/06-01_Templates_and_Standard_Details_Library.md`

### 06-01 Templates and Eurocode Standard Details Library - PROPOSED (16-OCT-2026)

Source: `04-01_General_Notes_Format.md` (APPROVED 14-OCT-2026), `04-02_Eurocode_General_Notes_Library.yaml`, and `tools/cadgen/build_notes_and_details.py`.

#### 1. Reusable CAD Detail Blocks (`06_Templates/blocks/`)
Each block is provided in both `.dxf` and `.dwg` (AutoCAD 2018 AC1032 format converted via AutoCAD 2023 `accoreconsole.exe`) and conforms strictly to `05_Drafting-Styles` (`05-01` text heights $\ge 2.0\text{ mm}$, `05-04`/`05-04a`/`05-04b` layers, ByLayer colours and lineweights, millimetre units):

| Block File | Description | Eurocode Reference | Layers Used |
|---|---|---|---|
| `STR_TITLEBLOCK_A3.dxf` / `.dwg` | Company A3 landscape title block with 9 attributes (`PROJ_REFERENCE`, `DRAWING_NAME`, `REVISION`, `DRAWN_BY`, `DRAWING_NUMBER`, `DRAWING_STAGE`, `CLIENT`, `SCALE`, `ISSUE_DATE`) | `01-01_Title_Block.md` | `S-TBLK-BORDER`, `S-TBLK-LINE`, `S-TBLK-TEXT` |
| `BLK_EC2_BENDS_AND_HOOKS.dxf` / `.dwg` | Standard 90° bend ($10\phi$), 135° hook ($10\phi$), 180° hook ($5\phi$), closed link with alternating 135° hooks, and minimum mandrel diameter schedule ($4\phi$ for $\phi \le 16$, $7\phi$ for $\phi > 16$) | EN 1992-1-1 §8.3, Table 8.1N, EN 13670 | `S-REBAR`, `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC2_LAP_SPLICE.dxf` / `.dwg` | Tension lap splice ($l_0 = \alpha_6 l_{bd}$) and anchorage schematic with minimum lap & transverse spacing criteria | EN 1992-1-1 §8.4, §8.7 | `S-REBAR`, `S-ANNO-DIMS`, `S-ANNO-TEXT` |
| `BLK_EC2_CORNER_DETAIL.dxf` / `.dwg` | Typical beam / wall corner L-bar anchorage detail in plan ($50\phi$ / $l_{bd}$) | EN 1992-1-1 §8.4 / §9.2 | `S-CONC-OUTLINE`, `S-REBAR`, `S-ANNO-TEXT` |
| `BLK_EC3_BOLT_SPACING_TABLE.dxf` / `.dwg` | Bolt hole ($d_0$), minimum edge distance ($e_1 \ge 1.2 d_0$), pitch ($p_1 \ge 2.2 d_0$), and tightening schedule for M12–M24 | EN 1993-1-8 Table 3.3, EN 1090-2 | `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC3_WELD_SYMBOLS.dxf` / `.dwg` | Standard fillet weld, CJP butt weld, all-round weld, and field weld schedule | EN 1993-1-8 §4, EN ISO 2553 | `S-ANNO-TABLE`, `S-ANNO-TEXT` |
| `BLK_EC3_STIFFENER_FINPLATE.dxf` / `.dwg` | Typical web stiffener (clipped $20 \times 20$ at corners) and bolted fin-plate connection schematic | EN 1993-1-8, EN 1993-1-5 | `S-STEEL-OUTLINE`, `S-ANNO-TEXT` |

---

#### 2. Standalone Master Sheet Templates (`06_Templates/sheets/`)
Ready-to-use A3 master sheets (`TPL-STR-SD-003` to `007`) in `.dxf`, `.dwg`, and combined preview PDF (`TPL-STR-SD_R00_preview.pdf`):
- `TPL-STR-SD-003_R00`: **General Notes - Part 01 (General, Design Basis & Loading)** — Eurocode design codes table, actions table, EN 1990 load combinations, design results summary template, and assumptions to be confirmed (`F1..Fn`).
- `TPL-STR-SD-004_R00`: **General Notes - Part 02 (Concrete & Reinforcement)** — EN 206 concrete classes & exposure table, EN 1992-1-1 §4.4 nominal cover table, live-computed EN 1992-1-1 §8.4/§8.7 anchorage/lap/mandrel table (`calc_lib/rc/ec2_anchorage.py`), reinforcement notes, concreting & curing, earthworks & ground slab, and brickwork infill notes.
- `TPL-STR-SD-005_R00`: **General Notes - Part 03 (Structural Steelwork)** — EN 10025-2 / EN 14399-3 materials table, steel sections schedule template, EN 1090-2 EXC2 fabrication & welding notes, ISO 12944 corrosion protection, erection sequence, and EN 1993-1-8 connection basis.
- `TPL-STR-SD-006_R00`: **General Notes - Part 04 (RC Standard Details)** — Bends & hooks, mandrel schedule, tension lap splice, corner detail, reinforcement notation, and RC standard notes.
- `TPL-STR-SD-007_R00`: **General Notes - Part 05 (Steel Standard Details)** — EN 1993-1-8 Table 3.3 bolt hole & spacing table, weld symbols, stiffener/fin-plate schematic, abbreviations, and steelwork standard notes.

---

#### 3. Parametric Generation for Any Project
To generate project-specific sheets `003`–`007` directly from a project's `design_basis.yaml` and `document_register.csv`:
```bash
python tools/cadgen/build_notes_and_details.py \
  --design-basis design-basis/<PROJECT>/design_basis.yaml \
  --register design-basis/<PROJECT>/document_register.csv \
  --standards Structural-Drawing-Standards \
  --out design-basis/<PROJECT>/output/cad \
  [--overrides design-basis/<PROJECT>/notes_overrides.yaml]
```
Or generate the full 7-sheet general package (`001` Cover, `002` Drawing List, `003`–`007` General Notes & Standard Details) in one command via `build_sheets.py --include-notes-details`.

---

## Source: `Structural-Drawing-Standards/04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml`

```yaml
# 04-02 Reusable Eurocode General Notes & Standard Details Library
# Status: PROPOSED (derived from approved 04-01_General_Notes_Format.md and WH-STR-SD-003..007)
# Rules:
# - Never invent project-specific engineering values. Any project parameter missing from design_basis.yaml
#   or project overrides is rendered explicitly as "TBC".
# - Anchorage, lap, and mandrel tables on Sheet 004 are computed dynamically via calc_lib/rc/ec2_anchorage.py.

meta:
  id: 04-02
  title: Eurocode General Notes and Standard Details Library
  status: PROPOSED
  version: R00
  date: 16-OCT-2026
  codes_basis: Eurocodes (EN 1990 to EN 1998, EN 206, EN 13670, EN 10025-2, EN 1090-2)

sheet_003:
  title_default: "GENERAL NOTES - PART 01 (GENERAL, DESIGN BASIS & LOADING)"
  scale: "N.T.S."
  general_notes_standard:
    - "THESE NOTES SHALL BE READ WITH ALL ARCHITECTURAL, MEP, EQUIPMENT AND CLADDING SUPPLIER DRAWINGS. ANY DISCREPANCY SHALL BE REPORTED TO THE STRUCTURAL ENGINEER BEFORE WORK PROCEEDS."
    - "ALL DIMENSIONS ARE IN mm AND LEVELS IN m UNLESS NOTED. DO NOT SCALE FROM DRAWINGS. WRITTEN DIMENSIONS GOVERN."
    - "THE CONTRACTOR SHALL VERIFY SITE LEVELS, SETBACKS AND BOUNDARY CLEARANCES BEFORE EXCAVATION."
    - "TEMPORARY WORKS AND STABILITY OF THE PARTLY ERECTED STRUCTURE ARE THE CONTRACTOR'S RESPONSIBILITY. TEMPORARY BRACING SHALL REMAIN UNTIL PERMANENT BRACING AND CLADDING ARE COMPLETE."
  default_codes_supplement:
    - {code: "EN 10025-2, EN 1090-2", scope: "STEEL PRODUCTS, EXECUTION (EXC2)"}
    - {code: "EN 206, EN 13670", scope: "CONCRETE, EXECUTION OF CONCRETE"}
    - {code: "EN 1996-1-1", scope: "MASONRY (INFILL WALL, ROBUSTNESS ONLY)"}
  combinations_standard:
    - "ULS (STR/GEO) EQ. 6.10: 1.35 G + 1.5 Q ; 1.35 G + 1.5 W ; 1.0 G + 1.5 W (UPLIFT) ; 1.35 G + 1.5 Q + 0.9 W (psi0 = 0.6)."
    - "EQUIVALENT HORIZONTAL FORCES (SWAY IMPERFECTION EN 1993-1-1 5.3.2) ADDED TO ALL ULS COMBINATIONS. 2nd-ORDER (P-DELTA) EFFECTS CONSIDERED WHERE APPLICABLE."
    - "SLS CHARACTERISTIC: G + Q ; G + W. DEFLECTION AND SWAY LIMITS PER EN 1990 / PROJECT DESIGN BASIS."

sheet_004:
  title_default: "GENERAL NOTES - PART 02 (CONCRETE & REINFORCEMENT)"
  scale: "N.T.S."
  cement_note: "CEMENT: PORTLAND CEMENT CEM I / II (EN 197-1). NO CALCIUM CHLORIDE. MAX. WATER-CEMENT RATIO 0.55."
  cover_note: "Cnom = Cmin + Delta_c,dev (10 mm). COVER TO BE CONFIRMED AGAINST SITE EXPOSURE (MARINE / CHEMICAL EXPOSURE RAISES THE CLASS)."
  default_materials_table:
    - {element: "LEAN CONCRETE (50 mm)", class_en206: "C12/15", exposure: "X0", notes: "BLINDING LAYER"}
    - {element: "PILE CAPS / TIE & GROUND BEAMS", class_en206: "{rc_foundation_class}", exposure: "XC2", notes: "Dmax 20, S3"}
    - {element: "PRECAST PILES", class_en206: "C40/50 MIN.", exposure: "XC2", notes: "FACTORY, EN 12794"}
    - {element: "COLUMNS / STUMPS / WALLS", class_en206: "{rc_column_class}", exposure: "XC3 / XC4", notes: "Dmax 20, S3"}
    - {element: "GROUND / SUSPENDED SLAB", class_en206: "{rc_slab_class}", exposure: "XC3", notes: "S2, w/c <= 0.55"}
    - {element: "REINFORCEMENT", class_en206: "fyk = {rebar_fyk} MPa DEFORMED", exposure: "-", notes: "EN 10080 DUCTILITY B"}
    - {element: "ANCHOR BOLTS", class_en206: "{anchor_bolt_spec}", exposure: "-", notes: "HOT-DIP GALV."}
    - {element: "GROUT (BASE PLATE)", class_en206: "NON-SHRINK, fck >= 50 MPa", exposure: "-", notes: "40 mm THICK"}
  default_cover_table:
    - {element: "FOUNDATION / PILE CAP (CAST AGAINST LEAN)", cnom: "50"}
    - {element: "FOUNDATION / PILE CAP TOP & SIDES (BACKFILLED)", cnom: "50"}
    - {element: "PRECAST PILE (TO LINKS)", cnom: "40"}
    - {element: "COLUMNS / STUMPS (TO LINKS)", cnom: "40"}
    - {element: "GROUND BEAMS / BOND BEAMS (TO LINKS)", cnom: "40"}
    - {element: "SLABS (TOP / BOTTOM MESH)", cnom: "40 (MIN. 30)"}
    - {element: "SPACER BLOCKS (CONCRETE) AT 1.0 m C/C MAX.", cnom: "REQUIRED"}
  reinforcement_notes:
    - "BAR TYPE: DB = DEFORMED BAR (fyk = {rebar_fyk} MPa); RB / R = PLAIN BAR (LINKS OF 6 mm ONLY IF DEFORMED BAR NOT AVAILABLE). NO BAR SHALL BE REBENT ON SITE EXCEPT AS PERMITTED BY EN 13670."
    - "FOUNDATION / PILE CAP TOP BARS PROVIDED WHERE UPLIFT OCCURS. PILE MAIN BARS ANCHORED INTO CAP PER DETAIL DRAWINGS."
    - "LAPS: STAGGER SO THAT NOT MORE THAN 50% OF BARS ARE LAPPED AT ONE SECTION. NO LAPS AT LOCATIONS OF MAX. MOMENT. BARS > DB32 SHALL NOT BE LAPPED."
    - "LINKS: CLOSED, 135 deg HOOKS WITH 10 phi (MIN. 75 mm) STRAIGHT EXTENSION, ALTERNATING SEATING."
    - "MINIMUM SPACING BETWEEN BARS = MAX(phi, 20 mm, Dmax + 5 mm)."
    - "STARTER BARS & ANCHOR BOLTS SHALL BE FIXED BY TEMPLATE AND SECURED AGAINST DISPLACEMENT; TOLERANCE +/- 3 mm."
    - "FOR GROUND BEAMS AND BOND BEAMS AT WALL CORNERS PROVIDE L-BARS (LAP 50 phi)."
  concreting_notes:
    - "CONCRETE SHALL BE COMPACTED WITH POKER VIBRATORS. NO ADDITION OF WATER ON SITE. MIN. 7 DAYS WET CURING (EN 13670 CURING CLASS 2)."
    - "COMPRESSION TESTING: 1 SET OF 3 SAMPLES PER 50 m3 OR PER POUR (7 / 28 DAYS) TO EN 12390."
    - "CONSTRUCTION JOINTS: REMOVE LAITANCE AND ROUGHEN TO 5 mm AMPLITUDE; WET BEFORE NEXT POUR. PROVIDE 50 mm KEYWAY WHERE REQUIRED."
  earthworks_notes:
    - "REMOVE TOP SOIL AND ORGANIC MATERIAL. PROOF-ROLL SUB-GRADE AND COMPACT FILL TO >= 95% MODIFIED PROCTOR (MDD) IN 200 mm MAX. LAYERS."
    - "FORMATION LEVELS SHALL BE INSPECTED BY THE ENGINEER. REMOVE SOFT SPOTS AND REPLACE WITH LEAN CONCRETE."
    - "GROUND SLAB BUILD-UP: RC SLAB ON 0.2 mm POLYTHENE SLIP MEMBRANE (LAPPED 300) - 50 mm LEAN CONCRETE - 100 mm CRUSHED STONE - COMPACTED FILL."
    - "CONTRACTION (SAWCUT) JOINTS AT 4.0 m x 4.0 m MAX. (<= 25 x SLAB DEPTH), DEPTH 1/4 SLAB, CUT WITHIN 12-24 h AND SEALED."
    - "ISOLATION JOINTS (20 mm COMPRESSIBLE FILLER + SEALANT) AT ALL COLUMNS, WALLS AND EQUIPMENT PLINTHS."
  brickwork_notes:
    - "BRICK WALL 200 mm, CEMENT MORTAR 1:4, PLASTERED BOTH SIDES. PROVIDE RC STIFFENER COLUMNS C2 (200x200 @ ~3.0 m MAX.) AND BOND BEAMS BB1 (200x200)."
    - "MASONRY WALLS ARE NON-LOAD-BEARING. ISOLATE TOP OF WALL FROM PRIMARY STRUCTURE BY 20 mm GAP + FLEXIBLE SEALANT. TIE WALL TO COLUMNS WITH DB8 DOWELS @ 600 (L=500)."

sheet_005:
  title_default: "GENERAL NOTES - PART 03 (STRUCTURAL STEELWORK)"
  scale: "N.T.S."
  default_materials_table:
    - {item: "PLATES, WELDED & HOT-ROLLED", spec: "{steel_main_spec} ; fy = 355 MPa (t <= 40)"}
    - {item: "SECONDARY CHS BRACING STRUTS", spec: "S355J0H (EN 10210) / EN 10219"}
    - {item: "PURLINS & GIRTS (COLD-FORMED)", spec: "S350GD+Z275 (EN 10346), SUPPLIER DESIGN"}
    - {item: "EAVE GUTTER / DOWNPIPES", spec: "GALV. STEEL t = 1.2 (Z275), FALL 1:200"}
    - {item: "BOLTS (STRUCTURAL)", spec: "{steel_bolts_spec}"}
    - {item: "ANCHOR BOLTS", spec: "GRADE 390 / 8.8 THREADED BAR, HDG + WASHER PL"}
    - {item: "BRACING RODS", spec: "CLASS 8.8 RODS + TURNBUCKLES"}
    - {item: "WELDING CONSUMABLES", spec: "E70xx / ER70S (EN ISO 14341), MATCHING S355"}
  fabrication_notes:
    - "FABRICATION AND ERECTION TO EN 1090-2 EXECUTION CLASS EXC2. FACTORY PRODUCTION CONTROL TO EN 1090-1."
    - "WELDS: CONTINUOUS FILLET 6 mm MIN. UNLESS NOTED; FULL-PENETRATION BUTT (CJP) FOR FLANGE-TO-END-PLATE AND ALL SPLICES. WELDERS QUALIFIED TO EN ISO 9606-1; WPS TO EN ISO 15614-1."
    - "NDT: 100% VISUAL; 10% MPI ON FILLET WELDS; 100% UT OF CJP BUTT WELDS AT FLANGE SPLICES, MIN. 20% OTHER (EXC2: ISO 17637 / 17640)."
    - "BUILT-UP WELDED I-SECTIONS: DOUBLE-SIDED 6 mm FILLET (a = 4.2 mm) MIN. WEB-TO-FLANGE WELD, CHECKED FOR SHEAR FLOW."
    - "HOLES FOR M24 = 26 mm, M20 = 22 mm, M16 = 18 mm. EDGE DISTANCE >= 1.2 d0 (>= 40 mm FOR M24), PITCH >= 2.2 d0."
    - "PRELOADED CONNECTIONS: HR / HV 10.9 BOLTS PRELOADED TO 0.7 fub As (M24: 220 kN) BY TORQUE-CONTROL OR PART-TURN. FAYING SURFACES FLAT AND UNPAINTED."
    - "FLY BRACES AT MAX. 3.0 m C/C ALONG COMPRESSION FLANGES OF RAFTERS AND COLUMNS."
    - "FABRICATION TOLERANCES EN 1090-2 CLASS 1; ERECTION TOLERANCES: COLUMN PLUMB h/300 (MAX. 20 mm), FRAME SPACING +/- 5 mm."
    - "NO FIELD WELDING OF PRIMARY MEMBERS WITHOUT ENGINEER'S APPROVAL. NO MEMBER CUT OR DRILLED OUTSIDE APPROVED SHOP DRAWINGS."
    - "CONTRACTOR TO SUBMIT SHOP DRAWINGS AND CONNECTION CALCULATIONS (EN 1993-1-8) FOR APPROVAL BEFORE FABRICATION."
  corrosion_notes:
    - "SURFACE PREPARATION Sa 2.5 (ISO 8501-1). SYSTEM C3 (MEDIUM, 15 YEARS, ISO 12944): 80 um EPOXY ZINC-RICH PRIMER + 120 um POLYURETHANE TOPCOAT (TOTAL 200 um). BOLTS HOT-DIP GALVANISED."
    - "NO PAINT ON AREAS TO BE WELDED OR CONTACT SURFACES OF PRELOADED BOLTS (MASKED)."
    - "PURLINS / GIRTS: Z275 GALVANISED. BASE PLATE AND ANCHOR BOLTS: HOT-DIP GALVANISED (EN ISO 1461)."
    - "CORROSIVITY CATEGORY TO BE CONFIRMED BY CLIENT AGAINST INTERNAL HUMIDITY / CHEMICAL ENVIRONMENT."
  erection_notes:
    - "ERECTION SEQUENCE: BASE PLATES ON SHIMS (40 mm GROUT SPACE) -> COLUMN LIFT -> RAFTER -> ROOF / WALL BRACING IN END BAYS -> EAVE STRUTS -> PURLINS & GIRTS -> CLADDING. FRAMES SHALL NOT BE LEFT UNBRACED."
    - "TENSION RODS: SNUG-TIGHT TURNBUCKLE ONLY; NO PRESTRESS. CHECK LINE AND LEVEL BEFORE FINAL BOLT TIGHTENING."

sheet_006:
  title_default: "GENERAL NOTES - PART 04 (RC STANDARD DETAILS)"
  scale: "N.T.S."
  mandrel_table:
    headers: ["BAR phi (mm)", "MIN. MANDREL (HOOKS/BENDS)", "LINKS (phi <= 16)", "BEND FOR LAPS (phi > 16)"]
    rows:
      - ["8 - 16", "4 phi", "4 phi", "-"]
      - ["20", "7 phi", "-", "7 phi"]
      - ["25", "7 phi", "-", "7 phi"]
      - ["32", "7 phi", "-", "7 phi"]
  rc_standard_notes:
    - "ALL DETAILS FOLLOW EN 1992-1-1 AND EN 13670; IN CASE OF DOUBT CONSULT THE ENGINEER."
    - "LINKS SHALL BE TIED WITH 1.6 mm ANNEALED WIRE AT EVERY BAR INTERSECTION IN COLUMNS / STUMPS (ALTERNATE ELSEWHERE)."
    - "BARS SHALL BE FREE FROM LOOSE RUST, OIL AND MUD AT TIME OF CONCRETING. NO RE-BENDING OF PARTLY EMBEDDED BARS WITHOUT APPROVAL."
    - "MINIMUM CLEAR SPACING = MAX(phi, 20 mm, Dmax + 5 mm = 25 mm). BARS IN COLUMNS: MIN. 40 mm."
    - "SPACER BLOCKS: CONCRETE, SAME GRADE AS ELEMENT (PILE CAPS: 50 mm, 4 No./m2). CHAIRS: STEEL, GALV. FOR SLAB MESH AT 1000 c/c EACH WAY."
    - "STARTER BARS ARE FIXED BY TEMPLATE AND SECURED AGAINST DISPLACEMENT DURING POURING. STARTER LAP = lbd x 1.5 (SD-004)."
    - "CONSTRUCTION JOINTS: ROUGHEN SURFACE TO 5 mm AMPLITUDE, REMOVE LAITANCE; WET BEFORE NEXT POUR. KEYWAY 50 mm."
    - "EXPOSED STUMP EDGES: 20 mm CHAMFER. TOP OF STUMP LEVEL (+0.000) UNDER THE 40 mm BASE GROUT; GROUT SLOPED 1:20 AWAY FROM THE BASE PLATE."
    - "STRIKE-OFF OF FORMWORK: SIDES 24 h MIN. (>= 5 MPa), SOFFITS 7 DAYS."
    - "EMBEDMENTS (ANCHOR BOLTS, SLEEVES) SHALL BE FIXED BEFORE CONCRETING AND CHECKED BY SURVEY: TOLERANCE +/- 3 mm ON ANCHOR BOLTS, +/- 10 mm ON STUMP SETTING-OUT."
  notation_lines:
    - "\"12 DB20\" = 12 BARS Ø20 mm DEFORMED BAR ;  \"DB10-150\" = Ø10 AT 150 mm C/C ;  \"2DB16 TOP\" = 2 BARS Ø16 AT TOP."
    - "BARS ARE MEASURED TO OUTSIDE OF BEND. BAR MARKS: B1, B2 = BOTTOM MESH ; T1, T2 = TOP MESH ; L = LINK ; S = STARTER."

sheet_007:
  title_default: "GENERAL NOTES - PART 05 (STEEL STANDARD DETAILS)"
  scale: "N.T.S."
  bolt_table:
    headers: ["BOLT", "d0 (HOLE)", "e1 (EDGE)", "p1 (PITCH)", "TIGHTENING", "NOTE"]
    rows:
      - ["M12", "14", ">= 1.2 d0 = 17", ">= 2.2 d0 = 31", "SNUG", "SECONDARY"]
      - ["M16", "18", ">= 22", ">= 40", "SNUG", "GIRT CLEATS"]
      - ["M20", "22", ">= 27", ">= 49", "SNUG (8.8)", "BRACING, FIN PL"]
      - ["M24", "26", ">= 31 (40 SPEC.)", ">= 57 (70 SPEC.)", "PRELOAD 10.9 (220 kN)", "PRIMARY JOINTS"]
  weld_table:
    headers: ["SYMBOL", "DESCRIPTION", "TYPICAL USE"]
    rows:
      - ["6 [FILLET]", "CONTINUOUS FILLET 6 mm (BOTH SIDES UNLESS NOTED)", "WEB-FLANGE (a = 4.2), STIFFENERS"]
      - ["8 [FILLET]", "CONTINUOUS FILLET 8 mm", "BASE PL / COLUMN"]
      - ["CJP", "COMPLETE-JOINT-PENETRATION BUTT", "FLANGE SPLICES, END PLATE TO FLANGE"]
      - ["[ALL-ROUND]", "ALL-ROUND WELD", "GUSSET, FIN PL"]
      - ["FW", "FIELD WELD (ONLY WITH APPROVAL)", "-"]
  steel_standard_notes:
    - "STEEL FABRICATION AND ERECTION TO EN 1090-2 (EXC2). SHOP DRAWINGS TO BE APPROVED BEFORE FABRICATION."
    - "ALL STEEL SHALL BE MARKED AND TRACEABLE (EN 10204 TYPE 3.1 CERTIFICATES FOR PRIMARY MEMBERS)."
    - "CUTTING: MACHINE-CUT OR PLASMA, EDGES GROUND SMOOTH; NO FLAME-CUT NOTCHES."
    - "WELDED SECTIONS: WEB-TO-FLANGE WELDS BY SUBMERGED ARC, FULL-LENGTH. CAMBER = L/500 NOT REQUIRED. SWEEP <= L/1000."
    - "HOLES: DRILLED, NOT FLAME-CUT. BOLT LENGTH SO THAT >= 2 THREADS PROJECT BEYOND THE NUT; WASHERS UNDER NUT AND HEAD FOR HV/HR."
    - "ALL BOLTS IN END-PLATE JOINTS SHALL BE TIGHTENED IN A CROSS-PATTERN FROM THE CENTRE OUT; FINAL CHECK BY TORQUE WRENCH."
    - "BASE PLATES SHALL BE GROUTED WITH NON-SHRINK GROUT AFTER FRAME ALIGNMENT AND TEMPORARY BRACING IS IN PLACE."
    - "PURLIN SPLICES ARE LAPPED OVER RAFTERS (SUPPLIER STANDARD). SAG RODS Ø12 AT MID-SPAN WITH DIAGONAL TIES AT RIDGE."
    - "ALL FIELD DRILLING / WELDING DAMAGE SHALL BE MADE GOOD WITH ZINC-RICH PAINT (2 x 40 um)."
    - "FIRE PROTECTION: NOT REQUIRED (SINGLE-STOREY, NO OCCUPANCY-BASED RATING ADVISED) - CONFIRM WITH LOCAL FIRE CODE."
  abbreviations_lines:
    - "PL = PLATE ; FL = FLANGE ; CJP = COMPLETE JOINT PENETRATION ; HR/HV = HIGH-STRENGTH PRELOADED BOLT ; CHS = CIRCULAR HOLLOW SECTION ;"
    - "EXC = EXECUTION CLASS ; MPI = MAGNETIC PARTICLE INSPECTION ; UT = ULTRASONIC TESTING ; MDD = MAXIMUM DRY DENSITY ;"
    - "GB = GROUND BEAM ; BB = BOND BEAM ; PC = STUMP COLUMN ; FFL = FINISHED FLOOR LEVEL."
```

---

## Source: `design-basis/PROJECT_TEMPLATE.yaml`

```yaml
# Design-basis template. Copy to design-basis/<PROJECT-CODE>.yaml and fill in.
# Leave unknowns as null - never guess. Validate:  python tools/design_basis/validate_design_basis.py <file>
project:
  code:               # AAA-YYYY-NNN  e.g. PRJ-2026-003
  name:
  description:
  stage:              # e.g. FOR APPROVAL / SHOP DRAWING / PRELIMINARY PT DESIGN
  client:
  drawing_prefix:     # XX-STR  e.g. WH-STR
  revision:           # R00 / P01 / C01
  issue_date:         # DD-MMM-YYYY
  structure_types: []     # steel | rc | pt | composite | timber | masonry | foundations | seismic
approval:
  status: DRAFT       # DRAFT | FOR_REVIEW | APPROVED
  prepared_by:
  checked_by:
  approved_by:        # authorised engineer (PE/RE) - required for APPROVED
  approved_date:
standards:            # one entry per Eurocode part actually used
  - {id: EN 1990, generation: null, edition: null, used_for: Basis of design}
national_annex:
  mode: UNRESOLVED    # NA | CEN_RECOMMENDED | UNRESOLVED
  country:
  references: []      # exact NA document references when mode = NA
  basis_note:         # required when mode = CEN_RECOMMENDED
regulatory: []
# mixed_generation_justification:   # required if 1st and 2nd generation parts are mixed
design_assumptions:
  design_working_life_years:
  consequence_class:
  units: {length: m, section: mm, force: kN, stress: MPa, pressure: kN/m2}
materials: []         # {id, element, spec, status: confirmed|assumed|to_confirm, source}
loads: []             # {id, description, value, unit, status, source}
combinations: []      # {id, description, status, source}
analysis_provenance:  # software, version, model_file, model_hash, run_date, export_files[]
open_items: []        # {id, status: open|closed, description}
```

---

## Source: `config/code_registry/README.md`

### Design-code registry

Decision: [ADR-004](../../docs/adr/ADR-004-design-code-registry.md). Loader: `calc_lib/core/registry.py`.

Holds every code-dependent parameter the calculations use: partial factors, coefficients and limits. Calculation code never hard-codes them.

#### Files

One YAML file per standard edition and National Annex choice:

- `<standard>_<edition>_CEN.yaml`: CEN recommended values. This is the full parameter list for that edition.
- `<standard>_<edition>_NA-<country>.yaml`: a National Annex overlay. It may only contain parameters that exist in the CEN file.

The project's design basis selects the file: `standards[].edition` and `national_annex.mode` / `national_annex.country`. If the mode is `UNRESOLVED` or the edition is missing, every check that needs the registry reports NOT EVALUATED.

#### File format

```yaml
file_version: 1                 # increase on every change to this file
standard: EN 1992-1-1
edition: "2004"                 # as written in the design basis standards[].edition
national_annex: CEN_RECOMMENDED # or NA
country: null                   # NA files only
na_reference: null              # NA files only: exact NA document reference
effective_date: null
parameters:
  gamma_c.persistent:
    description: Partial factor for concrete, persistent and transient design situations
    kind: dimensionless         # a kind from calc_lib/core/units.py INTERNAL_UNITS
    unit: dimensionless
    value: null
    ndp: true                   # nationally determined parameter
    source_ref: Table 2.1N      # clause / table / equation number only, never clause text
    status: UNVERIFIED          # UNVERIFIED | VERIFIED
    verified_by: null           # required when VERIFIED
    verified_date: null         # required when VERIFIED (YYYY-MM-DD)
    note: null
```

#### Rules

- An agent may add parameter IDs and draft entries, but only as `UNVERIFIED`. Only an engineer sets `VERIFIED`, together with `verified_by` and `verified_date`.
- A check that needs an `UNVERIFIED` or empty value reports NOT EVALUATED and names the parameter. There are no defaults.
- Under a National Annex, a parameter with `ndp: true` must be in the NA file. It never falls back to the CEN value.
- Every calculation run records the registry version string (file versions plus a content hash).
- Store references only. Don't copy clause text from the standards (licensing).

---

## Source: `.claude/skills/structural-documentation/SKILL.md`

---
name: structural-documentation
description: Coordinator for structural document packages (drawings, specification, calculation report, workbooks). Use first when a project needs more than one deliverable, when starting a new project, or when asked to issue/revise a package. Reads the design basis, picks the production skills, tracks the document register and keeps identifiers and revisions consistent.
---

### Structural Documentation Coordinator

You coordinate; the other skills produce. Never produce a deliverable here that a production skill owns.

#### Workflow
1. **Locate the project design basis** in `design-basis/<PROJECT-CODE>.yaml`. If none exists, copy `design-basis/PROJECT_TEMPLATE.yaml`, fill only what the user has stated, leave the rest `null`, and tell the user what is missing. Do not guess codes, editions, National Annex, loads or materials.
2. **Validate it:** `python tools/design_basis/validate_design_basis.py design-basis/<file>.yaml`. Report ERRORs (block approval/issue) and WARNINGs (unresolved items) in plain language.
3. **Identify the discipline** and load its entry skill for the design rules: `pt-floor-design` (bonded PT floors), `steel-design` (steel structures) or `rc-design` (reinforced concrete works). See `disciplines/README.md`. A package can span several disciplines; each keeps its own rules, all share one design basis and register.
4. **Choose skills** from `references/deliverable-matrix.md` for what was asked. Do not generate documents that were not requested.
5. **Maintain the document register** (`design-basis/<code>/document_register.csv`) and check it: `python tools/doc_control/check_register.py <register.csv> --design-basis <design_basis.yaml>`.
6. **Hand off** to the production skill with: project code, drawing prefix, stage, revision, issue date, and the open items affecting that deliverable.
7. **Before any issue**, run `structural-document-qa`. Final issue requires authorised engineering review (see `references/document-control.md`). You may prepare "FOR REVIEW" packages; you may not mark anything APPROVED yourself.

#### Rules
- Company standards live in `Structural-Drawing-Standards/` and are authoritative. Read them; do not copy them into skills.
- Check each standard's header status. Files marked **PROPOSED** (e.g. report and specification formats) are working conventions derived from a real drawing set, not approved standards: follow them, but say so in the report. Standards 01-04 and layers 05-04a/05-04b are approved by the user (14-OCT-2026).
- Any standard the library lacks goes into `Structural-Drawing-Standards/00_Standards_Gap_Register.md` as an open gap rather than being invented.
- Identifiers (project code, prefix, revision, date, stage) come from the design basis only. Never retype them from memory.
- Never claim a phase, check or file is complete unless it was actually run/opened. State what was not verified.

References: `references/deliverable-matrix.md`, `references/document-control.md`.

---

## Source: `.claude/skills/structural-documentation/references/deliverable-matrix.md`

### Deliverable matrix

| Request | Production skill | Output formats | Status of tooling |
|---|---|---|---|
| Drawing set / sheet / cover / drawing list / general notes | `structural-drawing` | DXF, DWG (only with native CAD), PDF | Phase 6: DXF + preview PDF built for sheets 001/002 only; no DWG |
| PT drawings: general notes, tendon plan, tendon profiles, schedule (bonded post-tensioning) | `structural-pt-drawing` | DXF + preview PDF, CSV schedule | Built for PT-001 notes, PT-101 plan, PT-102 profiles; anchorage, band-beam and summary sheets not built; no DWG |
| Technical specification | `structural-specification` | DOCX, PDF | Phase 4 generator built (`tools/docgen`); `07_*` standards not authored |
| Calculation report | `structural-calculation-report` | DOCX, PDF | Phase 4 generator built; only EN 1992 anchorage check implemented; `10_*` standards not authored |
| Calculation workbook | `structural-calculation-report` | XLSX | Phase 5 built for the anchorage check (`tools/xlsxgen`); other checks need their own builders |
| ETABS/SAFE results import | `structural-calculation-report` | CSV/XLSX table exports | `tools/etabs/etabs_import.py` (Phase 7; tested on synthetic data only, real export format unverified) |
| Consistency / readiness check | `structural-document-qa` | issue register CSV/MD | `tools/qa/package_qa.py` (Phase 8): cross-document consistency gate + issue register; consistency only, never an approval |

#### Discipline entry skills
| Discipline | Entry skill | Notes |
|---|---|---|
| 1 Post-tensioned floors | `pt-floor-design` | Most developed; PT drawings + screening checks |
| 2 Steel structures | `steel-design` | Skeleton only (gap G27) |
| 3 Reinforced concrete works | `rc-design` | Anchorage/lap check only (gap G28) |

Until a phase is built, the skill still guides the work manually, but must say that automated generation/validation is unavailable.

#### Typical package (as in WH-STR-SD R00)
Cover (001) -> Drawing list (002) -> General notes (003-007) -> Layouts and elevations (1xx) -> Reinforcement / connection details (2xx). Add specification and calculation report only when requested; all share the design-basis project code, stage and revision.

---

## Source: `.claude/skills/structural-documentation/references/document-control.md`

### Document control

#### Identifiers
| Item | Format | Example | Source of truth |
|---|---|---|---|
| Project code | `PJR-YYYY-NNN` | PJR-2026-003 | design basis `project.code` |
| Drawing number | `<prefix>-STR-<TYPE>-<NNN>` | WH-STR-SD-101 | register |
| Revision | `R00` issued, `P01` preliminary, `C01` construction | R00 | design basis / register |
| Date | `DD-MMM-YYYY` upper case | 13-OCT-2026 | design basis `issue_date` |

Confirmed 14-Oct-2026: project codes use `PJR-`. The issued R00 drawings show `PRJ-2026-003` and must be corrected at next revision. Open: how the 2-letter site code (`WH`, `OF`) is assigned.

#### States
`DRAFT` -> `FOR_REVIEW` -> `APPROVED` (design basis); drawings carry a stage (`FOR APPROVAL`, `SHOP DRAWING`, `PRELIMINARY PT DESIGN`...).

#### Rules
1. Claude may set DRAFT or FOR_REVIEW. **APPROVED needs a named authorised engineer (PE/RE) and date entered by the user**; Claude never fills `approved_by`.
2. A revision bump changes: design basis `revision`/`issue_date`, every affected register row, title blocks, drawing list, and revision history files - all in one change.
3. Superseded files move to `99_Archive/`; never overwrite an issued revision.
4. An issued package must have: design-basis validator = 0 errors, register check = 0 errors, QA issue register with no open Critical/Major items.

#### Drawing prefix / site code (user decision 14-OCT-2026)
Drawing number = `<SS>-STR-<TYPE>-<NNN>`; the two-letter site code SS is the first two letters of the drawing prefix and identifies the site/building type (e.g. WH = warehouse). It is chosen per project and recorded once in the design basis `project.drawing_prefix`. Project code prefix is `PJR-`.

---

## Source: `.claude/skills/structural-drawing/SKILL.md`

---
name: structural-drawing
description: Produce structural drawing sheets (cover page, drawing list, general notes, layouts, details) to company drawing standards for AutoCAD - DXF/DWG and PDF. Use for any request to create, revise or check structural drawings or sheets, or to apply the company title block, layers and text styles.
---

### Structural Drawing

#### Before drawing
1. Read the project design basis (`design-basis/<code>.yaml`); take project code, name, client, prefix, stage, revision and date from it.
2. Read the standards, in this order, noting each file's status header:
   - `Structural-Drawing-Standards/01_Title-Block/`, `02_Cover-Page/`, `03_Drawing-Index/`, `04_General-Notes-and-Details/` (derived from the WH-STR-SD R00 drawing set; approved by the user 14-OCT-2026)
   - `05_Drafting-Styles/` (company standard: text, annotation, line types, layers CSV)
3. Read `references/drawing-package-format.md` (what each sheet type looks like) and `references/cad-workflow.md` (what can and cannot be claimed about outputs).

#### Rules
- A3 landscape, two-row title block across the top, border and layout exactly per standard. Do not restyle.
- Text, dimensions, hatches, line weights and layers only from `05_Drafting-Styles`. Layer names/colours come from `05-04_Layer_Standards.csv`; if a needed layer does not exist, add it to the gap register - do not invent it silently.
- Separate geometry/data (member sizes, grid, levels) from presentation. Member data must come from the design basis/calc outputs; do not draw dimensions or reinforcement that no source supports. Mark unconfirmed values "TBC" on the sheet.
- Every sheet number must exist in the document register; update the drawing list (002) whenever sheets change.
- **Honesty about outputs:** only say "DWG generated/validated" if a native CAD tool produced and opened it. A DXF written by script is a DXF. A rendered PDF/PNG is a preview. Say which one you made and what was not checked (fonts, plot style, xrefs).

#### Output pipeline (built for cover 001, drawing list 002, and Eurocode general notes & standard details 003-007)
- Cover (001) & Drawing List (002): `python tools/cadgen/build_sheets.py --design-basis <db.yaml> --register <register.csv> --standards Structural-Drawing-Standards --out <dir> [--include-notes-details]`
- General Notes & Standard Details (003-007): `python tools/cadgen/build_notes_and_details.py --design-basis <db.yaml> --register <register.csv> --standards Structural-Drawing-Standards --out <dir> [--overrides <notes_overrides.yaml>] [--dwg]`
- Standalone reusable CAD blocks & master sheet templates live in `Structural-Drawing-Standards/06_Templates/` (`blocks/` and `sheets/`), driven by `04_General-Notes-and-Details/04-02_Eurocode_General_Notes_Library.yaml` and `calc_lib/rc/ec2_anchorage.py`. Rebuild templates with `python tools/cadgen/build_notes_and_details.py --export-templates --standards Structural-Drawing-Standards [--dwg]`.
- Always validate every DXF with `python tools/cadgen/validate_dxf.py <sheet.dxf> --standards ... --design-basis ... --register ...` and run `python tools/doc_control/check_register.py` after changing the sheet list.

---

## Source: `.claude/skills/structural-drawing/references/cad-workflow.md`

### CAD workflow and claim discipline

| Artifact | May be called | Requires |
|---|---|---|
| `.dxf` written by script | "DXF generated" | file exists, re-opened by a DXF reader, audit clean |
| `.dwg` | "DWG generated" | produced by AutoCAD / licensed converter AND opened successfully |
| `.pdf` | "PDF plotted" | plotted from the sheet with company plot style; pages rendered and inspected |
| PNG/SVG render | "preview" only | - |

#### Validation checklist (per file)
Units mm; drawing extents inside sheet border; only layers from `05-04_Layer_Standards.csv` (plus approved additions); text heights from `05-01` (>= 2.0 mm on A3); lineweights from layer table; title block fields match design basis/register; no unresolved external references; fonts available (Arial); plot style present.

#### Missing-tool flags
If AutoCAD, the company DWT template, CTB/STB plot style, title-block block definition or fonts are unavailable, say so explicitly and list them in the gap register. Do not substitute silently.

#### Environment on record (Oct 2026)
Cloud workspace: Python, ezdxf, matplotlib, LibreOffice; no AutoCAD/ETABS/ODA. User PC: Autodesk and Graphisoft folders exist; installed CAD/ETABS versions NOT verified (`tools/cadgen/probe_cad.py` must be run there).

#### What the preview PDF is
A matplotlib rendering of the DXF at true A3 size with layer lineweights applied (checked: 0.50 / 0.25 / 0.18 mm measure within 0.02 mm). It is not an AutoCAD plot: no CTB/STB, fonts substituted (Arial -> available sans), no xref handling. Call it a preview.

---

## Source: `.claude/skills/structural-drawing/references/drawing-package-format.md`

### Drawing package format (from WH-STR-SD Drawing Set R00, 7 sheets reviewed)

Status: convention observed from the user's issued drawing set; standards 01-04 approved by the user 14-OCT-2026.

#### Sheet frame
A3 landscape, single outer border. Title block is a strip across the TOP, two rows:
- Row 1: PROJ. REFERENCE | DRAWING NAME | REVISION | (blank cell) | DRAWN BY | north arrow + "STRUCTURAL (BIM)"
- Row 2: DRAWING NUMBER | DRAWING STAGE | CLIENT | SCALE | ISSUE DATE
- Labels small grey upper case; values larger, black. Right-hand box holds north arrow and discipline label (no company logo is reproduced).

Example values: PRJ-2026-003 | STRUCTURAL COVER PAGE | R00 | P.LIHENG | WH-STR-SD-001 | FOR APPROVAL | Mr. XXX | AS-SHOWN | 13-OCT-2026. Notes sheets use scale `N.T.S.`.

#### Numbering series
| Range | Content |
|---|---|
| 001 | Structural cover page |
| 002 | Structural drawing list |
| 003-007 | General notes parts 01-05 |
| 101-108 | Layouts, sections, elevations, steel connection/member details |
| 201-204 | Concrete reinforcement details |

#### Cover page (001)
Centred: `<PROJECT CODE>_<PROJECT NAME>` (large, underlined rule), `STRUCTURAL CONSTRUCTION DRAWING`, one-line description + design codes, isometric structure view, `ISSUE DATE: ...`, `REVISION: ...`.

#### Drawing list (002)
Heading `STRUCTURAL DRAWING LIST`; table columns: Sheet Number | Sheet Name | Paper | Current Revision | Sheet Issue Date. One row per sheet in number order, including the cover and list itself.

#### General notes (003-007)
Two-column text sheets with lettered sections (`A. GENERAL`, `B. DESIGN CODES`, ...), small bordered tables, numbered notes. Current split:
- 003 General, design codes, design basis & actions, load combinations, design results summary, assumptions to be confirmed
- 004 Concrete: materials, cover, anchorage/lap, reinforcement notes, curing, earthworks, brickwork
- 005 Steelwork: materials, sections adopted, fabrication & welding, corrosion protection, erection, connection basis
- 006 RC standard details (bends/hooks, laps, corner detail, notation)
- 007 Steel standard details (bolt table, weld symbols, stiffener/fin plate, abbreviations)

Design-derived values on notes sheets must trace to the design basis / calculation report; keep "assumptions to be confirmed" in sync with `open_items`.

---

## Source: `.claude/skills/structural-specification/SKILL.md`

---
name: structural-specification
description: Write structural technical specifications (general requirements, materials, workmanship, quality control, inspection and testing) as DOCX and PDF following company specification standards. Use when asked to create, revise or check a structural specification or a specification section.
---

### Structural Specification

#### Status
`Structural-Drawing-Standards/07_Structural-Specification/` has NOT been authored yet. Until it exists, follow `references/spec-format.md` (PROPOSED, derived from the lettered-section structure of the WH-STR-SD general notes) and say so in the document control block. If `07_*` files exist later, they override the reference.

#### Workflow
1. Read the design basis (codes, National Annex mode, materials, loads, stage, revision). Specification clauses must agree with it and with drawing general notes.
2. Read `references/spec-format.md`, and the relevant general-note sheets of the drawing set (003-007) so the spec does not contradict them.
3. Draft by section. Every requirement cites its source: Eurocode/EN clause, design-basis item, or drawing sheet. If no source can be named, mark `[SOURCE TBC]` - never invent a clause number, test frequency, tolerance or class.
4. Anything the design basis marks `assumed`/`to_confirm` stays visibly flagged in the text.
5. Generate DOCX + PDF with the generator: write a content file (see `design-basis/examples/PRJ-2026-003/content/specification.yaml`) and run `python tools/docgen/build_document.py <content.yaml> --design-basis <db.yaml> --out <dir>`. It numbers clauses itself, stops on any clause without a source, stamps DRAFT, appends open items, and never fills checked/approved cells. Clauses copied from issued drawings must carry `status: seed`.
6. Check: heading numbering continuous; cross-references resolve; no unresolved placeholders except flagged ones; project code/revision/date match the register; open and render the output files.
7. Hand to `structural-document-qa`; final issue needs authorised engineering review.

Never state compliance ("complies with EN 1090-2") without naming the verified basis.

---

## Source: `.claude/skills/structural-specification/references/spec-format.md`

### Specification format - PROPOSED, pending approval of `07_Structural-Specification/`

Document control block (first page): project code, name, document number `<prefix>-SP-<NNN>`, revision, date `DD-MMM-YYYY`, stage, prepared / checked / approved (blank until a human completes), design-basis revision referenced.

#### Numbering
Decimal: `1`, `1.1`, `1.1.1`. Parts mirror the library tree:
1. General requirements (scope, codes & standards, definitions, submittals, design basis summary)
2. Materials (2.1 concrete, 2.2 reinforcement, 2.3 structural steel, 2.4 bolts & welding consumables, 2.5 other)
3. Workmanship (earthworks & foundations, concrete work, steel fabrication & erection, protection)
4. Quality control (inspection & testing, hold points, records, non-conformance)
5. Appendices (referenced standards table, assumptions to be confirmed)

#### Clause style
Imperative, one requirement per clause: "The Contractor shall ...". Each clause ends with a source tag `[EN 13670 §x]`, `[DB: M-CONC-PILE]` or `[SD-004 §B]`. Units SI with mm for sections.

#### Content seeds taken from the R00 drawing notes (verify before reuse)
Concrete classes/exposure and cover table (SD-004), curing (EN 13670), cube testing frequency, steel execution class EXC2 (EN 1090-2), weld NDT percentages, bolt preload, corrosion protection systems (SD-005). Treat as project-specific, not company-standard, until approved.

---

## Source: `.claude/skills/structural-calculation-report/SKILL.md`

---
name: structural-calculation-report
description: Produce structural calculation reports (DOCX/PDF) and Excel calculation workbooks (XLSX) from verified scripts, Excel and ETABS/SAFE results, to Eurocode with the project design basis. Use for design checks, calculation notes, ETABS/SAFE result import, or reviewing calculation traceability.
---

### Structural Calculation Report

#### Status
`10_Structural-Calculation-Reports/` has NOT been authored yet. Use `references/report-format.md` (PROPOSED) until it exists. The DOCX/PDF report generator and one tested calculation (`calc_lib/rc/ec2_anchorage.py`) exist (Phase 4). Excel workbook generation (Phase 5) exists for the anchorage check; ETABS/SAFE table import exists (`tools/etabs/etabs_import.py`, Phase 7) but is tested only on a synthetic fixture and its export layout is unverified against a real file; manual work must still follow the integrity rules below.

#### Non-negotiable integrity rules
- **Never fabricate** forces, displacements, material properties, load combinations, code clauses, or PASS results. Missing input -> stop that check and list it as an open item; do not substitute a plausible number.
- Every input has: symbol, value, unit, source (design basis id / ETABS export / user). Every result has: formula, substituted values, unit, code clause, utilisation, status.
- Use only the code parts and National Annex mode recorded in the design basis. If a required parameter is not in the available text (e.g. NA value), flag it.
- Separate **calc logic** (reusable functions in `calc-lib/`, with tests) from **report formatting**. Reports pull numbers from calc outputs; they are not retyped.
- Independently verify critical results (hand check, second method, or limiting-case test) and record the check; unverified formulas are labelled UNVERIFIED.
- Final conclusions say "satisfies the checks performed under the stated assumptions", never "structure is safe". PASS/FAIL derives from computed utilisation only.

#### Workflow
1. Read design basis; run the validator; list unresolved items affecting these checks.
2. Read `references/report-format.md`, `references/data-contracts.md`, and (if ETABS/SAFE used) `references/etabs-safe-import.md`.
3. Gather inputs -> compute with tested functions in `calc_lib/` (add a run script like `calc_lib/runs/anchorage_check.py` that writes a results JSON, plus tests with hand values) -> write a content file -> `python tools/docgen/build_document.py <content.yaml> --design-basis <db.yaml> --out <dir> --results <results.json>` -> open and inspect every output page. Workbook: `python tools/xlsxgen/build_anchorage_workbook.py <inputs.yaml> --design-basis <db.yaml> --out <file.xlsx>` then `python tools/xlsxgen/verify_workbook.py <file.xlsx> --results <results.json>` (recalculates with LibreOffice, rejects formula errors, typed numbers/literals in Calc, failing hand checks, and report/workbook mismatches). New calculations need their own workbook builder following the same Inputs/Calc/Outputs/Checks/Log structure; never paste computed numbers as values.
3a. ETABS/SAFE results: `python tools/etabs/etabs_import.py <export.xlsx|csv> --out <analysis/<code>> --model-id <id> --model-file <name> --run-date <DD-MMM-YYYY> --members members.csv --expected expected_cases.yaml --hand-totals hand_totals.yaml`. Do NOT start any calculation unless `import_log.json` has `ready_for_calculations: true`; report every WARNING and every NOT CHECKED line to the user. Expected cases and combination factors come from the design basis; the hand total must be an independent take-down with a stated tolerance (the tool assumes none). `--assume-units` only if the user confirms the units. Import success is not evidence the model is correct.
4. Reconcile: values on drawings/specification vs report (e.g. general-note result summary vs report). Hand to `structural-document-qa`.
5. Engineering review sign-off is a human step.

---

## Source: `.claude/skills/structural-calculation-report/references/data-contracts.md`

### Data contracts (column sets; CSV/XLSX/JSON must use these names)

| Contract | Fields |
|---|---|
| project / design basis | see `design-basis/PROJECT_TEMPLATE.yaml` |
| member | member_id, type, section, material_id, length_m, grid_ref, drawing_ref |
| material | id, element, spec, fck_or_fy, unit, status, source |
| load | id, description, value, unit, status, source |
| combination | id, limit_state, expression, status, source |
| analysis_result | model_id, case_or_combo, member_id, station, N, V2, V3, T, M2, M3, unit_force, unit_length |
| design_check | check_id, member_id, clause, demand, capacity, unit, utilisation, status, inputs_ref |
| drawing_ref | member_id, sheet_number, detail_ref |
| workbook_value | report_ref, workbook, sheet, cell, value, unit |

#### Excel workbooks
Sheets: `Inputs` (units, validation, source), `Calc` (formulas only, no hard-coded numbers), `Outputs`, `Checks` (representative cases verified against independent calculation, with date/tester), `Log`. Status is formula-driven: CHECKS FAILING / UNVERIFIED (inputs differ from checked baseline) / CROSS-CHECKED - NOT ENGINEER-REVIEWED / REVIEWED BY <name>. No workbook is called VALIDATED. Hand-calculated expected values live on `Checks`; they apply only to the baseline inputs and show N/A otherwise. Report values cite sheet+cell.

---

## Source: `.claude/skills/structural-calculation-report/references/etabs-safe-import.md`

### ETABS / SAFE result import

Supported route (Phase 7, `tools/etabs/etabs_import.py`): ETABS/SAFE "Export tables to Excel/CSV" files. Direct API use only after the installed version and API are verified on the user's machine (not yet checked).

#### Steps
1. Record provenance: software + version, model file name and modified date, units in the export, analysis run date, who exported.
2. Parse tables (e.g. Frame Forces, Joint Reactions, Story Drifts, Load Combinations). Preserve units; convert only with explicit factor logged.
3. **Completeness/mapping check before any calculation:** every expected load case/combination present; every member id maps to a `member` row and drawing ref; no empty stations; units consistent; combination definitions agree with design basis (e.g. EN 1990 6.10 factors).
4. Record unsupported/missing fields in an import log. Do not fill gaps.
5. Sanity-check results independently (global equilibrium: sum of reactions vs applied load; spot hand calc). **A successful import is not evidence the model is correct** - report the equilibrium check result and flag modelling assumptions.
6. Store imported tables unchanged under `analysis/<code>/raw/`; derived tables separate.

#### Route chosen by the user: SQLite `.db` export (tools/etabs/etabs_db_import.py)
Run: `python tools/etabs/etabs_db_import.py <model.db> --out analysis/<code> --model-id <id> [--members members.csv] [--expected expected_cases.yaml] [--design-basis db.yaml]`.
Seen in one real file (ETABS 22.1.0): tables named like ETABS database tables + `_ModelInfo` (ModelFile, DataUnits, IncludesResults, ExportedAt) + `_Tables` (per-table status). That file has `IncludesResults = No`: it is a MODEL DEFINITION, so there are no reactions/forces and the equilibrium/superposition checks cannot run; `ready_for_calculations` is always false for it. Units are read from `DataUnits` (N_mm_C -> lengths to m); a different `Program_Control.CurrUnits` is warned, not assumed. Checks M1-M11: metadata, units, results present, exporter table status, referential integrity (sections, materials, joints, load names, stories), duplicates, supports, expected cases and combination factors, member mapping, model design codes vs design basis. Results-table layout of this exporter is unknown - never guess it; ask for a file with IncludesResults = Yes. SAFE .db files have not been seen. The source .db is opened read-only and copied unchanged with SHA-256.

#### Tool: tools/etabs/etabs_import.py
Run: `python tools/etabs/etabs_import.py <export> --out <dir> --model-id <id> [--model-file --run-date --software --members --expected --hand-totals --assume-units]`.
Writes `raw/` (unchanged copies + SHA-256), `analysis_results.csv`, `joint_reactions.csv`, `base_reactions.csv` (kN, m), `import_log.json`, `import_report.md`, and `analysis_provenance.proposed.yaml` (proposal only; never applied to the design basis automatically).

**Assumed export layout (UNVERIFIED against a real file):** each sheet / CSV block = row 1 `TABLE:  <name>`, row 2 column headers, row 3 units, then data. Supported tables: Joint Reactions, Base Reactions, Element Forces - Columns/Beams/Braces/Frames, Load Combinations, Program Control. Anything else is reported as UNSUPPORTED and not imported. A real ETABS/SAFE version may name tables or columns differently; the importer then rejects or reports - it never guesses.

| Check | Meaning | Needs |
|---|---|---|
| C1 | expected cases/combinations present | expected_cases.yaml |
| C2 | combination factors equal expected | expected_cases.yaml |
| C3 / C3b | exported members map to project members / members without results | members.csv (`etabs_label` column) |
| C4 | no duplicate (case, member, station) rows | - |
| C5 | combination joint reactions = factor-weighted sum of cases (linear combos only) | expected_cases.yaml |
| C6 | sum of joint-reaction FZ = base-reaction FZ (internal consistency only) | both tables |
| C7 | sum of reactions = independent hand total | hand_totals.yaml with `tolerance_pct` (none is assumed) |
| C8 | units read, recognised, converted; ASSUMED units give a WARNING | - |

Limits: C5/C6 prove internal consistency, not that the model is right. Non-linear combinations, envelopes, response-spectrum and time-history results, SAFE slab/strip tables and mapping to drawing references are NOT handled. FAIL on any check or table blocks `ready_for_calculations`.

---

## Source: `.claude/skills/structural-calculation-report/references/report-format.md`

### Calculation report format - PROPOSED, pending approval of `10_Structural-Calculation-Reports/`

Cover/control block: project code, name, report number `<prefix>-CR-<NNN>`, revision, date `DD-MMM-YYYY`, stage, prepared/checked/approved (human-completed), design-basis revision.

Sections (lettered, matching drawing general notes):
A. Scope & structure description  B. Design codes & National Annex (from design basis)  C. Materials  D. Design basis & actions (loads with sources)  E. Load combinations  F. Analysis model & provenance (software, version, model file, run date, export files)  G. Member / foundation checks (one sub-section each)  H. Results summary table (member, check, demand, capacity, utilisation, status)  I. Assumptions to be confirmed & limitations  J. Appendices (workbook references, ETABS tables)

#### Each check block
`Inputs` (table: symbol, value, unit, source) -> `Formula` (Eurocode notation, clause) -> `Substitution` -> `Result` -> `Utilisation = Ed / Rd` -> `Status`. Units on every line; no unit-less numbers.

#### Results summary
Numbers must equal calc output. Status values: OK (util <= 1.00), NOT OK, NOT CHECKED (missing input), UNVERIFIED (method not independently checked).

---

## Source: `.claude/skills/structural-document-qa/SKILL.md`

---
name: structural-document-qa
description: Quality-check a structural document package (drawings, specification, calculation report, workbook) against company standards and the project design basis, and produce a prioritised issue register. Use before any issue or revision, or when asked to review, audit or cross-check documents.
---

### Structural Document QA

You review; you do not silently fix. Output is an **issue register**, never an approval.

#### Run
1. Automated, whole package: `python tools/qa/package_qa.py <package_dir> --standards Structural-Drawing-Standards [--out <dir>]` (package = `design_basis.yaml`, `document_register.csv`, `output/` with `<NUMBER>_<REV>.<ext>` files and `CALC-*.json`, optional `analysis/*/import_log.json`). It runs the design-basis validator, register check, identity/revision/status/DRAFT-stamp checks on DOCX/XLSX/DXF/PDF, placeholder scan, report-vs-results-vs-workbook number tie-out, inputs-vs-design-basis materials, DXF standards validation, workbook integrity, ETABS/SAFE import log and hash checks, and writes `issue-register.csv` + `qa_report.md`. Exit 1 = open Critical/Major. Individual tools: `tools/design_basis/validate_design_basis.py`, `tools/doc_control/check_register.py`. `python -m unittest discover -s tests` if code changed.
   The tool reports a CONSISTENCY gate only; issue readiness is always NOT READY until an authorised engineer approves. Copy its "Not checked / limits" list into your report. Findings that are Info/Minor are still listed; do not drop them.
2. Manual checks from `references/qa-checklist.md`: standards compliance, cross-document consistency (codes, materials, loads, member sizes, project code/revision/date/stage), unsupported claims, placeholders (XXX, TBC), revision mismatches, output-file integrity (open and render every file).
3. Record each finding in `issue-register.csv` using `references/issue-register-template.csv` columns.

#### Severity
- **Critical** - wrong/unsafe or unsupported engineering claim, fabricated value, PASS without calc basis
- **Major** - inconsistency between documents, missing required standard element, unresolved National Annex/edition for an APPROVED basis
- **Minor** - formatting, numbering, style deviation
- **Info** - observation / open item already flagged

Every finding needs evidence (file, sheet/page, value seen) and corrective action. Review status values: Open, Fixed-awaiting-recheck, Closed (closed only after re-check), Accepted-by-engineer (name+date, human only).

#### Gate
Recommend issue only if there are no open Critical/Major items. State "authorised engineering review required before final issue" in every report. Do not mark Accepted-by-engineer yourself.

Also state what you could not check (software missing, files absent).

---

## Source: `.claude/skills/structural-document-qa/references/qa-checklist.md`

### QA checklist

#### A. Identity & control
- [ ] Project code, name, client identical on every document and equal to design basis
- [ ] Drawing numbers follow `<prefix>-STR-<TYPE>-<NNN>`, unique, listed in drawing list and register
- [ ] Revision/date/stage consistent; revision history updated; superseded files archived
- [ ] Title block fields complete; scale present (AS-SHOWN / N.T.S. / value)

#### B. Design basis consistency
- [ ] Codes on notes sheet = design-basis `standards`; National Annex statement identical
- [ ] Materials (concrete class, exposure, steel grade, bolts, fyk) identical across notes, spec, calc report, drawings
- [ ] Loads and combinations identical; load values traceable to a source
- [ ] Results summary on notes sheet equals calculation report values
- [ ] "Assumptions to be confirmed" = open items; none silently dropped
- [ ] No mixing of Eurocode generations; editions stated

#### C. Calculations
- [ ] Inputs with units/sources; formulas with clause references; no hard-coded numbers in workbook calc sheets
- [ ] PASS/OK only where utilisation computed; independent check recorded
- [ ] ETABS/SAFE provenance recorded, equilibrium check done

#### D. Drawings
- [ ] Layers/text/lines per `05_Drafting-Styles`; text >= 2.0 mm; lineweights >= 0.18 mm
- [ ] Section/detail bubble references resolve to existing sheets
- [ ] File type claims honest (DXF vs DWG vs preview)

#### E. Documents
- [ ] Heading numbers continuous; cross-references resolve; tables not truncated
- [ ] Placeholders (XXX, TBC, TBD) listed as open items
- [ ] All output files open and render; page counts match lists

---

## Source: `docs/adr/README.md`

### Architecture decision records

Software decisions for the bonded PT band beam & slab designer. Context: [Development Plan v2](../Development%20Plan%20v2.md), [Architecture v2](../Architecture%20v2.md), [tech stack page](https://claude.ai/artifact/8JPdaQXtUGDfXKxMMzh9zX).

These records cover software only. They are not engineering approvals: no calculation, value, clause or deliverable becomes approved because of anything here.

Status values: PROPOSED, ACCEPTED (who, date), OPEN (not decided), SUPERSEDED (by ADR-xxx).

| ADR | Decision | Status |
|---|---|---|
| [001](ADR-001-python-engineering-core.md) | Python engineering core; TypeScript only in the front end | ACCEPTED (user, 16-OCT-2026) |
| [002](ADR-002-analysis-adapter-safe-etabs.md) | Analysis results through an adapter; SAFE/ETABS import first | ACCEPTED (user, 16-OCT-2026) |
| [003](ADR-003-yaml-design-basis-source.md) | YAML design basis stays the source of truth until M6 | ACCEPTED (user, 16-OCT-2026) |
| [004](ADR-004-design-code-registry.md) | Versioned design-code registry with verification status | ACCEPTED (user, 16-OCT-2026) |
| [005](ADR-005-api-fastapi.md) | FastAPI for the server API | ACCEPTED (user, 16-OCT-2026) |
| [006](ADR-006-job-queue-redis-rq.md) | Redis + RQ for background jobs | ACCEPTED (user, 16-OCT-2026) |
| [007](ADR-007-units-pint.md) | pint for unit handling | ACCEPTED (user, 16-OCT-2026); internal base units OPEN |
| [008](ADR-008-hosting-and-data.md) | Supabase for database, files and auth; Vercel for the front end | ACCEPTED (user, 16-OCT-2026); container host OPEN |
| [009](ADR-009-front-end.md) | Next.js + TypeScript + Tailwind front end | ACCEPTED (user, 16-OCT-2026); viewer and chart libraries PROPOSED |
| [010](ADR-010-claude-tool-layer.md) | AI (Claude or local Ollama models) through a server-side, schema-validated tool layer | ACCEPTED (user, 16-OCT-2026); amendment 1 adds local models |
| [011](ADR-011-quality-gates.md) | unittest + benchmark register + mypy + ruff; CI when a remote exists | ACCEPTED (user, 16-OCT-2026) |
