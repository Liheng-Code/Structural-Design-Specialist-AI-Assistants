# Development Plan v2 - Bonded PT Band Beam & Slab Designer

Status: PROPOSED (16-OCT-2026). Architecture decisions in §3 ACCEPTED by the user (16-OCT-2026). No engineering approval.
Supersedes the *structure and sequencing* of Development Plan v1 (file removed 24-OCT-2026; recover it from git history, commit 98caf82, `docs/Development Plan.md`). The engineering requirements in v1 still apply where this document cites them (for example "v1 Part 10.4").
Architecture: [Architecture v2.md](Architecture%20v2.md).

---

## 1. Why v1 is being revised

| v1 assumption | Reality in this repo | Consequence |
|---|---|---|
| Next.js / TypeScript / Supabase web app (Parts 17, 21) | Python CLI tools, Claude Code skills and YAML project data; no web stack, database or auth | v1 contradicts itself ("preserve existing conventions" and "use strict TypeScript"). Decided in ADR-001 below |
| Build from CAD import forwards (M1 CAD, M4 FEA, M7 drawings) | Deliverable side already exists: DXF sheets, PT plan/profile sheets, DOCX/PDF, XLSX, package QA, ETABS/SAFE import | v1 order delays the parts that already work and front-loads the riskiest |
| In-house verified plate/shell FEA with PT is one milestone (M4) | This is a multi-year specialist product (comparable to RAM Concept, ADAPT, SAFE) | Moved to an optional research track behind the analysis adapter |
| "Continue milestone by milestone, do not stop" | Engineering milestones need an engineer to accept benchmarks before the next one starts | Each milestone ends at a review gate |
| Drawing register PT-001...PT-502 | Sheet numbering is set by `Structural-Drawing-Standards/03_Drawing-Index` (example set uses `WH-STR-SD-xxx`) | Numbering comes from the standards and the document register, never from the plan |

Unchanged from v1 and binding on every milestone: v1 Part 1 "Fundamental engineering principle", Part 3 scope limits, Part 4 code registry rules, Part 9 benchmark rules, Part 15 Claude operating rules, Part 16 status categories, Part 21 coding rules (except rule 3, see ADR-001), and the repo `CLAUDE.md`.

## 2. What already exists (reuse, do not rebuild)

| Capability | Location | State |
|---|---|---|
| Project design basis (single source) | `design-basis/PROJECT_TEMPLATE.yaml`, `tools/design_basis/validate_design_basis.py` | Built, tested |
| Bonded PT basis | `design-basis/PT_BASIS_TEMPLATE.yaml`, `tools/cadgen/validate_pt_basis.py` | Built; example `design-basis/examples/PJR-2F-PT/` |
| Document register control | `tools/doc_control/check_register.py` | Built, tested |
| DXF sheets + preview PDF | `tools/cadgen/build_sheets.py`, `build_notes_and_details.py`, `validate_dxf.py` | Cover, list, notes/details built. Not DWG, not a CTB plot |
| PT tendon plan + profile sheets | `tools/cadgen/pt_plan.py`, `pt_profiles.py`, `pt_notes.py` | Draws what the data gives; computes nothing |
| DXF plan to PT data | `disciplines/pt-floor/examples/2F-PT/redraft/convert_plan_to_pt_data.py` | Project-specific prototype |
| Calc report + spec DOCX/PDF | `tools/docgen/build_document.py` | Built; one calculation (EC2 anchorage) |
| Calculation library | `calc_lib/rc/ec2_anchorage.py` | One check |
| Excel workbooks | `tools/xlsxgen/` | Anchorage workbook only |
| ETABS/SAFE result import | `tools/etabs/etabs_import.py`, `etabs_db_import.py` | Built; tested on a SYNTHETIC export only |
| Package QA | `tools/qa/package_qa.py` | Consistency gate, not engineering correctness |
| Skills | `.claude/skills/` (incl. `structural-pt-drawing`) | Instruction level |

## 3. Architecture decisions

Recorded in [docs/adr/](adr/README.md). The full records take precedence over these summaries. All were accepted by the user on 16-OCT-2026 as software decisions; none is an engineering approval.

