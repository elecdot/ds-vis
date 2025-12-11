from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ds_vis.core.ops import Timeline

from .command import Command


@dataclass
class SceneGraph:
    """
    Central state/scene manager.

    Responsibilities:
      - Maintain all active data-structure model instances.
      - Accept high-level Command objects from UI/DSL.
      - Dispatch to the appropriate model.
      - Collect a structural Timeline (no coordinates).
      - Pass the Timeline through layout (core.layout) before handing it to a renderer.

    Phase 1: API and responsibilities are defined; implementation is intentionally
    stubbed.
    """

    # TODO: replace `object` with a proper model base class / protocol in later phases.
    _structures: Dict[str, object] = field(default_factory=dict)

    def apply_command(self, command: Command) -> Timeline:
        """
        Apply a high-level command and return a Timeline describing the animation.

        Current implementation is a placeholder. Future steps:
          - look up the target model by structure_id,
          - invoke the appropriate method on the model to get a structural Timeline,
          - run the Timeline through the layout engine to inject SET_POS ops.
        """
        # TODO: implement dispatch + layout pipeline in later phases.
        return Timeline()
