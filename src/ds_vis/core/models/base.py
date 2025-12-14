from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BaseModel:
    """
    Shared utilities and contract for all data-structure models.

    Responsibilities:
      - Hold structure_id.
      - Provide monotonic ID generation helpers (nodes/edges).
      - Act as the stable surface for SceneGraph/commands to rely on,
        without exposing internal state.
    """

    structure_id: str
    _next_obj_id: int = field(default=0, init=False, repr=False)

    @property
    def kind(self) -> str:  # pragma: no cover - interface only
        raise NotImplementedError

    def allocate_node_id(self, prefix: str) -> str:
        """
        Allocate a monotonic node ID scoped to this structure.
        """
        node_id = f"{self.structure_id}_{prefix}_{self._next_obj_id}"
        self._next_obj_id += 1
        return node_id

    def edge_id(self, edge_kind: str, src: str, dst: str) -> str:
        """
        Build a stable edge key scoped to this structure.
        """
        return f"{self.structure_id}|{edge_kind}|{src}->{dst}"
