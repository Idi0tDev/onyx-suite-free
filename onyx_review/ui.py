"""3D Viewport interface for Onyx Review."""

import bpy

from . import delta_state, highlight_state, operators
from .mesh_analysis import issue_selection_domain, simple_fix_info, topology_class_info


def _draw_topology_class(layout, object_name, topology_class, count):
    issue_code, label, _ = topology_class_info(topology_class)
    row = layout.row(align=True)
    row.label(text=f"{label} ({count:,})")
    actions = row.row(align=True)
    actions.enabled = count > 0
    visible = highlight_state.is_active(object_name, issue_code)
    highlight = actions.operator(
        "onyx.highlight_topology_class",
        text="Hide" if visible else "Show",
        icon="HIDE_ON" if visible else "HIDE_OFF",
    )
    highlight.object_name = object_name
    highlight.topology_class = topology_class
    inspect = actions.operator(
        "onyx.inspect_topology_class",
        text="Inspect",
        icon="VIEWZOOM",
    )
    inspect.object_name = object_name
    inspect.topology_class = topology_class


def _status_icon(settings):
    if settings.total_errors:
        return "ERROR"
    if settings.total_warnings:
        return "INFO"
    return "CHECKMARK"


def _live_status_icon(status):
    if status == "Up to date":
        return "CHECKMARK"
    if status.endswith("pending"):
        return "TIME"
    if status.startswith("Paused"):
        return "INFO"
    return "DOT"


