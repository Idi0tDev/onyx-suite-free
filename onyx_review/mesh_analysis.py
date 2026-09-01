"""Blender mesh inspection without modifying source data."""

from __future__ import annotations

import bmesh

from .analysis import Issue, ObjectReview, Severity


_TRANSFORM_EPSILON = 1.0e-4
_AREA_EPSILON = 1.0e-12
_POSITION_PRECISION = 9

_ISSUE_SELECTION_DOMAINS = {
    "topology.non_manifold": "EDGE",
    "topology.degenerate": "FACE",
    "topology.duplicate_faces": "FACE",
    "topology.winding": "EDGE",
    "topology.boundary": "EDGE",
    "topology.loose_edges": "EDGE",
    "topology.loose_vertices": "VERT",
    "topology.coincident_vertices": "VERT",
    "topology.disconnected_islands": "VERT",
    "topology.ngons": "FACE",
    "topology_map.triangles": "FACE",
    "topology_map.quads": "FACE",
    "topology_map.ngons": "FACE",
    "topology_map.poles_3": "VERT",
    "topology_map.poles_5": "VERT",
    "topology_map.poles_6_plus": "VERT",
}

_TOPOLOGY_CLASSES = {
    "FACE_TRIANGLES": (
        "topology_map.triangles",
        "Triangles",
        "Three-sided faces",
    ),
    "FACE_QUADS": (
        "topology_map.quads",
        "Quads",
        "Four-sided faces",
    ),
    "FACE_NGONS": (
        "topology_map.ngons",
        "Ngons",
        "Faces with more than four sides",
    ),
    "POLES_3": (
        "topology_map.poles_3",
        "3-edge poles",
        "Vertices connected to three edges",
    ),
    "POLES_5": (
        "topology_map.poles_5",
        "5-edge poles",
        "Vertices connected to five edges",
    ),
    "POLES_6_PLUS": (
        "topology_map.poles_6_plus",
        "6+-edge poles",
        "Vertices connected to six or more edges",
    ),
}

_TOPOLOGY_MAP_CLASSES = {
    "FACES": ("FACE_QUADS", "FACE_TRIANGLES", "FACE_NGONS"),
    "POLES": ("POLES_3", "POLES_5", "POLES_6_PLUS"),
}

_SIMPLE_FIXES = {
    "topology.duplicate_faces": (
        "Remove Exact Duplicates",
        "Delete redundant faces only when every vertex position matches exactly",
    ),
    "topology.winding": (
        "Recalculate Winding",
        "Make connected face winding consistent using Blender's normal recalculation",
    ),
    "topology.loose_edges": (
        "Delete Loose Edges",
        "Delete edges that are not used by any face",
    ),
    "topology.loose_vertices": (
        "Delete Loose Vertices",
        "Delete vertices that are not connected to any edge",
    ),
}

TOPOLOGY_CLASS_ENUM_ITEMS = tuple(
    (class_id, label, description)
    for class_id, (_, label, description) in _TOPOLOGY_CLASSES.items()
)


def _issue(code, message, count=1, *, error=False):
    return Issue(
        code,
        message,
        Severity.ERROR if error else Severity.WARNING,
        count,
    )


def _vertex_position_key(vertex):
    return tuple(round(float(value), _POSITION_PRECISION) for value in vertex.co)


def _face_position_key(face):
    return tuple(sorted(_vertex_position_key(vertex) for vertex in face.verts))


def _coincident_vertex_groups(vertices):
    groups = {}
    for vertex in vertices:
        groups.setdefault(_vertex_position_key(vertex), []).append(vertex)
    return tuple(tuple(group) for group in groups.values() if len(group) > 1)


def _duplicate_face_groups(faces):
    groups = {}
    for face in faces:
        groups.setdefault(_face_position_key(face), []).append(face)
    return tuple(tuple(group) for group in groups.values() if len(group) > 1)


def _vertex_islands(bm):
    seen = set()
    islands = []
    for start in bm.verts:
        if start.index in seen:
            continue
        seen.add(start.index)
        stack = [start]
        island = []
        while stack:
            vertex = stack.pop()
            island.append(vertex)
            for edge in vertex.link_edges:
                neighbor = edge.other_vert(vertex)
                if neighbor.index not in seen:
                    seen.add(neighbor.index)
                    stack.append(neighbor)
        islands.append(tuple(island))
    return tuple(islands)


