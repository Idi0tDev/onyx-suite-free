"""Blender RNA properties for Onyx Reviewer."""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from .review_profiles import PROFILE_ENUM_ITEMS


def _live_review_changed(_settings, context):
    if context is None:
        return
    from . import live_review

    live_review.settings_changed(context.scene)


def _review_option_changed(_settings, context):
    if context is None:
        return
    from . import live_review

    live_review.review_options_changed(context.scene)


def _review_semantics_changed(settings, context):
    """Mark old results as stale and discard comparisons made with other checks."""
    if context is None:
        return
    from . import delta_state, highlight_state, live_review

    settings.review_options_dirty = bool(settings.results)
    for result in settings.results:
        for issue in result.issues:
            issue.delta_status = "NONE"
    delta_state.clear_baseline(context.scene)
    highlight_state.clear_highlight()
    live_review.review_options_changed(context.scene)


def _finding_filter_changed(_settings, context):
    """Discard viewport evidence that no longer matches the visible findings."""
    from . import highlight_state

    active = highlight_state.active_highlights()
    if any(not item.issue_code.startswith("topology_map.") for item in active):
        highlight_state.clear_highlight()
    if context is not None and context.area is not None:
        context.area.tag_redraw()


class OnyxReviewerIssue(bpy.types.PropertyGroup):
    code: StringProperty(description="Stable identifier for this review finding")
    message: StringProperty(description="Artist-facing explanation of the finding")
    severity: EnumProperty(
        items=(
            ("WARNING", "Warning", "Review this condition before delivery"),
            ("ERROR", "Error", "This condition usually requires correction"),
        ),
        description="Importance of the review finding",
    )
    count: IntProperty(default=1, min=1, description="Number of matching elements")
    delta_status: EnumProperty(
        items=(
            ("NONE", "Not Compared", "No baseline comparison is active"),
            ("INTRODUCED", "New", "This finding was not in the saved baseline"),
            ("CHANGED", "Changed", "This finding is still present but its details changed"),
            ("UNCHANGED", "Unchanged", "This finding matches the saved baseline"),
        ),
        default="NONE",
        description="How this finding compares with the saved Review Delta baseline",
    )


class OnyxReviewerResult(bpy.types.PropertyGroup):
    object_ref: PointerProperty(type=bpy.types.Object, description="Reviewed mesh object")
    object_name: StringProperty(description="Name captured when the object was reviewed")
    base_vertices: IntProperty(min=0, description="Vertices in the source mesh")
    base_edges: IntProperty(min=0, description="Edges in the source mesh")
    base_faces: IntProperty(min=0, description="Faces in the source mesh")
    base_triangles: IntProperty(min=0, description="Triangles represented by the source mesh")
    evaluated_vertices: IntProperty(min=0, description="Vertices after visible modifiers")
    evaluated_faces: IntProperty(min=0, description="Faces after visible modifiers")
    evaluated_triangles: IntProperty(min=0, description="Triangles after visible modifiers")
    triangle_faces: IntProperty(min=0, description="Three-sided faces in the source mesh")
    quad_faces: IntProperty(min=0, description="Four-sided faces in the source mesh")
    ngon_faces: IntProperty(min=0, description="Faces with more than four sides in the source mesh")
    three_poles: IntProperty(min=0, description="Source vertices connected to three edges")
    five_poles: IntProperty(min=0, description="Source vertices connected to five edges")
    six_plus_poles: IntProperty(min=0, description="Source vertices connected to six or more edges")
    modifier_multiplier: FloatProperty(min=0.0, description="Evaluated triangle count divided by base triangles")
    dimensions: FloatVectorProperty(size=3, min=0.0, subtype="XYZ", description="World-space object dimensions")
    error_count: IntProperty(min=0, description="Number of error-level findings")
    warning_count: IntProperty(min=0, description="Number of warning-level findings")
    expanded: BoolProperty(default=False, description="Show this object's findings and tools")
    metrics_expanded: BoolProperty(
        default=False,
        description="Show detailed mesh counts and dimensions",
    )
    topology_expanded: BoolProperty(
        default=False,
        description="Show topology-map and class-selection controls",
    )
    issues: CollectionProperty(
        type=OnyxReviewerIssue,
        description="Findings recorded for this reviewed object",
    )


