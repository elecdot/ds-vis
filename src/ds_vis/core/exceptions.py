from __future__ import annotations


class DsVisError(Exception):
    """Base class for all exceptions in the ds-vis domain."""
    pass

class SceneError(DsVisError):
    """Raised when an operation on the SceneGraph fails (e.g. structure not found)."""
    pass

class ModelError(DsVisError):
    """Raised when a data structure model encounters an invalid state or operation."""
    pass

class LayoutError(DsVisError):
    """Raised when the layout engine fails to compute positions."""
    pass

class CommandError(DsVisError):
    """Raised when a command payload is invalid or malformed."""
    pass
