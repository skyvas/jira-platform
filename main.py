"""Universal entrypoint supporting ASGI/Uvicorn runtimes and zero-dependency Wasmer Edge environments."""
from datetime import datetime
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
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


# 2. Standalone in-memory state for Wasmer Edge WebAssembly execution
class WasmerState:
    def __init__(self):
        self.users = [
            {
                "id": "user-admin",
                "username": "admin",
                "full_name": "System Admin",
                "email": "admin@orbit.local",
                "role": "ADMIN",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin"
            },
            {
                "id": "user-alex",
                "username": "alex",
                "full_name": "Alex Chen",
                "email": "alex@orbit.local",
                "role": "MEMBER",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=alex"
            },
            {
                "id": "user-sam",
                "username": "sam",
                "full_name": "Sam Taylor",
                "email": "sam@orbit.local",
                "role": "VIEWER",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=sam"
            }
        ]
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
                "username": "admin",
                "title": "Welcome to Orbit",
                "message": "Platform running on Wasmer Edge with zero-dependency runtime.",
                "read": False,
                "issue_id": "iss-1",
                "created_at": "2026-09-10T00:00:00Z"
            }
        ]

    def find_issue(self, issue_id: str):
        target = issue_id.strip()
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

    def _send_json(self, data, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD")
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

        # Auth & Users
        if raw_path == "/api/auth/me":
            self._send_json(STATE.users[0])
            return

        if raw_path == "/api/users":
            self._send_json(STATE.users)
            return

        # Projects
        if raw_path == "/api/projects":
            self._send_json(STATE.projects)
            return

        # Board
        if raw_path == "/api/board":
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

        if raw_path == "/api/sprints":
            proj_id = query_params.get("project_id", [None])[0]
            sprints = [s for s in STATE.sprints if not proj_id or s.get("project_id") == proj_id]
            self._send_json(sprints)
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
            self._send_json(STATE.notifications)
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
            username = (body.get("username") or "admin").lower()
            user = next((u for u in STATE.users if u["username"].lower() == username), STATE.users[0])
            self._send_json(user, 200)
            return

        if raw_path == "/api/auth/logout":
            self._send_json({"status": "ok", "message": "Logged out successfully"}, 200)
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
                "assignee": body.get("assignee"),
                "tags": body.get("tags", []),
                "attachments": [],
                "comments": []
            }
            STATE.issues.append(new_issue)
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
            new_status = body.get("new_status")
            if new_status:
                issue["status"] = new_status
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
            new_comm = {
                "id": f"comm-{uuid.uuid4().hex[:8]}",
                "issue_id": issue["id"],
                "author_username": "admin",
                "author_name": "System Admin",
                "author_role": "ADMIN",
                "content": body.get("content", ""),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "images": body.get("images", [])
            }
            issue.setdefault("comments", []).append(new_comm)
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
            notif = next((n for n in STATE.notifications if n["id"] == notif_id), None)
            if not notif:
                self._send_json({"detail": "Notification not found"}, 404)
                return
            notif["read"] = not notif.get("read", False)
            self._send_json(notif, 200)
            return

        if raw_path == "/api/notifications/mark-all-read":
            for n in STATE.notifications:
                n["read"] = True
            self._send_json({"status": "ok", "marked_count": len(STATE.notifications)}, 200)
            return

        if raw_path == "/api/users":
            body = self._read_json()
            username = (body.get("username") or "user").strip()
            new_user = {
                "id": f"user-{username.lower()}",
                "username": username,
                "full_name": body.get("full_name", username),
                "email": body.get("email", f"{username}@orbit.local"),
                "role": body.get("role", "MEMBER"),
                "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
            }
            STATE.users.append(new_user)
            self._send_json(new_user, 201)
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
            new_status = body.get("new_status")
            if new_status:
                issue["status"] = new_status
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
            for field in ("title", "description", "priority", "status", "assignee", "tags", "sprint_id"):
                if field in body:
                    issue[field] = body[field]
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
            self._send_json(user, 200)
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
            self._send_json(user, 200)
            return

        m_pwd = re.match(r"^/api/users/([^/]+)/password$", raw_path)
        if m_pwd:
            user_id = m_pwd.group(1)
            user = next((u for u in STATE.users if u["id"] == user_id or u["username"].lower() == user_id.lower()), None)
            if not user:
                self._send_json({"detail": "User not found"}, 404)
                return
            self._send_json(user, 200)
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
            notif = next((n for n in STATE.notifications if n["id"] == notif_id), None)
            if not notif:
                self._send_json({"detail": "Notification not found"}, 404)
                return
            notif["read"] = not notif.get("read", False)
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
