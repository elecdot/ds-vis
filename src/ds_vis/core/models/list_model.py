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
    """

    structure_id: str
    values: List[Any] = field(default_factory=list)

    def create(self, values: Optional[Iterable[Any]] = None) -> Timeline:
        """
        Initialize the list with optional values and emit CREATE_NODE ops.

        Even for an empty list we create a sentinel node so the skeleton
        test can observe a structural op.
        """
        # TODO(phase1->2): add insert/delete/update operations and richer timelines.
        self.values = list(values or [])

        timeline = Timeline()
        ops: List[AnimationOp] = []

        if not self.values:
            ops.append(
                AnimationOp(
                    op=OpCode.CREATE_NODE,
                    target=f"{self.structure_id}_sentinel",
                    data={
                        "structure_id": self.structure_id,
                        "kind": "list_sentinel",
                        "label": "head",
                    },
                )
            )
        else:
            prev_node_id: Optional[str] = None
            for idx, value in enumerate(self.values):
                node_id = f"{self.structure_id}_node_{idx}"
                ops.append(
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target=node_id,
                        data={
                            "structure_id": self.structure_id,
                            "kind": "list_node",
                            "label": str(value),
                            "meta": {"index": idx},
                        },
                    )
                )

                if prev_node_id is not None:
                    edge_id = f"{prev_node_id}_to_{node_id}"
                    ops.append(
                        AnimationOp(
                            op=OpCode.CREATE_EDGE,
                            target=edge_id,
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

        timeline.add_step(AnimationStep(ops=ops))
        return timeline
