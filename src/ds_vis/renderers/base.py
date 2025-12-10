from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from ds_vis.core.ops import AnimationOp


class Renderer(ABC):
    """
    Abstract renderer interface.

    Concrete implementations (PySide6, Web, CLI, etc.) consume AnimationOps
    and are responsible for actually drawing and animating.
    """

    @abstractmethod
    def render(self, ops: Sequence[AnimationOp]) -> None:
        """
        Render (and optionally animate) a sequence of AnimationOps.

        Implementations may choose to:
          - play the sequence immediately
          - enqueue it in an internal timeline
          - support step-wise playback, etc.
        """
        raise NotImplementedError
