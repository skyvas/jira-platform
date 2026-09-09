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

    with pytest.raises(RuntimeError, match="PostgreSQL DATABASE_URL"):
        PostgresRepository()
