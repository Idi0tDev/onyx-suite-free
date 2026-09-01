"""Framework status shown in Blender's extension preferences."""

import platform
import sys

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences

from .api import api
from .integration import discover


class ONYX_CORE_Preferences(AddonPreferences):
    bl_idname = __package__

    show_services: BoolProperty(
        name="Show Runtime Services",
        description="List the versioned services currently published by enabled Onyx extensions",
        default=True,
    )
    show_runtime: BoolProperty(
        name="Show Runtime Details",
        description="Show Blender, Python, operating system, and API version details for diagnostics",
        default=False,
    )

    def draw(self, _context):
        layout = self.layout
        endpoint = discover(bpy) or api
        diagnostics = endpoint.diagnostics()

        framework = layout.box()
        framework.label(text=f"Onyx Core {diagnostics['core_version']}", icon="PACKAGE")
        framework.label(text="Shared framework only — no artist tools are included")
        framework.operator("onyx.validate_core_framework", icon="CHECKMARK")

        extensions = layout.box()
        extensions.label(text="Registered Onyx Extensions", icon="PLUGIN")
        consumers = [item for item in endpoint.extensions() if item.extension_id != "onyx_core"]
        if consumers:
            for item in consumers:
                row = extensions.row()
                row.label(text=item.name)
                row.label(text=str(item.version))
        else:
            extensions.label(text="No extensions have registered with Core", icon="INFO")

        layout.prop(self, "show_services")
        if self.show_services:
            services = layout.box()
            services.label(text="Runtime Services", icon="NETWORK_DRIVE")
            records = endpoint.services()
            if records:
                for item in records:
                    row = services.row()
                    row.label(text=item.service_id)
                    row.label(text=f"{item.version} · {item.owner_id}")
            else:
                services.label(text="No services are currently published", icon="INFO")

        layout.prop(self, "show_runtime")
        if self.show_runtime:
            runtime = layout.box()
            runtime.label(text="Runtime", icon="CONSOLE")
            runtime.label(text=f"API: {diagnostics['api_version']}")
            runtime.label(text=f"Blender: {bpy.app.version_string}")
            runtime.label(text=f"Python: {sys.version.split()[0]}")
            runtime.label(text=f"Platform: {platform.system()} {platform.machine()}")


CLASSES = (ONYX_CORE_Preferences,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
