"""3D Viewport interface for Onyx Review."""

import bpy

from . import highlight_state, operators
from .mesh_analysis import issue_selection_domain


def _status_icon(settings):
    if settings.total_errors:
        return "ERROR"
    if settings.total_warnings:
        return "INFO"
    return "CHECKMARK"


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

        row = layout.row(align=True)
        row.scale_y = 1.25
        row.enabled = bool(targets)
        row.operator(
            "onyx.run_review",
            text="Run Again" if settings.results else "Run Review",
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

        active_highlights = highlight_state.active_highlights()
        if active_highlights:
            active_highlight = active_highlights[0]
            visual = layout.box()
            visual.label(text="Viewport Highlight", icon="HIDE_OFF")
            visual.label(text=active_highlight.object_name, icon="MESH_DATA")
            if len(active_highlights) == 1 and not highlight_state.is_overview_active(
                active_highlight.object_name
            ):
                style = highlight_state.finding_style(
                    active_highlight.issue_code,
                    active_highlight.severity,
                )
                visual.label(text=f"{style.name} · {active_highlight.message}")
            else:
                visual.label(text=f"{len(active_highlights):,} actionable findings")
                visual.label(text="Errors use thicker marks", icon="INFO")
                for highlight in active_highlights:
                    style = highlight_state.finding_style(
                        highlight.issue_code,
                        highlight.severity,
                    )
                    icon = "ERROR" if highlight.severity == "ERROR" else "INFO"
                    visual.label(text=f"{style.name} · {highlight.message}", icon=icon)
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
            box.label(
                text=(
                    f"Size {result.dimensions[0]:.3g} × {result.dimensions[1]:.3g} × "
                    f"{result.dimensions[2]:.3g} scene units"
                )
            )
            if any(issue_selection_domain(issue.code) for issue in result.issues):
                overview_visible = highlight_state.is_overview_active(object_name)
                overview = box.operator(
                    "onyx.highlight_review_object",
                    text="Hide All Findings" if overview_visible else "Show All Findings",
                    icon="HIDE_ON" if overview_visible else "HIDE_OFF",
                )
                overview.object_name = object_name
            if not result.issues:
                box.label(text="No findings", icon="CHECKMARK")
            for issue in result.issues:
                icon = "ERROR" if issue.severity == "ERROR" else "INFO"
                suffix = f" ({issue.count:,})" if issue.count > 1 else ""
                row = box.row(align=True)
                row.label(text=f"{issue.message}{suffix}", icon=icon)
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


CLASSES = (ONYX_PT_review,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
