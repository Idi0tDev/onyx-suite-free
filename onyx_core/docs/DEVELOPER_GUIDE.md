# Onyx Core Developer Guide

## Contract

Onyx Core is infrastructure, not a tool bundle. Every Onyx product vendors the
Core runtime under its own package namespace, while the same source is also
available as a free standalone extension. API v1 owns only shared concerns:
runtime discovery, compatibility checks, registration lifetimes, service
ownership, readiness results, and canonical asset metadata. Product logic stays
inside the product extension.

The public API version and Core package version are separate. Add-ons declare
the API they need; they do not compare the Core package version directly. A
compatible API has the same major version and at least the requested minor
version.

## Attach a bundled product runtime

Products use their relative, vendored runtime and are self-contained:

```python
from ._onyx_core import EmbeddedCore, Lifecycle

CORE = EmbeddedCore(
    bpy,
    "onyx_example",
    "Onyx Example",
    "1.2.0",
    capabilities=("onyx.example.export",),
)

lifecycle = Lifecycle("Onyx Example")
lifecycle.add("Core runtime", CORE.register, CORE.unregister)
lifecycle.add("properties", properties.register, properties.unregister)
lifecycle.add("operators", operators.register, operators.unregister)
lifecycle.add("interface", ui.register, ui.unregister)
```

`tools/sync_embedded_core.ps1` updates the generated `_onyx_core` copies from
the canonical standalone source. Product packagers call the sync automatically.

## Discover the shared runtime

Blender extensions can be installed below different repository namespaces, so
one product must not import another product's Core copy by an assumed module
path. `EmbeddedCore` publishes or joins the API through Blender's runtime-only
driver namespace:

```python
CORE_BROKER_KEY = "onyx.core.api.v1"


def find_core():
    endpoint = bpy.app.driver_namespace.get(CORE_BROKER_KEY)
    if endpoint is None or not endpoint.supports_api((1, 0)):
        return None
    return endpoint
```

The dictionary entry is not saved into the `.blend` file. The last Onyx runtime
removes an empty endpoint when disabled.

## Register an extension manually

Register the extension before any services that it owns. Unregistering the
extension automatically removes all of its remaining services.

```python
core = find_core()
if core is None:
    raise RuntimeError("The bundled Onyx Core runtime did not start")

core.require_api((1, 0))
core.register_extension(
    "onyx_example",
    "Onyx Example",
    "1.2.0",
    description="Example product",
    capabilities=("onyx.example.export",),
)
```

IDs are intentionally strict. Extension IDs use `onyx_example`; capability and
service IDs use reverse-domain-style names beginning with `onyx.`. Registration
is idempotent only when all metadata and provider identity are unchanged.

## Publish and consume a service

A provider may be any non-`None` Python object. Prefer a small object with a
documented method surface over exposing an entire product module.

```python
core.register_service(
    "onyx.asset.naming",
    "onyx_example",
    "1.0.0",
    naming_service,
    description="Resolve source and result asset names",
)

naming = core.require_service("onyx.asset.naming", "1.0.0")
result_name = naming.result_name(source)
```

Only an owning extension may replace its service. Another extension cannot take
over an active service ID. Consumers that support an optional integration can
use `core.service(...)`, which returns `None` when the service is absent.

## Transactional Blender registration

`Lifecycle` keeps enable/disable ordering in one place and rolls back completed
steps if a later registration step fails:

```python
from ._onyx_core import Lifecycle

lifecycle = Lifecycle("Onyx Example")
lifecycle.add("properties", properties.register, properties.unregister)
lifecycle.add("operators", operators.register, operators.unregister)
lifecycle.add("interface", ui.register, ui.unregister)


def register():
    lifecycle.register()


def unregister():
    lifecycle.unregister()
```

Use relative imports for the product's bundled framework. Use the broker only
when communicating with another Onyx product, because the install repository
determines every extension's full module path.

## Shared metadata

`assets.py` standardizes `onyx_asset_id`, `onyx_asset_role`, and the diagnostic
`onyx_source_name`. Helpers accept a Blender ID property collection or any
mutable mapping, which keeps metadata logic testable outside Blender. API v1
roles are `HIGH`, `LOW`, `CAGE`, `SOURCE`, and `RESULT`.

## Failure behavior

The bundled framework is always present. If the active broker has an incompatible
API major version, show a proactive blocker in the product panel and disable the
primary action. If another product's service is optional, continue with the
documented standalone behavior and omit only that integration.