class ONYX_PT_review(bpy.types.Panel):
    bl_label = "Review"
    bl_idname = "ONYX_PT_review"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Onyx"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.onyx_review
        targets = operators.scoped_meshes(context, settings.scope)

        target = layout.box()
        target.label(text="Review Target", icon="OBJECT_DATA")
        if targets:
            if len(targets) == 1:
                target.label(text=targets[0].name, icon="MESH_DATA")
            else:
                target.label(text=f"{len(targets)} mesh objects", icon="MESH_DATA")
        else:
            target.alert = True
            target.label(text=operators.review_blocker(context, settings.scope), icon="ERROR")

        options = layout.box()
        options.label(text="Review Options", icon="PREFERENCES")
        options.prop(settings, "scope", expand=True)
        options.prop(settings, "triangle_budget")
        options.prop(settings, "live_review", toggle=True)
        if settings.live_review:
            live_options = options.column(align=True)
            live_options.prop(settings, "live_delay")
            live_options.prop(settings, "live_max_vertices")
            live_options.label(
                text=settings.live_status,
                icon=_live_status_icon(settings.live_status),
            )

        row = layout.row(align=True)
        row.scale_y = 1.25
        row.enabled = bool(targets)
        row.operator(
            "onyx.run_review",
            text=(
                "Run Now"
                if settings.live_review
                else "Run Again" if settings.results else "Run Review"
            ),
            icon="VIEWZOOM",
        )

        if not settings.last_summary:
            layout.label(text="Results will appear here", icon="INFO")
            return

        summary = layout.box()
        summary.label(text=settings.last_summary, icon=_status_icon(settings))
        summary.label(text=f"{settings.total_triangles:,} evaluated triangles")
        row = summary.row(align=True)
        row.operator("onyx.copy_review_report", icon="COPYDOWN")
        row.operator("onyx.clear_review", icon="X")

        saved_baseline = delta_state.baseline(context.scene)
        delta = delta_state.current_delta(context.scene)
        comparison = layout.box()
        comparison.label(text="Review Delta", icon="TIME")
        if saved_baseline is None:
            comparison.label(text="Save this review as your before snapshot.", icon="INFO")
            comparison.operator(
                "onyx.set_review_baseline",
                text="Save Baseline",
                icon="ADD",
            )
        else:
            comparison.label(text=f"Before: {saved_baseline.message}")
            if delta is None:
                comparison.label(text="Make changes, then run Review again.", icon="INFO")
                row = comparison.row(align=True)
                row.operator(
                    "onyx.set_review_baseline",
                    text="Replace Baseline",
                )
                row.operator(
                    "onyx.clear_review_baseline",
                    text="Clear Baseline",
                    icon="X",
                )
            else:
                row = comparison.row(align=True)
                row.label(text=f"New {len(delta.introduced)}", icon="INFO")
                row.label(text=f"Fixed {len(delta.resolved)}", icon="CHECKMARK")
                row = comparison.row(align=True)
                row.label(text=f"Changed {len(delta.changed)}", icon="INFO")
                row.label(text=f"Same {len(delta.unchanged)}")
                triangle_change = delta.triangle_change
                comparison.label(
                    text=(
                        f"Triangles {delta.baseline.evaluated_triangles:,} → "
                        f"{delta.current.evaluated_triangles:,} ({triangle_change:+,})"
                    )
                )
                if delta.resolved:
                    comparison.label(text="Fixed or gone since baseline", icon="CHECKMARK")
                    for item in delta.resolved:
                        count = f" ({item.baseline_count:,})" if item.baseline_count > 1 else ""
                        comparison.label(text=item.object_name, icon="MESH_DATA")
                        comparison.label(text=f"  {item.message}{count}")
                row = comparison.row(align=True)
                row.operator("onyx.copy_review_delta", icon="COPYDOWN")
                row.operator(
                    "onyx.set_review_baseline",
                    text="Use Current as Baseline",
                )
                comparison.operator(
                    "onyx.clear_review_baseline",
                    text="Clear Baseline",
                    icon="X",
                )

        if settings.total_errors or settings.total_warnings:
            finding_view = layout.box()
            finding_view.label(text="Finding View", icon="FILTER")
            finding_view.prop(settings, "finding_filter", expand=True)
            finding_view.label(text="Copy Report always includes every finding", icon="INFO")

        active_highlights = highlight_state.active_highlights()
        if active_highlights:
            active_highlight = active_highlights[0]
            overview_key = highlight_state.active_overview_key()
            visual = layout.box()
            visual.label(text="Viewport Highlight", icon="HIDE_OFF")
            visual.label(text=active_highlight.object_name, icon="MESH_DATA")
            if len(active_highlights) == 1 and not overview_key:
                style = highlight_state.finding_style(
                    active_highlight.issue_code,
                    active_highlight.severity,
                )
                visual.label(text=f"{style.name} · {active_highlight.message}")
            elif overview_key == "FINDINGS":
                visual.label(text=f"{len(active_highlights):,} actionable findings")
                visual.label(text="Errors use thicker marks", icon="INFO")
                for highlight in active_highlights:
                    style = highlight_state.finding_style(
                        highlight.issue_code,
                        highlight.severity,
                    )
                    icon = "ERROR" if highlight.severity == "ERROR" else "INFO"
                    visual.label(text=f"{style.name} · {highlight.message}", icon=icon)
            else:
                map_name = "Face Topology Map" if overview_key == "FACE_MAP" else "Pole Topology Map"
                visual.label(text=map_name, icon="OVERLAY")
                for highlight in active_highlights:
                    style = highlight_state.finding_style(
                        highlight.issue_code,
                        highlight.severity,
                    )
                    visual.label(text=f"{style.name} · {highlight.message}", icon="INFO")
            visual.operator("onyx.clear_review_highlight", icon="X")

        modes = layout.box()
        modes.label(text="Viewport Review", icon="SHADING_SOLID")
        row = modes.row(align=True)
        row.operator("onyx.review_mode", text="Studio").mode = "STUDIO"
        row.operator("onyx.review_mode", text="Silhouette").mode = "SILHOUETTE"
        row = modes.row(align=True)
        row.operator("onyx.review_mode", text="Topology").mode = "TOPOLOGY"
        row.operator("onyx.review_mode", text="Orientation").mode = "FACE_ORIENTATION"
        modes.operator("onyx.restore_review_view", icon="LOOP_BACK")

        for result in settings.results:
            box = layout.box()
            header = box.row(align=True)
            header.prop(
                result,
                "expanded",
                text="",
                emboss=False,
                icon="TRIA_DOWN" if result.expanded else "TRIA_RIGHT",
            )
            header.label(text=result.object_name, icon="MESH_DATA")
            select = header.operator("onyx.select_review_object", text="", icon="RESTRICT_SELECT_OFF")
            object_name = result.object_ref.name if result.object_ref else result.object_name
            select.object_name = object_name
            if not result.expanded:
                continue

            box.label(
                text=(
                    f"Base {result.base_triangles:,} tris  →  "
                    f"Evaluated {result.evaluated_triangles:,}"
                )
            )
            box.label(
                text=(
                    f"{result.base_vertices:,} verts · {result.base_edges:,} edges · "
                    f"{result.base_faces:,} faces"
                )
            )
            box.label(
                text=(
                    f"Face mix {result.triangle_faces:,} tris · "
                    f"{result.quad_faces:,} quads · {result.ngon_faces:,} ngons"
                )
            )
            box.label(
                text=(
                    f"Poles {result.three_poles:,} × 3 · {result.five_poles:,} × 5 · "
                    f"{result.six_plus_poles:,} × 6+"
                )
            )
            topology = box.box()
            topology_header = topology.row(align=True)
            topology_header.prop(
                result,
                "topology_expanded",
                text="",
                emboss=False,
                icon="TRIA_DOWN" if result.topology_expanded else "TRIA_RIGHT",
            )
            topology_header.label(text="Topology Detail", icon="OVERLAY")
            if result.topology_expanded:
                row = topology.row(align=True)
                face_map_visible = highlight_state.is_overview_active(
                    object_name,
                    "FACE_MAP",
                )
                face_map = row.operator(
                    "onyx.highlight_topology_map",
                    text="Hide Face Map" if face_map_visible else "Show Face Map",
                    icon="HIDE_ON" if face_map_visible else "HIDE_OFF",
                )
                face_map.object_name = object_name
                face_map.map_kind = "FACES"
                pole_map_visible = highlight_state.is_overview_active(
                    object_name,
                    "POLE_MAP",
                )
                pole_map = row.operator(
                    "onyx.highlight_topology_map",
                    text="Hide Pole Map" if pole_map_visible else "Show Pole Map",
                    icon="HIDE_ON" if pole_map_visible else "HIDE_OFF",
                )
                pole_map.object_name = object_name
                pole_map.map_kind = "POLES"
                topology.label(text="Face classes", icon="FACESEL")
                _draw_topology_class(
                    topology,
                    object_name,
                    "FACE_TRIANGLES",
                    result.triangle_faces,
                )
                _draw_topology_class(
                    topology,
                    object_name,
                    "FACE_QUADS",
                    result.quad_faces,
                )
                _draw_topology_class(
                    topology,
                    object_name,
                    "FACE_NGONS",
                    result.ngon_faces,
                )
                topology.label(text="Pole classes", icon="VERTEXSEL")
                _draw_topology_class(
                    topology,
                    object_name,
                    "POLES_3",
                    result.three_poles,
                )
                _draw_topology_class(
                    topology,
                    object_name,
                    "POLES_5",
                    result.five_poles,
                )
                _draw_topology_class(
                    topology,
                    object_name,
                    "POLES_6_PLUS",
                    result.six_plus_poles,
                )
            box.label(
                text=(
                    f"Size {result.dimensions[0]:.3g} × {result.dimensions[1]:.3g} × "
                    f"{result.dimensions[2]:.3g} scene units"
                )
            )
            visible_issues = tuple(
                issue
                for issue in result.issues
                if operators.finding_matches_filter(issue, settings.finding_filter)
            )
            if any(issue_selection_domain(issue.code) for issue in visible_issues):
                overview_visible = highlight_state.is_overview_active(object_name)
                overview = box.operator(
                    "onyx.highlight_review_object",
                    text=(
                        "Hide Visible Findings"
                        if overview_visible
                        else "Show Visible Findings"
                    ),
                    icon="HIDE_ON" if overview_visible else "HIDE_OFF",
                )
                overview.object_name = object_name
            if not result.issues:
                box.label(text="No findings", icon="CHECKMARK")
            elif not visible_issues:
                if settings.finding_filter == "CHANGES" and saved_baseline is None:
                    box.label(text="Save a baseline first", icon="INFO")
                elif settings.finding_filter == "CHANGES" and delta is None:
                    box.label(text="Run Review again to compare", icon="INFO")
                elif settings.finding_filter == "CHANGES":
                    box.label(text="No new or changed findings", icon="CHECKMARK")
                else:
                    box.label(text="No findings match this view", icon="CHECKMARK")
            for issue in visible_issues:
                icon = "ERROR" if issue.severity == "ERROR" else "INFO"
                prefix = {
                    "INTRODUCED": "New · ",
                    "CHANGED": "Changed · ",
                }.get(issue.delta_status, "")
                delta_item = next(
                    (
                        item
                        for item in delta.findings
                        if item.object_name == result.object_name and item.code == issue.code
                    ),
                    None,
                ) if delta else None
                if delta_item and issue.delta_status == "CHANGED":
                    suffix = f" ({delta_item.baseline_count:,} → {delta_item.current_count:,})"
                else:
                    suffix = f" ({issue.count:,})" if issue.count > 1 else ""
                fix_info = simple_fix_info(issue.code)
                if fix_info:
                    finding = box.column(align=True)
                    finding.label(text=f"{prefix}{issue.message}{suffix}", icon=icon)
                    row = finding.row(align=True)
                else:
                    row = box.row(align=True)
                    row.label(text=f"{prefix}{issue.message}{suffix}", icon=icon)
                if issue_selection_domain(issue.code):
                    is_visible = highlight_state.is_active(object_name, issue.code)
                    highlight = row.operator(
                        "onyx.highlight_review_issue",
                        text="Hide" if is_visible else "Show",
                        icon="HIDE_ON" if is_visible else "HIDE_OFF",
                    )
                    highlight.object_name = object_name
                    highlight.issue_code = issue.code
                    highlight.message = issue.message
                    highlight.severity = issue.severity
                    inspect = row.operator(
                        "onyx.inspect_review_issue",
                        text="Inspect",
                        icon="VIEWZOOM",
                    )
                    inspect.object_name = object_name
                    inspect.issue_code = issue.code
                    if fix_info:
                        fix = row.operator(
                            "onyx.fix_review_issue",
                            text="Fix",
                            icon="CHECKMARK",
                        )
                        fix.object_name = object_name
                        fix.issue_code = issue.code


CLASSES = (ONYX_PT_review,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
