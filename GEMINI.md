# Repository Directives for Autonomous Agents (Gemini)

## 1. Operating Axioms
- NEVER announce completion without a verified exit code 0 from testing tools.
- Never write code directly on protected branches (`main`, `staging`). Work strictly inside assigned Git Worktrees.
- Run tests (`pytest tests/ -v`) after every substantive file change.

## 2. Deterministic Verification Gates
- Unit & Integration Testing: `pytest tests/ -v`
- Process Exit Code: Process exit code must be strictly `0`.

## 3. Memory & Consolidation Directives
- Read architectural constants from `.memory/architecture.md` prior to planning.
- Document any verified edge-case fixes into `.memory/failure-patterns.md`.
