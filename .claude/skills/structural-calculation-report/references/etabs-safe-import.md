# ETABS / SAFE result import

Supported route (Phase 7, `04_tools/etabs/etabs_import.py`): ETABS/SAFE "Export tables to Excel/CSV" files. Direct API use only after the installed version and API are verified on the user's machine (not yet checked).

## Steps
1. Record provenance: software + version, model file name and modified date, units in the export, analysis run date, who exported.
2. Parse tables (e.g. Frame Forces, Joint Reactions, Story Drifts, Load Combinations). Preserve units; convert only with explicit factor logged.
3. **Completeness/mapping check before any calculation:** every expected load case/combination present; every member id maps to a `member` row and drawing ref; no empty stations; units consistent; combination definitions agree with design basis (e.g. EN 1990 6.10 factors).
4. Record unsupported/missing fields in an import log. Do not fill gaps.
5. Sanity-check results independently (global equilibrium: sum of reactions vs applied load; spot hand calc). **A successful import is not evidence the model is correct** - report the equilibrium check result and flag modelling assumptions.
6. Store imported tables unchanged under `analysis/<code>/raw/`; derived tables separate.

## Route chosen by the user: SQLite `.db` export (04_tools/etabs/etabs_db_import.py)
Run: `python 04_tools/etabs/etabs_db_import.py <model.db> --out analysis/<code> --model-id <id> [--members members.csv] [--expected expected_cases.yaml] [--design-basis db.yaml]`.
Seen in one real file (ETABS 22.1.0): tables named like ETABS database tables + `_ModelInfo` (ModelFile, DataUnits, IncludesResults, ExportedAt) + `_Tables` (per-table status). That file has `IncludesResults = No`: it is a MODEL DEFINITION, so there are no reactions/forces and the equilibrium/superposition checks cannot run; `ready_for_calculations` is always false for it. Units are read from `DataUnits` (N_mm_C -> lengths to m); a different `Program_Control.CurrUnits` is warned, not assumed. Checks M1-M11: metadata, units, results present, exporter table status, referential integrity (sections, materials, joints, load names, stories), duplicates, supports, expected cases and combination factors, member mapping, model design codes vs design basis. Results-table layout of this exporter is unknown - never guess it; ask for a file with IncludesResults = Yes. SAFE .db files have not been seen. The source .db is opened read-only and copied unchanged with SHA-256.

## Tool: 04_tools/etabs/etabs_import.py
Run: `python 04_tools/etabs/etabs_import.py <export> --out <dir> --model-id <id> [--model-file --run-date --software --members --expected --hand-totals --assume-units]`.
Writes `raw/` (unchanged copies + SHA-256), `analysis_results.csv`, `joint_reactions.csv`, `base_reactions.csv` (kN, m), `import_log.json`, `import_report.md`, and `analysis_provenance.proposed.yaml` (proposal only; never applied to the design basis automatically).

**Assumed export layout (UNVERIFIED against a real file):** each sheet / CSV block = row 1 `TABLE:  <name>`, row 2 column headers, row 3 units, then data. Supported tables: Joint Reactions, Base Reactions, Element Forces - Columns/Beams/Braces/Frames, Load Combinations, Program Control. Anything else is reported as UNSUPPORTED and not imported. A real ETABS/SAFE version may name tables or columns differently; the importer then rejects or reports - it never guesses.

| Check | Meaning | Needs |
|---|---|---|
| C1 | expected cases/combinations present | expected_cases.yaml |
| C2 | combination factors equal expected | expected_cases.yaml |
| C3 / C3b | exported members map to project members / members without results | members.csv (`etabs_label` column) |
| C4 | no duplicate (case, member, station) rows | - |
| C5 | combination joint reactions = factor-weighted sum of cases (linear combos only) | expected_cases.yaml |
| C6 | sum of joint-reaction FZ = base-reaction FZ (internal consistency only) | both tables |
| C7 | sum of reactions = independent hand total | hand_totals.yaml with `tolerance_pct` (none is assumed) |
| C8 | units read, recognised, converted; ASSUMED units give a WARNING | - |

Limits: C5/C6 prove internal consistency, not that the model is right. Non-linear combinations, envelopes, response-spectrum and time-history results, SAFE slab/strip tables and mapping to drawing references are NOT handled. FAIL on any check or table blocks `ready_for_calculations`.
