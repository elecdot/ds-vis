"""
Animation operation types and timeline utilities.

The concrete op set and semantics are defined in Phase 1 (OPS_SPEC).
"""
from .ops import AnimationOp
from .timeline import Timeline

__all__ = ["AnimationOp", "Timeline"]