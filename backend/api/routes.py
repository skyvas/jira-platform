"""FastAPI routes for JiraPlatform."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.models.domain import Issue, IssueStatus, Priority, Project, Sprint
from backend.services.jira_store import JiraStore
from backend.services.state_machine import InvalidTransitionError

router = APIRouter(prefix="/api")
store = JiraStore()


class CreateIssueRequest(BaseModel):
    project_id: Optional[str] = None
    title: str
    description: str = ""
    status: IssueStatus = IssueStatus.TODO
    priority: Priority = Priority.MEDIUM
    assignee: Optional[str] = None


class MoveIssueRequest(BaseModel):
    new_status: IssueStatus
    prev_rank: Optional[str] = None
    next_rank: Optional[str] = None


class CreateSprintRequest(BaseModel):
    project_id: str
    name: str
    goal: str = ""


@router.get("/projects", response_model=List[Project])
def get_projects():
    return list(store.projects.values())


@router.get("/board")
def get_board():
    board = next(iter(store.boards.values()))
    issues = store.get_issues(board.project_id)
    return {
        "board": board,
        "issues": issues
    }


@router.get("/issues", response_model=List[Issue])
def get_issues(project_id: Optional[str] = None):
    return store.get_issues(project_id)


@router.post("/issues", response_model=Issue)
def create_issue(req: CreateIssueRequest):
    proj_id = req.project_id or next(iter(store.projects.keys()))
    return store.create_issue(
        project_id=proj_id,
        title=req.title,
        description=req.description,
        status=req.status,
        priority=req.priority,
        assignee=req.assignee
    )


@router.patch("/issues/{issue_id}/move", response_model=Issue)
def move_issue(issue_id: str, req: MoveIssueRequest):
    try:
        return store.move_issue(
            issue_id=issue_id,
            new_status=req.new_status,
            prev_rank=req.prev_rank,
            next_rank=req.next_rank
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sprints", response_model=List[Sprint])
def get_sprints(project_id: Optional[str] = None):
    sprints = list(store.sprints.values())
    if project_id:
        sprints = [s for s in sprints if s.project_id == project_id]
    return sprints


@router.post("/sprints", response_model=Sprint)
def create_sprint(req: CreateSprintRequest):
    return store.create_sprint(project_id=req.project_id, name=req.name, goal=req.goal)


@router.post("/sprints/{sprint_id}/start", response_model=Sprint)
def start_sprint(sprint_id: str):
    try:
        return store.start_sprint(sprint_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprint not found")


@router.post("/sprints/{sprint_id}/complete", response_model=Sprint)
def complete_sprint(sprint_id: str):
    try:
        return store.complete_sprint(sprint_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprint not found")
