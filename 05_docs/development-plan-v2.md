# Development Plan v2 - Bonded PT Band Beam & Slab Designer

Status: PROPOSED (16-OCT-2026). Architecture decisions in §3 ACCEPTED by the user (16-OCT-2026). No engineering approval.
Supersedes the *structure and sequencing* of Development Plan v1 (file removed 24-OCT-2026; recover it from git history, commit 98caf82, `docs/Development Plan.md`). The engineering requirements in v1 still apply where this document cites them (for example "v1 Part 10.4").
Architecture: [Architecture v2.md](architecture-v2.md).


Sequence update 25-OCT-2026 (user decision): milestones M1-M7 re-sequenced to the user's workflow - structural layout DXF (vertical elements placed by the engineer), then the system proposes sizing, loading, load cases, patterns, combinations, support lines, strips and tendons, then builds and runs the model in SAFE 22 (§4, ADR-012).

Scope update 24-OCT-2026 (user decision): unbonded PT is also supported; bonded stays the default. Where this plan says "bonded", read "bonded (default) or unbonded" unless a step is specific to bonded tendons (e.g. ULS tendon stress, gap G32).
---

## 1. Why v1 is being revised

| v1 assumption | Reality in this repo | Consequence |
|---|---|---|
| Next.js / TypeScript / Supabase web app (Parts 17, 21) | Python CLI tools, Claude Code skills and YAML project data; no web stack, database or auth | v1 contradicts itself ("preserve existing conventions" and "use strict TypeScript"). Decided in ADR-001 below |
| Build from CAD import forwards (M1 CAD, M4 FEA, M7 drawings) | Deliverable side already exists: DXF sheets, PT plan/profile sheets, DOCX/PDF, XLSX, package QA, ETABS/SAFE import | v1 order delays the parts that already work and front-loads the riskiest |
| In-house verified plate/shell FEA with PT is one milestone (M4) | This is a multi-year specialist product (comparable to RAM Concept, ADAPT, SAFE) | Moved to an optional research track behind the analysis adapter |
| "Continue milestone by milestone, do not stop" | Engineering milestones need an engineer to accept benchmarks before the next one starts | Each milestone ends at a review gate |
| Drawing register PT-001...PT-502 | Sheet numbering is set by `01_standards/03-drawing-index` (example set uses `WH-STR-SD-xxx`) | Numbering comes from the standards and the document register, never from the plan |

Unchanged from v1 and binding on every milestone: v1 Part 1 "Fundamental engineering principle", Part 3 scope limits, Part 4 code registry rules, Part 9 benchmark rules, Part 15 Claude operating rules, Part 16 status categories, Part 21 coding rules (except rule 3, see ADR-001), and the repo `CLAUDE.md`.

## 2. What already exists (reuse, do not rebuild)

| Capability | Location | State |
|---|---|---|
| Project design basis (single source) | `03_projects/_template/design-basis.yaml`, `04_tools/design_basis/validate_design_basis.py` | Built, tested |
| Bonded PT basis | `03_projects/_template/pt-basis.yaml`, `04_tools/cadgen/validate_pt_basis.py` | Built; example `03_projects/PJR-2F-PT/` |
| Document register control | `04_tools/doc_control/check_register.py` | Built, tested |
| DXF sheets + preview PDF | `04_tools/cadgen/build_sheets.py`, `build_notes_and_details.py`, `validate_dxf.py` | Cover, list, notes/details built. Not DWG, not a CTB plot |
| PT tendon plan + profile sheets | `04_tools/cadgen/pt_plan.py`, `pt_profiles.py`, `pt_notes.py` | Draws what the data gives; computes nothing |
| DXF plan to PT data | `03_projects/PJR-2F-PT/redraft/convert_plan_to_pt_data.py` | Project-specific prototype |
| Calc report + spec DOCX/PDF | `04_tools/docgen/build_document.py` | Built; one calculation (EC2 anchorage) |
| Calculation library | `04_tools/calc_lib/rc/ec2_anchorage.py` | One check |
| Excel workbooks | `04_tools/xlsxgen/` | Anchorage workbook only |
| ETABS/SAFE result import | `04_tools/etabs/etabs_import.py`, `etabs_db_import.py` | Built; tested on a SYNTHETIC export only |
| Package QA | `04_tools/qa/package_qa.py` | Consistency gate, not engineering correctness |
| Skills | `.claude/skills/` (incl. `pt-drawings`) | Instruction level |

