"""FastAPI routes for Orbit."""
from __future__ import annotations
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
import uuid

from fastapi import APIRouter, Cookie, File, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.models.domain import (
    Attachment, Board, BoardColumnsUpdateRequest, ChecklistItem, ColumnConfig, Comment,
    Issue, IssueStatus, IssueType, Notification, Priority, Project, ProjectCreateRequest,
    Role, Sprint, SprintState, UpdateUserNameRequest, UpdateUserPasswordRequest,
    User, UserCreate, UserLogin
)
from backend.services.event_broadcaster import broadcaster
from backend.services.jira_store import OrbitStore, JiraStore
from backend.services.postgres_repository import PostgresRepository, get_database_url
from backend.services.state_machine import InvalidTransitionError

router = APIRouter(prefix="/api")

def _init_store():
    try:
        db_url = get_database_url()
        return PostgresRepository(db_url)
    except Exception:
        return OrbitStore()

store = _init_store()

frontend_uploads_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "uploads"
frontend_uploads_dir.mkdir(parents=True, exist_ok=True)


# ------------------ Request Schemas ------------------

class CreateIssueRequest(BaseModel):
    project_id: Optional[str] = None
    title: str
    description: str = ""
    status: Union[IssueStatus, str] = IssueStatus.TODO
    priority: Priority = Priority.MEDIUM
    issue_type: Optional[Union[IssueType, str]] = IssueType.TASK
    story_points: Optional[float] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None
    sprint_id: Optional[str] = None
    checklist: Optional[List[dict]] = None


class UpdateIssueRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    issue_type: Optional[Union[IssueType, str]] = None
    story_points: Optional[float] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None
    sprint_id: Optional[str] = None


class CreateChecklistItemRequest(BaseModel):
    text: str


class UpdateChecklistItemRequest(BaseModel):
    text: Optional[str] = None
    completed: Optional[bool] = None


class MoveIssueRequest(BaseModel):
    new_status: str
    prev_rank: Optional[str] = None
    next_rank: Optional[str] = None


class CreateSprintRequest(BaseModel):
    project_id: str
    name: str
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_weeks: Optional[int] = 2


class StartSprintRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CompleteSprintRequest(BaseModel):
    move_incomplete_to: Optional[str] = "backlog"


class CreateCommentRequest(BaseModel):
    content: str
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_role: Optional[Role] = None
    images: Optional[List[str]] = None


class Base64AttachmentRequest(BaseModel):
    filename: str
    content_type: str = "image/png"
    data: str  # Base64 data or data URI


class ToggleReadRequest(BaseModel):
    read: Optional[bool] = None


class UpdateUserRoleRequest(BaseModel):
    role: Role


# ------------------ Auth Helpers ------------------

def get_current_user_from_req(request: Request) -> Optional[User]:
    # Check session cookie
    token = request.cookies.get("session_id")
    if not token:
        # Check Authorization header: Bearer <token>
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1].strip()
    return store.get_session_user(token)


def require_admin(request: Request) -> User:
    """Ensures request is from an authenticated user with ADMIN role."""
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_val.upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required for this action")
    return user



# ------------------ Auth Endpoints ------------------

@router.post("/auth/login", response_model=User)
def login(req: UserLogin, response: Response):
    user = store.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = store.create_session(user.id)
    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
        path="/"
    )
    return user


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_id")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1].strip()
    if token:
        store.delete_session(token)
    response.delete_cookie(key="session_id", path="/")
    response.set_cookie(key="session_id", value="", max_age=0, path="/")
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/auth/me", response_model=User)
def get_me(request: Request):
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ------------------ User Management Endpoints ------------------

@router.get("/users", response_model=List[User])
def get_users():
    return store.get_users()


