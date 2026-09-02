"""Transactional registration helpers for Blender extension modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import LifecycleError, ValidationError


class LifecycleState(str, Enum):
    NEW = "NEW"
    REGISTERING = "REGISTERING"
    REGISTERED = "REGISTERED"
    UNREGISTERING = "UNREGISTERING"


@dataclass(frozen=True)
class RegistrationStep:
    name: str
    register: object
    unregister: object

    def __post_init__(self):
        if not str(self.name).strip():
            raise ValidationError("Lifecycle step name cannot be empty")
        if not callable(self.register) or not callable(self.unregister):
            raise ValidationError(f"Lifecycle step {self.name!r} requires callable register and unregister functions")


class Lifecycle:
    """Register a set of modules atomically and unregister them in reverse."""

    def __init__(self, owner, steps=()):
        self.owner = str(owner).strip()
        if not self.owner:
            raise ValidationError("Lifecycle owner cannot be empty")
        self._steps = list(steps)
        self._completed = []
        self.state = LifecycleState.NEW

    @property
    def steps(self):
        return tuple(self._steps)

    def add(self, name, register, unregister):
        if self.state is not LifecycleState.NEW:
            raise LifecycleError(f"Cannot change {self.owner} lifecycle while it is {self.state.value.lower()}")
        self._steps.append(RegistrationStep(name, register, unregister))
        return self

    def register(self):
        if self.state is LifecycleState.REGISTERED:
            return False
        if self.state is not LifecycleState.NEW:
            raise LifecycleError(f"Cannot register {self.owner} while it is {self.state.value.lower()}")
        self.state = LifecycleState.REGISTERING
        self._completed = []
        try:
            for step in self._steps:
                step.register()
                self._completed.append(step)
        except Exception as exc:
            cleanup_errors = []
            for completed in reversed(self._completed):
                try:
                    completed.unregister()
                except Exception as cleanup_exc:
                    cleanup_errors.append((completed.name, cleanup_exc))
            self._completed = []
            self.state = LifecycleState.NEW
            raise LifecycleError(
                f"Could not register {self.owner} at step {step.name}: {exc}",
                cause=exc,
                cleanup_errors=cleanup_errors,
            ) from exc
        self.state = LifecycleState.REGISTERED
        return True

    def unregister(self):
        if self.state is LifecycleState.NEW:
            return False
        if self.state is not LifecycleState.REGISTERED:
            raise LifecycleError(f"Cannot unregister {self.owner} while it is {self.state.value.lower()}")
        self.state = LifecycleState.UNREGISTERING
        cleanup_errors = []
        for step in reversed(self._completed):
            try:
                step.unregister()
            except Exception as exc:
                cleanup_errors.append((step.name, exc))
        self._completed = []
        self.state = LifecycleState.NEW
        if cleanup_errors:
            summary = "; ".join(f"{name}: {error}" for name, error in cleanup_errors)
            raise LifecycleError(
                f"Could not fully unregister {self.owner}: {summary}",
                cause=cleanup_errors[0][1],
                cleanup_errors=cleanup_errors,
            )
        return True
