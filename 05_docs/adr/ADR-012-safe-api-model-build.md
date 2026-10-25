# ADR-012 - System builds and runs the SAFE 22 model through the local CSI API

Status: ACCEPTED (user, 25-OCT-2026). Amends ADR-002.

## Context
ADR-002 made SAFE/ETABS the analysis engine and started from tables exported from a model the engineer built by hand. It left local automation through the CSI API as "a separate decision". On 25-OCT-2026 the user set a different workflow: the engineer sends the architect drawing (DXF) and the system proposes element sizes, loading, load cases, load patterns, load combinations, support lines, strips and tendons, then builds the model for analysis. SAFE 22 is installed on the user's PC (probe 14-OCT-2026, gap G20); its API has not been tried. The user chose SAFE 22 over ADAPT-Builder INP export.

## Decision
- The system builds the SAFE 22 model from the reviewed data of gates A-C (Development Plan v2, M1-M3) through the CSI OAPI on the engineer's PC, runs the analysis and reads the results back into `AnalysisResults`.
- The adapter boundary of ADR-002 stays: design code reads results only through `AnalysisResults`, with the same completeness, units, equilibrium and provenance checks.
- Every API call and the SAFE object IDs it creates are logged with the input snapshot and SHA-256, so a generated model can be traced and rebuilt.
- The engineer reviews the inputs at gates A-C and the generated model at gate D (opens it in SAFE). The system builds the model; the engineer remains responsible for it.
- Each run writes a new SAFE file; the system never edits an engineer's own model.
- SAFE and its licence stay on the engineer's PC. Driving SAFE from the cloud remains out of scope (ADR-002).
- Importing an engineer-built model's results (ADR-002 adapter 1) stays as a second route for checking existing designs.
- ADAPT-Builder INP export is not pursued now; it can be added later as another writer from the same reviewed data.

## Consequences
- Milestones re-sequenced: CAD import first (M1), model proposal (M2, M3), SAFE build and run (M4); see Development Plan v2 §4.
- M4 starts with an API probe on the user's PC (version, licence, one-panel test model). If the API cannot be driven reliably, this ADR is revisited before building further.
- Adds `comtypes` (Windows only) as a dependency of the SAFE writer; the engineering core stays platform-independent.
- The design loop (M5) can re-run SAFE without manual steps, which ADR-002 had expected to be manual.
