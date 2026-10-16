# Document control

## Identifiers
| Item | Format | Example | Source of truth |
|---|---|---|---|
| Project code | `PJR-YYYY-NNN` | PJR-2026-003 | design basis `project.code` |
| Drawing number | `<prefix>-STR-<TYPE>-<NNN>` | WH-STR-SD-101 | register |
| Revision | `R00` issued, `P01` preliminary, `C01` construction | R00 | design basis / register |
| Date | `DD-MMM-YYYY` upper case | 13-OCT-2026 | design basis `issue_date` |

Confirmed 14-Oct-2026: project codes use `PJR-`. The issued R00 drawings show `PRJ-2026-003` and must be corrected at next revision. Open: how the 2-letter site code (`WH`, `OF`) is assigned.

## States
`DRAFT` -> `FOR_REVIEW` -> `APPROVED` (design basis); drawings carry a stage (`FOR APPROVAL`, `SHOP DRAWING`, `PRELIMINARY PT DESIGN`...).

## Rules
1. Claude may set DRAFT or FOR_REVIEW. **APPROVED needs a named authorised engineer (PE/RE) and date entered by the user**; Claude never fills `approved_by`.
2. A revision bump changes: design basis `revision`/`issue_date`, every affected register row, title blocks, drawing list, and revision history files - all in one change.
3. Superseded files move to `99_Archive/`; never overwrite an issued revision.
4. An issued package must have: design-basis validator = 0 errors, register check = 0 errors, QA issue register with no open Critical/Major items.

## Drawing prefix / site code (user decision 14-OCT-2026)
Drawing number = `<SS>-STR-<TYPE>-<NNN>`; the two-letter site code SS is the first two letters of the drawing prefix and identifies the site/building type (e.g. WH = warehouse). It is chosen per project and recorded once in the design basis `project.drawing_prefix`. Project code prefix is `PJR-`.
