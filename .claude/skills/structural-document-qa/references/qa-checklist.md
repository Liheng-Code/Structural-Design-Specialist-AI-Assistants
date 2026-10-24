# QA checklist

## A. Identity & control
- [ ] Project code, name, client identical on every document and equal to design basis
- [ ] Drawing numbers follow `<prefix>-STR-<TYPE>-<NNN>`, unique, listed in drawing list and register
- [ ] Revision/date/stage consistent; revision history updated; superseded files archived
- [ ] Title block fields complete; scale present (AS-SHOWN / N.T.S. / value)

## B. Design basis consistency
- [ ] Codes on notes sheet = design-basis `standards`; National Annex statement identical
- [ ] Materials (concrete class, exposure, steel grade, bolts, fyk) identical across notes, spec, calc report, drawings
- [ ] Loads and combinations identical; load values traceable to a source
- [ ] Results summary on notes sheet equals calculation report values
- [ ] "Assumptions to be confirmed" = open items; none silently dropped
- [ ] No mixing of Eurocode generations; editions stated

## C. Calculations
- [ ] Inputs with units/sources; formulas with clause references; no hard-coded numbers in workbook calc sheets
- [ ] PASS/OK only where utilisation computed; independent check recorded
- [ ] ETABS/SAFE provenance recorded, equilibrium check done

## D. Drawings
- [ ] Layers/text/lines per `05-drafting-styles`; text >= 2.0 mm; lineweights >= 0.18 mm
- [ ] Section/detail bubble references resolve to existing sheets
- [ ] File type claims honest (DXF vs DWG vs preview)

## E. Documents
- [ ] Heading numbers continuous; cross-references resolve; tables not truncated
- [ ] Placeholders (XXX, TBC, TBD) listed as open items
- [ ] All output files open and render; page counts match lists
