"""Tests for Multiple Sprints per Project lifecycle, workflows, and history."""
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_multiple_sprints_lifecycle_and_history():
    # Login as admin
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    # Get project id
    proj_res = client.get("/api/projects")
    proj_id = proj_res.json()[0]["id"]

    # 1. Create Sprint Alpha
    sprint_a_res = client.post("/api/sprints", json={
        "project_id": proj_id,
        "name": "Sprint Alpha - Payment Integration",
        "goal": "Integrate Stripe and Apple Pay checkout flows",
        "start_date": "2026-10-01",
        "end_date": "2026-10-14",
        "duration_weeks": 2
    })
    assert sprint_a_res.status_code == 200
    sprint_a = sprint_a_res.json()
    assert sprint_a["state"] == "PLANNED"
    assert sprint_a["name"] == "Sprint Alpha - Payment Integration"

    # 2. Create Sprint Beta in the same project
    sprint_b_res = client.post("/api/sprints", json={
        "project_id": proj_id,
        "name": "Sprint Beta - Analytics & Invoicing",
        "goal": "Build monthly recurring billing invoice PDFs",
        "start_date": "2026-10-15",
        "end_date": "2026-10-29",
        "duration_weeks": 2
    })
    assert sprint_b_res.status_code == 200
    sprint_b = sprint_b_res.json()
    assert sprint_b["state"] == "PLANNED"

    # 3. Start Sprint Alpha
    start_res = client.post(f"/api/sprints/{sprint_a['id']}/start")
    assert start_res.status_code == 200
    assert start_res.json()["state"] == "ACTIVE"

    # 4. Create an issue assigned to Sprint Alpha
    issue1 = client.post("/api/issues", json={
        "project_id": proj_id,
        "title": "Stripe Webhook Listener",
        "status": "DONE",
        "sprint_id": sprint_a["id"]
    }).json()

    issue2 = client.post("/api/issues", json={
        "project_id": proj_id,
        "title": "Apple Pay Merchant Validation",
        "status": "TODO",
        "sprint_id": sprint_a["id"]
    }).json()

    # 5. Check Sprint summary before completion
    summary_res = client.get(f"/api/sprints/{sprint_a['id']}/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_issues"] >= 2
    assert summary["completed_count"] >= 1
    assert summary["incomplete_count"] >= 1

    # 6. Complete Sprint Alpha with carryover to Sprint Beta
    complete_res = client.post(
        f"/api/sprints/{sprint_a['id']}/complete",
        json={"move_incomplete_to": sprint_b["id"]}
    )
    assert complete_res.status_code == 200
    completed_sprint = complete_res.json()
    assert completed_sprint["state"] == "COMPLETED"
    assert completed_sprint["completed_at"] is not None

    # Verify incomplete issue moved to Sprint Beta
    updated_issue2 = client.get(f"/api/issues/{issue2['id']}").json()
    assert updated_issue2["sprint_id"] == sprint_b["id"]

    # 7. Check Sprint History endpoint
    history_res = client.get(f"/api/sprints/history?project_id={proj_id}")
    assert history_res.status_code == 200
    history = history_res.json()
    completed_ids = [h["sprint"]["id"] for h in history]
    assert sprint_a["id"] in completed_ids
