"""Comprehensive verification suite for User Management, Auth, Attachments, Comments, Tags, Filtering, Multi-Project & Notifications."""
import base64
import pytest
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_default_admin_and_users():
    """Verify default Admin user and seeded team members exist."""
    res = client.get("/api/users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3

    admin = next((u for u in users if u["username"] == "admin"), None)
    assert admin is not None
    assert admin["role"] == "ADMIN"
    assert admin["full_name"] == "System Admin"

    alex = next((u for u in users if u["username"] == "alex"), None)
    assert alex is not None
    assert alex["role"] == "MEMBER"

    sam = next((u for u in users if u["username"] == "sam"), None)
    assert sam is not None
    assert sam["role"] == "VIEWER"


def test_auth_login_and_session_cookie():
    """Verify login with credentials, session cookie persistence, /api/auth/me, and logout."""
    # 1. Failed login with wrong password
    bad_login = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_login.status_code == 401

    # 2. Successful login sets session_id cookie
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    assert "session_id" in login_res.cookies
    user_data = login_res.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "ADMIN"

    # 3. GET /api/auth/me using session cookie
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"

    # 4. Logout clears session cookie
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # 5. GET /api/auth/me after logout returns 401
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 401


def test_user_creation_and_role_management():
    """Verify creating a new user and updating their role."""
    # Authenticate as admin to create user
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200

    # Create new user
    new_username = "dev_jordan"
    create_res = client.post("/api/users", json={
        "username": new_username,
        "password": "Password123!",
        "full_name": "Jordan Lee",
        "email": "jordan@jira.local",
        "role": "MEMBER"
    })
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["username"] == new_username
    assert created["role"] == "MEMBER"
    user_id = created["id"]

    # Authenticate as newly created MEMBER
    login_res = client.post("/api/auth/login", json={"username": new_username, "password": "Password123!"})
    assert login_res.status_code == 200
    assert login_res.json()["id"] == user_id

    # Non-admin member should NOT be able to change roles (403 Forbidden)
    forbidden_role_res = client.patch(f"/api/users/{user_id}/role", json={"role": "ADMIN"})
    assert forbidden_role_res.status_code == 403

    # Authenticate back as admin to successfully update role
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    role_res = client.patch(f"/api/users/{user_id}/role", json={"role": "ADMIN"})
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "ADMIN"



def test_multi_project_management_and_switching():
    """Verify creating multiple projects, fetching scoped boards and issues."""
    # Authenticate as admin
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    # 1. List existing projects (PROJ, MOBILE)
    res = client.get("/api/projects")
    assert res.status_code == 200
    projs = res.json()
    keys = [p["key"] for p in projs]
    assert "PROJ" in keys
    assert "MOBILE" in keys

    # 2. Create new project CLOUD
    create_proj = client.post("/api/projects", json={
        "key": "CLOUD",
        "name": "Cloud Infrastructure",
        "description": "Multi-region Kubernetes management"
    })
    assert create_proj.status_code == 200
    cloud_proj = create_proj.json()
    assert cloud_proj["key"] == "CLOUD"

    # 3. Create issue in CLOUD project
    issue_res = client.post("/api/issues", json={
        "project_id": cloud_proj["id"],
        "title": "Provision Staging Cluster",
        "description": "Setup GKE 1.30 with Istio mesh",
        "status": "TODO",
        "priority": "HIGH",
        "assignee": "alex",
        "tags": ["DevOps", "Kubernetes"]
    })
    assert issue_res.status_code == 200
    cloud_issue = issue_res.json()
    assert cloud_issue["key"].startswith("CLOUD-")

    # 4. Fetch board scoped to CLOUD project
    board_res = client.get(f"/api/board?project_id={cloud_proj['id']}")
    assert board_res.status_code == 200
    board_data = board_res.json()
    assert board_data["project"]["key"] == "CLOUD"
    cloud_issue_keys = [i["key"] for i in board_data["issues"]]
    assert cloud_issue["key"] in cloud_issue_keys


def test_issue_tags_functionality():
    """Verify assigning and updating single and multiple custom tags on issues."""
    # Create issue with multiple tags
    issue_res = client.post("/api/issues", json={
        "title": "Fix CSS Overflow in Filter Dropdown",
        "status": "TODO",
        "priority": "LOW",
        "tags": ["UI/UX", "Bug", "Frontend", "CSS"]
    })
    assert issue_res.status_code == 200
    issue = issue_res.json()
    assert set(issue["tags"]) == {"UI/UX", "Bug", "Frontend", "CSS"}

    # Update issue tags
    issue_id = issue["id"]
    update_res = client.patch(f"/api/issues/{issue_id}", json={
        "tags": ["Frontend", "Resolved"]
    })
    assert update_res.status_code == 200
    assert set(update_res.json()["tags"]) == {"Frontend", "Resolved"}


def test_issue_attachments():
    """Verify uploading base64 and multipart image attachments and deleting them."""
    # 1. Create target issue
    issue_res = client.post("/api/issues", json={
        "title": "Inspect Screen Mockups",
        "status": "TODO"
    })
    issue_id = issue_res.json()["id"]

    # 2. Upload base64 image
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b64_str = "data:image/png;base64," + base64.b64encode(dummy_png).decode("utf-8")

    att_res = client.post(f"/api/issues/{issue_id}/attachments", json={
        "filename": "mockup_dashboard.png",
        "content_type": "image/png",
        "data": b64_str
    })
    assert att_res.status_code == 200
    att = att_res.json()
    assert att["filename"] == "mockup_dashboard.png"
    assert att["file_url"].startswith("/static/uploads/")
    att_id = att["id"]

    # 3. Check issue has attachment
    fetch_res = client.get(f"/api/issues/{issue_id}")
    assert len(fetch_res.json()["attachments"]) == 1

    # 4. Delete attachment
    del_res = client.delete(f"/api/issues/{issue_id}/attachments/{att_id}")
    assert del_res.status_code == 200
    fetch_after = client.get(f"/api/issues/{issue_id}")
    assert len(fetch_after.json()["attachments"]) == 0


def test_comments_and_mentions_notifications():
    """Verify ticket comments with @mentions generate notifications for mentioned users and assignees."""
    # 1. Create issue assigned to alex
    issue_res = client.post("/api/issues", json={
        "title": "Database Indexing Optimization",
        "status": "TODO",
        "assignee": "alex"
    })
    issue = issue_res.json()
    issue_id = issue["id"]

    # 2. Login as admin
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    # 3. Post comment tagging sam: "@sam please benchmark query plan"
    comment_res = client.post(f"/api/issues/{issue_id}/comments", json={
        "content": "@sam please benchmark the Postgres query plan for this index."
    })
    assert comment_res.status_code == 200
    cmt = comment_res.json()
    assert "sam" in cmt["mentions"]

    # 4. Check Sam's notifications -> should have MENTION notification
    sam_notifs = client.get("/api/notifications?username=sam").json()
    sam_mention = next((n for n in sam_notifs if n["type"] == "MENTION" and n["issue_id"] == issue_id), None)
    assert sam_mention is not None
    assert "System Admin" in sam_mention["title"]

    # 5. Check Alex's notifications -> should have COMMENT notification (as assignee)
    alex_notifs = client.get("/api/notifications?username=alex").json()
    alex_comment_alert = next((n for n in alex_notifs if n["type"] == "COMMENT" and n["issue_id"] == issue_id), None)
    assert alex_comment_alert is not None


def test_notification_standard_features():
    """Verify toggle read/unread, unread counts, and mark all as read."""
    # Create test user to isolate notifications
    user_res = client.post("/api/users", json={
        "username": "notif_tester",
        "password": "Password123!",
        "full_name": "Notif Tester",
        "email": "notif@jira.local",
        "role": "MEMBER"
    })
    username = "notif_tester"

    # Trigger notifications by creating issue assigned to notif_tester
    client.post("/api/issues", json={
        "title": "Task Alpha for Tester",
        "status": "TODO",
        "assignee": username
    })
    client.post("/api/issues", json={
        "title": "Task Beta for Tester",
        "status": "TODO",
        "assignee": username
    })

    # Fetch notifications
    notifs = client.get(f"/api/notifications?username={username}").json()
    assert len(notifs) >= 2
    unread_count = sum(1 for n in notifs if not n["read"])
    assert unread_count >= 2

    first_id = notifs[0]["id"]

    # 1. Toggle mark read on first notification
    toggle_res = client.post(f"/api/notifications/{first_id}/toggle-read", json={"read": True})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["read"] is True

    # 2. Toggle mark unread on first notification
    toggle_back = client.post(f"/api/notifications/{first_id}/toggle-read", json={"read": False})
    assert toggle_back.status_code == 200
    assert toggle_back.json()["read"] is False

    # 3. Mark all as read
    mark_all_res = client.post(f"/api/notifications/mark-all-read?username={username}")
    assert mark_all_res.status_code == 200

    # Verify all are now read
    notifs_after = client.get(f"/api/notifications?username={username}").json()
    unread_after = sum(1 for n in notifs_after if not n["read"])
    assert unread_after == 0


def test_assignee_change_notifications():
    """Verify status change on card move generates notification for the assigned user."""
    # Create issue assigned to alex
    issue_res = client.post("/api/issues", json={
        "title": "Verify State Machine Flow",
        "status": "TODO",
        "assignee": "alex"
    })
    issue_id = issue_res.json()["id"]

    # Login as admin and move issue
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    move_res = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "IN_PROGRESS"})
    assert move_res.status_code == 200

    # Verify Alex received STATUS_CHANGE notification
    alex_notifs = client.get("/api/notifications?username=alex").json()
    status_notif = next((n for n in alex_notifs if n["type"] == "STATUS_CHANGE" and n["issue_id"] == issue_id), None)
    assert status_notif is not None
    assert "IN_PROGRESS" in status_notif["message"]


