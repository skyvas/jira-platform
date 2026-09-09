import os


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
    def __init__(self, dsn=None):
        self.autocommit = False

    def cursor(self):
        return FakeCursor()


# Provide a deterministic PostgreSQL URL for all test collection/imports.
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/jira")

try:
    import psycopg2
except Exception:
    psycopg2 = None

if psycopg2 is not None:
    psycopg2.connect = lambda url: FakeConnection(url)
