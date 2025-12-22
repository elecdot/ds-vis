from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from ds_vis.core.layout import LayoutEngine, LayoutStrategy
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class TreeLayoutEngine(LayoutEngine):
    """
    Minimal层次树布局（占位版）。

    设计目标：
    - 从结构 Ops（CREATE_NODE/CREATE_EDGE/DELETE_*）推断父子关系。
    - 以中序遍历为序号，水平等距；纵向按深度分层。
    - 仅注入 SET_POS，不处理旋转/重排动画，未来可替换为更精细算法。
    """

    spacing: float = 140.0
    level_spacing: float = 120.0
    start_x: float = 50.0
    start_y: float = 50.0
    strategy: LayoutStrategy = LayoutStrategy.TREE

    _nodes: Dict[str, List[str]] = field(default_factory=dict)
    _parents: Dict[str, Dict[str, Tuple[str, str]]] = field(default_factory=dict)
    _positions: Dict[str, Dict[str, Tuple[float, float]]] = field(default_factory=dict)
    _dirty_structures: set[str] = field(default_factory=set)

    def apply_layout(self, timeline: Timeline) -> Timeline:
        new_timeline = Timeline()
        for step in timeline.steps:
            new_step = AnimationStep(
                duration_ms=step.duration_ms, label=step.label, ops=list(step.ops)
            )
            self._apply_structural_ops(step)
            pos_ops = self._inject_positions()
            new_step.ops.extend(pos_ops)
            new_timeline.add_step(new_step)
        return new_timeline

    def reset(self) -> None:
        self._nodes.clear()
        self._parents.clear()
        self._positions.clear()
        self._dirty_structures.clear()

    def _apply_structural_ops(self, step: AnimationStep) -> None:
        for op in step.ops:
            sid = op.data.get("structure_id")
            if not sid:
                continue
            if op.op is OpCode.CREATE_NODE:
                self._nodes.setdefault(sid, []).append(op.target or "")
                self._dirty_structures.add(sid)
            elif op.op is OpCode.DELETE_NODE:
                nodes = self._nodes.get(sid, [])
                if op.target in nodes:
                    nodes.remove(op.target or "")
                parent_map = self._parents.get(sid, {})
                parent_map.pop(op.target or "", None)
                # 清理指向该节点的父关系
                for child_id_loop, (parent_id, _) in list(parent_map.items()):
                    if child_id_loop == op.target or parent_id == op.target:
                        parent_map.pop(child_id_loop, None)
                self._dirty_structures.add(sid)
            elif op.op is OpCode.CREATE_EDGE:
                parent: Optional[str] = op.data.get("from")
                edge_child: Optional[str] = op.data.get("to")
                direction: str = op.data.get("label") or ""
                if parent and edge_child:
                    self._parents.setdefault(sid, {})[edge_child] = (
                        parent,
                        direction,
                    )
                    self._dirty_structures.add(sid)
            elif op.op is OpCode.DELETE_EDGE:
                edge_child_del: Optional[str] = op.data.get("to")
                if edge_child_del:
                    parent_map = self._parents.get(sid, {})
                    parent_map.pop(edge_child_del, None)
                    self._dirty_structures.add(sid)

    def _inject_positions(self) -> List[AnimationOp]:
        ops: List[AnimationOp] = []
        for sid in list(self._dirty_structures):
            nodes = self._nodes.get(sid, [])
            parent_map = self._parents.get(sid, {})
            roots = [n for n in nodes if n and n not in parent_map]
            positions: Dict[str, Tuple[float, float]] = {}

            next_x = 0

            def dfs(node_id: Optional[str], depth: int) -> None:
                nonlocal next_x
                if not node_id:
                    return
                left: Optional[str] = self._child(parent_map, node_id, "L")
                right: Optional[str] = self._child(parent_map, node_id, "R")
                if left:
                    dfs(left, depth + 1)
                x = self.start_x + next_x * self.spacing
                y = self.start_y + depth * self.level_spacing
                positions[node_id] = (x, y)
                next_x += 1
                if right:
                    dfs(right, depth + 1)

            for root in roots:
                dfs(root, depth=0)

            prev_pos = self._positions.setdefault(sid, {})
            for node_id, pos in positions.items():
                if prev_pos.get(node_id) != pos:
                    ops.append(
                        AnimationOp(
                            op=OpCode.SET_POS,
                            target=node_id,
                            data={"x": pos[0], "y": pos[1]},
                        )
                    )
            self._positions[sid] = positions
        self._dirty_structures.clear()
        return ops

    @staticmethod
    def _child(
        parent_map: Mapping[str, Tuple[str, str]], parent_id: str, direction: str
    ) -> Optional[str]:
        for child_id, (parent, dir_label) in parent_map.items():
            if parent == parent_id and dir_label.upper().startswith(direction):
                return child_id
        return None
