"""Exercise UI-neutral Onyx Review result aggregation."""

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PATH = PROJECT_ROOT / "onyx_review" / "analysis.py"
SPEC = importlib.util.spec_from_file_location("onyx_review_analysis_test_module", ANALYSIS_PATH)
ANALYSIS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYSIS
SPEC.loader.exec_module(ANALYSIS)
Issue = ANALYSIS.Issue
ObjectReview = ANALYSIS.ObjectReview
ReviewSummary = ANALYSIS.ReviewSummary
Severity = ANALYSIS.Severity
format_review_report = ANALYSIS.format_review_report


def raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as exc:
        return exc
    raise AssertionError(f"Expected {error_type.__name__}")


def review(name, base, evaluated, issues=()):
    return ObjectReview(
        name,
        base_vertices=8,
        base_edges=12,
        base_faces=6,
        base_triangles=base,
        evaluated_vertices=24,
        evaluated_faces=18,
        evaluated_triangles=evaluated,
        dimensions=(2.0, 3.0, 4.0),
        issues=issues,
    )


def main():
    warning = Issue("mesh.boundary", "Open boundary edges", count=4)
    error = Issue("mesh.degenerate", "Degenerate faces", Severity.ERROR, 2)
    item = review("Crate", 12, 48, (warning, error))
    assert item.modifier_multiplier == 4.0
    assert item.warning_count == 4
    assert item.error_count == 2

    summary = ReviewSummary((item, review("Barrel", 20, 20)))
    assert summary.object_count == 2
    assert summary.evaluated_triangles == 68
    assert summary.error_count == 2
    assert summary.warning_count == 4
    assert summary.message == "2 meshes · 2 errors · 4 warnings"
    report = format_review_report(summary)
    assert report.startswith("Onyx Review Report\n")
    assert "Crate" in report and "12 base triangles -> 48 evaluated (4.00x)" in report
    assert "[ERROR] Degenerate faces (2)" in report
    assert "Barrel" in report and "No findings" in report

    raises(ValueError, Issue, "", "Missing code")
    raises(ValueError, Issue, "bad", "", count=1)
    raises(ValueError, Issue, "bad", "Bad count", count=0)
    raises(
        ValueError,
        ObjectReview,
        "",
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        (0.0, 0.0, 0.0),
    )
    raises(TypeError, format_review_report, object())
    print("ONYX_REVIEW_ANALYSIS_OK")


if __name__ == "__main__":
    main()
