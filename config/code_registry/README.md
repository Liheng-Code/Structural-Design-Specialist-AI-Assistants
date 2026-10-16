# Design-code registry

Decision: [ADR-004](../../docs/adr/ADR-004-design-code-registry.md). Loader: `calc_lib/core/registry.py`.

Holds every code-dependent parameter the calculations use: partial factors, coefficients and limits. Calculation code never hard-codes them.

## Files

One YAML file per standard edition and National Annex choice:

- `<standard>_<edition>_CEN.yaml`: CEN recommended values. This is the full parameter list for that edition.
- `<standard>_<edition>_NA-<country>.yaml`: a National Annex overlay. It may only contain parameters that exist in the CEN file.

The project's design basis selects the file: `standards[].edition` and `national_annex.mode` / `national_annex.country`. If the mode is `UNRESOLVED` or the edition is missing, every check that needs the registry reports NOT EVALUATED.

## File format

```yaml
file_version: 1                 # increase on every change to this file
standard: EN 1992-1-1
edition: "2004"                 # as written in the design basis standards[].edition
national_annex: CEN_RECOMMENDED # or NA
country: null                   # NA files only
na_reference: null              # NA files only: exact NA document reference
effective_date: null
parameters:
  gamma_c.persistent:
    description: Partial factor for concrete, persistent and transient design situations
    kind: dimensionless         # a kind from calc_lib/core/units.py INTERNAL_UNITS
    unit: dimensionless
    value: null
    ndp: true                   # nationally determined parameter
    source_ref: Table 2.1N      # clause / table / equation number only, never clause text
    status: UNVERIFIED          # UNVERIFIED | VERIFIED
    verified_by: null           # required when VERIFIED
    verified_date: null         # required when VERIFIED (YYYY-MM-DD)
    note: null
```

## Rules

- An agent may add parameter IDs and draft entries, but only as `UNVERIFIED`. Only an engineer sets `VERIFIED`, together with `verified_by` and `verified_date`.
- A check that needs an `UNVERIFIED` or empty value reports NOT EVALUATED and names the parameter. There are no defaults.
- Under a National Annex, a parameter with `ndp: true` must be in the NA file. It never falls back to the CEN value.
- Every calculation run records the registry version string (file versions plus a content hash).
- Store references only. Don't copy clause text from the standards (licensing).
