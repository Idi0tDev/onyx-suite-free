"""Blender RNA properties for Onyx Review."""

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


class OnyxReviewIssue(bpy.types.PropertyGroup):
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


class OnyxReviewResult(bpy.types.PropertyGroup):
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
    expanded: BoolProperty(default=True, description="Show detailed metrics and findings")
    topology_expanded: BoolProperty(
        default=False,
        description="Show topology-map and class-selection controls",
    )
    issues: CollectionProperty(
        type=OnyxReviewIssue,
        description="Findings recorded for this reviewed object",
    )


class OnyxReviewSettings(bpy.types.PropertyGroup):
    scope: EnumProperty(
        name="Review Scope",
        items=(
            ("ACTIVE", "Active", "Review only the active mesh object"),
            ("SELECTED", "Selected", "Review every selected mesh object"),
            ("COLLECTION", "Collection", "Review meshes in the active collection"),
        ),
        default="ACTIVE",
        description="Choose which mesh objects to inspect",
        update=_review_option_changed,
    )
    triangle_budget: IntProperty(
        name="Triangle Budget",
        default=100_000,
        min=0,
        soft_max=1_000_000,
        description="Warn when an evaluated mesh exceeds this count; use zero to disable",
        update=_review_option_changed,
    )
    live_review: BoolProperty(
        name="Live Review",
        default=False,
        description="Refresh diagnostics after mesh changes without editing or repairing geometry",
        update=_live_review_changed,
    )
    live_delay: FloatProperty(
        name="Debounce",
        default=0.75,
        min=0.25,
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
    results: CollectionProperty(
        type=OnyxReviewResult,
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


CLASSES = (OnyxReviewIssue, OnyxReviewResult, OnyxReviewSettings)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.onyx_review = PointerProperty(type=OnyxReviewSettings)


def unregister():
    if hasattr(bpy.types.Scene, "onyx_review"):
        del bpy.types.Scene.onyx_review
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
