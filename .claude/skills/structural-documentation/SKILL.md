---
name: structural-documentation
description: Coordinator for structural document packages (drawings, specification, calculation report, workbooks). Use first when a project needs more than one deliverable, when starting a new project, or when asked to issue/revise a package. Reads the design basis, picks the production skills, tracks the document register and keeps identifiers and revisions consistent.
---

# Structural Documentation Coordinator

You coordinate; the other skills produce. Never produce a deliverable here that a production skill owns.

## Workflow
1. **Locate the project design basis** in `03_projects/<PROJECT-CODE>/design-basis.yaml`. If none exists, copy `03_projects/_template/design-basis.yaml`, fill only what the user has stated, leave the rest `null`, and tell the user what is missing. Do not guess codes, editions, National Annex, loads or materials.
2. **Validate it:** `python 04_tools/design_basis/validate_design_basis.py 03_projects/<PROJECT-CODE>/design-basis.yaml`. Report ERRORs (block approval/issue) and WARNINGs (unresolved items) in plain language.
3. **Identify the discipline** and load its entry skill for the design rules: `pt-floor-design` (bonded PT floors), `steel-design` (steel structures) or `rc-design` (reinforced concrete works). See `02_disciplines/README.md`. A package can span several disciplines; each keeps its own rules, all share one design basis and register.
4. **Choose skills** from `references/deliverable-matrix.md` for what was asked. Do not generate documents that were not requested.
5. **Maintain the document register** (`03_projects/<code>/document-register.csv`) and check it: `python 04_tools/doc_control/check_register.py <register.csv> --design-basis <design-basis.yaml>`.
6. **Hand off** to the production skill with: project code, drawing prefix, stage, revision, issue date, and the open items affecting that deliverable.
7. **Before any issue**, run `structural-document-qa`. Final issue requires authorised engineering review (see `references/document-control.md`). You may prepare "FOR REVIEW" packages; you may not mark anything APPROVED yourself.

## Rules
- Company standards live in `01_standards/` and are authoritative. Read them; do not copy them into skills.
- Check each standard's header status. Files marked **PROPOSED** (e.g. report and specification formats) are working conventions derived from a real drawing set, not approved standards: follow them, but say so in the report. Standards 01-04 and layers 05-04a/05-04b are approved by the user (14-OCT-2026).
- Any standard the library lacks goes into `01_standards/00-gap-register.md` as an open gap rather than being invented.
- Identifiers (project code, prefix, revision, date, stage) come from the design basis only. Never retype them from memory.
- Never claim a phase, check or file is complete unless it was actually run/opened. State what was not verified.

References: `references/deliverable-matrix.md`, `references/document-control.md`.
