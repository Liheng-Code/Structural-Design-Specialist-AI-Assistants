# Architecture decision records

Software decisions for the bonded PT band beam & slab designer. Context: [Development Plan v2](../development-plan-v2.md), [Architecture v2](../architecture-v2.md), [tech stack page](https://claude.ai/artifact/8JPdaQXtUGDfXKxMMzh9zX).

These records cover software only. They are not engineering approvals: no calculation, value, clause or deliverable becomes approved because of anything here.

Status values: PROPOSED, ACCEPTED (who, date), OPEN (not decided), SUPERSEDED (by ADR-xxx).

| ADR | Decision | Status |
|---|---|---|
| [001](ADR-001-python-engineering-core.md) | Python engineering core; TypeScript only in the front end | ACCEPTED (user, 16-OCT-2026) |
| [002](ADR-002-analysis-adapter-safe-etabs.md) | Analysis results through an adapter; SAFE/ETABS import first | ACCEPTED (user, 16-OCT-2026); amended by ADR-012 |
| [003](ADR-003-yaml-design-basis-source.md) | YAML design basis stays the source of truth until M6 | ACCEPTED (user, 16-OCT-2026) |
| [004](ADR-004-design-code-registry.md) | Versioned design-code registry with verification status | ACCEPTED (user, 16-OCT-2026) |
| [005](ADR-005-api-fastapi.md) | FastAPI for the server API | ACCEPTED (user, 16-OCT-2026) |
| [006](ADR-006-job-queue-redis-rq.md) | Redis + RQ for background jobs | ACCEPTED (user, 16-OCT-2026) |
| [007](ADR-007-units-pint.md) | pint for unit handling | ACCEPTED (user, 16-OCT-2026); internal base units N, mm, MPa with kN in/out (user, 25-OCT-2026) |
| [008](ADR-008-hosting-and-data.md) | Supabase for database, files and auth; Vercel for the front end | ACCEPTED (user, 16-OCT-2026); container host OPEN |
| [009](ADR-009-front-end.md) | Next.js + TypeScript + Tailwind front end | ACCEPTED (user, 16-OCT-2026); viewer and chart libraries PROPOSED |
| [010](ADR-010-claude-tool-layer.md) | AI (Claude or local Ollama models) through a server-side, schema-validated tool layer | ACCEPTED (user, 16-OCT-2026); amendment 1 adds local models |
| [011](ADR-011-quality-gates.md) | unittest + benchmark register + mypy + ruff; CI when a remote exists | ACCEPTED (user, 16-OCT-2026) |
| [012](ADR-012-safe-api-model-build.md) | System builds and runs the SAFE 22 model from the architect DXF through the local CSI API | ACCEPTED (user, 25-OCT-2026) |
