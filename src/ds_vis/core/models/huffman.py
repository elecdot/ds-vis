from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import List, Mapping, Optional

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel, IdAllocator
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass(order=True)
class _QueueNode:
    """内部使用的小顶堆节点，按权值排序。"""

    weight: float
    order: int
    node_id: str = field(compare=False)
    left: Optional[str] = field(default=None, compare=False)
    right: Optional[str] = field(default=None, compare=False)


class HuffmanModel(BaseModel):
    """
    Huffman 构建模型：输入权值列表，逐步合并生成 Huffman 树。

    - 仅支持 build/delete_all。
    - 使用 heapq 维护候选队列，生成 L2 微步骤（高亮两最小、生成父节点、重新入队）。
    - 输出结构 Ops（CREATE_NODE/CREATE_EDGE 等），不包含坐标，位置由 Layout 注入。
    """

    def __init__(
        self, structure_id: str, id_allocator: IdAllocator | None = None
    ) -> None:
        super().__init__(structure_id=structure_id, id_allocator=id_allocator)
        self._nodes: dict[str, _QueueNode] = {}
        self._root: Optional[str] = None
        self._last_values: list[float] = []

    @property
    def kind(self) -> str:
        return "huffman"

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def apply_operation(self, op: str, payload: Mapping[str, object]) -> Timeline:
        if op == "build":
            values = payload.get("values")
            if values is None:
                raise ModelError("build requires values")
            if not isinstance(values, (list, tuple)):
                raise ModelError("values must be list/tuple")
            return self.build(list(values))
        if op == "delete_all":
            return self.delete_all()
        raise ModelError(f"Unsupported operation: {op}")

    # ------------------------------------------------------------------ #
    # Public ops
    # ------------------------------------------------------------------ #
    def build(self, values: List[object]) -> Timeline:
        timeline = Timeline()
        self._nodes.clear()
        self._root = None
        self._last_values = []
        if not values:
            timeline.add_step(
                AnimationStep(ops=[self._msg("Empty weights for Huffman build")])
            )
            timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
            return timeline

        heap: list[_QueueNode] = []
        normalized_values: list[float] = []
        for i, val in enumerate(values):
            if not isinstance(val, (int, float)):
                raise ModelError("Huffman weights must be numbers")
            weight = float(val)
            normalized_values.append(weight)
            node_id = self.allocate_node_id("node")
            node = _QueueNode(weight=weight, order=i, node_id=node_id)
            heapq.heappush(heap, node)
            self._nodes[node_id] = node
        self._last_values = normalized_values

        # 初始创建节点（按权值排序后分配 queue_index）
        initial_queue = sorted(heap)
        create_ops: list[AnimationOp] = [self._msg("Init Huffman queue")]
        for idx, node in enumerate(initial_queue):
            create_ops.append(self._create_node_op(node.node_id, node.weight, idx))
        timeline.add_step(AnimationStep(ops=create_ops, label="Init"))

        merge_order = len(initial_queue)
        step_idx = 0
        while len(heap) > 1:
            step_idx += 1
            n1 = heapq.heappop(heap)
            n2 = heapq.heappop(heap)
            highlight_ops = [
                self._msg(f"Merge step {step_idx}: pick {n1.weight} & {n2.weight}"),
                self._set_state(n1.node_id, "highlight"),
                self._set_state(n2.node_id, "highlight"),
            ]
            timeline.add_step(AnimationStep(ops=highlight_ops, label="Pick two"))

            parent_weight = n1.weight + n2.weight
            parent_id = self.allocate_node_id("node")
            parent_node = _QueueNode(
                weight=parent_weight,
                order=merge_order,
                node_id=parent_id,
                left=n1.node_id,
                right=n2.node_id,
            )
            merge_order += 1
            self._nodes[parent_id] = parent_node
            self._root = parent_id
            heapq.heappush(heap, parent_node)

            create_parent_ops = [
                self._create_node_op(parent_id, parent_weight, None),
                self._create_edge_op(parent_id, n1.node_id, "L"),
                self._create_edge_op(parent_id, n2.node_id, "R"),
            ]
            timeline.add_step(
                AnimationStep(ops=create_parent_ops, label="Create parent")
            )

            # 更新队列顺序（按权值排序后赋予 queue_index）
            sorted_queue = sorted(heap)
            reorder_ops = []
            for idx, node in enumerate(sorted_queue):
                reorder_ops.append(
                    self._set_label(node.node_id, node.weight, queue_index=idx)
                )
                reorder_ops.append(self._set_state(node.node_id, "normal"))
            reorder_ops.append(self._clear_msg())
            timeline.add_step(AnimationStep(ops=reorder_ops, label="Requeue"))

        if heap:
            root_node = heap[0]
            self._root = root_node.node_id
            timeline.add_step(
                AnimationStep(
                    ops=[
                        self._msg(f"Done: root weight={root_node.weight}"),
                        self._set_state(root_node.node_id, "active"),
                    ],
                    label="Complete",
                )
            )
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def delete_all(self) -> Timeline:
        timeline = Timeline()
        if not self._nodes:
            return timeline
        ops: list[AnimationOp] = [self._msg("Delete all Huffman nodes")]
        for node_id in list(self._nodes.keys()):
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=node_id,
                    data={"structure_id": self.structure_id},
                )
            )
        self._nodes.clear()
        self._root = None
        self._last_values = []
        timeline.add_step(AnimationStep(ops=ops, label="Delete all"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def export_state(self) -> Mapping[str, object]:
        """Export last build weights for persistence replay."""
        return {"values": list(self._last_values)}

    # ------------------------------------------------------------------ #
    # Op helpers
    # ------------------------------------------------------------------ #
    def _create_node_op(
        self, node_id: str, weight: float, queue_index: Optional[int]
    ) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=node_id,
            data={
                "structure_id": self.structure_id,
                "label": str(weight),
                "shape": "circle",
                "queue_index": queue_index,
            },
        )

    def _create_edge_op(self, parent: str, child: str, label: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_EDGE,
            target=self.edge_id("huff", parent, child),
            data={
                "structure_id": self.structure_id,
                "from": parent,
                "to": child,
                "label": label,
            },
        )

    def _set_state(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"structure_id": self.structure_id, "state": state},
        )

    def _set_label(
        self, target: str, weight: float, queue_index: Optional[int]
    ) -> AnimationOp:
        data: dict[str, object] = {
            "structure_id": self.structure_id,
            "text": str(weight),
            "label": str(weight),
        }
        if queue_index is not None:
            data["queue_index"] = queue_index
        return AnimationOp(op=OpCode.SET_LABEL, target=target, data=data)

    def _msg(self, text: str) -> AnimationOp:
        return AnimationOp(op=OpCode.SET_MESSAGE, target=None, data={"text": text})

    def _clear_msg(self) -> AnimationOp:
        return AnimationOp(op=OpCode.CLEAR_MESSAGE, target=None, data={})
