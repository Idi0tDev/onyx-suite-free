"""Transient 3D Viewport highlights for mesh-review findings."""

from __future__ import annotations

from dataclasses import dataclass
import textwrap

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from . import compatibility
from ._reviewer_common.palettes import (
    DEFAULT_PALETTE,
    FindingStyle,
    PALETTE_ENUM_ITEMS,
    base_finding_style,
    base_palette_styles,
    fallback_style,
    normalize_palette_id,
    palette_ids,
)
from .mesh_analysis import issue_recommendation


# Compatibility aliases keep the original Onyx style table available to older
# internal checks. Runtime lookup below always honors the active scene palette.
_FINDING_STYLES = base_palette_styles(DEFAULT_PALETTE)
_ERROR_STYLE = fallback_style(DEFAULT_PALETTE, "ERROR")
_WARNING_STYLE = fallback_style(DEFAULT_PALETTE, "WARNING")


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
_PIXEL_HANDLER = None
_SHADER = None
_BATCHES = None
_HOVER_POSITION = None
_HOVER_MONITORS = set()

_HOVER_RADIUS = 15.0
_MAX_HOVER_POINTS = 2_048
_MAX_HOVER_SEGMENTS = 2_048


def active_highlight():
    return _ACTIVE[0] if _ACTIVE else None


def active_highlights():
    return _ACTIVE


def active_overview_key():
    return _OVERVIEW_KEY


def _scene_settings():
    scene = getattr(bpy.context, "scene", None)
    return getattr(scene, "onyx_reviewer", None) if scene is not None else None


def current_palette():
    """Return the valid palette selected by the active scene."""
    settings = _scene_settings()
    palette_id = getattr(settings, "color_palette", DEFAULT_PALETTE)
    try:
        return normalize_palette_id(palette_id)
    except ValueError:
        return DEFAULT_PALETTE


def palette_styles(palette_id):
    """Return a copy of every Free finding and topology-map style."""
    return base_palette_styles(palette_id)


def finding_style(issue_code, severity, palette_id=None):
    """Return a palette-aware viewport style for one finding type."""
    palette_id = (
        current_palette()
        if palette_id is None
        else normalize_palette_id(palette_id)
    )
    return base_finding_style(palette_id, issue_code, severity)


def refresh_colors():
    """Redraw existing evidence in the active scene's current palette."""
    _tag_redraw()


def set_palette(palette_id):
    """Select a valid palette on the active scene without touching results."""
    palette_id = normalize_palette_id(palette_id)
    settings = _scene_settings()
    if settings is not None and hasattr(settings, "color_palette"):
        if settings.color_palette != palette_id:
            settings.color_palette = palette_id
    refresh_colors()
    return palette_id


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


def claim_hover_monitor(key):
    """Reserve one passive mouse listener for a window and 3D Viewport."""
    key = tuple(key)
    if key in _HOVER_MONITORS:
        return False
    _HOVER_MONITORS.add(key)
    return True


def has_hover_monitor(key):
    return tuple(key) in _HOVER_MONITORS


def release_hover_monitor(key):
    _HOVER_MONITORS.discard(tuple(key))


def set_hover_position(region_pointer, x, y):
    global _HOVER_POSITION
    _HOVER_POSITION = (int(region_pointer), float(x), float(y))


def clear_hover_position(region_pointer=None):
    global _HOVER_POSITION
    if (
        region_pointer is None
        or _HOVER_POSITION is None
        or _HOVER_POSITION[0] == int(region_pointer)
    ):
        _HOVER_POSITION = None


