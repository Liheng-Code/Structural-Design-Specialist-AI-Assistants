---
name: structural-calculation-report
description: Produce structural calculation reports (DOCX/PDF) and Excel calculation workbooks (XLSX) from verified scripts, Excel and ETABS/SAFE results, to Eurocode with the project design basis. Use for design checks, calculation notes, ETABS/SAFE result import, or reviewing calculation traceability.
---

# Structural Calculation Report

## Status
`10_Structural-Calculation-Reports/` has NOT been authored yet. Use `references/report-format.md` (PROPOSED) until it exists. The DOCX/PDF report generator and one tested calculation (`calc_lib/ec2_anchorage.py`) exist (Phase 4). Excel workbook generation (Phase 5) exists for the anchorage check; ETABS/SAFE table import exists (`tools/etabs/etabs_import.py`, Phase 7) but is tested only on a synthetic fixture and its export layout is unverified against a real file; manual work must still follow the integrity rules below.

## Non-negotiable integrity rules
- **Never fabricate** forces, displacements, material properties, load combinations, code clauses, or PASS results. Missing input -> stop that check and list it as an open item; do not substitute a plausible number.
- Every input has: symbol, value, unit, source (design basis id / ETABS export / user). Every result has: formula, substituted values, unit, code clause, utilisation, status.
- Use only the code parts and National Annex mode recorded in the design basis. If a required parameter is not in the available text (e.g. NA value), flag it.
- Separate **calc logic** (reusable functions in `calc-lib/`, with tests) from **report formatting**. Reports pull numbers from calc outputs; they are not retyped.
- Independently verify critical results (hand check, second method, or limiting-case test) and record the check; unverified formulas are labelled UNVERIFIED.
- Final conclusions say "satisfies the checks performed under the stated assumptions", never "structure is safe". PASS/FAIL derives from computed utilisation only.

## Workflow
1. Read design basis; run the validator; list unresolved items affecting these checks.
2. Read `references/report-format.md`, `references/data-contracts.md`, and (if ETABS/SAFE used) `references/etabs-safe-import.md`.
3. Gather inputs -> compute with tested functions in `calc_lib/` (add a run script like `calc_lib/runs/anchorage_check.py` that writes a results JSON, plus tests with hand values) -> write a content file -> `python tools/docgen/build_document.py <content.yaml> --design-basis <db.yaml> --out <dir> --results <results.json>` -> open and inspect every output page. Workbook: `python tools/xlsxgen/build_anchorage_workbook.py <inputs.yaml> --design-basis <db.yaml> --out <file.xlsx>` then `python tools/xlsxgen/verify_workbook.py <file.xlsx> --results <results.json>` (recalculates with LibreOffice, rejects formula errors, typed numbers/literals in Calc, failing hand checks, and report/workbook mismatches). New calculations need their own workbook builder following the same Inputs/Calc/Outputs/Checks/Log structure; never paste computed numbers as values.
3a. ETABS/SAFE results: `python tools/etabs/etabs_import.py <export.xlsx|csv> --out <analysis/<code>> --model-id <id> --model-file <name> --run-date <DD-MMM-YYYY> --members members.csv --expected expected_cases.yaml --hand-totals hand_totals.yaml`. Do NOT start any calculation unless `import_log.json` has `ready_for_calculations: true`; report every WARNING and every NOT CHECKED line to the user. Expected cases and combination factors come from the design basis; the hand total must be an independent take-down with a stated tolerance (the tool assumes none). `--assume-units` only if the user confirms the units. Import success is not evidence the model is correct.
4. Reconcile: values on drawings/specification vs report (e.g. general-note result summary vs report). Hand to `structural-document-qa`.
5. Engineering review sign-off is a human step.
