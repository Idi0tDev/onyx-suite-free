"""Run with Blender 5.2 in background mode to exercise Onyx Review."""

import sys
from pathlib import Path

import bpy
import bmesh


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import onyx_review  # noqa: E402
from onyx_review import highlight_state, operators, properties, viewport_state  # noqa: E402
from onyx_review._onyx_core.integration import BROKER_KEY  # noqa: E402


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
    onyx_review.register()
    assert bpy.app.driver_namespace[BROKER_KEY] is onyx_review.CORE.endpoint
    assert onyx_review.CORE.endpoint.extension("onyx_review") is not None
    check_tooltips()
    check_viewport_restore()
    assert not bpy.ops.onyx.run_review.poll()

    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = "ReviewedCube"
    modifier = cube.modifiers.new("Subdivision", "SUBSURF")
    modifier.levels = 1
    settings = bpy.context.scene.onyx_review
    settings.scope = "ACTIVE"
    settings.triangle_budget = 1_000_000
    assert bpy.ops.onyx.run_review() == {"FINISHED"}
    assert len(settings.results) == 1
    result = settings.results[0]
    assert result.object_name == "ReviewedCube"
    assert result.base_triangles == 12
    assert result.evaluated_triangles > result.base_triangles
    stored_report = operators.format_review_report(operators._stored_summary(settings))
    assert "Onyx Review Report" in stored_report
    assert "ReviewedCube" in stored_report
    assert bpy.ops.onyx.copy_review_report() == {"FINISHED"}

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
    issue_counts = {issue.code: issue.count for issue in settings.results[0].issues}
    assert issue_counts["topology.coincident_vertices"] == 5
    assert issue_counts["topology.disconnected_islands"] == 3
    assert highlight_state.active_highlight() is None

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

    assert bpy.ops.onyx.clear_review() == {"FINISHED"}
    assert not settings.results and not settings.last_summary
    assert highlight_state.active_highlight() is None
    onyx_review.unregister()
    assert BROKER_KEY not in bpy.app.driver_namespace
    print("ONYX_REVIEW_BLENDER_OK")


if __name__ == "__main__":
    main()
