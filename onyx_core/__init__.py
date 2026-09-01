"""Onyx Core: free shared framework for Onyx Blender extensions."""

# Pure framework exports remain safe to import outside Blender. The bpy-facing
# module is loaded only when Blender calls register().
from .api import API_VERSION, CORE_VERSION, OnyxAPI, api
from .assets import ASSET_ID, ASSET_ROLE, ASSET_ROLES, SOURCE_NAME, AssetReference
from .embedded import EmbeddedCore
from .errors import OnyxCoreError
from .lifecycle import Lifecycle, LifecycleState, RegistrationStep
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
    "SOURCE_NAME",
    "AssetReference",
    "Check",
    "EmbeddedCore",
    "ExtensionRecord",
    "FrameworkRegistry",
    "Lifecycle",
    "LifecycleState",
    "OnyxAPI",
    "OnyxCoreError",
    "ReadinessReport",
    "RegistrationStep",
    "ServiceRecord",
    "Severity",
    "Version",
    "api",
    "evaluate",
    "register",
    "unregister",
)
