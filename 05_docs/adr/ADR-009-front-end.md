# ADR-009 - Front end: Next.js + TypeScript + Tailwind

Status: ACCEPTED (user, 16-OCT-2026). Applies from M6. Viewer and chart libraries: PROPOSED.

## Decision
- Next.js with React and strict TypeScript, styled with Tailwind CSS, hosted on Vercel (ADR-008).
- API types are generated from the FastAPI OpenAPI schema (ADR-005).
- No calculation logic in the front end. It displays stored results only and never shows a value the API didn't return.
- Status display uses the v1 Part 16 categories: PASS, FAIL, NOT EVALUATED, BLOCKED, WARNING, ENGINEER REVIEW REQUIRED. NOT EVALUATED is never styled like PASS.

## Proposed (evaluate before adopting)
- `dxf-viewer` (three.js based) for viewing DXF files and reviewing geometry in the browser. Check its licence, entity coverage and performance on large files.
- Plotly.js for moment, stress and deflection plots along design strips.

## Consequences
- The UI can be built in parallel with the core once the API schema is stable.
