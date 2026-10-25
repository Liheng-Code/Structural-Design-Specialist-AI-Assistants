# ADR-007 - pint for unit handling

Status: ACCEPTED (user, 16-OCT-2026). Internal base units: DECIDED (user, 25-OCT-2026), see below.

## Context
v1 Part 6 requires internal normalisation of units and dimensional validation. The existing ETABS importer normalises to kN and m with conversion tables of its own.

## Decision
- Quantities crossing a module boundary carry units, using pint.
- Each calculation module converts its inputs to its declared internal units on entry and returns quantities with units. Dimension mismatches raise an error and are never coerced.
- Plain floats are allowed only inside a module's own arithmetic, after conversion.
- Reports and drawings format units through one shared formatter, so the same quantity always prints the same way.

## Sub-decision: internal base units (decided by the user 25-OCT-2026)
- Internal units of the core: N, mm and MPa (N/mm²), as in `INTERNAL_UNITS` in `04_tools/calc_lib/core/units.py`. This set is consistent (force / area gives stress with no factor), which a mixed set is not: kN with mm and MPa gives kN/mm² = 1000 MPa.
- Input and output: forces in kN and moments in kN·m. Inputs carry their unit and are converted on entry; reports and drawings convert back through the shared formatter.
- Analysis adapter boundary: kN and m, converted on import.
- The user first asked for kN, mm, MPa; the inconsistency was explained and the user chose N, mm, MPa inside with kN in and out.

## Consequences
- Adds pint as a core dependency.
- The `04_tools/etabs/` conversion tables either stay as the adapter's edge conversion or are replaced by pint; either way their tests must still pass.
