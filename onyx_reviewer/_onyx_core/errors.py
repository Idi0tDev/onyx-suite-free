"""Public exception hierarchy for the Onyx Core framework."""


class OnyxCoreError(Exception):
    """Base class for failures reported by Onyx Core."""


class ValidationError(OnyxCoreError, ValueError):
    """Raised when framework metadata does not satisfy the public contract."""


class DuplicateRegistrationError(OnyxCoreError):
    """Raised when a different extension or service owns an existing ID."""


class MissingExtensionError(OnyxCoreError, LookupError):
    """Raised when a service refers to an extension that is not registered."""


class MissingServiceError(OnyxCoreError, LookupError):
    """Raised when a required service is unavailable."""


class IncompatibleVersionError(OnyxCoreError):
    """Raised when an API or service is older than a consumer requires."""


class LifecycleError(OnyxCoreError):
    """Raised when transactional registration or unregistration fails."""

    def __init__(self, message, *, cause=None, cleanup_errors=()):
        super().__init__(message)
        self.cause = cause
        self.cleanup_errors = tuple(cleanup_errors)
