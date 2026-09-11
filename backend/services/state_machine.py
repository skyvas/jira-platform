from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from backend.models.domain import Issue, IssueStatus


def _norm_status(s: Any) -> str:
    if hasattr(s, "value"):
        return str(s.value).upper()
    return str(s).upper()


class InvalidTransitionError(Exception):
    """Raised when an issue transition violates workflow transition policies."""
    pass


class StateMachine:
    """Validates and executes lifecycle state transitions on issues."""

    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "BACKLOG": {"TODO"},
        "TODO": {"IN_PROGRESS", "BACKLOG"},
        "IN_PROGRESS": {"REVIEW", "TODO"},
        "REVIEW": {"DONE", "IN_PROGRESS"},
        "DONE": {"TODO"},  # Reopen
    }

    @classmethod
    def can_transition(
        cls,
        from_status: Any,
        to_status: Any,
        board_columns: Optional[List[str]] = None
    ) -> bool:
        """Returns True if transition is valid or if same status."""
        f_norm = _norm_status(from_status)
        t_norm = _norm_status(to_status)

        if f_norm == t_norm:
            return True

        # Check project custom board column layout if provided
        if board_columns:
            cols = [_norm_status(c) for c in board_columns]
            if f_norm in cols and t_norm in cols:
                idx_from = cols.index(f_norm)
                idx_to = cols.index(t_norm)

                # Reopening from DONE
                if f_norm == "DONE":
                    if t_norm in {"TODO", "BACKLOG", cols[0], cols[1] if len(cols) > 1 else cols[0]}:
                        return True

                # Adjacent step forward or backward
                if abs(idx_to - idx_from) <= 1:
                    return True

                # Direct leap from Backlog to Done is illegal
                if idx_from == 0 and idx_to == len(cols) - 1:
                    return False

                # Fallback to standard transitions if defined
                if f_norm in cls.ALLOWED_TRANSITIONS and t_norm in cls.ALLOWED_TRANSITIONS[f_norm]:
                    return True

                return False

        # Standard state transitions
        if f_norm in cls.ALLOWED_TRANSITIONS:
            if t_norm in cls.ALLOWED_TRANSITIONS[f_norm]:
                return True
            # Allow moving from standard to a custom status if not leaping directly to DONE
            if t_norm not in cls.ALLOWED_TRANSITIONS:
                return f_norm != "BACKLOG"
            return False

        # Moving from a custom status
        return True

    @classmethod
    def transition_issue(
        cls,
        issue: Issue,
        new_status: Any,
        board_columns: Optional[List[str]] = None
    ) -> Issue:
        """
        Applies transition to issue, validating transition rules and
        managing resolved_at timestamp.
        """
        f_norm = _norm_status(issue.status)
        t_norm = _norm_status(new_status)

        if not cls.can_transition(f_norm, t_norm, board_columns):
            raise InvalidTransitionError(
                f"Cannot transition issue {issue.key} from {f_norm} to {t_norm}."
            )

        if t_norm == "DONE":
            checklist = getattr(issue, "checklist", None) or []
            incomplete = [
                item for item in checklist
                if not (getattr(item, "completed", False) or getattr(item, "is_completed", False))
            ]
            if incomplete:
                raise InvalidTransitionError(
                    f"Cannot resolve issue {issue.key}: all acceptance checklist items must be completed before moving to DONE ({len(incomplete)} incomplete)."
                )

        now = datetime.utcnow()
        # Preserve enum if standard status, otherwise string
        try:
            issue.status = IssueStatus(t_norm)
        except ValueError:
            issue.status = t_norm

        issue.updated_at = now

        if t_norm == "DONE":
            issue.resolved_at = now
        elif issue.resolved_at is not None and t_norm != "DONE":
            issue.resolved_at = None

        return issue
