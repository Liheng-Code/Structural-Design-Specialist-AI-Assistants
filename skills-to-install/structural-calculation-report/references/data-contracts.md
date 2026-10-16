# Data contracts (column sets; CSV/XLSX/JSON must use these names)

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

## Excel workbooks
Sheets: `Inputs` (units, validation, source), `Calc` (formulas only, no hard-coded numbers), `Outputs`, `Checks` (representative cases verified against independent calculation, with date/tester), `Log`. Status is formula-driven: CHECKS FAILING / UNVERIFIED (inputs differ from checked baseline) / CROSS-CHECKED - NOT ENGINEER-REVIEWED / REVIEWED BY <name>. No workbook is called VALIDATED. Hand-calculated expected values live on `Checks`; they apply only to the baseline inputs and show N/A otherwise. Report values cite sheet+cell.
