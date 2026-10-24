# ADR-004 - Versioned design-code registry

Status: ACCEPTED (user, 16-OCT-2026)

## Context
v1 Part 4 requires code factors and parameters to be held in reviewed, versioned configuration, never scattered through calculation code, and forbids fabricated clauses. CLAUDE.md requires CEN recommended values unless the design basis records a National Annex.

## Decision
- Registry files live in `04_tools/code_registry/` (YAML), one file per standard edition, with an optional overlay per National Annex.
- Each entry records: parameter id, standard, edition/amendment, NA (or "CEN recommended"), value with unit, source reference (clause/table number only), verification status (`UNVERIFIED`, or `VERIFIED` with verifier and date), effective date, and registry version.
- Values are entered or confirmed by an engineer. An agent may draft entries only as `UNVERIFIED`.
- A calculation that uses an `UNVERIFIED` value, or finds a value missing, reports `NOT EVALUATED` with the parameter named. It never falls back to a default.
- Every calculation run stores the registry version it used.
- No clause text is stored, only references, to respect standards licensing.

## Consequences
- The registry has to be populated and verified before checks can report PASS. That is intended.
- Changing a registry value marks dependent results stale (stale tracking, ADR-008).
