# ADR-011 - Quality gates

Status: ACCEPTED (user, 16-OCT-2026)

## Decision
- Keep the existing unittest suite (`python -m unittest discover -s tests`); new modules add tests in the same style.
- Benchmark register (from M2): each benchmark records the reference model, reference result, units, assumptions, tolerance and its justification, owner and verification status (v1 Part 9). Tolerances are set per quantity, not globally.
- mypy and ruff run on the core from M0.
- CI (GitHub Actions) runs tests and benchmarks on every merge once the repo has a remote.
- Each milestone ends at an engineer review gate (Development Plan v2 §4). Passing tests is necessary but not sufficient.

## Consequences
- A change to the analysis adapter, a calculation module or the registry re-runs the benchmarks that depend on it.
