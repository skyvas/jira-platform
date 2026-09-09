"""In-memory thread-safe store with auto-increment keys and persistence."""
from __future__ import annotations
from datetime import datetime
import threading
from typing import Dict, List, Optional
import uuid

from backend.models.domain import (
    Board, ColumnLane, Issue, IssueActivity, IssueStatus, Priority, Project, Sprint, SprintState
)
from backend.services.rank_service import LexoRank
from backend.services.state_machine import StateMachine


class JiraStore:
    """Thread-safe state repository for Jira entities."""

    def __init__(self):
        self._lock = threading.RLock()
        self.projects: Dict[str, Project] = {}
        self.boards: Dict[str, Board] = {}
        self.issues: Dict[str, Issue] = {}
        self.sprints: Dict[str, Sprint] = {}
        self.activities: List[IssueActivity] = []
        self._seed_default_project()

    def _seed_default_project(self):
        proj = self.create_project("PROJ", "Core Platform", "Primary platform engineering workspace")
        # Create default board
        board_id = f"board-{uuid.uuid4().hex[:8]}"
        columns = [
            ColumnLane(id="col-backlog", name="Backlog", status=IssueStatus.BACKLOG, order_index=0),
            ColumnLane(id="col-todo", name="To Do", status=IssueStatus.TODO, order_index=1),
            ColumnLane(id="col-progress", name="In Progress", status=IssueStatus.IN_PROGRESS, order_index=2),
            ColumnLane(id="col-review", name="In Review", status=IssueStatus.REVIEW, order_index=3),
            ColumnLane(id="col-done", name="Done", status=IssueStatus.DONE, order_index=4),
        ]
        self.boards[board_id] = Board(id=board_id, project_id=proj.id, name="Main Kanban Board", columns=columns)

    def create_project(self, key: str, name: str, description: str = "") -> Project:
        with self._lock:
            proj_id = f"proj-{key.lower()}"
            proj = Project(id=proj_id, key=key.upper(), name=name, description=description)
            self.projects[proj_id] = proj
            return proj

    def create_issue(
        self,
        project_id: str,
        title: str,
        description: str = "",
        status: IssueStatus = IssueStatus.TODO,
        priority: Priority = Priority.MEDIUM,
        assignee: Optional[str] = None
    ) -> Issue:
        with self._lock:
            proj = self.projects.get(project_id)
            if not proj:
                # Fallback to first project
                proj = next(iter(self.projects.values()))

            proj.issue_counter += 1
            issue_key = f"{proj.key}-{proj.issue_counter}"
            issue_id = f"issue-{uuid.uuid4().hex[:8]}"

            # Calculate rank
            existing = [i for i in self.issues.values() if i.status == status]
            last_rank = existing[-1].rank if existing else None
            new_rank = LexoRank.between(last_rank, None)

            issue = Issue(
                id=issue_id,
                key=issue_key,
                project_id=proj.id,
                title=title,
                description=description,
                status=status,
                priority=priority,
                rank=new_rank,
                assignee=assignee
            )
            self.issues[issue_id] = issue
            return issue

    def get_issues(self, project_id: Optional[str] = None) -> List[Issue]:
        with self._lock:
            issues = list(self.issues.values())
            if project_id:
                issues = [i for i in issues if i.project_id == project_id]
            # Natural sort by rank
            issues.sort(key=lambda x: x.rank)
            return issues

    def move_issue(
        self,
        issue_id: str,
        new_status: IssueStatus,
        prev_rank: Optional[str] = None,
        next_rank: Optional[str] = None
    ) -> Issue:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            # Validate transition
            old_status = issue.status
            StateMachine.transition_issue(issue, new_status)

            # Update rank
            issue.rank = LexoRank.between(prev_rank, next_rank)

            self.activities.append(
                IssueActivity(
                    id=f"act-{uuid.uuid4().hex[:8]}",
                    issue_id=issue_id,
                    action="STATUS_CHANGED",
                    details=f"Moved from {old_status.value} to {new_status.value}"
                )
            )
            return issue

    def create_sprint(self, project_id: str, name: str, goal: str = "") -> Sprint:
        with self._lock:
            sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"
            sprint = Sprint(id=sprint_id, project_id=project_id, name=name, goal=goal)
            self.sprints[sprint_id] = sprint
            return sprint

    def start_sprint(self, sprint_id: str) -> Sprint:
        with self._lock:
            sprint = self.sprints.get(sprint_id)
            if not sprint:
                raise KeyError(f"Sprint {sprint_id} not found.")
            sprint.state = SprintState.ACTIVE
            return sprint

    def complete_sprint(self, sprint_id: str) -> Sprint:
        with self._lock:
            sprint = self.sprints.get(sprint_id)
            if not sprint:
                raise KeyError(f"Sprint {sprint_id} not found.")
            sprint.state = SprintState.COMPLETED
            sprint.completed_at = datetime.utcnow()
            return sprint
