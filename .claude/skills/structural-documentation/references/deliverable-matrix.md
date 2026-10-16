# Deliverable matrix

| Request | Production skill | Output formats | Status of tooling |
|---|---|---|---|
| Drawing set / sheet / cover / drawing list / general notes | `structural-drawing` | DXF, DWG (only with native CAD), PDF | Phase 6: DXF + preview PDF built for sheets 001/002 only; no DWG |
| Technical specification | `structural-specification` | DOCX, PDF | Phase 4 generator built (`tools/docgen`); `07_*` standards not authored |
| Calculation report | `structural-calculation-report` | DOCX, PDF | Phase 4 generator built; only EN 1992 anchorage check implemented; `10_*` standards not authored |
| Calculation workbook | `structural-calculation-report` | XLSX | Phase 5 built for the anchorage check (`tools/xlsxgen`); other checks need their own builders |
| ETABS/SAFE results import | `structural-calculation-report` | CSV/XLSX table exports | `tools/etabs/etabs_import.py` (Phase 7; tested on synthetic data only, real export format unverified) |
| Consistency / readiness check | `structural-document-qa` | issue register CSV/MD | `tools/qa/package_qa.py` (Phase 8): cross-document consistency gate + issue register; consistency only, never an approval |

Until a phase is built, the skill still guides the work manually, but must say that automated generation/validation is unavailable.

## Typical package (as in WH-STR-SD R00)
Cover (001) -> Drawing list (002) -> General notes (003-007) -> Layouts and elevations (1xx) -> Reinforcement / connection details (2xx). Add specification and calculation report only when requested; all share the design-basis project code, stage and revision.
