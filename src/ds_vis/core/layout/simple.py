from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from ds_vis.core.layout import LayoutEngine, LayoutStrategy
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class SimpleLayoutEngine(LayoutEngine):
    """
    P0.4: linear layout with multi-structure stacking and dirty check.

    Assumptions: Node size is fixed; spacing is based on a single width/height;
    spacing/row_spacing can be replaced in the future to support variable sizes.
    Row alignment: left-aligned by default; other alignment strategies for trees/DAGs
    are reserved for future use but not yet enabled.
    Dirty check: Only inject SET_POS for nodes whose positions have changed;
    cascading displacements caused by deletion/insertion are captured.
    Stateful & sequential: relies on internal snapshots and assumes forward playback;
    seek/rewind requires state rebuild or replay.
    """

    spacing: float = 120.0
    row_spacing: float = 120.0
    start_x: float = 50.0
    start_y: float = 50.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    _structure_offsets: Dict[str, Tuple[float, float]] = field(
        default_factory=dict
    )
    _structure_nodes: Dict[str, List[str]] = field(default_factory=dict)
    _structure_rows: Dict[str, int] = field(default_factory=dict)
    _structure_positions: Dict[str, Dict[str, Tuple[float, float]]] = field(
        default_factory=dict
    )
    _row_order: List[str] = field(default_factory=list)
    _dirty_structures: set[str] = field(default_factory=set)
    strategy: LayoutStrategy = LayoutStrategy.LINEAR

    def set_offsets(self, offsets: Dict[str, tuple[float, float]]) -> None:
        self._structure_offsets = offsets

    def apply_layout(self, timeline: Timeline) -> Timeline:
        """
        Inject SET_POS ops for current nodes after each step, with per-structure
        row stacking and dirty check to avoid redundant SET_POS.
        """
        new_timeline = Timeline()

        for step in timeline.steps:
            new_step = AnimationStep(
                duration_ms=step.duration_ms,
                label=step.label,
                ops=list(step.ops),
            )

            self._apply_structural_ops(step)
            dirty_ops = self._inject_positions()
            new_step.ops.extend(dirty_ops)

            new_timeline.add_step(new_step)

        return new_timeline

    def reset(self) -> None:
        """Reset internal state (rows/positions) for rebuild/seek."""
        self._structure_nodes.clear()
        self._structure_rows.clear()
        self._structure_positions.clear()
        self._row_order.clear()
        self._dirty_structures.clear()
        self._structure_offsets.clear()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _apply_structural_ops(self, step: AnimationStep) -> None:
        for op in step.ops:
            structure_id = op.data.get("structure_id")
            node_id = op.target
            if op.op is OpCode.CREATE_NODE and structure_id and node_id:
                self._assign_row_if_absent(structure_id)
                nodes = self._structure_nodes.setdefault(structure_id, [])
                insert_idx = self._extract_index(op.data)
                if node_id in nodes:
                    nodes.remove(node_id)
                if insert_idx is None or insert_idx >= len(nodes):
                    nodes.append(node_id)
                else:
                    nodes.insert(insert_idx, node_id)
                self._dirty_structures.add(structure_id)
            elif op.op is OpCode.DELETE_NODE and structure_id and node_id:
                nodes = self._structure_nodes.get(structure_id, [])
                if node_id in nodes:
                    nodes.remove(node_id)
                self._dirty_structures.add(structure_id)
                if not nodes:
                    self._clear_structure(structure_id)

    def _inject_positions(self) -> List[AnimationOp]:
        ops: List[AnimationOp] = []
        for structure_id, nodes in self._structure_nodes.items():
            row_index = self._structure_rows[structure_id]
            offset_x, offset_y = self._structure_offsets.get(structure_id, (0.0, 0.0))
            y = self.start_y + offset_y + self.row_spacing * row_index
            pos_cache = self._structure_positions.setdefault(structure_id, {})
            force_dirty = structure_id in self._dirty_structures

            for idx, node_id in enumerate(nodes):
                x = self.start_x + offset_x + self.spacing * idx
                current = (x, y)
                if force_dirty or pos_cache.get(node_id) != current:
                    ops.append(
                        AnimationOp(
                            op=OpCode.SET_POS,
                            target=node_id,
                            data={"x": x, "y": y},
                        )
                    )
                pos_cache[node_id] = current
        self._dirty_structures.clear()
        return ops

    def _assign_row_if_absent(self, structure_id: str) -> None:
        if structure_id in self._structure_rows:
            return
        self._row_order.append(structure_id)
        self._structure_rows[structure_id] = len(self._row_order) - 1

    def _clear_structure(self, structure_id: str) -> None:
        self._structure_nodes.pop(structure_id, None)
        self._structure_positions.pop(structure_id, None)
        if structure_id in self._structure_rows:
            self._row_order = [sid for sid in self._row_order if sid != structure_id]
            # Re-pack rows to avoid unbounded vertical drift.
            self._structure_rows = {
                sid: idx for idx, sid in enumerate(self._row_order)
            }

    @staticmethod
    def _extract_index(data: Mapping[str, object]) -> Optional[int]:
        index_value = data.get("index")
        if isinstance(index_value, int):
            return max(index_value, 0)
        return None
