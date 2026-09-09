# JiraPlatform: Agile Project Management & Kanban Tracker

JiraPlatform is a modern, high-performance agile project management system and issue tracker featuring dynamic Kanban boards, sprint backlogs, state machine transition guards, and LexoRank fractional indexing.

The repository is natively integrated with the **AgentGraph** autonomous orchestration harness, pairing isolated Git worktrees with deterministic compiler verification gates and offline Markdown memory consolidation ("dreaming").

---

## 🚀 Key Features

- **Agile Kanban Board**: Visual drag-and-drop column lanes (`Backlog`, `To Do`, `In Progress`, `Code Review`, `Done`).
- **Issue Tracking & Keys**: Auto-incrementing project issue keys (e.g. `PROJ-1`, `PROJ-2`).
- **Deterministic State Machine**: Strictly validates issue status transitions and automatically manages `resolved_at` timestamps.
- **LexoRank Fractional Indexing**: Instant, collision-free card re-ordering without expensive batch updates.
- **Sprint Management**: Sprint planning cycles with capacity and completion analytics.
- **AgentGraph Harness Embedded**: Native multi-agent DAGs (`workflows/`), memory storage (`.memory/`), and deterministic exit-code-0 verification gates (`GEMINI.md`).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+ with FastAPI, PostgreSQL-ready persistence adapter, and Pydantic; the repository supports a Postgres `DATABASE_URL`
- **Frontend**: Glassmorphic dark-mode web application.
- **Autonomous Engine**: AgentGraph (DAG scheduler, Git worktrees, pristine verifier, dreaming engine).
- **Testing**: Pytest suites with strict binary verification gates.

---

## 📦 Quickstart

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run test suites
pytest tests/ -v

# Start the application
python -m uvicorn backend.api.app:app --port 8000 --reload
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
