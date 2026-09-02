"""Publish and discover the Onyx API without cross-extension imports."""

from .api import api
from .errors import DuplicateRegistrationError


BROKER_KEY = "onyx.core.api.v1"


def publish(bpy_module, endpoint=api):
    namespace = bpy_module.app.driver_namespace
    existing = namespace.get(BROKER_KEY)
    if existing is not None and existing is not endpoint:
        existing_version = getattr(existing, "api_version", None)
        incoming_version = getattr(endpoint, "api_version", None)
        compatible = (
            isinstance(existing_version, tuple)
            and isinstance(incoming_version, tuple)
            and existing_version
            and incoming_version
            and existing_version[0] == incoming_version[0] == 1
        )
        if not compatible:
            raise DuplicateRegistrationError("An incompatible Onyx Core API v1 endpoint is already active")
        return existing
    namespace[BROKER_KEY] = endpoint
    return endpoint


def discover(bpy_module):
    return bpy_module.app.driver_namespace.get(BROKER_KEY)


def unpublish(bpy_module, endpoint=api):
    namespace = bpy_module.app.driver_namespace
    if namespace.get(BROKER_KEY) is endpoint:
        del namespace[BROKER_KEY]
        return True
    return False
