"""3D Viewport interface for Onyx Reviewer."""

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


def _draw_disclosure(layout, owner, property_name, label, icon):
    expanded = getattr(owner, property_name)
    row = layout.row(align=True)
    row.prop(
        owner,
        property_name,
        text="",
        emboss=False,
        icon="TRIA_DOWN" if expanded else "TRIA_RIGHT",
    )
    row.label(text=label, icon=icon)
    return expanded


class ONYX_PT_review(bpy.types.Panel):
    bl_label = "Review"
    bl_idname = "ONYX_PT_review"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Onyx"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.onyx_reviewer
        targets = operators.scoped_meshes(context, settings.scope)

        target = layout.box()
        if targets:
            if len(targets) == 1:
                target.label(text=targets[0].name, icon="MESH_DATA")
            else:
                target.label(text=f"{len(targets)} meshes ready", icon="MESH_DATA")
        else:
            target.alert = True
            target.label(text=operators.review_blocker(context, settings.scope), icon="ERROR")

        choices = target.row(align=True)
        choices.prop(settings, "scope", text="")
        choices.prop(settings, "review_profile", text="")

        profile = operators.active_review_profile(settings)

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
        live = row.row(align=True)
        live.enabled = bool(targets)
        live.prop(settings, "live_review", text="Live", toggle=True, icon="FILE_REFRESH")

        optional = layout.box()
        if _draw_disclosure(
            optional,
            settings,
            "more_settings_expanded",
            "More Settings",
            "PREFERENCES",
        ):
            optional.label(text=profile.short_summary, icon="INFO")
            if settings.review_profile == "CUSTOM":
                checks = optional.column(align=True)
                checks.label(text="Checks")
                checks.prop(settings, "check_topology")
                checks.prop(settings, "check_transforms")
                checks.prop(settings, "check_asset_setup")
                checks.prop(settings, "check_triangle_budget")
            budget = optional.row()
            budget.enabled = profile.triangle_budget
            budget.prop(settings, "triangle_budget")
            if settings.live_review:
                optional.separator()
                optional.label(text="Live Review")
                optional.prop(settings, "live_delay")
                optional.prop(settings, "live_max_vertices")
                optional.label(
                    text=settings.live_status,
                    icon=_live_status_icon(settings.live_status),
                )
        if settings.review_options_dirty:
            optional.label(text="Settings changed · run Review again", icon="INFO")

        if not settings.last_summary:
            layout.label(text="Run Review to check the mesh", icon="INFO")
            return

        summary = layout.box()
        summary.label(text=settings.last_summary, icon=_status_icon(settings))
        summary.label(
            text=(
                f"{settings.last_profile or 'General'} · "
                f"{settings.total_triangles:,} evaluated triangles"
            )
        )
        row = summary.row(align=True)
        row.operator("onyx.copy_review_report", text="Copy Report", icon="COPYDOWN")
        row.operator("onyx.clear_review", text="Clear", icon="X")

        saved_baseline = delta_state.baseline(context.scene)
        delta = delta_state.current_delta(context.scene)
        comparison = layout.box()
        delta_label = "Compare Changes"
        if delta is not None:
            delta_label += f" · {len(delta.introduced)} new, {len(delta.resolved)} fixed"
        if _draw_disclosure(
            comparison,
            settings,
            "delta_expanded",
            delta_label,
            "TIME",
        ):
            if settings.review_options_dirty:
                comparison.label(text="Run Review again before saving a baseline.", icon="INFO")
            elif saved_baseline is None:
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
                    row.operator("onyx.copy_review_delta", text="Copy Delta", icon="COPYDOWN")
                    row.operator(
                        "onyx.set_review_baseline",
                        text="Use Current",
                    )
                    comparison.operator(
                        "onyx.clear_review_baseline",
                        text="Clear Baseline",
                        icon="X",
                    )

        if settings.total_errors or settings.total_warnings:
            finding_view = layout.row(align=True)
            finding_view.label(text="Show", icon="FILTER")
            finding_view.prop(settings, "finding_filter", text="")

        visual_findings = operators.visible_actionable_findings(settings)
        if visual_findings:
            active_index = operators.active_visual_finding_index(
                settings,
                visual_findings,
            )
            navigator = layout.row(align=True)
            navigator.label(
                text=(
                    f"Mesh problem {active_index + 1} of {len(visual_findings)}"
                    if active_index >= 0
                    else f"{len(visual_findings)} mesh problems"
                ),
                icon="HIDE_OFF",
            )
            previous = navigator.operator(
                "onyx.step_review_finding",
                text="",
                icon="TRIA_LEFT",
            )
            previous.direction = "PREVIOUS"
            next_finding = navigator.operator(
                "onyx.step_review_finding",
                text="Next",
                icon="TRIA_RIGHT",
            )
            next_finding.direction = "NEXT"

        active_highlights = highlight_state.active_highlights()
        if active_highlights:
            active_highlight = active_highlights[0]
            overview_key = highlight_state.active_overview_key()
            visual = layout.box()
            row = visual.row(align=True)
            row.label(text=active_highlight.object_name, icon="HIDE_OFF")
            row.operator("onyx.clear_review_highlight", text="Hide", icon="X")
            if len(active_highlights) == 1 and not overview_key:
                style = highlight_state.finding_style(
                    active_highlight.issue_code,
                    active_highlight.severity,
                )
                visual.label(text=f"{style.name} · {active_highlight.message}")
            elif overview_key == "FINDINGS":
                visual.label(text=f"{len(active_highlights):,} problems highlighted")
                if _draw_disclosure(
                    visual,
                    settings,
                    "highlight_legend_expanded",
                    "Color Key",
                    "INFO",
                ):
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
                if _draw_disclosure(
                    visual,
                    settings,
                    "highlight_legend_expanded",
                    "Color Key",
                    "INFO",
                ):
                    for highlight in active_highlights:
                        style = highlight_state.finding_style(
                            highlight.issue_code,
                            highlight.severity,
                        )
                        visual.label(text=f"{style.name} · {highlight.message}", icon="INFO")

        modes = layout.box()
        if _draw_disclosure(
            modes,
            settings,
            "viewport_tools_expanded",
            "Viewport Modes",
            "SHADING_SOLID",
        ):
            row = modes.row(align=True)
            row.operator("onyx.review_mode", text="Studio").mode = "STUDIO"
            row.operator("onyx.review_mode", text="Silhouette").mode = "SILHOUETTE"
            row = modes.row(align=True)
            row.operator("onyx.review_mode", text="Topology").mode = "TOPOLOGY"
            row.operator("onyx.review_mode", text="Orientation").mode = "FACE_ORIENTATION"
            modes.operator("onyx.restore_review_view", text="Restore View", icon="LOOP_BACK")

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
            box.label(
                text=f"{result.error_count} errors · {result.warning_count} warnings"
            )
            if not result.expanded:
                continue
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
                        "Hide Problems"
                        if overview_visible
                        else "Show Problems"
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
                selection_domain = issue_selection_domain(issue.code)
                if selection_domain:
                    finding = box.column(align=True)
                    finding.label(text=f"{prefix}{issue.message}{suffix}", icon=icon)
                    row = finding.row(align=True)
                else:
                    row = box.row(align=True)
                    row.label(text=f"{prefix}{issue.message}{suffix}", icon=icon)
                if selection_domain:
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

            metrics = box.box()
            if _draw_disclosure(
                metrics,
                result,
                "metrics_expanded",
                "Mesh Statistics",
                "MESH_DATA",
            ):
                metrics.label(
                    text=(
                        f"Base {result.base_triangles:,} tris  →  "
                        f"Evaluated {result.evaluated_triangles:,}"
                    )
                )
                metrics.label(
                    text=(
                        f"{result.base_vertices:,} verts · {result.base_edges:,} edges · "
                        f"{result.base_faces:,} faces"
                    )
                )
                metrics.label(
                    text=(
                        f"Face mix {result.triangle_faces:,} tris · "
                        f"{result.quad_faces:,} quads · {result.ngon_faces:,} ngons"
                    )
                )
                metrics.label(
                    text=(
                        f"Poles {result.three_poles:,} × 3 · {result.five_poles:,} × 5 · "
                        f"{result.six_plus_poles:,} × 6+"
                    )
                )
                metrics.label(
                    text=(
                        f"Size {result.dimensions[0]:.3g} × {result.dimensions[1]:.3g} × "
                        f"{result.dimensions[2]:.3g} scene units"
                    )
                )

            topology = box.box()
            if _draw_disclosure(
                topology,
                result,
                "topology_expanded",
                "Topology Tools",
                "OVERLAY",
            ):
                row = topology.row(align=True)
                face_map_visible = highlight_state.is_overview_active(
                    object_name,
                    "FACE_MAP",
                )
                face_map = row.operator(
                    "onyx.highlight_topology_map",
                    text="Hide Face Map" if face_map_visible else "Face Map",
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
                    text="Hide Pole Map" if pole_map_visible else "Pole Map",
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


CLASSES = (ONYX_PT_review,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