## 3. Architecture decisions

Recorded in [05_docs/adr/](adr/README.md). The full records take precedence over these summaries. All were accepted by the user on 16-OCT-2026 as software decisions; none is an engineering approval.

| ADR | Decision | Open items |
|---|---|---|
| [001](adr/ADR-001-python-engineering-core.md) | Python engineering core (pure, typed, mypy-checked); TypeScript only in the front end. Replaces v1 Part 21 rule 3 | - |
| [002](adr/ADR-002-analysis-adapter-safe-etabs.md) | Analysis through an adapter; SAFE/ETABS import first; in-house FE solver is an optional research track | Amended by ADR-012 |
| [012](adr/ADR-012-safe-api-model-build.md) | System builds and runs the SAFE 22 model from the structural layout DXF through the local CSI API (25-OCT-2026) | SAFE 22 API probe (M4) |
| [003](adr/ADR-003-yaml-design-basis-source.md) | YAML design basis + PT basis are the source of truth until M6; the database round-trips the same schema | - |
| [004](adr/ADR-004-design-code-registry.md) | Versioned registry in `04_tools/code_registry/`; `UNVERIFIED` values give NOT EVALUATED; references only, no clause text | NA decision (§6 input 2) |
| [005](adr/ADR-005-api-fastapi.md) | FastAPI; Pydantic models shared with Claude tool schemas; OpenAPI generates the front-end types | - |
| [006](adr/ADR-006-job-queue-redis-rq.md) | Redis + RQ background jobs, run in a Linux container | - |
| [007](adr/ADR-007-units-pint.md) | pint at every module boundary; internal N, mm, MPa, kN in/out (25-OCT-2026) | - |
| [008](adr/ADR-008-hosting-and-data.md) | Supabase Postgres, Storage and Auth with row-level security; Vercel for the front end; API and workers on a container host | Container host provider (§6 input 6) |
| [009](adr/ADR-009-front-end.md) | Next.js + strict TypeScript + Tailwind; no calculation logic in the browser | dxf-viewer and Plotly.js to be evaluated |
| [010](adr/ADR-010-claude-tool-layer.md) | Claude server-side only, through schema-validated tools; read-only on check results; no approval or issue tools | - |
| [011](adr/ADR-011-quality-gates.md) | unittest + benchmark register + mypy + ruff; CI once a remote exists; engineer gate per milestone | - |

## 4. Milestones

Each milestone ends at a **review gate**: tests pass, benchmark results are tabled, open items are listed, and the engineer accepts or returns it. An agent does not start the next milestone without that acceptance.

### M0 - Foundations (small)
- ADRs: done ([05_docs/adr/](adr/README.md)). Close the ADR-007 base-units decision with the user.
- Create the code registry skeleton and loader (ADR-004); no values entered by the agent.
- Define the shared data schemas as Pydantic models (ADR-001, ADR-005): `GeometryModel`, `AnalysisResults`, `Tendon`, `LossResult`, `CheckResult` (status, inputs, value, limit, method reference, trace), `ReinforcementGroup` (fields from v1 Part 11).
- Add the pint units layer with dimensional checks (ADR-007).
- Add mypy and ruff configuration for the core (ADR-011).
- **Gate:** schemas reviewed; existing test suite still passes.
- **Status (16-OCT-2026):** built, awaiting the gate. `04_tools/calc_lib/core/` (units, status, registry, schemas), `04_tools/code_registry/` (skeleton: EN 1992-1-1:2004 CEN parameter IDs, all values empty and UNVERIFIED), `tests/test_core.py` (34 tests), `pyproject.toml` (mypy strict, ruff). Full suite: 202 tests, 1 failure that predates M0 (`test_pt.Notes`, PT notes sheet 1.3 mm past the border). Open: ADR-007 base units (N, mm, MPa used provisionally).
- **Gate closed 25-OCT-2026 by the user** ("close the M0"): base units N, mm, MPa inside, kN and kN·m for input and output (ADR-007); schemas accepted as built. Full suite at closure: 233 tests OK, 1 skipped (real `GDT_CleanV3.db` not in the repo); mypy strict and ruff clean. This is the user's acceptance of the software foundations, not an engineering approval. Next: M1.

