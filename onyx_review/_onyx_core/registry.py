"""Thread-safe extension and service discovery for Onyx products."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Iterable

from .errors import (
    DuplicateRegistrationError,
    IncompatibleVersionError,
    MissingExtensionError,
    MissingServiceError,
    ValidationError,
)


_EXTENSION_ID = re.compile(r"^onyx_[a-z0-9_]+$")
_PUBLIC_ID = re.compile(r"^onyx\.[a-z][a-z0-9_.-]*$")


def _nonempty(value, label):
    text = str(value).strip()
    if not text:
        raise ValidationError(f"{label} cannot be empty")
    return text


@dataclass(frozen=True, order=True)
class Version:
    """Small, strict semantic version used at framework boundaries."""

    major: int
    minor: int
    patch: int

    def __post_init__(self):
        for label, value in (("major", self.major), ("minor", self.minor), ("patch", self.patch)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError(f"Version {label} must be a non-negative integer")

    @classmethod
    def parse(cls, value) -> "Version":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
            if not match:
                raise ValidationError(f"Invalid semantic version: {value!r}")
            return cls(*(int(part) for part in match.groups()))
        if isinstance(value, Iterable):
            parts = tuple(value)
            if len(parts) == 3:
                return cls(*parts)
        raise ValidationError(f"Version must be 'major.minor.patch' or three integers: {value!r}")

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def _normalize_public_ids(values, label):
    normalized = tuple(sorted({_nonempty(value, label) for value in values}))
    for value in normalized:
        if not _PUBLIC_ID.fullmatch(value):
            raise ValidationError(f"Invalid {label}: {value!r}")
    return normalized


@dataclass(frozen=True)
class ExtensionRecord:
    """Metadata published by one enabled Onyx extension."""

    extension_id: str
    name: str
    version: Version
    description: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    website: str = ""

    def __post_init__(self):
        extension_id = _nonempty(self.extension_id, "Extension ID")
        if not _EXTENSION_ID.fullmatch(extension_id):
            raise ValidationError("Extension ID must start with 'onyx_' and use lowercase letters, digits, or underscores")
        object.__setattr__(self, "extension_id", extension_id)
        object.__setattr__(self, "name", _nonempty(self.name, "Extension name"))
        object.__setattr__(self, "version", Version.parse(self.version))
        object.__setattr__(self, "description", str(self.description).strip())
        object.__setattr__(self, "capabilities", _normalize_public_ids(self.capabilities, "capability ID"))
        object.__setattr__(self, "website", str(self.website).strip())


@dataclass(frozen=True)
class ServiceRecord:
    """A versioned runtime capability supplied by an enabled extension."""

    service_id: str
    owner_id: str
    version: Version
    provider: Any = field(compare=False, repr=False)
    description: str = ""

    def __post_init__(self):
        service_id = _nonempty(self.service_id, "Service ID")
        if not _PUBLIC_ID.fullmatch(service_id):
            raise ValidationError("Service ID must start with 'onyx.' and use lowercase letters, digits, dots, dashes, or underscores")
        owner_id = _nonempty(self.owner_id, "Service owner ID")
        if not _EXTENSION_ID.fullmatch(owner_id):
            raise ValidationError(f"Invalid service owner ID: {owner_id!r}")
        if self.provider is None:
            raise ValidationError("Service provider cannot be None")
        object.__setattr__(self, "service_id", service_id)
        object.__setattr__(self, "owner_id", owner_id)
        object.__setattr__(self, "version", Version.parse(self.version))
        object.__setattr__(self, "description", str(self.description).strip())


class FrameworkRegistry:
    """Owns runtime registrations while keeping provider lifetimes explicit."""

    def __init__(self):
        self._lock = RLock()
        self._extensions = {}
        self._services = {}

    def register_extension(self, record: ExtensionRecord) -> ExtensionRecord:
        if not isinstance(record, ExtensionRecord):
            raise ValidationError("register_extension expects an ExtensionRecord")
        with self._lock:
            existing = self._extensions.get(record.extension_id)
            if existing is not None:
                if existing != record:
                    raise DuplicateRegistrationError(
                        f"{record.extension_id} is already registered as {existing.name} {existing.version}"
                    )
                return existing
            self._extensions[record.extension_id] = record
            return record

    def unregister_extension(self, extension_id: str) -> bool:
        extension_id = _nonempty(extension_id, "Extension ID")
        with self._lock:
            if self._extensions.pop(extension_id, None) is None:
                return False
            owned = [service_id for service_id, service in self._services.items() if service.owner_id == extension_id]
            for service_id in owned:
                del self._services[service_id]
            return True

    def extension(self, extension_id: str):
        with self._lock:
            return self._extensions.get(extension_id)

    def extensions(self):
        with self._lock:
            return tuple(sorted(self._extensions.values(), key=lambda item: item.extension_id))

    def register_service(self, record: ServiceRecord, *, replace=False) -> ServiceRecord:
        if not isinstance(record, ServiceRecord):
            raise ValidationError("register_service expects a ServiceRecord")
        with self._lock:
            if record.owner_id not in self._extensions:
                raise MissingExtensionError(
                    f"Register extension {record.owner_id} before publishing {record.service_id}"
                )
            existing = self._services.get(record.service_id)
            if existing is not None:
                same_registration = (
                    existing.owner_id == record.owner_id
                    and existing.version == record.version
                    and existing.provider is record.provider
                    and existing.description == record.description
                )
                if same_registration:
                    return existing
                if not replace or existing.owner_id != record.owner_id:
                    raise DuplicateRegistrationError(
                        f"{record.service_id} is already provided by {existing.owner_id} {existing.version}"
                    )
            self._services[record.service_id] = record
            return record

    def unregister_service(self, service_id: str, *, owner_id=None) -> bool:
        service_id = _nonempty(service_id, "Service ID")
        with self._lock:
            existing = self._services.get(service_id)
            if existing is None:
                return False
            if owner_id is not None and existing.owner_id != owner_id:
                raise DuplicateRegistrationError(
                    f"{service_id} belongs to {existing.owner_id}, not {owner_id}"
                )
            del self._services[service_id]
            return True

    def service(self, service_id: str, minimum_version=None):
        service_id = _nonempty(service_id, "Service ID")
        with self._lock:
            record = self._services.get(service_id)
        if record is None:
            return None
        if minimum_version is not None:
            minimum = Version.parse(minimum_version)
            if record.version < minimum:
                raise IncompatibleVersionError(
                    f"{service_id} {record.version} is installed; {minimum} or newer is required"
                )
        return record

    def require_service(self, service_id: str, minimum_version=None) -> ServiceRecord:
        record = self.service(service_id, minimum_version)
        if record is None:
            suffix = f" {Version.parse(minimum_version)} or newer" if minimum_version is not None else ""
            raise MissingServiceError(f"Required service is unavailable: {service_id}{suffix}")
        return record

    def services(self):
        with self._lock:
            return tuple(sorted(self._services.values(), key=lambda item: item.service_id))

    def audit(self):
        """Return invariant violations without exposing mutable registry state."""
        with self._lock:
            return tuple(
                f"{service.service_id} has missing owner {service.owner_id}"
                for service in self._services.values()
                if service.owner_id not in self._extensions
            )
