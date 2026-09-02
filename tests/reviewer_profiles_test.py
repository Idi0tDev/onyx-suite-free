"""Exercise UI-neutral Onyx Reviewer profile resolution."""

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = PROJECT_ROOT / "onyx_reviewer" / "review_profiles.py"
SPEC = importlib.util.spec_from_file_location("onyx_reviewer_profiles_test_module", PROFILE_PATH)
PROFILES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROFILES
SPEC.loader.exec_module(PROFILES)


def main():
    general = PROFILES.resolve_review_profile("GENERAL")
    assert general.enabled_groups == (
        "Topology",
        "Transforms",
        "UVs and materials",
        "Triangle budget",
    )
    assert general.short_summary == "All finding groups"

    modeling = PROFILES.resolve_review_profile("MODELING")
    assert modeling.topology and modeling.transforms
    assert not modeling.asset_setup and not modeling.triangle_budget

    topology = PROFILES.resolve_review_profile("TOPOLOGY")
    assert topology.enabled_groups == ("Topology",)

    custom = PROFILES.resolve_review_profile(
        "CUSTOM",
        topology=False,
        transforms=False,
        asset_setup=True,
        triangle_budget=False,
    )
    assert custom.enabled_groups == ("UVs and materials",)
    assert custom.short_summary == "1 finding group enabled"
    assert PROFILES.resolve_review_profile(
        "CUSTOM",
        topology=False,
        transforms=False,
        asset_setup=False,
        triangle_budget=False,
    ).short_summary == "Metrics only"

    try:
        PROFILES.resolve_review_profile("UNKNOWN")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected an unknown profile to be rejected")
    print("ONYX_REVIEWER_PROFILES_OK")


if __name__ == "__main__":
    main()
