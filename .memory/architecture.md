# Architecture Invariants & System Constants (Orbit)

*Last Updated by Agent Dreaming Engine: 2026-09-09 (Task: memory-remediation)*

## State Machine Invariants
- **Legal Transitions:** Strict transition flow: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE (or dynamic ordering defined by custom project columns).
- **Done Timestamping:** Every issue entering DONE must have resolved_at populated with UTC now; reopening an issue clears resolved_at.
- **Keys:** Project issue keys are strictly formatted as `{PROJECT_KEY}-{COUNTER}`.
- **Dynamic Columns:** Project custom board column ordering overrides default transition lanes while preserving directional flow and DONE timestamping invariants.

## Issue Taxonomy, Sizing & Checklists
- **Issue Types:** Issues support semantic classification into `STORY`, `BUG`, `TASK`, and `EPIC` with dedicated visual indicators and filtering.
- **Story Points & WIP Totals:** Issues support optional numeric story points (Fibonacci scale `1, 2, 3, 5, 8, 13, 21`). Column headers calculate and display live aggregate story points for WIP visibility.
- **Acceptance Checklists:** Issues support atomic acceptance criteria and sub-task checklists (`ChecklistItem`) with dedicated `POST`, `PATCH`, `DELETE` endpoints under `/api/issues/{id}/checklist` maintaining dual-mode parity across FastAPI and `WasmerEdgeHandler`.

## Ordering & Concurrency
- **Fractional Indexing (LexoRank):** Drag-and-drop card reordering must compute midpoints using LexoRank rather than shifting integer positions across the entire column.

## Role-Based Access Control (RBAC)
- **Role Hierarchy:** User roles are strictly partitioned into ADMIN, MEMBER, and VIEWER.
- **Admin Gate:** Administrative and board-defining operations (/api/sprints lifecycle, /api/board/{id}/columns, /api/projects, /api/users, /api/users/{id}/role) must strictly enforce require_admin() yielding HTTP 403 Forbidden for non-Admin roles.

## Authentication & Session Security
- **Session Cookie:** Authentication state is stored in an HttpOnly, SameSite=Lax cookie (jira_session) validated via the active in-memory session store.
- **Logout Invalidation:** Explicit logout terminates the session, immediately revoking access to protected endpoints like /api/board.

## File Storage & Attachments
- **Attachment Directory:** Uploaded issue attachments are stored in frontend/uploads/ and served via static mount /uploads.

## Notifications Engine
- **Event Triggers:** Notifications must be dispatched for assignment, unassignment (old_assignee), mentions in comments, and issue status transitions.

## Persistence & PostgreSQL Storage
- **PostgreSQL Configuration:** Connection settings support unified connection URLs (`DATABASE_URL`, `POSTGRES_DATABASE_URL`, `POSTGRES_URL`) and discrete GitHub Environment / Repository variables (`HOST`, `PORT`, `NAME`, `USERNAME`, `PASSWORD` or `DB_*`/`POSTGRES_*`/`PG*` variants) with URL-encoding for special characters.
- **Snapshot Persistence:** `PostgresRepository` serializes full entity states into `app_state` JSONB snapshots on mutations, preserving story points, issue types, and checklists across restarts.

## Security & Cryptography
- **Password Hashing:** Passwords are encrypted using standard library PBKDF2-HMAC-SHA256 with 100,000 iterations and random per-user salt. Password verification employs constant-time `hmac.compare_digest` with backwards-compatible fallback for legacy SHA-256 hashes.
- **CORS Hardening:** API origins are governed by `CORS_ALLOWED_ORIGINS` environment variables, automatically toggling `allow_credentials` to prevent browser wildcard credential vulnerabilities.

## Real-Time Engine (Server-Sent Events)
- **Unidirectional Card Push:** Real-time synchronization is driven strictly by Server-Sent Events (`GET /api/events`) with `text/event-stream` mime-type, keepalive pings, and disconnect cleanup.
- **Broadcast Events:** Mutating operations broadcast `ISSUE_CREATED`, `ISSUE_MOVED`, `ISSUE_UPDATED`, `ISSUE_DELETED`, `CHECKLIST_UPDATED`, and `COMMENT_ADDED`.
- **Client Synchronization:** The frontend establishes an `EventSource` on workspace initialization, live-refreshing the board without disrupting active input or modal focus.

## State Machine Workflow Guards
- **Checklist Resolution Gate:** Issues cannot transition to `DONE` if any acceptance checklist item remains incomplete (`completed == False`). Violations trigger an `InvalidTransitionError` and return HTTP 400 with a descriptive count of incomplete items.

## Deployment & Cloud Execution Invariants
- **Root Entrypoint:** Root `main.py` and `Procfile` expose the ASGI FastAPI app with dynamic `$PORT` and `0.0.0.0` binding.
- **Health Probes:** `/health` and `/` endpoints must support both `GET` and `HEAD` methods with HTTP 200 responses.
- **Persistence Fallback:** In the absence of a configured `DATABASE_URL`, the service gracefully initializes `OrbitStore` in memory with seeded demo accounts, preventing startup 500 crashes.
- **Wasmer Edge Dual-Mode Architecture:** In WebAssembly environments (`wasmer/python` / WASIX) where `uvicorn` and `pip` are unavailable, `main.py` gracefully shifts to Python's standard-library `http.server.HTTPServer` with a stateful in-memory store (`WasmerState`) supporting full CRUD for issues, cards, sprints, comments, checklists, and columns. `WasmerEdgeHandler` enforces full feature parity with the ASGI stack: HttpOnly session cookie authentication (`session_id`/`jira_session`), PBKDF2 password hashing, user switching, SSE real-time connection handshake, workflow resolution checklist guards, and an automated event-driven notification engine for assignments, transitions, and @mentions. All `/api/...` routes strictly return JSON (with 404 JSON for undefined endpoints) to guarantee client `fetch()` JSON deserialization never receives HTML.
- **Edge Deployment Manifests:** Application deployment is governed by `app.yaml` (schema `wasmer.io/App.v0`), package definition `wasmer.toml`, and `.wasmerignore` to exclude local symlinks.

