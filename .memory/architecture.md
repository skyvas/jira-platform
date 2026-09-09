# Architecture Invariants & System Constants (JiraPlatform)

*Last Updated by Agent Dreaming Engine: 2026-09-09 (Task: jira-init)*

## State Machine Invariants
- **Legal Transitions:** Strict transition flow: BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE.
- **Done Timestamping:** Every issue entering DONE must have resolved_at populated with UTC now; reopening an issue clears resolved_at.
- **Keys:** Project issue keys are strictly formatted as `{PROJECT_KEY}-{COUNTER}`.

## Ordering & Concurrency
- **Fractional Indexing (LexoRank):** Drag-and-drop card reordering must compute midpoints using LexoRank rather than shifting integer positions across the entire column.
