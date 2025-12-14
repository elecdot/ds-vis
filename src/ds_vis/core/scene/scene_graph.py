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

        Current Phase:
          - CREATE_STRUCTURE (list) with minimal payload validation,
          - DELETE (list) to remove visuals but keep ID monotonicity,
          - unsupported commands raise CommandError (no silent no-op).
        """
        if command.type is CommandType.CREATE_STRUCTURE:
            structural_timeline = self._handle_create_structure(command)
        elif command.type is CommandType.DELETE:
            structural_timeline = self._handle_delete(command)
        else:
            raise CommandError(f"Unsupported command type: {command.type!s}")

        if self._layout_engine:
            return self._layout_engine.apply_layout(structural_timeline)

        return structural_timeline

    def _handle_create_structure(self, command: Command) -> Timeline:
        kind = command.payload.get("kind")
        if not kind:
            raise CommandError("CREATE_STRUCTURE requires payload.kind")

        if kind == "list":
            model = self._get_or_create_list_model(command.structure_id)
            values = command.payload.get("values")
            # Recreate if structure already exists to keep IDs monotonic.
            if model._node_ids:
                return model.recreate(values)
            return model.create(values)

        raise CommandError(f"Unsupported structure kind: {kind!r}")

    def _handle_delete(self, command: Command) -> Timeline:
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")

        if isinstance(model, ListModel):
            return model.delete_all()

        raise CommandError(
            f"DELETE unsupported for structure: {command.structure_id!r}"
        )

    def _get_or_create_list_model(self, structure_id: str) -> ListModel:
        existing = self._structures.get(structure_id)
        if isinstance(existing, ListModel):
            return existing

        model = ListModel(structure_id=structure_id)
        self._structures[structure_id] = model
        return model
