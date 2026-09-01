"""Transient 3D Viewport highlights for mesh-review findings."""

from __future__ import annotations

from dataclasses import dataclass

import bpy
import gpu
from gpu_extras.batch import batch_for_shader


_ERROR_COLOR = (1.0, 0.12, 0.03, 0.95)
_WARNING_COLOR = (1.0, 0.48, 0.03, 0.95)


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
_HANDLER = None
_SHADER = None
_BATCHES = None


def active_highlight():
    return _ACTIVE[0] if _ACTIVE else None


def active_highlights():
    return _ACTIVE


def is_active(object_name, issue_code):
    return bool(
        len(_ACTIVE) == 1
        and _ACTIVE[0].object_name == object_name
        and _ACTIVE[0].issue_code == issue_code
    )


def is_overview_active(object_name):
    return bool(_ACTIVE and _OVERVIEW_OBJECT == object_name)


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
            color = _ERROR_COLOR if highlight.severity == "ERROR" else _WARNING_COLOR
            shader.bind()
            shader.uniform_float("color", color)
            if line_batch is not None:
                gpu.state.line_width_set(3.0)
                line_batch.draw(shader)
            if point_batch is not None:
                gpu.state.point_size_set(11.0)
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


def _show(highlights, overview_object=""):
    global _ACTIVE, _OVERVIEW_OBJECT, _HANDLER, _SHADER, _BATCHES
    highlights = tuple(highlights)
    if not highlights:
        raise ValueError("At least one viewport highlight is required")
    _ACTIVE = highlights
    _OVERVIEW_OBJECT = str(overview_object)
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


def show_overview(object_name, highlights):
    ordered = sorted(
        highlights,
        key=lambda highlight: (
            1 if highlight.severity == "ERROR" else 0,
            highlight.issue_code,
        ),
    )
    _show(ordered, overview_object=object_name)


def clear_highlight():
    global _ACTIVE, _OVERVIEW_OBJECT, _HANDLER, _SHADER, _BATCHES
    _ACTIVE = ()
    _OVERVIEW_OBJECT = ""
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
