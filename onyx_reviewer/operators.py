"""Operators for mesh review, navigation, and viewport modes."""

from __future__ import annotations

import math

import bpy
from bpy.props import EnumProperty, StringProperty

from .analysis import (
    FindingDeltaStatus,
    Issue,
    ObjectReview,
    ReviewSummary,
    Severity,
    format_review_delta,
    format_review_report,
)
from .mesh_analysis import (
    TOPOLOGY_CLASS_ENUM_ITEMS,
    apply_simple_fix,
    issue_overlay_geometry,
    issue_overlays_geometry,
    issue_selection_domain,
    review_object,
    select_issue_elements,
    simple_fix_info,
    topology_class_info,
    topology_map_classes,
)
from .review_profiles import resolve_review_profile
from . import delta_state, highlight_state, viewport_state


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


def active_review_profile(settings):
    """Resolve the scene's artist-facing profile into finding-group switches."""
    return resolve_review_profile(
        settings.review_profile,
        topology=settings.check_topology,
        transforms=settings.check_transforms,
        asset_setup=settings.check_asset_setup,
        triangle_budget=settings.check_triangle_budget,
    )


def finding_matches_filter(issue, filter_mode):
    """Return whether a stored finding belongs in the current artist-facing view."""
    if filter_mode == "ALL":
        return True
    if filter_mode == "ERRORS":
        return issue.severity == "ERROR"
    if filter_mode == "WARNINGS":
        return issue.severity == "WARNING"
    if filter_mode == "FIXABLE":
        return simple_fix_info(issue.code) is not None
    if filter_mode == "CHANGES":
        return getattr(issue, "delta_status", "NONE") in {"INTRODUCED", "CHANGED"}
    raise ValueError(f"Unknown finding filter: {filter_mode}")


def visible_actionable_findings(settings):
    """Return filtered findings that can be pointed out on the mesh."""
    findings = []
    for result in settings.results:
        object_name = result.object_ref.name if result.object_ref else result.object_name
        for issue in result.issues:
            if (
                finding_matches_filter(issue, settings.finding_filter)
                and issue_selection_domain(issue.code)
            ):
                findings.append((result, issue, object_name))
    return tuple(findings)


def active_visual_finding_index(settings, findings=None):
    """Return the active single-finding overlay's position, or -1."""
    findings = visible_actionable_findings(settings) if findings is None else findings
    active = highlight_state.active_highlight()
    if active is None or highlight_state.active_overview_key():
        return -1
    return next(
        (
            index
            for index, (_, issue, object_name) in enumerate(findings)
            if active.object_name == object_name and active.issue_code == issue.code
        ),
        -1,
    )


def _store_review(settings, obj, review, delta_statuses):
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
    item.triangle_faces = review.triangle_faces
    item.quad_faces = review.quad_faces
    item.ngon_faces = review.ngon_faces
    item.three_poles = review.three_poles
    item.five_poles = review.five_poles
    item.six_plus_poles = review.six_plus_poles
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
        stored.delta_status = delta_statuses.get(
            (review.object_name, issue.code),
            "NONE",
        )


def _clear_delta_markers(settings):
    for result in settings.results:
        for issue in result.issues:
            issue.delta_status = "NONE"


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
                triangle_faces=result.triangle_faces,
                quad_faces=result.quad_faces,
                ngon_faces=result.ngon_faces,
                three_poles=result.three_poles,
                five_poles=result.five_poles,
                six_plus_poles=result.six_plus_poles,
                issues=issues,
            )
        )
    return ReviewSummary(tuple(reviews))


def perform_review(context):
    """Run the current scene review and return its reusable summary."""
    settings = context.scene.onyx_reviewer
    objects = scoped_meshes(context, settings.scope)
    if not objects:
        raise ValueError(review_blocker(context, settings.scope))

    # Any existing overlay represents the previous mesh state. Never leave
    # stale evidence visible after either a manual or live refresh.
    highlight_state.clear_highlight()
    settings.results.clear()
    depsgraph = context.evaluated_depsgraph_get()
    profile = active_review_profile(settings)
    reviews = tuple(
        review_object(
            obj,
            depsgraph,
            triangle_budget=settings.triangle_budget,
            profile=profile,
        )
        for obj in objects
    )
    summary = ReviewSummary(reviews)
    delta = delta_state.compare(context.scene, summary)
    delta_statuses = {
        (item.object_name, item.code): item.status.value
        for item in delta.findings
        if item.status is not FindingDeltaStatus.RESOLVED
    } if delta else {}
    for obj, review in zip(objects, reviews):
        _store_review(settings, obj, review, delta_statuses)
    settings.last_summary = summary.message
    settings.total_errors = summary.error_count
    settings.total_warnings = summary.warning_count
    settings.total_triangles = summary.evaluated_triangles
    settings.last_profile = profile.label
    settings.review_options_dirty = False
    if settings.live_review:
        settings.live_status = "Up to date"
    return summary


