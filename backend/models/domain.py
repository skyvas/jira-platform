"""Domain models and schemas for JiraPlatform."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


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


class ColumnLane(BaseModel):
    id: str
    name: str
    status: IssueStatus
    order_index: int


class Board(BaseModel):
    id: str
    project_id: str
    name: str
    columns: List[ColumnLane] = Field(default_factory=list)


class Project(BaseModel):
    id: str
    key: str
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    issue_counter: int = 0


class Issue(BaseModel):
    id: str
    key: str
    project_id: str
    title: str
    description: str = ""
    status: IssueStatus = IssueStatus.TODO
    priority: Priority = Priority.MEDIUM
    issue_type: IssueType = IssueType.TASK
    rank: str = "0|hzzzzz:"
    assignee: Optional[str] = None
    sprint_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class Sprint(BaseModel):
    id: str
    project_id: str
    name: str
    goal: str = ""
    state: SprintState = SprintState.PLANNED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class IssueActivity(BaseModel):
    id: str
    issue_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    details: str
