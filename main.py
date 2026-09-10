"""Universal entrypoint supporting ASGI/Uvicorn runtimes and zero-dependency Wasmer Edge environments."""
from datetime import datetime
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional
import urllib.parse
import uuid

# 1. Attempt standard ASGI FastAPI import
try:
    import uvicorn
    from backend.api.app import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    app = None

__all__ = ["app"] if app is not None else []


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = uuid.uuid4().hex[:16]
    pwd_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    expected, _ = hash_password(password, salt)
    return expected == pwd_hash


# 2. Standalone in-memory state for Wasmer Edge WebAssembly execution
class WasmerState:
    def __init__(self):
        self.reset()

    def reset(self):
        admin_hash, admin_salt = hash_password("admin123")
        alex_hash, alex_salt = hash_password("alex123")
        sam_hash, sam_salt = hash_password("sam123")

        self.users = [
            {
                "id": "user-admin",
                "username": "admin",
                "full_name": "System Admin",
                "email": "admin@orbit.local",
                "role": "ADMIN",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin",
                "password_hash": admin_hash,
                "password_salt": admin_salt
            },
            {
                "id": "user-alex",
                "username": "alex",
                "full_name": "Alex Chen",
                "email": "alex@orbit.local",
                "role": "MEMBER",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=alex",
                "password_hash": alex_hash,
                "password_salt": alex_salt
            },
            {
                "id": "user-sam",
                "username": "sam",
                "full_name": "Sam Taylor",
                "email": "sam@orbit.local",
                "role": "VIEWER",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=sam",
                "password_hash": sam_hash,
                "password_salt": sam_salt
            }
        ]
        self.sessions: Dict[str, dict] = {}
        self.projects = [
            {
                "id": "proj-proj",
                "key": "PROJ",
                "name": "Core Platform",
                "description": "Primary platform engineering workspace"
            },
            {
                "id": "proj-mobile",
                "key": "MOBILE",
                "name": "Mobile Experience",
                "description": "iOS and Android client applications"
            }
        ]
        self.default_columns = [
            {"id": "col-backlog", "name": "Backlog", "status": "BACKLOG", "order_index": 0},
            {"id": "col-todo", "name": "To Do", "status": "TODO", "order_index": 1},
            {"id": "col-progress", "name": "In Progress", "status": "IN_PROGRESS", "order_index": 2},
            {"id": "col-review", "name": "In Review", "status": "REVIEW", "order_index": 3},
            {"id": "col-done", "name": "Done", "status": "DONE", "order_index": 4}
        ]
        self.columns = {
            "proj-proj": [c.copy() for c in self.default_columns],
            "proj-mobile": [c.copy() for c in self.default_columns]
        }
        self.sprints = [
            {
                "id": "sprint-1",
                "name": "Sprint 1 - Foundation",
                "state": "ACTIVE",
                "project_id": "proj-proj",
                "capacity": 30,
                "committed_points": 24,
                "completed_points": 18,
                "goal": "Establish core architecture invariants and responsive Kanban board",
                "start_date": "2026-09-01",
                "end_date": "2026-09-14"
            },
            {
                "id": "sprint-2",
                "name": "Sprint 2 - Scale & Orbit",
                "state": "PLANNED",
                "project_id": "proj-proj",
                "capacity": 35,
                "committed_points": 0,
                "completed_points": 0,
                "goal": "Enterprise agile workflows, custom columns, and cloud deployment",
                "start_date": "2026-09-15",
                "end_date": "2026-09-29"
            }
        ]
        self.sprint_history = [
            {
                "sprint": {
                    "id": "sprint-0",
                    "name": "Sprint 0 - Genesis",
                    "state": "COMPLETED",
                    "project_id": "proj-proj",
                    "goal": "Repository setup and CI verification pipeline",
                    "completed_at": "2026-08-31T23:59:59Z"
                },
                "completed_count": 8,
                "incomplete_count": 0,
                "completion_percentage": 100
            }
        ]
        self.issues = [
            {
                "id": "iss-1",
                "key": "PROJ-1",
                "title": "Design Orbit Architecture Invariants",
                "description": "Implement state machine guards and memory persistence contracts.",
                "status": "DONE",
                "priority": "HIGH",
                "rank": "0|hzzzzz:",
                "project_id": "proj-proj",
                "assignee": "admin",
                "tags": ["core", "architecture"],
                "sprint_id": "sprint-1",
                "resolved_at": "2026-09-10T00:00:00Z",
                "attachments": [],
                "comments": [
                    {
                        "id": "comm-1",
                        "author_username": "admin",
                        "author_name": "System Admin",
                        "author_role": "ADMIN",
                        "content": "Initial architecture invariants validated against deterministic verification gates.",
                        "created_at": "2026-09-10T00:00:00Z",
                        "images": []
                    }
                ]
            },
            {
                "id": "iss-2",
                "key": "PROJ-2",
                "title": "Implement LexoRank Fractional Indexing",
                "description": "Enable collision-free card reordering with midpoint string generation.",
                "status": "IN_PROGRESS",
                "priority": "CRITICAL",
                "rank": "0|i00007:",
                "project_id": "proj-proj",
                "assignee": "alex",
                "tags": ["backend", "performance"],
                "sprint_id": "sprint-1",
                "attachments": [],
                "comments": [
                    {
                        "id": "comm-2",
                        "author_username": "alex",
                        "author_name": "Alex Chen",
                        "author_role": "MEMBER",
                        "content": "LexoRank generator implemented with base-36 mid-point string division.",
                        "created_at": "2026-09-10T01:00:00Z",
                        "images": []
                    }
                ]
            },
            {
                "id": "iss-3",
                "key": "PROJ-3",
                "title": "Glassmorphic Dark-Mode UI Theme",
                "description": "Elevate user experience with modern CSS design tokens and micro-animations.",
                "status": "TODO",
                "priority": "MEDIUM",
                "rank": "0|i0000e:",
                "project_id": "proj-proj",
                "assignee": "sam",
                "tags": ["frontend", "ui"],
                "sprint_id": "sprint-1",
                "attachments": [],
                "comments": []
            },
            {
                "id": "iss-4",
                "key": "PROJ-4",
                "title": "Configure Wasmer Edge Cloud Deployment",
                "description": "Ensure zero-dependency fallback for WebAssembly runtime.",
                "status": "IN_PROGRESS",
                "priority": "HIGH",
                "rank": "0|i0000l:",
                "project_id": "proj-proj",
                "assignee": "admin",
                "tags": ["cloud", "wasmer"],
                "sprint_id": "sprint-1",
                "attachments": [],
                "comments": []
            }
        ]
        self.issue_counter = 4
        self.notifications = [
            {
                "id": "notif-1",
                "user_id": "user-admin",
                "user_username": "admin",
                "username": "admin",
                "type": "STATUS_CHANGE",
                "title": "Welcome to Orbit",
                "message": "Platform running on Wasmer Edge with zero-dependency runtime.",
                "read": False,
                "issue_id": "iss-1",
                "issue_key": "PROJ-1",
                "created_at": "2026-09-10T00:00:00Z"
            },
            {
                "id": "notif-2",
                "user_id": "user-alex",
                "user_username": "alex",
                "username": "alex",
                "type": "ASSIGNED",
                "title": "Assigned to PROJ-2",
                "message": "You were assigned to PROJ-2: 'Implement LexoRank Fractional Indexing'",
                "read": False,
                "issue_id": "iss-2",
                "issue_key": "PROJ-2",
                "created_at": "2026-09-10T01:00:00Z"
            }
        ]

    def clean_user(self, u: dict) -> dict:
        return {k: v for k, v in u.items() if not k.startswith("password_")}

    def clean_users(self) -> List[dict]:
        return [self.clean_user(u) for u in self.users]

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        u_clean = (username or "").lower().strip()
        for u in self.users:
            if u["username"].lower() == u_clean:
                pwd_hash = u.get("password_hash")
                salt = u.get("password_salt")
                if pwd_hash and salt:
                    if verify_password(password, pwd_hash, salt):
                        return u
                elif password == f"{u_clean}123":
                    return u
        return None

    def create_session(self, user_id: str) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        self.sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        return token

    def get_session_user(self, token: Optional[str]) -> Optional[dict]:
        if not token or token not in self.sessions:
            return None
        user_id = self.sessions[token]["user_id"]
        for u in self.users:
            if u["id"] == user_id or u["username"].lower() == user_id.lower():
                return self.clean_user(u)
        return None

    def delete_session(self, token: Optional[str]) -> bool:
        if token and token in self.sessions:
            del self.sessions[token]
            return True
        return False

    def create_notification(
        self,
        username: str,
        notif_type: str,
        title: str,
        message: str,
        issue_id: str,
        issue_key: str
    ) -> dict:
        u_clean = username.lower().strip().lstrip("@")
        notif = {
            "id": f"notif-{uuid.uuid4().hex[:8]}",
            "user_id": f"user-{u_clean}",
            "user_username": u_clean,
            "username": u_clean,
            "type": notif_type,
            "title": title,
            "message": message,
            "issue_id": issue_id,
            "issue_key": issue_key,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "read": False
        }
        self.notifications.insert(0, notif)
        return notif

    def get_user_notifications(self, username: str) -> List[dict]:
        u_clean = username.lower().strip().lstrip("@")
        return [
            n for n in self.notifications
            if n.get("username", "").lower() == u_clean or n.get("user_username", "").lower() == u_clean
        ]

    def toggle_notification_read(self, notif_id: str, read_val: Optional[bool] = None) -> Optional[dict]:
        for n in self.notifications:
            if n["id"] == notif_id:
                if read_val is not None:
                    n["read"] = bool(read_val)
                else:
                    n["read"] = not n.get("read", False)
                return n
        return None

    def mark_all_notifications_read(self, username: str) -> int:
        u_clean = username.lower().strip().lstrip("@")
        count = 0
        for n in self.notifications:
            if (n.get("username", "").lower() == u_clean or n.get("user_username", "").lower() == u_clean) and not n.get("read", False):
                n["read"] = True
                count += 1
        return count

    def get_sprint_summary(self, sprint_id: str) -> Optional[dict]:
        sprint = next((s for s in self.sprints if s["id"] == sprint_id), None)
        if not sprint:
            return None
        sprint_issues = [i for i in self.issues if i.get("sprint_id") == sprint_id]
        completed = [i for i in sprint_issues if i.get("status") == "DONE"]
        incomplete = [i for i in sprint_issues if i.get("status") != "DONE"]
        pct = round((len(completed) / len(sprint_issues) * 100), 1) if sprint_issues else 0.0
        return {
            "sprint": sprint,
            "total_issues": len(sprint_issues),
            "completed_count": len(completed),
            "incomplete_count": len(incomplete),
            "completion_percentage": pct
        }

    def find_issue(self, issue_id: str) -> Optional[dict]:
        target = str(issue_id).strip()
        for i in self.issues:
            if i.get("id") == target or i.get("key", "").lower() == target.lower():
                return i
        m = re.match(r"^iss-(\d+)$", target, re.IGNORECASE)
        if m:
            num = m.group(1)
            for i in self.issues:
                if i.get("key", "").endswith(f"-{num}"):
                    return i
        return None


