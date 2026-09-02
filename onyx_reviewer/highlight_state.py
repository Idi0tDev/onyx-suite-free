"""Transient 3D Viewport highlights for mesh-review findings."""

from __future__ import annotations

from dataclasses import dataclass

import bpy
import gpu
from gpu_extras.batch import batch_for_shader


@dataclass(frozen=True)
class FindingStyle:
    name: str
    color: tuple


_FINDING_STYLES = {
    "topology.non_manifold": FindingStyle("Red", (1.0, 0.05, 0.12, 0.98)),
    "topology.degenerate": FindingStyle("Rose", (1.0, 0.08, 0.42, 0.98)),
    "topology.duplicate_faces": FindingStyle("Magenta", (0.95, 0.08, 1.0, 0.98)),
    "topology.winding": FindingStyle("Purple", (0.62, 0.24, 1.0, 0.98)),
    "topology.boundary": FindingStyle("Cyan", (0.05, 0.82, 1.0, 0.96)),
    "topology.loose_edges": FindingStyle("Yellow", (1.0, 0.82, 0.05, 0.96)),
    "topology.loose_vertices": FindingStyle("Lime", (0.55, 1.0, 0.12, 0.96)),
    "topology.coincident_vertices": FindingStyle("Orange", (1.0, 0.34, 0.03, 0.96)),
    "topology.disconnected_islands": FindingStyle("Blue", (0.12, 0.42, 1.0, 0.96)),
    "topology.ngons": FindingStyle("Amber", (1.0, 0.58, 0.04, 0.96)),
    "topology_map.triangles": FindingStyle("Gold", (1.0, 0.72, 0.04, 0.96)),
    "topology_map.quads": FindingStyle("Teal", (0.05, 0.86, 0.64, 0.96)),
    "topology_map.ngons": FindingStyle("Coral", (1.0, 0.18, 0.08, 0.98)),
    "topology_map.poles_3": FindingStyle("Sky", (0.05, 0.64, 1.0, 0.96)),
    "topology_map.poles_5": FindingStyle("Violet", (0.58, 0.18, 1.0, 0.98)),
    "topology_map.poles_6_plus": FindingStyle("Pink", (1.0, 0.05, 0.52, 0.98)),
}
_ERROR_STYLE = FindingStyle("Red", (1.0, 0.12, 0.03, 0.98))
_WARNING_STYLE = FindingStyle("Orange", (1.0, 0.48, 0.03, 0.96))


@dataclass(frozen=True)
class Highlight:
    object_name: str
    issue_code: str
    message: str
    severity: str
    domain: str
    element_count: int
    points: tuple
    lines: tuple


_ACTIVE = ()
_OVERVIEW_OBJECT = ""
_OVERVIEW_KEY = ""
_HANDLER = None
_SHADER = None
_BATCHES = None


def active_highlight():
    return _ACTIVE[0] if _ACTIVE else None


def active_highlights():
    return _ACTIVE


def active_overview_key():
    return _OVERVIEW_KEY


def finding_style(issue_code, severity):
    """Return the stable viewport color assigned to a finding type."""
    return _FINDING_STYLES.get(
        issue_code,
        _ERROR_STYLE if severity == "ERROR" else _WARNING_STYLE,
    )


def is_active(object_name, issue_code):
    return bool(
        len(_ACTIVE) == 1
        and _ACTIVE[0].object_name == object_name
        and _ACTIVE[0].issue_code == issue_code
    )


def is_overview_active(object_name, overview_key="FINDINGS"):
    return bool(
        _ACTIVE
        and _OVERVIEW_OBJECT == object_name
        and _OVERVIEW_KEY == overview_key
    )


def _tag_redraw():
    window_manager = getattr(bpy.context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _draw_highlight():
    global _SHADER, _BATCHES
    if not _ACTIVE:
        return

    if _SHADER is None:
        _SHADER = gpu.shader.from_builtin("UNIFORM_COLOR")
        _BATCHES = tuple(
            (
                highlight,
                batch_for_shader(_SHADER, "POINTS", {"pos": highlight.points})
                if highlight.points
                else None,
                batch_for_shader(_SHADER, "LINES", {"pos": highlight.lines})
                if highlight.lines
                else None,
            )
            for highlight in _ACTIVE
        )
    shader = _SHADER
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("NONE")
    try:
        for highlight, point_batch, line_batch in _BATCHES:
            obj = bpy.data.objects.get(highlight.object_name)
            if obj is None or obj.name not in bpy.context.view_layer.objects:
                continue
            if not obj.visible_get():
                continue
            style = finding_style(highlight.issue_code, highlight.severity)
            shader.bind()
            shader.uniform_float("color", style.color)
            if line_batch is not None:
                gpu.state.line_width_set(4.0 if highlight.severity == "ERROR" else 2.5)
                line_batch.draw(shader)
            if point_batch is not None:
                gpu.state.point_size_set(13.0 if highlight.severity == "ERROR" else 10.0)
                point_batch.draw(shader)
    finally:
        gpu.state.line_width_set(1.0)
        gpu.state.point_size_set(1.0)
        gpu.state.depth_test_set("NONE")
        gpu.state.blend_set("NONE")


def make_highlight(
    object_name,
    issue_code,
    message,
    severity,
    domain,
    element_count,
    points,
    lines,
):
    return Highlight(
        object_name=str(object_name),
        issue_code=str(issue_code),
        message=str(message),
        severity=str(severity),
        domain=str(domain),
        element_count=int(element_count),
        points=tuple(points),
        lines=tuple(lines),
    )


def _show(highlights, overview_object="", overview_key=""):
    global _ACTIVE, _OVERVIEW_OBJECT, _OVERVIEW_KEY, _HANDLER, _SHADER, _BATCHES
    highlights = tuple(highlights)
    if not highlights:
        raise ValueError("At least one viewport highlight is required")
    _ACTIVE = highlights
    _OVERVIEW_OBJECT = str(overview_object)
    _OVERVIEW_KEY = str(overview_key)
    _SHADER = None
    _BATCHES = None
    if _HANDLER is None:
        _HANDLER = bpy.types.SpaceView3D.draw_handler_add(
            _draw_highlight,
            (),
            "WINDOW",
            "POST_VIEW",
        )
    _tag_redraw()


def show_highlight(
    object_name,
    issue_code,
    message,
    severity,
    domain,
    element_count,
    points,
    lines,
):
    _show(
        (
            make_highlight(
                object_name,
                issue_code,
                message,
                severity,
                domain,
                element_count,
                points,
                lines,
            ),
        )
    )


def show_overview(object_name, highlights, overview_key="FINDINGS"):
    if overview_key == "FINDINGS":
        highlights = sorted(
            highlights,
            key=lambda highlight: (
                1 if highlight.severity == "ERROR" else 0,
                highlight.issue_code,
            ),
        )
    _show(
        highlights,
        overview_object=object_name,
        overview_key=overview_key,
    )


def clear_highlight():
    global _ACTIVE, _OVERVIEW_OBJECT, _OVERVIEW_KEY, _HANDLER, _SHADER, _BATCHES
    _ACTIVE = ()
    _OVERVIEW_OBJECT = ""
    _OVERVIEW_KEY = ""
    _SHADER = None
    _BATCHES = None
    if _HANDLER is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_HANDLER, "WINDOW")
        except (ReferenceError, ValueError):
            pass
        _HANDLER = None
    _tag_redraw()


def register():
    return None


def unregister():
    clear_highlight()