def _secondary_island_vertices(bm):
    islands = _vertex_islands(bm)
    if len(islands) <= 1:
        return ()
    largest_index = max(
        range(len(islands)),
        key=lambda index: (len(islands[index]), -index),
    )
    return tuple(
        vertex
        for index, island in enumerate(islands)
        if index != largest_index
        for vertex in island
    )


def issue_selection_domain(issue_code):
    """Return the element domain for an inspectable finding or topology class."""
    return _ISSUE_SELECTION_DOMAINS.get(issue_code, "")


def topology_class_info(class_id):
    """Return the stable overlay code, label, and description for a class."""
    try:
        return _TOPOLOGY_CLASSES[class_id]
    except KeyError as exc:
        raise ValueError(f"Unknown topology class: {class_id}") from exc


def topology_map_classes(map_kind):
    """Return the ordered topology classes shown by a map."""
    try:
        return _TOPOLOGY_MAP_CLASSES[map_kind]
    except KeyError as exc:
        raise ValueError(f"Unknown topology map: {map_kind}") from exc


def simple_fix_info(issue_code):
    """Return the label and description for a deliberately narrow quick fix."""
    return _SIMPLE_FIXES.get(issue_code)


def _exact_face_position_key(face):
    return tuple(sorted(tuple(vertex.co) for vertex in face.verts))


def _exact_duplicate_faces_to_remove(faces):
    groups = {}
    for face in faces:
        groups.setdefault(_exact_face_position_key(face), []).append(face)
    return tuple(
        face
        for group in groups.values()
        for face in sorted(group, key=lambda item: item.index)[1:]
    )


def apply_simple_fix(mesh, issue_code):
    """Apply one deterministic base-mesh fix and return its changed element count."""
    if issue_code not in _SIMPLE_FIXES:
        raise ValueError(f"No simple fix is available for {issue_code}")

    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        if issue_code == "topology.duplicate_faces":
            elements = _exact_duplicate_faces_to_remove(bm.faces)
            if elements:
                bmesh.ops.delete(bm, geom=elements, context="FACES_ONLY")
        elif issue_code == "topology.winding":
            elements = _matching_elements(bm, issue_code)
            if elements:
                bmesh.ops.recalc_face_normals(bm, faces=tuple(bm.faces))
        elif issue_code == "topology.loose_edges":
            elements = _matching_elements(bm, issue_code)
            if elements:
                bmesh.ops.delete(bm, geom=elements, context="EDGES")
        else:
            elements = _matching_elements(bm, issue_code)
            if elements:
                bmesh.ops.delete(bm, geom=elements, context="VERTS")

        changed = len(elements)
        if changed:
            bm.normal_update()
            bm.to_mesh(mesh)
            mesh.update()
        return changed
    finally:
        bm.free()


def _matching_elements(bm, issue_code):
    if issue_code == "topology.non_manifold":
        return tuple(edge for edge in bm.edges if len(edge.link_faces) > 2)
    if issue_code == "topology.degenerate":
        return tuple(face for face in bm.faces if face.calc_area() <= _AREA_EPSILON)
    if issue_code == "topology.duplicate_faces":
        return tuple(face for group in _duplicate_face_groups(bm.faces) for face in group)
    if issue_code == "topology.winding":
        return tuple(
            edge
            for edge in bm.edges
            if len(edge.link_faces) == 2 and not edge.is_contiguous
        )
    if issue_code == "topology.boundary":
        return tuple(edge for edge in bm.edges if len(edge.link_faces) == 1)
    if issue_code == "topology.loose_edges":
        return tuple(edge for edge in bm.edges if not edge.link_faces)
    if issue_code == "topology.loose_vertices":
        return tuple(vertex for vertex in bm.verts if not vertex.link_edges)
    if issue_code == "topology.coincident_vertices":
        return tuple(
            vertex
            for group in _coincident_vertex_groups(bm.verts)
            for vertex in group
        )
    if issue_code == "topology.disconnected_islands":
        return _secondary_island_vertices(bm)
    if issue_code == "topology.ngons":
        return tuple(face for face in bm.faces if len(face.verts) > 4)
    if issue_code == "topology_map.triangles":
        return tuple(face for face in bm.faces if len(face.verts) == 3)
    if issue_code == "topology_map.quads":
        return tuple(face for face in bm.faces if len(face.verts) == 4)
    if issue_code == "topology_map.ngons":
        return tuple(face for face in bm.faces if len(face.verts) > 4)
    if issue_code == "topology_map.poles_3":
        return tuple(vertex for vertex in bm.verts if len(vertex.link_edges) == 3)
    if issue_code == "topology_map.poles_5":
        return tuple(vertex for vertex in bm.verts if len(vertex.link_edges) == 5)
    if issue_code == "topology_map.poles_6_plus":
        return tuple(vertex for vertex in bm.verts if len(vertex.link_edges) >= 6)
    raise ValueError(f"Finding cannot select mesh elements: {issue_code}")


