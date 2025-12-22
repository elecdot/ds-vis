"""
Experimental helper utilities for assembling AnimationOps.

WARNING:
- 尚未形成统一设计或广泛复用，当前模型未依赖。
- 接下来可能调整/删除；使用时请局部试点并配套测试。
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode


def make_node(structure_id: str, node_id: str, label: Any) -> AnimationOp:
    return AnimationOp(
        op=OpCode.CREATE_NODE,
        target=node_id,
        data={"structure_id": structure_id, "label": str(label)},
    )


def make_edge(
    structure_id: str, edge_id: str, src: str, dst: str, label: Optional[str] = None
) -> AnimationOp:
    data = {"structure_id": structure_id, "from": src, "to": dst}
    if label is not None:
        data["label"] = label
    return AnimationOp(op=OpCode.CREATE_EDGE, target=edge_id, data=data)


def delete_edge(structure_id: str, edge_id: str) -> AnimationOp:
    return AnimationOp(
        op=OpCode.DELETE_EDGE, target=edge_id, data={"structure_id": structure_id}
    )


def delete_node(structure_id: str, node_id: str) -> AnimationOp:
    return AnimationOp(
        op=OpCode.DELETE_NODE, target=node_id, data={"structure_id": structure_id}
    )


def set_state(structure_id: str, target: str, state: str) -> AnimationOp:
    return AnimationOp(
        op=OpCode.SET_STATE,
        target=target,
        data={"state": state, "structure_id": structure_id},
    )


def set_label(structure_id: str, target: str, label: Any) -> AnimationOp:
    return AnimationOp(
        op=OpCode.SET_LABEL,
        target=target,
        data={"label": str(label), "structure_id": structure_id},
    )


def set_message(text: str) -> AnimationOp:
    return AnimationOp(op=OpCode.SET_MESSAGE, target=None, data={"text": text})


def clear_message() -> AnimationOp:
    return AnimationOp(op=OpCode.CLEAR_MESSAGE, target=None, data={})


def steps_from_ops(ops: Iterable[AnimationOp], duration_ms: int = 0) -> AnimationStep:
    return AnimationStep(duration_ms=duration_ms, ops=list(ops))


def merge_timelines(*steps: AnimationStep) -> List[AnimationStep]:
    return [
        AnimationStep(duration_ms=s.duration_ms, label=s.label, ops=list(s.ops))
        for s in steps
    ]