class OnyxReviewerSettings(bpy.types.PropertyGroup):
    more_settings_expanded: BoolProperty(
        default=False,
        description="Show optional review controls",
    )
    topology_rules_expanded: BoolProperty(
        default=False,
        description="Show allowances for intentionally open edges and ngons",
    )
    delta_expanded: BoolProperty(
        default=False,
        description="Show before-and-after comparison controls",
    )
    viewport_tools_expanded: BoolProperty(
        default=False,
        description="Show viewport review modes",
    )
    highlight_legend_expanded: BoolProperty(
        default=False,
        description="Show the exact viewport colors for the current highlight",
    )
    scope: EnumProperty(
        name="Review Scope",
        items=(
            ("ACTIVE", "Active", "Review only the active mesh object"),
            ("SELECTED", "Selected", "Review every selected mesh object"),
            ("COLLECTION", "Collection", "Review meshes in the active collection"),
        ),
        default="ACTIVE",
        description="Choose which mesh objects to inspect",
        update=_review_semantics_changed,
    )
    review_profile: EnumProperty(
        name="Review Profile",
        items=PROFILE_ENUM_ITEMS,
        default="GENERAL",
        description="Choose which groups of findings matter for this review",
        update=_review_semantics_changed,
    )
    check_topology: BoolProperty(
        name="Topology",
        default=True,
        description="Check mesh structure such as boundaries, loose elements, and ngons",
        update=_review_semantics_changed,
    )
    check_transforms: BoolProperty(
        name="Transforms",
        default=True,
        description="Check negative transforms and unapplied scale",
        update=_review_semantics_changed,
    )
    check_asset_setup: BoolProperty(
        name="UVs and Materials",
        default=True,
        description="Check whether meshes have UV maps and material slots",
        update=_review_semantics_changed,
    )
    check_triangle_budget: BoolProperty(
        name="Triangle Budget",
        default=True,
        description="Use the triangle budget as part of the review",
        update=_review_semantics_changed,
    )
    allowed_boundary_edges: IntProperty(
        name="Allowed Open Edges",
        default=0,
        min=0,
        soft_max=1_000,
        description="Ignore the open-edge warning up to this count; zero flags any open edge",
        update=_review_semantics_changed,
    )
    allowed_ngons: IntProperty(
        name="Allowed Ngons",
        default=0,
        min=0,
        soft_max=1_000,
        description="Ignore the ngon warning up to this count; zero flags any ngon",
        update=_review_semantics_changed,
    )
    triangle_budget: IntProperty(
        name="Triangle Budget",
        default=100_000,
        min=0,
        soft_max=1_000_000,
        description="Warn when an evaluated mesh exceeds this count; use zero to disable",
        update=_review_semantics_changed,
    )
    live_review: BoolProperty(
        name="Live Review",
        default=False,
        description="Refresh diagnostics after mesh changes without editing or repairing geometry",
        update=_live_review_changed,
    )
    live_delay: FloatProperty(
        name="Debounce",
        default=0.3,
        min=0.1,
        max=5.0,
        subtype="TIME",
        description="Wait after the last detected change before refreshing diagnostics",
        update=_review_option_changed,
    )
    live_max_vertices: IntProperty(
        name="Live Vertex Limit",
        default=250_000,
        min=0,
        soft_max=2_000_000,
        description="Pause live refreshes above this source-vertex count; use zero to disable the limit",
        update=_review_option_changed,
    )
    finding_filter: EnumProperty(
        name="Finding View",
        items=(
            ("ALL", "All", "Show every finding from the latest review"),
            ("ERRORS", "Errors", "Show conditions that usually require correction"),
            ("WARNINGS", "Warnings", "Show contextual conditions that deserve review"),
            (
                "FIXABLE",
                "On Mesh",
                "Show findings that Reviewer can point out directly on the mesh",
            ),
            ("CHANGES", "Changes", "Show findings introduced or changed since the saved baseline"),
        ),
        default="ALL",
        description="Choose which findings to display without changing the complete report",
        update=_finding_filter_changed,
    )
    results: CollectionProperty(
        type=OnyxReviewerResult,
        description="Object results from the most recent review",
    )
    last_summary: StringProperty(description="Summary of the most recent review")
    total_errors: IntProperty(min=0, description="Total error findings in the most recent review")
    total_warnings: IntProperty(min=0, description="Total warning findings in the most recent review")
    total_triangles: IntProperty(min=0, description="Total evaluated triangles in the most recent review")
    live_status: StringProperty(
        default="Off",
        description="Current state of the optional live diagnostics",
    )
    review_options_dirty: BoolProperty(
        default=False,
        description="The current results were made with earlier review options",
    )
    last_profile: StringProperty(
        description="Profile used for the most recent completed review",
    )


CLASSES = (OnyxReviewerIssue, OnyxReviewerResult, OnyxReviewerSettings)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.onyx_reviewer = PointerProperty(type=OnyxReviewerSettings)


def unregister():
    if hasattr(bpy.types.Scene, "onyx_reviewer"):
        del bpy.types.Scene.onyx_reviewer
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
