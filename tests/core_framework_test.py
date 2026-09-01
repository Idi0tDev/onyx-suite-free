"""Exercise Onyx Core without importing Blender's bpy module."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from onyx_core.api import OnyxAPI  # noqa: E402
from onyx_core.assets import ASSET_ID, ASSET_ROLE, SOURCE_NAME, clear_asset, read_asset, same_asset, tag_asset  # noqa: E402
from onyx_core.errors import (  # noqa: E402
    DuplicateRegistrationError,
    IncompatibleVersionError,
    LifecycleError,
    MissingExtensionError,
    MissingServiceError,
    ValidationError,
)
from onyx_core.integration import BROKER_KEY, discover, publish, unpublish  # noqa: E402
from onyx_core.lifecycle import Lifecycle, LifecycleState  # noqa: E402
from onyx_core.readiness import Check, Severity, evaluate  # noqa: E402
from onyx_core.registry import FrameworkRegistry, Version  # noqa: E402


def raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as exc:
        return exc
    raise AssertionError(f"Expected {error_type.__name__}")


def test_versions_and_api():
    assert str(Version.parse("2.4.1")) == "2.4.1"
    assert Version.parse((2, 4, 1)) > Version(2, 3, 9)
    raises(ValidationError, Version.parse, "2.4")

    endpoint = OnyxAPI(FrameworkRegistry(), core_version="0.1.0", api_version=(1, 2))
    assert endpoint.supports_api(1)
    assert endpoint.supports_api((1, 2))
    assert not endpoint.supports_api((1, 3))
    assert not endpoint.supports_api((2, 0))
    raises(IncompatibleVersionError, endpoint.require_api, (2, 0))


def test_registry_and_services():
    endpoint = OnyxAPI(FrameworkRegistry())
    extension = endpoint.register_extension(
        "onyx_example",
        "Onyx Example",
        "1.2.3",
        description="Test extension",
        capabilities=("onyx.example.export", "onyx.example.import"),
    )
    assert endpoint.register_extension(
        "onyx_example",
        "Onyx Example",
        "1.2.3",
        description="Test extension",
        capabilities=("onyx.example.import", "onyx.example.export"),
    ) is extension
    raises(
        DuplicateRegistrationError,
        endpoint.register_extension,
        "onyx_example",
        "Renamed Example",
        "1.2.3",
    )

    provider = object()
    service = endpoint.register_service(
        "onyx.example.naming",
        "onyx_example",
        "1.1.0",
        provider,
        description="Naming test",
    )
    assert endpoint.service("onyx.example.naming", "1.0.0") is provider
    assert endpoint.require_service("onyx.example.naming") is provider
    assert endpoint.register_service(
        "onyx.example.naming",
        "onyx_example",
        "1.1.0",
        provider,
        description="Naming test",
    ) is service
    raises(IncompatibleVersionError, endpoint.service, "onyx.example.naming", "2.0.0")
    raises(MissingServiceError, endpoint.require_service, "onyx.example.missing")
    raises(
        MissingExtensionError,
        endpoint.register_service,
        "onyx.orphan.service",
        "onyx_missing",
        "1.0.0",
        object(),
    )

    diagnostics = endpoint.diagnostics()
    assert diagnostics["healthy"]
    assert diagnostics["extension_count"] == 1
    assert diagnostics["service_count"] == 1
    assert endpoint.unregister_extension("onyx_example")
    assert endpoint.service("onyx.example.naming") is None
    assert not endpoint.unregister_extension("onyx_example")


def test_lifecycle():
    events = []
    lifecycle = Lifecycle("Example")
    lifecycle.add("first", lambda: events.append("register first"), lambda: events.append("unregister first"))
    lifecycle.add("second", lambda: events.append("register second"), lambda: events.append("unregister second"))
    assert lifecycle.register()
    assert lifecycle.state is LifecycleState.REGISTERED
    assert not lifecycle.register()
    assert lifecycle.unregister()
    assert events == ["register first", "register second", "unregister second", "unregister first"]
    assert lifecycle.state is LifecycleState.NEW

    rollback_events = []

    def fail():
        rollback_events.append("register failure")
        raise RuntimeError("expected")

    rollback = Lifecycle("Rollback")
    rollback.add("safe", lambda: rollback_events.append("register safe"), lambda: rollback_events.append("undo safe"))
    rollback.add("failure", fail, lambda: rollback_events.append("undo failure"))
    error = raises(LifecycleError, rollback.register)
    assert error.cause.args == ("expected",)
    assert rollback_events == ["register safe", "register failure", "undo safe"]
    assert rollback.state is LifecycleState.NEW


def test_readiness_and_assets():
    warning = Check("uv.warning", False, "UV transfer is disabled", Severity.WARNING)
    blocker = Check("mesh.required", False, "Select a mesh")
    report = evaluate(warning, blocker, ready_message="Ready to build")
    assert not report.ready
    assert report.first_blocker is blocker
    assert report.message == "Select a mesh"
    warning_only = evaluate(warning, ready_message="Ready to build")
    assert warning_only.ready and warning_only.message == "UV transfer is disabled"

    high = {}
    low = {}
    high_reference = tag_asset(high, "high", asset_id="shared-id", source_name="Rock_high")
    low_reference = tag_asset(low, "LOW", asset_id=high_reference.asset_id)
    assert high[ASSET_ROLE] == "HIGH" and high[SOURCE_NAME] == "Rock_high"
    assert low[ASSET_ID] == high[ASSET_ID]
    assert read_asset(low) == low_reference
    assert same_asset(high, low)
    clear_asset(low)
    assert read_asset(low) is None and not same_asset(high, low)


def test_runtime_broker():
    class App:
        driver_namespace = {}

    class FakeBpy:
        app = App()

    endpoint = OnyxAPI(FrameworkRegistry())
    assert publish(FakeBpy, endpoint) is endpoint
    assert discover(FakeBpy) is endpoint
    assert BROKER_KEY in FakeBpy.app.driver_namespace
    assert publish(FakeBpy, endpoint) is endpoint
    # A separately bundled Core copy must join the compatible active broker.
    assert publish(FakeBpy, OnyxAPI(FrameworkRegistry())) is endpoint
    raises(
        DuplicateRegistrationError,
        publish,
        FakeBpy,
        OnyxAPI(FrameworkRegistry(), api_version=(2, 0)),
    )
    assert unpublish(FakeBpy, endpoint)
    assert discover(FakeBpy) is None
    assert not unpublish(FakeBpy, endpoint)


def main():
    test_versions_and_api()
    test_registry_and_services()
    test_lifecycle()
    test_readiness_and_assets()
    test_runtime_broker()
    print("ONYX_CORE_FRAMEWORK_OK")


if __name__ == "__main__":
    main()