def select_issue_elements(mesh, issue_code):
    """Select edit-mesh elements matching a finding or topology class."""
    domain = issue_selection_domain(issue_code)
    if not domain:
        raise ValueError(f"Finding cannot select mesh elements: {issue_code}")

    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        face.select_set(False)
    for edge in bm.edges:
        edge.select_set(False)
    for vertex in bm.verts:
        vertex.select_set(False)

    matches = _matching_elements(bm, issue_code)
    for element in matches:
        element.select_set(True)
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    return domain, len(matches)


def issue_overlays_geometry(obj, issue_codes):
    """Build world-space overlay geometry for inspectable element classes."""
    issue_codes = tuple(dict.fromkeys(issue_codes))
    for issue_code in issue_codes:
        if not issue_selection_domain(issue_code):
            raise ValueError(f"Finding cannot highlight mesh elements: {issue_code}")
    owns_bmesh = obj.mode != "EDIT"
    bm = bmesh.new() if owns_bmesh else bmesh.from_edit_mesh(obj.data)
    try:
        if owns_bmesh:
            bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        matrix = obj.matrix_world

        def position(coordinate):
            return tuple(float(value) for value in matrix @ coordinate)

        overlays = []
        for issue_code in issue_codes:
            domain = issue_selection_domain(issue_code)
            matches = _matching_elements(bm, issue_code)
            points = []
            lines = []
            if domain == "VERT":
                points.extend(position(vertex.co) for vertex in matches)
                if issue_code == "topology.disconnected_islands":
                    matched_indices = {vertex.index for vertex in matches}
                    for edge in bm.edges:
                        if all(vertex.index in matched_indices for vertex in edge.verts):
                            lines.extend(position(vertex.co) for vertex in edge.verts)
            elif domain == "EDGE":
                for edge in matches:
                    lines.extend(position(vertex.co) for vertex in edge.verts)
            else:
                for face in matches:
                    points.append(position(face.calc_center_median()))
                    for loop in face.loops:
                        lines.append(position(loop.vert.co))
                        lines.append(position(loop.link_loop_next.vert.co))
            overlays.append(
                (issue_code, domain, tuple(points), tuple(lines), len(matches))
            )
        return tuple(overlays)
    finally:
        if owns_bmesh:
            bm.free()


def issue_overlay_geometry(obj, issue_code):
    """Build world-space points and lines for one inspectable element class."""
    _, domain, points, lines, count = issue_overlays_geometry(obj, (issue_code,))[0]
    return domain, points, lines, count


def _base_mesh_metrics(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        duplicate_faces = sum(
            len(group) - 1 for group in _duplicate_face_groups(bm.faces)
        )
        coincident_vertices = sum(
            len(group) - 1 for group in _coincident_vertex_groups(bm.verts)
        )
        disconnected_islands = max(len(_vertex_islands(bm)) - 1, 0)

        boundaries = sum(1 for edge in bm.edges if len(edge.link_faces) == 1)
        non_manifold = sum(1 for edge in bm.edges if len(edge.link_faces) > 2)
        loose_edges = sum(1 for edge in bm.edges if not edge.link_faces)
        loose_vertices = sum(1 for vertex in bm.verts if not vertex.link_edges)
        degenerate = sum(1 for face in bm.faces if face.calc_area() <= _AREA_EPSILON)
        triangle_faces = sum(1 for face in bm.faces if len(face.verts) == 3)
        quad_faces = sum(1 for face in bm.faces if len(face.verts) == 4)
        ngons = sum(1 for face in bm.faces if len(face.verts) > 4)
        three_poles = sum(1 for vertex in bm.verts if len(vertex.link_edges) == 3)
        five_poles = sum(1 for vertex in bm.verts if len(vertex.link_edges) == 5)
        six_plus_poles = sum(1 for vertex in bm.verts if len(vertex.link_edges) >= 6)
        inconsistent = sum(
            1
            for edge in bm.edges
            if len(edge.link_faces) == 2 and not edge.is_contiguous
        )
        triangles = sum(max(len(face.verts) - 2, 0) for face in bm.faces)
        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "triangles": triangles,
            "boundaries": boundaries,
            "non_manifold": non_manifold,
            "loose_edges": loose_edges,
            "loose_vertices": loose_vertices,
            "degenerate": degenerate,
            "duplicate_faces": duplicate_faces,
            "coincident_vertices": coincident_vertices,
            "disconnected_islands": disconnected_islands,
            "triangle_faces": triangle_faces,
            "quad_faces": quad_faces,
            "ngons": ngons,
            "three_poles": three_poles,
            "five_poles": five_poles,
            "six_plus_poles": six_plus_poles,
            "inconsistent": inconsistent,
        }
    finally:
        bm.free()


