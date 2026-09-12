"""Immutable review results and the versioned portable report shape."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


REPORT_SCHEMA = "onyx.reviewer.report/1"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    message: str
    severity: str
    count: int

    def __post_init__(self):
        if not str(self.rule_id).strip() or not str(self.message).strip():
            raise ValueError("Finding identity cannot be empty")
        severity = str(self.severity).strip().upper()
        if severity not in {"ERROR", "WARNING"}:
            raise ValueError(f"Invalid finding severity: {severity}")
        if int(self.count) < 1:
            raise ValueError("Finding count must be positive")
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "count", int(self.count))


@dataclass(frozen=True)
class ObjectResult:
    object_name: str
    base_vertices: int
    base_edges: int
    base_faces: int
    base_triangles: int
    evaluated_vertices: int
    evaluated_faces: int
    evaluated_triangles: int
    findings: tuple[Finding, ...]

    def __post_init__(self):
        if not str(self.object_name).strip():
            raise ValueError("Reviewed object name cannot be empty")
        counts = (
            self.base_vertices,
            self.base_edges,
            self.base_faces,
            self.base_triangles,
            self.evaluated_vertices,
            self.evaluated_faces,
            self.evaluated_triangles,
        )
        if any(int(value) < 0 for value in counts):
            raise ValueError("Geometry counts cannot be negative")
        object.__setattr__(self, "findings", tuple(self.findings))

    @property
    def error_count(self):
        return sum(1 for finding in self.findings if finding.severity == "ERROR")

    @property
    def warning_count(self):
        return sum(1 for finding in self.findings if finding.severity == "WARNING")


@dataclass(frozen=True)
class ReviewReport:
    addon_version: str
    blender_version: str
    edition: str
    profile: str
    scope: str
    objects: tuple[ObjectResult, ...]
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            object.__setattr__(self, "generated_at", datetime.now(timezone.utc).isoformat())
        object.__setattr__(self, "objects", tuple(self.objects))

    @property
    def error_count(self):
        return sum(result.error_count for result in self.objects)

    @property
    def warning_count(self):
        return sum(result.warning_count for result in self.objects)

    def to_dict(self):
        return {
            "schema": REPORT_SCHEMA,
            "generated_at": self.generated_at,
            "addon_version": self.addon_version,
            "blender_version": self.blender_version,
            "edition": self.edition,
            "profile": self.profile,
            "scope": self.scope,
            "summary": {
                "objects": len(self.objects),
                "errors": self.error_count,
                "warnings": self.warning_count,
            },
            "objects": [asdict(result) for result in self.objects],
        }
