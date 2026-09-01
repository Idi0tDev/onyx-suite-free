"""Small diagnostics operator for the framework preferences."""

import bpy
from bpy.types import Operator

from .integration import discover


class ONYX_CORE_OT_validate_framework(Operator):
    bl_idname = "onyx.validate_core_framework"
    bl_label = "Validate Framework"
    bl_description = "Check the Onyx API broker, extension registry, and service ownership for runtime problems"
    bl_options = {"INTERNAL"}

    def execute(self, _context):
        endpoint = discover(bpy)
        if endpoint is None:
            self.report({"ERROR"}, "Onyx API v1 is not published")
            return {"CANCELLED"}
        diagnostics = endpoint.diagnostics()
        if diagnostics["issues"]:
            self.report({"ERROR"}, diagnostics["issues"][0])
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Onyx Core is healthy: {diagnostics['extension_count']} extensions, "
            f"{diagnostics['service_count']} services",
        )
        return {"FINISHED"}


CLASSES = (ONYX_CORE_OT_validate_framework,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