def _evaluated_mesh_metrics(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
    try:
        mesh.calc_loop_triangles()
        return len(mesh.vertices), len(mesh.polygons), len(mesh.loop_triangles)
    finally:
        evaluated.to_mesh_clear()


def review_object(obj, depsgraph, *, triangle_budget=100_000):
    if obj.type != "MESH":
        raise TypeError("Onyx Review can inspect mesh objects only")

    base = _base_mesh_metrics(obj.data)
    evaluated_vertices, evaluated_faces, evaluated_triangles = _evaluated_mesh_metrics(
        obj, depsgraph
    )
    issues = []

    if base["non_manifold"]:
        issues.append(
            _issue(
                "topology.non_manifold",
                "Edges connected to more than two faces",
                base["non_manifold"],
                error=True,
            )
        )
    if base["degenerate"]:
        issues.append(
            _issue(
                "topology.degenerate",
                "Faces with effectively zero area",
                base["degenerate"],
                error=True,
            )
        )
    if base["duplicate_faces"]:
        issues.append(
            _issue(
                "topology.duplicate_faces",
                "Faces occupy the same vertex positions",
                base["duplicate_faces"],
                error=True,
            )
        )
    if base["inconsistent"]:
        issues.append(
            _issue(
                "topology.winding",
                "Edges with inconsistent face winding",
                base["inconsistent"],
                error=True,
            )
        )
    if base["boundaries"]:
        issues.append(
            _issue(
                "topology.boundary",
                "Open boundary edges",
                base["boundaries"],
            )
        )
    if base["loose_edges"]:
        issues.append(
            _issue("topology.loose_edges", "Loose edges", base["loose_edges"])
        )
    if base["loose_vertices"]:
        issues.append(
            _issue("topology.loose_vertices", "Loose vertices", base["loose_vertices"])
        )
    if base["coincident_vertices"]:
        issues.append(
            _issue(
                "topology.coincident_vertices",
                "Vertices share the same position",
                base["coincident_vertices"],
            )
        )
    if base["disconnected_islands"]:
        issues.append(
            _issue(
                "topology.disconnected_islands",
                "Additional disconnected mesh islands",
                base["disconnected_islands"],
            )
        )
    if base["ngons"]:
        issues.append(_issue("topology.ngons", "Faces with more than four sides", base["ngons"]))

    scale = tuple(float(value) for value in obj.scale)
    if obj.matrix_world.to_3x3().determinant() < 0.0:
        issues.append(
            _issue(
                "transform.negative_scale",
                "World transform has a negative determinant",
                error=True,
            )
        )
    elif any(abs(abs(value) - 1.0) > _TRANSFORM_EPSILON for value in scale):
        issues.append(_issue("transform.scale", "Scale is not applied"))

    if not obj.data.uv_layers:
        issues.append(_issue("data.uv", "Mesh has no UV map"))
    if not obj.material_slots:
        issues.append(_issue("data.material", "Object has no material slots"))
    if triangle_budget > 0 and evaluated_triangles > triangle_budget:
        issues.append(
            _issue(
                "budget.triangles",
                f"Evaluated mesh exceeds the {triangle_budget:,} triangle review budget",
            )
        )

    return ObjectReview(
        object_name=obj.name,
        base_vertices=base["vertices"],
        base_edges=base["edges"],
        base_faces=base["faces"],
        base_triangles=base["triangles"],
        evaluated_vertices=evaluated_vertices,
        evaluated_faces=evaluated_faces,
        evaluated_triangles=evaluated_triangles,
        dimensions=tuple(abs(float(value)) for value in obj.dimensions),
        triangle_faces=base["triangle_faces"],
        quad_faces=base["quad_faces"],
        ngon_faces=base["ngons"],
        three_poles=base["three_poles"],
        five_poles=base["five_poles"],
        six_plus_poles=base["six_plus_poles"],
        issues=tuple(issues),
    )