### Re-sequenced 25-OCT-2026 (user decision)
The user set the workflow: the engineer sends a structural layout DXF, and the system proposes the model step by step - element sizing (a check of the sizes drawn), loading, load cases, load patterns, load combinations, support lines, strips, tendons - then builds and runs it in SAFE 22 (ADR-012). Decided with it: input is a structural layout DXF - a concrete body layout in which the engineer has placed and sized the columns, walls, drop panels and band beams - not an architect plan, because vertical elements cannot be estimated reliably from an architect plan (user, 25-OCT-2026; example `03_projects/PJR-2026-004/inputs/str-layout/3F Floor.dxf`); analysis is SAFE 22 driven locally through the CSI API; the system stops for the engineer at three gates (A geometry, B sizing and loads, C strips and tendons) and runs automatically between them.

This replaces the earlier order, which started from a SAFE model built by the engineer (old M1) and imported CAD last (old M5). Importing an engineer-built SAFE model stays available as a second route (M4) for checking existing designs.

Old to new numbering, for documents written before 25-OCT-2026 (ADR-001 to ADR-011, the code registry README and comments): old M1 (SAFE import) is now the second route in M4; old M2 (PT calc library) is split between M3 (modules 1-6) and M5 (modules 7-12); old M3 (design loop, reinforcement) is M5; old M4 (deliverables) is M6; old M5 (CAD import) is M1; old M6 (web app, database) is M7. "From M6" or "until M6" in an ADR means the web-app milestone, now M7.

"The system proposes" means: every number comes from the design basis, the PT basis, approved supplier data, the code registry or an ACCEPTED ruleset rule, and is shown to the engineer with its source at the next gate. A missing or UNVERIFIED value stops the step with `NOT EVALUATED`; it is never filled with a default.

| User step | Milestone | Gate |
|---|---|---|
| 1 Structural layout DXF (engineer) | M1 | A |
| 2 Element sizing, 3 Loading, 4 Load cases, 5 Load patterns, 6 Load combinations | M2 | B |
| 7 Support lines, 8 Strips, 9 Tendons | M3 | C |
| Build, run and read back in SAFE 22 | M4 | D |
| Design checks, reinforcement, deliverables, web app | M5-M7 | - |

### M1 - Structural layout DXF to reviewed geometry (user step 1)
- Generalise `03_projects/PJR-2F-PT/redraft/convert_plan_to_pt_data.py` into a DXF reader in `04_tools/model_builder/` (Architecture v2 diagram 2). Layer names differ per drawing, so a per-project layer map (YAML, e.g. `03_projects/PJR-2026-004/inputs/str-layout/layer-map.yaml`) says which layers and blocks hold columns, walls, slab edge, openings, drop panels, band beams, beams, pour strips, sleeves and grids.
- Output: `GeometryModel` (M0 schema): grids, columns, walls, slab regions, openings, drop panels, band beams; units from the DXF header, checked. Sizes and names are attached from the drawing's labels (e.g. "BB2 (900x350)", "THK: 200mm"); a label that cannot be matched to one element is listed, not guessed.
- Preflight checks: closed slab boundary, duplicate or overlapping elements, columns outside the slab, unsupported entities, unit sanity (a 6 m span read as 6 mm).
- Review output for the engineer: an overlay preview (PDF/DXF) with every recognised element labelled, a list of what was not recognised, and a `GeometryReview` record. Corrections are saved as a checksummed snapshot.
- Benchmarks: `03_projects/PJR-2026-004/inputs/str-layout/3F Floor.dxf` (mock-up project) and the 2F PT layout (PJR-2F-PT).
- **Gate A:** the engineer confirms the geometry of both drawings; all fatal errors are caught; re-running gives the same snapshot.

