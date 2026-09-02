"""UI-neutral review results and aggregation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class FindingDeltaStatus(str, Enum):
    INTRODUCED = "INTRODUCED"
    RESOLVED = "RESOLVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


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
    triangle_faces: int = 0
    quad_faces: int = 0
    ngon_faces: int = 0
    three_poles: int = 0
    five_poles: int = 0
    six_plus_poles: int = 0
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
            self.triangle_faces,
            self.quad_faces,
            self.ngon_faces,
            self.three_poles,
            self.five_poles,
            self.six_plus_poles,
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


@dataclass(frozen=True)
class FindingDelta:
    object_name: str
    code: str
    message: str
    severity: Severity
    status: FindingDeltaStatus
    baseline_count: int = 0
    current_count: int = 0

    def __post_init__(self):
        object_name = str(self.object_name).strip()
        code = str(self.code).strip()
        message = str(self.message).strip()
        baseline_count = int(self.baseline_count)
        current_count = int(self.current_count)
        status = FindingDeltaStatus(self.status)
        if not object_name or not code or not message:
            raise ValueError("Finding delta identity cannot be empty")
        if baseline_count < 0 or current_count < 0:
            raise ValueError("Finding delta counts cannot be negative")
        if status is FindingDeltaStatus.INTRODUCED and not (
            baseline_count == 0 and current_count > 0
        ):
            raise ValueError("Introduced findings require only a current count")
        if status is FindingDeltaStatus.RESOLVED and not (
            baseline_count > 0 and current_count == 0
        ):
            raise ValueError("Resolved findings require only a baseline count")
        if status in (FindingDeltaStatus.CHANGED, FindingDeltaStatus.UNCHANGED) and not (
            baseline_count > 0 and current_count > 0
        ):
            raise ValueError("Persistent findings require baseline and current counts")
        object.__setattr__(self, "object_name", object_name)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "severity", Severity(self.severity))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "baseline_count", baseline_count)
        object.__setattr__(self, "current_count", current_count)

    @property
    def count_change(self):
        return self.current_count - self.baseline_count


@dataclass(frozen=True)
class ReviewDelta:
    baseline: ReviewSummary
    current: ReviewSummary
    findings: tuple[FindingDelta, ...]

    def __post_init__(self):
        if not isinstance(self.baseline, ReviewSummary) or not isinstance(
            self.current, ReviewSummary
        ):
            raise TypeError("Review delta requires two ReviewSummary values")
        object.__setattr__(self, "findings", tuple(self.findings))

    def with_status(self, status):
        status = FindingDeltaStatus(status)
        return tuple(item for item in self.findings if item.status is status)

    @property
    def introduced(self):
        return self.with_status(FindingDeltaStatus.INTRODUCED)

    @property
    def resolved(self):
        return self.with_status(FindingDeltaStatus.RESOLVED)

    @property
    def changed(self):
        return self.with_status(FindingDeltaStatus.CHANGED)

    @property
    def unchanged(self):
        return self.with_status(FindingDeltaStatus.UNCHANGED)

    @property
    def triangle_change(self):
        return self.current.evaluated_triangles - self.baseline.evaluated_triangles

    @property
    def message(self):
        return (
            f"{len(self.introduced)} introduced · {len(self.resolved)} resolved · "
            f"{len(self.changed)} changed"
        )


def _summary_findings(summary):
    if not isinstance(summary, ReviewSummary):
        raise TypeError("Expected a ReviewSummary")
    findings = {}
    for review in summary.reviews:
        for issue in review.issues:
            key = (review.object_name, issue.code)
            if key in findings:
                raise ValueError(
                    f"Duplicate finding code for {review.object_name}: {issue.code}"
                )
            findings[key] = issue
    return findings


def compare_review_summaries(baseline, current):
    """Compare two complete reviews without depending on Blender UI state."""
    before = _summary_findings(baseline)
    after = _summary_findings(current)
    findings = []
    for object_name, code in sorted(before.keys() | after.keys()):
        old = before.get((object_name, code))
        new = after.get((object_name, code))
        if old is None:
            status = FindingDeltaStatus.INTRODUCED
            issue = new
            baseline_count = 0
            current_count = new.count
        elif new is None:
            status = FindingDeltaStatus.RESOLVED
            issue = old
            baseline_count = old.count
            current_count = 0
        else:
            status = (
                FindingDeltaStatus.UNCHANGED
                if old.count == new.count
                and old.message == new.message
                and old.severity is new.severity
                else FindingDeltaStatus.CHANGED
            )
            issue = new
            baseline_count = old.count
            current_count = new.count
        findings.append(
            FindingDelta(
                object_name=object_name,
                code=code,
                message=issue.message,
                severity=issue.severity,
                status=status,
                baseline_count=baseline_count,
                current_count=current_count,
            )
        )
    return ReviewDelta(baseline, current, tuple(findings))


def format_review_report(summary, *, profile_name=""):
    """Format a complete, portable plain-text report."""
    if not isinstance(summary, ReviewSummary):
        raise TypeError("Expected a ReviewSummary")

    profile_name = str(profile_name).strip()

    lines = [
        "Onyx Reviewer Report",
        summary.message,
    ]
    if profile_name:
        lines.append(f"Profile: {profile_name}")
    lines.extend((f"{summary.evaluated_triangles:,} evaluated triangles", ""))
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
            f"  Face mix: {review.triangle_faces:,} triangles, "
            f"{review.quad_faces:,} quads, {review.ngon_faces:,} ngons"
        )
        output.append(
            f"  Poles: {review.three_poles:,} 3-edge, {review.five_poles:,} 5-edge, "
            f"{review.six_plus_poles:,} 6+-edge"
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


def format_review_delta(delta):
    """Format a portable comparison between a saved baseline and the current review."""
    if not isinstance(delta, ReviewDelta):
        raise TypeError("Expected a ReviewDelta")
    triangle_change = delta.triangle_change
    triangle_change_text = f"{triangle_change:+,}"
    output = [
        "Onyx Reviewer Delta",
        f"Baseline: {delta.baseline.message}",
        f"Current: {delta.current.message}",
        (
            f"Evaluated triangles: {delta.baseline.evaluated_triangles:,} -> "
            f"{delta.current.evaluated_triangles:,} ({triangle_change_text})"
        ),
        delta.message,
        f"{len(delta.unchanged)} unchanged",
        "",
    ]
    sections = (
        ("Introduced", delta.introduced),
        ("Resolved", delta.resolved),
        ("Changed", delta.changed),
        ("Unchanged", delta.unchanged),
    )
    for heading, findings in sections:
        if not findings:
            continue
        output.append(heading)
        for item in findings:
            if item.status is FindingDeltaStatus.CHANGED:
                count = f" ({item.baseline_count:,} -> {item.current_count:,})"
            else:
                value = item.current_count or item.baseline_count
                count = f" ({value:,})" if value > 1 else ""
            output.append(f"  {item.object_name} · {item.message}{count}")
        output.append("")
    return "\n".join(output).rstrip() + "\n"
