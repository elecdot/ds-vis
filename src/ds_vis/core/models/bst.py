from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class _BstNode:
    key: Any
    left: Optional[str] = None
    right: Optional[str] = None
    parent: Optional[str] = None


@dataclass
class BstModel(BaseModel):
    """
    Minimal BST-like树模型骨架，支持 create / insert。

    设计目标：
    - 作为后续 BST/AVL/Huffman 的共用起点，优先保证可解释的微步骤与可扩展性。
    - 不包含布局信息；SET_POS 由 Layout 注入。
    - ID/边 key 稳定，便于 Renderer/UI 复用。
    """

    _root_id: Optional[str] = None
    _nodes: Dict[str, _BstNode] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        return "bst"

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def apply_operation(self, op: str, payload: Mapping[str, Any]) -> Timeline:
        if op == "create":
            return self.create(payload.get("values"))
        if op == "insert":
            return self.insert(value=payload.get("value"))
        if op == "search":
            return self.search(value=payload.get("value"))
        if op == "delete_value":
            return self.delete_value(value=payload.get("value"))
        if op == "delete_all":
            return self.delete_all()
        raise ModelError(f"Unsupported operation: {op}")

    # ------------------------------------------------------------------ #
    # Public ops
    # ------------------------------------------------------------------ #
    def create(self, values: Optional[Mapping[str, Any]] = None) -> Timeline:
        """
        初始化或重建树结构；values（可选）按插入顺序逐个 insert。
        """
        timeline = Timeline()
        # 重建前先清空
        delete_tl = self.delete_all()
        for step in delete_tl.steps:
            timeline.add_step(step)

        values_iter: list[Any] = list(values or [])
        for value in values_iter:
            ins_tl = self.insert(value)
            for step in ins_tl.steps:
                timeline.add_step(step)
        # 空树也返回空 timeline（无 sentinel）
        return timeline

    def insert(self, value: Any) -> Timeline:
        if value is None:
            raise ModelError("insert requires value")

        timeline = Timeline()
        if self._root_id is None:
            node_id = self._create_node(value, parent=None)
            timeline.add_step(
                AnimationStep(
                    ops=[
                        self._msg(f"Insert {value} as root"),
                        self._op_create_node(node_id, value),
                    ],
                    label="Create root",
                )
            )
            timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
            return timeline

        # 遍历寻找插入位置
        traversal_steps: list[AnimationStep] = []
        edge_traversed: list[str] = []
        path = []
        parent_id = self._root_id
        direction = "left"
        while parent_id:
            path.append(parent_id)
            parent_node = self._nodes[parent_id]
            traversal_steps.append(
                AnimationStep(
                    label="Compare",
                    ops=[
                        self._msg(f"Compare {value} with {parent_node.key}"),
                        self._set_state(parent_id, "highlight"),
                    ],
                )
            )
            if value < parent_node.key:
                direction = "left"
                if parent_node.left:
                    traversal_steps.append(
                        AnimationStep(
                            label="Move left",
                            ops=[
                                self._set_state(
                                    self.edge_id("left", parent_id, parent_node.left),
                                    "secondary",
                                )
                            ],
                        )
                    )
                    edge_traversed.append(
                        self.edge_id("left", parent_id, parent_node.left)
                    )
                    parent_id = parent_node.left
                    continue
                break
            else:
                direction = "right"
                if parent_node.right:
                    traversal_steps.append(
                        AnimationStep(
                            label="Move right",
                            ops=[
                                self._set_state(
                                    self.edge_id("right", parent_id, parent_node.right),
                                    "secondary",
                                )
                            ],
                        )
                    )
                    edge_traversed.append(
                        self.edge_id("right", parent_id, parent_node.right)
                    )
                    parent_id = parent_node.right
                    continue
                break

        for step in traversal_steps:
            timeline.add_step(step)

        new_id = self._create_node(value, parent=parent_id, direction=direction)
        connect_ops = [
            self._msg(f"Insert {value} to {direction} of {parent_id}"),
            self._set_state(parent_id, "highlight"),
            self._op_create_node(new_id, value),
            self._op_create_edge(parent_id, new_id, direction),
        ]
        timeline.add_step(AnimationStep(ops=connect_ops))

        # 收尾：恢复状态、清理消息
        restore_ops = [self._clear_msg()]
        for node_id in path:
            restore_ops.append(self._set_state(node_id, "normal"))
        for edge_id in edge_traversed:
            restore_ops.append(self._set_state(edge_id, "normal"))
        timeline.add_step(AnimationStep(ops=restore_ops))
        return timeline

    def search(self, value: Any) -> Timeline:
        if value is None:
            raise ModelError("search requires value")
        timeline = Timeline()
        if self._root_id is None:
            timeline.add_step(
                AnimationStep(ops=[self._msg("Tree is empty"), self._clear_msg()])
            )
            return timeline

        current = self._root_id
        visited: list[str] = []
        traversed_edges: list[str] = []
        while current:
            node = self._nodes[current]
            compare_ops = [
                self._msg(f"Compare {value} with {node.key}"),
                self._set_state(current, "highlight"),
            ]
            timeline.add_step(AnimationStep(ops=compare_ops, label="Compare"))

            if value == node.key:
                timeline.add_step(
                    AnimationStep(
                        ops=[
                            self._msg(f"Found {value}"),
                            self._set_state(current, "highlight"),
                        ],
                        label="Found",
                    )
                )
                restore_ops = [self._clear_msg()]
                for nid in visited + [current]:
                    restore_ops.append(self._set_state(nid, "normal"))
                for edge_id in traversed_edges:
                    restore_ops.append(self._set_state(edge_id, "normal"))
                timeline.add_step(AnimationStep(ops=restore_ops, label="Restore"))
                return timeline

            direction = "left" if value < node.key else "right"
            edge_target = node.left if direction == "left" else node.right
            visited.append(current)
            if edge_target:
                edge_id = self.edge_id(direction, current, edge_target)
                traversed_edges.append(edge_id)
                timeline.add_step(
                    AnimationStep(
                        ops=[
                            self._set_state(
                                edge_id,
                                "secondary",
                            )
                        ],
                        label="Move edge",
                    )
                )
            if edge_target is None:
                timeline.add_step(
                    AnimationStep(
                        ops=[
                            self._msg(f"{value} not found"),
                            self._set_state(current, "secondary"),
                        ],
                        label="Miss",
                    )
                )
                restore_ops = [self._clear_msg()]
                for nid in visited + [current]:
                    restore_ops.append(self._set_state(nid, "normal"))
                for edge_id in traversed_edges:
                    restore_ops.append(self._set_state(edge_id, "normal"))
                timeline.add_step(AnimationStep(ops=restore_ops, label="Restore"))
                return timeline
            current = edge_target

        return timeline

    def delete_value(self, value: Any) -> Timeline:
        if value is None:
            raise ModelError("delete_value requires value")
        timeline = Timeline()
        if self._root_id is None:
            return timeline

        # locate node
        target_id, search_steps = self._find_node(value)
        for step in search_steps:
            timeline.add_step(step)
        if target_id is None:
            return timeline

        ops: list[AnimationOp] = []
        ops.append(self._msg(f"Delete {value}"))
        ops.append(self._set_state(target_id, "highlight"))

        node = self._nodes[target_id]
        if node.left is None and node.right is None:
            ops.extend(self._delete_leaf_ops(target_id))
        elif node.left is None or node.right is None:
            ops.extend(self._delete_single_child_ops(target_id))
        else:
            # two children: use successor
            succ_id, succ_ops = self._find_successor_ops(node.right)
            for step in succ_ops:
                timeline.add_step(step)
            if succ_id:
                succ_node = self._nodes[succ_id]
                ops.append(self._set_state(succ_id, "highlight"))
                ops.append(self._set_label(target_id, succ_node.key))
                self._nodes[target_id].key = succ_node.key
                ops.extend(self._delete_single_child_ops(succ_id))
        ops.append(self._clear_msg())
        timeline.add_step(AnimationStep(ops=ops, label="Delete"))
        # restore states
        timeline.add_step(
            AnimationStep(
                ops=[self._set_state(nid, "normal") for nid in self._nodes.keys()],
                label="Restore",
            )
        )
        return timeline

    def delete_all(self) -> Timeline:
        timeline = Timeline()
        if not self._nodes:
            return timeline

        ops: list[AnimationOp] = []
        # delete edges first
        for node_id, node in list(self._nodes.items()):
            if node.left:
                ops.append(self._op_delete_edge(node_id, node.left))
            if node.right:
                ops.append(self._op_delete_edge(node_id, node.right))
        for node_id in list(self._nodes.keys()):
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=node_id,
                    data={"structure_id": self.structure_id},
                )
            )
        self._nodes.clear()
        self._root_id = None
        timeline.add_step(AnimationStep(ops=ops))
        return timeline

    def export_state(self) -> Mapping[str, object]:
        """Export current BST keys in pre-order for persistence replay."""
        return {"values": list(self._iter_preorder(self._root_id))}

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_node(
        self, value: Any, parent: Optional[str], direction: str | None = None
    ) -> str:
        node_id = self.allocate_node_id("node")
        self._nodes[node_id] = _BstNode(key=value, parent=parent)
        if parent and direction:
            parent_node = self._nodes[parent]
            if direction == "left":
                parent_node.left = node_id
            else:
                parent_node.right = node_id
        if self._root_id is None:
            self._root_id = node_id
        return node_id

    def _op_create_node(self, node_id: str, value: Any) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=node_id,
            data={
                "structure_id": self.structure_id,
                "label": str(value),
            },
        )

    def _op_create_edge(
        self, parent_id: str, child_id: str, direction: str
    ) -> AnimationOp:
        label = "L" if direction == "left" else "R"
        return AnimationOp(
            op=OpCode.CREATE_EDGE,
            target=self.edge_id(direction, parent_id, child_id),
            data={
                "structure_id": self.structure_id,
                "from": parent_id,
                "to": child_id,
                "label": label,
            },
        )

    def _op_delete_edge(self, parent_id: str, child_id: str) -> AnimationOp:
        direction = "left" if self._nodes[parent_id].left == child_id else "right"
        return AnimationOp(
            op=OpCode.DELETE_EDGE,
            target=self.edge_id(direction, parent_id, child_id),
            data={"structure_id": self.structure_id},
        )

    def _set_state(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"state": state, "structure_id": self.structure_id},
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

    def _iter_preorder(self, node_id: Optional[str]) -> Iterable[Any]:
        if node_id is None:
            return []
        node = self._nodes[node_id]
        yield node.key
        if node.left:
            yield from self._iter_preorder(node.left)
        if node.right:
            yield from self._iter_preorder(node.right)

    def _find_node(self, value: Any) -> tuple[Optional[str], list[AnimationStep]]:
        steps: list[AnimationStep] = []
        current = self._root_id
        visited: list[str] = []
        while current:
            node = self._nodes[current]
            steps.append(
                AnimationStep(
                    ops=[self._set_state(current, "secondary")],
                    label="Traverse",
                )
            )
            if value == node.key:
                return current, steps
            visited.append(current)
            if value < node.key:
                current = node.left
            else:
                current = node.right
        # not found, restore visited
        steps.append(
            AnimationStep(
                ops=[self._set_state(nid, "normal") for nid in visited],
                label="Restore",
            )
        )
        return None, steps

    def _delete_leaf_ops(
        self, node_id: str, reroute_parent: bool = True, delete_parent_edge: bool = True
    ) -> list[AnimationOp]:
        ops: list[AnimationOp] = []
        parent_id = self._nodes[node_id].parent
        if delete_parent_edge and parent_id:
            ops.append(self._op_delete_edge(parent_id, node_id))
        ops.append(
            AnimationOp(
                op=OpCode.DELETE_NODE,
                target=node_id,
                data={"structure_id": self.structure_id},
            )
        )
        self._detach(node_id)
        return ops

    def _delete_single_child_ops(self, node_id: str) -> list[AnimationOp]:
        ops: list[AnimationOp] = []
        node = self._nodes[node_id]
        child_id = node.left or node.right
        parent_id = node.parent
        if parent_id:
            ops.append(self._op_delete_edge(parent_id, node_id))

        if child_id:
            ops.append(self._op_delete_edge(node_id, child_id))
            if parent_id:
                ops.append(
                    self._op_create_edge(
                        parent_id, child_id, self._dir(parent_id, node_id)
                    )
                )
            self._reparent(child_id, parent_id)
            if parent_id is None:
                self._root_id = child_id
                self._nodes[child_id].parent = None
        ops.append(
            AnimationOp(
                op=OpCode.DELETE_NODE,
                target=node_id,
                data={"structure_id": self.structure_id},
            )
        )
        self._detach(node_id, new_root=self._root_id)
        return ops

    def _find_successor_ops(
        self, start_id: str
    ) -> tuple[Optional[str], list[AnimationStep]]:
        steps: list[AnimationStep] = []
        current = start_id
        while True:
            node = self._nodes[current]
            steps.append(
                AnimationStep(
                    ops=[self._set_state(current, "secondary")], label="Succ traverse"
                )
            )
            if node.left:
                current = node.left
                continue
            return current, steps

    def _detach(self, node_id: str, new_root: Optional[str] = None) -> None:
        node = self._nodes.pop(node_id, None)
        if not node:
            return
        if node.parent:
            parent = self._nodes[node.parent]
            if parent.left == node_id:
                parent.left = None
            if parent.right == node_id:
                parent.right = None
        if self._root_id == node_id:
            self._root_id = new_root

    def _reparent(self, node_id: str, new_parent: Optional[str]) -> None:
        node = self._nodes[node_id]
        node.parent = new_parent
        if new_parent:
            parent = self._nodes[new_parent]
            if node.key < parent.key:
                parent.left = node_id
            else:
                parent.right = node_id

    def _dir(self, parent_id: str, child_id: str) -> str:
        parent = self._nodes[parent_id]
        if parent.left == child_id:
            return "left"
        return "right"
