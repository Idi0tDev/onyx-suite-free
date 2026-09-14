"""Stable rule descriptions shared by Onyx Reviewer editions."""

from __future__ import annotations

from dataclasses import dataclass


VALID_CATEGORIES = frozenset({"TOPOLOGY", "TRANSFORMS", "ASSET_SETUP", "BUDGET"})
VALID_SEVERITIES = frozenset({"ERROR", "WARNING"})
VALID_COSTS = frozenset({"QUICK", "DEEP"})
VALID_MODES = frozenset({"OBJECT", "EDIT"})
VALID_DOMAINS = frozenset({"", "VERT", "EDGE", "FACE", "OBJECT"})


@dataclass(frozen=True)
class RuleDefinition:
    """Everything the UI and report need to explain one review rule."""

    rule_id: str
    label: str
    category: str
    severity: str
    scan_cost: str
    modes: tuple[str, ...]
    evidence_domain: str
    recommendation: str
    threshold_keys: tuple[str, ...] = ()
    helper_id: str = ""

    def __post_init__(self):
        rule_id = str(self.rule_id).strip().lower()
        label = str(self.label).strip()
        category = str(self.category).strip().upper()
        severity = str(self.severity).strip().upper()
        scan_cost = str(self.scan_cost).strip().upper()
        modes = tuple(str(mode).strip().upper() for mode in self.modes)
        evidence_domain = str(self.evidence_domain).strip().upper()
        recommendation = str(self.recommendation).strip()
        if isinstance(self.threshold_keys, (str, bytes)):
            raise ValueError(f"Threshold keys must be a tuple for {rule_id}")
        try:
            threshold_keys = tuple(
                str(threshold_key).strip().lower()
                for threshold_key in self.threshold_keys
            )
        except TypeError as exc:
            raise ValueError(f"Threshold keys must be a tuple for {rule_id}") from exc
        helper_id = str(self.helper_id).strip().lower()
        if not rule_id.startswith(("topology.", "transform.", "data.", "budget.")):
            raise ValueError(f"Invalid review rule ID: {rule_id!r}")
        if not label or not recommendation:
            raise ValueError(f"Rule text cannot be empty: {rule_id}")
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category for {rule_id}: {category}")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity for {rule_id}: {severity}")
        if scan_cost not in VALID_COSTS:
            raise ValueError(f"Invalid scan cost for {rule_id}: {scan_cost}")
        if not modes or not set(modes) <= VALID_MODES:
            raise ValueError(f"Invalid supported modes for {rule_id}: {modes}")
        if evidence_domain not in VALID_DOMAINS:
            raise ValueError(f"Invalid evidence domain for {rule_id}: {evidence_domain}")
        if any(
            not threshold_key
            or not threshold_key.isidentifier()
            or threshold_key.startswith("_")
            for threshold_key in threshold_keys
        ):
            raise ValueError(f"Invalid threshold keys for {rule_id}: {threshold_keys}")
        if len(set(threshold_keys)) != len(threshold_keys):
            raise ValueError(f"Duplicate threshold keys for {rule_id}: {threshold_keys}")
        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "scan_cost", scan_cost)
        object.__setattr__(self, "modes", modes)
        object.__setattr__(self, "evidence_domain", evidence_domain)
        object.__setattr__(self, "recommendation", recommendation)
        object.__setattr__(self, "threshold_keys", threshold_keys)
        object.__setattr__(self, "helper_id", helper_id)


def _rule(
    rule_id,
    label,
    category,
    severity,
    domain,
    recommendation,
    *,
    threshold_keys=(),
    helper_id="",
):
    return RuleDefinition(
        rule_id=rule_id,
        label=label,
        category=category,
        severity=severity,
        scan_cost="QUICK",
        modes=("OBJECT", "EDIT"),
        evidence_domain=domain,
        recommendation=recommendation,
        threshold_keys=threshold_keys,
        helper_id=helper_id,
    )


