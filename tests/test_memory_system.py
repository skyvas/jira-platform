"""Unit and integration tests for AgentGraph memory and dreaming system."""
from datetime import date
from pathlib import Path
import tempfile
import pytest

from src.memory.markdown_memory import MarkdownMemoryManager, FailurePattern, ArchitectureInvariant, ADR
from src.memory.context_pruner import ContextPruner
from src.memory.gemini_updater import GeminiUpdater
from src.memory.dreaming_engine import DreamingEngine


def test_markdown_memory_manager_failure_patterns():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = MarkdownMemoryManager(memory_dir=Path(tmpdir) / ".memory")
        
        # Verify initial empty state
        assert mgr.read_failure_patterns() == []

        # Add a failure pattern
        fp1 = FailurePattern(
            id="FP-001",
            title="Missing Auth Guard",
            date_str="2026-09-09",
            symptoms="Unauthenticated access",
            root_cause="Missing session validation",
            rule="Require valid session"
        )
        mgr.add_failure_pattern(fp1)

        patterns = mgr.read_failure_patterns()
        assert len(patterns) == 1
        assert patterns[0].id == "FP-001"
        assert patterns[0].title == "Missing Auth Guard"
        assert patterns[0].rule == "Require valid session"

        # Update existing failure pattern with same ID
        fp1_updated = FailurePattern(
            id="FP-001",
            title="Missing Auth Guard (Updated)",
            date_str="2026-09-09",
            symptoms="Unauthenticated access to board",
            root_cause="Missing session validation on board endpoint",
            rule="Strictly enforce session on all board endpoints"
        )
        mgr.add_failure_pattern(fp1_updated)
        patterns_after = mgr.read_failure_patterns()
        assert len(patterns_after) == 1
        assert patterns_after[0].title == "Missing Auth Guard (Updated)"


def test_markdown_memory_manager_invariants():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = MarkdownMemoryManager(memory_dir=Path(tmpdir) / ".memory")

        # Add invariant to existing/new category
        mgr.add_invariant(
            category="State Machine",
            title="Strict Legal Transitions",
            rule="BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE",
            task_ref="test-task-1"
        )

        content = mgr.read_architecture()
        assert "## State Machine" in content
        assert "Strict Legal Transitions" in content
        assert "BACKLOG -> TODO -> IN_PROGRESS -> REVIEW -> DONE" in content
        assert "test-task-1" in content


def test_markdown_memory_manager_adr():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = MarkdownMemoryManager(memory_dir=Path(tmpdir) / ".memory")

        adr = ADR(
            id="ADR-001",
            title="Adopt LexoRank Fractional Indexing",
            status="ACCEPTED",
            context="Card ordering performance in Kanban columns",
            decision="Use LexoRank midpoints instead of full-column updates",
            consequences=["O(1) drag operations", "Thread-safe concurrent reorders"]
        )

        saved_path = mgr.add_decision_record(adr)
        assert saved_path.exists()
        file_text = saved_path.read_text(encoding="utf-8")
        assert "# ADR-001: Adopt LexoRank Fractional Indexing" in file_text
        assert "O(1) drag operations" in file_text


def test_context_pruner_noise_removal():
    noisy_output = (
        "\x1b[32mSuccess\x1b[0m\n"
        "npm notice created\n"
        "Traceback (most recent call last):\n"
        "  File test.py line 1\n"
        "ValueError: invalid\n"
        "Core semantic information preserved"
    )
    cleaned = ContextPruner.prune_text(noisy_output)
    assert "\x1b[32m" not in cleaned
    assert "npm notice" not in cleaned
    assert "Core semantic information preserved" in cleaned


def test_gemini_updater_sync():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_dir = Path(tmpdir) / ".memory"
        gemini_path = Path(tmpdir) / "GEMINI.md"
        gemini_path.write_text("# Repo Directives\n\n## 1. Operating Axioms\n- Test axiom\n", encoding="utf-8")

        mgr = MarkdownMemoryManager(memory_dir=mem_dir)
        mgr.add_failure_pattern(
            FailurePattern(
                id="FP-042",
                title="Stale Cache",
                date_str="2026-09-09",
                symptoms="Outdated board data",
                root_cause="Missing cache invalidation",
                rule="Invalidate on issue update"
            )
        )

        updater = GeminiUpdater(gemini_file_path=gemini_path, memory_manager=mgr)
        assert updater.sync() is True

        gemini_content = gemini_path.read_text(encoding="utf-8")
        assert "## 4. Active Distilled Rules (From Dreaming Engine)" in gemini_content
        assert "FP-042 (Stale Cache)" in gemini_content


