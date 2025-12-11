from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from ds_vis.core.exceptions import CommandError
from ds_vis.core.layout import LayoutEngine
from ds_vis.core.layout.simple import SimpleLayoutEngine
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
    _layout_engine: Optional[LayoutEngine] = None

    def __post_init__(self) -> None:
        # Phase 1: default to a naive linear layout to keep the pipeline connected.
        if self._layout_engine is None:
            self._layout_engine = SimpleLayoutEngine()

    def apply_command(self, command: Command) -> Timeline:
        """
        Apply a high-level command and return a Timeline describing the animation.

        Current Phase: handle CREATE_STRUCTURE for list skeletons.
        Future steps:
          - dispatch to more structure kinds,
          - run the Timeline through the layout engine to inject SET_POS ops.
        """
        if command.type is CommandType.CREATE_STRUCTURE:
            structural_timeline = self._handle_create_structure(command)
        else:
            # For unimplemented command types, return an empty timeline to keep
            # the walking skeleton stable until future phases fill them in.
            structural_timeline = Timeline()

        if self._layout_engine:
            return self._layout_engine.apply_layout(structural_timeline)

        return structural_timeline

    def _handle_create_structure(self, command: Command) -> Timeline:
        kind = command.payload.get("kind")

        if kind == "list":
            model = ListModel(structure_id=command.structure_id)
            self._structures[command.structure_id] = model
            values = command.payload.get("values")
            return model.create(values)

        raise CommandError(f"Unsupported structure kind: {kind!r}")
