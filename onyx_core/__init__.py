"""Onyx Core: free shared framework for Onyx Blender extensions."""

# Pure framework exports remain safe to import outside Blender. The bpy-facing
# module is loaded only when Blender calls register().
from .api import API_VERSION, CORE_VERSION, OnyxAPI, api
from .assets import ASSET_ID, ASSET_ROLE, ASSET_ROLES, SOURCE_NAME, AssetReference
from .embedded import EmbeddedCore
from .errors import OnyxCoreError
from .lifecycle import Lifecycle, LifecycleState, RegistrationStep
from .materials import (
    ALPHA,
    AMBIENT_OCCLUSION,
    BASE_COLOR,
    CHANNEL_DESCRIPTORS,
    CHANNEL_SCHEMA_VERSION,
    CHANNEL_SERVICE_ID,
    CHANNEL_SERVICE_VERSION,
    EMISSION,
    HEIGHT,
    MATERIAL_CHANNEL,
    MATERIAL_CHANNEL_SCHEMA,
    MATERIAL_CHANNELS,
    METALLIC,
    NORMAL,
    ROUGHNESS,
    MaterialChannelDescriptor,
    MaterialChannelTag,
    clear_material_channel,
    material_channel_descriptor,
    normalize_material_channel,
    read_material_channel,
    tag_material_channel,
)
from .readiness import Check, ReadinessReport, Severity, evaluate
from .registry import ExtensionRecord, FrameworkRegistry, ServiceRecord, Version


def register():
    from . import blender_runtime

    blender_runtime.register()


def unregister():
    from . import blender_runtime

    blender_runtime.unregister()


__all__ = (
    "API_VERSION",
    "ASSET_ID",
    "ASSET_ROLE",
    "ASSET_ROLES",
    "CORE_VERSION",
    "CHANNEL_DESCRIPTORS",
    "CHANNEL_SCHEMA_VERSION",
    "CHANNEL_SERVICE_ID",
    "CHANNEL_SERVICE_VERSION",
    "MATERIAL_CHANNEL",
    "MATERIAL_CHANNEL_SCHEMA",
    "MATERIAL_CHANNELS",
    "SOURCE_NAME",
    "AssetReference",
    "Check",
    "EmbeddedCore",
    "ExtensionRecord",
    "FrameworkRegistry",
    "Lifecycle",
    "LifecycleState",
    "MaterialChannelDescriptor",
    "MaterialChannelTag",
    "OnyxAPI",
    "OnyxCoreError",
    "ReadinessReport",
    "RegistrationStep",
    "ServiceRecord",
    "Severity",
    "Version",
    "api",
    "clear_material_channel",
    "evaluate",
    "material_channel_descriptor",
    "normalize_material_channel",
    "read_material_channel",
    "register",
    "tag_material_channel",
    "unregister",
    "ALPHA",
    "AMBIENT_OCCLUSION",
    "BASE_COLOR",
    "EMISSION",
    "HEIGHT",
    "METALLIC",
    "NORMAL",
    "ROUGHNESS",
)
