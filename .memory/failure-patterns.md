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

## FP-008: Cloud Deployment Startup Crash & 500 Error Lacking DATABASE_URL / Health Probes
- **Date:** 2026-09-10
- **Symptoms:** Deploying the application to cloud runtimes (e.g. Wasmer, Render, Fly.io) resulted in HTTP 500 Internal Server Error.
- **Root Cause:** Direct instantiation of `PostgresRepository()` on missing `DATABASE_URL` raised an unhandled `RuntimeError`, crashing the server on startup. Additionally, load balancer `HEAD` health probes returned 405 Method Not Allowed.
- **Rule:** `backend/api/routes.py` and `app.py` must gracefully fall back to `OrbitStore` when `DATABASE_URL` is absent. `app.py` must support `HEAD` and `GET` on both `/` and `/health`, and a root `main.py` entrypoint with dynamic `$PORT` and `Dockerfile` must be provided for container runners.

## FP-009: Wasmer Edge WebAssembly Environment Lacking Pip/Uvicorn/SSL Support
- **Date:** 2026-09-10
- **Symptoms:** Deployment on Wasmer Edge (`*.wasmer.app`) exited with code 1: `/bin/python: No module named uvicorn` and HTTP 500.
- **Root Cause:** Wasmer Edge runs a WebAssembly sandbox (`wasmer/python`) containing only the Python standard library. It does not run a `pip install` build step during GitHub deployments. Furthermore, `uvicorn` unconditionally imports `ssl`, which is missing in WASIX Python. Passing `-m uvicorn` via `cli_args` in `app.yaml` or `main-args` in `wasmer.toml` caused `/bin/python` to fail immediately on startup.
- **Rule:**
  1. Root `main.py` must implement a dual-mode universal runner: use `uvicorn` and FastAPI if available; otherwise gracefully fall back to Python's standard library `http.server.HTTPServer` with zero third-party dependencies to serve the frontend, health checks (`/health`), and JSON REST mock routes.
  2. `app.yaml` (`cli_args: ["main.py"]`) and `wasmer.toml` (`main-args = ["main.py"]`) must execute `main.py` directly without `-m uvicorn`.
  3. `requirements.txt` must strictly contain pure-Python runtime dependencies, moving native C-extensions (`psycopg2-binary`) and browser test tooling (`playwright`, `pytest`) to `requirements-dev.txt`.
  4. Use `.wasmerignore` to exclude local virtual environment symlinks (`.venv/`) so the Wasmer package compiler passes verification without symlink containment errors.

## FP-010: Edge Fallback Handler Serving HTML on Unmatched API Routes Causing UI Breakage
- **Date:** 2026-09-10
- **Symptoms:** On the live Wasmer deployment, clicking on Kanban cards, creating issues, moving cards, or modifying columns did not open modals or complete actions. Browser console logged: `SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON`.
- **Root Cause:** In `main.py`, `WasmerEdgeHandler` only matched a small subset of API paths and routed any unmatched path to `frontend/index.html` with HTTP 200. When client JavaScript called `fetch('/api/issues/iss-1')` or `fetch('/api/board/.../columns')`, the server returned HTML instead of JSON. Calling `res.json()` threw an unhandled `SyntaxError`, preventing `#issue-detail-modal` from opening and breaking UI clicks.
- **Rule:**
  1. `WasmerEdgeHandler` must strictly guard all `/api/...` routes: any unrecognized API route must return JSON with HTTP 404 (`{"detail": "Not found"}`), never falling through to `index.html`.
  2. The edge handler must provide a complete, stateful in-memory store supporting full CRUD for issues (`GET /api/issues/{id}`, `POST /api/issues`, `PATCH /api/issues/{id}`, `POST /api/issues/{id}/move`), comments, sprints, and custom columns so that all UI buttons and modal triggers operate interactively in zero-dependency environments.

