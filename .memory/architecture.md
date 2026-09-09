# Architecture Invariants & System Constants (Orbit)

*Last Updated by Agent Dreaming Engine: 2026-09-09 (Task: memory-remediation)*

## State Machine Invariants
- **Legal Transitions:** Strict transition flow: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE (or dynamic ordering defined by custom project columns).
- **Done Timestamping:** Every issue entering DONE must have resolved_at populated with UTC now; reopening an issue clears resolved_at.
- **Keys:** Project issue keys are strictly formatted as `{PROJECT_KEY}-{COUNTER}`.
- **Dynamic Columns:** Project custom board column ordering overrides default transition lanes while preserving directional flow and DONE timestamping invariants.

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

