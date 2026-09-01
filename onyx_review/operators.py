"""Operators for mesh review, navigation, and viewport modes."""

from __future__ import annotations

import math

import bpy
from bpy.props import EnumProperty, StringProperty

from .analysis import Issue, ObjectReview, ReviewSummary, Severity, format_review_report
from .mesh_analysis import (
    issue_overlay_geometry,
    issue_overlays_geometry,
    issue_selection_domain,
    review_object,
    select_issue_elements,
)
from . import highlight_state, viewport_state


def scoped_meshes(context, scope):
    if scope == "ACTIVE":
        candidates = (context.active_object,) if context.active_object else ()
    elif scope == "SELECTED":
        candidates = tuple(context.selected_objects)
    elif scope == "COLLECTION":
        candidates = tuple(context.collection.all_objects) if context.collection else ()
    else:
        raise ValueError(f"Unknown review scope: {scope}")
    return tuple(sorted((obj for obj in candidates if obj.type == "MESH"), key=lambda obj: obj.name))


def review_blocker(context, scope):
    """Return the first artist-facing reason the chosen scope cannot run."""
    if scoped_meshes(context, scope):
        return ""
    if scope == "ACTIVE":
        return "Select an active mesh object"
    if scope == "SELECTED":
        return "Select one or more mesh objects"
    return "The active collection contains no mesh objects"


def _store_review(settings, obj, review):
    item = settings.results.add()
    item.object_ref = obj
    item.object_name = review.object_name
    item.base_vertices = review.base_vertices
    item.base_edges = review.base_edges
    item.base_faces = review.base_faces
    item.base_triangles = review.base_triangles
    item.evaluated_vertices = review.evaluated_vertices
    item.evaluated_faces = review.evaluated_faces
    item.evaluated_triangles = review.evaluated_triangles
    multiplier = review.modifier_multiplier
    item.modifier_multiplier = multiplier if math.isfinite(multiplier) else 0.0
    item.dimensions = review.dimensions
    item.error_count = review.error_count
    item.warning_count = review.warning_count
    for issue in review.issues:
        stored = item.issues.add()
        stored.code = issue.code
        stored.message = issue.message
        stored.severity = issue.severity.value
        stored.count = issue.count


def _stored_summary(settings):
    reviews = []
    for result in settings.results:
        issues = tuple(
            Issue(issue.code, issue.message, Severity(issue.severity), issue.count)
            for issue in result.issues
        )
        reviews.append(
            ObjectReview(
                object_name=result.object_name,
                base_vertices=result.base_vertices,
                base_edges=result.base_edges,
                base_faces=result.base_faces,
                base_triangles=result.base_triangles,
                evaluated_vertices=result.evaluated_vertices,
                evaluated_faces=result.evaluated_faces,
                evaluated_triangles=result.evaluated_triangles,
                dimensions=tuple(result.dimensions),
                issues=issues,
            )
        )
    return ReviewSummary(tuple(reviews))


class ONYX_OT_run_review(bpy.types.Operator):
    bl_idname = "onyx.run_review"
    bl_label = "Run Review"
    bl_description = "Inspect the chosen meshes without changing their data"

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_review", None)
        if settings is None:
            cls.poll_message_set("Onyx Review is not available in this scene")
            return False
        blocker = review_blocker(context, settings.scope)
        if blocker:
            cls.poll_message_set(blocker)
            return False
        return True

    def execute(self, context):
        settings = context.scene.onyx_review
        objects = scoped_meshes(context, settings.scope)
        if not objects:
            self.report({"WARNING"}, "No mesh objects are available in the chosen scope")
            return {"CANCELLED"}

        highlight_state.clear_highlight()
        settings.results.clear()
        depsgraph = context.evaluated_depsgraph_get()
        reviews = tuple(
            review_object(obj, depsgraph, triangle_budget=settings.triangle_budget)
            for obj in objects
        )
        summary = ReviewSummary(reviews)
        for obj, review in zip(objects, reviews):
            _store_review(settings, obj, review)
        settings.last_summary = summary.message
        settings.total_errors = summary.error_count
        settings.total_warnings = summary.warning_count
        settings.total_triangles = summary.evaluated_triangles
        self.report({"INFO"}, summary.message)
        return {"FINISHED"}


