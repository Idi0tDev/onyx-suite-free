"""Self-contained Core runtime used inside every Onyx product package."""

from __future__ import annotations

from .api import API_VERSION, api
from .integration import discover, publish, unpublish


class EmbeddedCore:
    """Attach one product to the shared broker using its bundled Core copy."""

    def __init__(
        self,
        bpy_module,
        extension_id,
        name,
        version,
        *,
        description="",
        capabilities=(),
        website="",
        minimum_api=API_VERSION,
    ):
        self._bpy = bpy_module
        self.extension_id = extension_id
        self.name = name
        self.version = version
        self.description = description
        self.capabilities = tuple(capabilities)
        self.website = website
        self.minimum_api = tuple(minimum_api)
        self._endpoint = None

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def registered(self):
        return self._endpoint is not None

    def register(self):
        if self._endpoint is not None:
            return False
        endpoint = discover(self._bpy)
        if endpoint is None:
            endpoint = publish(self._bpy, api)
        endpoint.require_api(self.minimum_api)
        try:
            endpoint.register_extension(
                self.extension_id,
                self.name,
                self.version,
                description=self.description,
                capabilities=self.capabilities,
                website=self.website,
            )
        except Exception:
            if not endpoint.extensions():
                unpublish(self._bpy, endpoint)
            raise
        self._endpoint = endpoint
        return True

    def unregister(self):
        endpoint = self._endpoint
        if endpoint is None:
            return False
        endpoint.unregister_extension(self.extension_id)
        if not endpoint.extensions():
            unpublish(self._bpy, endpoint)
        self._endpoint = None
        return True
