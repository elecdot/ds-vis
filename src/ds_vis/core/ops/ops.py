from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping, Optional


class OpCode(Enum):
    """
    Operation codes defined in OPS_SPEC v1.0.

    These ops are renderer-independent and can be serialized to JSON.
    """

    # Structural
    CREATE_NODE = auto()
    DELETE_NODE = auto()
    CREATE_EDGE = auto()
    DELETE_EDGE = auto()

    # Layout / position
    SET_POS = auto()

    # Visual / state
    SET_STATE = auto()
    SET_LABEL = auto()

    # Global
    SET_MESSAGE = auto()
    CLEAR_MESSAGE = auto()


@dataclass(frozen=True)
class AnimationOp:
    """
    A single animation operation.

    Mirrors the OPS_SPEC structure:

        {
          "op": "CREATE_NODE",
          "target": "node_7",
          "data": { ... }
        }

    - `op`:       the operation code (OpCode)
    - `target`:   primary object identifier (node_id, edge_id, etc.), or None (global)
    - `data`:     operation-specific payload (keys and values are JSON-serializable)
    """

    op: OpCode
    target: Optional[str]
    data: Mapping[str, Any]
