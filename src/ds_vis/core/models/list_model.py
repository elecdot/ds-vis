from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class ListModel(BaseModel):
    """
    Minimal list model used by the walking skeleton.

    Responsibilities:
      - store logical values,
      - emit structural AnimationOps (no coordinates).

    P0.3: IDs are monotonic and never reused within the same structure instance.
    """

    values: List[Any] = field(default_factory=list)
    _node_ids: List[str] = field(default_factory=list)
    _sentinel_id: Optional[str] = None

    @property
    def kind(self) -> str:
        return "list"

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

    def create(self, values: Optional[Iterable[Any]] = None) -> Timeline:
        """
        Initialize or populate the list and emit CREATE_* ops.

        Even for an empty list we create a sentinel node so the skeleton
        test can observe a structural op.
        """
        # NOTE: sentinel exists only for visualization of empty list (display-only).
        self.values = list(values or [])
        self._sentinel_id = None
        ops = self._emit_create_ops()

        timeline = Timeline()
        timeline.add_step(AnimationStep(ops=ops))
        return timeline

    def delete_all(self) -> Timeline:
        """
        Emit DELETE_* ops for all tracked nodes/edges.
        """
        timeline = Timeline()
        if not self._node_ids and not self._sentinel_id:
            return timeline

        ops: List[AnimationOp] = []
        # Delete edges first.
        for src, dst in zip(self._node_ids, self._node_ids[1:]):
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self.edge_id("next", src, dst),
                    data={"structure_id": self.structure_id},
                )
            )

        for node_id in reversed(self._node_ids):
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=node_id,
                    data={"structure_id": self.structure_id},
                )
            )

        if self._sentinel_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_NODE,
                    target=self._sentinel_id,
                    data={"structure_id": self.structure_id},
                )
            )

        self._node_ids.clear()
        self.values = []
        self._sentinel_id = None
        timeline.add_step(AnimationStep(ops=ops))
        return timeline

    def delete_index(self, index: int) -> Timeline:
        """
        Delete a node by logical position, rewiring adjacent edges.
        """
        timeline = Timeline()
        if index < 0 or index >= len(self._node_ids):
            raise ModelError("delete_index out of range")

        ops: List[AnimationOp] = []
        target_id = self._node_ids[index]
        prev_id = self._node_ids[index - 1] if index - 1 >= 0 else None
        next_id = self._node_ids[index + 1] if index + 1 < len(self._node_ids) else None

        if prev_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self.edge_id("next", prev_id, target_id),
                    data={"structure_id": self.structure_id},
                )
            )
        if next_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self.edge_id("next", target_id, next_id),
                    data={"structure_id": self.structure_id},
                )
            )

        ops.append(
            AnimationOp(
                op=OpCode.DELETE_NODE,
                target=target_id,
                data={"structure_id": self.structure_id},
            )
        )

        if prev_id and next_id:
            ops.append(
                AnimationOp(
                    op=OpCode.CREATE_EDGE,
                    target=self.edge_id("next", prev_id, next_id),
                    data={
                        "structure_id": self.structure_id,
                        "from": prev_id,
                        "to": next_id,
                        "directed": True,
                        "label": "next",
                    },
                )
            )

        del self._node_ids[index]
        if index < len(self.values):
            del self.values[index]

        timeline.add_step(AnimationStep(ops=ops))
        return timeline

    def insert(self, index: int, value: Any) -> Timeline:
        """
        Insert a value at the given logical position with L2 micro-steps:
        Highlight -> structural move -> restore visuals.
        """
        if index < 0 or index > len(self._node_ids):
            raise ModelError("insert index out of range")

        timeline = Timeline()
        if self._sentinel_id:
            remove_sentinel = AnimationOp(
                op=OpCode.DELETE_NODE,
                target=self._sentinel_id,
                data={"structure_id": self.structure_id},
            )
            timeline.add_step(
                AnimationStep(ops=[remove_sentinel], label="Remove empty")
            )
            self._sentinel_id = None

        prev_id = self._node_ids[index - 1] if index - 1 >= 0 else None
        next_id = self._node_ids[index] if index < len(self._node_ids) else None

        for node_id in self._emit_traversal_nodes(prev_id):
            self._add_state_step(
                timeline, [node_id], "highlight", "Traverse node"
            )
            self._add_state_step(
                timeline, [node_id], "normal", "Traverse reset"
            )

        highlight_targets = [nid for nid in (prev_id, next_id) if nid is not None]
        self._add_state_step(
            timeline, highlight_targets, "highlight", "Highlight neighbors"
        )

        new_node_id = self.allocate_node_id(prefix="node")
        edge_highlight_ops = self._emit_edge_state_between(
            prev_id, next_id, "highlight"
        )
        self._add_ops_step(timeline, edge_highlight_ops, "Highlight link")

        delete_ops = self._emit_delete_edge_between(prev_id, next_id)
        self._add_ops_step(timeline, delete_ops, "Remove old link")

        node_ops = self._emit_create_node_with_state(new_node_id, value, index)
        self._add_ops_step(timeline, node_ops, "Create new node")

        new_edge_ids = self._emit_new_edge_ids(prev_id, new_node_id, next_id)
        rewire_ops = self._emit_rewire_edges(prev_id, new_node_id, next_id)
        rewire_ops.extend(self._emit_edge_state_ops(new_edge_ids, "highlight"))
        self._add_ops_step(timeline, rewire_ops, "Rewire links")

        self._node_ids.insert(index, new_node_id)
        self.values.insert(index, value)

        restore_targets = list(
            dict.fromkeys(highlight_targets + [new_node_id] + new_edge_ids)
        )
        self._add_state_step(timeline, restore_targets, "normal", "Restore state")
        return timeline

    def search(
        self, *, value: Any | None = None, index: int | None = None
    ) -> Timeline:
        if value is None and index is None:
            raise ModelError("search requires value or index")
        if index is not None and (index < 0 or index >= len(self._node_ids)):
            raise ModelError("search index out of range")

        timeline = Timeline()
        target_index: Optional[int] = None
        for idx, node_id in enumerate(self._node_ids):
            match_index = index is not None and idx == index
            match_value = (
                value is not None
                and idx < len(self.values)
                and self.values[idx] == value
            )
            self._add_state_step(timeline, [node_id], "highlight", "Search visit")
            if match_index or match_value:
                target_index = idx
                break
            self._add_state_step(timeline, [node_id], "normal", "Search reset")

        if target_index is None:
            self._add_message_step(timeline, "Search not found", "Search result")
            return timeline

        target_id = self._node_ids[target_index]
        self._add_message_step(
            timeline, f"Found at index {target_index}", "Search result"
        )
        self._add_state_step(timeline, [target_id], "highlight", "Search highlight")
        self._add_state_step(timeline, [target_id], "normal", "Search restore")
        return timeline

    def update(
        self,
        *,
        new_value: Any,
        index: int | None = None,
        value: Any | None = None,
    ) -> Timeline:
        if new_value is None:
            raise ModelError("update requires new_value")
        if index is None and value is None:
            raise ModelError("update requires value or index")
        if index is not None and (index < 0 or index >= len(self._node_ids)):
            raise ModelError("update index out of range")

        target_index: Optional[int] = None
        if index is not None:
            target_index = index
        else:
            for idx, current in enumerate(self.values):
                if current == value:
                    target_index = idx
                    break
        if target_index is None:
            raise ModelError("update target not found")

        timeline = Timeline()
        for idx, node_id in enumerate(self._node_ids):
            self._add_state_step(timeline, [node_id], "highlight", "Update visit")
            if idx == target_index:
                break
            self._add_state_step(timeline, [node_id], "normal", "Update reset")

        target_id = self._node_ids[target_index]
        self.values[target_index] = new_value
        ops = [
            AnimationOp(
                op=OpCode.SET_LABEL,
                target=target_id,
                data={"structure_id": self.structure_id, "text": str(new_value)},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target=target_id,
                data={"structure_id": self.structure_id, "state": "highlight"},
            ),
        ]
        self._add_ops_step(timeline, ops, "Update value")
        self._add_state_step(timeline, [target_id], "normal", "Update restore")
        return timeline

    def recreate(self, values: Optional[Iterable[Any]] = None) -> Timeline:
        """
        Delete current visuals and recreate with new values.

        Node IDs remain monotonic across recreations; deleted IDs are not reused.
        """
        timeline = Timeline()
        delete_timeline = self.delete_all()
        for step in delete_timeline.steps:
            timeline.add_step(step)

        create_timeline = self.create(values)
        for step in create_timeline.steps:
            timeline.add_step(step)
        return timeline

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _add_ops_step(
        self, timeline: Timeline, ops: List[AnimationOp], label: Optional[str] = None
    ) -> None:
        if ops:
            timeline.add_step(AnimationStep(ops=ops, label=label))

    def _add_state_step(
        self,
        timeline: Timeline,
        targets: List[str],
        state: str,
        label: Optional[str] = None,
    ) -> None:
        if not targets:
            return
        ops = [self._build_set_state_op(target, state) for target in targets]
        timeline.add_step(AnimationStep(ops=ops, label=label))

    def _add_message_step(
        self, timeline: Timeline, message: str, label: Optional[str] = None
    ) -> None:
        timeline.add_step(
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.SET_MESSAGE,
                        target=None,
                        data={"text": message},
                    )
                ],
                label=label,
            )
        )

    def _build_set_state_op(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"structure_id": self.structure_id, "state": state},
        )

    def _emit_edge_state_ops(
        self, edge_ids: List[str], state: str
    ) -> List[AnimationOp]:
        return [self._build_set_state_op(edge_id, state) for edge_id in edge_ids]

    def _emit_edge_state_between(
        self, prev_id: Optional[str], next_id: Optional[str], state: str
    ) -> List[AnimationOp]:
        if not (prev_id and next_id):
            return []
        return self._emit_edge_state_ops(
            [self.edge_id("next", prev_id, next_id)], state
        )

    def _emit_new_edge_ids(
        self,
        prev_id: Optional[str],
        new_id: str,
        next_id: Optional[str],
    ) -> List[str]:
        edge_ids: List[str] = []
        if prev_id:
            edge_ids.append(self.edge_id("next", prev_id, new_id))
        if next_id:
            edge_ids.append(self.edge_id("next", new_id, next_id))
        return edge_ids

    def _emit_traversal_nodes(self, stop_at: Optional[str]) -> List[str]:
        if stop_at is None:
            return []
        if stop_at not in self._node_ids:
            return []
        stop_index = self._node_ids.index(stop_at)
        return list(self._node_ids[: stop_index + 1])

    def _emit_delete_edge_between(
        self, prev_id: Optional[str], next_id: Optional[str]
    ) -> List[AnimationOp]:
        if not (prev_id and next_id):
            return []
        return [
            AnimationOp(
                op=OpCode.DELETE_EDGE,
                target=self.edge_id("next", prev_id, next_id),
                data={"structure_id": self.structure_id},
            )
        ]

    def _emit_create_node_with_state(
        self, node_id: str, value: Any, index: int
    ) -> List[AnimationOp]:
        return [
            self._build_create_node_op(
                node_id=node_id,
                kind="list_node",
                label=str(value),
                index=index,
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target=node_id,
                data={"structure_id": self.structure_id, "state": "highlight"},
            ),
        ]

    def _emit_rewire_edges(
        self,
        prev_id: Optional[str],
        new_id: str,
        next_id: Optional[str],
    ) -> List[AnimationOp]:
        ops: List[AnimationOp] = []
        if prev_id:
            ops.append(self._build_create_edge_op(prev_id, new_id, "next"))
        if next_id:
            ops.append(self._build_create_edge_op(new_id, next_id, "next"))
        return ops

    def _build_create_node_op(
        self,
        node_id: str,
        kind: str,
        label: str,
        index: Optional[int] = None,
    ) -> AnimationOp:
        data: Dict[str, Any] = {
            "structure_id": self.structure_id,
            "kind": kind,
            "label": label,
        }
        if index is not None:
            data["index"] = index
        return AnimationOp(op=OpCode.CREATE_NODE, target=node_id, data=data)

    def _build_create_edge_op(
        self, src: str, dst: str, label: str
    ) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_EDGE,
            target=self.edge_id(label, src, dst),
            data={
                "structure_id": self.structure_id,
                "from": src,
                "to": dst,
                "directed": True,
                "label": label,
            },
        )

    def _emit_create_ops(self) -> List[AnimationOp]:
        ops: List[AnimationOp] = []
        if not self.values:
            node_id = self.allocate_node_id(prefix="sentinel")
            self._node_ids = []
            self._sentinel_id = node_id
            ops.append(
                self._build_create_node_op(
                    node_id=node_id,
                    kind="list_sentinel",
                    label="head",
                )
            )
            return ops

        self._node_ids = []
        prev_node_id: Optional[str] = None
        for value in self.values:
            node_id = self.allocate_node_id(prefix="node")
            self._node_ids.append(node_id)
            ops.append(
                self._build_create_node_op(
                    node_id=node_id,
                    kind="list_node",
                    label=str(value),
                )
            )

            if prev_node_id is not None:
                ops.append(self._build_create_edge_op(prev_node_id, node_id, "next"))
            prev_node_id = node_id

        return ops