| ADR | Decision | Open items |
|---|---|---|
| [001](adr/ADR-001-python-engineering-core.md) | Python engineering core (pure, typed, mypy-checked); TypeScript only in the front end. Replaces v1 Part 21 rule 3 | - |
| [002](adr/ADR-002-analysis-adapter-safe-etabs.md) | Analysis through an adapter; SAFE/ETABS import first; in-house FE solver is an optional research track | Real SAFE export (§6 input 1) |
| [003](adr/ADR-003-yaml-design-basis-source.md) | YAML design basis + PT basis are the source of truth until M6; the database round-trips the same schema | - |
| [004](adr/ADR-004-design-code-registry.md) | Versioned registry in `config/code_registry/`; `UNVERIFIED` values give NOT EVALUATED; references only, no clause text | NA decision (§6 input 2) |
| [005](adr/ADR-005-api-fastapi.md) | FastAPI; Pydantic models shared with Claude tool schemas; OpenAPI generates the front-end types | - |
| [006](adr/ADR-006-job-queue-redis-rq.md) | Redis + RQ background jobs, run in a Linux container | - |
| [007](adr/ADR-007-units-pint.md) | pint at every module boundary | Internal base units (recommended N, mm, MPa) |
| [008](adr/ADR-008-hosting-and-data.md) | Supabase Postgres, Storage and Auth with row-level security; Vercel for the front end; API and workers on a container host | Container host provider (§6 input 6) |
| [009](adr/ADR-009-front-end.md) | Next.js + strict TypeScript + Tailwind; no calculation logic in the browser | dxf-viewer and Plotly.js to be evaluated |
| [010](adr/ADR-010-claude-tool-layer.md) | Claude server-side only, through schema-validated tools; read-only on check results; no approval or issue tools | - |
| [011](adr/ADR-011-quality-gates.md) | unittest + benchmark register + mypy + ruff; CI once a remote exists; engineer gate per milestone | - |

## 4. Milestones

Each milestone ends at a **review gate**: tests pass, benchmark results are tabled, open items are listed, and the engineer accepts or returns it. An agent does not start the next milestone without that acceptance.

### M0 - Foundations (small)
- ADRs: done ([docs/adr/](adr/README.md)). Close the ADR-007 base-units decision with the user.
- Create the code registry skeleton and loader (ADR-004); no values entered by the agent.
- Define the shared data schemas as Pydantic models (ADR-001, ADR-005): `GeometryModel`, `AnalysisResults`, `Tendon`, `LossResult`, `CheckResult` (status, inputs, value, limit, method reference, trace), `ReinforcementGroup` (fields from v1 Part 11).
- Add the pint units layer with dimensional checks (ADR-007).
- Add mypy and ruff configuration for the core (ADR-011).
- **Gate:** schemas reviewed; existing test suite still passes.
- **Status (16-OCT-2026):** built, awaiting the gate. `calc_lib/core/` (units, status, registry, schemas), `config/code_registry/` (skeleton: EN 1992-1-1:2004 CEN parameter IDs, all values empty and UNVERIFIED), `tests/test_core.py` (34 tests), `pyproject.toml` (mypy strict, ruff). Full suite: 202 tests, 1 failure that predates M0 (`test_pt.Notes`, PT notes sheet 1.3 mm past the border). Open: ADR-007 base units (N, mm, MPa used provisionally).

### M1 - Real analysis input (unblocks everything else)
- Get one real SAFE (or ETABS) PT-slab export from the user's software version. *The user must supply this.*
- Verify `tools/etabs/` against it; fix the format assumptions; extend it to strip/section forces and design-strip results if SAFE provides them.
- Map the results to `AnalysisResults` through the adapter, keeping SHA-256 provenance and the input snapshot.
- Checks: completeness, load-case mapping, global equilibrium against hand totals, units.
- **Gate:** import of the real model reproduces SAFE's own reaction totals within stated tolerances.

### M2 - PT calculation library (core engineering value)
Implement each as a separate module in `calc_lib/pt/`, each with hand-calculated benchmarks in `tests/` (v1 Part 9 fields: reference, units, assumptions, tolerance, owner, status):

1. Tendon geometry: parabolic profiles, high/low points, inflection points, cover, curvature, angle change.
2. Friction and wobble loss along the tendon (EN 1992-1-1:2004 5.10.5.2 form; mu and k from approved system data).
3. Anchorage draw-in and the affected length.
4. Elastic shortening (where stressing sequence makes it relevant).
5. Time-dependent losses: creep, shrinkage, relaxation (EN 1992-1-1:2004 5.10.6 and Annex B).
6. Equivalent prestress actions from profile and force, for export back to the analysis model.
7. Stress limits at stressing and at service.
8. SLS concrete stresses at transfer and service; decompression/crack checks as the design basis requires.
9. Deflection: short and long term, with the method and its limits stated.
10. ULS flexure with bonded tendon stress.
11. ULS shear (beam) and punching shear including the prestress contribution.
12. Anchorage-zone bursting and spalling (reuse and extend `calc_lib/rc/ec2_anchorage.py`).

Clause references above are to EN 1992-1-1:2004. Confirm them against the edition recorded in the design basis and the code registry; the 2nd-generation EN 1992-1-1:2023 numbering differs.

Rules: every parameter comes from the design basis, the PT basis, approved system data or the code registry; nothing is hard-coded. A missing input gives `NOT EVALUATED`, never a default.
- **Gate:** every module matches its benchmarks; the engineer signs off the benchmark table.

