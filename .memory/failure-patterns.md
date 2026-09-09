# Known Failure Patterns & Regressions

This document is maintained by the Dreaming Engine to record resolved bugs and prevent regressions.

## FP-001: Missing Status Guard on Direct Drag-and-Drop
- **Date:** 2026-09-09
- **Symptoms:** Issues dragged directly from Backlog to Done bypassed code review validation.
- **Root Cause:** Missing state machine transition check in PATCH endpoint.
- **Rule:** Every card move endpoint must strictly enforce StateMachine.can_transition().

## FP-002: Reopened Issues Retaining Stale Resolution Dates
- **Date:** 2026-09-09
- **Symptoms:** Reopened issues still reported in sprint velocity as resolved.
- **Root Cause:** Failure to clear resolved_at on non-Done transitions.
- **Rule:** Reset resolved_at = None whenever an issue transitions out of DONE.

## FP-003: Unprotected Board Data Access Post-Logout
- **Date:** 2026-09-09
- **Symptoms:** After session logout, directly calling `/api/board` still returned project Kanban board data.
- **Root Cause:** Missing active session authentication check on `/api/board`.
- **Rule:** `/api/board` must require an authenticated session and raise HTTP 401 Unauthorized if unauthenticated or session invalidated.

## FP-004: Custom Column Dynamic State Transitions
- **Date:** 2026-09-09
- **Symptoms:** Dragging cards between custom-defined columns failed if StateMachine only recognized hardcoded enum values.
- **Root Cause:** StateMachine allowed only default enum statuses.
- **Rule:** StateMachine must support project column ordering for dynamic custom lanes while still enforcing directional flow and DONE timestamping invariants.

## FP-005: Issue Unassignment Ignored on PATCH
- **Date:** 2026-09-09
- **Symptoms:** Sending `{"assignee": null}` or `{"assignee": ""}` to `/api/issues/{id}` failed to unassign the issue.
- **Root Cause:** `UpdateIssueRequest` treated `assignee: None` identically whether it was omitted or explicitly set to `null`, and `store.update_issue` checked `if assignee is not None:`.
- **Rule:** Inspect `req.model_fields_set` on PATCH to pass explicit `null`/empty values to the store using sentinel defaults (`_UNSET`), allowing unassignment to set `issue.assignee = None`.

## FP-006: Missing Notification Trigger on Issue Unassignment
- **Date:** 2026-09-09
- **Symptoms:** When an assigned user was unassigned from an issue, no notification was sent to inform them of the change.
- **Root Cause:** `update_issue` notification conditions only checked `if issue.assignee and issue.assignee != old_assignee`, omitting notifications when `issue.assignee` became `None` or changed away from `old_assignee`.
- **Rule:** Trigger `NotificationType.UNASSIGNED` for `old_assignee` whenever `old_assignee and old_assignee != issue.assignee`.

## FP-007: Unauthorized Modifications by Non-Admin Roles
- **Date:** 2026-09-09
- **Symptoms:** Member and Viewer roles were able to create/start/complete sprints, modify custom board columns, create projects, and alter user roles.
- **Root Cause:** Endpoints lacked explicit role checks beyond basic authentication.
- **Rule:** All administrative and board-defining operations (`/api/sprints` lifecycle, `/api/board/{id}/columns`, `/api/projects`, `/api/users`, `/api/users/{id}/role`) must strictly enforce `require_admin()` yielding HTTP 403 Forbidden for non-Admin roles (`MEMBER`, `VIEWER`), and the frontend must hide/disable critical control surfaces for non-admins.
