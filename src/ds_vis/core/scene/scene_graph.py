from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from ds_vis.core.ops import AnimationOp, Timeline
from .command import Command


@dataclass
class SceneGraph:
    """
    Central scene/state manager.

    Responsibilities:
      - Maintain all current data-structure instances (lists, trees, GitGraph, etc.).
      - Accept high-level `Command`s from UI/DSL/persistence.
      - Delegate to the appropriate model instance.
      - Collect and return AnimationOps describing the visual changes.

    Phase 0: structure and API only; implementation is intentionally left as stubs.
    """

    # TODO: replace `object` with concrete model base class / protocol in later phases.
    _structures: Dict[str, object] = field(default_factory=dict)

    def apply_command(self, command: Command) -> Sequence[AnimationOp]:
        """
        Apply a high-level command to the scene and return the resulting animation ops.

        For Phase 0, this method is a stub and should be implemented in later phases.
        """
        # Placeholder implementation to be filled in Phase 2+.
        # raise NotImplementedError("SceneGraph.apply_command is not implemented yet.")
        return Timeline().ops
