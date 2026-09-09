"""Domain models and schemas for Orbit."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: Role = Role.MEMBER
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role: Role = Role.MEMBER


class UserLogin(BaseModel):
    username: str
    password: str


class UpdateUserNameRequest(BaseModel):
    full_name: str


class UpdateUserPasswordRequest(BaseModel):
    new_password: str


class IssueStatus(str, Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueType(str, Enum):
    TASK = "TASK"
    BUG = "BUG"
    STORY = "STORY"
    EPIC = "EPIC"


class SprintState(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class ColumnLane(BaseModel):
    id: str
    name: str
    status: str
    order_index: int


class Board(BaseModel):
    id: str
    project_id: str
    name: str
    columns: List[ColumnLane] = Field(default_factory=list)


class ColumnConfig(BaseModel):
    id: Optional[str] = None
    name: str
    status: str
    order_index: Optional[int] = 0


class BoardColumnsUpdateRequest(BaseModel):
    columns: List[ColumnConfig]


class Project(BaseModel):
    id: str
    key: str
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    issue_counter: int = 0


class ProjectCreateRequest(BaseModel):
    key: str
    name: str
    description: str = ""
    columns: Optional[List[ColumnConfig]] = None


class Attachment(BaseModel):
    id: str
    issue_id: str
    filename: str
    file_url: str
    content_type: str
    size_bytes: int
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Comment(BaseModel):
    id: str
    issue_id: str
    author_username: str
    author_name: str
    author_role: Role = Role.MEMBER
    content: str
    mentions: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationType(str, Enum):
    MENTION = "MENTION"
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"
    COMMENT = "COMMENT"
    UPDATE = "UPDATE"



class Notification(BaseModel):
    id: str
    user_username: str
    type: NotificationType = NotificationType.UPDATE
    title: str
    message: str
    issue_id: str
    issue_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False


class Issue(BaseModel):
    id: str
    key: str
    project_id: str
    title: str
    description: str = ""
    status: str = "TODO"
    priority: Priority = Priority.MEDIUM
    issue_type: IssueType = IssueType.TASK
    rank: str = "0|hzzzzz:"
    assignee: Optional[str] = None
    sprint_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    attachments: List[Attachment] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class Sprint(BaseModel):
    id: str
    project_id: str
    name: str
    goal: str = ""
    state: SprintState = SprintState.PLANNED
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_weeks: Optional[int] = 2
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class IssueActivity(BaseModel):
    id: str
    issue_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    details: str
