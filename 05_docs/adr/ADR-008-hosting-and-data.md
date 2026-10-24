# ADR-008 - Supabase for data, files and auth; Vercel for the front end

Status: ACCEPTED (user, 16-OCT-2026). Applies from M6. Container host: OPEN.

## Context
M6 needs a relational database (v1 Part 17), file storage with checksums, sign-in and role checks (v1 Part 18), and hosting. Supabase and Vercel are already connected to the user's account but not used by the repo.

## Decision
- **Database:** Supabase Postgres. Schema from v1 Part 17 plus input snapshots and stale-result tracking. Migrations add or transform; they never drop data without explicit authorisation.
- **Files:** Supabase Storage for uploaded DXF/DWG, SAFE/ETABS exports and generated deliverables. Every file records SHA-256, size, uploader, time and the run that produced it. Large files are not stored in table rows.
- **Auth:** Supabase Auth. The API (ADR-005) verifies the token and checks the project role on every request. Row-level security is enabled on all project tables as a second line of defence.
- **Roles:** Admin, Design Engineer, Checker, Approver, Viewer. Only an Approver can record an approval; neither the system nor Claude can.
- **Front-end hosting:** Vercel serves the Next.js app only.
- **API and workers:** a Docker container host, because LibreOffice and long jobs can't run on Vercel functions. Provider is OPEN (Development Plan v2 §6, input 6).
- **Stale tracking:** any change to the design basis, geometry, PT data or registry version marks downstream analysis runs, check results and deliverables stale.

## Consequences
- Three hosted services (Vercel, Supabase, container host) plus Redis (ADR-006).
- Licensed desktop tools (SAFE, ETABS, AutoCAD) stay on the engineer's PC; files move by upload and download.