### M2 - Proposed sizing and loading (user steps 2-6)
- Step 2, sizing: the sizes come from the structural layout (M1); the system checks slab thickness, band beam and drop panel depth and width, and column size against span-to-depth rules, flags any that fail, and proposes a size only where the drawing gives none. Only rules marked ACCEPTED in `02_disciplines/pt-floor/knowledge/pt-master-ruleset.yaml` are used (gap G33: all are UNVERIFIED today).
- Step 3, loading: self-weight from geometry and concrete density; superimposed dead load, live load per area, and line loads (facade, partitions) from the design basis. The system assigns them to regions; it does not choose their values.
- Step 4, load cases: dead, superimposed dead, live, prestress (placeholder until M3), and others the design basis lists.
- Step 5, load patterns: live-load patterning as the design basis records it (rule and pattern set stated, never assumed).
- Step 6, load combinations: EN 1990 ULS and SLS (characteristic, frequent, quasi-permanent) with partial and psi factors from the code registry. Needs a new `04_tools/code_registry/EN1990_2002_CEN.yaml`, values entered by the engineer.
- Output: a model-definition file (sizes, load assignments, `LoadCase`, `Combination`), each value carrying its source.
- **Gate B:** the engineer reviews the sizing and loading summary and accepts or edits it.

### M3 - Support lines, strips and tendons (user steps 7-9)
- Step 7, support lines: generated from column and wall lines in both directions; the engineer can move or merge them at the gate.
- Step 8, design strips: column and middle strip widths from the support lines, by the method the design basis states.
- Step 9, tendons: layout type (banded or distributed) and arrangement from ACCEPTED rules (G33, G34); profiles from cover and support geometry; tendon force from a load-balancing target the design basis states.
- PT calculation modules needed for step 9, each a separate module in `04_tools/calc_lib/pt/` with hand-calculated benchmarks in `tests/` (v1 Part 9 fields: reference, units, assumptions, tolerance, owner, status):
  1. Tendon geometry: parabolic profiles, high/low points, inflection points, cover, curvature, angle change.
  2. Friction and wobble loss along the tendon (EN 1992-1-1:2004 5.10.5.2 form; mu and k from approved system data).
  3. Anchorage draw-in and the affected length.
  4. Elastic shortening (where stressing sequence makes it relevant).
  5. Time-dependent losses: creep, shrinkage, relaxation (EN 1992-1-1:2004 5.10.6 and Annex B).
  6. Equivalent prestress actions from profile and force.
- Module 1 needs no supplier data and can start first; modules 2-5 need the PT system ETA (section 6, input 3).
- **Gate C:** the engineer reviews support lines, strips and the tendon layout, profiles and forces; modules 1-6 match their benchmarks.

### M4 - Build, run and read back in SAFE 22 (ADR-012)
- Probe the SAFE 22 API on the user's PC (CSI OAPI through `comtypes`): version, licence, a one-panel test model. Nothing else starts until this works.
- Build the model from the Gate A-C data: materials, slab areas and band beams, columns and walls as supports, mesh settings, loads, load cases, patterns, combinations, tendon objects (path, profile, strands, jacking force), support lines and strips.
- Save as a new SAFE file; record every API call and the SAFE object IDs (audit trail, input snapshot, SHA-256).
- Run the analysis; read errors and warnings; extract reactions, strip forces and deflections into `AnalysisResults` (reuse `04_tools/etabs/etabs_db_import.py` concepts and its provenance checks).
- Second route: import an engineer-built SAFE model's results (`.db` export) for checking existing designs; this replaces the old M1 and still needs one real export with results (gap G16).
- **Gate D:** SAFE reaction totals equal the applied load totals within stated tolerances; the engineer opens the generated model in SAFE and confirms it matches the reviewed data.

### M5 - Design checks and reinforcement
- Remaining PT modules in `04_tools/calc_lib/pt/`, with benchmarks as in M3:
  7. Stress limits at stressing and at service.
  8. SLS concrete stresses at transfer and service; decompression/crack checks as the design basis requires.
  9. Deflection: short and long term, with the method and its limits stated.
  10. ULS flexure with bonded tendon stress (unbonded: gap G32).
  11. ULS shear (beam) and punching shear including the prestress contribution.
  12. Anchorage-zone bursting and spalling (reuse and extend `04_tools/calc_lib/rc/ec2_anchorage.py`).
- Design loop (Architecture v2 diagram 3): change the tendons, rebuild and re-run in SAFE (M4), re-check; iteration record, iteration limit and a design-failed report (v1 Part 10.7).
- Conventional reinforcement (v1 Part 11): required areas, minimums, spacing, cover, laps, curtailment, punching reinforcement, trimming at openings.
- Clash checks: tendon against tendon, tendon against openings, tendon against bars and anchorages.
- Clause references are to EN 1992-1-1:2004; confirm them against the edition in the design basis and the code registry (EN 1992-1-1:2023 numbering differs).
- **Gate:** the benchmark floor (PJR-2F-PT recommended) runs end to end with every check result recorded; the engineer signs off the benchmark table.

