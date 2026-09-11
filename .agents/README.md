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
│   ├── senior-architect/
│   ├── tech-stack-evaluator/
│   ├── migration-architect/
│   ├── observability-designer/
│   ├── senior-frontend/
│   ├── ui-design-system/
│   ├── a11y-audit/
│   ├── ux-researcher-designer/
│   ├── product-discovery/
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

### System Architecture & Modernization
- **`senior-architect`**: System architecture design, ADR formulation, monolith vs. microservices trade-offs, scalability planning, dependency analysis, and automated diagram generation (`architecture_diagram_generator.py`, `dependency_analyzer.py`, `project_architect.py`).
- **`tech-stack-evaluator`**: Multi-criteria technical evaluation, comparison matrices, architectural suitability scoring, and Total Cost of Ownership (TCO) estimation.
- **`migration-architect`**: Modernization and migration architecture, database schema migrations, service decomposition, zero-downtime cutover planning, and rollback runbooks.
- **`observability-designer`**: Telemetry architecture (metrics, logs, traces), SLI/SLO design, golden-signals monitoring, and alert optimization.

### UI Engineering, Design Systems & Accessibility
- **`senior-frontend`**: Frontend architecture for React, Next.js, HTML, CSS, and Tailwind. Bundles component scaffolding (`component_generator.py`), bundle analysis (`bundle_analyzer.py`), and performance profiling.
- **`ui-design-system`**: Design token architecture, dark-mode glassmorphic aesthetics, component modularity, and micro-animations for Vanilla HTML/CSS/JS.
- **`a11y-audit`**: Complete accessibility audit and remediation pipeline for WCAG 2.2 Level A and AA compliance, color contrast calculation, ARIA role validation, and stakeholder compliance reporting.

### UX Research, Discovery & Product Strategy
- **`ux-researcher-designer`**: UX research synthesis, data-driven user persona generator (`persona_generator.py`), customer journey mapper (`journey_mapper.py`), and usability testing protocol planner (`usability_test_planner.py`).
- **`product-discovery`**: Continuous customer discovery, assumption mapper (`assumption_mapper.py`), user interview guides, and opportunity solution tree structuring.

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

### API, Database & Infrastructure
- **`api-design-reviewer`**: REST API design auditing: URL hierarchy, HTTP status codes, error payload schemas, backward compatibility.
- **`database-schema-designer`**: Schema normalization, ERD planning, migration safety, foreign key constraints, and indexing for SQLite and PostgreSQL adapters.
- **`senior-backend`**: FastAPI backend patterns, dependency injection, connection pooling, and error handling.
- **`docker-development`**: Dockerfile optimization, multi-stage builds, container development, and runtime security.

---

## 2. Autonomous DAG Workflows

Workflows are executed via:
```bash
python -m src.cli run-graph workflows/<workflow-name>.yaml
```
See [`workflows/README.md`](file:///Users/akash-mac/workspace/jira-platform/.agents/workflows/README.md) for full details.
