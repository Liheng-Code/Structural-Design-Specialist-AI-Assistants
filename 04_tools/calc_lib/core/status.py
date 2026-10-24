"""Check status categories (v1 Part 16) and how they combine.

NOT EVALUATED is never PASS. A set of checks is PASS only if every check in it is PASS and the set is not empty.
Nothing here can produce APPROVED: approval is a human record, not a check status.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT EVALUATED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"
    ENGINEER_REVIEW_REQUIRED = "ENGINEER REVIEW REQUIRED"


# Most severe first. The combined status of a set is the most severe status in it.
SEVERITY: tuple[CheckStatus, ...] = (
    CheckStatus.FAIL,
    CheckStatus.BLOCKED,
    CheckStatus.NOT_EVALUATED,
    CheckStatus.ENGINEER_REVIEW_REQUIRED,
    CheckStatus.WARNING,
    CheckStatus.PASS,
)


class NotEvaluated(Exception):
    """Raised when a check cannot be evaluated: a value, method or clause is missing or unverified.

    Calculation code catches it and records a NOT EVALUATED CheckResult naming what is missing. It is never
    replaced by a default value.
    """

    def __init__(self, reason: str, missing: Iterable[str] = ()) -> None:
        super().__init__(reason)
        self.reason = reason
        self.missing = tuple(missing)


def combine(statuses: Iterable[CheckStatus]) -> CheckStatus:
    """Combined status of a set of mandatory checks. An empty set is NOT EVALUATED, never PASS."""
    seen = set(statuses)
    if not seen:
        return CheckStatus.NOT_EVALUATED
    for s in SEVERITY:
        if s in seen:
            return s
    raise ValueError(f"unknown statuses {seen}")  # pragma: no cover - every CheckStatus is in SEVERITY
