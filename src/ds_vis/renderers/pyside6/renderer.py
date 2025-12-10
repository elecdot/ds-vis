from __future__ import annotations

from typing import Sequence

from PySide6.QtWidgets import QGraphicsScene
from ds_vis.core.ops import AnimationOp
from ds_vis.renderers.base import Renderer


class PySide6Renderer(Renderer):
    """
    PySide6-based renderer using QGraphicsScene/QGraphicsView.

    Phase 0: skeleton only. Concrete drawing/animation logic will be implemented later.
    """

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene

    def render(self, ops: Sequence[AnimationOp]) -> None:
        """
        Interpret the given AnimationOps and update the scene accordingly.

        Phase 0 implementation is a stub.
        """
        # TODO: implement in later phase
        return
