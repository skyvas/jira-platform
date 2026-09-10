# Orbit Workspace Customizations (`.agents/`)

This directory contains workspace-specific skills and workflows that empower autonomous AI agents to build, test, and maintain Orbit with domain expertise and engineering discipline.

---

## Directory Structure

```
.agents/
├── README.md               # Workspace customizations overview
├── skills/                 # Modular agent skills with SKILL.md and tools
│   ├── jira-expert/
│   ├── scrum-master/
│   ├── agile-product-owner/
│   ├── atlassian-templates/
│   ├── playwright-pro/
│   ├── api-test-suite-builder/
│   ├── tdd-guide/
│   ├── senior-qa/
│   ├── git-worktree-manager/
│   ├── agent-workflow-designer/
│   ├── memory-engineering/
│   ├── self-improving-agent/
│   ├── zero-hallucination-coder/
│   ├── api-design-reviewer/
│   ├── database-schema-designer/
│   ├── senior-backend/
│   ├── ui-design-system/
│   └── docker-development/
└── workflows/              # Autonomous DAG workflows executed by AgentGraph
    ├── README.md
    ├── jira-core.yaml
    ├── qa-regression-pipeline.yaml
    ├── feature-delivery-dag.yaml
    └── database-migration-dag.yaml
```

---

## 1. Installed Skills Summary

### Agile & Jira Platform Core
- **`jira-expert`**: Jira issue hierarchies, workflows, state machine transitions, JQL, custom board configurations, sprint backlogs. Bundles `scripts/workflow_validator.py`.
- **`scrum-master`**: Sprint lifecycle, velocity calculations, capacity forecasting, burndown/burnup analysis, and agile coaching.
- **`agile-product-owner`**: User story creation, acceptance criteria formulation (Gherkin format), INVEST criteria, Definition of Done (DoD) & Definition of Ready (DoR).
- **`atlassian-templates`**: Standardized templates for user stories, bug tickets, sprint planning briefs, and acceptance criteria.

### QA Automation, Testing & TDD
- **`playwright-pro`**: Playwright browser testing toolkit: robust auto-wait selectors, page objects, visual regression, handling session cookies, and debugging test flakes.
- **`api-test-suite-builder`**: Scans FastAPI routes and generates integration test suites covering edge cases, status code boundaries, and RBAC authentication guards (`ADMIN`, `MEMBER`, `VIEWER`).
- **`tdd-guide`**: Test-Driven Development (Red-Green-Refactor) workflow. Generates fixtures and unit tests before code implementation to satisfy Orbit's strict exit-code-0 verification gates.
- **`senior-qa`**: Test pyramid strategy, test matrix design, automation frameworks, and regression coverage tracking.

### AgentGraph, Worktrees & Autonomous Memory
- **`git-worktree-manager`**: Standardizes branch isolation, port allocation, and worktree cleanup. Directly enforces Orbit's operating axiom on protected branches.
- **`agent-workflow-designer`**: Multi-agent orchestration architectures (sequential, parallel DAGs, routers, evaluators, verification loops).
- **`memory-engineering`**: Designing and pricing agent memory systems (fact/skill/log density, forgetting policies, promotion to durable memory).
- **`self-improving-agent`**: Auto-memory curation, analyzing execution logs/traces for failure patterns, and distilling edge cases into `.memory/failure-patterns.md`.
- **`zero-hallucination-coder`**: Disciplined Discuss → Map → Decompose → Execute → Verify loop that grounds modifications in reality and deterministic unit tests.

### API, Database & UI Architecture
- **`api-design-reviewer`**: REST API design auditing: URL hierarchy, HTTP status codes, error payload schemas, backward compatibility.
- **`database-schema-designer`**: Schema normalization, ERD planning, migration safety, foreign key constraints, and indexing for SQLite and PostgreSQL adapters.
- **`senior-backend`**: FastAPI backend patterns, dependency injection, connection pooling, and error handling.
- **`ui-design-system`**: Design token architecture, dark-mode glassmorphic aesthetics, component modularity, and micro-animations for Vanilla HTML/CSS/JS.
- **`docker-development`**: Dockerfile optimization, multi-stage builds, container development, and runtime security.

---

## 2. Autonomous DAG Workflows

Workflows are executed via:
```bash
python -m src.cli run-graph workflows/<workflow-name>.yaml
```
See [`workflows/README.md`](file:///Users/akash-mac/workspace/jira-platform/.agents/workflows/README.md) for full details.
