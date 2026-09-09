"""Tests for Sprint management API."""
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_sprint_lifecycle():
    # Get project id
    proj_res = client.get("/api/projects")
    proj_id = proj_res.json()[0]["id"]

    # Create sprint
    create_res = client.post("/api/sprints", json={
        "project_id": proj_id,
        "name": "Sprint 2 - Board Refinement",
        "goal": "Polish drag-and-drop interactions"
    })
    assert create_res.status_code == 200
    sprint = create_res.json()
    sprint_id = sprint["id"]
    assert sprint["state"] == "PLANNED"

    # Start sprint
    start_res = client.post(f"/api/sprints/{sprint_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["state"] == "ACTIVE"

    # Complete sprint
    comp_res = client.post(f"/api/sprints/{sprint_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["state"] == "COMPLETED"
    assert comp_res.json()["completed_at"] is not None