def test_dreaming_engine_cycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_dir = Path(tmpdir) / ".memory"
        trace_dir = Path(tmpdir) / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)

        mgr = MarkdownMemoryManager(memory_dir=mem_dir)
        engine = DreamingEngine(memory_manager=mgr, trace_dir=trace_dir)

        # Create sample session trace
        trace_file = trace_dir / "session-001.json"
        trace_file.write_text("""[
            {"type": "goal", "output": "Setup Auth"},
            {"type": "error_resolution", "title": "Session Invalidation Bug", "symptoms": "Token reused", "root_cause": "Cookie not cleared", "rule": "Set max_age=0 on cookie"},
            {"type": "invariant", "category": "Auth Invariants", "title": "Logout Security", "rule": "Clear all tokens and storage"}
        ]""", encoding="utf-8")

        result = engine.run_dreaming_cycle(sync_gemini=False, prune_transient=True)

        assert result.traces_processed == 1
        assert result.new_invariants == 1
        assert result.new_failure_patterns == 1
        assert not trace_file.exists(), "Transient session file should be pruned after consolidation"

        # Check that memory manager persisted the new entries
        patterns = mgr.read_failure_patterns()
        assert len(patterns) == 1
        assert patterns[0].title == "Session Invalidation Bug"
        assert "Logout Security" in mgr.read_architecture()


def test_markdown_memory_manager_conventions():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = MarkdownMemoryManager(memory_dir=Path(tmpdir) / ".memory")

        assert mgr.read_conventions() == []

        mgr.add_convention("All REST models must inherit from Pydantic BaseModel.")
        conventions = mgr.read_conventions()
        assert len(conventions) == 1
        assert conventions[0] == "All REST models must inherit from Pydantic BaseModel."

        # Deduplication test
        mgr.add_convention("All REST models must inherit from Pydantic BaseModel.")
        assert len(mgr.read_conventions()) == 1

        mgr.add_convention("Enforce strict typing with Python 3.9+ type hints.")
        assert len(mgr.read_conventions()) == 2


def test_markdown_memory_manager_invariants_deduplication():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = MarkdownMemoryManager(memory_dir=Path(tmpdir) / ".memory")

        mgr.add_invariant(
            category="Ordering",
            title="LexoRank Midpoints",
            rule="Compute midpoints on card drag",
            task_ref="task-1"
        )
        invariants = mgr.read_invariants()
        assert len(invariants) == 1
        assert invariants[0].title == "LexoRank Midpoints"
        assert invariants[0].rule == "Compute midpoints on card drag"

        # Update existing invariant with new rule
        mgr.add_invariant(
            category="Ordering",
            title="LexoRank Midpoints",
            rule="Compute fractional midpoints with collision handling",
            task_ref="task-2"
        )
        updated_invariants = mgr.read_invariants()
        assert len(updated_invariants) == 1
        assert updated_invariants[0].rule == "Compute fractional midpoints with collision handling"
        content = mgr.read_architecture()
        assert "task-2" in content


def test_dreaming_engine_cycle_with_conventions():
    with tempfile.TemporaryDirectory() as tmpdir:
        mem_dir = Path(tmpdir) / ".memory"
        trace_dir = Path(tmpdir) / "traces"
        trace_dir.mkdir(parents=True, exist_ok=True)

        mgr = MarkdownMemoryManager(memory_dir=mem_dir)
        engine = DreamingEngine(memory_manager=mgr, trace_dir=trace_dir)

        trace_file = trace_dir / "trace-with-conv.json"
        trace_file.write_text("""[
            {"type": "goal", "output": "Refactor Endpoints"},
            {"type": "convention", "rule": "Protected API routes must use FastAPI Depends(get_current_user)."},
            {"type": "invariant", "category": "Auth Invariants", "title": "Session Tokens", "rule": "Use HttpOnly cookies."}
        ]""", encoding="utf-8")

        result = engine.run_dreaming_cycle(sync_gemini=False, prune_transient=True)
        assert result.traces_processed == 1
        assert result.new_conventions == 1
        assert result.new_invariants == 1
        assert not trace_file.exists()

        conventions = mgr.read_conventions()
        assert len(conventions) == 1
        assert "Depends(get_current_user)" in conventions[0]


def test_agent_loop_trace_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / "sessions"
        from src.loop.agent_loop import AgentLoop

        loop = AgentLoop(max_iterations=1, trace_dir=trace_dir)
        res = loop.run(goal="Test trace logging", verify_cmd="echo PASS", session_id="test-session-42")

        assert res.success is True
        saved_trace = trace_dir / "test-session-42.json"
        assert saved_trace.exists()
        trace_content = saved_trace.read_text(encoding="utf-8")
        assert "Test trace logging" in trace_content
        assert "verification" in trace_content


def test_dag_engine_dream_node_with_target():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        mem_dir = repo_root / ".memory"
        trace_dir = repo_root / ".logs" / "sessions"
        trace_dir.mkdir(parents=True, exist_ok=True)

        from src.graph.types import WorkflowSpec, DAGNode, NodeType
        from src.graph.dag_engine import DAGEngine

        workflow = WorkflowSpec(
            version="1.0",
            name="Targeted Memory Test",
            nodes=[
                DAGNode(
                    id="save-rule",
                    type=NodeType.DREAM,
                    target=".memory/conventions.md",
                    prompt="All REST models must inherit from Pydantic BaseModel."
                )
            ]
        )

        engine = DAGEngine(repo_root=repo_root)
        result = engine.run_workflow(workflow)
        assert result.success is True

        mgr = MarkdownMemoryManager(memory_dir=mem_dir)
        conventions = mgr.read_conventions()
        assert len(conventions) == 1
        assert "Pydantic BaseModel" in conventions[0]

