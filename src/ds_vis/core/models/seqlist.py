from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class SeqlistModel(BaseModel):
    """
    顺序表模型（数组式），生成仅包含节点的结构 Ops，不使用边。

    设计目标：
    - 支持 create/insert/delete_index/delete_all/search/update。
    - 微步骤包含消息与状态高亮，满足 animation.md 的 L2 诉求。
    - 不包含坐标，布局由 Layout 注入 SET_POS。
    """

    values: List[Any] = field(default_factory=list)
    _node_ids: List[str] = field(default_factory=list)
    _container_id: Optional[str] = None

    @property
    def kind(self) -> str:
        return "seqlist"

    @property
    def node_count(self) -> int:
        return len(self._node_ids)

    def apply_operation(self, op: str, payload: Mapping[str, Any]) -> Timeline:
        if op == "create":
            return self.create(payload.get("values"))
        if op == "delete_all":
            return self.delete_all()
        if op == "delete_index":
            index = payload.get("index")
            if not isinstance(index, int):
                raise ModelError("delete_index requires int index")
            return self.delete_index(index)
        if op == "insert":
            index = payload.get("index")
            if not isinstance(index, int):
                raise ModelError("insert requires int index")
            return self.insert(index=index, value=payload.get("value"))
        if op == "search":
            return self.search(value=payload.get("value"), index=payload.get("index"))
        if op == "update":
            return self.update(
                new_value=payload.get("new_value"),
                index=payload.get("index"),
                value=payload.get("value"),
            )
        raise ModelError(f"Unsupported operation: {op}")

    # ------------------------------------------------------------------ #
    # Public ops
    # ------------------------------------------------------------------ #
    def create(self, values: Optional[list[Any]] = None) -> Timeline:
        timeline = Timeline()
        self.values = list(values or [])
        self._node_ids = []
        ops: List[AnimationOp] = []
        ops.extend(self._create_container_ops(count=len(self.values)))
        for val in self.values:
            node_id = self._create_node_id()
            self._node_ids.append(node_id)
            ops.append(self._op_create_node(node_id, val))
        if not ops:
            ops.append(self._msg("Create empty seqlist"))
        timeline.add_step(AnimationStep(ops=ops, label="Create"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def delete_all(self) -> Timeline:
        timeline = Timeline()
        if not self._node_ids:
            return timeline
        ops: List[AnimationOp] = [self._msg("Delete all")]
        for nid in list(self._node_ids):
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=nid,
                    data={"structure_id": self.structure_id},
                )
            )
        if self._container_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=self._container_id,
                    data={"structure_id": self.structure_id},
                )
            )
            self._container_id = None
        self.values.clear()
        self._node_ids.clear()
        timeline.add_step(AnimationStep(ops=ops, label="Delete all"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def insert(self, index: int, value: Any) -> Timeline:
        if value is None:
            raise ModelError("insert requires value")
        if index < 0 or index > len(self.values):
            raise ModelError("insert index out of range")
        timeline = Timeline()
        msg = f"Insert {value} at index {index}"
        highlight_ops: List[AnimationOp] = [self._msg(msg)]
        if index < len(self._node_ids):
            highlight_ops.append(self._set_state(self._node_ids[index], "highlight"))
        timeline.add_step(AnimationStep(ops=highlight_ops, label="Highlight target"))

        # Highlight shift range
        if index < len(self._node_ids):
            shift_ops = [
                self._set_state(nid, "secondary")
                for nid in self._node_ids[index:]
            ]
            timeline.add_step(AnimationStep(ops=shift_ops, label="Shift range"))

        # Insert new node
        new_id = self._create_node_id()
        self.values.insert(index, value)
        self._node_ids.insert(index, new_id)
        timeline.add_step(
            AnimationStep(
                ops=[self._op_create_node(new_id, value)], label="Create node"
            )
        )

        resize_ops = self._resize_container_ops()
        if resize_ops:
            timeline.add_step(AnimationStep(ops=resize_ops, label="Resize container"))

        # Restore states and clear message
        restore_ops = [self._clear_msg()]
        restore_ops.extend(self._restore_all_states())
        timeline.add_step(AnimationStep(ops=restore_ops, label="Restore"))
        return timeline

    def delete_index(self, index: int) -> Timeline:
        if index < 0 or index >= len(self.values):
            raise ModelError("delete_index out of range")
        timeline = Timeline()
        target_id = self._node_ids[index]

        timeline.add_step(
            AnimationStep(
                ops=[
                    self._msg(f"Delete index {index}"),
                    self._set_state(target_id, "highlight"),
                ],
                label="Highlight",
            )
        )
        timeline.add_step(
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.DELETE_NODE,
                        target=target_id,
                        data={"structure_id": self.structure_id},
                    )
                ],
                label="Delete",
            )
        )
        del self.values[index]
        del self._node_ids[index]

        resize_ops = self._resize_container_ops()
        if resize_ops:
            timeline.add_step(AnimationStep(ops=resize_ops, label="Resize container"))

        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_all_states(), label="Restore"
            )
        )
        return timeline

    def search(self, value: Any = None, index: Any = None) -> Timeline:
        if value is None and index is None:
            raise ModelError("search requires value or index")

        timeline = Timeline()
        for idx, nid in enumerate(self._node_ids):
            msg = (
                f"Compare idx {idx}"
                if value is None
                else f"Compare {self.values[idx]} with {value}"
            )
            timeline.add_step(
                AnimationStep(
                    ops=[self._msg(msg), self._set_state(nid, "highlight")],
                    label="Compare",
                )
            )
            if (index is not None and idx == index) or (
                value is not None and self.values[idx] == value
            ):
                timeline.add_step(
                    AnimationStep(
                        ops=[self._msg(f"Found at index {idx}")],
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
                    ops=[self._set_state(nid, "secondary")], label="Mark visited"
                )
            )

        timeline.add_step(
            AnimationStep(ops=[self._msg("Not found")], label="Miss")
        )
        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_all_states(),
                label="Restore",
            )
        )
        return timeline

    def update(
        self,
        new_value: Any,
        index: Optional[int] = None,
        value: Optional[Any] = None,
    ) -> Timeline:
        if new_value is None:
            raise ModelError("update requires new_value")
        target_idx: Optional[int] = None
        if index is not None:
            if not isinstance(index, int) or index < 0 or index >= len(self.values):
                raise ModelError("update index out of range")
            target_idx = index
        elif value is not None:
            try:
                target_idx = self.values.index(value)
            except ValueError:
                target_idx = None
        if target_idx is None:
            timeline = Timeline()
            timeline.add_step(
                AnimationStep(ops=[self._msg("Update target not found")])
            )
            timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
            return timeline

        nid = self._node_ids[target_idx]
        timeline = Timeline()
        timeline.add_step(
            AnimationStep(
                ops=[
                    self._msg(f"Update index {target_idx} to {new_value}"),
                    self._set_state(nid, "highlight"),
                ],
                label="Highlight",
            )
        )
        timeline.add_step(
            AnimationStep(
                ops=[self._set_label(nid, new_value)], label="Set label"
            )
        )
        self.values[target_idx] = new_value
        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_all_states(),
                label="Restore",
            )
        )
        return timeline

    def export_state(self) -> Mapping[str, object]:
        """Export current values for persistence replay."""
        return {"values": list(self.values)}

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_node_id(self) -> str:
        return self.allocate_node_id("node")

    def _op_create_node(self, node_id: str, value: Any) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=node_id,
            data={
                "structure_id": self.structure_id,
                "label": str(value),
                "shape": "rect",
            },
        )

    def _set_state(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"structure_id": self.structure_id, "state": state},
        )

    def _set_label(self, target: str, value: Any) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_LABEL,
            target=target,
            data={
                "structure_id": self.structure_id,
                "label": str(value),
                "text": str(value),
            },
        )

    def _msg(self, text: str) -> AnimationOp:
        return AnimationOp(op=OpCode.SET_MESSAGE, target=None, data={"text": text})

    def _clear_msg(self) -> AnimationOp:
        return AnimationOp(op=OpCode.CLEAR_MESSAGE, target=None, data={})

    def _restore_all_states(self) -> list[AnimationOp]:
        return [
            self._set_state(nid, "normal")
            for nid in list(self._node_ids)
        ]

    def _create_container_ops(self, count: int) -> list[AnimationOp]:
        width = (
            max(1, count) * 80.0 + 40.0
        )  # approximate spacing; layout controls positions
        height = 40.0
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

    def _resize_container_ops(self) -> list[AnimationOp]:
        if self._container_id is None:
            return self._create_container_ops(count=len(self._node_ids))
        ops: list[AnimationOp] = []
        # delete old
        ops.append(
            AnimationOp(
                op=OpCode.DELETE_NODE,
                target=self._container_id,
                data={"structure_id": self.structure_id},
            )
        )
        ops.extend(self._create_container_ops(count=len(self._node_ids)))
        return ops
