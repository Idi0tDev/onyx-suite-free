"""Vendored Onyx Core runtime; generated from the standalone Core source."""

from .api import API_VERSION, CORE_VERSION, OnyxAPI, api
from .assets import ASSET_ID, ASSET_ROLE, ASSET_ROLES, SOURCE_NAME, AssetReference
from .embedded import EmbeddedCore
from .errors import OnyxCoreError
from .lifecycle import Lifecycle, LifecycleState, RegistrationStep
from .readiness import Check, ReadinessReport, Severity, evaluate
from .registry import ExtensionRecord, FrameworkRegistry, ServiceRecord, Version


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
)
