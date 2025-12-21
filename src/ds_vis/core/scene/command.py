from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping


class CommandType(Enum):
    """
    High-level operation categories, across all structures.

    Non-exhaustive, extended as needed (e.g. GIT_COMMIT, AVL_ROTATE, etc.).
    """

    # Generic DS commands
    CREATE_STRUCTURE = auto()
    INSERT = auto()
    DELETE_STRUCTURE = auto()
    DELETE_NODE = auto()
    SEARCH = auto()
    UPDATE = auto()

    # Git-related commands (teaching visualization, not real git)
    GIT_INIT = auto()
    GIT_COMMIT = auto()
    GIT_BRANCH = auto()
    GIT_CHECKOUT = auto()
    GIT_MERGE = auto()


@dataclass(frozen=True)
class Command:
    """
    A high-level command issued by UI, DSL, or persistence replay.

    - `structure_id` identifies the target structure instance within the SceneGraph.
    - `type` describes the kind of operation.
    - `payload` contains operation-specific parameters (values, keys, options).

    Concrete shape of `payload` will be documented in DSL/OPS specs.
    """

    structure_id: str
    type: CommandType
    payload: Mapping[str, Any]