def _distance_squared_to_segment(point, start, end):
    segment_x = end[0] - start[0]
    segment_y = end[1] - start[1]
    length_squared = segment_x * segment_x + segment_y * segment_y
    if length_squared == 0.0:
        return (point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2
    amount = (
        (point[0] - start[0]) * segment_x
        + (point[1] - start[1]) * segment_y
    ) / length_squared
    amount = max(0.0, min(1.0, amount))
    nearest = (start[0] + amount * segment_x, start[1] + amount * segment_y)
    return (point[0] - nearest[0]) ** 2 + (point[1] - nearest[1]) ** 2


def _project(region, region_data, coordinate):
    value = view3d_utils.location_3d_to_region_2d(
        region,
        region_data,
        Vector(coordinate),
        default=None,
    )
    return tuple(value) if value is not None else None


def _hovered_highlight(region, region_data, mouse):
    best = None
    best_distance = _HOVER_RADIUS * _HOVER_RADIUS
    highlight_count = max(len(_ACTIVE), 1)
    point_limit = max(64, _MAX_HOVER_POINTS // highlight_count)
    segment_limit = max(64, _MAX_HOVER_SEGMENTS // highlight_count)
    # Reverse order matches the marks drawn last when several issue types overlap.
    for highlight in reversed(_ACTIVE):
        if not issue_recommendation(highlight.issue_code):
            continue

        point_step = max(1, (len(highlight.points) + point_limit - 1) // point_limit)
        for index in range(0, len(highlight.points), point_step):
            projected = _project(region, region_data, highlight.points[index])
            if projected is None:
                continue
            distance = (mouse[0] - projected[0]) ** 2 + (mouse[1] - projected[1]) ** 2
            if distance < best_distance:
                best = highlight
                best_distance = distance

        segment_count = len(highlight.lines) // 2
        segment_step = max(
            1,
            (segment_count + segment_limit - 1) // segment_limit,
        )
        for segment_index in range(0, segment_count, segment_step):
            start_index = segment_index * 2
            start = _project(region, region_data, highlight.lines[start_index])
            end = _project(region, region_data, highlight.lines[start_index + 1])
            if start is None or end is None:
                continue
            distance = _distance_squared_to_segment(mouse, start, end)
            if distance < best_distance:
                best = highlight
                best_distance = distance
    return best


def _draw_rectangle(shader, x, y, width, height, color):
    batch = batch_for_shader(
        shader,
        "TRIS",
        {
            "pos": (
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y),
                (x + width, y + height),
                (x, y + height),
            )
        },
    )
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_tooltip(region, mouse, highlight):
    recommendation = issue_recommendation(highlight.issue_code)
    if not recommendation:
        return

    ui_scale = max(float(bpy.context.preferences.system.ui_scale), 0.75)
    font_id = 0
    font_size = max(11, round(13 * ui_scale))
    blf.size(font_id, font_size)
    title_lines = textwrap.wrap(
        f"{highlight.message} ({highlight.element_count:,})",
        width=48,
    )
    guide_lines = textwrap.wrap(f"Try: {recommendation}", width=58)
    lines = (*title_lines, "", *guide_lines)
    line_height = 18 * ui_scale
    padding = 12 * ui_scale
    widest = max((blf.dimensions(font_id, line)[0] for line in lines), default=0.0)
    width = min(max(widest + padding * 2, 260 * ui_scale), region.width - 16)
    height = line_height * len(lines) + padding * 2

    x = mouse[0] + 18 * ui_scale
    y = mouse[1] + 18 * ui_scale
    if x + width > region.width - 8:
        x = mouse[0] - width - 18 * ui_scale
    if y + height > region.height - 8:
        y = mouse[1] - height - 18 * ui_scale
    x = max(8.0, min(x, region.width - width - 8.0))
    y = max(8.0, min(y, region.height - height - 8.0))

    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    gpu.state.blend_set("ALPHA")
    try:
        _draw_rectangle(shader, x, y, width, height, (0.025, 0.025, 0.025, 0.94))
        style = finding_style(highlight.issue_code, highlight.severity)
        _draw_rectangle(shader, x, y + height - 3 * ui_scale, width, 3 * ui_scale, style.color)

        cursor_y = y + height - padding - line_height
        for index, line in enumerate(lines):
            blf.position(font_id, x + padding, cursor_y, 0)
            if index < len(title_lines):
                blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            else:
                blf.color(font_id, 0.82, 0.82, 0.82, 1.0)
            if line:
                blf.draw(font_id, line)
            cursor_y -= line_height
    finally:
        gpu.state.blend_set("NONE")


def _draw_hover():
    if (
        not _ACTIVE
        or _HOVER_POSITION is None
        or compatibility.review_display_suspended()
    ):
        return
    region = getattr(bpy.context, "region", None)
    region_data = getattr(bpy.context, "region_data", None)
    if region is None or region_data is None:
        return
    if region.as_pointer() != _HOVER_POSITION[0]:
        return
    mouse = _HOVER_POSITION[1:]
    highlight = _hovered_highlight(region, region_data, mouse)
    if highlight is not None:
        _draw_tooltip(region, mouse, highlight)


def _draw_highlight():
    global _SHADER, _BATCHES
    if not _ACTIVE or compatibility.review_display_suspended():
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
    global _ACTIVE, _OVERVIEW_OBJECT, _OVERVIEW_KEY, _HANDLER, _PIXEL_HANDLER
    global _SHADER, _BATCHES
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
    if _PIXEL_HANDLER is None:
        _PIXEL_HANDLER = bpy.types.SpaceView3D.draw_handler_add(
            _draw_hover,
            (),
            "WINDOW",
            "POST_PIXEL",
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
    global _ACTIVE, _OVERVIEW_OBJECT, _OVERVIEW_KEY, _HANDLER, _PIXEL_HANDLER
    global _SHADER, _BATCHES
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
    if _PIXEL_HANDLER is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_PIXEL_HANDLER, "WINDOW")
        except (ReferenceError, ValueError):
            pass
        _PIXEL_HANDLER = None
    clear_hover_position()
    _tag_redraw()


def _production_review_changed(active):
    if active:
        clear_hover_position()
    _tag_redraw()


def register():
    compatibility.register_listener(_production_review_changed)


def unregister():
    compatibility.unregister_listener(_production_review_changed)
    clear_highlight()
    _HOVER_MONITORS.clear()
