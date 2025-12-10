from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping


class OpKind(Enum):
    """
    High-level kinds of animation operations.

    The exact set and semantics will be refined in OPS_SPEC (Phase 1).
    """
    CREATE_NODE = auto()
    DELETE_NODE = auto()
    MOVE_NODE = auto()
    HIGHLIGHT_NODE = auto()
    CREATE_EDGE = auto()
    DELETE_EDGE = auto()
    SET_LABEL = auto()
    WAIT = auto()
    GROUP = auto()


@dataclass(frozen=True)
class AnimationOp:
    """
    A single animation operation.

    This is intentionally generic for Phase 0:
    - `kind` describes the operation type (CREATE_NODE, MOVE_NODE, etc.).
    - `payload` carries operation-specific parameters.

    In Phase 1, this will either be specialized into distinct dataclasses
    per operation, or have a stronger typed payload schema.
    """

    kind: OpKind
    payload: Mapping[str, Any]