STATE = WasmerState()


# 3. Standalone zero-dependency handler for Wasmer Edge / WASIX
from http.server import SimpleHTTPRequestHandler, HTTPServer


class WasmerEdgeHandler(SimpleHTTPRequestHandler):
    """Zero-dependency HTTP request handler for Wasmer Edge WebAssembly execution."""

    def __init__(self, *args, **kwargs):
        self.root_dir = Path(__file__).resolve().parent
        self.frontend_dir = self.root_dir / "frontend"
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        sys.stderr.write(f"[WasmerEdge] {self.address_string()} - {format % args}\n")

    def _send_json(self, data, status: int = 200, cookies: Optional[List[str]] = None):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD")
        if cookies:
            for c in cookies:
                self.send_header("Set-Cookie", c)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw = self.rfile.read(content_length).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def _get_token(self) -> Optional[str]:
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            parts = cookie_header.split(";")
            for part in parts:
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    if k in ("session_id", "jira_session"):
                        return v.strip()
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1].strip()
        return None

    def _get_current_user(self) -> Optional[dict]:
        token = self._get_token()
        return STATE.get_session_user(token)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD")
        self.end_headers()

    def do_HEAD(self):
        path = self.path.split("?")[0]
        if path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json" if path == "/health" else "text/html")
            self.end_headers()
        else:
            self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # Health probe
        if raw_path == "/health":
            self._send_json({"status": "ok", "app": "orbit", "runtime": "wasmer-edge"})
            return

        # Auth & Current User
        if raw_path == "/api/auth/me":
            user = self._get_current_user()
            if not user:
                self._send_json({"detail": "Not authenticated"}, 401)
                return
            self._send_json(user, 200)
            return

        if raw_path == "/api/users":
            self._send_json(STATE.clean_users())
            return

        # Projects
        if raw_path == "/api/projects":
            self._send_json(STATE.projects)
            return

        # Board
        if raw_path == "/api/board":
            user = self._get_current_user()
            if not user:
                self._send_json({"detail": "Authentication required to view Kanban board"}, 401)
                return
            proj_id = query_params.get("project_id", ["proj-proj"])[0]
            proj = next((p for p in STATE.projects if p["id"] == proj_id), STATE.projects[0])
            cols = STATE.columns.get(proj_id, STATE.default_columns)
            board_issues = [i for i in STATE.issues if i.get("project_id") == proj_id]
            self._send_json({
                "board": {
                    "id": f"board-{proj_id}",
                    "project_id": proj_id,
                    "name": f"{proj['name']} Board",
                    "columns": cols
                },
                "project": proj,
                "issues": board_issues
            })
            return

        # Sprints
        if raw_path == "/api/sprints/history":
            self._send_json(STATE.sprint_history)
            return

        m_sprint_sum = re.match(r"^/api/sprints/([^/]+)/summary$", raw_path)
        if m_sprint_sum:
            sprint_id = m_sprint_sum.group(1)
            summary = STATE.get_sprint_summary(sprint_id)
            if not summary:
                self._send_json({"detail": "Sprint not found"}, 404)
                return
            self._send_json(summary, 200)
            return

        if raw_path == "/api/sprints":
            proj_id = query_params.get("project_id", [None])[0]
            sprints = [s for s in STATE.sprints if not proj_id or s.get("project_id") == proj_id]
            self._send_json(sprints)
            return

        # Comments on Issue
        m_comm_get = re.match(r"^/api/issues/([^/]+)/comments$", raw_path)
        if m_comm_get:
            issue_id = m_comm_get.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            self._send_json(issue.get("comments", []), 200)
            return

        # Issues
        if raw_path == "/api/issues":
            proj_id = query_params.get("project_id", [None])[0]
            issues = [i for i in STATE.issues if not proj_id or i.get("project_id") == proj_id]
            self._send_json(issues)
            return

        # Single Issue Details
        m_issue = re.match(r"^/api/issues/([^/]+)$", raw_path)
        if m_issue:
            issue_id = m_issue.group(1)
            issue = STATE.find_issue(issue_id)
            if issue:
                self._send_json(issue, 200)
            else:
                self._send_json({"detail": "Issue not found"}, 404)
            return

        # Notifications
        if raw_path == "/api/notifications":
            caller = self._get_current_user()
            query_user = query_params.get("username", [None])[0]
            target_user = query_user or (caller["username"] if caller else None)
            if target_user:
                notifs = STATE.get_user_notifications(target_user)
            else:
                notifs = STATE.notifications
            self._send_json(notifs, 200)
            return

        # Strictly block undefined /api/... paths from returning index.html
        if raw_path.startswith("/api/"):
            self._send_json({"detail": "Not found"}, 404)
            return

        # Static assets and index.html routing
        file_target = self.frontend_dir / "index.html"
        if raw_path.startswith("/static/"):
            rel = raw_path[len("/static/"):]
            file_target = self.frontend_dir / rel
        elif raw_path != "/":
            possible_target = self.frontend_dir / raw_path.lstrip("/")
            if possible_target.exists() and possible_target.is_file():
                file_target = possible_target

        if file_target.exists() and file_target.is_file():
            content_type, _ = mimetypes.guess_type(str(file_target))
            if not content_type:
                content_type = "application/octet-stream"
            content = file_target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            index_file = self.frontend_dir / "index.html"
            if index_file.exists():
                content = index_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path

        if raw_path == "/api/auth/login":
            body = self._read_json()
            username = (body.get("username") or "").strip()
            password = (body.get("password") or "").strip()
            user = STATE.authenticate(username, password)
            if not user:
                self._send_json({"detail": "Invalid username or password"}, 401)
                return

            token = STATE.create_session(user["id"])
            cookies = [
                f"session_id={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800",
                f"jira_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800"
            ]
            self._send_json(STATE.clean_user(user), 200, cookies=cookies)
            return

        if raw_path == "/api/auth/logout":
            token = self._get_token()
            if token:
                STATE.delete_session(token)
            cookies = [
                "session_id=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT",
                "jira_session=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
            ]
            self._send_json({"status": "ok", "message": "Logged out successfully"}, 200, cookies=cookies)
            return

        if raw_path == "/api/projects":
            body = self._read_json()
            key = (body.get("key") or "PRJ").upper()
            name = body.get("name") or "New Project"
            desc = body.get("description", "")
            proj_id = f"proj-{key.lower()}"
            cols = body.get("columns") or [c.copy() for c in STATE.default_columns]
            new_proj = {"id": proj_id, "key": key, "name": name, "description": desc}
            STATE.projects.append(new_proj)
            STATE.columns[proj_id] = cols
            self._send_json(new_proj, 201)
            return

        m_cols = re.match(r"^/api/board/([^/]+)/columns$", raw_path)
        if m_cols:
            proj_id = m_cols.group(1)
            body = self._read_json()
            cols = body.get("columns", [])
            STATE.columns[proj_id] = cols
            self._send_json({"id": f"board-{proj_id}", "project_id": proj_id, "columns": cols}, 200)
            return

        if raw_path == "/api/issues":
            body = self._read_json()
            STATE.issue_counter += 1
            proj_id = body.get("project_id") or "proj-proj"
            proj = next((p for p in STATE.projects if p["id"] == proj_id), STATE.projects[0])
            issue_key = f"{proj['key']}-{STATE.issue_counter}"
            issue_id = f"iss-{STATE.issue_counter}"
            assignee = body.get("assignee")
            new_issue = {
                "id": issue_id,
                "key": issue_key,
                "project_id": proj_id,
                "sprint_id": body.get("sprint_id"),
                "title": body.get("title", "Untitled"),
                "description": body.get("description", ""),
                "status": body.get("status", "TODO"),
                "priority": body.get("priority", "MEDIUM"),
                "rank": f"0|i{STATE.issue_counter:05d}:",
                "assignee": assignee,
                "tags": body.get("tags", []),
                "attachments": [],
                "comments": []
            }
            STATE.issues.append(new_issue)

            # Trigger assignment notification if assigned on creation
            if assignee:
                STATE.create_notification(
                    username=assignee,
                    notif_type="ASSIGNED",
                    title=f"Assigned to {issue_key}",
                    message=f"You were assigned to {issue_key}: '{new_issue['title']}'",
                    issue_id=issue_id,
                    issue_key=issue_key
                )

            self._send_json(new_issue, 201)
            return

        m_move = re.match(r"^/api/issues/([^/]+)/move$", raw_path)
        if m_move:
            issue_id = m_move.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            body = self._read_json()
            caller = self._get_current_user()
            mover = caller["username"] if caller else "admin"

            old_status = issue.get("status")
            new_status = body.get("new_status")
            if new_status and new_status != old_status:
                issue["status"] = new_status
                if new_status == "DONE":
                    issue["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                elif old_status == "DONE":
                    issue.pop("resolved_at", None)

                # Trigger status change notification
                assignee = issue.get("assignee")
                if assignee and assignee.lower() != mover.lower():
                    STATE.create_notification(
                        username=assignee,
                        notif_type="STATUS_CHANGE",
                        title=f"Status Change: {issue['key']}",
                        message=f"{issue['key']} was moved from {old_status} to {new_status} by {mover}.",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            if body.get("next_rank"):
                issue["rank"] = body["next_rank"]
            self._send_json(issue, 200)
            return

        m_comm = re.match(r"^/api/issues/([^/]+)/comments$", raw_path)
        if m_comm:
            issue_id = m_comm.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            body = self._read_json()
            caller = self._get_current_user()
            author_username = caller["username"] if caller else (body.get("author_username") or "admin")
            author_name = caller["full_name"] if caller else (body.get("author_name") or "System Admin")
            author_role = caller["role"] if caller else (body.get("author_role") or "ADMIN")
            content = body.get("content", "")

            # Extract @mentions
            mention_matches = re.findall(r"@([a-zA-Z0-9_-]+)", content)
            mentions = list(set([m.lower() for m in mention_matches]))

            new_comm = {
                "id": f"comm-{uuid.uuid4().hex[:8]}",
                "issue_id": issue["id"],
                "author_username": author_username,
                "author_name": author_name,
                "author_role": author_role,
                "content": content,
                "mentions": mentions,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "images": body.get("images", [])
            }
            issue.setdefault("comments", []).append(new_comm)

            snippet = content[:60] + "..." if len(content) > 60 else content

            # Notify mentioned users
            for m in mentions:
                if m != author_username.lower():
                    STATE.create_notification(
                        username=m,
                        notif_type="MENTION",
                        title=f"{author_name} mentioned you in {issue['key']}",
                        message=f"{author_name} tagged you: \"{snippet}\"",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            # Notify assignee if not mentioned and not author
            assignee = issue.get("assignee")
            if assignee:
                assignee_clean = assignee.lower().lstrip("@")
                if assignee_clean != author_username.lower() and assignee_clean not in mentions:
                    STATE.create_notification(
                        username=assignee_clean,
                        notif_type="COMMENT",
                        title=f"New comment on {issue['key']}",
                        message=f"{author_name} commented on {issue['key']}: \"{snippet}\"",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            self._send_json(new_comm, 201)
            return

        m_att = re.match(r"^/api/issues/([^/]+)/attachments$", raw_path)
        if m_att:
            issue_id = m_att.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            att = {
                "id": f"att-{uuid.uuid4().hex[:8]}",
                "filename": "attachment.png",
                "file_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"
            }
            issue.setdefault("attachments", []).append(att)

            caller = self._get_current_user()
            uploader = caller["username"] if caller else "admin"
            assignee = issue.get("assignee")
            if assignee and assignee.lower() != uploader.lower():
                STATE.create_notification(
                    username=assignee,
                    notif_type="UPDATE",
                    title=f"New Attachment: {issue['key']}",
                    message=f"{uploader} uploaded attachment to {issue['key']}.",
                    issue_id=issue["id"],
                    issue_key=issue["key"]
                )

            self._send_json(att, 201)
            return

        if raw_path == "/api/comments/upload-image":
            self._send_json({"url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800"}, 200)
            return

        if raw_path == "/api/sprints":
            body = self._read_json()
            sprint_id = f"sprint-{len(STATE.sprints)+1}"
            new_sprint = {
                "id": sprint_id,
                "name": body.get("name", f"Sprint {len(STATE.sprints)+1}"),
                "state": "PLANNED",
                "project_id": body.get("project_id", "proj-proj"),
                "capacity": 30,
                "committed_points": 0,
                "completed_points": 0,
                "goal": body.get("goal", ""),
                "start_date": body.get("start_date"),
                "end_date": body.get("end_date")
            }
            STATE.sprints.append(new_sprint)
            self._send_json(new_sprint, 201)
            return

        m_start = re.match(r"^/api/sprints/([^/]+)/start$", raw_path)
        if m_start:
            sprint_id = m_start.group(1)
            sprint = next((s for s in STATE.sprints if s["id"] == sprint_id), None)
            if not sprint:
                self._send_json({"detail": "Sprint not found"}, 404)
                return
            sprint["state"] = "ACTIVE"
            self._send_json(sprint, 200)
            return

        m_comp = re.match(r"^/api/sprints/([^/]+)/complete$", raw_path)
        if m_comp:
            sprint_id = m_comp.group(1)
            sprint = next((s for s in STATE.sprints if s["id"] == sprint_id), None)
            if not sprint:
                self._send_json({"detail": "Sprint not found"}, 404)
                return
            sprint["state"] = "COMPLETED"
            sprint["completed_at"] = datetime.utcnow().isoformat() + "Z"
            sprint_issues = [i for i in STATE.issues if i.get("sprint_id") == sprint_id]
            done_count = len([i for i in sprint_issues if i.get("status") == "DONE"])
            incomplete_count = len(sprint_issues) - done_count
            pct = round((done_count / len(sprint_issues) * 100) if sprint_issues else 100)
            STATE.sprint_history.insert(0, {
                "sprint": sprint,
                "completed_count": done_count,
                "incomplete_count": incomplete_count,
                "completion_percentage": pct
            })
            self._send_json(sprint, 200)
            return

        m_notif = re.match(r"^/api/notifications/([^/]+)/toggle-read$", raw_path)
        if m_notif:
            notif_id = m_notif.group(1)
            body = self._read_json()
            read_val = body.get("read") if "read" in body else None
            notif = STATE.toggle_notification_read(notif_id, read_val)
            if not notif:
                self._send_json({"detail": "Notification not found"}, 404)
                return
            self._send_json(notif, 200)
            return

        if raw_path == "/api/notifications/mark-all-read":
            caller = self._get_current_user()
            username = caller["username"] if caller else "admin"
            count = STATE.mark_all_notifications_read(username)
            self._send_json({"status": "ok", "marked_count": count}, 200)
            return

        if raw_path == "/api/users":
            body = self._read_json()
            username = (body.get("username") or "user").strip()
            password = body.get("password") or f"{username.lower()}123"
            pwd_hash, salt = hash_password(password)
            new_user = {
                "id": f"user-{username.lower()}",
                "username": username,
                "full_name": body.get("full_name", username),
                "email": body.get("email", f"{username}@orbit.local"),
                "role": body.get("role", "MEMBER"),
                "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                "password_hash": pwd_hash,
                "password_salt": salt
            }
            STATE.users.append(new_user)
            self._send_json(STATE.clean_user(new_user), 201)
            return

        if raw_path.startswith("/api/"):
            self._send_json({"detail": "Not found"}, 404)
            return

        self._send_json({"status": "created"}, 201)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path

        m_cols = re.match(r"^/api/board/([^/]+)/columns$", raw_path)
        if m_cols:
            proj_id = m_cols.group(1)
            body = self._read_json()
            cols = body.get("columns", [])
            STATE.columns[proj_id] = cols
            self._send_json({"id": f"board-{proj_id}", "project_id": proj_id, "columns": cols}, 200)
            return

        if raw_path.startswith("/api/"):
            self._send_json({"detail": "Not found"}, 404)
            return

        self._send_json({"status": "updated"}, 200)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path

        m_move = re.match(r"^/api/issues/([^/]+)/move$", raw_path)
        if m_move:
            issue_id = m_move.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            body = self._read_json()
            caller = self._get_current_user()
            mover = caller["username"] if caller else "admin"

            old_status = issue.get("status")
            new_status = body.get("new_status")
            if new_status and new_status != old_status:
                issue["status"] = new_status
                if new_status == "DONE":
                    issue["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                elif old_status == "DONE":
                    issue.pop("resolved_at", None)

                assignee = issue.get("assignee")
                if assignee and assignee.lower() != mover.lower():
                    STATE.create_notification(
                        username=assignee,
                        notif_type="STATUS_CHANGE",
                        title=f"Status Change: {issue['key']}",
                        message=f"{issue['key']} was moved from {old_status} to {new_status} by {mover}.",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            if body.get("next_rank"):
                issue["rank"] = body["next_rank"]
            self._send_json(issue, 200)
            return

        m_issue = re.match(r"^/api/issues/([^/]+)$", raw_path)
        if m_issue:
            issue_id = m_issue.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            body = self._read_json()
            caller = self._get_current_user()
            updater = caller["username"] if caller else "admin"

            old_assignee = issue.get("assignee")
            old_status = issue.get("status")

            for field in ("title", "description", "priority", "tags", "sprint_id"):
                if field in body:
                    issue[field] = body[field]

            if "status" in body and body["status"] != old_status:
                new_status = body["status"]
                issue["status"] = new_status
                if new_status == "DONE":
                    issue["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                elif old_status == "DONE":
                    issue.pop("resolved_at", None)

                assignee = issue.get("assignee")
                if assignee and assignee.lower() != updater.lower():
                    STATE.create_notification(
                        username=assignee,
                        notif_type="STATUS_CHANGE",
                        title=f"Status Change: {issue['key']}",
                        message=f"{issue['key']} was moved from {old_status} to {new_status} by {updater}.",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            if "assignee" in body and body["assignee"] != old_assignee:
                new_assignee = body["assignee"]
                issue["assignee"] = new_assignee
                if new_assignee:
                    STATE.create_notification(
                        username=new_assignee,
                        notif_type="ASSIGNED",
                        title=f"Assigned to {issue['key']}",
                        message=f"You were assigned to {issue['key']}: '{issue['title']}'",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )
                if old_assignee:
                    STATE.create_notification(
                        username=old_assignee,
                        notif_type="UNASSIGNED",
                        title=f"Unassigned from {issue['key']}",
                        message=f"You were unassigned from {issue['key']}: '{issue['title']}' by {updater}.",
                        issue_id=issue["id"],
                        issue_key=issue["key"]
                    )

            self._send_json(issue, 200)
            return

        m_role = re.match(r"^/api/users/([^/]+)/role$", raw_path)
        if m_role:
            user_id = m_role.group(1)
            user = next((u for u in STATE.users if u["id"] == user_id or u["username"].lower() == user_id.lower()), None)
            if not user:
                self._send_json({"detail": "User not found"}, 404)
                return
            body = self._read_json()
            if "role" in body:
                user["role"] = body["role"]
            self._send_json(STATE.clean_user(user), 200)
            return

        m_name = re.match(r"^/api/users/([^/]+)/name$", raw_path)
        if m_name:
            user_id = m_name.group(1)
            user = next((u for u in STATE.users if u["id"] == user_id or u["username"].lower() == user_id.lower()), None)
            if not user:
                self._send_json({"detail": "User not found"}, 404)
                return
            body = self._read_json()
            if "full_name" in body:
                user["full_name"] = body["full_name"]
            self._send_json(STATE.clean_user(user), 200)
            return

        m_pwd = re.match(r"^/api/users/([^/]+)/password$", raw_path)
        if m_pwd:
            user_id = m_pwd.group(1)
            user = next((u for u in STATE.users if u["id"] == user_id or u["username"].lower() == user_id.lower()), None)
            if not user:
                self._send_json({"detail": "User not found"}, 404)
                return
            body = self._read_json()
            new_pwd = body.get("new_password")
            if not new_pwd or len(new_pwd) < 4:
                self._send_json({"detail": "Password must be at least 4 characters"}, 400)
                return
            pwd_hash, salt = hash_password(new_pwd)
            user["password_hash"] = pwd_hash
            user["password_salt"] = salt
            self._send_json(STATE.clean_user(user), 200)
            return

        m_proj_cols = re.match(r"^/api/projects/([^/]+)/columns$", raw_path)
        if m_proj_cols:
            proj_id = m_proj_cols.group(1)
            body = self._read_json()
            cols = body.get("columns", [])
            STATE.columns[proj_id] = cols
            self._send_json({"id": f"board-{proj_id}", "project_id": proj_id, "columns": cols}, 200)
            return

        m_notif = re.match(r"^/api/notifications/([^/]+)/toggle-read$", raw_path)
        if m_notif:
            notif_id = m_notif.group(1)
            body = self._read_json()
            read_val = body.get("read") if "read" in body else None
            notif = STATE.toggle_notification_read(notif_id, read_val)
            if not notif:
                self._send_json({"detail": "Notification not found"}, 404)
                return
            self._send_json(notif, 200)
            return

        if raw_path.startswith("/api/"):
            self._send_json({"detail": "Not found"}, 404)
            return

        self._send_json({"status": "updated"}, 200)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path

        m_del_att = re.match(r"^/api/issues/([^/]+)/attachments/([^/]+)$", raw_path)
        if m_del_att:
            issue_id, att_id = m_del_att.group(1), m_del_att.group(2)
            issue = STATE.find_issue(issue_id)
            if issue and "attachments" in issue:
                issue["attachments"] = [a for a in issue["attachments"] if a.get("id") != att_id]
            self._send_json({"status": "deleted"}, 200)
            return

        m_del_issue = re.match(r"^/api/issues/([^/]+)$", raw_path)
        if m_del_issue:
            issue_id = m_del_issue.group(1)
            issue = STATE.find_issue(issue_id)
            if not issue:
                self._send_json({"detail": "Issue not found"}, 404)
                return
            STATE.issues = [i for i in STATE.issues if i.get("id") != issue["id"]]
            self._send_json({"status": "deleted", "id": issue["id"]}, 200)
            return

        if raw_path.startswith("/api/"):
            self._send_json({"status": "deleted"}, 200)
            return

        self._send_json({"status": "deleted"}, 200)


def start():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    if HAS_FASTAPI:
        print(f"Starting Orbit with Uvicorn ASGI on http://{host}:{port}")
        uvicorn.run("main:app", host=host, port=port, reload=False)
    else:
        print(f"Starting Orbit with Wasmer Edge Native HTTP Server on http://{host}:{port}")
        server = HTTPServer((host, port), WasmerEdgeHandler)
        server.serve_forever()


if __name__ == "__main__":
    start()
