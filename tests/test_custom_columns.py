"""Tests for Custom Kanban Columns configuration, ordering, and state transitions."""
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_custom_kanban_columns_workflow():
    # Login as admin
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    # 1. Create project with custom columns
    custom_cols = [
        {"id": "col-backlog", "name": "Product Backlog", "status": "BACKLOG", "order_index": 0},
        {"id": "col-design", "name": "UX Design", "status": "DESIGN", "order_index": 1},
        {"id": "col-dev", "name": "Engineering", "status": "IN_PROGRESS", "order_index": 2},
        {"id": "col-qa", "name": "Quality Assurance", "status": "QA", "order_index": 3},
        {"id": "col-done", "name": "Shipped", "status": "DONE", "order_index": 4},
    ]
    proj_res = client.post("/api/projects", json={
        "key": "FINTECH",
        "name": "Fintech Core Engine",
        "description": "High throughput transaction processor",
        "columns": custom_cols
    })
    assert proj_res.status_code == 200
    proj = proj_res.json()
    proj_id = proj["id"]

    # 2. Fetch Board and verify custom columns
    board_res = client.get(f"/api/board?project_id={proj_id}")
    assert board_res.status_code == 200
    board = board_res.json()["board"]
    col_names = [c["name"] for c in board["columns"]]
    assert "UX Design" in col_names
    assert "Quality Assurance" in col_names
    assert "Shipped" in col_names

    # 3. Create issue in custom project
    issue_res = client.post("/api/issues", json={
        "project_id": proj_id,
        "title": "Design Payment Modal Screen",
        "status": "BACKLOG"
    })
    assert issue_res.status_code == 200
    issue = issue_res.json()
    issue_id = issue["id"]

    # 4. Move issue: BACKLOG -> DESIGN (custom column)
    move1 = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "DESIGN"})
    assert move1.status_code == 200
    assert move1.json()["status"] == "DESIGN"
    assert move1.json()["resolved_at"] is None

    # 5. Move issue: DESIGN -> IN_PROGRESS -> QA -> DONE
    move2 = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "IN_PROGRESS"})
    assert move2.status_code == 200

    move3 = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "QA"})
    assert move3.status_code == 200
    assert move3.json()["status"] == "QA"

    move4 = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "DONE"})
    assert move4.status_code == 200
    assert move4.json()["status"] == "DONE"
    assert move4.json()["resolved_at"] is not None

    # 6. Reopen issue from DONE to DESIGN
    reopen = client.patch(f"/api/issues/{issue_id}/move", json={"new_status": "DESIGN"})
    assert reopen.status_code == 200
    assert reopen.json()["status"] == "DESIGN"
    assert reopen.json()["resolved_at"] is None

    # 7. Update board columns via API
    updated_cols = custom_cols + [
        {"id": "col-staging", "name": "Staging Verification", "status": "STAGING", "order_index": 5}
    ]
    update_cols_res = client.put(f"/api/board/{proj_id}/columns", json={"columns": updated_cols})
    assert update_cols_res.status_code == 200
    assert len(update_cols_res.json()["columns"]) == 6