### M6 - Deliverables wired to the design data
- Feed `pt_plan.py`, `pt_profiles.py`, `build_sheets.py` and the reinforcement sheets from M3-M5 outputs instead of hand-made JSON.
- Calc report sections (v1 Part 13) generated from `CheckResult` records; workbooks for each new check; tendon/anchorage and bar schedules from the same objects as the drawings.
- Specification sections for PT materials, stressing and grouting from the approved templates (v1 Part 14); supplier requirements only from supplied documents.
- Extend `04_tools/qa/package_qa.py`: drawing values against calc values against schedules.
- Everything is generated as DRAFT. Sheet numbers come from the standards and the register.
- **Gate:** package QA passes on the benchmark floor; the engineer reviews the draft package.

### M7 - Web application, database, roles, approval workflow
- **Early slice built 16-OCT-2026 at the user's request** (`webapp/`, local mockup): landing page, AI connection (key + model + test), projects, file import (DXF read, DWG converted with AutoCAD 2023 console, PDF view, DWF/DWFX stored), project assistant. Local SQLite/files instead of Supabase; no sign-in or roles yet. Mockup removed from the repo 24-OCT-2026 (recover from git history, commit 98caf82, `webapp/`).
- v1 Parts 16-18 on top of the proven core: project dashboard, workspace tabs, CAD review, results and checks screens, review and issue.
- Database schema from v1 Part 17, plus stale-result tracking and immutable input snapshots.
- Roles enforced on the server; approval is recorded only from a signed-in engineer with the Approver role.
- Claude orchestration (v1 Part 15) server-side, exposing only the implemented tools; uploaded CAD text is treated as untrusted. SAFE stays on the engineer's PC (ADR-012).
- **Gate:** security review; end-to-end run of the benchmark floor through the UI matches the CLI results exactly.

### Research track (optional, not blocking v1) - In-house FE solver
- Run only if ADR-002 is revisited with a documented reason (licensing, automation limits, cost).
- Evaluate libraries and licences first (v1 Part 8), then the full v1 Part 9 benchmark suite, before any design use.

## 5. Definition of done for v1 (controlled engineering beta)

v1 Part 22 applies, with step 1 read as "DXF" and step 6 as "build and run the model in SAFE 22 through the API (ADR-012), or import an engineer-built SAFE model's results, through the adapter".

## 6. Inputs needed from the user

| # | Needed for | Item |
|---|---|---|
| 1 | M1 | Structural layout DXF with columns and walls placed and sized: RECEIVED 25-OCT-2026 (`PJR-2026-004/inputs/str-layout/3F Floor.dxf`); answers to its open items OI-04, OI-05 |
| 2 | M0, M2 | National Annex decision per project, or confirmation that CEN recommended values apply (CEN confirmed 14-OCT-2026, gap G09) |
| 3 | M3 | Approved PT system data sheet / ETA (mu, k, draw-in, relaxation class, anchorage data) |
| 4 | M3, M5 | Hand calculations or verified reference results for benchmarks (or approval of agent-prepared ones after an engineer's check) |
| 5 | M2, M3 | Engineer review of the PT rulesets (G33, G34): sizing and tendon-layout rules must be ACCEPTED before the system uses them |
| 6 | M2 | EN 1990 partial and psi factors entered in the code registry by the engineer; loads, live-load patterning rule and strip method in the design basis |
| 7 | M4 | SAFE 22 licence available for API use on the PC that runs the system |
| 8 | M4 (second route) | One real SAFE/ETABS `.db` export with results included, and the software version (gap G16) |
| 9 | M7 | Container host provider for the API and workers (Supabase and Vercel are decided in ADR-008) |
| 10 | M0 | Internal base units for the core (ADR-007): DONE 25-OCT-2026, N, mm, MPa inside, kN in/out |

## 7. Instruction for an implementing agent

Work on one milestone at a time. Inspect the repo first and reuse what's listed in section 2. Run `python -m unittest discover -s tests` before and after each change. Stop at each gate and report actual test output, benchmark tables and open items. Never enter engineering values, clause numbers or PASS results that aren't sourced, and never mark anything APPROVED.
