---
name: structural-document-qa
description: Quality-check a structural document package (drawings, specification, calculation report, workbook) against company standards and the project design basis, and produce a prioritised issue register. Use before any issue or revision, or when asked to review, audit or cross-check documents.
---

# Structural Document QA

You review; you do not silently fix. Output is an **issue register**, never an approval.

## Run
1. Automated, whole package: `python 04_tools/qa/package_qa.py <package_dir> --standards 01_standards [--out <dir>]` (package = `design-basis.yaml`, `document-register.csv`, `output/` with `<NUMBER>_<REV>.<ext>` files and `CALC-*.json`, optional `analysis/*/import_log.json`). It runs the design-basis validator, register check, identity/revision/status/DRAFT-stamp checks on DOCX/XLSX/DXF/PDF, placeholder scan, report-vs-results-vs-workbook number tie-out, inputs-vs-design-basis materials, DXF standards validation, workbook integrity, ETABS/SAFE import log and hash checks, and writes `issue-register.csv` + `qa_report.md`. Exit 1 = open Critical/Major. Individual tools: `04_tools/design_basis/validate_design_basis.py`, `04_tools/doc_control/check_register.py`. `python -m unittest discover -s tests` if code changed.
   The tool reports a CONSISTENCY gate only; issue readiness is always NOT READY until an authorised engineer approves. Copy its "Not checked / limits" list into your report. Findings that are Info/Minor are still listed; do not drop them.
2. Manual checks from `references/qa-checklist.md`: standards compliance, cross-document consistency (codes, materials, loads, member sizes, project code/revision/date/stage), unsupported claims, placeholders (XXX, TBC), revision mismatches, output-file integrity (open and render every file).
3. Record each finding in `issue-register.csv` using `references/issue-register-template.csv` columns.

## Severity
- **Critical** - wrong/unsafe or unsupported engineering claim, fabricated value, PASS without calc basis
- **Major** - inconsistency between documents, missing required standard element, unresolved National Annex/edition for an APPROVED basis
- **Minor** - formatting, numbering, style deviation
- **Info** - observation / open item already flagged

Every finding needs evidence (file, sheet/page, value seen) and corrective action. Review status values: Open, Fixed-awaiting-recheck, Closed (closed only after re-check), Accepted-by-engineer (name+date, human only).

## Gate
Recommend issue only if there are no open Critical/Major items. State "authorised engineering review required before final issue" in every report. Do not mark Accepted-by-engineer yourself.

Also state what you could not check (software missing, files absent).
