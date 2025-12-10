from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .ops import AnimationOp


@dataclass
class AnimationStep:
    """
    A single teaching micro-step.

    Semantics (see OPS_SPEC v1.0):

    - duration_ms: how long this step should take to play, in milliseconds.
    - label:       optional human-readable title for UI / debugging.
    - ops:         all AnimationOps that semantically belong to this time window.
    """

    duration_ms: int = 400
    label: Optional[str] = None
    ops: List[AnimationOp] = field(default_factory=list)


@dataclass
class Timeline:
    """
    An ordered sequence of AnimationSteps.

    Renderer is expected to:
      - iterate steps in order,
      - for each step, compute the visual end-state after applying all ops,
      - animate from previous step's end-state to this end-state over duration_ms.
    """

    steps: List[AnimationStep] = field(default_factory=list)

    def add_step(self, step: AnimationStep) -> None:
        self.steps.append(step)

    def __iter__(self) -> Sequence[AnimationStep]:
        return iter(self.steps)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.steps)
