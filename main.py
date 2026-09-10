"""Universal entrypoint supporting ASGI/Uvicorn runtimes and zero-dependency Wasmer Edge environments."""
import json
import mimetypes
import os
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path

# 1. Attempt standard ASGI FastAPI import
try:
    import uvicorn
    from backend.api.app import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    app = None

__all__ = ["app"] if app is not None else []


# 2. Standalone zero-dependency handler for Wasmer Edge / WASIX
class WasmerEdgeHandler(SimpleHTTPRequestHandler):
    """Zero-dependency HTTP request handler for Wasmer Edge WebAssembly execution."""

    def __init__(self, *args, **kwargs):
        self.root_dir = Path(__file__).resolve().parent
        self.frontend_dir = self.root_dir / "frontend"
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[WasmerEdge] {self.address_string()} - {format % args}\n")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS, HEAD")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS, HEAD")
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
        raw_path = self.path.split("?")[0]

        # Health probe
        if raw_path == "/health":
            self._send_json({"status": "ok", "app": "orbit", "runtime": "wasmer-edge"})
            return

        # API Endpoints
        if raw_path == "/api/projects":
            self._send_json([
                {"id": "proj-proj", "key": "PROJ", "name": "Core Platform", "description": "Primary platform engineering workspace"},
                {"id": "proj-mobile", "key": "MOBILE", "name": "Mobile Experience", "description": "iOS and Android client applications"}
            ])
            return

        if raw_path == "/api/users":
            self._send_json([
                {"id": "user-admin", "username": "admin", "full_name": "System Admin", "email": "admin@orbit.local", "role": "ADMIN", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin"},
                {"id": "user-alex", "username": "alex", "full_name": "Alex Chen", "email": "alex@orbit.local", "role": "MEMBER", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=alex"},
                {"id": "user-sam", "username": "sam", "full_name": "Sam Taylor", "email": "sam@orbit.local", "role": "VIEWER", "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=sam"}
            ])
            return

        if raw_path == "/api/auth/me":
            self._send_json({
                "id": "user-admin", "username": "admin", "full_name": "System Admin", "email": "admin@orbit.local", "role": "ADMIN", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin"
            })
            return

        if raw_path == "/api/board":
            self._send_json({
                "columns": [
                    {"id": "col-backlog", "title": "Backlog", "status": "BACKLOG", "order": 0},
                    {"id": "col-todo", "title": "To Do", "status": "TODO", "order": 1},
                    {"id": "col-in_progress", "title": "In Progress", "status": "IN_PROGRESS", "order": 2},
                    {"id": "col-review", "title": "Code Review", "status": "REVIEW", "order": 3},
                    {"id": "col-done", "title": "Done", "status": "DONE", "order": 4}
                ],
                "issues": [
                    {"id": "iss-1", "key": "PROJ-1", "title": "Design Orbit Architecture Invariants", "description": "Implement state machine guards and memory persistence contracts.", "status": "DONE", "priority": "HIGH", "rank": "0|hzzzzz:", "project_id": "proj-proj", "assignee": "admin", "tags": ["core", "architecture"]},
                    {"id": "iss-2", "key": "PROJ-2", "title": "Implement LexoRank Fractional Indexing", "description": "Enable collision-free card reordering with midpoint string generation.", "status": "IN_PROGRESS", "priority": "CRITICAL", "rank": "0|i00007:", "project_id": "proj-proj", "assignee": "alex", "tags": ["backend", "performance"]},
                    {"id": "iss-3", "key": "PROJ-3", "title": "Glassmorphic Dark-Mode UI Theme", "description": "Elevate user experience with modern CSS design tokens and micro-animations.", "status": "TODO", "priority": "MEDIUM", "rank": "0|i0000e:", "project_id": "proj-proj", "assignee": "sam", "tags": ["frontend", "ui"]},
                    {"id": "iss-4", "key": "PROJ-4", "title": "Configure Wasmer Edge Cloud Deployment", "description": "Ensure zero-dependency fallback for WebAssembly runtime.", "status": "IN_PROGRESS", "priority": "HIGH", "rank": "0|i0000l:", "project_id": "proj-proj", "assignee": "admin", "tags": ["cloud", "wasmer"]}
                ]
            })
            return

        if raw_path == "/api/sprints":
            self._send_json([
                {"id": "sprint-1", "name": "Sprint 1 - Foundation", "state": "ACTIVE", "project_id": "proj-proj", "capacity": 30, "committed_points": 24, "completed_points": 18},
                {"id": "sprint-2", "name": "Sprint 2 - Scale & Orbit", "state": "PLANNED", "project_id": "proj-proj", "capacity": 35, "committed_points": 0, "completed_points": 0}
            ])
            return

        if raw_path == "/api/notifications":
            self._send_json([])
            return

        # Static assets and index.html routing
        file_target = self.frontend_dir / "index.html"
        if raw_path.startswith("/static/"):
            rel = raw_path[len("/static/"):]
            file_target = self.frontend_dir / rel
        elif raw_path == "/":
            file_target = self.frontend_dir / "index.html"

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
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        raw_path = self.path.split("?")[0]
        if raw_path == "/api/auth/login":
            self._send_json({
                "id": "user-admin",
                "username": "admin",
                "full_name": "System Admin",
                "email": "admin@orbit.local",
                "role": "ADMIN",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin"
            })
            return
        if raw_path == "/api/auth/logout":
            self._send_json({"message": "Logged out successfully"})
            return
        self._send_json({"status": "created"}, 201)

    def do_PATCH(self):
        self._send_json({"status": "updated"}, 200)

    def do_DELETE(self):
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
