from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Tuple

from ds_vis.core.layout import LayoutEngine, LayoutStrategy
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class GitLayoutEngine(LayoutEngine):
    """
    Simplified Git DAG layout.

    目标：
    - 按 commit 创建顺序纵向排布（单列 lane 占位）。
    - 处理 label 的 attach_to：HEAD/branch label 总是锚定到目标 commit 之上并保持堆叠。
    - 仅注入 SET_POS，不修改结构 Ops。
    """

    spacing_y: float = 140.0
    start_x: float = 50.0
    start_y: float = 50.0
    label_offset: float = 40.0
    label_stack_gap: float = 26.0
    strategy: LayoutStrategy = LayoutStrategy.DAG

    _offsets: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    _structure_config: Dict[str, Mapping[str, object]] = field(default_factory=dict)
    _commits: Dict[str, List[str]] = field(default_factory=dict)
    _labels: Dict[str, List[str]] = field(default_factory=dict)
    _attachments: Dict[str, Dict[str, str]] = field(default_factory=dict)
    _positions: Dict[str, Dict[str, Tuple[float, float]]] = field(default_factory=dict)
    _dirty_structures: set[str] = field(default_factory=set)

    def set_offsets(self, offsets: Dict[str, Tuple[float, float]]) -> None:
        self._offsets = offsets

    def set_structure_config(self, config: Dict[str, Mapping[str, object]]) -> None:
        self._structure_config = config

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
        self._offsets.clear()
        self._structure_config.clear()
        self._commits.clear()
        self._labels.clear()
        self._attachments.clear()
        self._positions.clear()
        self._dirty_structures.clear()

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    def _apply_structural_ops(self, step: AnimationStep) -> None:
        for op in step.ops:
            sid = op.data.get("structure_id")
            if not sid:
                continue
            if op.op is OpCode.CREATE_NODE:
                target = op.target or ""
                kind = str(op.data.get("kind", ""))
                if kind == "commit":
                    commits = self._commits.setdefault(sid, [])
                    if target not in commits:
                        commits.append(target)
                else:
                    labels = self._labels.setdefault(sid, [])
                    if target not in labels:
                        labels.append(target)
                self._dirty_structures.add(sid)
            elif op.op is OpCode.DELETE_NODE:
                target = op.target or ""
                commits = self._commits.get(sid, [])
                if target in commits:
                    commits.remove(target)
                labels = self._labels.get(sid, [])
                if target in labels:
                    labels.remove(target)
                attach = self._attachments.get(sid, {})
                attach.pop(target, None)
                # 清理指向被删目标的依附关系
                for label_id, tgt in list(attach.items()):
                    if tgt == target:
                        attach.pop(label_id, None)
                self._dirty_structures.add(sid)
            elif op.op is OpCode.SET_LABEL:
                attach_to = op.data.get("attach_to")
                if isinstance(attach_to, str) and op.target:
                    self._attachments.setdefault(sid, {})[op.target] = attach_to
                    self._dirty_structures.add(sid)

    def _inject_positions(self) -> List[AnimationOp]:
        ops: List[AnimationOp] = []
        for sid in list(self._dirty_structures):
            offset_x, offset_y = self._offsets.get(sid, (0.0, 0.0))
            cfg = self._structure_config.get(sid, {})
            spacing_y = _as_float(cfg.get("spacing"), self.spacing_y)
            start_x = _as_float(cfg.get("start_x"), self.start_x)
            start_y = _as_float(cfg.get("start_y"), self.start_y)
            orientation = str(cfg.get("orientation", "vertical")).lower()

            commits = self._commits.get(sid, [])
            labels = self._labels.get(sid, [])
            attachments = self._attachments.get(sid, {})
            new_positions: Dict[str, Tuple[float, float]] = {}

            for idx, commit_id in enumerate(commits):
                if orientation == "horizontal":
                    pos = (
                        start_x + offset_x + spacing_y * idx,
                        start_y + offset_y,
                    )
                else:
                    pos = (
                        start_x + offset_x,
                        start_y + offset_y + spacing_y * idx,
                    )
                new_positions[commit_id] = pos

            labels_by_target: Dict[str, List[str]] = {}
            for label_id in labels:
                target = attachments.get(label_id)
                labels_by_target.setdefault(target or "", []).append(label_id)

            for target, label_ids in labels_by_target.items():
                base_pos = new_positions.get(target)
                if base_pos is None:
                    base_pos = (
                        start_x + offset_x,
                        start_y + offset_y - self.label_offset,
                    )
                for stack_idx, label_id in enumerate(label_ids):
                    pos = (
                        base_pos[0],
                        base_pos[1]
                        - self.label_offset
                        - stack_idx * self.label_stack_gap,
                    )
                    new_positions[label_id] = pos

            prev = self._positions.setdefault(sid, {})
            for node_id, pos in new_positions.items():
                if prev.get(node_id) != pos:
                    ops.append(
                        AnimationOp(
                            op=OpCode.SET_POS,
                            target=node_id,
                            data={"x": pos[0], "y": pos[1]},
                        )
                    )
            self._positions[sid] = new_positions
        self._dirty_structures.clear()
        return ops


def _as_float(value: object | None, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default
