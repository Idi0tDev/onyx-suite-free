"""Blender registration boundary kept separate from the pure framework."""

import bpy

from . import operators, preferences
from .api import API_VERSION, CORE_VERSION, api
from .integration import publish, unpublish
from .lifecycle import Lifecycle


_endpoint = None


def _connect():
    global _endpoint
    _endpoint = publish(bpy, api)
    _endpoint.require_api(API_VERSION)


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
