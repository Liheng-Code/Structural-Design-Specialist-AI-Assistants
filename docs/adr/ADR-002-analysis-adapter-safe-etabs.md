# ADR-002 - Analysis through an adapter; SAFE/ETABS import first

Status: ACCEPTED (user, 16-OCT-2026)

## Context
v1 milestone M4 asked for an in-house, verified plate/shell FE solver with prestress, staged construction and long-term effects. That is a specialist product in its own right. The repo already has a SAFE/ETABS table importer (`tools/etabs/`) with unit normalisation, equilibrium checks and SHA-256 provenance, tested only on a synthetic export.

## Decision
- Design code reads analysis results only through an `AnalysisResults` schema behind an analysis adapter.
- Adapter 1 imports SAFE/ETABS exported tables, extended from `tools/etabs/`. It must be verified against a real export from the user's software version before any design module relies on it (M1 gate).
- Prestress equivalent loads calculated by `calc_lib/pt` are exported as load cases for the engineer to apply in SAFE/ETABS; results are re-imported for each iteration.
- The engineer owns and is responsible for the SAFE/ETABS model. The adapter checks completeness, load-case mapping, units, global equilibrium and provenance; it does not judge whether the model is correct.
- An in-house FE solver (adapter 2) is an optional research track. It starts only if this ADR is revisited with a documented reason, and must pass the full v1 Part 9 benchmark suite before design use.
- Driving SAFE/ETABS through the CSI API from the cloud is out of scope; licensed software stays on the engineer's PC.

## Consequences
- v1 does not depend on building an FE solver.
- Each design iteration includes a manual SAFE re-run, unless local automation through the CSI API is added later (a separate decision).
- Result schema changes need an adapter version bump and a re-run of the M1 tests.
