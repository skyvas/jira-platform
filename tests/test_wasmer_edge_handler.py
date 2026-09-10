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


def _login(base_url: str, username: str = "admin", password: str = "admin123") -> tuple[dict, str]:
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        cookie = resp.headers.get("Set-Cookie", "")
        data = json.loads(resp.read().decode())
        # extract session_id token
        token = ""
        for part in cookie.split(";"):
            if "session_id=" in part:
                token = part.split("session_id=")[1].strip()
                break
        return data, f"session_id={token}"


def test_wasmer_health_endpoint(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type").startswith("application/json")
        data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        assert data["runtime"] == "wasmer-edge"


def test_wasmer_auth_unauthenticated_me_returns_401(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/api/auth/me")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.status == 401
    data = json.loads(exc_info.value.read().decode())
    assert data["detail"] == "Not authenticated"


def test_wasmer_auth_login_invalid_password_returns_401(wasmer_server):
    payload = json.dumps({"username": "admin", "password": "wrongpassword"}).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.status == 401
    data = json.loads(exc_info.value.read().decode())
    assert data["detail"] == "Invalid username or password"


def test_wasmer_auth_login_and_me_lifecycle(wasmer_server):
    # 1. Login as admin
    user, cookie_header = _login(wasmer_server, "admin", "admin123")
    assert user["username"] == "admin"
    assert user["role"] == "ADMIN"
    assert "password_hash" not in user

    # 2. Call /api/auth/me with cookie
    req = urllib.request.Request(f"{wasmer_server}/api/auth/me", headers={"Cookie": cookie_header})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        me = json.loads(resp.read().decode())
        assert me["username"] == "admin"

    # 3. Call /api/auth/logout
    logout_req = urllib.request.Request(
        f"{wasmer_server}/api/auth/logout",
        data=b"{}",
        headers={"Content-Type": "application/json", "Cookie": cookie_header},
        method="POST"
    )
    with urllib.request.urlopen(logout_req) as resp:
        assert resp.status == 200
        set_cookie = resp.headers.get("Set-Cookie", "")
        assert "Max-Age=0" in set_cookie

    # 4. Access /api/auth/me after logout -> strictly 401
    me_after = urllib.request.Request(f"{wasmer_server}/api/auth/me", headers={"Cookie": cookie_header})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(me_after)
    assert exc_info.value.status == 401


def test_wasmer_board_unauthenticated_returns_401(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/api/board?project_id=proj-proj")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.status == 401


def test_wasmer_board_endpoint_structure(wasmer_server):
    _, cookie_header = _login(wasmer_server, "admin", "admin123")
    req = urllib.request.Request(
        f"{wasmer_server}/api/board?project_id=proj-proj",
        headers={"Cookie": cookie_header}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "board" in data
        assert "columns" in data["board"]
        assert len(data["board"]["columns"]) >= 5
        assert "issues" in data
        assert len(data["issues"]) >= 4


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


def test_wasmer_comment_workflow_and_get_comments(wasmer_server):
    payload = json.dumps({"content": "New test comment with @alex mention"}).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues/iss-1/comments",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode())
        assert data["content"] == "New test comment with @alex mention"

    # GET /api/issues/{id}/comments
    get_comm_req = urllib.request.Request(f"{wasmer_server}/api/issues/iss-1/comments")
    with urllib.request.urlopen(get_comm_req) as resp:
        assert resp.status == 200
        comments = json.loads(resp.read().decode())
        assert any(c["content"] == "New test comment with @alex mention" for c in comments)


def test_wasmer_notifications_generation_and_management(wasmer_server):
    # 1. Login as admin
    _, admin_cookie = _login(wasmer_server, "admin", "admin123")

    # 2. Add comment mentioning @alex on issue 1
    comm_payload = json.dumps({
        "content": "Hey @alex please review the invariant specifications!"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues/iss-1/comments",
        data=comm_payload,
        headers={"Content-Type": "application/json", "Cookie": admin_cookie},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201

    # 3. Check notifications for alex
    alex_notif_req = urllib.request.Request(f"{wasmer_server}/api/notifications?username=alex")
    with urllib.request.urlopen(alex_notif_req) as resp:
        assert resp.status == 200
        notifs = json.loads(resp.read().decode())
        mention_notif = next((n for n in notifs if n.get("type") == "MENTION"), None)
        assert mention_notif is not None
        assert "tagged you" in mention_notif["message"]
        notif_id = mention_notif["id"]

    # 4. Toggle read state
    toggle_req = urllib.request.Request(
        f"{wasmer_server}/api/notifications/{notif_id}/toggle-read",
        data=json.dumps({"read": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(toggle_req) as resp:
        assert resp.status == 200
        updated = json.loads(resp.read().decode())
        assert updated["read"] is True

    # 5. Mark all as read
    mark_all_req = urllib.request.Request(
        f"{wasmer_server}/api/notifications/mark-all-read",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(mark_all_req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode())
        assert "marked_count" in res


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

    # Check summary
    sum_req = urllib.request.Request(f"{wasmer_server}/api/sprints/sprint-2/summary")
    with urllib.request.urlopen(sum_req) as resp:
        assert resp.status == 200
        summary = json.loads(resp.read().decode())
        assert "completion_percentage" in summary


def test_wasmer_user_password_update_and_relogin(wasmer_server):
    # Change alex's password
    pwd_req = urllib.request.Request(
        f"{wasmer_server}/api/users/user-alex/password",
        data=json.dumps({"new_password": "newalexpassword99"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(pwd_req) as resp:
        assert resp.status == 200

    # Old password fails
    with pytest.raises(urllib.error.HTTPError):
        _login(wasmer_server, "alex", "alex123")

    # New password succeeds
    user, _ = _login(wasmer_server, "alex", "newalexpassword99")
    assert user["username"] == "alex"


def test_wasmer_delete_issue(wasmer_server):
    # Create issue to delete
    payload = json.dumps({
        "project_id": "proj-proj",
        "title": "Issue to be deleted",
        "status": "TODO"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{wasmer_server}/api/issues",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        created = json.loads(resp.read().decode())
        del_id = created["id"]

    del_req = urllib.request.Request(
        f"{wasmer_server}/api/issues/{del_id}",
        method="DELETE"
    )
    with urllib.request.urlopen(del_req) as resp:
        assert resp.status == 200

    # Verify 404
    get_req = urllib.request.Request(f"{wasmer_server}/api/issues/{del_id}")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(get_req)
    assert exc_info.value.status == 404


def test_wasmer_api_404_returns_json_not_html(wasmer_server):
    req = urllib.request.Request(f"{wasmer_server}/api/unknown-route")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    err_resp = exc_info.value
    assert err_resp.status == 404
    assert err_resp.headers.get("Content-Type").startswith("application/json")
    data = json.loads(err_resp.read().decode())
    assert "detail" in data

