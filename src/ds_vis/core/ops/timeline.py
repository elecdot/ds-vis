from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from .ops import AnimationOp


@dataclass
class Timeline:
    """
    A simple container for an ordered sequence of AnimationOps.

    In later phases this may support:
      - hierarchical grouping (sequences / parallels)
      - time offsets and durations
      - step-wise playback control

    For Phase 0, this is a minimal placeholder.
    """

    ops: List[AnimationOp] = field(default_factory=list)

    def extend(self, ops: Iterable[AnimationOp]) -> None:
        """Append multiple operations to the timeline."""
        self.ops.extend(ops)

    def __iter__(self) -> Sequence[AnimationOp]:
        return iter(self.ops)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.ops)
