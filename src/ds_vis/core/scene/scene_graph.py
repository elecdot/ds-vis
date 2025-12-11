from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ds_vis.core.exceptions import CommandError
from ds_vis.core.models import ListModel
from ds_vis.core.ops import Timeline

from .command import Command, CommandType


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

        Current Phase: handle CREATE_STRUCTURE for list skeletons.
        Future steps:
          - dispatch to more structure kinds,
          - run the Timeline through the layout engine to inject SET_POS ops.
        """
        if command.type is CommandType.CREATE_STRUCTURE:
            return self._handle_create_structure(command)

        # For unimplemented command types, return an empty timeline to keep
        # the walking skeleton stable until future phases fill them in.
        return Timeline()

    def _handle_create_structure(self, command: Command) -> Timeline:
        kind = command.payload.get("kind")

        if kind == "list":
            model = ListModel(structure_id=command.structure_id)
            self._structures[command.structure_id] = model
            values = command.payload.get("values")
            return model.create(values)

        raise CommandError(f"Unsupported structure kind: {kind!r}")
