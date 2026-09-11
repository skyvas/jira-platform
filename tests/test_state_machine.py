"""Tests for issue lifecycle state transitions."""
import pytest
from backend.models.domain import Issue, IssueStatus, Priority
from backend.services.state_machine import StateMachine, InvalidTransitionError


def test_valid_forward_transitions():
    issue = Issue(id="1", key="PROJ-1", project_id="p1", title="Task 1", status=IssueStatus.BACKLOG)

    # BACKLOG -> TODO
    StateMachine.transition_issue(issue, IssueStatus.TODO)
    assert issue.status == IssueStatus.TODO
    assert issue.resolved_at is None

    # TODO -> IN_PROGRESS
    StateMachine.transition_issue(issue, IssueStatus.IN_PROGRESS)
    assert issue.status == IssueStatus.IN_PROGRESS

    # IN_PROGRESS -> REVIEW
    StateMachine.transition_issue(issue, IssueStatus.REVIEW)
    assert issue.status == IssueStatus.REVIEW

    # REVIEW -> DONE
    StateMachine.transition_issue(issue, IssueStatus.DONE)
    assert issue.status == IssueStatus.DONE
    assert issue.resolved_at is not None


def test_invalid_transition_rejected():
    issue = Issue(id="1", key="PROJ-1", project_id="p1", title="Task 1", status=IssueStatus.BACKLOG)

    # Backlog directly to Done is illegal
    with pytest.raises(InvalidTransitionError):
        StateMachine.transition_issue(issue, IssueStatus.DONE)


def test_reopen_issue_clears_resolved_at():
    issue = Issue(id="1", key="PROJ-1", project_id="p1", title="Task 1", status=IssueStatus.REVIEW)
    StateMachine.transition_issue(issue, IssueStatus.DONE)
    assert issue.resolved_at is not None

    # Reopen to TODO
    StateMachine.transition_issue(issue, IssueStatus.TODO)
    assert issue.status == IssueStatus.TODO
    assert issue.resolved_at is None


def test_checklist_guard_prevents_transition_to_done_until_completed():
    from backend.models.domain import ChecklistItem
    issue = Issue(
        id="1",
        key="PROJ-1",
        project_id="p1",
        title="Task 1",
        status=IssueStatus.REVIEW,
        checklist=[
            ChecklistItem(id="c1", text="Requirement A", completed=True),
            ChecklistItem(id="c2", text="Requirement B", completed=False),
        ]
    )

    with pytest.raises(InvalidTransitionError, match="all acceptance checklist items must be completed"):
        StateMachine.transition_issue(issue, IssueStatus.DONE)

    # Complete the item
    issue.checklist[1].completed = True
    StateMachine.transition_issue(issue, IssueStatus.DONE)
    assert issue.status == IssueStatus.DONE
    assert issue.resolved_at is not None
