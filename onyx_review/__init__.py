"""Onyx Review Blender extension."""

import bpy

from . import highlight_state, operators, properties, ui, viewport_state
from ._onyx_core import EmbeddedCore, Lifecycle


VERSION = "0.2.0"

CORE = EmbeddedCore(
    bpy,
    "onyx_review",
    "Onyx Review",
    VERSION,
    description="Reversible topology and mesh-health inspection",
    capabilities=("onyx.review.inspect",),
)

LIFECYCLE = Lifecycle("Onyx Review")
LIFECYCLE.add("Core runtime", CORE.register, CORE.unregister)
LIFECYCLE.add("viewport state", viewport_state.register, viewport_state.unregister)
LIFECYCLE.add("highlight state", highlight_state.register, highlight_state.unregister)
LIFECYCLE.add("properties", properties.register, properties.unregister)
LIFECYCLE.add("operators", operators.register, operators.unregister)
LIFECYCLE.add("interface", ui.register, ui.unregister)


def register():
    LIFECYCLE.register()


def unregister():
    LIFECYCLE.unregister()