@router.post("/users", response_model=User)
def create_user(req: UserCreate, request: Request):
    require_admin(request)
    try:
        user = store.create_user(
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            email=req.email,
            role=req.role
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/users/{user_id}/role", response_model=User)
def update_user_role(user_id: str, req: UpdateUserRoleRequest, request: Request):
    require_admin(request)
    try:
        return store.update_user_role(user_id, req.role)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")


@router.patch("/users/{user_id}/name", response_model=User)
def update_user_name(user_id: str, req: UpdateUserNameRequest, request: Request):
    caller = get_current_user_from_req(request)
    if not caller:
        raise HTTPException(status_code=401, detail="Authentication required")

    target = store.get_user_by_id(user_id) or store.get_user_by_username(user_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    is_self = (caller.id == target.id or caller.username.lower() == target.username.lower())
    is_admin = (caller.role == Role.ADMIN)
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only update your own name unless you are an Admin"
        )

    if not req.full_name or not req.full_name.strip():
        raise HTTPException(status_code=400, detail="User full name cannot be empty")

    try:
        return store.update_user_name(target.id, req.full_name.strip())
    except KeyError:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")


@router.patch("/users/{user_id}/password", response_model=User)
def update_user_password(user_id: str, req: UpdateUserPasswordRequest, request: Request):
    require_admin(request)

    target = store.get_user_by_id(user_id) or store.get_user_by_username(user_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    if not req.new_password or len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    try:
        return store.update_user_password(target.id, req.new_password)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")



# ------------------ Notification Endpoints ------------------

@router.get("/notifications", response_model=List[Notification])
def get_notifications(request: Request, username: Optional[str] = None):
    user = get_current_user_from_req(request)
    target_username = username.lower().strip() if username else (user.username if user else "admin")
    return store.get_user_notifications(target_username)


@router.post("/notifications/{notification_id}/toggle-read", response_model=Notification)
def toggle_notification_read(notification_id: str, req: Optional[ToggleReadRequest] = None):
    try:
        read_val = req.read if req else None
        return store.toggle_notification_read(notification_id, read_val)
    except KeyError:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(request: Request, username: Optional[str] = None):
    user = get_current_user_from_req(request)
    target_username = username.lower().strip() if username else (user.username if user else "admin")
    count = store.mark_all_notifications_read(target_username)
    return {"status": "ok", "marked_count": count}


# ------------------ Project Endpoints ------------------

@router.get("/projects", response_model=List[Project])
def get_projects():
    return list(store.projects.values())


@router.post("/projects", response_model=Project)
def create_project(req: ProjectCreateRequest, request: Request):
    require_admin(request)
    if not req.key or not req.name:
        raise HTTPException(status_code=400, detail="Project key and name are required")
    proj = store.create_project(req.key, req.name, req.description, custom_columns=req.columns)
    return proj


@router.put("/board/{project_id}/columns", response_model=Board)
@router.post("/board/{project_id}/columns", response_model=Board)
@router.patch("/projects/{project_id}/columns", response_model=Board)
def update_project_columns(project_id: str, req: BoardColumnsUpdateRequest, request: Request):
    require_admin(request)
    try:
        return store.update_board_columns(project_id, req.columns)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")



@router.get("/board")
def get_board(request: Request, project_id: Optional[str] = Query(None)):
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to view Kanban board")
    board = store.get_board(project_id)
    if not board:
        raise HTTPException(status_code=404, detail="No board found")
    issues = store.get_issues(board.project_id)
    project = store.projects.get(board.project_id)
    return {
        "board": board,
        "project": project,
        "issues": issues
    }


# ------------------ Issue Endpoints ------------------

@router.get("/issues", response_model=List[Issue])
def get_issues(project_id: Optional[str] = None):
    return store.get_issues(project_id)


# ------------------ Real-Time Server-Sent Events (SSE) ------------------

@router.get("/events")
async def sse_events(request: Request, once: bool = False):
    """Server-Sent Events endpoint for unidirectional real-time board and card updates."""
    sub_queue = broadcaster.subscribe()

    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
        if once:
            broadcaster.unsubscribe(sub_queue)
            return
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(sub_queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            broadcaster.unsubscribe(sub_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/issues", response_model=Issue)
def create_issue(req: CreateIssueRequest, request: Request):
    proj_id = req.project_id or next(iter(store.projects.keys()))
    issue = store.create_issue(
        project_id=proj_id,
        title=req.title,
        description=req.description,
        status=req.status,
        priority=req.priority,
        issue_type=req.issue_type or IssueType.TASK,
        story_points=req.story_points,
        assignee=req.assignee,
        tags=req.tags,
        sprint_id=req.sprint_id,
        checklist=req.checklist
    )
    broadcaster.publish("ISSUE_CREATED", issue.model_dump(mode="json"))
    return issue


@router.get("/issues/{issue_id}", response_model=Issue)
def get_issue(issue_id: str):
    issue = store.get_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.delete("/issues/{issue_id}")
def delete_issue(issue_id: str, request: Request):
    current_user = get_current_user_from_req(request)
    if current_user and current_user.role not in (Role.ADMIN, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Permission denied")
    success = store.delete_issue(issue_id)
    if not success:
        raise HTTPException(status_code=404, detail="Issue not found")
    broadcaster.publish("ISSUE_DELETED", {"issue_id": issue_id})
    return {"status": "ok", "deleted": True}


@router.patch("/issues/{issue_id}", response_model=Issue)
def update_issue(issue_id: str, req: UpdateIssueRequest, request: Request):
    current_user = get_current_user_from_req(request)
    updater = current_user.username if current_user else None

    fields_set = req.model_fields_set
    kwargs: Dict[str, Any] = {"updater_username": updater}
    if "title" in fields_set:
        kwargs["title"] = req.title
    if "description" in fields_set:
        kwargs["description"] = req.description
    if "priority" in fields_set:
        kwargs["priority"] = req.priority
    if "issue_type" in fields_set:
        kwargs["issue_type"] = req.issue_type
    if "story_points" in fields_set:
        kwargs["story_points"] = req.story_points
    if "assignee" in fields_set:
        kwargs["assignee"] = req.assignee
    if "tags" in fields_set:
        kwargs["tags"] = req.tags
    if "sprint_id" in fields_set:
        kwargs["sprint_id"] = req.sprint_id

    try:
        updated = store.update_issue(issue_id=issue_id, **kwargs)
        broadcaster.publish("ISSUE_UPDATED", updated.model_dump(mode="json"))
        return updated
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")


# ------------------ Checklist Endpoints ------------------

@router.post("/issues/{issue_id}/checklist", response_model=ChecklistItem)
def add_checklist_item(issue_id: str, req: CreateChecklistItemRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Checklist item text is required")
    try:
        item = store.add_checklist_item(issue_id, req.text.strip())
        broadcaster.publish("CHECKLIST_UPDATED", {"issue_id": issue_id, "item": item.model_dump(mode="json")})
        return item
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")


@router.patch("/issues/{issue_id}/checklist/{item_id}", response_model=ChecklistItem)
def update_checklist_item(issue_id: str, item_id: str, req: UpdateChecklistItemRequest):
    fields_set = req.model_fields_set
    kwargs: Dict[str, Any] = {}
    if "text" in fields_set:
        kwargs["text"] = req.text
    if "completed" in fields_set:
        kwargs["completed"] = req.completed

    try:
        item = store.update_checklist_item(issue_id, item_id, **kwargs)
        broadcaster.publish("CHECKLIST_UPDATED", {"issue_id": issue_id, "item": item.model_dump(mode="json")})
        return item
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/issues/{issue_id}/checklist/{item_id}")
def delete_checklist_item(issue_id: str, item_id: str):
    try:
        success = store.delete_checklist_item(issue_id, item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Checklist item not found")
        broadcaster.publish("CHECKLIST_UPDATED", {"issue_id": issue_id, "item_id": item_id})
        return {"status": "ok", "deleted": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")



@router.patch("/issues/{issue_id}/move", response_model=Issue)
@router.post("/issues/{issue_id}/move", response_model=Issue)
def move_issue(issue_id: str, req: MoveIssueRequest, request: Request):
    current_user = get_current_user_from_req(request)
    mover = current_user.username if current_user else None
    try:
        moved = store.move_issue(
            issue_id=issue_id,
            new_status=req.new_status,
            prev_rank=req.prev_rank,
            next_rank=req.next_rank,
            mover_username=mover
        )
        broadcaster.publish("ISSUE_MOVED", moved.model_dump(mode="json"))
        return moved
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------ Attachments ------------------

@router.post("/issues/{issue_id}/attachments", response_model=Attachment)
async def upload_attachment(
    issue_id: str,
    request: Request,
    file: Optional[UploadFile] = File(None)
):
    issue = store.get_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    current_user = get_current_user_from_req(request)
    uploader = current_user.username if current_user else "admin"

    if file:
        file_bytes = await file.read()
        clean_name = Path(file.filename or "attachment.png").name
        saved_name = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        save_path = frontend_uploads_dir / saved_name
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_url = f"/static/uploads/{saved_name}"
        return store.add_attachment(
            issue_id=issue_id,
            filename=clean_name,
            file_url=file_url,
            content_type=file.content_type or "image/png",
            size_bytes=len(file_bytes),
            uploaded_by=uploader
        )

    # Check for JSON base64 upload
    try:
        body = await request.json()
        req_data = Base64AttachmentRequest(**body)
        raw_b64 = req_data.data
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        file_bytes = base64.b64decode(raw_b64)
        clean_name = Path(req_data.filename).name
        saved_name = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        save_path = frontend_uploads_dir / saved_name
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_url = f"/static/uploads/{saved_name}"
        return store.add_attachment(
            issue_id=issue_id,
            filename=clean_name,
            file_url=file_url,
            content_type=req_data.content_type,
            size_bytes=len(file_bytes),
            uploaded_by=uploader
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process attachment: {str(e)}")


@router.delete("/issues/{issue_id}/attachments/{attachment_id}")
def delete_attachment(issue_id: str, attachment_id: str):
    success = store.remove_attachment(issue_id, attachment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment or issue not found")
    return {"status": "deleted", "attachment_id": attachment_id}


# ------------------ Comments ------------------

@router.get("/issues/{issue_id}/comments", response_model=List[Comment])
def get_comments(issue_id: str):
    try:
        return store.get_comments(issue_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")


@router.post("/issues/{issue_id}/comments", response_model=Comment)
def add_comment(issue_id: str, req: CreateCommentRequest, request: Request):
    current_user = get_current_user_from_req(request)
    author_username = current_user.username if current_user else (req.author_username or "admin")
    author_name = current_user.full_name if current_user else (req.author_name or "System Admin")
    author_role = current_user.role if current_user else (req.author_role or Role.ADMIN)

    try:
        comment = store.add_comment(
            issue_id=issue_id,
            author_username=author_username,
            author_name=author_name,
            author_role=author_role,
            content=req.content,
            images=req.images
        )
        broadcaster.publish("COMMENT_ADDED", {"issue_id": issue_id, "comment": comment.model_dump(mode="json")})
        return comment
    except KeyError:
        raise HTTPException(status_code=404, detail="Issue not found")


@router.post("/comments/upload-image")
async def upload_comment_image(
    request: Request,
    file: Optional[UploadFile] = File(None)
):
    current_user = get_current_user_from_req(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if file:
        file_bytes = await file.read()
        clean_name = Path(file.filename or "comment_image.png").name
        saved_name = f"cmt_{uuid.uuid4().hex[:8]}_{clean_name}"
        save_path = frontend_uploads_dir / saved_name
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_url = f"/static/uploads/{saved_name}"
        return {"file_url": file_url, "filename": clean_name}

    try:
        body = await request.json()
        raw_b64 = body.get("data", "")
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        file_bytes = base64.b64decode(raw_b64)
        clean_name = Path(body.get("filename", "comment_image.png")).name
        saved_name = f"cmt_{uuid.uuid4().hex[:8]}_{clean_name}"
        save_path = frontend_uploads_dir / saved_name
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        file_url = f"/static/uploads/{saved_name}"
        return {"file_url": file_url, "filename": clean_name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")


# ------------------ Sprints ------------------

@router.get("/sprints", response_model=List[Sprint])
def get_sprints(project_id: Optional[str] = None, state: Optional[str] = None):
    sprints = list(store.sprints.values())
    if project_id:
        sprints = [s for s in sprints if s.project_id == project_id]
    if state:
        state_upper = state.upper().strip()
        sprints = [s for s in sprints if s.state == state_upper or s.state.value == state_upper]
    return sprints


@router.post("/sprints", response_model=Sprint)
def create_sprint(req: CreateSprintRequest, request: Request):
    require_admin(request)
    return store.create_sprint(
        project_id=req.project_id,
        name=req.name,
        goal=req.goal,
        start_date=req.start_date,
        end_date=req.end_date,
        duration_weeks=req.duration_weeks
    )


@router.get("/sprints/history")
def get_sprint_history(project_id: str):
    return store.get_sprint_history(project_id)


@router.get("/sprints/{sprint_id}/summary")
def get_sprint_summary(sprint_id: str):
    try:
        return store.get_sprint_summary(sprint_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprint not found")


@router.post("/sprints/{sprint_id}/start", response_model=Sprint)
def start_sprint(sprint_id: str, request: Request, req: Optional[StartSprintRequest] = None):
    require_admin(request)
    try:
        start_date = req.start_date if req else None
        end_date = req.end_date if req else None
        return store.start_sprint(sprint_id, start_date=start_date, end_date=end_date)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprint not found")


@router.post("/sprints/{sprint_id}/complete", response_model=Sprint)
def complete_sprint(sprint_id: str, request: Request, req: Optional[CompleteSprintRequest] = None):
    require_admin(request)
    try:
        move_to = req.move_incomplete_to if req else "backlog"
        return store.complete_sprint(sprint_id, move_incomplete_to=move_to)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sprint not found")