### M3 - Design loop and reinforcement
- Design-strip workflow following Architecture v2 diagram 3: trial sizing, tendon arrangement, losses, equivalent loads, re-analysis (export the load cases to SAFE, import the results), SLS, ULS.
- Iteration record, iteration limit, and a design-failed report (v1 Part 10.7).
- Conventional reinforcement (v1 Part 11): required areas, minimums, spacing, cover, laps, curtailment, punching reinforcement, trimming at openings.
- Clash checks: tendon against tendon, tendon against openings, tendon against bars and anchorages.
- **Gate:** one benchmark floor (PJR-2F-PT recommended) runs end to end, with every check result recorded.

### M4 - Deliverables wired to the design data
- Feed `pt_plan.py`, `pt_profiles.py`, `build_sheets.py` and the reinforcement sheets from M2/M3 outputs instead of hand-made JSON.
- Calc report sections (v1 Part 13) generated from `CheckResult` records; workbooks for each new check; tendon/anchorage and bar schedules from the same objects as the drawings.
- Specification sections for PT materials, stressing and grouting from the approved templates (v1 Part 14); supplier requirements only from supplied documents.
- Extend `tools/qa/package_qa.py`: drawing values against calc values against schedules.
- Everything is generated as DRAFT. Sheet numbers come from the standards and the register.
- **Gate:** package QA passes on the benchmark floor; the engineer reviews the draft package.

### M5 - CAD import and geometry review
- Generalise `disciplines/pt-floor/examples/2F-PT/redraft/convert_plan_to_pt_data.py` into a DXF importer following Architecture v2 diagram 2.
- DWG: support it only once a converter is installed and tested on the user's PC (see `probe_result.json` and the `convert_*_dwg.bat` scripts); otherwise ask for a DXF.
- Geometry validation (v1 Part 5, Module B); review/correction output saved as a checksummed snapshot.
- Output: a `GeometryModel` that can produce the SAFE model input or check it against the imported SAFE geometry.
- **Gate:** two real layouts import with all fatal errors caught and the corrected geometry reproducible.

### M6 - Web application, database, roles, approval workflow
- **Early slice built 16-OCT-2026 at the user's request** (`webapp/`, local mockup): landing page, AI connection (key + model + test), projects, file import (DXF read, DWG converted with AutoCAD 2023 console, PDF view, DWF/DWFX stored), project assistant. Local SQLite/files instead of Supabase; no sign-in or roles yet. Mockup removed from the repo 24-OCT-2026 (recover from git history, commit 98caf82, `webapp/`).
- v1 Parts 16-18 on top of the proven core: project dashboard, workspace tabs, CAD review, results and checks screens, review and issue.
- Database schema from v1 Part 17, plus stale-result tracking and immutable input snapshots.
- Roles enforced on the server; approval is recorded only from a signed-in engineer with the Approver role.
- Claude orchestration (v1 Part 15) server-side, exposing only the implemented tools; uploaded CAD text is treated as untrusted.
- **Gate:** security review; end-to-end run of the benchmark floor through the UI matches the CLI results exactly.

### Research track (optional, not blocking v1) - In-house FE solver
- Run only if ADR-002 is revisited with a documented reason (licensing, automation limits, cost).
- Evaluate libraries and licences first (v1 Part 8), then the full v1 Part 9 benchmark suite, before any design use.

## 5. Definition of done for v1 (controlled engineering beta)

v1 Part 22 applies, with step 6 read as "import or run a validated structural analysis through the adapter" and step 1 as "DXF, or DWG only where conversion has been tested".

## 6. Inputs needed from the user

| # | Needed for | Item |
|---|---|---|
| 1 | M1 | One real SAFE/ETABS PT model plus its exported tables (and the software version) |
| 2 | M0, M2 | National Annex decision per project, or confirmation that CEN recommended values apply |
| 3 | M2 | Approved PT system data sheet / ETA (mu, k, draw-in, relaxation class, anchorage data) |
| 4 | M2 | Hand calculations or verified reference results for benchmarks (or approval of agent-prepared ones after an engineer's check) |
| 5 | M5 | Whether an ODA File Converter or AutoCAD batch route is available on the production PC |
| 6 | M6 | Container host provider for the API and workers (Supabase and Vercel are decided in ADR-008) |
| 7 | M0 | Internal base units for the core (ADR-007; recommended N, mm, MPa) |

## 7. Instruction for an implementing agent

Work on one milestone at a time. Inspect the repo first and reuse what's listed in section 2. Run `python -m unittest discover -s tests` before and after each change. Stop at each gate and report actual test output, benchmark tables and open items. Never enter engineering values, clause numbers or PASS results that aren't sourced, and never mark anything APPROVED.