class ONYX_OT_clear_review(bpy.types.Operator):
    bl_idname = "onyx.clear_review"
    bl_label = "Clear Review"
    bl_description = "Remove the current review results without changing any objects"

    def execute(self, context):
        settings = context.scene.onyx_review
        highlight_state.clear_highlight()
        settings.results.clear()
        settings.last_summary = ""
        settings.total_errors = 0
        settings.total_warnings = 0
        settings.total_triangles = 0
        return {"FINISHED"}


class ONYX_OT_copy_review_report(bpy.types.Operator):
    bl_idname = "onyx.copy_review_report"
    bl_label = "Copy Report"
    bl_description = "Copy the complete review report to the clipboard"

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_review", None)
        return bool(settings and settings.results)

    def execute(self, context):
        summary = _stored_summary(context.scene.onyx_review)
        context.window_manager.clipboard = format_review_report(summary)
        self.report({"INFO"}, "Review report copied to the clipboard")
        return {"FINISHED"}


class ONYX_OT_select_review_object(bpy.types.Operator):
    bl_idname = "onyx.select_review_object"
    bl_label = "Select Reviewed Object"
    bl_description = "Select and activate the object represented by this review result"

    object_name: StringProperty(description="Name of the reviewed object to select")

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed object is no longer in the active view layer")
            return {"CANCELLED"}
        for selected in tuple(context.selected_objects):
            selected.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class ONYX_OT_inspect_review_issue(bpy.types.Operator):
    bl_idname = "onyx.inspect_review_issue"
    bl_label = "Inspect Finding"
    bl_description = "Enter Edit Mode and select the mesh elements behind this finding"

    object_name: StringProperty(description="Name of the reviewed mesh to inspect")
    issue_code: StringProperty(description="Stable identifier of the finding to inspect")

    def execute(self, context):
        domain = issue_selection_domain(self.issue_code)
        if not domain:
            self.report({"WARNING"}, "This finding has no mesh elements to select")
            return {"CANCELLED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before inspecting its elements")
            return {"CANCELLED"}

        active = context.view_layer.objects.active
        if active is not None and active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for selected in tuple(context.selected_objects):
            selected.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        context.tool_settings.mesh_select_mode = {
            "VERT": (True, False, False),
            "EDGE": (False, True, False),
            "FACE": (False, False, True),
        }[domain]
        _, count = select_issue_elements(obj.data, self.issue_code)
        if not count:
            self.report({"INFO"}, "No matching elements remain; run Review again")
            return {"FINISHED"}

        noun = {"VERT": "vertices", "EDGE": "edges", "FACE": "faces"}[domain]
        self.report({"INFO"}, f"Selected {count:,} matching {noun}")
        return {"FINISHED"}


class ONYX_OT_highlight_review_issue(bpy.types.Operator):
    bl_idname = "onyx.highlight_review_issue"
    bl_label = "Show Finding"
    bl_description = "Draw the affected mesh elements over the 3D Viewport"

    object_name: StringProperty(description="Name of the reviewed mesh to highlight")
    issue_code: StringProperty(description="Stable identifier of the finding to highlight")
    message: StringProperty(description="Artist-facing description of the finding")
    severity: StringProperty(description="Importance of the review finding")

    def execute(self, context):
        if highlight_state.is_active(self.object_name, self.issue_code):
            highlight_state.clear_highlight()
            self.report({"INFO"}, "Viewport highlight hidden")
            return {"FINISHED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before highlighting its elements")
            return {"CANCELLED"}

        try:
            domain, points, lines, count = issue_overlay_geometry(obj, self.issue_code)
        except ValueError:
            self.report({"WARNING"}, "This finding has no mesh elements to highlight")
            return {"CANCELLED"}
        if not count:
            self.report({"INFO"}, "No matching elements remain; run Review again")
            return {"FINISHED"}

        highlight_state.show_highlight(
            obj.name,
            self.issue_code,
            self.message,
            self.severity,
            domain,
            count,
            points,
            lines,
        )
        self.report({"INFO"}, f"Showing {count:,} matching mesh elements")
        return {"FINISHED"}


