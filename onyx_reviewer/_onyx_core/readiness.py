"""Shared, UI-neutral readiness results for proactive Onyx validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import ValidationError


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Check:
    code: str
    passed: bool
    message: str
    severity: Severity = Severity.ERROR

    def __post_init__(self):
        if not str(self.code).strip():
            raise ValidationError("Readiness check code cannot be empty")
        if not str(self.message).strip():
            raise ValidationError("Readiness check message cannot be empty")
        object.__setattr__(self, "code", str(self.code).strip())
        object.__setattr__(self, "message", str(self.message).strip())
        object.__setattr__(self, "severity", Severity(self.severity))

    @property
    def blocking(self):
        return not self.passed and self.severity is Severity.ERROR


@dataclass(frozen=True)
class ReadinessReport:
    checks: tuple[Check, ...]
    ready_message: str = "Ready"

    def __post_init__(self):
        object.__setattr__(self, "checks", tuple(self.checks))
        if not str(self.ready_message).strip():
            raise ValidationError("Ready message cannot be empty")

    @property
    def ready(self):
        return not any(check.blocking for check in self.checks)

    @property
    def first_blocker(self):
        return next((check for check in self.checks if check.blocking), None)

    @property
    def warnings(self):
        return tuple(check for check in self.checks if not check.passed and check.severity is Severity.WARNING)

    @property
    def message(self):
        blocker = self.first_blocker
        if blocker is not None:
            return blocker.message
        warning = next(iter(self.warnings), None)
        return warning.message if warning is not None else self.ready_message


def evaluate(*checks, ready_message="Ready"):
    return ReadinessReport(tuple(checks), ready_message)