class ONYX_OT_run_review(bpy.types.Operator):
    bl_idname = "onyx.run_review"
    bl_label = "Run Review"
    bl_description = "Inspect the chosen meshes without changing their data"

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_reviewer", None)
        if settings is None:
            cls.poll_message_set("Onyx Reviewer is not available in this scene")
            return False
        blocker = review_blocker(context, settings.scope)
        if blocker:
            cls.poll_message_set(blocker)
            return False
        return True

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        blocker = review_blocker(context, settings.scope)
        if blocker:
            self.report({"WARNING"}, blocker)
            return {"CANCELLED"}
        summary = perform_review(context)
        self.report({"INFO"}, summary.message)
        return {"FINISHED"}


class ONYX_OT_clear_review(bpy.types.Operator):
    bl_idname = "onyx.clear_review"
    bl_label = "Clear Review"
    bl_description = "Clear the current results and temporary baseline without changing any objects"

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        highlight_state.clear_highlight()
        settings.results.clear()
        settings.last_summary = ""
        settings.total_errors = 0
        settings.total_warnings = 0
        settings.total_triangles = 0
        settings.last_profile = ""
        settings.review_options_dirty = False
        delta_state.clear_baseline(context.scene)
        if settings.live_review:
            settings.live_status = "Waiting for mesh changes"
        return {"FINISHED"}


class ONYX_OT_copy_review_report(bpy.types.Operator):
    bl_idname = "onyx.copy_review_report"
    bl_label = "Copy Report"
    bl_description = "Copy the complete review report to the clipboard"

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_reviewer", None)
        return bool(settings and settings.results)

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        summary = _stored_summary(settings)
        context.window_manager.clipboard = format_review_report(
            summary,
            profile_name=settings.last_profile or "General",
        )
        self.report({"INFO"}, "Review report copied to the clipboard")
        return {"FINISHED"}


class ONYX_OT_set_review_baseline(bpy.types.Operator):
    bl_idname = "onyx.set_review_baseline"
    bl_label = "Save Review Baseline"
    bl_description = "Save the current review as a session-only before snapshot"

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_reviewer", None)
        if not settings or not settings.results:
            return False
        if settings.review_options_dirty:
            cls.poll_message_set("Run Review again after changing its options")
            return False
        return True

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        delta_state.set_baseline(context.scene, _stored_summary(settings))
        _clear_delta_markers(settings)
        highlight_state.clear_highlight()
        self.report({"INFO"}, "Review baseline saved for this Blender session")
        return {"FINISHED"}


class ONYX_OT_clear_review_baseline(bpy.types.Operator):
    bl_idname = "onyx.clear_review_baseline"
    bl_label = "Clear Review Baseline"
    bl_description = "Forget the saved before snapshot without changing the review or mesh"

    @classmethod
    def poll(cls, context):
        scene = getattr(context, "scene", None)
        return bool(scene and delta_state.baseline(scene) is not None)

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        delta_state.clear_baseline(context.scene)
        _clear_delta_markers(settings)
        highlight_state.clear_highlight()
        self.report({"INFO"}, "Review baseline cleared")
        return {"FINISHED"}


class ONYX_OT_copy_review_delta(bpy.types.Operator):
    bl_idname = "onyx.copy_review_delta"
    bl_label = "Copy Delta"
    bl_description = "Copy the complete before-and-after comparison to the clipboard"

    @classmethod
    def poll(cls, context):
        scene = getattr(context, "scene", None)
        return bool(scene and delta_state.current_delta(scene) is not None)

    def execute(self, context):
        delta = delta_state.current_delta(context.scene)
        context.window_manager.clipboard = format_review_delta(delta)
        self.report({"INFO"}, "Review Delta copied to the clipboard")
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


