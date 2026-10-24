# ADR-006 - Redis + RQ for background jobs

Status: ACCEPTED (user, 16-OCT-2026). Applies from M6.

## Context
Imports, design runs, LibreOffice conversions and DXF/DOCX/XLSX builds take seconds to minutes and must not run inside web requests. Options considered: Redis + RQ; Celery; a Postgres-backed queue.

## Decision
- Jobs are queued in Redis and executed by RQ workers running the Python core.
- Every job records: input snapshot id, registry version (ADR-004), code version (Git commit), start and end time, outcome, and the files it produced with SHA-256.
- Jobs never execute uploaded content or AI-generated code.
- Failed calculation jobs stay failed and visible; they are not retried automatically.

## Consequences
- One more service (Redis) to host. If that becomes a burden, a Postgres-backed queue is the fallback, so RQ specifics must not leak into the core.
- RQ workers rely on `fork` and need Linux, so they run in the Linux container. Local development on Windows uses Docker or WSL for the worker; the CLI tools are unaffected.