## FP-011: Wasmer Edge Runtime Parity Gaps for Authentication and Notification Systems
- **Date:** 2026-09-10
- **Symptoms:** On the live Wasmer deployment, users could not log out (reloading immediately logged them back in as Admin), user switching failed, invalid passwords were accepted, notifications did not update when issues moved or comments with mentions were posted, notifications lacked type icons, and `/api/issues/{id}/comments` returned 404.
- **Root Cause:**
  1. `main.py` `WasmerEdgeHandler` unconditionally returned `STATE.users[0]` (Admin) on `GET /api/auth/me` without checking cookies.
  2. `POST /api/auth/login` did not validate passwords against hash/salt and did not emit `Set-Cookie` headers for `session_id`/`jira_session`.
  3. `POST /api/auth/logout` did not destroy active sessions or expire client cookies.
  4. Initial notifications lacked the `type` attribute needed for SVG rendering, and zero notifications were dispatched when issues were created, assigned, transitioned, or commented on.
  5. Missing REST endpoints in `main.py` (`GET /api/issues/{id}/comments`, `GET /api/sprints/{id}/summary`, `DELETE /api/issues/{id}`).
- **Rule:**
  1. `WasmerState` must support standard library `hashlib.sha256` password hashing, tokenized session management (`STATE.sessions`), and user notification filtering.
  2. `WasmerEdgeHandler` must enforce session cookies on `/api/auth/me` and protected endpoints like `/api/board`.
  3. Every issue creation, transition, assignment change, and comment mention must trigger notifications dispatched to `STATE.notifications` with explicit `type` values (`STATUS_CHANGE`, `ASSIGNED`, `UNASSIGNED`, `MENTION`, `COMMENT`, `UPDATE`).
  4. Ensure complete REST endpoint parity in `WasmerEdgeHandler` so zero-dependency edge runtimes behave identically to ASGI FastAPI.

## FP-012: Ticket Image Upload Hardcoded Mocks, Scoping Errors, and Stale State Leakage
- **Date:** 2026-09-10
- **Symptoms:** Uploading an image to a ticket or comment attached an incorrect external Unsplash photo (`photo-1618005182384-a83a8bd57fbe`) rather than the user's local file. Sequential uploads could mix up or reuse state. In the comment stream, attached images lacked compact thumbnails and visual badges. Opening image previews closed or navigated away from the ticket modal, and clicking tickets occasionally failed with `ReferenceError: renderStagedCommentImages is not defined`.
- **Root Cause:**
  1. `main.py` WasmerEdgeHandler routes `/api/issues/{id}/attachments` and `/api/comments/upload-image` hardcoded static Unsplash URLs and dummy attachment names instead of decoding HTTP multipart/form-data or JSON base64 payloads.
  2. `app.js` declared `renderStagedCommentImages` inside `DOMContentLoaded` instead of module scope, throwing a `ReferenceError` when `openIssueDetail` tried to reset staged comment images upon opening a ticket.
  3. Asynchronous file input listeners did not reset file inputs within `finally` blocks, and modal closure did not purge staged comment images, causing state leakage across tickets.
  4. Comment images lacked thumbnail formatting (`object-fit: contain`, badges) and lacked a dedicated non-destructive Lightbox modal with Download action.
- **Rule:**
  1. Upload endpoints in all runtime layers (`main.py` and `FastAPI`) must parse multipart/form-data and JSON payloads into distinct files saved under `frontend/uploads/{uuid}_{filename}`, returning deterministic `/static/uploads/...` URLs verified to match binary bytes.
  2. All helper functions invoked by asynchronous data loaders (`renderStagedCommentImages`, `openLightbox`, etc.) must be defined in global/top-level scope.
  3. Comment streams must render compact thumbnails (`object-fit: contain`, max dimensions 180x120) with attachment badges and open a dedicated Lightbox modal with Close and Download buttons that retains the parent ticket context upon closing.
  4. File input elements must clear `e.target.value = ''` in `finally` blocks after upload requests resolve, and ticket modal open/close handlers must always purge staged state.

