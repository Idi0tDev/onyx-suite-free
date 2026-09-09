"""Canonical material-channel roles and persistent metadata for Onyx products."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import IncompatibleVersionError, ValidationError
from .registry import Version


CHANNEL_SERVICE_ID = "onyx.material.channels"
CHANNEL_SERVICE_VERSION = "1.0.0"
CHANNEL_SCHEMA_VERSION = "1.0.0"
MATERIAL_CHANNEL = "onyx_material_channel"
MATERIAL_CHANNEL_SCHEMA = "onyx_material_channel_schema"

BASE_COLOR = "BASE_COLOR"
ROUGHNESS = "ROUGHNESS"
METALLIC = "METALLIC"
NORMAL = "NORMAL"
HEIGHT = "HEIGHT"
AMBIENT_OCCLUSION = "AMBIENT_OCCLUSION"
EMISSION = "EMISSION"
ALPHA = "ALPHA"


@dataclass(frozen=True)
class MaterialChannelDescriptor:
    """Stable description of one interoperable material channel."""

    channel_id: str
    label: str
    data_kind: str
    color_role: str

    def as_dict(self):
        return {
            "id": self.channel_id,
            "label": self.label,
            "data_kind": self.data_kind,
            "color_role": self.color_role,
        }


@dataclass(frozen=True)
class MaterialChannelTag:
    """Canonical persistent channel tag read from a mapping or Blender ID property."""

    channel_id: str
    schema_version: str = CHANNEL_SCHEMA_VERSION


CHANNEL_DESCRIPTORS = (
    MaterialChannelDescriptor(BASE_COLOR, "Base Color", "COLOR", "COLOR"),
    MaterialChannelDescriptor(ROUGHNESS, "Roughness", "SCALAR", "DATA"),
    MaterialChannelDescriptor(METALLIC, "Metallic", "SCALAR", "DATA"),
    MaterialChannelDescriptor(NORMAL, "Normal", "VECTOR", "DATA"),
    MaterialChannelDescriptor(HEIGHT, "Height", "SCALAR", "DATA"),
    MaterialChannelDescriptor(AMBIENT_OCCLUSION, "Ambient Occlusion", "SCALAR", "DATA"),
    MaterialChannelDescriptor(EMISSION, "Emission", "COLOR", "COLOR"),
    MaterialChannelDescriptor(ALPHA, "Alpha", "SCALAR", "DATA"),
)
MATERIAL_CHANNELS = tuple(item.channel_id for item in CHANNEL_DESCRIPTORS)
_BY_ID = {item.channel_id: item for item in CHANNEL_DESCRIPTORS}
_ALIASES = {
    "ALBEDO": BASE_COLOR,
    "BASECOLOR": BASE_COLOR,
    "BASE_COLOR": BASE_COLOR,
    "BASE COLOUR": BASE_COLOR,
    "DIFFUSE": BASE_COLOR,
    "ROUGHNESS": ROUGHNESS,
    "METAL": METALLIC,
    "METALLIC": METALLIC,
    "METALNESS": METALLIC,
    "NORMAL": NORMAL,
    "NORMALS": NORMAL,
    "BUMP": HEIGHT,
    "DISPLACEMENT": HEIGHT,
    "HEIGHT": HEIGHT,
    "AMBIENT OCCLUSION": AMBIENT_OCCLUSION,
    "AMBIENT_OCCLUSION": AMBIENT_OCCLUSION,
    "AO": AMBIENT_OCCLUSION,
    "EMISSION": EMISSION,
    "EMISSIVE": EMISSION,
    "ALPHA": ALPHA,
    "OPACITY": ALPHA,
}


def normalize_material_channel(value):
    """Return one canonical role ID or raise for an unknown material channel."""
    text = str(value).strip().upper().replace("-", " ")
    compact = " ".join(text.split())
    channel_id = _ALIASES.get(compact) or _ALIASES.get(compact.replace(" ", "_"))
    if channel_id is None or channel_id not in _BY_ID:
        raise ValidationError(f"Unknown material channel: {value!r}")
    return channel_id


def material_channel_descriptor(value):
    return _BY_ID[normalize_material_channel(value)]


def tag_material_channel(target, channel):
    """Write the canonical role and schema to a mutable mapping or Blender property owner."""
    channel_id = normalize_material_channel(channel)
    target[MATERIAL_CHANNEL] = channel_id
    target[MATERIAL_CHANNEL_SCHEMA] = CHANNEL_SCHEMA_VERSION
    return MaterialChannelTag(channel_id)


def read_material_channel(target):
    """Read one compatible canonical role, returning ``None`` when untagged."""
    raw = target.get(MATERIAL_CHANNEL)
    if raw is None:
        return None
    schema = str(target.get(MATERIAL_CHANNEL_SCHEMA, CHANNEL_SCHEMA_VERSION))
    parsed = Version.parse(schema)
    supported = Version.parse(CHANNEL_SCHEMA_VERSION)
    if parsed.major != supported.major:
        raise IncompatibleVersionError(
            f"Material channel schema {schema} is stored; schema {CHANNEL_SCHEMA_VERSION} is supported"
        )
    return MaterialChannelTag(normalize_material_channel(raw), schema)


def clear_material_channel(target):
    changed = False
    for key in (MATERIAL_CHANNEL, MATERIAL_CHANNEL_SCHEMA):
        if key in target:
            del target[key]
            changed = True
    return changed
