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
