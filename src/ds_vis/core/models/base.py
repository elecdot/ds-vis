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

    设计取舍：
      - 使用 ABC 强制公开接口（kind、node_count、apply_operation）。
      - 可插拔 ID 策略：默认单调计数；可注入/覆写以支持自带 ID。
      - apply_operation 不依赖 Command，避免 Model 对 SceneGraph 反向耦合。
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
        SceneGraph 负责映射 Command → op+payload，避免 Model 依赖 Command 定义。
        """

    # ------------------------------------------------------------------ #
    # ID helpers (override or inject allocator for custom schemes)
    # ------------------------------------------------------------------ #
    def allocate_node_id(self, prefix: str) -> str:
        """
        Allocate a node ID scoped to this structure.

        默认单调计数；如需自定义（GitGraph hash），可传入 id_allocator 或覆写本方法。
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

        子类可覆写以适配特定 edge 命名策略。
        """
        return f"{self.structure_id}|{edge_kind}|{src}->{dst}"
