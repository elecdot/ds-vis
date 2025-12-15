from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Mapping, Optional

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
        raise ModelError(f"Unsupported operation: {op}")

    def create(self, values: Optional[Iterable[Any]] = None) -> Timeline:
        """
        Initialize or populate the list and emit CREATE_* ops.

        Even for an empty list we create a sentinel node so the skeleton
        test can observe a structural op.
        """
        self.values = list(values or [])
        ops = self._emit_create_ops()

        timeline = Timeline()
        timeline.add_step(AnimationStep(ops=ops))
        return timeline

    def delete_all(self) -> Timeline:
        """
        Emit DELETE_* ops for all tracked nodes/edges.
        """
        timeline = Timeline()
        if not self._node_ids:
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

        self._node_ids.clear()
        self.values = []
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
        prev_id = self._node_ids[index - 1] if index - 1 >= 0 else None
        next_id = self._node_ids[index] if index < len(self._node_ids) else None

        highlight_targets = [nid for nid in (prev_id, next_id) if nid is not None]
        timeline.add_step(
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target=nid,
                        data={
                            "structure_id": self.structure_id,
                            "state": "highlight",
                        },
                    )
                    for nid in highlight_targets
                ]
            )
        )

        new_node_id = self.allocate_node_id(prefix="node")
        structural_ops: List[AnimationOp] = []
        if prev_id and next_id:
            structural_ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self.edge_id("next", prev_id, next_id),
                    data={"structure_id": self.structure_id},
                )
            )

        structural_ops.append(
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target=new_node_id,
                data={
                    "structure_id": self.structure_id,
                    "kind": "list_node",
                    "label": str(value),
                    "index": index,
                },
            )
        )
        if prev_id:
            structural_ops.append(
                AnimationOp(
                    op=OpCode.CREATE_EDGE,
                    target=self.edge_id("next", prev_id, new_node_id),
                    data={
                        "structure_id": self.structure_id,
                        "from": prev_id,
                        "to": new_node_id,
                        "directed": True,
                        "label": "next",
                    },
                )
            )
        if next_id:
            structural_ops.append(
                AnimationOp(
                    op=OpCode.CREATE_EDGE,
                    target=self.edge_id("next", new_node_id, next_id),
                    data={
                        "structure_id": self.structure_id,
                        "from": new_node_id,
                        "to": next_id,
                        "directed": True,
                        "label": "next",
                    },
                )
            )

        self._node_ids.insert(index, new_node_id)
        self.values.insert(index, value)
        timeline.add_step(AnimationStep(ops=structural_ops))

        restore_targets = highlight_targets + [new_node_id]
        timeline.add_step(
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target=nid,
                        data={
                            "structure_id": self.structure_id,
                            "state": "normal",
                        },
                    )
                    for nid in restore_targets
                ]
            )
        )
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
    def _emit_create_ops(self) -> List[AnimationOp]:
        ops: List[AnimationOp] = []

        if not self.values:
            node_id = self.allocate_node_id(prefix="sentinel")
            self._node_ids = [node_id]
            ops.append(
                AnimationOp(
                    op=OpCode.CREATE_NODE,
                    target=node_id,
                    data={
                        "structure_id": self.structure_id,
                        "kind": "list_sentinel",
                        "label": "head",
                    },
                )
            )
            return ops

        self._node_ids = []
        prev_node_id: Optional[str] = None
        for value in self.values:
            node_id = self.allocate_node_id(prefix="node")
            self._node_ids.append(node_id)
            ops.append(
                AnimationOp(
                    op=OpCode.CREATE_NODE,
                    target=node_id,
                    data={
                        "structure_id": self.structure_id,
                        "kind": "list_node",
                        "label": str(value),
                    },
                )
                )

            if prev_node_id is not None:
                ops.append(
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target=self.edge_id("next", prev_node_id, node_id),
                        data={
                            "structure_id": self.structure_id,
                            "from": prev_node_id,
                            "to": node_id,
                            "directed": True,
                            "label": "next",
                        },
                    )
                )
            prev_node_id = node_id

        return ops