class ONYX_OT_highlight_review_object(bpy.types.Operator):
    bl_idname = "onyx.highlight_review_object"
    bl_label = "Show All Findings"
    bl_description = "Draw every actionable finding for this mesh in the 3D Viewport"

    object_name: StringProperty(description="Name of the reviewed mesh to highlight")

    def execute(self, context):
        if highlight_state.is_overview_active(self.object_name):
            highlight_state.clear_highlight()
            self.report({"INFO"}, "Viewport findings hidden")
            return {"FINISHED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before highlighting its elements")
            return {"CANCELLED"}

        settings = context.scene.onyx_review
        result = next(
            (
                item
                for item in settings.results
                if item.object_ref == obj or item.object_name == self.object_name
            ),
            None,
        )
        if result is None:
            self.report({"WARNING"}, "Run Review again before showing this mesh")
            return {"CANCELLED"}

        actionable = tuple(
            issue for issue in result.issues if issue_selection_domain(issue.code)
        )
        geometry = {
            issue_code: (domain, points, lines, count)
            for issue_code, domain, points, lines, count in issue_overlays_geometry(
                obj,
                (issue.code for issue in actionable),
            )
        }
        highlights = []
        for issue in actionable:
            domain, points, lines, count = geometry[issue.code]
            if count:
                highlights.append(
                    highlight_state.make_highlight(
                        obj.name,
                        issue.code,
                        issue.message,
                        issue.severity,
                        domain,
                        count,
                        points,
                        lines,
                    )
                )
        if not highlights:
            self.report({"INFO"}, "This mesh has no actionable findings to show")
            return {"FINISHED"}

        highlight_state.show_overview(obj.name, highlights)
        self.report({"INFO"}, f"Showing {len(highlights):,} findings")
        return {"FINISHED"}


class ONYX_OT_clear_review_highlight(bpy.types.Operator):
    bl_idname = "onyx.clear_review_highlight"
    bl_label = "Clear Highlight"
    bl_description = "Remove the current mesh-finding overlay from the 3D Viewport"

    @classmethod
    def poll(cls, _context):
        return highlight_state.active_highlight() is not None

    def execute(self, _context):
        highlight_state.clear_highlight()
        return {"FINISHED"}


class ONYX_OT_review_mode(bpy.types.Operator):
    bl_idname = "onyx.review_mode"
    bl_label = "Set Review Mode"
    bl_description = "Apply a temporary inspection preset to this 3D Viewport"

    mode: EnumProperty(
        items=(
            ("STUDIO", "Studio", "Use neutral material-colored studio shading"),
            ("SILHOUETTE", "Silhouette", "Use flat near-black silhouette shading"),
            ("TOPOLOGY", "Topology", "Show a high-contrast wire overlay"),
            ("FACE_ORIENTATION", "Orientation", "Show front and back face orientation"),
        ),
        description="Temporary viewport inspection preset",
    )

    @classmethod
    def poll(cls, context):
        return getattr(context.space_data, "type", "") == "VIEW_3D"

    def execute(self, context):
        viewport_state.apply_mode(context.space_data, self.mode)
        return {"FINISHED"}


class ONYX_OT_restore_review_view(bpy.types.Operator):
    bl_idname = "onyx.restore_review_view"
    bl_label = "Restore View"
    bl_description = "Restore this 3D Viewport to its settings from before review mode"

    @classmethod
    def poll(cls, context):
        return getattr(context.space_data, "type", "") == "VIEW_3D"

    def execute(self, context):
        if not viewport_state.restore_space(context.space_data):
            self.report({"INFO"}, "This viewport has no saved review state")
        return {"FINISHED"}


CLASSES = (
    ONYX_OT_run_review,
    ONYX_OT_clear_review,
    ONYX_OT_copy_review_report,
    ONYX_OT_select_review_object,
    ONYX_OT_inspect_review_issue,
    ONYX_OT_highlight_review_issue,
    ONYX_OT_highlight_review_object,
    ONYX_OT_clear_review_highlight,
    ONYX_OT_review_mode,
    ONYX_OT_restore_review_view,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
