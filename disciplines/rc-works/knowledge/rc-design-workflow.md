# Reinforced concrete works - design workflow

Status: DRAFT (17-OCT-2026), written by Claude as a working outline. Not an approved standard. Contains no design values: every number comes from the project design basis, the code registry or the engineer.

## 1. Standards family
The design basis (`standards[]`) records the editions and National Annex actually used. The usual family is:

| Topic | Standard |
|---|---|
| Basis of design, combinations | EN 1990 |
| Actions | EN 1991 parts |
| Concrete structures - general rules and rules for buildings | EN 1992-1-1 |
| Structural fire design | EN 1992-1-2 |
| Foundations / geotechnical | EN 1997-1 |
| Seismic (if required) | EN 1998-1 |
| Concrete specification, performance, production, conformity | EN 206 |
| Execution of concrete structures | EN 13670 |
| Weldable reinforcing steel | EN 10080 |

Do not quote clause numbers, factors or limits from memory. Cite only what the code registry or the engineer supplies.

## 2. Inputs needed before any check
1. Design basis: project code, stage, revision, standards and National Annex stance, design working life, consequence class.
2. Concrete strength class and exposure class per element; nominal cover basis; reinforcement grade and ductility class.
3. Loads and combinations, or an analysis export (ETABS/SAFE) with units and sign convention.
4. Fire resistance period; crack width limits; deflection limits.
5. Geotechnical data for foundations (from the geotechnical report, never assumed).

If any of these is missing, list it and stop; do not assume.

## 3. Design sequence
1. Durability and cover from exposure class (values from the basis/registry).
2. Analysis results import (`tools/etabs/`), checked for completeness and equilibrium.
3. ULS: flexure, shear, torsion, punching, axial + bending for columns and walls.
4. SLS: stress limits, crack control, deflection.
5. Detailing: anchorage and laps (`calc_lib/rc/ec2_anchorage.py`), minimum and maximum reinforcement, spacing, curtailment.
6. Documentation: general notes, layouts, reinforcement details, bar schedules, calculation report.

## 4. Deliverables and which shared skill produces them
| Deliverable | Skill |
|---|---|
| General notes, layouts, reinforcement details | `structural-drawing` |
| Concrete and reinforcement specification | `structural-specification` |
| Calculation report and workbook | `structural-calculation-report` |
| Package consistency check | `structural-document-qa` |

## 5. Open items (gap G28)
- Only the anchorage/lap check is built.
- EN 1992-1-1 registry values are all null and UNVERIFIED.
- No approved bar-schedule format.
