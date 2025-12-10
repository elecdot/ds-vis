from __future__ import annotations

"""
Animation operation and timeline primitives.

This package implements the data structures specified in OPS_SPEC v1.0:
- AnimationOp: a single semantic operation (no time attached)
- AnimationStep: a teaching micro-step with duration and ops
- Timeline: an ordered sequence of steps
"""

from .ops import OpCode, AnimationOp
from .timeline import AnimationStep, Timeline

__all__ = [
    "OpCode",
    "AnimationOp",
    "AnimationStep",
    "Timeline",
]
