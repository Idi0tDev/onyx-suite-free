"""UI-neutral review profiles for choosing relevant finding groups."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewProfile:
    profile_id: str
    label: str
    description: str
    topology: bool
    transforms: bool
    asset_setup: bool
    triangle_budget: bool

    def __post_init__(self):
        profile_id = str(self.profile_id).strip().upper()
        label = str(self.label).strip()
        description = str(self.description).strip()
        if not profile_id or not label or not description:
            raise ValueError("Review profile identity cannot be empty")
        object.__setattr__(self, "profile_id", profile_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "description", description)
        for name in ("topology", "transforms", "asset_setup", "triangle_budget"):
            object.__setattr__(self, name, bool(getattr(self, name)))

    @property
    def enabled_groups(self):
        groups = []
        if self.topology:
            groups.append("Topology")
        if self.transforms:
            groups.append("Transforms")
        if self.asset_setup:
            groups.append("UVs and materials")
        if self.triangle_budget:
            groups.append("Triangle budget")
        return tuple(groups)

    @property
    def short_summary(self):
        if self.profile_id == "GENERAL":
            return "All finding groups"
        if self.profile_id == "MODELING":
            return "Topology + transforms"
        if self.profile_id == "TOPOLOGY":
            return "Topology findings only"
        count = len(self.enabled_groups)
        if count == 1:
            return "1 finding group enabled"
        return f"{count} finding groups enabled" if count else "Metrics only"


_PRESETS = {
    "GENERAL": ReviewProfile(
        "GENERAL",
        "General",
        "Run every current finding group",
        True,
        True,
        True,
        True,
    ),
    "MODELING": ReviewProfile(
        "MODELING",
        "While Modeling",
        "Focus on topology and transforms while the asset is still being built",
        True,
        True,
        False,
        False,
    ),
    "TOPOLOGY": ReviewProfile(
        "TOPOLOGY",
        "Topology Only",
        "Show mesh-structure findings and skip setup checks",
        True,
        False,
        False,
        False,
    ),
}

PROFILE_ENUM_ITEMS = (
    ("GENERAL", "General", _PRESETS["GENERAL"].description),
    ("MODELING", "While Modeling", _PRESETS["MODELING"].description),
    ("TOPOLOGY", "Topology Only", _PRESETS["TOPOLOGY"].description),
    ("CUSTOM", "Custom", "Choose the finding groups yourself"),
)


def resolve_review_profile(
    profile_id,
    *,
    topology=True,
    transforms=True,
    asset_setup=True,
    triangle_budget=True,
):
    """Return a validated preset or a profile made from the custom switches."""
    profile_id = str(profile_id).strip().upper()
    if profile_id == "CUSTOM":
        return ReviewProfile(
            "CUSTOM",
            "Custom",
            "Use the finding groups selected in Review Options",
            topology,
            transforms,
            asset_setup,
            triangle_budget,
        )
    try:
        return _PRESETS[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown review profile: {profile_id}") from exc
