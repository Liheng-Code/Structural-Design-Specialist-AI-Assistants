# ADR-005 - FastAPI for the server API

Status: ACCEPTED (user, 16-OCT-2026). Applies from M6.

## Context
The web app (M6) needs an API in front of the Python core (ADR-001). Options considered: FastAPI; Next.js API routes calling Python through a subprocess.

## Decision
- The API is FastAPI, running in the same Python environment as the core.
- Request and response models are Pydantic. The same models define the Claude tool schemas (ADR-010).
- The OpenAPI schema is the contract: front-end TypeScript types are generated from it, never written by hand.
- Long work (imports, design runs, document builds) is never done inside a request; it is queued (ADR-006).
- Authorisation is checked on every endpoint against the user's project role (ADR-008).

## Consequences
- One language for the core and its API, with no subprocess bridge.
- The API is deployed separately from the front end, on the container host (ADR-008).
