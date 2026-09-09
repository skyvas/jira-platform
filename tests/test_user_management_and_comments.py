"""Tests for User Name/Password Management and Comment Images."""
import pytest
from starlette.testclient import TestClient

from backend.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def login(client: TestClient, username: str, password: str):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()


def test_user_name_update_permissions(client: TestClient):
    # 1. Unauthenticated request -> 401
    res = client.patch("/api/users/user-alex/name", json={"full_name": "Alexander Great"})
    assert res.status_code == 401

    # 2. Member (alex) updating their own name -> 200
    login(client, "alex", "alex123")
    res = client.patch("/api/users/user-alex/name", json={"full_name": "Alexander Chen"})
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Alexander Chen"

    # Verify empty name is rejected -> 400
    res = client.patch("/api/users/user-alex/name", json={"full_name": "   "})
    assert res.status_code == 400

    # 3. Member (alex) trying to update another user's name (sam) -> 403
    res = client.patch("/api/users/user-sam/name", json={"full_name": "Samantha Modified"})
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

    # 4. Admin updating another user's name (sam) -> 200
    login(client, "admin", "admin123")
    res = client.patch("/api/users/user-sam/name", json={"full_name": "Samantha Taylor"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "Samantha Taylor"


def test_user_password_update_admin_only(client: TestClient):
    # 1. Unauthenticated request -> 401
    res = client.patch("/api/users/user-alex/password", json={"new_password": "newpassword123"})
    assert res.status_code == 401

    # 2. Member (alex) trying to update password -> 403
    login(client, "alex", "alex123")
    res = client.patch("/api/users/user-alex/password", json={"new_password": "newpassword123"})
    assert res.status_code == 403

    # 3. Admin updates password for alex -> 200
    login(client, "admin", "admin123")
    res = client.patch("/api/users/user-alex/password", json={"new_password": "alexbrandnew123"})
    assert res.status_code == 200

    # 4. Password validation: too short (< 4 chars) -> 400
    res = client.patch("/api/users/user-alex/password", json={"new_password": "ab"})
    assert res.status_code == 400

    # 5. Verify alex can now log in with the new password
    # Clear cookies by creating a new client
    new_client = TestClient(app)
    # Old password fails -> 401
    res_fail = new_client.post("/api/auth/login", json={"username": "alex", "password": "alex123"})
    assert res_fail.status_code == 401

    # New password succeeds -> 200
    res_ok = new_client.post("/api/auth/login", json={"username": "alex", "password": "alexbrandnew123"})
    assert res_ok.status_code == 200


def test_comments_with_image_attachments(client: TestClient):
    login(client, "admin", "admin123")

    # Get an issue
    board_res = client.get("/api/board")
    assert board_res.status_code == 200
    issues = board_res.json()["issues"]
    assert len(issues) > 0
    target_issue = issues[0]

    # Post comment with images
    test_img = "/static/uploads/cmt_test_image.png"
    comment_payload = {
        "content": "Attaching visual bug proof @alex",
        "images": [test_img]
    }
    res = client.post(f"/api/issues/{target_issue['id']}/comments", json=comment_payload)
    assert res.status_code == 200
    cmt = res.json()
    assert cmt["content"] == "Attaching visual bug proof @alex"
    assert test_img in cmt["images"]

    # Verify GET comments returns the image
    comments_res = client.get(f"/api/issues/{target_issue['id']}/comments")
    assert comments_res.status_code == 200
    all_cmts = comments_res.json()
    matching = [c for c in all_cmts if c["id"] == cmt["id"]]
    assert len(matching) == 1
    assert matching[0]["images"] == [test_img]
