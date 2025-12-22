from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class StackModel(BaseModel):
    """
    栈模型：仅使用节点（矩形单元）和桶容器，不包含边。

    设计要点：
    - 操作：create / push / pop / delete_all / search（教学向线性扫描）。
    - 节点顺序为 **top -> bottom**（index 0 为栈顶），push/pop 都作用于 index 0。
    - 不含坐标信息，Layout 负责定位；容器尺寸随元素数目调整。
    """

    values: List[Any] = field(default_factory=list)  # top -> bottom
    _node_ids: List[str] = field(default_factory=list)
    _container_id: Optional[str] = None
    _cell_spacing: float = 80.0  # 与 LINEAR layout spacing 保持一致

    @property
    def kind(self) -> str:
        return "stack"

    @property
    def node_count(self) -> int:
        return len(self._node_ids)

    def apply_operation(self, op: str, payload: Mapping[str, Any]) -> Timeline:
        if op == "create":
            return self.create(payload.get("values"))
        if op == "delete_all":
            return self.delete_all()
        if op == "push":
            return self.push(payload.get("value"), index=payload.get("index"))
        if op == "pop":
            return self.pop(index=payload.get("index"))
        if op == "search":
            return self.search(value=payload.get("value"))
        raise ModelError(f"Unsupported operation: {op}")

    # ------------------------------------------------------------------ #
    # Public ops
    # ------------------------------------------------------------------ #
    def create(self, values: Optional[list[Any]] = None) -> Timeline:
        timeline = Timeline()
        raw_values = list(values or [])
        # Interpret input as push sequence: 最后一个值为栈顶
        self.values = list(reversed(raw_values))
        self._node_ids = []
        ops: list[AnimationOp] = []
        ops.extend(self._create_container_ops())
        for idx, val in enumerate(self.values):
            node_id = self._create_node_id()
            self._node_ids.append(node_id)
            ops.append(self._op_create_node(node_id, val, index=idx))
        if not ops:
            ops.append(self._msg("Create empty stack"))
        timeline.add_step(AnimationStep(ops=ops, label="Create"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def delete_all(self) -> Timeline:
        timeline = Timeline()
        if not self._node_ids and not self._container_id:
            return timeline
        ops: list[AnimationOp] = [self._msg("Delete all")]
        for nid in list(self._node_ids):
            ops.append(self._delete_node_op(nid))
        if self._container_id:
            ops.append(self._delete_node_op(self._container_id))
            self._container_id = None
        self.values.clear()
        self._node_ids.clear()
        timeline.add_step(AnimationStep(ops=ops, label="Delete all"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def push(self, value: Any, index: Any = None) -> Timeline:
        if value is None:
            raise ModelError("push requires value")
        if index is not None and (not isinstance(index, int) or index != 0):
            raise ModelError("push only supports index=0 (top)")

        timeline = Timeline()
        ensure_ops = self._ensure_container_ops()
        timeline.add_step(
            AnimationStep(
                ops=ensure_ops
                + [
                    self._msg(f"Push {value}"),
                    self._highlight_bucket(),
                ],
                label="Highlight entry",
            )
        )

        new_id = self._create_node_id()
        self.values.insert(0, value)
        self._node_ids.insert(0, new_id)
        timeline.add_step(
            AnimationStep(
                ops=[self._op_create_node(new_id, value, index=0)],
                label="Create node",
            )
        )

        resize_ops = self._resize_container_ops()
        if resize_ops:
            timeline.add_step(AnimationStep(ops=resize_ops, label="Resize container"))

        restore_ops = [self._clear_msg()] + self._restore_all_states()
        timeline.add_step(AnimationStep(ops=restore_ops, label="Restore"))
        return timeline

    def pop(self, index: Any = None) -> Timeline:
        if index is not None and (not isinstance(index, int) or index != 0):
            raise ModelError("pop only supports index=0 (top)")
        timeline = Timeline()
        if not self._node_ids:
            timeline.add_step(AnimationStep(ops=[self._msg("Stack empty")]))
            timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
            return timeline

        top_id = self._node_ids[0]
        timeline.add_step(
            AnimationStep(
                ops=[self._msg("Pop top"), self._set_state(top_id, "highlight")],
                label="Highlight top",
            )
        )
        timeline.add_step(
            AnimationStep(
                ops=[self._delete_node_op(top_id)],
                label="Delete top",
            )
        )
        self._node_ids.pop(0)
        self.values.pop(0)

        resize_ops = self._resize_container_ops()
        if resize_ops:
            timeline.add_step(AnimationStep(ops=resize_ops, label="Resize container"))

        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_all_states(),
                label="Restore",
            )
        )
        return timeline

    def search(self, value: Any = None) -> Timeline:
        if value is None:
            raise ModelError("search requires value")
        timeline = Timeline()
        for idx, (nid, val) in enumerate(zip(self._node_ids, self.values)):
            timeline.add_step(
                AnimationStep(
                    ops=[
                        self._msg(f"Compare top-{idx}"),
                        self._set_state(nid, "highlight"),
                    ],
                    label="Compare",
                )
            )
            if val == value:
                timeline.add_step(
                    AnimationStep(
                        ops=[self._msg(f"Found at top-{idx}")],
                        label="Found",
                    )
                )
                timeline.add_step(
                    AnimationStep(
                        ops=[self._clear_msg()] + self._restore_all_states(),
                        label="Restore",
                    )
                )
                return timeline
            timeline.add_step(
                AnimationStep(
                    ops=[self._set_state(nid, "secondary")],
                    label="Mark visited",
                )
            )
        timeline.add_step(AnimationStep(ops=[self._msg("Not found")], label="Miss"))
        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_all_states(),
                label="Restore",
            )
        )
        return timeline

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_node_id(self) -> str:
        return self.allocate_node_id("node")

    def _op_create_node(
        self, node_id: str, value: Any, index: int | None = None
    ) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=node_id,
            data={
                "structure_id": self.structure_id,
                "label": str(value),
                "shape": "rect",
                "index": index,
            },
        )

    def _delete_node_op(self, target: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.DELETE_NODE,
            target=target,
            data={"structure_id": self.structure_id},
        )

    def _set_state(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"structure_id": self.structure_id, "state": state},
        )

    def _msg(self, text: str) -> AnimationOp:
        return AnimationOp(op=OpCode.SET_MESSAGE, target=None, data={"text": text})

    def _clear_msg(self) -> AnimationOp:
        return AnimationOp(op=OpCode.CLEAR_MESSAGE, target=None, data={})

    def _restore_all_states(self) -> list[AnimationOp]:
        ops: list[AnimationOp] = []
        if self._container_id:
            ops.append(self._set_state(self._container_id, "normal"))
        for nid in list(self._node_ids):
            ops.append(self._set_state(nid, "normal"))
        return ops

    def _highlight_bucket(self) -> AnimationOp:
        if self._container_id:
            return self._set_state(self._container_id, "active")
        return self._msg("Push")  # fallback, should not happen

    def _create_container_ops(self) -> list[AnimationOp]:
        width = 80.0
        height = max(1, len(self.values)) * self._cell_spacing + 40.0
        container_id = self.allocate_node_id("bucket")
        self._container_id = container_id
        return [
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target=container_id,
                data={
                    "structure_id": self.structure_id,
                    "shape": "bucket",
                    "width": width,
                    "height": height,
                },
            )
        ]

    def _ensure_container_ops(self) -> list[AnimationOp]:
        if self._container_id:
            return []
        return self._create_container_ops()

    def _resize_container_ops(self) -> list[AnimationOp]:
        if self._container_id is None:
            return self._create_container_ops()
        ops: list[AnimationOp] = [self._delete_node_op(self._container_id)]
        ops.extend(self._create_container_ops())
        return ops
