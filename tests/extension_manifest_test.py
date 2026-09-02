from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "version",
    "name",
    "tagline",
    "maintainer",
    "type",
    "tags",
    "blender_version_min",
    "license",
}


def read_manifest(extension_id: str) -> dict[str, object]:
    path = ROOT / extension_id / "blender_manifest.toml"
    with path.open("rb") as handle:
        return tomllib.load(handle)


def read_string_assignment(path: Path, assignment_name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == assignment_name
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise AssertionError(f"Could not find string assignment {assignment_name} in {path}")


def read_version_assignment(path: Path, assignment_name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if not isinstance(target, ast.Name) or target.id != assignment_name:
            continue
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "Version"
            and len(value.args) == 3
        ):
            break
        parts: list[str] = []
        for argument in value.args:
            if not isinstance(argument, ast.Constant) or not isinstance(argument.value, int):
                break
            parts.append(str(argument.value))
        if len(parts) == 3:
            return ".".join(parts)
    raise AssertionError(f"Could not find Version assignment {assignment_name} in {path}")


def validate_manifest(extension_id: str, expected_name: str) -> dict[str, object]:
    manifest = read_manifest(extension_id)
    missing = REQUIRED_FIELDS - manifest.keys()
    assert not missing, f"{extension_id} manifest is missing: {sorted(missing)}"
    assert manifest["schema_version"] == "1.0.0"
    assert manifest["id"] == extension_id
    assert manifest["name"] == expected_name
    assert manifest["type"] == "add-on"
    assert manifest["blender_version_min"] == "5.2.0"
    assert isinstance(manifest["version"], str)
    assert SEMANTIC_VERSION.fullmatch(manifest["version"])
    assert isinstance(manifest["tagline"], str) and manifest["tagline"].strip()
    assert isinstance(manifest["maintainer"], str) and manifest["maintainer"].strip()
    assert isinstance(manifest["tags"], list) and manifest["tags"]
    assert "SPDX:GPL-3.0-or-later" in manifest["license"]
    assert "permissions" not in manifest, f"{extension_id} should not request permissions"
    return manifest


core_manifest = validate_manifest("onyx_core", "Onyx Core")
review_manifest = validate_manifest("onyx_review", "Onyx Review")

core_runtime_version = read_version_assignment(ROOT / "onyx_core" / "api.py", "CORE_VERSION")
review_runtime_version = read_string_assignment(ROOT / "onyx_review" / "__init__.py", "VERSION")

assert core_manifest["version"] == core_runtime_version, (
    f"Core manifest version {core_manifest['version']} does not match runtime {core_runtime_version}"
)
assert review_manifest["version"] == review_runtime_version, (
    f"Review manifest version {review_manifest['version']} does not match runtime {review_runtime_version}"
)

print("ONYX_EXTENSION_MANIFESTS_OK")
