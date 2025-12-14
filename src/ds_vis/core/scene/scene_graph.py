from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Set

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

    P0.3: commands are routed via a handler registry; surface-only support for list
    CREATE_STRUCTURE / DELETE_STRUCTURE / DELETE_NODE. Unknown commands raise
    CommandError (no silent no-op).
    """

    # TODO: replace `object` with a proper model base class / protocol in later phases.
    _structures: Dict[str, object] = field(default_factory=dict)
    _layout_engine: Optional[LayoutEngine] = None
    _handlers: Dict[CommandType, Callable[[Command], Timeline]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # Default to a simple linear layout to keep the pipeline connected.
        if self._layout_engine is None:
            self._layout_engine = SimpleLayoutEngine()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self._handlers = {
            CommandType.CREATE_STRUCTURE: self._handle_create_structure,
            CommandType.DELETE_STRUCTURE: self._handle_delete_structure,
            CommandType.DELETE_NODE: self._handle_delete_node,
        }

    def apply_command(self, command: Command) -> Timeline:
        """
        Apply a high-level command and return a Timeline describing the animation.

        Current Phase:
          - CREATE_STRUCTURE (list) with minimal payload validation.
          - DELETE_STRUCTURE / DELETE_NODE for list (no legacy DELETE overload).
          - Unsupported commands raise CommandError (no silent no-op).
        """
        handler = self._handlers.get(command.type)
        if handler is None:
            raise CommandError(f"Unsupported command type: {command.type!s}")
        self._validate_payload(command)
        structural_timeline = handler(command)

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

    def _handle_delete_structure(self, command: Command) -> Timeline:
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")

        if isinstance(model, ListModel):
            payload_kind = command.payload.get("kind", "list")
            if payload_kind != model.kind:
                raise CommandError(
                    f"DELETE kind mismatch for structure {command.structure_id!r}"
                )
            return model.delete_all()

        raise CommandError(
            f"DELETE unsupported for structure: {command.structure_id!r}"
        )

    def _handle_delete_node(self, command: Command) -> Timeline:
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")

        if isinstance(model, ListModel):
            payload_kind = command.payload.get("kind", "list")
            if payload_kind != model.kind:
                raise CommandError(
                    f"DELETE_NODE kind mismatch for structure {command.structure_id!r}"
                )
            if "index" not in command.payload:
                raise CommandError("DELETE_NODE requires 'index'")
            index = command.payload.get("index")
            if not isinstance(index, int):
                raise CommandError("DELETE_NODE index must be int")
            if index < 0 or index >= len(model._node_ids):
                raise CommandError("DELETE_NODE index out of range")
            return model.delete_index(index)

        raise CommandError(
            f"DELETE_NODE unsupported for structure: {command.structure_id!r}"
        )

    # ------------------------------------------------------------------ #
    # Payload validation helpers
    # ------------------------------------------------------------------ #
    def _validate_payload(self, command: Command) -> None:
        payload = command.payload
        if not isinstance(payload, Mapping):
            raise CommandError("Command payload must be a mapping")

        if command.type == CommandType.CREATE_STRUCTURE:
            self._validate_create_structure_payload(payload)
        elif command.type == CommandType.DELETE_STRUCTURE:
            self._validate_delete_structure_payload(payload)
        elif command.type == CommandType.DELETE_NODE:
            self._validate_delete_node_payload(payload)

    def _validate_create_structure_payload(self, payload: Mapping[str, Any]) -> None:
        self._reject_unknown_fields(payload, {"kind", "values"})
        kind = payload.get("kind")
        if not kind:
            raise CommandError("CREATE_STRUCTURE requires payload.kind")
        if not isinstance(kind, str):
            raise CommandError("CREATE_STRUCTURE kind must be a string")
        if "values" in payload:
            values = payload.get("values")
            if values is not None and not isinstance(values, (list, tuple)):
                raise CommandError("values must be a list or tuple")

    def _validate_delete_structure_payload(self, payload: Mapping[str, Any]) -> None:
        self._reject_unknown_fields(payload, {"kind"})
        if "kind" in payload and not isinstance(payload.get("kind"), str):
            raise CommandError("DELETE_STRUCTURE kind must be a string")

    def _validate_delete_node_payload(self, payload: Mapping[str, Any]) -> None:
        self._reject_unknown_fields(payload, {"kind", "index"})
        if "kind" in payload and not isinstance(payload.get("kind"), str):
            raise CommandError("DELETE_NODE kind must be a string")
        if "index" not in payload:
            raise CommandError("DELETE_NODE requires 'index'")
        index = payload.get("index")
        if not isinstance(index, int):
            raise CommandError("DELETE_NODE index must be int")

    def _reject_unknown_fields(
        self, payload: Mapping[str, Any], allowed: Set[str]
    ) -> None:
        unknown = set(payload.keys()) - allowed
        if unknown:
            unknown_list = ", ".join(sorted(unknown))
            raise CommandError(f"Unexpected payload fields: {unknown_list}")

    def _get_or_create_list_model(self, structure_id: str) -> ListModel:
        existing = self._structures.get(structure_id)
        if isinstance(existing, ListModel):
            return existing

        model = ListModel(structure_id=structure_id)
        self._structures[structure_id] = model
        return model
