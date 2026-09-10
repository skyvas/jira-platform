# Autonomous DAG Workflows for Orbit

Orbit includes an embedded DAG execution engine (`src/graph/dag_engine.py`) that orchestrates multi-agent tasks using topological wave dispatch, Git worktree isolation, deterministic compiler/test verification gates, and offline memory dreaming.

Workflows can be executed using the `src.cli` command:
```bash
python -m src.cli run-graph workflows/<workflow-file>.yaml
```

Use `--dry-run` to simulate execution without executing shell commands or modifying files:
```bash
python -m src.cli run-graph workflows/<workflow-file>.yaml --dry-run
```

---

## Available Workflows

| Workflow | File Path | Objective | Key Node Sequence |
|---|---|---|---|
| **Orbit Core** | [`workflows/jira-core.yaml`](file:///Users/akash-mac/workspace/jira-platform/workflows/jira-core.yaml) | Full sprint and Kanban board core feature loop | `board-spec` (Planner) → `issue-worker` (Worktree Worker) → `security-verifier` (Verifier) → `memory-dream` (Dream) → `final-synthesizer` (Synthesizer) |
| **QA Regression Pipeline** | [`workflows/qa-regression-pipeline.yaml`](file:///Users/akash-mac/workspace/jira-platform/workflows/qa-regression-pipeline.yaml) | Automated regression test verification and failure consolidation | `test-matrix-planner` (Planner) → `api-integration-worker` & `playwright-ui-worker` (Workers) → `rbac-security-verifier` (Verifier) → `memory-failure-dream` (Dream) → `qa-synthesizer` (Synthesizer) |
| **Agile Feature Delivery** | [`workflows/feature-delivery-dag.yaml`](file:///Users/akash-mac/workspace/jira-platform/workflows/feature-delivery-dag.yaml) | End-to-end user story specification, isolated coding, and verification | `feature-spec-planner` (Planner) → `feature-worker` (Worktree Worker) → `tdd-test-verifier` (Verifier) → `architecture-memory-dream` (Dream) → `synthesizer-merge` (Synthesizer) |
| **Database Schema Migration** | [`workflows/database-migration-dag.yaml`](file:///Users/akash-mac/workspace/jira-platform/workflows/database-migration-dag.yaml) | Safe relational schema migration and persistence verification | `migration-planner` (Planner) → `migration-worker` (Worktree Worker) → `persistence-verifier` (Verifier) → `schema-memory-dream` (Dream) → `migration-synthesizer` (Synthesizer) |

---

## Workflow Node Types

1. **`planner`**: Formulates specifications, API contracts, user stories, and acceptance criteria. Emits files into `docs/specs/`.
2. **`worker`**: Implements code changes. When `worktree: true`, execution occurs in an isolated Git worktree branch (`task-<node-id>`), preventing contamination of protected branches.
3. **`verifier`**: Executes deterministic test commands (`pytest tests/ -v`). When `gate: blocking`, a non-zero exit code halts the workflow immediately.
4. **`dream`**: Consolidates architecture invariants or distilled failure patterns into `.memory/` (`architecture.md` or `failure-patterns.md`).
5. **`synthesizer`**: Merges worktree changes, executes final integration verification, and emits sign-off logs.