def test_unassigned_notification():
    """Verify that when someone is unassigned from a ticket, an UNASSIGNED notification is triggered."""
    # 1. Create issue assigned to alex
    issue_res = client.post("/api/issues", json={
        "title": "Fix Memory Leak in Frontend",
        "status": "TODO",
        "assignee": "alex"
    })
    assert issue_res.status_code == 200
    issue_data = issue_res.json()
    issue_id = issue_data["id"]
    issue_key = issue_data["key"]

    # 2. Login as admin and unassign alex
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    patch_res = client.patch(f"/api/issues/{issue_id}", json={"assignee": None})
    assert patch_res.status_code == 200
    assert patch_res.json()["assignee"] is None

    # 3. Verify Alex received UNASSIGNED notification
    alex_notifs = client.get("/api/notifications?username=alex").json()
    unassign_notif = next((n for n in alex_notifs if n["type"] == "UNASSIGNED" and n["issue_id"] == issue_id), None)
    assert unassign_notif is not None, f"Alex did not receive UNASSIGNED notification for {issue_key}"
    assert issue_key in unassign_notif["title"]
    assert "admin" in unassign_notif["message"]
    assert "Fix Memory Leak in Frontend" in unassign_notif["message"]

    # 4. Test reassignment triggers both UNASSIGNED for old assignee and ASSIGNED for new assignee
    reassign_issue = client.post("/api/issues", json={
        "title": "Reassignment Test Ticket",
        "status": "TODO",
        "assignee": "alex"
    }).json()

    patch_reassign = client.patch(f"/api/issues/{reassign_issue['id']}", json={"assignee": "sam"})
    assert patch_reassign.status_code == 200
    assert patch_reassign.json()["assignee"] == "sam"

    # Alex should have UNASSIGNED notification for the new ticket
    alex_reassign_notif = next(
        (n for n in client.get("/api/notifications?username=alex").json()
         if n["type"] == "UNASSIGNED" and n["issue_id"] == reassign_issue["id"]),
        None
    )
    assert alex_reassign_notif is not None

    # Sam should have ASSIGNED notification for the new ticket
    sam_assign_notif = next(
        (n for n in client.get("/api/notifications?username=sam").json()
         if n["type"] == "ASSIGNED" and n["issue_id"] == reassign_issue["id"]),
        None
    )
    assert sam_assign_notif is not None

