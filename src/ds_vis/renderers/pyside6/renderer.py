from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QGraphicsScene

from ds_vis.core.ops import Timeline, AnimationStep, AnimationOp, OpCode
from ds_vis.renderers.base import Renderer


class PySide6Renderer(Renderer):
    """
    PySide6-based renderer using QGraphicsScene/QGraphicsView.

    Phase 1: skeleton only. It defines where and how Timeline will be consumed,
    but does not implement actual drawing yet.
    """

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        # TODO: maintain internal visual state here in later phases.

    def render_timeline(self, timeline: Timeline) -> None:
        """
        Interpret the given Timeline and update the scene accordingly.

        Phase 1: stub implementation. Later, this will:
          - iterate all steps,
          - for each step, apply ops to an internal scene model,
          - animate transitions over duration_ms using Qt's facilities.
        """
        # For now, do nothing.
        return

    # Optional helper skeletons (to be implemented later):

    def _apply_step(self, step: AnimationStep) -> None:
        """Apply a single AnimationStep to the internal state (stub)."""
        for op in step.ops:
            self._apply_op(op)

    def _apply_op(self, op: AnimationOp) -> None:
        """Apply a single AnimationOp to the internal state (stub)."""
        # Example switch skeleton; actual drawing will be added later.
        if op.op is OpCode.CREATE_NODE:
            return
        if op.op is OpCode.DELETE_NODE:
            return
        # ... handle other op codes as needed
        return
