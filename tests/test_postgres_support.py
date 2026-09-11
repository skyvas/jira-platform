import pytest

from backend.services import postgres_repository
from backend.services.postgres_repository import PostgresRepository, get_database_url


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        return None

    def fetchone(self):
        return None


class FakeConnection:
    def __init__(self):
        self.autocommit = False

    def cursor(self):
        return FakeCursor()


def test_postgres_repository_reads_env_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/jira")

    monkeypatch.setattr(postgres_repository.psycopg2, "connect", lambda url: FakeConnection())

    assert get_database_url() == "postgresql://user:pass@localhost:5432/jira"
    repo = PostgresRepository()
    assert repo.database_url == "postgresql://user:pass@localhost:5432/jira"
    assert repo.is_postgres_enabled() is True


def test_postgres_repository_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("NAME", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)

    with pytest.raises(RuntimeError, match="PostgreSQL DATABASE_URL"):
        PostgresRepository()


def test_postgres_repository_assembles_from_discrete_github_vars(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)

    monkeypatch.setenv("HOST", "cloud-db.internal")
    monkeypatch.setenv("PORT", "5433")
    monkeypatch.setenv("NAME", "orbit_prod")
    monkeypatch.setenv("USERNAME", "orbit_admin")
    monkeypatch.setenv("PASSWORD", "secret#pass@123")

    monkeypatch.setattr(postgres_repository.psycopg2, "connect", lambda url: FakeConnection())

    expected_url = "postgresql://orbit_admin:secret%23pass%40123@cloud-db.internal:5433/orbit_prod"
    assert get_database_url() == expected_url

    repo = PostgresRepository()
    assert repo.database_url == expected_url
    assert repo.is_postgres_enabled() is True


def test_postgres_snapshot_roundtrips_story_points_type_and_checklist(monkeypatch):
    captured_payloads = []

    class MockCursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, params=None):
            if "INSERT INTO app_state" in sql and params:
                captured_payloads.append(params[1])
        def fetchone(self):
            return None

    class MockConnection:
        def __init__(self):
            self.autocommit = False
        def cursor(self):
            return MockCursor()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/jira")
    monkeypatch.setattr(postgres_repository.psycopg2, "connect", lambda url: MockConnection())

    repo = PostgresRepository()
    issue = repo.create_issue(
        title="Checklist Test Issue",
        project_id="p-1",
        description="Testing checklist persistence",
        issue_type="BUG",
        story_points=8.0
    )
    repo.add_checklist_item(issue.id, "Acceptance criterion 1")

    assert len(captured_payloads) > 0
    latest_payload_str = captured_payloads[-1]

    # Re-hydrate into a new instance using the captured snapshot
    class HydrateCursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, params=None):
            pass
        def fetchone(self):
            return [latest_payload_str]

    class HydrateConnection:
        def __init__(self):
            self.autocommit = False
        def cursor(self):
            return HydrateCursor()

    monkeypatch.setattr(postgres_repository.psycopg2, "connect", lambda url: HydrateConnection())
    hydrated_repo = PostgresRepository()
    hydrated_issue = hydrated_repo.get_issue_by_id(issue.id)

    assert hydrated_issue is not None
    assert str(hydrated_issue.issue_type) == "BUG" or getattr(hydrated_issue.issue_type, "value", None) == "BUG"
    assert hydrated_issue.story_points == 8.0
    assert len(hydrated_issue.checklist) == 1
    assert hydrated_issue.checklist[0].text == "Acceptance criterion 1"
    assert hydrated_issue.checklist[0].is_completed is False
