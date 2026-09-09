# ADR-0001: FastAPI for High-Concurrency Agile REST Engine

## Status
Accepted

## Context
A Jira-like Kanban platform requires high-frequency card state transitions, WebSocket updates, and rapid API serialization.

## Decision
Adopt FastAPI with Pydantic domain models for predictable validation and high async performance.

## Consequences
- Fast response times for drag-and-drop actions.
- Native OpenAPI documentation generation.
