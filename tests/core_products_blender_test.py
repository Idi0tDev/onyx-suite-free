"""Verify every product-bundled Core runtime cooperates in Blender 5.2."""

import importlib
import sys
from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import onyx_core  # noqa: E402
from onyx_core.integration import BROKER_KEY  # noqa: E402


def product_ids():
    return tuple(
        path.name
        for path in sorted(PROJECT_ROOT.glob("onyx_*"))
        if path.name != "onyx_core"
        and path.is_dir()
        and (path / "blender_manifest.toml").is_file()
        and (path / "__init__.py").is_file()
    )


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    ids = product_ids()
    assert ids, "No Onyx product extensions were discovered"
    products = tuple(importlib.import_module(product_id) for product_id in ids)
    endpoint = None
    for product in products:
        product.register()
        if endpoint is None:
            endpoint = bpy.app.driver_namespace[BROKER_KEY]
        assert product.CORE.endpoint is endpoint
    assert {item.extension_id for item in endpoint.extensions()} == set(ids)

    # The optional standalone extension must join the already-active runtime.
    onyx_core.register()
    assert bpy.app.driver_namespace[BROKER_KEY] is endpoint
    assert endpoint.extension("onyx_core") is not None
    assert bpy.ops.onyx.validate_core_framework() == {"FINISHED"}

    # Disabling standalone Core leaves the self-contained products operational.
    onyx_core.unregister()
    assert bpy.app.driver_namespace[BROKER_KEY] is endpoint
    assert endpoint.extension("onyx_core") is None
    assert len(endpoint.extensions()) == len(products)

    for index, product in enumerate(reversed(products)):
        product.unregister()
        if index < len(products) - 1:
            assert bpy.app.driver_namespace[BROKER_KEY] is endpoint
    assert BROKER_KEY not in bpy.app.driver_namespace
    print("ONYX_CORE_PRODUCTS_OK")


if __name__ == "__main__":
    main()
