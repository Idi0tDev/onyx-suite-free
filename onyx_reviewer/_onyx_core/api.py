"""Versioned public API published to other Onyx Blender extensions."""

from __future__ import annotations

from .errors import IncompatibleVersionError, ValidationError
from .registry import ExtensionRecord, FrameworkRegistry, ServiceRecord, Version


CORE_VERSION = Version(0, 1, 0)
API_VERSION = (1, 0)


def _api_version(value):
    if isinstance(value, int) and not isinstance(value, bool):
        value = (value, 0)
    try:
        parts = tuple(value)
    except TypeError as exc:
        raise ValidationError("API version must be a major integer or a (major, minor) pair") from exc
    if len(parts) != 2 or any(isinstance(part, bool) or not isinstance(part, int) or part < 0 for part in parts):
        raise ValidationError("API version must contain two non-negative integers")
    return parts


class OnyxAPI:
    """Stable facade; consumers should not depend on registry internals."""

    def __init__(self, registry=None, *, core_version=CORE_VERSION, api_version=API_VERSION):
        self._registry = registry or FrameworkRegistry()
        self._core_version = Version.parse(core_version)
        self._api_version = _api_version(api_version)

    @property
    def core_version(self):
        return str(self._core_version)

    @property
    def api_version(self):
        return self._api_version

    def supports_api(self, required_version):
        required = _api_version(required_version)
        return required[0] == self._api_version[0] and required <= self._api_version

    def require_api(self, required_version):
        required = _api_version(required_version)
        if not self.supports_api(required):
            raise IncompatibleVersionError(
                f"Onyx API {self._api_version[0]}.{self._api_version[1]} is installed; "
                f"API {required[0]}.{required[1]} is required"
            )
        return self

    def register_extension(
        self,
        extension_id,
        name,
        version,
        *,
        description="",
        capabilities=(),
        website="",
    ):
        return self._registry.register_extension(
            ExtensionRecord(extension_id, name, Version.parse(version), description, tuple(capabilities), website)
        )

    def unregister_extension(self, extension_id):
        return self._registry.unregister_extension(extension_id)

    def extension(self, extension_id):
        return self._registry.extension(extension_id)

    def extensions(self):
        return self._registry.extensions()

    def register_service(
        self,
        service_id,
        owner_id,
        version,
        provider,
        *,
        description="",
        replace=False,
    ):
        return self._registry.register_service(
            ServiceRecord(service_id, owner_id, Version.parse(version), provider, description),
            replace=replace,
        )

    def unregister_service(self, service_id, *, owner_id=None):
        return self._registry.unregister_service(service_id, owner_id=owner_id)

    def service(self, service_id, minimum_version=None):
        record = self._registry.service(service_id, minimum_version)
        return None if record is None else record.provider

    def service_record(self, service_id, minimum_version=None):
        return self._registry.service(service_id, minimum_version)

    def require_service(self, service_id, minimum_version=None):
        return self._registry.require_service(service_id, minimum_version).provider

    def services(self):
        return self._registry.services()

    def diagnostics(self):
        extensions = self.extensions()
        services = self.services()
        issues = self._registry.audit()
        return {
            "core_version": self.core_version,
            "api_version": f"{self.api_version[0]}.{self.api_version[1]}",
            "extension_count": len(extensions),
            "service_count": len(services),
            "extensions": tuple(
                {
                    "id": item.extension_id,
                    "name": item.name,
                    "version": str(item.version),
                    "capabilities": item.capabilities,
                }
                for item in extensions
            ),
            "services": tuple(
                {
                    "id": item.service_id,
                    "owner": item.owner_id,
                    "version": str(item.version),
                }
                for item in services
            ),
            "issues": issues,
            "healthy": not issues,
        }


api = OnyxAPI()
