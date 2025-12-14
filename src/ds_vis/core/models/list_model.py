from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class ListModel:
    """
    Minimal list model used by the walking skeleton.

    Responsibilities:
      - store logical values,
      - emit structural AnimationOps (no coordinates).

    P0.3: IDs are monotonic and never reused within the same structure instance.
    """

    structure_id: str
    values: List[Any] = field(default_factory=list)
    _node_ids: List[str] = field(default_factory=list)
    _next_node_id: int = 0

    @property
    def kind(self) -> str:
        return "list"

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
                    target=self._edge_id(src, dst),
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
            return timeline  # Nothing to delete; caller should have validated.

        ops: List[AnimationOp] = []
        target_id = self._node_ids[index]
        prev_id = self._node_ids[index - 1] if index - 1 >= 0 else None
        next_id = self._node_ids[index + 1] if index + 1 < len(self._node_ids) else None

        if prev_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self._edge_id(prev_id, target_id),
                    data={"structure_id": self.structure_id},
                )
            )
        if next_id:
            ops.append(
                AnimationOp(
                    op=OpCode.DELETE_EDGE,
                    target=self._edge_id(target_id, next_id),
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
                    target=self._edge_id(prev_id, next_id),
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
            node_id = self._allocate_node_id(prefix="sentinel")
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
            node_id = self._allocate_node_id(prefix="node")
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
                        target=self._edge_id(prev_node_id, node_id),
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

    def _allocate_node_id(self, prefix: str) -> str:
        node_id = f"{self.structure_id}_{prefix}_{self._next_node_id}"
        self._next_node_id += 1
        return node_id

    def _edge_id(self, src: str, dst: str) -> str:
        return f"{self.structure_id}|next|{src}->{dst}"
