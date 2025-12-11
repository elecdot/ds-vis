from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class SimpleLayoutEngine:
    """
    Phase 1: naive linear layout.

    - Places nodes of the same structure on a horizontal line.
    - Injects SET_POS ops in the same step as each CREATE_NODE.
    - Never mutates structural ops.
    """

    spacing: float = 120.0
    start_x: float = 50.0
    start_y: float = 50.0
    _structure_nodes: Dict[str, List[str]] = field(default_factory=dict)

    def apply_layout(self, timeline: Timeline) -> Timeline:
        """
        Inject SET_POS ops for every CREATE_NODE in the given timeline.
        """
        new_timeline = Timeline()

        for step in timeline.steps:
            new_step = AnimationStep(
                duration_ms=step.duration_ms,
                label=step.label,
                ops=list(step.ops),
            )

            for op in step.ops:
                if op.op is not OpCode.CREATE_NODE:
                    continue

                structure_id = op.data.get("structure_id")
                node_id = op.target
                if not structure_id or not node_id:
                    continue  # Missing metadata; skip layout for this op.

                nodes = self._structure_nodes.setdefault(structure_id, [])
                if node_id not in nodes:
                    nodes.append(node_id)

                x = self.start_x + self.spacing * (len(nodes) - 1)
                y = self.start_y

                new_step.ops.append(
                    AnimationOp(
                        op=OpCode.SET_POS,
                        target=node_id,
                        data={"x": x, "y": y},
                    )
                )

            new_timeline.add_step(new_step)

        return new_timeline