# Keep this order aligned with the active Free scanner. Reports and interfaces can
# then present a stable order without depending on whichever findings happen to fire.
BASE_RULES = (
    _rule(
        "topology.non_manifold",
        "Edges shared by too many faces",
        "TOPOLOGY",
        "ERROR",
        "EDGE",
        "Inspect the highlighted edge and remove internal faces, or rebuild the join "
        "so no more than two faces share the edge.",
    ),
    _rule(
        "topology.degenerate",
        "Zero-area faces",
        "TOPOLOGY",
        "ERROR",
        "FACE",
        "Dissolve or rebuild the zero-area face. If its vertices sit together, merge "
        "them first and check the surrounding faces.",
    ),
    _rule(
        "topology.duplicate_faces",
        "Duplicate faces",
        "TOPOLOGY",
        "ERROR",
        "FACE",
        "Inspect the matching faces, keep the surface you need, and delete only the "
        "redundant copy.",
    ),
    _rule(
        "topology.overlapping_faces",
        "Crossing or overlapping faces",
        "TOPOLOGY",
        "ERROR",
        "FACE",
        "Move or rebuild the highlighted surfaces so they no longer pass through or "
        "cover each other. Keep overlaps only when the asset really needs them.",
    ),
    _rule(
        "topology.non_planar_faces",
        "Non-planar faces",
        "TOPOLOGY",
        "WARNING",
        "FACE",
        "Flatten the highlighted face or split it into stable quads or triangles. "
        "A deliberately bent face can be left alone when its triangulation is safe.",
        threshold_keys=("non_planar_angle",),
    ),
    _rule(
        "topology.normal_outliers",
        "Faces pointing against their neighbors",
        "TOPOLOGY",
        "ERROR",
        "FACE",
        "Compare the highlighted face with its neighbors. Flip that face, or select "
        "the connected patch and use Recalculate Outside if the whole patch is wrong.",
    ),
    _rule(
        "topology.winding",
        "Inconsistent face winding",
        "TOPOLOGY",
        "ERROR",
        "EDGE",
        "Select the connected surface and use Mesh > Normals > Recalculate Outside. "
        "Flip intentional inward-facing parts by hand afterward.",
    ),
    _rule(
        "topology.boundary",
        "Open holes",
        "TOPOLOGY",
        "WARNING",
        "EDGE",
        "Close an accidental hole by filling or bridging its boundary, or weld nearby "
        "vertices. If the opening is intentional, add a hole allowance.",
        threshold_keys=("allowed_boundary_edges",),
    ),
    _rule(
        "topology.loose_edges",
        "Loose edges",
        "TOPOLOGY",
        "WARNING",
        "EDGE",
        "Delete the loose edge if it is leftover construction geometry, or connect it "
        "to faces if it belongs to the final mesh.",
    ),
    _rule(
        "topology.loose_vertices",
        "Loose vertices",
        "TOPOLOGY",
        "WARNING",
        "VERT",
        "Delete the loose vertex if it is accidental, or connect it to the mesh if it "
        "is meant to contribute to the shape.",
    ),
    _rule(
        "topology.coincident_vertices",
        "Coincident unwelded vertices",
        "TOPOLOGY",
        "WARNING",
        "VERT",
        "Inspect the stacked vertices and use Merge by Distance only where those "
        "points are meant to be welded.",
    ),
    _rule(
        "topology.disconnected_islands",
        "Disconnected mesh islands",
        "TOPOLOGY",
        "WARNING",
        "VERT",
        "Remove stray islands, connect pieces that belong together, or separate "
        "intentional pieces into their own objects.",
    ),
    _rule(
        "topology.ngons",
        "Faces with more than four sides",
        "TOPOLOGY",
        "WARNING",
        "FACE",
        "Split the face into clean quads or triangles where it bends or shades badly. "
        "A flat, stable ngon can be left alone or covered by an allowance.",
        threshold_keys=("allowed_ngons",),
    ),
    _rule(
        "transform.negative_scale",
        "Negative object scale",
        "TRANSFORMS",
        "ERROR",
        "OBJECT",
        "In Object Mode, use Apply > Scale when the mirrored result is final, then "
        "check face orientation and modifier behavior.",
    ),
    _rule(
        "transform.scale",
        "Unapplied object scale",
        "TRANSFORMS",
        "WARNING",
        "OBJECT",
        "In Object Mode, use Apply > Scale when the current size should become the "
        "object's new default scale.",
    ),
    _rule(
        "data.uv",
        "Missing UV map",
        "ASSET_SETUP",
        "WARNING",
        "OBJECT",
        "Add and unwrap a UV map if the asset uses image textures, baking, or workflows "
        "that expect UV coordinates.",
    ),
    _rule(
        "data.material",
        "Missing material slot",
        "ASSET_SETUP",
        "WARNING",
        "OBJECT",
        "Add a material slot and assign a material, even if it is only a simple "
        "placeholder for handoff.",
    ),
    _rule(
        "budget.triangles",
        "Triangle budget exceeded",
        "BUDGET",
        "WARNING",
        "OBJECT",
        "Reduce dense source geometry or expensive modifiers, or raise the review "
        "budget when this level of detail is intentional.",
        threshold_keys=("triangle_budget",),
    ),
)

RULE_BY_ID = {rule.rule_id: rule for rule in BASE_RULES}
if len(RULE_BY_ID) != len(BASE_RULES):
    raise RuntimeError("Reviewer rule IDs must be unique")
