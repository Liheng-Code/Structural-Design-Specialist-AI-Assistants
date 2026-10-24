# Product Roadmap — Bonded PT Band Beam & Slab Platform

## Current Status (October 2026)

This repository currently provides a **skill-based structural documentation system** focused on:

- Consistent drawing packages
- Design-basis YAML
- Calculation report generation
- QA and document control
- Eurocode-aligned rules

The new skill `pt-slab-package` extends this system so that AI can produce a complete 10-sheet post-tensioned slab drawing package to Eurocode 2 when given a draft layout.

## Two Parallel Tracks

### Track A — Knowledge & AI Skill Layer (Active now)

Goal: Make AI produce high-quality, consistent, Eurocode-compliant PT drawings and calculation notes.

Completed / in progress:
- Company drawing standards
- Design-basis YAML system
- Multiple Claude skills (documentation, drawing, calculation report, QA, specification)
- `pt-slab-package` skill (added 2026-10-16)
- Initial deterministic calculation modules in `calc_lib` (anchorage, etc.)

Near-term priorities:
1. Expand `calc_lib` with deterministic PT modules (losses, initial sizing, simple stress/deflection checks).
2. Improve drawing generation for PT-specific sheets.
3. Add more benchmark examples.
4. Keep skills and standards version-controlled and shared across machines via this repository.

### Track B — Full Product Platform (Long-term vision)

A complete web application for bonded PT band-beam and slab design is described in the Master Implementation Prompt (stored separately by the project owner).

That vision includes:
- CAD import (DXF/DWG) and geometry recognition
- Finite-element analysis
- Deterministic PT design engine (profiles, losses, SLS/ULS)
- Reinforcement design and clash checking
- Coordinated drawing, report and specification generation
- Claude orchestration with strict tool boundaries
- Full revision control, audit trail and engineering approval workflow

This is a multi-year product effort requiring a team of structural engineers and software engineers, independent verification of the analysis and design engines, and careful licensing of any FEA components.

**Do not treat the Master Implementation Prompt as an immediate implementation plan.**  
Use it as the official long-term product specification.  
Only begin Milestone M0–M1 of that plan when team capacity, funding and a clear verification strategy are in place.

## Guiding Principle

The system must remain an **engineering calculation and documentation platform**, not merely an AI drawing generator.

- Deterministic, testable calculations for all numerical results.
- AI is used to orchestrate tools, interpret instructions, explain results and draft documentation.
- AI must never invent numerical results, override failed checks, or issue unverified construction drawings.

## How to Use This Repository Today

1. Clone the repository.
2. Install the skills (they are already in `.claude/skills/`; run `setup.bat` for the Python libraries).
3. For a new PT slab project:
   - Create / fill a design-basis YAML.
   - Use the prompt in `.claude/skills/pt-slab-package/references/user-prompt.md`.
   - Request the full 10-sheet package.
4. Always finish with the existing QA skill and human engineering review.

---

*Last updated: 2026-10-16*
