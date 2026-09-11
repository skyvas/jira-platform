"""PostgreSQL-only repository adapter for JiraPlatform.

This repository is intentionally PostgreSQL-only. If no valid
PostgreSQL `DATABASE_URL` is configured, the service must fail fast
instead of silently falling back to the in-memory `OrbitStore`.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import psycopg2
except Exception:  # pragma: no cover
    psycopg2 = None

from backend.models.domain import (
    Board,
    Issue,
    IssueActivity,
    Notification,
    Project,
    Sprint,
    User,
)
from backend.services.jira_store import OrbitStore


import urllib.parse


def get_database_url() -> str:
    """Return the configured PostgreSQL URL or raise if missing.

    Supports direct connection strings (DATABASE_URL, POSTGRES_DATABASE_URL, POSTGRES_URL)
    or discrete environment variables (HOST, PORT, NAME, USERNAME, PASSWORD or DB_*/POSTGRES_*/PG* variants).
    """
    value = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or ""
    ).strip()
    if value:
        return value

    # Check discrete connection variables (prioritize DB_* and POSTGRES_* over generic PORT / USERNAME)
    host = (
        os.getenv("DB_HOST")
        or os.getenv("POSTGRES_HOST")
        or os.getenv("PGHOST")
        or os.getenv("HOST")
        or ""
    ).strip()

    name = (
        os.getenv("DB_NAME")
        or os.getenv("POSTGRES_DB")
        or os.getenv("PGDATABASE")
        or os.getenv("POSTGRES_NAME")
        or os.getenv("NAME")
        or ""
    ).strip()

    username = (
        os.getenv("DB_USERNAME")
        or os.getenv("DB_USER")
        or os.getenv("POSTGRES_USER")
        or os.getenv("PGUSER")
        or os.getenv("POSTGRES_USERNAME")
        or os.getenv("USERNAME")
        or ""
    ).strip()

    password = (
        os.getenv("DB_PASSWORD")
        or os.getenv("POSTGRES_PASSWORD")
        or os.getenv("PGPASSWORD")
        or os.getenv("PASSWORD")
        or ""
    ).strip()

    port = (
        os.getenv("DB_PORT")
        or os.getenv("POSTGRES_PORT")
        or os.getenv("PGPORT")
        or (os.getenv("PORT") if not os.getenv("DB_PORT") and os.getenv("PORT", "").isdigit() and int(os.getenv("PORT", "0")) in (5432, 5433, 6432) else "")
        or "5432"
    ).strip()

    if host and name:
        user_info = ""
        if username:
            quoted_user = urllib.parse.quote_plus(username)
            if password:
                quoted_pass = urllib.parse.quote_plus(password)
                user_info = f"{quoted_user}:{quoted_pass}@"
            else:
                user_info = f"{quoted_user}@"
        return f"postgresql://{user_info}{host}:{port}/{name}"

    raise RuntimeError("PostgreSQL DATABASE_URL is required; no in-memory fallback is allowed.")


class PostgresRepository(OrbitStore):
    """OrbitStore subclass with a PostgreSQL JSON snapshot persistence layer."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_database_url()
        if not self.database_url:
            raise RuntimeError("PostgreSQL DATABASE_URL is required; no in-memory fallback is allowed.")

        if psycopg2 is None:
            raise RuntimeError("psycopg2 is required for PostgreSQL support.")

        self.conn: Any = None
        self._postgres_enabled = False
        self._connection_error: Optional[str] = None

        super().__init__()
        self._connect_and_initialize()

    def _connect_and_initialize(self) -> None:
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = True
            self._postgres_enabled = True
            self._ensure_schema()
            self._load_snapshot_into_store()
            self.save_snapshot()
        except Exception as exc:
            self._connection_error = str(exc)
            self._postgres_enabled = False
            self.conn = None
            raise RuntimeError(f"PostgreSQL repository initialization failed: {exc}") from exc

    def _ensure_schema(self) -> None:
        if not self.conn:
            return

        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL
                )
                """
            )

    def _load_snapshot_into_store(self) -> None:
        """Hydrate the in-memory dictionaries from the Postgres snapshot if present."""
        if not self.conn:
            return

        with self.conn.cursor() as cur:
            cur.execute("SELECT value FROM app_state WHERE key = %s", ("orbit_store_snapshot",))
            row = cur.fetchone()
            if not row:
                return

        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)

        if not isinstance(payload, dict):
            return

        self.projects = {}
        self.boards = {}
        self.issues = {}
        self.sprints = {}
        self.activities = []
        self.users = {}
        self.sessions = {}
        self.notifications = []

        for project in payload.get("projects", []):
            obj = Project.model_validate(project)
            self.projects[obj.id] = obj

        for board in payload.get("boards", []):
            obj = Board.model_validate(board)
            self.boards[obj.id] = obj

        for issue in payload.get("issues", []):
            obj = Issue.model_validate(issue)
            self.issues[obj.id] = obj

        for sprint in payload.get("sprints", []):
            obj = Sprint.model_validate(sprint)
            self.sprints[obj.id] = obj

        for activity in payload.get("activities", []):
            self.activities.append(IssueActivity.model_validate(activity))

        for user in payload.get("users", []):
            user_obj = User.model_validate(user["user"])
            self.users[user_obj.id] = {
                "user": user_obj,
                "hash": user["hash"],
                "salt": user["salt"],
            }

        for session in payload.get("sessions", []):
            self.sessions[session["token"]] = {
                "user_id": session["user_id"],
                "created_at": datetime.fromisoformat(session["created_at"]),
            }

        for notification in payload.get("notifications", []):
            obj = Notification.model_validate(notification)
            self.notifications.append(obj)

    def save_snapshot(self) -> None:
        """Write the in-memory object graph to Postgres as a JSON snapshot."""
        if not self.conn:
            return

        payload = {
            "projects": [p.model_dump(mode="json") for p in self.projects.values()],
            "boards": [b.model_dump(mode="json") for b in self.boards.values()],
            "issues": [i.model_dump(mode="json") for i in self.issues.values()],
            "sprints": [s.model_dump(mode="json") for s in self.sprints.values()],
            "activities": [a.model_dump(mode="json") for a in self.activities],
            "users": [
                {
                    "user": u["user"].model_dump(mode="json"),
                    "hash": u["hash"],
                    "salt": u["salt"],
                }
                for u in self.users.values()
            ],
            "sessions": [
                {
                    "token": token,
                    "user_id": session["user_id"],
                    "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else str(session["created_at"]),
                }
                for token, session in self.sessions.items()
            ],
            "notifications": [n.model_dump(mode="json") for n in self.notifications],
        }

        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO app_state(key, value) VALUES (%s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                ("orbit_store_snapshot", json.dumps(payload)),
            )

    def is_postgres_enabled(self) -> bool:
        return self._postgres_enabled

    def availability_error(self) -> Optional[str]:
        return self._connection_error

    def persist(self) -> None:
        self.save_snapshot()

    def create_user(self, *args, **kwargs):
        out = super().create_user(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_user_role(self, *args, **kwargs):
        out = super().update_user_role(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_user_name(self, *args, **kwargs):
        out = super().update_user_name(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_user_password(self, *args, **kwargs):
        out = super().update_user_password(*args, **kwargs)
        self.save_snapshot()
        return out

    def create_session(self, *args, **kwargs):
        out = super().create_session(*args, **kwargs)
        self.save_snapshot()
        return out

    def delete_session(self, *args, **kwargs):
        out = super().delete_session(*args, **kwargs)
        self.save_snapshot()
        return out

    def create_notification(self, *args, **kwargs):
        out = super().create_notification(*args, **kwargs)
        self.save_snapshot()
        return out

    def toggle_notification_read(self, *args, **kwargs):
        out = super().toggle_notification_read(*args, **kwargs)
        self.save_snapshot()
        return out

    def mark_all_notifications_read(self, *args, **kwargs):
        out = super().mark_all_notifications_read(*args, **kwargs)
        self.save_snapshot()
        return out

    def create_project(self, *args, **kwargs):
        out = super().create_project(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_board_columns(self, *args, **kwargs):
        out = super().update_board_columns(*args, **kwargs)
        self.save_snapshot()
        return out

    def create_issue(self, *args, **kwargs):
        out = super().create_issue(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_issue(self, *args, **kwargs):
        out = super().update_issue(*args, **kwargs)
        self.save_snapshot()
        return out

    def move_issue(self, *args, **kwargs):
        out = super().move_issue(*args, **kwargs)
        self.save_snapshot()
        return out

    def add_attachment(self, *args, **kwargs):
        out = super().add_attachment(*args, **kwargs)
        self.save_snapshot()
        return out

    def remove_attachment(self, *args, **kwargs):
        out = super().remove_attachment(*args, **kwargs)
        self.save_snapshot()
        return out

    def add_comment(self, *args, **kwargs):
        out = super().add_comment(*args, **kwargs)
        self.save_snapshot()
        return out

    def create_sprint(self, *args, **kwargs):
        out = super().create_sprint(*args, **kwargs)
        self.save_snapshot()
        return out

    def start_sprint(self, *args, **kwargs):
        out = super().start_sprint(*args, **kwargs)
        self.save_snapshot()
        return out

    def complete_sprint(self, *args, **kwargs):
        out = super().complete_sprint(*args, **kwargs)
        self.save_snapshot()
        return out

    def add_checklist_item(self, *args, **kwargs):
        out = super().add_checklist_item(*args, **kwargs)
        self.save_snapshot()
        return out

    def update_checklist_item(self, *args, **kwargs):
        out = super().update_checklist_item(*args, **kwargs)
        self.save_snapshot()
        return out

    def delete_checklist_item(self, *args, **kwargs):
        out = super().delete_checklist_item(*args, **kwargs)
        self.save_snapshot()
        return out

    def delete_issue(self, *args, **kwargs):
        out = super().delete_issue(*args, **kwargs)
        self.save_snapshot()
        return out
