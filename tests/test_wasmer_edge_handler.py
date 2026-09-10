"""Unit tests for WasmerEdgeHandler zero-dependency runtime."""
import json
import threading
from http.server import HTTPServer
import urllib.request
import urllib.error
import pytest

from main import WasmerEdgeHandler, STATE


@pytest.fixture(scope="module")
def wasmer_server():
    server = HTTPServer(("127.0.0.1", 0), WasmerEdgeHandler)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield base_url

    server.shutdown()
    server.server_close()


def test_wasmer_health_endpoint(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type").startswith("application/json")
        data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        assert data["runtime"] == "wasmer-edge"


def test_wasmer_issue_detail_json_never_html(wasmer_server):
    """Verify that clicking a card to get issue details returns valid JSON and never HTML."""
    req = urllib.request.Request(f"{wasmer_server}/api/issues/iss-1")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type").startswith("application/json")
        data = json.loads(resp.read().decode())
        assert data["id"] == "iss-1"
        assert data["key"] == "PROJ-1"
        assert "comments" in data
        assert "attachments" in data


def test_wasmer_board_endpoint_structure(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/api/board?project_id=proj-proj")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "board" in data
        assert "columns" in data["board"]
        assert len(data["board"]["columns"]) >= 5
        assert "issues" in data
        assert len(data["issues"]) >= 4


def test_wasmer_create_issue_workflow(wasmer_server):
    payload = json.dumps({
        "project_id": "proj-proj",
        "title": "Edge Test Issue",
        "description": "Created during edge test",
        "priority": "HIGH",
        "status": "TODO",
        "assignee": "alex",
        "tags": ["edge", "test"]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode())
        assert data["title"] == "Edge Test Issue"
        assert data["key"].startswith("PROJ-")
        new_id = data["id"]

    # Retrieve created issue
    get_req = urllib.request.Request(f"{wasmer_server}/api/issues/{new_id}")
    with urllib.request.urlopen(get_req) as resp:
        assert resp.status == 200
        issue = json.loads(resp.read().decode())
        assert issue["title"] == "Edge Test Issue"


def test_wasmer_move_issue_workflow(wasmer_server):
    payload = json.dumps({"new_status": "IN_PROGRESS"}).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues/iss-1/move",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "IN_PROGRESS"


def test_wasmer_comment_workflow(wasmer_server):
    payload = json.dumps({"content": "New test comment"}).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues/iss-1/comments",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode())
        assert data["content"] == "New test comment"


def test_wasmer_sprint_lifecycle_and_history(wasmer_server):
    # Start sprint
    start_req = urllib.request.Request(
        f"{wasmer_server}/api/sprints/sprint-2/start",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(start_req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["state"] == "ACTIVE"

    # Complete sprint
    comp_req = urllib.request.Request(
        f"{wasmer_server}/api/sprints/sprint-2/complete",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(comp_req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["state"] == "COMPLETED"

    # Check history
    hist_req = urllib.request.Request(f"{wasmer_server}/api/sprints/history")
    with urllib.request.urlopen(hist_req) as resp:
        assert resp.status == 200
        history = json.loads(resp.read().decode())
        assert len(history) >= 2


def test_wasmer_api_404_returns_json_not_html(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/api/unknown-route")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    err_resp = exc_info.value
    assert err_resp.status == 404
    assert err_resp.headers.get("Content-Type").startswith("application/json")
    data = json.loads(err_resp.read().decode())
    assert "detail" in data
