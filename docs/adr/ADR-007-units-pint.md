# ADR-007 - pint for unit handling

Status: ACCEPTED (user, 16-OCT-2026). Internal base units: OPEN.

## Context
v1 Part 6 requires internal normalisation of units and dimensional validation. The existing ETABS importer normalises to kN and m with conversion tables of its own.

## Decision
- Quantities crossing a module boundary carry units, using pint.
- Each calculation module converts its inputs to its declared internal units on entry and returns quantities with units. Dimension mismatches raise an error and are never coerced.
- Plain floats are allowed only inside a module's own arithmetic, after conversion.
- Reports and drawings format units through one shared formatter, so the same quantity always prints the same way.

## Open sub-decision
Internal base units for the core. Recommendation: N, mm and MPa (N/mm²) for section and stress calculations, matching EN 1992-1-1 practice; kN and m at the analysis adapter boundary, converted on import. To be confirmed by the user before M0 closes.

## Consequences
- Adds pint as a core dependency.
- The `tools/etabs/` conversion tables either stay as the adapter's edge conversion or are replaced by pint; either way their tests must still pass.
