from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from ds_vis.core.ops import Timeline

IdAllocator = Callable[[str, str, int], str]


@dataclass
class BaseModel(ABC):
    """
    Abstract base for all data-structure models.

    Design trade-offs:
      - Use ABC to enforce public interfaces (kind, node_count, apply_operation).
      - Pluggable ID strategy: default monotonic counting; can be injected/overridden
        to support custom IDs.
      - apply_operation does not depend on Command, avoiding reverse coupling from
        Model to SceneGraph.
    """

    structure_id: str
    id_allocator: Optional[IdAllocator] = None
    _next_obj_id: int = field(default=0, init=False, repr=False)

    @property
    @abstractmethod
    def kind(self) -> str:
        """Model type identifier used by SceneGraph dispatch."""

    @property
    @abstractmethod
    def node_count(self) -> int:
        """Logical node count for validation/layout queries."""

    @abstractmethod
    def apply_operation(self, op: str, payload: Mapping[str, Any]) -> Timeline:
        """
        Uniform entry for model-level operations (model-scoped op, not CommandType).
        SceneGraph maps Command -> op+payload, avoiding Model dependency on Command
        definition.
        """

    # ------------------------------------------------------------------ #
    # ID helpers (override or inject allocator for custom schemes)
    # ------------------------------------------------------------------ #
    def allocate_node_id(self, prefix: str) -> str:
        """
        Allocate a node ID scoped to this structure.

        Default monotonic counting; if customization is needed (e.g., GitGraph hash),
        pass id_allocator or override this method.
        """
        if self.id_allocator:
            node_id = self.id_allocator(self.structure_id, prefix, self._next_obj_id)
        else:
            node_id = f"{self.structure_id}_{prefix}_{self._next_obj_id}"
        self._next_obj_id += 1
        return node_id

    def edge_id(self, edge_kind: str, src: str, dst: str) -> str:
        """
        Build a stable edge key scoped to this structure.

        Subclasses can override to adapt to specific edge naming strategies.
        """
        return f"{self.structure_id}|{edge_kind}|{src}->{dst}"
