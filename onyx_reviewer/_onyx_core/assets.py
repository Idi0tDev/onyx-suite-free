"""Canonical metadata helpers for assets shared by Onyx extensions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from .errors import ValidationError


ASSET_ID = "onyx_asset_id"
ASSET_ROLE = "onyx_asset_role"
SOURCE_NAME = "onyx_source_name"
ASSET_ROLES = frozenset({"HIGH", "LOW", "CAGE", "SOURCE", "RESULT"})


@dataclass(frozen=True)
class AssetReference:
    asset_id: str
    role: str
    source_name: str = ""


def _value(data, key):
    value = data.get(key, "")
    return str(value).strip() if value is not None else ""


def read_asset(data):
    """Read Onyx metadata from any Blender ID-like mapping."""
    asset_id = _value(data, ASSET_ID)
    role = _value(data, ASSET_ROLE).upper()
    if not asset_id or role not in ASSET_ROLES:
        return None
    return AssetReference(asset_id, role, _value(data, SOURCE_NAME))


def tag_asset(data, role, *, asset_id=None, source_name=""):
    """Write canonical metadata and return the normalized reference."""
    role = str(role).strip().upper()
    if role not in ASSET_ROLES:
        raise ValidationError(f"Asset role must be one of: {', '.join(sorted(ASSET_ROLES))}")
    asset_id = str(asset_id or uuid.uuid4()).strip()
    if not asset_id or len(asset_id) > 128:
        raise ValidationError("Asset ID must contain between 1 and 128 characters")
    source_name = str(source_name).strip()
    data[ASSET_ID] = asset_id
    data[ASSET_ROLE] = role
    if source_name:
        data[SOURCE_NAME] = source_name
    elif SOURCE_NAME in data:
        del data[SOURCE_NAME]
    return AssetReference(asset_id, role, source_name)


def clear_asset(data):
    for key in (ASSET_ID, ASSET_ROLE, SOURCE_NAME):
        if key in data:
            del data[key]


def same_asset(left, right):
    left_reference = read_asset(left)
    right_reference = read_asset(right)
    return bool(
        left_reference
        and right_reference
        and left_reference.asset_id == right_reference.asset_id
    )
