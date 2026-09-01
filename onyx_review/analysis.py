"""UI-neutral review results and aggregation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    severity: Severity = Severity.WARNING
    count: int = 1

    def __post_init__(self):
        code = str(self.code).strip()
        message = str(self.message).strip()
        count = int(self.count)
        if not code:
            raise ValueError("Issue code cannot be empty")
        if not message:
            raise ValueError("Issue message cannot be empty")
        if count < 1:
            raise ValueError("Issue count must be positive")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "severity", Severity(self.severity))
        object.__setattr__(self, "count", count)


@dataclass(frozen=True)
class ObjectReview:
    object_name: str
    base_vertices: int
    base_edges: int
    base_faces: int
    base_triangles: int
    evaluated_vertices: int
    evaluated_faces: int
    evaluated_triangles: int
    dimensions: tuple[float, float, float]
    issues: tuple[Issue, ...] = ()

    def __post_init__(self):
        name = str(self.object_name).strip()
        if not name:
            raise ValueError("Object name cannot be empty")
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
        dimensions = tuple(float(value) for value in self.dimensions)
        if len(dimensions) != 3 or any(value < 0 for value in dimensions):
            raise ValueError("Dimensions must contain three non-negative values")
        object.__setattr__(self, "object_name", name)
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "issues", tuple(self.issues))

    @property
    def error_count(self):
        return sum(issue.count for issue in self.issues if issue.severity is Severity.ERROR)

    @property
    def warning_count(self):
        return sum(issue.count for issue in self.issues if issue.severity is Severity.WARNING)

    @property
    def modifier_multiplier(self):
        if self.base_triangles == 0:
            return 0.0 if self.evaluated_triangles == 0 else float("inf")
        return self.evaluated_triangles / self.base_triangles


@dataclass(frozen=True)
class ReviewSummary:
    reviews: tuple[ObjectReview, ...]

    def __post_init__(self):
        object.__setattr__(self, "reviews", tuple(self.reviews))

    @property
    def object_count(self):
        return len(self.reviews)

    @property
    def error_count(self):
        return sum(review.error_count for review in self.reviews)

    @property
    def warning_count(self):
        return sum(review.warning_count for review in self.reviews)

    @property
    def evaluated_triangles(self):
        return sum(review.evaluated_triangles for review in self.reviews)

    @property
    def message(self):
        noun = "mesh" if self.object_count == 1 else "meshes"
        return (
            f"{self.object_count} {noun} · {self.error_count} errors · "
            f"{self.warning_count} warnings"
        )


def format_review_report(summary):
    """Format a complete, portable plain-text report."""
    if not isinstance(summary, ReviewSummary):
        raise TypeError("Expected a ReviewSummary")

    lines = (
        "Onyx Review Report",
        summary.message,
        f"{summary.evaluated_triangles:,} evaluated triangles",
        "",
    )
    output = list(lines)
    for review in summary.reviews:
        output.append(review.object_name)
        multiplier = review.modifier_multiplier
        multiplier_text = f"{multiplier:.2f}x" if math.isfinite(multiplier) else "n/a"
        output.append(
            f"  Geometry: {review.base_triangles:,} base triangles -> "
            f"{review.evaluated_triangles:,} evaluated ({multiplier_text})"
        )
        output.append(
            "  Dimensions: "
            f"{review.dimensions[0]:.3g} x {review.dimensions[1]:.3g} x "
            f"{review.dimensions[2]:.3g} scene units"
        )
        if review.issues:
            for issue in review.issues:
                count = f" ({issue.count:,})" if issue.count > 1 else ""
                output.append(f"  [{issue.severity.value}] {issue.message}{count}")
        else:
            output.append("  No findings")
        output.append("")
    return "\n".join(output).rstrip() + "\n"
