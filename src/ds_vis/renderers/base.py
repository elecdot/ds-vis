from __future__ import annotations

from abc import ABC, abstractmethod

from ds_vis.core.ops import Timeline


class Renderer(ABC):
    """
    Abstract renderer interface.

    Concrete implementations consume a Timeline and are responsible for:
      - maintaining visual state,
      - animating each AnimationStep over its duration_ms,
      - applying all AnimationOps per step.
    """

    @abstractmethod
    def render_timeline(self, timeline: Timeline) -> None:
        """
        Render (and optionally animate) the given Timeline.

        Implementations may:
          - play the steps immediately,
          - enqueue them into an internal player,
          - support single-step playback, etc.
        """
        raise NotImplementedError
