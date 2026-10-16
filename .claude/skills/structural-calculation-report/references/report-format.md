# Calculation report format - PROPOSED, pending approval of `10_Structural-Calculation-Reports/`

Cover/control block: project code, name, report number `<prefix>-CR-<NNN>`, revision, date `DD-MMM-YYYY`, stage, prepared/checked/approved (human-completed), design-basis revision.

Sections (lettered, matching drawing general notes):
A. Scope & structure description  B. Design codes & National Annex (from design basis)  C. Materials  D. Design basis & actions (loads with sources)  E. Load combinations  F. Analysis model & provenance (software, version, model file, run date, export files)  G. Member / foundation checks (one sub-section each)  H. Results summary table (member, check, demand, capacity, utilisation, status)  I. Assumptions to be confirmed & limitations  J. Appendices (workbook references, ETABS tables)

## Each check block
`Inputs` (table: symbol, value, unit, source) -> `Formula` (Eurocode notation, clause) -> `Substitution` -> `Result` -> `Utilisation = Ed / Rd` -> `Status`. Units on every line; no unit-less numbers.

## Results summary
Numbers must equal calc output. Status values: OK (util <= 1.00), NOT OK, NOT CHECKED (missing input), UNVERIFIED (method not independently checked).
