"""Deterministic state transition machine for JiraPlatform issues."""
from datetime import datetime
from typing import Dict, Optional, Set
from backend.models.domain import Issue, IssueStatus


class InvalidTransitionError(Exception):
    """Raised when an issue transition violates workflow transition policies."""
    pass


class StateMachine:
    """Validates and executes lifecycle state transitions on issues."""

    ALLOWED_TRANSITIONS: Dict[IssueStatus, Set[IssueStatus]] = {
        IssueStatus.BACKLOG: {IssueStatus.TODO},
        IssueStatus.TODO: {IssueStatus.IN_PROGRESS, IssueStatus.BACKLOG},
        IssueStatus.IN_PROGRESS: {IssueStatus.REVIEW, IssueStatus.TODO},
        IssueStatus.REVIEW: {IssueStatus.DONE, IssueStatus.IN_PROGRESS},
        IssueStatus.DONE: {IssueStatus.TODO},  # Reopen
    }

    @classmethod
    def can_transition(cls, from_status: IssueStatus, to_status: IssueStatus) -> bool:
        """Returns True if transition is valid or if same status."""
        if from_status == to_status:
            return True
        return to_status in cls.ALLOWED_TRANSITIONS.get(from_status, set())

    @classmethod
    def transition_issue(cls, issue: Issue, new_status: IssueStatus) -> Issue:
        """
        Applies transition to issue, validating transition rules and
        managing resolved_at timestamp.
        """
        if not cls.can_transition(issue.status, new_status):
            raise InvalidTransitionError(
                f"Cannot transition issue {issue.key} from {issue.status.value} to {new_status.value}."
            )

        now = datetime.utcnow()
        issue.status = new_status
        issue.updated_at = now

        if new_status == IssueStatus.DONE:
            issue.resolved_at = now
        elif issue.resolved_at is not None and new_status != IssueStatus.DONE:
            issue.resolved_at = None

        return issue
