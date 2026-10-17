# Steel structures - design workflow

Status: DRAFT (17-OCT-2026), written by Claude as a working outline. Not an approved standard. Contains no design values: every number comes from the project design basis, the code registry or the engineer.

## 1. Standards family
The design basis (`standards[]`) records the editions and National Annex actually used. The usual family is:

| Topic | Standard |
|---|---|
| Basis of design, combinations | EN 1990 |
| Actions (self-weight, imposed, wind, snow, thermal, execution) | EN 1991 parts |
| General rules and rules for buildings | EN 1993-1-1 |
| Fire design | EN 1993-1-2 |
| Cold-formed members and sheeting | EN 1993-1-3 |
| Plated structural elements | EN 1993-1-5 |
| Design of joints | EN 1993-1-8 |
| Fatigue | EN 1993-1-9 |
| Material toughness and through-thickness properties | EN 1993-1-10 |
| Composite steel-concrete (if used) | EN 1994-1-1 |
| Execution of steel structures | EN 1090-2 |
| Hot-rolled structural steel products | EN 10025 parts |
| Seismic (if required) | EN 1998-1 |

Do not quote clause numbers, factors or limits from memory. Cite only what the code registry or the engineer supplies.

## 2. Inputs needed before any check
1. Design basis: project code, stage, revision, standards and National Annex stance, consequence class, design working life.
2. Steel grade and product standard per member type; execution class (EN 1090-2); bolt and weld specifications.
3. Loads and load combinations, or an analysis model export (ETABS/SAFE/other) with its units and sign convention.
4. Restraint and bracing arrangement, effective lengths basis, frame stability approach (sway / non-sway, imperfections).
5. Fire resistance period, corrosion protection system and durability requirements.

If any of these is missing, list it and stop; do not assume.

## 3. Design sequence
1. Stability system: identify bracing, moment frames, diaphragms.
2. Analysis: global analysis method and imperfections per the design basis; import results with `tools/etabs/`.
3. Members: cross-section classification, cross-section resistance, member buckling (flexural, lateral-torsional), combined actions.
4. Serviceability: deflections and vibration against limits recorded in the design basis.
5. Connections: bolts, welds, end plates, splices, base plates and holding-down bolts.
6. Fire and corrosion: protection system consistent with the basis.
7. Documentation: general arrangement, member schedules, connection details, steel general notes, calculation report.

## 4. Deliverables and which shared skill produces them
| Deliverable | Skill |
|---|---|
| GA plans, elevations, connection details | `structural-drawing` |
| Steelwork specification (materials, fabrication, erection, inspection) | `structural-specification` |
| Calculation report and workbook | `structural-calculation-report` |
| Package consistency check | `structural-document-qa` |

## 5. Open items (gap G27)
- No steel drawing standard (layers, member marks, connection detail library, general notes).
- No EN 1993 code-registry file.
- No calculation modules in `calc_lib/steel/`.
- No worked example.
