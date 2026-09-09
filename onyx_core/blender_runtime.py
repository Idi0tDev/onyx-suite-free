"""Blender registration boundary kept separate from the pure framework."""

import bpy

from . import operators, preferences
from .api import CORE_VERSION, api
from .integration import publish, unpublish
from .lifecycle import Lifecycle


_endpoint = None
_MINIMUM_COMPATIBLE_API = (1, 0)


def _connect():
    global _endpoint
    _endpoint = publish(bpy, api)
    # The standalone extension can provide API 1.1 when it owns the broker,
    # while still joining an already-active compatible API 1.0 broker.
    _endpoint.require_api(_MINIMUM_COMPATIBLE_API)


def _disconnect():
    global _endpoint
    if _endpoint is not None and not _endpoint.extensions():
        unpublish(bpy, _endpoint)
    _endpoint = None


def _register_self():
    _endpoint.register_extension(
        "onyx_core",
        "Onyx Core",
        str(CORE_VERSION),
        description="Free shared framework for Onyx Blender extensions",
        capabilities=("onyx.framework", "onyx.interoperability"),
    )


def _unregister_self():
    _endpoint.unregister_extension("onyx_core")


LIFECYCLE = Lifecycle("Onyx Core")
LIFECYCLE.add("operators", operators.register, operators.unregister)
LIFECYCLE.add("preferences", preferences.register, preferences.unregister)
LIFECYCLE.add("API broker", _connect, _disconnect)
LIFECYCLE.add("framework registration", _register_self, _unregister_self)


def register():
    LIFECYCLE.register()


def unregister():
    LIFECYCLE.unregister()