class ONYX_OT_step_review_finding(bpy.types.Operator):
    bl_idname = "onyx.step_review_finding"
    bl_label = "Step Through Mesh Problems"
    bl_description = "Select the reviewed object and show the previous or next visible mesh problem"

    direction: EnumProperty(
        items=(
            ("PREVIOUS", "Previous", "Show the previous visible mesh problem"),
            ("NEXT", "Next", "Show the next visible mesh problem"),
        ),
        default="NEXT",
        description="Direction to move through visible mesh problems",
    )

    @classmethod
    def poll(cls, context):
        settings = getattr(getattr(context, "scene", None), "onyx_reviewer", None)
        if settings is None:
            return False
        return bool(visible_actionable_findings(settings))

    def execute(self, context):
        settings = context.scene.onyx_reviewer
        findings = visible_actionable_findings(settings)
        if not findings:
            self.report({"INFO"}, "This view has no mesh problems to show")
            return {"CANCELLED"}

        active_index = active_visual_finding_index(settings, findings)
        if active_index < 0:
            index = 0 if self.direction == "NEXT" else len(findings) - 1
        else:
            step = 1 if self.direction == "NEXT" else -1
            index = (active_index + step) % len(findings)
        result, issue, object_name = findings[index]

        obj = bpy.data.objects.get(object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before highlighting its problems")
            return {"CANCELLED"}

        active_object = context.view_layer.objects.active
        if active_object is not None and active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        for selected in tuple(context.selected_objects):
            selected.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        for stored_result in settings.results:
            stored_result.expanded = stored_result.object_name == result.object_name

        domain, points, lines, count = issue_overlay_geometry(obj, issue.code)
        if not count:
            highlight_state.clear_highlight()
            self.report({"INFO"}, "This problem changed; run Review again")
            return {"FINISHED"}

        highlight_state.show_highlight(
            obj.name,
            issue.code,
            issue.message,
            issue.severity,
            domain,
            count,
            points,
            lines,
        )

        area = getattr(context, "area", None)
        if area is not None and area.type == "VIEW_3D":
            window_region = next(
                (region for region in area.regions if region.type == "WINDOW"),
                None,
            )
            if window_region is not None:
                with context.temp_override(area=area, region=window_region):
                    bpy.ops.view3d.view_selected(use_all_regions=False)

        self.report(
            {"INFO"},
            f"Mesh problem {index + 1} of {len(findings)}: {issue.message}",
        )
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


class ONYX_OT_fix_review_issue(bpy.types.Operator):
    bl_idname = "onyx.fix_review_issue"
    bl_label = "Fix Finding"
    bl_description = "Apply one explicit, undoable fix for a supported mesh finding"
    bl_options = {"REGISTER", "UNDO"}

    object_name: StringProperty(description="Name of the reviewed mesh to fix")
    issue_code: StringProperty(description="Stable identifier of the finding to fix")

    @classmethod
    def description(cls, _context, properties):
        info = simple_fix_info(properties.issue_code)
        return info[1] if info else cls.bl_description

    def execute(self, context):
        info = simple_fix_info(self.issue_code)
        if info is None:
            self.report({"WARNING"}, "This finding has no simple fix")
            return {"CANCELLED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.mode != "OBJECT":
            self.report({"WARNING"}, "Leave Edit Mode before applying a fix")
            return {"CANCELLED"}

        mesh = obj.data
        if mesh.library is not None or not mesh.is_editable:
            self.report({"WARNING"}, "Linked mesh data cannot be fixed")
            return {"CANCELLED"}
        if mesh.users > 1:
            self.report({"WARNING"}, "Make the mesh data single-user before applying a fix")
            return {"CANCELLED"}
        if mesh.shape_keys is not None:
            self.report({"WARNING"}, "Simple fixes are disabled for meshes with shape keys")
            return {"CANCELLED"}

        changed = apply_simple_fix(mesh, self.issue_code)
        if not changed:
            self.report({"INFO"}, "No exact matching elements remain; run Review again")
            return {"CANCELLED"}

        if not review_blocker(context, context.scene.onyx_reviewer.scope):
            perform_review(context)
        label, _ = info
        self.report({"INFO"}, f"{label}: changed {changed:,} mesh elements")
        return {"FINISHED"}


class ONYX_OT_inspect_topology_class(bpy.types.Operator):
    bl_idname = "onyx.inspect_topology_class"
    bl_label = "Inspect Topology Class"
    bl_description = "Enter Edit Mode and select this face or pole class"

    object_name: StringProperty(description="Name of the reviewed mesh to inspect")
    topology_class: EnumProperty(
        items=TOPOLOGY_CLASS_ENUM_ITEMS,
        description="Face or topology-pole class to inspect",
    )

    def execute(self, context):
        issue_code, label, _ = topology_class_info(self.topology_class)
        domain = issue_selection_domain(issue_code)
        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before inspecting its topology")
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
            "FACE": (False, False, True),
        }[domain]
        _, count = select_issue_elements(obj.data, issue_code)
        if not count:
            self.report({"INFO"}, f"No {label.lower()} remain; run Review again")
            return {"FINISHED"}

        noun = "vertices" if domain == "VERT" else "faces"
        self.report(
            {"INFO"},
            f"Selected {count:,} matching {noun} for {label.lower()}",
        )
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
    bl_label = "Show Visible Findings"
    bl_description = "Draw the currently visible actionable findings for this mesh in the 3D Viewport"

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

        settings = context.scene.onyx_reviewer
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
            issue
            for issue in result.issues
            if finding_matches_filter(issue, settings.finding_filter)
            and issue_selection_domain(issue.code)
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
            self.report({"INFO"}, "This view has no actionable findings to show")
            return {"FINISHED"}

        highlight_state.show_overview(obj.name, highlights)
        self.report({"INFO"}, f"Showing {len(highlights):,} findings")
        return {"FINISHED"}


class ONYX_OT_highlight_topology_class(bpy.types.Operator):
    bl_idname = "onyx.highlight_topology_class"
    bl_label = "Show Topology Class"
    bl_description = "Draw this face or pole class over the 3D Viewport"

    object_name: StringProperty(description="Name of the reviewed mesh to highlight")
    topology_class: EnumProperty(
        items=TOPOLOGY_CLASS_ENUM_ITEMS,
        description="Face or topology-pole class to highlight",
    )

    def execute(self, context):
        issue_code, label, _ = topology_class_info(self.topology_class)
        if highlight_state.is_active(self.object_name, issue_code):
            highlight_state.clear_highlight()
            self.report({"INFO"}, "Topology highlight hidden")
            return {"FINISHED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before highlighting its topology")
            return {"CANCELLED"}

        domain, points, lines, count = issue_overlay_geometry(obj, issue_code)
        if not count:
            self.report({"INFO"}, f"No {label.lower()} remain; run Review again")
            return {"FINISHED"}
        highlight_state.show_highlight(
            obj.name,
            issue_code,
            f"{label} ({count:,})",
            "INFO",
            domain,
            count,
            points,
            lines,
        )
        self.report(
            {"INFO"},
            f"Showing {count:,} matching mesh elements for {label.lower()}",
        )
        return {"FINISHED"}


class ONYX_OT_highlight_topology_map(bpy.types.Operator):
    bl_idname = "onyx.highlight_topology_map"
    bl_label = "Show Topology Map"
    bl_description = "Draw a color-coded face or pole map over the 3D Viewport"

    object_name: StringProperty(description="Name of the reviewed mesh to highlight")
    map_kind: EnumProperty(
        items=(
            ("FACES", "Faces", "Map triangles, quads, and ngons"),
            ("POLES", "Poles", "Map 3-edge, 5-edge, and 6+-edge poles"),
        ),
        description="Topology classes to show together",
    )

    def execute(self, context):
        overview_key = "FACE_MAP" if self.map_kind == "FACES" else "POLE_MAP"
        if highlight_state.is_overview_active(self.object_name, overview_key):
            highlight_state.clear_highlight()
            self.report({"INFO"}, "Topology map hidden")
            return {"FINISHED"}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None or obj.type != "MESH" or obj.name not in context.view_layer.objects:
            self.report({"WARNING"}, "The reviewed mesh is no longer in the active view layer")
            return {"CANCELLED"}
        if obj.hide_get() or obj.hide_viewport:
            self.report({"WARNING"}, "Show the reviewed mesh before highlighting its topology")
            return {"CANCELLED"}

        classes = topology_map_classes(self.map_kind)
        descriptions = {
            issue_code: (label, description)
            for class_id in classes
            for issue_code, label, description in (topology_class_info(class_id),)
        }
        geometry = issue_overlays_geometry(obj, descriptions)
        highlights = []
        for issue_code, domain, points, lines, count in geometry:
            if not count:
                continue
            label, _ = descriptions[issue_code]
            highlights.append(
                highlight_state.make_highlight(
                    obj.name,
                    issue_code,
                    f"{label} ({count:,})",
                    "INFO",
                    domain,
                    count,
                    points,
                    lines,
                )
            )
        if not highlights:
            self.report({"INFO"}, "This mesh has no matching topology classes")
            return {"FINISHED"}

        highlight_state.show_overview(
            obj.name,
            highlights,
            overview_key=overview_key,
        )
        map_name = "face" if self.map_kind == "FACES" else "pole"
        self.report({"INFO"}, f"Showing {map_name} topology map")
        return {"FINISHED"}


class ONYX_OT_clear_review_highlight(bpy.types.Operator):
    bl_idname = "onyx.clear_review_highlight"
    bl_label = "Clear Highlight"
    bl_description = "Remove the current review overlay from the 3D Viewport"

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
    ONYX_OT_set_review_baseline,
    ONYX_OT_clear_review_baseline,
    ONYX_OT_copy_review_delta,
    ONYX_OT_select_review_object,
    ONYX_OT_step_review_finding,
    ONYX_OT_inspect_review_issue,
    ONYX_OT_fix_review_issue,
    ONYX_OT_inspect_topology_class,
    ONYX_OT_highlight_review_issue,
    ONYX_OT_highlight_review_object,
    ONYX_OT_highlight_topology_class,
    ONYX_OT_highlight_topology_map,
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
