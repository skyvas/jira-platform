"""In-memory thread-safe store with auto-increment keys, persistence, auth, and notifications."""
from __future__ import annotations
from datetime import datetime
import hashlib
import os
import re
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.models.domain import (
    Attachment, Board, ColumnConfig, ColumnLane, Comment, Issue, IssueActivity,
    IssueStatus, Notification, NotificationType, Priority, Project, Role,
    Sprint, SprintState, User
)
from backend.services.rank_service import LexoRank
from backend.services.state_machine import StateMachine


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    expected, _ = hash_password(password, salt)
    return expected == pwd_hash


_UNSET = object()


class OrbitStore:

    """Thread-safe state repository for Orbit entities, users, and notifications."""

    def __init__(self):
        self._lock = threading.RLock()
        self.projects: Dict[str, Project] = {}
        self.boards: Dict[str, Board] = {}
        self.issues: Dict[str, Issue] = {}
        self.sprints: Dict[str, Sprint] = {}
        self.activities: List[IssueActivity] = []

        # Users and Auth
        self.users: Dict[str, dict] = {}  # user_id -> {user: User, hash: str, salt: str}
        self.sessions: Dict[str, dict] = {}  # session_token -> {user_id: str, created_at: datetime}

        # Notifications
        self.notifications: List[Notification] = []

        # Seed initial data
        self._seed_default_users()
        self._seed_default_projects_and_issues()

    def _seed_default_users(self):
        # 1. Admin user
        self._create_seed_user(
            username="admin",
            password="admin123",
            full_name="System Admin",
            email="admin@orbit.local",
            role=Role.ADMIN,
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=admin"
        )
        # 2. Member user
        self._create_seed_user(
            username="alex",
            password="alex123",
            full_name="Alex Chen",
            email="alex@orbit.local",
            role=Role.MEMBER,
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=alex"
        )
        # 3. Viewer user
        self._create_seed_user(
            username="sam",
            password="sam123",
            full_name="Sam Taylor",
            email="sam@orbit.local",
            role=Role.VIEWER,
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=sam"
        )

    def _create_seed_user(self, username: str, password: str, full_name: str, email: str, role: Role, avatar_url: Optional[str] = None):
        user_id = f"user-{username.lower()}"
        pwd_hash, salt = hash_password(password)
        user = User(
            id=user_id,
            username=username.lower(),
            full_name=full_name,
            email=email,
            role=role,
            avatar_url=avatar_url
        )
        self.users[user_id] = {
            "user": user,
            "hash": pwd_hash,
            "salt": salt
        }

    def _seed_default_projects_and_issues(self):
        # Project 1: PROJ (Core Platform)
        proj = self.create_project("PROJ", "Core Platform", "Primary platform engineering workspace")

        # Project 2: MOBILE (Mobile Experience)
        mobile_proj = self.create_project("MOBILE", "Mobile Experience", "iOS and Android client applications")

        # Seed multiple Sprints for PROJ
        sprint1 = self.create_sprint(
            project_id=proj.id,
            name="Sprint 1 - Core Platform Architecture",
            goal="Establish robust state machine, auth session controls, and live board synchronization",
            start_date="2026-09-01",
            end_date="2026-09-14",
            duration_weeks=2
        )
        self.start_sprint(sprint1.id)

        sprint2 = self.create_sprint(
            project_id=proj.id,
            name="Sprint 2 - Enterprise Agile & Sprints",
            goal="Multi-sprint velocity tracking, prominent assignees, and custom workflow columns",
            start_date="2026-09-15",
            end_date="2026-09-29",
            duration_weeks=2
        )

        # Seed issues for PROJ with sprint linkage
        i1 = self.create_issue(
            project_id=proj.id,
            title="Implement Real-time WebSocket Board Updates",
            description="Add WebSocket or SSE streaming for real-time synchronization between active users.",
            status=IssueStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            assignee="alex",
            tags=["Backend", "Performance", "WebSocket"],
            sprint_id=sprint1.id
        )

        i2 = self.create_issue(
            project_id=proj.id,
            title="Security Audit on Session Cookies",
            description="Verify HttpOnly, SameSite=Lax flags and session token entropy across browser restarts.",
            status=IssueStatus.REVIEW,
            priority=Priority.CRITICAL,
            assignee="admin",
            tags=["Security", "Auth"],
            sprint_id=sprint1.id
        )

        i3 = self.create_issue(
            project_id=proj.id,
            title="Design System Glassmorphism Polish",
            description="Ensure backdrop filters and glowing accents render smoothly across dark mode themes.",
            status=IssueStatus.TODO,
            priority=Priority.MEDIUM,
            assignee="sam",
            tags=["UI/UX", "Frontend"],
            sprint_id=sprint1.id
        )

        i4 = self.create_issue(
            project_id=proj.id,
            title="Initial Kanban Architecture Draft",
            description="Completed architecture document and deterministic verification rules.",
            status=IssueStatus.DONE,
            priority=Priority.LOW,
            assignee="admin",
            tags=["Documentation"],
            sprint_id=sprint1.id
        )

        # Seed planned issue for Sprint 2
        self.create_issue(
            project_id=proj.id,
            title="Sprint Velocity Metrics & Cumulative Flow",
            description="Visualize completed vs carryover points across historical sprints.",
            status=IssueStatus.TODO,
            priority=Priority.MEDIUM,
            assignee="alex",
            tags=["Metrics", "Agile"],
            sprint_id=sprint2.id
        )

        # Seed issue for MOBILE
        self.create_issue(
            project_id=mobile_proj.id,
            title="Offline Cache for Mobile Kanban",
            description="Enable SQLite caching on iOS and Android for offline card reordering.",
            status=IssueStatus.TODO,
            priority=Priority.HIGH,
            assignee="alex",
            tags=["Mobile", "Offline"]
        )

        # Add sample comment with mention
        self.add_comment(
            issue_id=i1.id,
            author_username="admin",
            author_name="System Admin",
            author_role=Role.ADMIN,
            content="Hey @alex, please ensure reconnect logic backoff is included."
        )

        # Add sample comment on i2
        self.add_comment(
            issue_id=i2.id,
            author_username="alex",
            author_name="Alex Chen",
            author_role=Role.MEMBER,
            content="@admin Review complete, session token entropy verified at 256 bits."
        )

    # ------------------ User & Auth Methods ------------------

    def get_users(self) -> List[User]:
        with self._lock:
            return [data["user"] for data in self.users.values()]

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self._lock:
            u_clean = username.lower().strip().lstrip("@")
            for data in self.users.values():
                if data["user"].username == u_clean:
                    return data["user"]
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            data = self.users.get(user_id)
            return data["user"] if data else None

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        role: Role = Role.MEMBER
    ) -> User:
        with self._lock:
            u_clean = username.lower().strip()
            if self.get_user_by_username(u_clean):
                raise ValueError(f"User with username '{username}' already exists.")

            user_id = f"user-{uuid.uuid4().hex[:8]}"
            pwd_hash, salt = hash_password(password)
            user = User(
                id=user_id,
                username=u_clean,
                full_name=full_name,
                email=email,
                role=role,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={u_clean}"
            )
            self.users[user_id] = {
                "user": user,
                "hash": pwd_hash,
                "salt": salt
            }
            return user

    def _find_user_entry(self, user_id: str):
        data = self.users.get(user_id)
        if not data:
            u_clean = user_id.lower().strip().lstrip("@")
            for uid, entry in self.users.items():
                if entry["user"].username == u_clean or entry["user"].id == user_id:
                    return entry
        return data

    def update_user_role(self, user_id: str, new_role: Role) -> User:
        with self._lock:
            data = self._find_user_entry(user_id)
            if not data:
                raise KeyError(f"User '{user_id}' not found.")
            data["user"].role = new_role
            return data["user"]

    def update_user_name(self, user_id: str, new_full_name: str) -> User:
        with self._lock:
            data = self._find_user_entry(user_id)
            if not data:
                raise KeyError(f"User '{user_id}' not found.")
            data["user"].full_name = new_full_name.strip()
            return data["user"]

    def update_user_password(self, user_id: str, new_password: str) -> User:
        with self._lock:
            data = self._find_user_entry(user_id)
            if not data:
                raise KeyError(f"User '{user_id}' not found.")
            pwd_hash, salt = hash_password(new_password)
            data["hash"] = pwd_hash
            data["salt"] = salt
            return data["user"]

    def authenticate(self, username: str, password: str) -> Optional[User]:
        with self._lock:
            u_clean = username.lower().strip()
            for data in self.users.values():
                if data["user"].username == u_clean:
                    if verify_password(password, data["hash"], data["salt"]):
                        return data["user"]
                    return None
            return None

    def create_session(self, user_id: str) -> str:
        with self._lock:
            token = uuid.uuid4().hex + uuid.uuid4().hex
            self.sessions[token] = {
                "user_id": user_id,
                "created_at": datetime.utcnow()
            }
            return token

    def get_session_user(self, session_token: Optional[str]) -> Optional[User]:
        if not session_token:
            return None
        with self._lock:
            session = self.sessions.get(session_token)
            if not session:
                return None
            return self.get_user_by_id(session["user_id"])

    def delete_session(self, session_token: Optional[str]) -> bool:
        if not session_token:
            return False
        with self._lock:
            if session_token in self.sessions:
                del self.sessions[session_token]
                return True
            return False

    # ------------------ Notifications ------------------

    def create_notification(
        self,
        user_username: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        issue_id: str,
        issue_key: str
    ) -> Notification:
        with self._lock:
            u_clean = user_username.lower().strip().lstrip("@")
            notif = Notification(
                id=f"notif-{uuid.uuid4().hex[:8]}",
                user_username=u_clean,
                type=notification_type,
                title=title,
                message=message,
                issue_id=issue_id,
                issue_key=issue_key,
                created_at=datetime.utcnow(),
                read=False
            )
            self.notifications.insert(0, notif)
            return notif

    def get_user_notifications(self, username: str) -> List[Notification]:
        with self._lock:
            u_clean = username.lower().strip().lstrip("@")
            return [n for n in self.notifications if n.user_username == u_clean]

    def toggle_notification_read(self, notification_id: str, read: Optional[bool] = None) -> Notification:
        with self._lock:
            for notif in self.notifications:
                if notif.id == notification_id:
                    notif.read = not notif.read if read is None else read
                    return notif
            raise KeyError(f"Notification {notification_id} not found.")

    def mark_all_notifications_read(self, username: str) -> int:
        with self._lock:
            u_clean = username.lower().strip().lstrip("@")
            count = 0
            for notif in self.notifications:
                if notif.user_username == u_clean and not notif.read:
                    notif.read = True
                    count += 1
            return count

    # ------------------ Project & Board Methods ------------------

    def create_project(
        self,
        key: str,
        name: str,
        description: str = "",
        custom_columns: Optional[List[ColumnConfig]] = None
    ) -> Project:
        with self._lock:
            key_upper = key.strip().upper()
            proj_id = f"proj-{key_upper.lower()}"
            proj = Project(id=proj_id, key=key_upper, name=name, description=description)
            self.projects[proj_id] = proj

            # Provision board for this project
            board_id = f"board-{proj_id}"
            if custom_columns and len(custom_columns) > 0:
                columns = [
                    ColumnLane(
                        id=c.id or f"col-{uuid.uuid4().hex[:6]}",
                        name=c.name,
                        status=c.status.upper(),
                        order_index=c.order_index if c.order_index is not None else idx
                    )
                    for idx, c in enumerate(custom_columns)
                ]
            else:
                columns = [
                    ColumnLane(id="col-backlog", name="Backlog", status="BACKLOG", order_index=0),
                    ColumnLane(id="col-todo", name="To Do", status="TODO", order_index=1),
                    ColumnLane(id="col-progress", name="In Progress", status="IN_PROGRESS", order_index=2),
                    ColumnLane(id="col-review", name="In Review", status="REVIEW", order_index=3),
                    ColumnLane(id="col-done", name="Done", status="DONE", order_index=4),
                ]
            self.boards[board_id] = Board(
                id=board_id,
                project_id=proj_id,
                name=f"{name} Board",
                columns=columns
            )
            return proj

    def update_board_columns(self, project_id: str, new_columns: List[ColumnConfig]) -> Board:
        with self._lock:
            board = self.get_board(project_id)
            if not board:
                raise KeyError(f"Board for project '{project_id}' not found.")
            columns = [
                ColumnLane(
                    id=c.id or f"col-{uuid.uuid4().hex[:6]}",
                    name=c.name,
                    status=c.status.upper(),
                    order_index=c.order_index if c.order_index is not None else idx
                )
                for idx, c in enumerate(new_columns)
            ]
            board.columns = columns
            return board

    def get_board(self, project_id: Optional[str] = None) -> Board:
        with self._lock:
            if project_id:
                for b in self.boards.values():
                    if b.project_id == project_id:
                        return b
            if self.boards:
                return next(iter(self.boards.values()))
            # Fallback
            proj = next(iter(self.projects.values()))
            return self.boards.get(f"board-{proj.id}")

    # ------------------ Issue Methods ------------------

    def create_issue(
        self,
        project_id: str,
        title: str,
        description: str = "",
        status: Any = IssueStatus.TODO,
        priority: Priority = Priority.MEDIUM,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sprint_id: Optional[str] = None
    ) -> Issue:
        with self._lock:
            proj = self.projects.get(project_id)
            if not proj:
                # Try finding by key
                for p in self.projects.values():
                    if p.key.upper() == project_id.upper():
                        proj = p
                        break
            if not proj:
                proj = next(iter(self.projects.values()))

            proj.issue_counter += 1
            issue_key = f"{proj.key}-{proj.issue_counter}"
            issue_id = f"issue-{uuid.uuid4().hex[:8]}"

            # Calculate rank
            existing = [i for i in self.issues.values() if i.project_id == proj.id and i.status == status]
            last_rank = existing[-1].rank if existing else None
            new_rank = LexoRank.between(last_rank, None)

            clean_tags = [t.strip() for t in (tags or []) if t.strip()]

            # Determine status string / enum
            status_val = status.value if hasattr(status, "value") else str(status)

            issue = Issue(
                id=issue_id,
                key=issue_key,
                project_id=proj.id,
                title=title,
                description=description,
                status=status_val,
                priority=priority,
                rank=new_rank,
                assignee=assignee,
                sprint_id=sprint_id,
                tags=clean_tags,
                attachments=[],
                comments=[]
            )
            self.issues[issue_id] = issue

            # Notify assignee if assigned on creation
            if assignee:
                self.create_notification(
                    user_username=assignee,
                    notification_type=NotificationType.ASSIGNED,
                    title=f"Assigned to {issue_key}",
                    message=f"You were assigned to {issue_key}: '{title}'",
                    issue_id=issue_id,
                    issue_key=issue_key
                )

            return issue

    def get_issues(self, project_id: Optional[str] = None) -> List[Issue]:
        with self._lock:
            issues = list(self.issues.values())
            if project_id:
                # Match either project_id or project key
                issues = [
                    i for i in issues
                    if i.project_id == project_id or i.key.split("-")[0].upper() == project_id.upper()
                ]
            # Natural sort by rank
            issues.sort(key=lambda x: x.rank)
            return issues

    def get_issue_by_id(self, issue_id: str) -> Optional[Issue]:
        with self._lock:
            if issue_id in self.issues:
                return self.issues[issue_id]
            for issue in self.issues.values():
                if issue.key.lower() == issue_id.lower() or issue.id.lower() == issue_id.lower():
                    return issue
            m = re.match(r"^iss-(\d+)$", issue_id, re.IGNORECASE)
            if m:
                num = m.group(1)
                for issue in self.issues.values():
                    if issue.key.endswith(f"-{num}"):
                        return issue
            return None

    def update_issue(
        self,
        issue_id: str,
        title: Any = _UNSET,
        description: Any = _UNSET,
        priority: Any = _UNSET,
        assignee: Any = _UNSET,
        tags: Any = _UNSET,
        sprint_id: Any = _UNSET,
        updater_username: Optional[str] = None
    ) -> Issue:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            old_assignee = issue.assignee
            if title is not _UNSET:
                issue.title = title if title is not None else ""
            if description is not _UNSET:
                issue.description = description if description is not None else ""
            if priority is not _UNSET:
                if priority is not None:
                    issue.priority = priority
            if assignee is not _UNSET:
                if assignee is None or (isinstance(assignee, str) and not assignee.strip()):
                    issue.assignee = None
                else:
                    issue.assignee = str(assignee).strip()
            if tags is not _UNSET:
                issue.tags = [t.strip() for t in (tags or []) if t.strip()]
            if sprint_id is not _UNSET:
                if sprint_id is None or (isinstance(sprint_id, str) and not sprint_id.strip()):
                    issue.sprint_id = None
                else:
                    issue.sprint_id = str(sprint_id).strip()

            issue.updated_at = datetime.utcnow()

            # Record assignment change activity
            if assignee is not _UNSET and old_assignee != issue.assignee:
                if issue.assignee is None:
                    details_msg = f"Unassigned from {old_assignee}" if old_assignee else "Unassigned ticket"
                else:
                    details_msg = f"Assigned to {issue.assignee}" + (f" (was {old_assignee})" if old_assignee else "")
                self.activities.append(
                    IssueActivity(
                        id=f"act-{uuid.uuid4().hex[:8]}",
                        issue_id=issue_id,
                        action="ASSIGNEE_CHANGED",
                        details=details_msg
                    )
                )

            # Trigger notification if assignee changed
            if issue.assignee and issue.assignee != old_assignee:
                self.create_notification(
                    user_username=issue.assignee,
                    notification_type=NotificationType.ASSIGNED,
                    title=f"Assigned to {issue.key}",
                    message=f"You were assigned to {issue.key}: '{issue.title}'",
                    issue_id=issue.id,
                    issue_key=issue.key
                )
            if old_assignee and old_assignee != issue.assignee:
                self.create_notification(
                    user_username=old_assignee,
                    notification_type=NotificationType.UNASSIGNED,
                    title=f"Unassigned from {issue.key}",
                    message=f"You were unassigned from {issue.key}: '{issue.title}' by {updater_username or 'a team member'}.",
                    issue_id=issue.id,
                    issue_key=issue.key
                )
            elif issue.assignee and issue.assignee == old_assignee and issue.assignee != (updater_username or ""):
                # Notify assignee of ticket update
                self.create_notification(
                    user_username=issue.assignee,
                    notification_type=NotificationType.UPDATE,
                    title=f"Updated: {issue.key}",
                    message=f"Ticket {issue.key} was updated by {updater_username or 'a team member'}.",
                    issue_id=issue.id,
                    issue_key=issue.key
                )


            return issue

    def move_issue(
        self,
        issue_id: str,
        new_status: Any,
        prev_rank: Optional[str] = None,
        next_rank: Optional[str] = None,
        mover_username: Optional[str] = None
    ) -> Issue:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            # Validate transition
            old_status = issue.status
            board = self.get_board(issue.project_id)
            board_cols = [c.status for c in board.columns] if board and board.columns else None
            StateMachine.transition_issue(issue, new_status, board_columns=board_cols)

            # Update rank
            issue.rank = LexoRank.between(prev_rank, next_rank)

            old_str = old_status.value if hasattr(old_status, 'value') else str(old_status)
            new_str = new_status.value if hasattr(new_status, 'value') else str(new_status)

            self.activities.append(
                IssueActivity(
                    id=f"act-{uuid.uuid4().hex[:8]}",
                    issue_id=issue_id,
                    action="STATUS_CHANGED",
                    details=f"Moved from {old_str} to {new_str}"
                )
            )

            # Notify assignee if status changed and mover is different
            if issue.assignee and issue.assignee != (mover_username or ""):
                self.create_notification(
                    user_username=issue.assignee,
                    notification_type=NotificationType.STATUS_CHANGE,
                    title=f"Status Change: {issue.key}",
                    message=f"{issue.key} was moved from {old_str} to {new_str} by {mover_username or 'a team member'}.",
                    issue_id=issue.id,
                    issue_key=issue.key
                )

            return issue

    # ------------------ Attachments ------------------

    def add_attachment(
        self,
        issue_id: str,
        filename: str,
        file_url: str,
        content_type: str,
        size_bytes: int,
        uploaded_by: str
    ) -> Attachment:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            attachment = Attachment(
                id=f"att-{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                filename=filename,
                file_url=file_url,
                content_type=content_type,
                size_bytes=size_bytes,
                uploaded_by=uploaded_by,
                uploaded_at=datetime.utcnow()
            )
            issue.attachments.append(attachment)
            issue.updated_at = datetime.utcnow()

            # Notify assignee if uploader != assignee
            if issue.assignee and issue.assignee != uploaded_by:
                self.create_notification(
                    user_username=issue.assignee,
                    notification_type=NotificationType.UPDATE,
                    title=f"New Attachment: {issue.key}",
                    message=f"{uploaded_by} uploaded attachment '{filename}' to {issue.key}.",
                    issue_id=issue.id,
                    issue_key=issue.key
                )

            return attachment

    def remove_attachment(self, issue_id: str, attachment_id: str) -> bool:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            before_len = len(issue.attachments)
            issue.attachments = [a for a in issue.attachments if a.id != attachment_id]
            return len(issue.attachments) < before_len

    # ------------------ Comments & @Mentions ------------------

    def add_comment(
        self,
        issue_id: str,
        author_username: str,
        author_name: str,
        author_role: Role,
        content: str,
        images: Optional[List[str]] = None
    ) -> Comment:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")

            # Extract @mentions
            mention_matches = re.findall(r"@([a-zA-Z0-9_-]+)", content)
            mentions = list(set([m.lower() for m in mention_matches]))

            comment = Comment(
                id=f"cmt-{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                author_username=author_username,
                author_name=author_name,
                author_role=author_role,
                content=content,
                mentions=mentions,
                images=images or [],
                created_at=datetime.utcnow()
            )
            issue.comments.append(comment)
            issue.updated_at = datetime.utcnow()

            # Snippet for notification preview
            snippet = content[:60] + "..." if len(content) > 60 else content

            # Notify all mentioned users
            for m in mentions:
                if m != author_username.lower():
                    self.create_notification(
                        user_username=m,
                        notification_type=NotificationType.MENTION,
                        title=f"{author_name} mentioned you in {issue.key}",
                        message=f"{author_name} tagged you: \"{snippet}\"",
                        issue_id=issue.id,
                        issue_key=issue.key
                    )

            # Notify assignee if not already mentioned and not author
            if issue.assignee:
                assignee_clean = issue.assignee.lower().lstrip("@")
                if assignee_clean != author_username.lower() and assignee_clean not in mentions:
                    self.create_notification(
                        user_username=assignee_clean,
                        notification_type=NotificationType.COMMENT,
                        title=f"New comment on {issue.key}",
                        message=f"{author_name} commented on {issue.key}: \"{snippet}\"",
                        issue_id=issue.id,
                        issue_key=issue.key
                    )

            return comment

    def get_comments(self, issue_id: str) -> List[Comment]:
        with self._lock:
            issue = self.issues.get(issue_id)
            if not issue:
                raise KeyError(f"Issue {issue_id} not found.")
            return issue.comments

    # ------------------ Sprint Methods ------------------

    def create_sprint(
        self,
        project_id: str,
        name: str,
        goal: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_weeks: Optional[int] = 2
    ) -> Sprint:
        with self._lock:
            sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"
            sprint = Sprint(
                id=sprint_id,
                project_id=project_id,
                name=name,
                goal=goal,
                start_date=start_date,
                end_date=end_date,
                duration_weeks=duration_weeks,
                state=SprintState.PLANNED
            )
            self.sprints[sprint_id] = sprint
            return sprint

    def start_sprint(
        self,
        sprint_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Sprint:
        with self._lock:
            sprint = self.sprints.get(sprint_id)
            if not sprint:
                raise KeyError(f"Sprint {sprint_id} not found.")

            # Deactivate any other active sprint in the same project
            for s in self.sprints.values():
                if s.project_id == sprint.project_id and s.id != sprint_id and s.state == SprintState.ACTIVE:
                    s.state = SprintState.COMPLETED
                    s.completed_at = datetime.utcnow()

            sprint.state = SprintState.ACTIVE
            if start_date:
                sprint.start_date = start_date
            elif not sprint.start_date:
                sprint.start_date = datetime.utcnow().strftime("%Y-%m-%d")
            if end_date:
                sprint.end_date = end_date
            return sprint

    def complete_sprint(
        self,
        sprint_id: str,
        move_incomplete_to: Optional[str] = "backlog"
    ) -> Sprint:
        with self._lock:
            sprint = self.sprints.get(sprint_id)
            if not sprint:
                raise KeyError(f"Sprint {sprint_id} not found.")

            sprint_issues = [i for i in self.issues.values() if i.sprint_id == sprint_id]
            incomplete_issues = [i for i in sprint_issues if str(i.status).upper() != "DONE"]

            target_sprint_id = None
            if move_incomplete_to == "next_sprint":
                planned = [
                    s for s in self.sprints.values()
                    if s.project_id == sprint.project_id and s.state == SprintState.PLANNED and s.id != sprint_id
                ]
                if planned:
                    target_sprint_id = planned[0].id
                else:
                    count = len([s for s in self.sprints.values() if s.project_id == sprint.project_id])
                    next_sprint = self.create_sprint(
                        project_id=sprint.project_id,
                        name=f"Sprint {count + 1}",
                        goal=f"Carryover from {sprint.name}"
                    )
                    target_sprint_id = next_sprint.id
            elif move_incomplete_to and move_incomplete_to != "backlog" and move_incomplete_to in self.sprints:
                target_sprint_id = move_incomplete_to

            for issue in incomplete_issues:
                issue.sprint_id = target_sprint_id
                issue.updated_at = datetime.utcnow()

            sprint.state = SprintState.COMPLETED
            sprint.completed_at = datetime.utcnow()

            return sprint

    def get_sprint_summary(self, sprint_id: str) -> dict:
        with self._lock:
            sprint = self.sprints.get(sprint_id)
            if not sprint:
                raise KeyError(f"Sprint {sprint_id} not found.")
            sprint_issues = [i for i in self.issues.values() if i.sprint_id == sprint_id]
            completed = [i for i in sprint_issues if str(i.status).upper() == "DONE"]
            incomplete = [i for i in sprint_issues if str(i.status).upper() != "DONE"]
            return {
                "sprint": sprint,
                "total_issues": len(sprint_issues),
                "completed_count": len(completed),
                "incomplete_count": len(incomplete),
                "completion_percentage": round((len(completed) / len(sprint_issues) * 100), 1) if sprint_issues else 0.0
            }

    def get_sprint_history(self, project_id: str) -> List[dict]:
        with self._lock:
            sprints = [
                s for s in self.sprints.values()
                if s.project_id == project_id and s.state in {SprintState.COMPLETED, SprintState.CLOSED}
            ]
            sprints.sort(key=lambda s: s.completed_at or s.created_at, reverse=True)
            result = []
            for s in sprints:
                summary = self.get_sprint_summary(s.id)
                result.append(summary)
            return result


# Backward compatibility alias
JiraStore = OrbitStore
