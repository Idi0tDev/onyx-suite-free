"""Run with Blender 5.2 in background mode to exercise Onyx Reviewer."""

import sys
from pathlib import Path

import bpy
import bmesh


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import onyx_reviewer  # noqa: E402
from onyx_reviewer import (  # noqa: E402
    delta_state,
    highlight_state,
    live_review,
    operators,
    properties,
    viewport_state,
)
from onyx_reviewer._onyx_core.integration import BROKER_KEY  # noqa: E402


class Bag:
    pass


class FakeSpace:
    type = "VIEW_3D"

    def __init__(self):
        self.shading = Bag()
        self.overlay = Bag()
        self.shading.type = "MATERIAL"
        self.shading.light = "MATCAP"
        self.shading.color_type = "RANDOM"
        self.shading.single_color = (0.4, 0.5, 0.6)
        self.shading.show_shadows = False
        self.shading.show_cavity = False
        self.shading.show_xray = True
        self.overlay.show_overlays = False
        self.overlay.show_wireframes = False
        self.overlay.wireframe_opacity = 0.35
        self.overlay.show_face_orientation = False

    def as_pointer(self):
        return 321


def make_problem_mesh():
    mesh = bpy.data.meshes.new("ProblemMesh")
    mesh.from_pydata(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.5, 1.5, 0.0),
            (0.0, 1.0, 0.0),
            (3.0, 3.0, 3.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.5, 1.5, 0.0),
            (0.0, 1.0, 0.0),
        ),
        (),
        ((0, 1, 2, 3, 4), (6, 7, 8), (9, 10, 11, 12, 13)),
    )
    mesh.update()
    obj = bpy.data.objects.new("ProblemAsset", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_simple_fix_mesh():
    mesh = bpy.data.meshes.new("SimpleFixMesh")
    mesh.from_pydata(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, -1.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (4.0, 1.0, 0.0),
            (3.0, 1.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (4.0, 1.0, 0.0),
            (3.0, 1.0, 0.0),
            (6.0, 0.0, 0.0),
            (7.0, 0.0, 0.0),
            (8.0, 0.0, 0.0),
        ),
        ((12, 13),),
        (
            (0, 1, 2),
            (0, 1, 3),
            (4, 5, 6, 7),
            (8, 9, 10, 11),
        ),
    )
    mesh.update()
    obj = bpy.data.objects.new("SimpleFixAsset", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def check_tooltips():
    for cls in properties.CLASSES:
        for identifier in cls.__annotations__:
            prop = cls.bl_rna.properties[identifier]
            assert prop.description.strip(), f"Missing tooltip: {cls.__name__}.{identifier}"
    for cls in operators.CLASSES:
        assert cls.bl_description.strip(), f"Missing operator tooltip: {cls.__name__}"


def check_viewport_restore():
    space = FakeSpace()
    original = {
        "type": space.shading.type,
        "light": space.shading.light,
        "color_type": space.shading.color_type,
        "single_color": space.shading.single_color,
        "show_xray": space.shading.show_xray,
        "show_overlays": space.overlay.show_overlays,
        "wireframe_opacity": space.overlay.wireframe_opacity,
    }
    viewport_state.apply_mode(space, "TOPOLOGY")
    assert space.shading.type == "SOLID"
    assert space.overlay.show_wireframes
    assert viewport_state.restore_space(space)
    assert space.shading.type == original["type"]
    assert space.shading.light == original["light"]
    assert space.shading.color_type == original["color_type"]
    assert tuple(space.shading.single_color) == original["single_color"]
    assert space.shading.show_xray == original["show_xray"]
    assert space.overlay.show_overlays == original["show_overlays"]
    assert space.overlay.wireframe_opacity == original["wireframe_opacity"]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    onyx_reviewer.register()
    assert live_review.is_registered()
    assert delta_state._load_post in bpy.app.handlers.load_post
    assert bpy.app.driver_namespace[BROKER_KEY] is onyx_reviewer.CORE.endpoint
    assert onyx_reviewer.CORE.endpoint.extension("onyx_reviewer") is not None
    check_tooltips()
    check_viewport_restore()
    assert not bpy.ops.onyx.run_review.poll()

    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = "ReviewedCube"
    modifier = cube.modifiers.new("Subdivision", "SUBSURF")
    modifier.levels = 1
    settings = bpy.context.scene.onyx_reviewer
    assert not settings.more_settings_expanded
    assert not settings.delta_expanded
    assert not settings.viewport_tools_expanded
    assert not settings.highlight_legend_expanded
    settings.scope = "ACTIVE"
    settings.triangle_budget = 1_000_000
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert len(settings.results) == 1
    result = settings.results[0]
    assert not result.expanded
    assert not result.metrics_expanded
    assert not result.topology_expanded
    assert result.object_name == "ReviewedCube"
    assert result.base_triangles == 12
    assert result.evaluated_triangles > result.base_triangles
    assert result.triangle_faces == 0
    assert result.quad_faces == 6
    assert result.ngon_faces == 0
    assert result.three_poles == 8
    assert result.five_poles == 0
    assert result.six_plus_poles == 0
    stored_report = operators.format_review_report(operators._stored_summary(settings))
    assert "Onyx Reviewer Report" in stored_report
    assert "ReviewedCube" in stored_report
    assert bpy.ops.onyx.copy_review_report() == {"FINISHED"}

    # Profiles keep work-in-progress reviews useful without pretending missing
    # UVs or materials are always a problem. Custom keeps every group explicit.
    assert settings.last_profile == "General"
    assert {issue.code for issue in settings.results[0].issues} == {"data.material"}
    settings.review_profile = "MODELING"
    assert settings.review_options_dirty
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert settings.last_profile == "While Modeling"
    assert not settings.results[0].issues
    assert not settings.review_options_dirty

    settings.review_profile = "TOPOLOGY"
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert settings.last_profile == "Topology Only"
    assert not settings.results[0].issues

    settings.review_profile = "CUSTOM"
    settings.check_topology = False
    settings.check_transforms = False
    settings.check_asset_setup = True
    settings.check_triangle_budget = False
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert settings.last_profile == "Custom"
    assert {issue.code for issue in settings.results[0].issues} == {"data.material"}

    settings.review_profile = "GENERAL"
    assert bpy.ops.onyx.run_review() == {"FINISHED"}

    # Review Delta keeps a session-only before snapshot. It reports new and
    # resolved findings without touching the mesh, then can be cleared cleanly.
    assert delta_state.baseline(bpy.context.scene) is None
    assert bpy.ops.onyx.set_review_baseline() == {"FINISHED"}
    assert delta_state.baseline(bpy.context.scene) is not None
    assert delta_state.current_delta(bpy.context.scene) is None
    assert all(issue.delta_status == "NONE" for issue in settings.results[0].issues)

    # A different profile changes the meaning of a finding, so an old baseline
    # is cleared instead of showing a misleading improvement.
    settings.review_profile = "MODELING"
    assert delta_state.baseline(bpy.context.scene) is None
    assert settings.review_options_dirty
    assert not bpy.ops.onyx.set_review_baseline.poll()
    settings.review_profile = "GENERAL"
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert bpy.ops.onyx.set_review_baseline() == {"FINISHED"}

    material = bpy.data.materials.new("ReviewDeltaMaterial")
    cube.data.materials.append(material)
    cube.scale.x = 2.0
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    delta = delta_state.current_delta(bpy.context.scene)
    assert delta is not None
    assert {item.code for item in delta.introduced} == {"transform.scale"}
    assert {item.code for item in delta.resolved} == {"data.material"}
    assert settings.results[0].issues[0].delta_status == "INTRODUCED"
    settings.finding_filter = "CHANGES"
    assert {
        issue.code
        for issue in settings.results[0].issues
        if operators.finding_matches_filter(issue, settings.finding_filter)
    } == {"transform.scale"}
    assert bpy.ops.onyx.copy_review_delta() == {"FINISHED"}
    assert bpy.ops.onyx.clear_review_baseline() == {"FINISHED"}
    assert delta_state.baseline(bpy.context.scene) is None
    assert delta_state.current_delta(bpy.context.scene) is None
    assert all(issue.delta_status == "NONE" for issue in settings.results[0].issues)
    settings.finding_filter = "ALL"
    cube.scale.x = 1.0
    cube.data.materials.clear()
    bpy.data.materials.remove(material)
    assert bpy.ops.onyx.run_review() == {"FINISHED"}

    assert bpy.ops.onyx.highlight_topology_map(
        object_name=cube.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    highlights = highlight_state.active_highlights()
    assert highlight_state.is_overview_active(cube.name, "FACE_MAP")
    assert not highlight_state.is_overview_active(cube.name)
    assert len(highlights) == 1
    assert highlights[0].issue_code == "topology_map.quads"
    assert highlights[0].element_count == 6
    assert len(highlights[0].points) == 6
    assert len(highlights[0].lines) == 48
    assert bpy.ops.onyx.highlight_topology_map(
        object_name=cube.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    assert not highlight_state.active_highlights()

    assert bpy.ops.onyx.highlight_topology_map(
        object_name=cube.name,
        map_kind="POLES",
    ) == {"FINISHED"}
    highlights = highlight_state.active_highlights()
    assert highlight_state.is_overview_active(cube.name, "POLE_MAP")
    assert len(highlights) == 1
    assert highlights[0].issue_code == "topology_map.poles_3"
    assert highlights[0].element_count == 8
    assert len(highlights[0].points) == 8
    assert not highlights[0].lines
    assert bpy.ops.onyx.highlight_topology_map(
        object_name=cube.name,
        map_kind="POLES",
    ) == {"FINISHED"}
    assert not highlight_state.active_highlights()

    assert bpy.ops.onyx.inspect_topology_class(
        object_name=cube.name,
        topology_class="POLES_3",
    ) == {"FINISHED"}
    assert bpy.context.mode == "EDIT_MESH"
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False)
    edit_mesh = bmesh.from_edit_mesh(cube.data)
    assert sum(1 for vertex in edit_mesh.verts if vertex.select) == 8
    bpy.ops.object.mode_set(mode="OBJECT")

    # Live Review reuses the same inspection path, invalidates stale overlays,
    # and pauses instead of reading or changing a mesh in Edit Mode.
    settings.live_review = True
    assert live_review.has_pending(bpy.context.scene)
    assert live_review.flush_scene(bpy.context.scene)
    assert settings.live_status == "Up to date"
    live_triangles = settings.results[0].evaluated_triangles

    assert bpy.ops.onyx.highlight_topology_map(
        object_name=cube.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    assert highlight_state.active_highlights()
    modifier.levels = 2
    bpy.context.view_layer.update()
    assert live_review.has_pending(bpy.context.scene)
    assert live_review.flush_scene(bpy.context.scene)
    assert settings.results[0].evaluated_triangles > live_triangles
    assert not highlight_state.active_highlights()

    settings.live_max_vertices = 1
    assert live_review.has_pending(bpy.context.scene)
    assert not live_review.flush_scene(bpy.context.scene)
    assert settings.live_status.startswith("Paused:")
    assert not live_review.has_pending(bpy.context.scene)

    settings.live_max_vertices = 250_000
    bpy.ops.object.mode_set(mode="EDIT")
    assert live_review.has_pending(bpy.context.scene)
    assert not live_review.flush_scene(bpy.context.scene)
    assert "Edit Mode" in settings.live_status
    assert live_review.has_pending(bpy.context.scene)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert live_review.flush_scene(bpy.context.scene)
    assert settings.live_status == "Up to date"
    settings.live_review = False
    assert settings.live_status == "Off"
    assert not live_review.has_pending(bpy.context.scene)

    problem = make_problem_mesh()
    for obj in tuple(bpy.context.selected_objects):
        obj.select_set(False)
    problem.select_set(True)
    bpy.context.view_layer.objects.active = problem
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    codes = {issue.code for issue in settings.results[0].issues}
    assert "topology.degenerate" in codes
    assert "topology.duplicate_faces" in codes
    assert "topology.boundary" in codes
    assert "topology.loose_vertices" in codes
    assert "topology.coincident_vertices" in codes
    assert "topology.disconnected_islands" in codes
    assert "topology.ngons" in codes
    assert "data.uv" in codes
    assert "data.material" in codes
    filtered_codes = {
        filter_mode: {
            issue.code
            for issue in settings.results[0].issues
            if operators.finding_matches_filter(issue, filter_mode)
        }
        for filter_mode in ("ALL", "ERRORS", "WARNINGS", "FIXABLE", "CHANGES")
    }
    assert filtered_codes["ALL"] == codes
    assert filtered_codes["ERRORS"] == {
        "topology.degenerate",
        "topology.duplicate_faces",
    }
    assert filtered_codes["WARNINGS"] == codes - filtered_codes["ERRORS"]
    assert filtered_codes["FIXABLE"] == {
        "topology.duplicate_faces",
        "topology.loose_vertices",
    }
    assert filtered_codes["CHANGES"] == set()

    settings.finding_filter = "ERRORS"
    assert bpy.ops.onyx.highlight_review_object(object_name=problem.name) == {"FINISHED"}
    assert {highlight.issue_code for highlight in highlight_state.active_highlights()} == {
        "topology.degenerate",
        "topology.duplicate_faces",
    }
    settings.finding_filter = "WARNINGS"
    assert not highlight_state.active_highlights()
    assert bpy.ops.onyx.highlight_review_object(object_name=problem.name) == {"FINISHED"}
    assert {highlight.issue_code for highlight in highlight_state.active_highlights()} == {
        "topology.boundary",
        "topology.loose_vertices",
        "topology.coincident_vertices",
        "topology.disconnected_islands",
        "topology.ngons",
    }
    settings.finding_filter = "FIXABLE"
    assert not highlight_state.active_highlights()
    assert bpy.ops.onyx.highlight_review_object(object_name=problem.name) == {"FINISHED"}
    assert {highlight.issue_code for highlight in highlight_state.active_highlights()} == {
        "topology.duplicate_faces",
        "topology.loose_vertices",
    }
    settings.finding_filter = "ALL"
    assert not highlight_state.active_highlights()
    assert bpy.ops.onyx.highlight_topology_map(
        object_name=problem.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    settings.finding_filter = "ERRORS"
    assert highlight_state.is_overview_active(problem.name, "FACE_MAP")
    assert bpy.ops.onyx.highlight_topology_map(
        object_name=problem.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    settings.finding_filter = "ALL"
    issue_counts = {issue.code: issue.count for issue in settings.results[0].issues}
    assert issue_counts["topology.coincident_vertices"] == 5
    assert issue_counts["topology.disconnected_islands"] == 3
    assert settings.results[0].triangle_faces == 1
    assert settings.results[0].quad_faces == 0
    assert settings.results[0].ngon_faces == 2
    assert highlight_state.active_highlight() is None

    # The compact navigator follows the finding filter, opens the matching
    # result, selects its object, and cycles focused viewport evidence.
    settings.results[0].expanded = False
    settings.finding_filter = "ERRORS"
    visual_findings = operators.visible_actionable_findings(settings)
    assert [issue.code for _, issue, _ in visual_findings] == [
        "topology.degenerate",
        "topology.duplicate_faces",
    ]
    assert operators.active_visual_finding_index(settings, visual_findings) == -1
    assert bpy.ops.onyx.step_review_finding(direction="NEXT") == {"FINISHED"}
    assert settings.results[0].expanded
    assert bpy.context.view_layer.objects.active == problem
    assert highlight_state.active_highlight().issue_code == "topology.degenerate"
    assert operators.active_visual_finding_index(settings) == 0
    assert bpy.ops.onyx.step_review_finding(direction="NEXT") == {"FINISHED"}
    assert highlight_state.active_highlight().issue_code == "topology.duplicate_faces"
    assert operators.active_visual_finding_index(settings) == 1
    assert bpy.ops.onyx.step_review_finding(direction="NEXT") == {"FINISHED"}
    assert highlight_state.active_highlight().issue_code == "topology.degenerate"
    assert bpy.ops.onyx.step_review_finding(direction="PREVIOUS") == {"FINISHED"}
    assert highlight_state.active_highlight().issue_code == "topology.duplicate_faces"
    highlight_state.clear_highlight()
    settings.finding_filter = "ALL"

    palette_codes = (
        ("topology.non_manifold", "ERROR"),
        ("topology.degenerate", "ERROR"),
        ("topology.duplicate_faces", "ERROR"),
        ("topology.winding", "ERROR"),
        ("topology.boundary", "WARNING"),
        ("topology.loose_edges", "WARNING"),
        ("topology.loose_vertices", "WARNING"),
        ("topology.coincident_vertices", "WARNING"),
        ("topology.disconnected_islands", "WARNING"),
        ("topology.ngons", "WARNING"),
    )
    styles = tuple(
        highlight_state.finding_style(issue_code, severity)
        for issue_code, severity in palette_codes
    )
    assert len({style.name for style in styles}) == len(styles)
    assert len({style.color for style in styles}) == len(styles)
    assert highlight_state.finding_style("unknown.error", "ERROR").name == "Red"
    assert highlight_state.finding_style("unknown.warning", "WARNING").name == "Orange"
    topology_map_codes = (
        "topology_map.triangles",
        "topology_map.quads",
        "topology_map.ngons",
        "topology_map.poles_3",
        "topology_map.poles_5",
        "topology_map.poles_6_plus",
    )
    topology_map_styles = tuple(
        highlight_state.finding_style(issue_code, "INFO")
        for issue_code in topology_map_codes
    )
    assert len({style.name for style in topology_map_styles}) == len(topology_map_styles)
    assert len({style.color for style in topology_map_styles}) == len(topology_map_styles)

    assert bpy.ops.onyx.highlight_topology_class(
        object_name=problem.name,
        topology_class="FACE_TRIANGLES",
    ) == {"FINISHED"}
    highlight = highlight_state.active_highlight()
    assert highlight.issue_code == "topology_map.triangles"
    assert highlight.domain == "FACE"
    assert highlight.element_count == 1
    assert highlight_state.finding_style(highlight.issue_code, "INFO").name == "Gold"
    assert bpy.ops.onyx.highlight_topology_class(
        object_name=problem.name,
        topology_class="FACE_TRIANGLES",
    ) == {"FINISHED"}
    assert not highlight_state.active_highlights()

    assert bpy.ops.onyx.highlight_topology_map(
        object_name=problem.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    highlights = highlight_state.active_highlights()
    assert highlight_state.is_overview_active(problem.name, "FACE_MAP")
    assert {highlight.issue_code for highlight in highlights} == {
        "topology_map.triangles",
        "topology_map.ngons",
    }
    assert {highlight.element_count for highlight in highlights} == {1, 2}
    assert bpy.ops.onyx.highlight_topology_map(
        object_name=problem.name,
        map_kind="FACES",
    ) == {"FINISHED"}
    assert not highlight_state.active_highlights()

    assert bpy.ops.onyx.inspect_topology_class(
        object_name=problem.name,
        topology_class="FACE_TRIANGLES",
    ) == {"FINISHED"}
    assert bpy.context.mode == "EDIT_MESH"
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for face in edit_mesh.faces if face.select) == 1
    bpy.ops.object.mode_set(mode="OBJECT")

    assert bpy.ops.onyx.highlight_review_issue(
        object_name=problem.name,
        issue_code="topology.duplicate_faces",
        message="Faces occupy the same vertex positions",
        severity="ERROR",
    ) == {"FINISHED"}
    highlight = highlight_state.active_highlight()
    assert highlight.object_name == problem.name
    assert highlight.issue_code == "topology.duplicate_faces"
    assert highlight.domain == "FACE"
    assert highlight_state.finding_style(highlight.issue_code, highlight.severity).name == "Magenta"
    assert highlight.element_count == 2
    assert len(highlight.points) == 2
    assert len(highlight.lines) == 20
    assert bpy.ops.onyx.highlight_review_issue(
        object_name=problem.name,
        issue_code="topology.duplicate_faces",
        message="Faces occupy the same vertex positions",
        severity="ERROR",
    ) == {"FINISHED"}
    assert highlight_state.active_highlight() is None

    assert bpy.ops.onyx.highlight_review_object(object_name=problem.name) == {"FINISHED"}
    highlights = highlight_state.active_highlights()
    assert highlight_state.is_overview_active(problem.name)
    assert len(highlights) == 7
    assert {highlight.severity for highlight in highlights} == {"ERROR", "WARNING"}
    assert len(
        {
            highlight_state.finding_style(highlight.issue_code, highlight.severity).color
            for highlight in highlights
        }
    ) == len(highlights)
    assert {highlight.issue_code for highlight in highlights} == {
        "topology.degenerate",
        "topology.duplicate_faces",
        "topology.boundary",
        "topology.loose_vertices",
        "topology.coincident_vertices",
        "topology.disconnected_islands",
        "topology.ngons",
    }
    assert bpy.ops.onyx.highlight_review_object(object_name=problem.name) == {"FINISHED"}
    assert not highlight_state.active_highlights()

    geometry_counts = (
        len(problem.data.vertices),
        len(problem.data.edges),
        len(problem.data.polygons),
    )
    assert operators.issue_selection_domain("topology.duplicate_faces") == "FACE"
    assert not operators.issue_selection_domain("data.uv")
    assert bpy.ops.onyx.inspect_review_issue(
        object_name=problem.name,
        issue_code="topology.duplicate_faces",
    ) == {"FINISHED"}
    assert bpy.context.mode == "EDIT_MESH"
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (False, False, True)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for face in edit_mesh.faces if face.select) == 2
    bpy.ops.object.mode_set(mode="OBJECT")

    assert bpy.ops.onyx.inspect_review_issue(
        object_name=problem.name,
        issue_code="topology.loose_vertices",
    ) == {"FINISHED"}
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for vertex in edit_mesh.verts if vertex.select) == 1
    bpy.ops.object.mode_set(mode="OBJECT")

    assert bpy.ops.onyx.inspect_review_issue(
        object_name=problem.name,
        issue_code="topology.coincident_vertices",
    ) == {"FINISHED"}
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for vertex in edit_mesh.verts if vertex.select) == 10
    bpy.ops.object.mode_set(mode="OBJECT")

    assert bpy.ops.onyx.inspect_review_issue(
        object_name=problem.name,
        issue_code="topology.disconnected_islands",
    ) == {"FINISHED"}
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for vertex in edit_mesh.verts if vertex.select) == 9
    assert bpy.ops.onyx.highlight_review_issue(
        object_name=problem.name,
        issue_code="topology.disconnected_islands",
        message="Additional disconnected mesh islands",
        severity="WARNING",
    ) == {"FINISHED"}
    highlight = highlight_state.active_highlight()
    assert highlight.domain == "VERT"
    assert highlight.element_count == 9
    assert len(highlight.points) == 9
    assert len(highlight.lines) == 16
    bpy.ops.object.mode_set(mode="OBJECT")

    assert bpy.ops.onyx.inspect_review_issue(
        object_name=problem.name,
        issue_code="topology.boundary",
    ) == {"FINISHED"}
    assert tuple(bpy.context.tool_settings.mesh_select_mode) == (False, True, False)
    edit_mesh = bmesh.from_edit_mesh(problem.data)
    assert sum(1 for edge in edit_mesh.edges if edge.select) == 13
    bpy.ops.object.mode_set(mode="OBJECT")
    assert geometry_counts == (
        len(problem.data.vertices),
        len(problem.data.edges),
        len(problem.data.polygons),
    )

    fix_asset = make_simple_fix_mesh()
    for obj in tuple(bpy.context.selected_objects):
        obj.select_set(False)
    fix_asset.select_set(True)
    bpy.context.view_layer.objects.active = fix_asset
    settings.scope = "ACTIVE"
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    fix_codes = {issue.code for issue in settings.results[0].issues}
    assert {
        "topology.duplicate_faces",
        "topology.winding",
        "topology.loose_edges",
        "topology.loose_vertices",
    }.issubset(fix_codes)
    assert operators.simple_fix_info("topology.boundary") is None
    assert "UNDO" in operators.ONYX_OT_fix_review_issue.bl_options

    shared_fix_asset = bpy.data.objects.new("SimpleFixSharedAsset", fix_asset.data)
    bpy.context.collection.objects.link(shared_fix_asset)
    assert fix_asset.data.users == 2
    assert bpy.ops.onyx.fix_review_issue(
        object_name=fix_asset.name,
        issue_code="topology.winding",
    ) == {"CANCELLED"}
    assert "topology.winding" in {
        issue.code for issue in settings.results[0].issues
    }
    bpy.data.objects.remove(shared_fix_asset, do_unlink=True)
    assert fix_asset.data.users == 1

    face_count = len(fix_asset.data.polygons)
    assert bpy.ops.onyx.fix_review_issue(
        object_name=fix_asset.name,
        issue_code="topology.winding",
    ) == {"FINISHED"}
    assert len(fix_asset.data.polygons) == face_count
    assert "topology.winding" not in {
        issue.code for issue in settings.results[0].issues
    }

    assert bpy.ops.onyx.fix_review_issue(
        object_name=fix_asset.name,
        issue_code="topology.duplicate_faces",
    ) == {"FINISHED"}
    assert len(fix_asset.data.polygons) == face_count - 1
    assert "topology.duplicate_faces" not in {
        issue.code for issue in settings.results[0].issues
    }

    assert bpy.ops.onyx.fix_review_issue(
        object_name=fix_asset.name,
        issue_code="topology.loose_edges",
    ) == {"FINISHED"}
    assert "topology.loose_edges" not in {
        issue.code for issue in settings.results[0].issues
    }

    assert bpy.ops.onyx.fix_review_issue(
        object_name=fix_asset.name,
        issue_code="topology.loose_vertices",
    ) == {"FINISHED"}
    assert "topology.loose_vertices" not in {
        issue.code for issue in settings.results[0].issues
    }

    assert bpy.ops.onyx.clear_review() == {"FINISHED"}
    assert not settings.results and not settings.last_summary
    assert highlight_state.active_highlight() is None
    onyx_reviewer.unregister()
    assert not live_review.is_registered()
    assert delta_state._load_post not in bpy.app.handlers.load_post
    assert BROKER_KEY not in bpy.app.driver_namespace
    print("ONYX_REVIEWER_BLENDER_OK")


if __name__ == "__main__":
    main()
