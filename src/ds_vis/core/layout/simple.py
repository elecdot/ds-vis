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
        Inject SET_POS ops for current nodes after each step, refreshing when
        nodes are created or deleted.
        """
        new_timeline = Timeline()

        for step in timeline.steps:
            new_step = AnimationStep(
                duration_ms=step.duration_ms,
                label=step.label,
                ops=list(step.ops),
            )

            # Update snapshot based on structural ops in this step.
            for op in step.ops:
                structure_id = op.data.get("structure_id")
                node_id = op.target
                if op.op is OpCode.CREATE_NODE and structure_id and node_id:
                    nodes = self._structure_nodes.setdefault(structure_id, [])
                    if node_id not in nodes:
                        nodes.append(node_id)
                elif op.op is OpCode.DELETE_NODE and structure_id and node_id:
                    nodes = self._structure_nodes.get(structure_id, [])
                    if node_id in nodes:
                        nodes.remove(node_id)
                    if not nodes and structure_id in self._structure_nodes:
                        self._structure_nodes.pop(structure_id, None)

            # Inject positions for the current snapshot (deterministic order).
            for structure_id, nodes in self._structure_nodes.items():
                for idx, node_id in enumerate(nodes):
                    x = self.start_x + self.spacing * idx
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
