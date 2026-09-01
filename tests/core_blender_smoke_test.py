"""Run with Blender 5.2 in background mode to verify Onyx Core registration."""

import sys
from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import onyx_core  # noqa: E402
from onyx_core import operators, preferences  # noqa: E402
from onyx_core.integration import BROKER_KEY, discover  # noqa: E402


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    onyx_core.register()

    endpoint = discover(bpy)
    assert endpoint is onyx_core.api
    assert bpy.app.driver_namespace[BROKER_KEY] is endpoint
    assert endpoint.supports_api((1, 0))
    assert endpoint.extension("onyx_core").name == "Onyx Core"

    for preferences_class in preferences.CLASSES:
        for identifier in preferences_class.__annotations__:
            prop = preferences_class.bl_rna.properties[identifier]
            assert prop.description.strip(), f"Missing tooltip: {preferences_class.__name__}.{identifier}"
    for operator in operators.CLASSES:
        assert operator.bl_description.strip(), f"Missing operator tooltip: {operator.__name__}"

    endpoint.register_extension(
        "onyx_smoke",
        "Onyx Smoke Consumer",
        "1.0.0",
        capabilities=("onyx.smoke.test",),
    )
    provider = object()
    endpoint.register_service("onyx.smoke.service", "onyx_smoke", "1.0.0", provider)
    assert endpoint.require_service("onyx.smoke.service", "1.0.0") is provider
    assert bpy.ops.onyx.validate_core_framework() == {"FINISHED"}

    diagnostics = endpoint.diagnostics()
    assert diagnostics["healthy"]
    assert diagnostics["extension_count"] == 2
    assert diagnostics["service_count"] == 1

    endpoint.unregister_extension("onyx_smoke")
    assert endpoint.service("onyx.smoke.service") is None
    onyx_core.unregister()
    assert BROKER_KEY not in bpy.app.driver_namespace
    assert endpoint.extensions() == ()
    assert endpoint.services() == ()

    # Registration must be clean after a normal disable/enable cycle.
    onyx_core.register()
    assert discover(bpy) is endpoint
    onyx_core.unregister()
    print("ONYX_CORE_BLENDER_OK")


if __name__ == "__main__":
    main()
