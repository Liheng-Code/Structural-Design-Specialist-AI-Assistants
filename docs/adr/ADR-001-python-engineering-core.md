# ADR-001 - Python engineering core

Status: ACCEPTED (user, 16-OCT-2026)

## Context
The v1 plan asked for a Next.js/TypeScript application with "strict TypeScript" (v1 Part 21 rule 3) while also requiring existing conventions to be preserved (v1 Part 2). The repo is Python: `tools/cadgen`, `tools/docgen`, `tools/xlsxgen`, `tools/qa`, `tools/etabs`, `calc_lib/`, with a unittest suite. The libraries the calculations and deliverables need (numpy, scipy, ezdxf, python-docx, openpyxl) have no equivalent of the same maturity in TypeScript.

## Decision
- All engineering calculations, adapters and document generators are Python.
- Calculation modules are pure functions: structured inputs with units, structured outputs, no file or network I/O.
- Core code is typed (type hints, Pydantic models or dataclasses) and checked with mypy (ADR-011).
- TypeScript is used only in the front end (ADR-009), with types generated from the API schema (ADR-005).
- v1 Part 21 rule 3 is read as: "typed Python in the core; strict TypeScript in the front end".
- Python 3.9+ remains the minimum until M6; raise it then only if a dependency requires it.

## Consequences
- Existing tools and tests are reused without rewriting.
- The CLI (Claude Code + skills) and the web worker run the same core code, so results don't depend on which interface was used.
- Front-end code can't call calculation code directly; everything goes through the API.
