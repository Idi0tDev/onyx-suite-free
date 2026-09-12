"""Accessible viewport color definitions shared by Reviewer editions."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import BASE_RULES


DEFAULT_PALETTE = "ONYX"
PALETTE_ENUM_ITEMS = (
    ("ONYX", "Onyx", "Use the familiar bright Onyx colors"),
    (
        "HIGH_CONTRAST",
        "High Contrast",
        "Use very bright colors that stand out against Blender's dark viewport",
    ),
    (
        "COLORBLIND_SAFE",
        "Colorblind Safe",
        "Use a blue, orange, yellow, purple, and teal focused palette",
    ),
)


@dataclass(frozen=True)
class FindingStyle:
    """One human label and one straight-alpha viewport color."""

    name: str
    color: tuple[float, float, float, float]

    def __post_init__(self):
        name = str(self.name).strip()
        try:
            color = tuple(float(channel) for channel in self.color)
        except TypeError as exc:
            raise ValueError("A finding color must contain four numbers") from exc
        if not name:
            raise ValueError("A finding color needs a readable name")
        if len(color) != 4 or any(channel < 0.0 or channel > 1.0 for channel in color):
            raise ValueError(f"Invalid RGBA color for {name}: {color}")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "color", color)


_TOPOLOGY_MAP_STYLE_IDS = (
    "topology_map.triangles",
    "topology_map.quads",
    "topology_map.ngons",
    "topology_map.poles_3",
    "topology_map.poles_5",
    "topology_map.poles_6_plus",
)
BASE_STYLE_IDS = tuple(
    rule.rule_id
    for rule in BASE_RULES
    if rule.evidence_domain in {"VERT", "EDGE", "FACE"}
) + _TOPOLOGY_MAP_STYLE_IDS


def _style(name, red, green, blue, alpha):
    return FindingStyle(name, (red, green, blue, alpha))


# ONYX intentionally preserves every color shipped before palette selection was
# added. Artists opening an older file therefore see no surprise color changes.
_ONYX = {
    "topology.non_manifold": _style("Red", 1.0, 0.05, 0.12, 0.98),
    "topology.degenerate": _style("Rose", 1.0, 0.08, 0.42, 0.98),
    "topology.duplicate_faces": _style("Magenta", 0.95, 0.08, 1.0, 0.98),
    "topology.overlapping_faces": _style("Mint", 0.05, 1.0, 0.58, 0.98),
    "topology.non_planar_faces": _style(
        "Light Lavender", 0.76, 0.56, 1.0, 0.98
    ),
    "topology.normal_outliers": _style("Indigo", 0.25, 0.08, 0.95, 0.98),
    "topology.winding": _style("Purple", 0.62, 0.24, 1.0, 0.98),
    "topology.boundary": _style("Cyan", 0.05, 0.82, 1.0, 0.96),
    "topology.loose_edges": _style("Yellow", 1.0, 0.82, 0.05, 0.96),
    "topology.loose_vertices": _style("Lime", 0.55, 1.0, 0.12, 0.96),
    "topology.coincident_vertices": _style("Orange", 1.0, 0.34, 0.03, 0.96),
    "topology.disconnected_islands": _style("Blue", 0.12, 0.42, 1.0, 0.96),
    "topology.ngons": _style("Amber", 1.0, 0.58, 0.04, 0.96),
    "topology_map.triangles": _style("Gold", 1.0, 0.72, 0.04, 0.96),
    "topology_map.quads": _style("Teal", 0.05, 0.86, 0.64, 0.96),
    "topology_map.ngons": _style("Coral", 1.0, 0.18, 0.08, 0.98),
    "topology_map.poles_3": _style("Sky", 0.05, 0.64, 1.0, 0.96),
    "topology_map.poles_5": _style("Violet", 0.58, 0.18, 1.0, 0.98),
    "topology_map.poles_6_plus": _style("Pink", 1.0, 0.05, 0.52, 0.98),
}

_HIGH_CONTRAST = {
    "topology.non_manifold": _style("Bright Red", 1.0, 0.0, 0.05, 0.99),
    "topology.degenerate": _style("Hot Rose", 1.0, 0.25, 0.55, 0.99),
    "topology.duplicate_faces": _style("Bright Magenta", 1.0, 0.1, 1.0, 0.99),
    "topology.overlapping_faces": _style("Neon Green", 0.0, 1.0, 0.35, 0.99),
    "topology.non_planar_faces": _style(
        "Bright Lavender", 0.78, 0.6, 1.0, 0.99
    ),
    "topology.normal_outliers": _style("Electric Blue", 0.15, 0.25, 1.0, 0.99),
    "topology.winding": _style("Neon Purple", 0.7, 0.1, 1.0, 0.99),
    "topology.boundary": _style("Electric Cyan", 0.0, 0.9, 1.0, 0.99),
    "topology.loose_edges": _style("Signal Yellow", 1.0, 1.0, 0.05, 0.99),
    "topology.loose_vertices": _style("Chartreuse", 0.55, 1.0, 0.05, 0.99),
    "topology.coincident_vertices": _style("Bright Orange", 1.0, 0.35, 0.0, 0.99),
    "topology.disconnected_islands": _style("Azure", 0.0, 0.55, 1.0, 0.99),
    "topology.ngons": _style("Bright Amber", 1.0, 0.58, 0.0, 0.99),
    "topology_map.triangles": _style("Bright Gold", 1.0, 0.78, 0.0, 0.99),
    "topology_map.quads": _style("Bright Aqua", 0.0, 1.0, 0.72, 0.99),
    "topology_map.ngons": _style("Bright Coral", 1.0, 0.15, 0.02, 0.99),
    "topology_map.poles_3": _style("Bright Sky", 0.0, 0.7, 1.0, 0.99),
    "topology_map.poles_5": _style("Bright Violet", 0.52, 0.25, 1.0, 0.99),
    "topology_map.poles_6_plus": _style("Bright Pink", 1.0, 0.0, 0.48, 0.99),
}

# The blue/orange/teal/purple direction avoids the most common red-green trap.
# Lightness changes separate the extra categories while severity remains
# independently visible through marker size and line weight.
_COLORBLIND_SAFE = {
    "topology.non_manifold": _style("Vermilion", 0.835, 0.369, 0.0, 0.98),
    "topology.degenerate": _style("Reddish Purple", 0.8, 0.475, 0.655, 0.98),
    "topology.duplicate_faces": _style("Pearl", 0.88, 0.88, 0.88, 0.98),
    "topology.overlapping_faces": _style("Bluish Green", 0.0, 0.62, 0.451, 0.98),
    "topology.non_planar_faces": _style("Lavender", 0.7, 0.62, 0.9, 0.98),
    "topology.normal_outliers": _style("Deep Blue", 0.0, 0.35, 0.58, 0.98),
    "topology.winding": _style("Purple", 0.67, 0.45, 0.72, 0.98),
    "topology.boundary": _style("Sky Blue", 0.337, 0.706, 0.914, 0.98),
    "topology.loose_edges": _style("Yellow", 0.941, 0.894, 0.259, 0.98),
    "topology.loose_vertices": _style("Yellow Green", 0.68, 0.78, 0.28, 0.98),
    "topology.coincident_vertices": _style("Orange", 0.902, 0.624, 0.0, 0.98),
    "topology.disconnected_islands": _style("Cornflower", 0.39, 0.56, 0.85, 0.98),
    "topology.ngons": _style("Burnt Orange", 0.75, 0.3, 0.0, 0.98),
    "topology_map.triangles": _style("Soft Gold", 1.0, 0.78, 0.22, 0.98),
    "topology_map.quads": _style("Teal", 0.15, 0.72, 0.67, 0.98),
    "topology_map.ngons": _style("Warm Coral", 0.93, 0.45, 0.25, 0.98),
    "topology_map.poles_3": _style("Pale Sky", 0.48, 0.78, 0.92, 0.98),
    "topology_map.poles_5": _style("Mauve", 0.75, 0.52, 0.72, 0.98),
    "topology_map.poles_6_plus": _style("Soft Pink", 0.92, 0.55, 0.72, 0.98),
}

_PALETTE_STYLES = {
    "ONYX": _ONYX,
    "HIGH_CONTRAST": _HIGH_CONTRAST,
    "COLORBLIND_SAFE": _COLORBLIND_SAFE,
}

_FALLBACK_STYLES = {
    "ONYX": {
        "ERROR": _style("Red", 1.0, 0.12, 0.03, 0.98),
        "WARNING": _style("Orange", 1.0, 0.48, 0.03, 0.96),
    },
    "HIGH_CONTRAST": {
        "ERROR": _style("Bright Red", 1.0, 0.0, 0.05, 0.99),
        "WARNING": _style("Bright Orange", 1.0, 0.45, 0.0, 0.99),
    },
    "COLORBLIND_SAFE": {
        "ERROR": _style("Vermilion", 0.835, 0.369, 0.0, 0.98),
        "WARNING": _style("Orange", 0.902, 0.624, 0.0, 0.98),
    },
}


def normalize_palette_id(palette_id):
    """Return a validated stable palette ID."""
    value = str(palette_id).strip().upper()
    if value not in _PALETTE_STYLES:
        raise ValueError(f"Unknown Reviewer color palette: {palette_id!r}")
    return value


def palette_ids():
    return tuple(item[0] for item in PALETTE_ENUM_ITEMS)


def base_palette_styles(palette_id):
    """Return a copy of every shared style in one palette."""
    return dict(_PALETTE_STYLES[normalize_palette_id(palette_id)])


def base_finding_style(palette_id, issue_code, severity):
    """Resolve one shared style without copying the complete palette."""
    palette_id = normalize_palette_id(palette_id)
    style = _PALETTE_STYLES[palette_id].get(issue_code)
    return style if style is not None else fallback_style(palette_id, severity)


def fallback_style(palette_id, severity):
    """Return a palette-aware style for a finding unknown to the catalog."""
    palette_id = normalize_palette_id(palette_id)
    level = "ERROR" if str(severity).upper() == "ERROR" else "WARNING"
    return _FALLBACK_STYLES[palette_id][level]


_expected_style_ids = frozenset(BASE_STYLE_IDS)
if tuple(_PALETTE_STYLES) != palette_ids():
    raise RuntimeError("Reviewer palette definitions do not match the UI order")
for _palette_id, _styles in _PALETTE_STYLES.items():
    if frozenset(_styles) != _expected_style_ids:
        missing = sorted(_expected_style_ids - frozenset(_styles))
        extra = sorted(frozenset(_styles) - _expected_style_ids)
        raise RuntimeError(
            f"Incomplete {_palette_id} Reviewer palette; missing={missing}, extra={extra}"
        )


__all__ = (
    "BASE_STYLE_IDS",
    "DEFAULT_PALETTE",
    "FindingStyle",
    "PALETTE_ENUM_ITEMS",
    "base_finding_style",
    "base_palette_styles",
    "fallback_style",
    "normalize_palette_id",
    "palette_ids",
)
